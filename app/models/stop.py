from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from api.ptv_api import send_ptv_request
from models.route import Route
from utils import parse_departure_time
from datetime import datetime
import pytz
import os
import re

tz = pytz.timezone(os.getenv("TIMEZONE"))


class Stop:
    def __init__(self, name: str, platforms: List[str]):
        self.platforms = platforms
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

    # Resolve stop ID using provided name
    def resolve_stop(self):
        print(f'Resolving stop for input name: {self._input_name}...')
        # Format input
        raw_name = self._input_name.strip()
        query_name = raw_name.replace(' ', '%20')
        endpoint = f"/v3/search/{query_name}?route_types=0"
        result = send_ptv_request(endpoint)

        target = self.normalise(raw_name)
        scored = [
            (self.score_stop(c,target), c)
            for c in result["stops"]
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, stop = scored[0] if scored else (0, None)
        if best_score == 0:
            print("NO GOOD STOP FOUND --------------------------")
            exit()

        self._input_name = None  # discard after use
        
        print(f"Found stop {stop['stop_name']} [{stop['stop_id']}] with a score of {best_score}")

        # Filling metadata
        self.name = stop['stop_name']
        self.stop_id = stop['stop_id']
        self.routes = stop['routes']
        self.stop_suburb = stop['stop_suburb']
        self.route_type = stop['route_type']
        self.stop_latitude = stop['stop_latitude']
        self.stop_longitude = stop['stop_longitude']
        self.stop_sequence = stop['stop_sequence']
        self.stop_landmark = stop['stop_landmark']

    def get_next_departures(self, n_departures, return_next_run = False):
        platform_str = ''
        if self.platforms != ['']:
            for platform_no in self.platforms:
                platform_str = platform_str + f'&platform_numbers={platform_no}'

        endpoint = (
            f"/v3/departures/route_type/0/stop/{self.stop_id}"
            f"?max_results={n_departures}&expand=0&include_skipped_stops=true"
            f"{platform_str}"
        )
        result = send_ptv_request(endpoint)
        if not result:
            return []

        departures = result.get("departures", [])
        runs = result.get("runs", {}) or {}
        
        # Parse Results
        departures_list: List[Dict[str, Any]] = []
        now_local = datetime.now(tz)

        for departure in departures:
            departure_time, time_to_departure = parse_departure_time(
                departure=departure,
                now_local=now_local,
            )

            run_id = departure.get("run_id")
            run_info = runs.get(str(run_id)) if run_id is not None else None
            destination = self._get_pid_destination(run_info or {})
            for route in self.routes:
                if route['route_id'] == departure['route_id']:
                    route_gtfs_id = route['route_gtfs_id']
            
            run_info = runs[str(run_id)]
            if run_info['express_stop_count'] == 0:
                express_note = 'Stops all'
            elif run_info['express_stop_count'] > 0:
                express_note = 'Express'
            else:
                express_note = ''
            departures_list.append(
                {
                    "platform": departure.get("platform_number", "0") or "0",
                    "destination": destination,
                    "departure_time": departure_time,
                    "time_to_departure": time_to_departure,
                    "departure_note": departure["departure_note"],
                    "express_note": express_note,
                    "route_gtfs_id": route_gtfs_id,
                    "run_id": departure['run_id']
                }
            )
        if return_next_run:
            next_run = result['runs'][str(departures[0]['run_id'])]
            return departures_list, next_run
        else:
            return departures_list

    def _get_pid_destination(self, run: dict) -> str:
        """
        Given a PTV 'run' object, return the PID destination.
        """
        interchange = run.get("interchange") or {}

        distributor = interchange.get("distributor")
        feeder = interchange.get("feeder")

        # 1. Distributor takes priority for departures
        if distributor and distributor.get("advertised"):
            return distributor.get("destination_name") or "Unknown"

        # 2. If no distributor advertised, fallback to run destination
        return run.get("destination_name", "Unknown")
    

    def normalise(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"[^\w\s]", "", s)  # remove punctuation
        s = re.sub(r"\s+", " ", s)     # collapse spaces
        return s.strip()
    

    """ Stop Matching Funct """
    def score_stop(self, stop, target_name, target_suburb=None):
        name = self.normalise(stop["stop_name"])
        score = 0

        if name == target_name:
            score += 100
        elif name.startswith(target_name):
            score += 70
        elif target_name in name:
            score += 40
        
        if target_suburb and stop["stop_suburb"]:
            if stop["stop_suburb"].lower() == target_suburb.lower():
                score += 20
        
        return score

    