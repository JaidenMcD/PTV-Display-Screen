

from typing import Dict, List, Any
from datetime import datetime
import os
import re
import api.gtfs

import pytz
from collections import defaultdict

from api.ptv_api import send_ptv_request
from utils import parse_departure_time
import config


tz = pytz.timezone(os.getenv("TIMEZONE"))

class TramStop:
    """
    Represents a PTV tram stop and provides departure lookup functionality.
    """
    def __init__(self, name: str):
        """
        Initialise a Stop object and resolve it against the PTV API.

        :param name: User-provided stop name
        """
        self._input_name = name

        # Core stop metadata (important)
        self.stop_id = None
        self.name = None
        self.routes = []

        # Core stop metadata (unimportant)
        self.stop_suburb = None
        self.route_type = None
        self.stop_latitude = None
        self.stop_longitude = None
        self.stop_sequence = None
        self.stop_landmark = None

        # Non-metadata
        self.stop_id_gtfs = None

        self.resolve_stop()

    def resolve_stop(self) -> None:
        """
        Resolve the provided stop name to a PTV stop ID and metadata.
        """
        print(f'Resolving stop for input name: {self._input_name}...')

        raw_name = self._input_name.strip()
        query_name = raw_name.replace(' ', '%20')
        target = self.normalise(raw_name)

        # Resolve Metro
        endpoint = (
            f"/v3/search/{query_name}"
            f"?route_types={config.route_type_tram}"
        )
        result = send_ptv_request(endpoint)
        
        scored = [
            (self.score_stop(candidate, target), candidate)
            for candidate in result.get("stops", [])
        ]
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, tram_stop = scored[0] if scored else (0, None)

        if best_score == 0 or tram_stop is None:
            raise ValueError(f"No matching metro station found for '{raw_name}'")
        
        print(
            f"Found stop {tram_stop['stop_name']} "
            f"[{tram_stop['stop_id']}] with score {best_score}"
        )

        self._input_name = None  # discard after use
        
        # Populate Metadata
        self.stop_id = tram_stop['stop_id'] 
        self.route_type = tram_stop['route_type']
        self.name = tram_stop['stop_name']
        self.routes = tram_stop['routes']
        self.stop_suburb = tram_stop['stop_suburb']
        self.stop_latitude = tram_stop['stop_latitude']
        self.stop_longitude = tram_stop['stop_longitude']
        self.stop_sequence = tram_stop['stop_sequence']
        self.stop_landmark = tram_stop['stop_landmark']
    
    def get_next_departures(self,
                            n_departures: int,
    ):
        """
        Retrieve upcoming departures for this stop.

        :param n_departures: Number of departures to return
        :param return_next_run: Whether to return the full run object
        :return: List of departure dictionaries (optionally plus next run)
        returns{
            "platform": departure.get("platform_number"),
            "destination": destination,
            "departure_time": departure_time,
            "time_to_departure": time_to_departure,
            "departure_note": departure.get("departure_note"),
            "route_gtfs_id": route_gtfs_id,
            "run_id": run_id,
            "flag": departure.get("flags", ""),
        }
        """

        endpoint = (
            f"/v3/departures/route_type/1/stop/{self.stop_id}"
            f"?max_results={n_departures}"
            f"&expand=0"
        )

        result = send_ptv_request(endpoint)
        if not result:
            return [], []
        

        departures = result.get("departures", [])[:n_departures]
        directions = result.get("directions", {}) or {}
        if departures == []:
            return [], []
        
        departures_list: List[Dict[str, Any]] = []
        now_local = datetime.now(tz)

        for departure in departures:
            departure_time, time_to_departure = parse_departure_time(
                departure=departure,
                now_local=now_local,
            )
            time_to_departure = time_to_departure.replace(" min", "")  # Tram Display does not use "mins" suffix
            direction_id = departure.get("direction_id")
            run_id = departure.get("run_id")
            direction_info = directions.get(str(direction_id), {})

            destination = direction_info.get("direction_name", "Unknown")

            route_gtfs_id = None
            for route in self.routes:
                if route["route_id"] == departure["route_id"]:
                    route_gtfs_id = route["route_gtfs_id"]
                    route_number = route["route_number"]
                    break
            
            departures_list.append(
                {
                    "platform": departure.get("platform_number"),
                    "destination": destination,
                    "departure_time": departure_time,
                    "time_to_departure": time_to_departure,
                    "departure_note": departure.get("departure_note"),
                    "route_gtfs_id": route_gtfs_id,
                    "route_number": route_number,
                    "run_id": run_id,
                    "flag": departure.get("flags", ""),
                }
            )
        departures_list = self.filter_departure_list(
            departures_list,
            n_departures,
        )
        return departures_list

    def get_next_departures_per_route(self,
                            min_departures: int,
    ):
        """
        Retrieve upcoming departures grouped by route.
        
        Selects departures using round-robin (one per route), then greedily adds
        the earliest remaining departures until min_departures is reached.
        Final list is sorted by route_id so routes display grouped together.
        
        :param n_departures: Unused (kept for compatibility)
        :return: List of departure dictionaries sorted by route_id
        """
        endpoint = (
            f"/v3/departures/route_type/1/stop/{self.stop_id}"
            f"?max_results={20}"
            f"&expand=0"
        )

        result = send_ptv_request(endpoint)
        if not result:
            return []
        
        # disruptions
        # get route numbers
        routes = result.get("routes", []) 
        route_numbers = [info['route_number'] for info in routes.values()]
        service_updates = api.gtfs.tram_service_updates(route_numbers)

        alerts = []
        for service_update in service_updates:
            alerts.append({
                "header": service_update['header'],
                "description": service_update['description'],
                "url": service_update['url']
            })

        # Group Departures by route_id
        raw_departures = result.get('departures', [])
        grouped_departures = defaultdict(list)
        for dep in raw_departures:
            grouped_departures[dep['route_id']].append(dep)
        
        # Sort each route's departures by estimated (or scheduled) departure time
        for route_id in grouped_departures:
            grouped_departures[route_id].sort(
                key=lambda x: x.get('estimated_departure_utc') or x.get('scheduled_departure_utc', '')
            )

        # Phase 1: Round-robin - take one departure per route
        selected_departures = []
        route_ids = list(grouped_departures.keys())
    
        for route_id in route_ids:
            if grouped_departures[route_id]:
                selected_departures.append(grouped_departures[route_id].pop(0))

        # Phase 2: If we haven't reached min_departures, greedily add next earliest
        while len(selected_departures) < min_departures:
            # Find the route with the earliest next departure
            earliest_dep = None
            earliest_route_id = None
            earliest_time = None
            
            for route_id in route_ids:
                if grouped_departures[route_id]:
                    next_dep = grouped_departures[route_id][0]
                    # Use estimated time if available, otherwise scheduled
                    dep_time = next_dep.get('estimated_departure_utc') or next_dep.get('scheduled_departure_utc', '')
                    
                    if earliest_time is None or dep_time < earliest_time:
                        earliest_time = dep_time
                        earliest_dep = next_dep
                        earliest_route_id = route_id
            
            if earliest_dep is None:
                break  # No more departures available
            
            selected_departures.append(grouped_departures[earliest_route_id].pop(0))

        directions = result.get("directions", {}) or {}
        now_local = datetime.now(tz)

        # Build the departures list with full details
        departures_list: List[Dict[str, Any]] = []
        
        for departure in selected_departures:
            departure_time, time_to_departure = parse_departure_time(
                departure=departure,
                now_local=now_local,
            )
            time_to_departure = time_to_departure.replace(" min", "")
            direction_id = departure.get("direction_id")
            run_id = departure.get("run_id")
            direction_info = directions.get(str(direction_id), {})

            destination = direction_info.get("direction_name", "Unknown")

            route_gtfs_id = None
            route_number = None
            route_id = departure["route_id"]
            for route in self.routes:
                if route["route_id"] == route_id:
                    route_gtfs_id = route["route_gtfs_id"]
                    route_number = route["route_number"]
                    break
            
            departures_list.append(
                {
                    "platform": departure.get("platform_number"),
                    "destination": destination,
                    "departure_time": departure_time,
                    "time_to_departure": time_to_departure,
                    "departure_note": departure.get("departure_note"),
                    "route_gtfs_id": route_gtfs_id,
                    "route_number": route_number,
                    "run_id": run_id,
                    "flag": departure.get("flags", ""),
                    "route_id": route_id,
                }
            )
        
        # Sort by route_id so routes are grouped together on display
        departures_list.sort(key=lambda x: int(x["route_number"]) if x["route_number"].isdigit() else float('inf'))
        
        return departures_list, alerts


    @staticmethod
    def normalise(text: str) -> str:
        """
        Normalise text for fuzzy matching.
        """
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    

    def score_stop(
        self,
        stop: Dict[str, Any],
        target_name: str,
        target_suburb: str | None = None,
    ) -> int:
        """
        Score how well a stop matches a target name and suburb.
        """
        name = self.normalise(stop.get("stop_name", ""))
        score = 0

        if name == target_name:
            score += 100
        elif name.startswith(target_name):
            score += 70
        elif target_name in name:
            score += 40

        if target_suburb and stop.get("stop_suburb"):
            if stop["stop_suburb"].lower() == target_suburb.lower():
                score += 20

        return score

    @staticmethod
    def filter_departure_list(
        departures: List[Dict[str, Any] | None],
        n_to_show: int,
    ) -> List[Dict[str, Any] | None]:
        """
        Remove RRB services and pad the list with None up to n_to_show.
        """
        filtered: List[Dict[str, Any] | None] = []

        for dep in departures:
            if dep and "RRB" not in dep.get("flag", ""):
                filtered.append(dep)
            if len(filtered) == n_to_show:
                break

        while len(filtered) < n_to_show:
            filtered.append(None)

        return filtered