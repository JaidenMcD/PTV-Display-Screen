from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from api.ptv_api import send_ptv_request
from models.route import Route
from utils import parse_departure_time
from datetime import datetime
import pytz
import os

tz = pytz.timezone(os.getenv("TIMEZONE"))


@dataclass
class Stop:
    # Temp unstored input arg
    _input_name: str = field(default=None, repr=False)

    # Core stop metadata (important)
    stop_id: int = field(init=False)
    name: Optional[str] = None
    routes: list = field(default_factory=list)

    # Core stop metadata (unimportant)
    stop_suburb: Optional[str] = None
    route_type: Optional[int] = None
    stop_latitude: Optional[str] = None
    stop_longitude: Optional[str] = None
    stop_sequence: Optional[int] = None
    stop_landmark: Optional[str] = None

    # Non-metadata
    stop_id_gtfs: Optional[int] = None

    # Resolve stop ID using provided name
    def __post_init__(self):
        endpoint = f"/v3/search/{self._input_name}?route_types=0"
        result = send_ptv_request(endpoint)
        stop = None
        for stop_candidate in result['stops']:
            if self._input_name in stop_candidate['stop_name']:
                stop = stop_candidate
                break
                
        if stop is None:
            print("NO STOP FOUND --------------------------")
            exit()
        self._input_name = None  # discard after use
        
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
    
    def get_next_departures(self, n_departures, return_next_run = False, platform = None):
        platform_str = ''
        if type(platform) == type([]):
            for platform_no in platform:
                platform_str = platform_str + f'&platform_numbers={platform_no}'
        elif platform is not None:
            platform_str = f'&platform_numbers={platform}'

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
    def get_gtfs_id(self):
        return
