
from typing import Dict, List, Any
from datetime import datetime
import os
import re

import pytz

from api.ptv_api import send_ptv_request
from utils import parse_departure_time
import config


tz = pytz.timezone(os.getenv("TIMEZONE"))


class Stop:
    """
    Represents a PTV metro train stop and provides departure lookup functionality.
    """
    def __init__(self, name: str, platforms: List[str]):
        """
        Initialise a Stop object and resolve it against the PTV API.

        :param name: User-provided stop name
        :param platforms: List of platform numbers to filter departures
        """
        self.platforms = platforms
        self._input_name = name

        # Core stop metadata (important)
        self.stop_id = None
        self.name = None
        self.routes: List[Dict[str, Any]] = []

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
            f"?route_types={config.route_type_train}"
        )
        result = send_ptv_request(endpoint)
        
        scored = [
            (self.score_stop(candidate, target), candidate)
            for candidate in result.get("stops", [])
        ]
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, train_stop = scored[0] if scored else (0, None)

        if best_score == 0 or train_stop is None:
            raise ValueError(f"No matching metro station found for '{raw_name}'")
        
        print(
            f"Found stop {train_stop['stop_name']} "
            f"[{train_stop['stop_id']}] with score {best_score}"
        )

        self._input_name = None  # discard after use
        
        # Populate Metadata
        self.stop_id = train_stop['stop_id'] 
        self.route_type = train_stop['route_type']
        self.name = train_stop['stop_name']
        self.routes = train_stop['routes']
        self.stop_suburb = train_stop['stop_suburb']
        self.stop_latitude = train_stop['stop_latitude']
        self.stop_longitude = train_stop['stop_longitude']
        self.stop_sequence = train_stop['stop_sequence']
        self.stop_landmark = train_stop['stop_landmark']

    def get_next_departures(self,
                            n_departures: int,
                            return_next_run: bool = False
    ):
        """
        Retrieve upcoming departures for this stop.

        :param n_departures: Number of departures to return
        :param return_next_run: Whether to return the full run object
        :return: List of departure dictionaries (optionally plus next run)
        """
        platform_str = ""
        if self.platforms != [""]:
            for platform_no in self.platforms:
                platform_str += f"&platform_numbers={platform_no}"

        endpoint = (
            f"/v3/departures/route_type/0/stop/{self.stop_id}"
            f"?max_results={n_departures}"
            f"&expand=0"
            f"&include_skipped_stops=true"
            f"{platform_str}"
        )

        result = send_ptv_request(endpoint)
        if not result:
            return []

        departures = result.get("departures", [])[:n_departures]
        runs = result.get("runs", {}) or {}
        
        departures_list: List[Dict[str, Any]] = []
        now_local = datetime.now(tz)

        for departure in departures:
            departure_time, time_to_departure = parse_departure_time(
                departure=departure,
                now_local=now_local,
            )

    
            run_id = departure.get("run_id")
            run_info = runs.get(str(run_id), {})

            destination = self._get_pid_destination(run_info)

            route_gtfs_id = None
            for route in self.routes:
                if route["route_id"] == departure["route_id"]:
                    route_gtfs_id = route["route_gtfs_id"]
                    break
            
            express_count = run_info.get("express_stop_count")
            if express_count == 0:
                express_note = "Stops all"
            elif express_count and express_count > 0:
                express_note = "Express"
            else:
                express_note = ""
            
            departures_list.append(
                {
                    "platform": departure.get("platform_number"),
                    "destination": destination,
                    "departure_time": departure_time,
                    "time_to_departure": time_to_departure,
                    "departure_note": departure.get("departure_note"),
                    "express_note": express_note,
                    "route_gtfs_id": route_gtfs_id,
                    "run_id": run_id,
                    "flag": departure.get("flags", ""),
                }
            )
        departures_list = self.filter_departure_list(
            departures_list,
            n_departures,
        )

        if return_next_run and departures:
            next_run = runs.get(str(departures[0]["run_id"]))
            return departures_list, next_run
        
        return departures_list

    def _get_pid_destination(self, run: dict) -> str:
        """
        Determine the PID destination for a run.

        Distributor destinations take priority over run destinations.
        """
        interchange = run.get("interchange") or {}


        distributor = interchange.get("distributor")
        if distributor and distributor.get("advertised"):
            return distributor.get("destination_name") or "Unknown"

        return run.get("destination_name", "Unknown")
    
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

    