from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import re
import logging
import api.gtfs

import pytz
from collections import defaultdict

from api.ptv_api import send_ptv_request
from utils import parse_departure_time
import config

logger = logging.getLogger("ptv_display")
tz = pytz.timezone(os.getenv("TIMEZONE"))

class TramStop:
    """
    Represents a PTV tram stop and provides departure lookup functionality.
    """
    def __init__(self, stop_id):
        """
        Initialise a Stop object and resolve it against the PTV API.

        :param name: User-provided stop name
        :raises ValueError: If stop cannot be resolved
        """

        # Core stop metadata (important)
        self.stop_id = stop_id
        self.name: Optional[str] = None
        self.routes: List[Dict[str, Any]] = []

        # Core stop metadata (unimportant)
        self.stop_suburb: Optional[str] = None
        self.route_type: Optional[int] = None
        self.stop_latitude: Optional[float] = None
        self.stop_longitude: Optional[float] = None
        self.stop_sequence: Optional[int] = None
        self.stop_landmark: Optional[str] = None

        # Non-metadata
        self.stop_id_gtfs: Optional[str] = None

        self.resolve_stop()

    def resolve_stop(self) -> None:
        """
        Resolve the provided stop name to a PTV stop ID and metadata.
        
        :raises ValueError: If no matching stop found
        """
        logger.info(f'Resolving tram stop for stop ID: {self.stop_id}...')

        try:   
            # Resolve Tram
            endpoint = (
                f"/v3/stops/{self.stop_id}/route_type/{config.route_type_tram}"
                f"?stop_location=true&stop_amenities=true&stop_accessibility=true"
                f"&stop_contact=true&stop_ticket=true&stop_staffing=true&stop_disruptions=true"
            )
            result = send_ptv_request(endpoint)
            tram_stop = result['stop']
            # Populate Metadata
            self.route_type = tram_stop['route_type']
            self.name = tram_stop['stop_name']
            self.routes = tram_stop.get('routes', [])
            self.stop_suburb = tram_stop.get('stop_suburb')
            self.stop_latitude = tram_stop.get('stop_latitude')
            self.stop_longitude = tram_stop.get('stop_longitude')
            self.stop_sequence = tram_stop.get('stop_sequence')
            self.stop_landmark = tram_stop.get('stop_landmark')
        
        except KeyError as e:
            logger.error(f"Missing expected field in API response: {str(e)}")
            raise ValueError(f"Invalid API response for stop '{self._input_name}'")
        except Exception as e:
            logger.error(f"Unexpected error resolving stop '{self._input_name}': {str(e)}")
            raise

    def get_next_departures_per_route(self, n_departures: int) -> List[Dict[str, Any]]:
        """
        Retrieve upcoming departures grouped by route.
        
        Selects departures using round-robin (one per route), then greedily adds
        the earliest remaining departures until min_departures is reached.
        Final list is sorted by route_number so routes display grouped together.
        
        :param n_departures: Requested number of departures (for compatibility)
        :return: List of departure dictionaries sorted by route_number
        """
        endpoint = (
            f"/v3/departures/route_type/1/stop/{self.stop_id}"
            f"?max_results={20}"
            f"&expand=0"
        )

        result = send_ptv_request(endpoint)
        if result is None:
            logger.warning(f"API returned None for departures from stop {self.stop_id}")
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
        while len(selected_departures) < n_departures:
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
        
        :param text: Text to normalise
        :return: Normalised text
        """
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def score_stop(
        self,
        stop: Dict[str, Any],
        target_name: str,
        target_suburb: Optional[str] = None,
    ) -> int:
        """
        Score how well a stop matches a target name and suburb.
        
        :param stop: Stop object from API
        :param target_name: Normalised target name
        :param target_suburb: Optional suburb name
        :return: Match score (higher is better)
        """
        try:
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
        except Exception as e:
            logger.error(f"Error scoring stop: {str(e)}")
            return 0

    @staticmethod
    def filter_departure_list(
        departures: List[Optional[Dict[str, Any]]],
        n_to_show: int,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Remove RRB services and pad the list with None up to n_to_show.
        
        :param departures: List of departures
        :param n_to_show: Target number of items
        :return: Filtered and padded list
        """
        filtered: List[Optional[Dict[str, Any]]] = []

        for dep in departures:
            if dep and "RRB" not in dep.get("flag", ""):
                filtered.append(dep)
            if len(filtered) == n_to_show:
                break

        while len(filtered) < n_to_show:
            filtered.append(None)

        return filtered