
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import re
import logging

import pytz

from api.ptv_api import send_ptv_request
from utils import parse_departure_time
import config

logger = logging.getLogger("ptv_display")
tz = pytz.timezone(os.getenv("TIMEZONE"))


class TrainStop:
    """
    Represents a PTV metro train stop and provides departure lookup functionality.
    """
    def __init__(self, stop_id, platforms: Optional[List[str]] = None):
        """
        Initialise a Stop object and resolve it against the PTV API.

        :param name: User-provided stop name
        :param platforms: List of platform numbers to filter departures
        """

        # Validate and clean platforms
        if platforms:
            self.platform = [str(p).strip() for p in platforms if p.strip()]
        else:
            self.platform = None

        # Core stop metadata (important)
        self.stop_id = stop_id
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
        logger.info(f'Resolving stop for stop ID: {self.stop_id}...')
        try:

            # Resolve Metro
            endpoint = (
                f"/v3/stops/{self.stop_id}/route_type/0"
                f"?stop_location=true&stop_amenities=true&stop_accessibility=true"
                f"&stop_contact=true&stop_ticket=true&stop_staffing=true&stop_disruptions=true"
            )
            result = send_ptv_request(endpoint)
            train_stop = result.get("stop")

            # Populate Metadata
            self.route_type = train_stop['route_type']
            self.name = train_stop['stop_name']
            self.routes = train_stop['routes']
            self.stop_suburb = train_stop["stop_location"]["suburb"]
            self.stop_latitude = train_stop["stop_location"]["gps"]['latitude']
            self.stop_longitude = train_stop["stop_location"]["gps"]['longitude']
            self.stop_landmark = train_stop['stop_landmark']
        
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error resolving stop: {str(e)}")
            raise

    def get_next_departures(self,
                            n_departures: int,
                            platform = None,
                            return_next_run: bool = False
    ):
        """
        Retrieve upcoming departures for this stop.

        :param n_departures: Number of departures to return
        :param return_next_run: Whether to return the full run object
        :return: List of departure dictionaries (optionally plus next run)
        """
        platform_str = ""
        if platform and platform != ['']:
            for platform_no in platform:
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
            return [], []

        departures = result.get("departures", [])[:n_departures]
        runs = result.get("runs", {}) or {}
        
        if departures == []:
            return [], []
        
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
        
        return departures_list, []

    def get_pid_stops(self, run: dict) -> List[Dict[str, Any]]:
        """
        Get stops for a PID display (with interchange logic).
        
        Args:
            run: Run object from PTV API
            start_stop_id: Current stop ID
        
        Returns:
            List of stops to display
        """
        try:
            interchange = run.get("interchange") or {}
            distributor = interchange.get("distributor")
            stops = self._get_stops_for_run(run["run_id"])

            if distributor and distributor.get("advertised"):
                second_leg = self._get_stops_for_run(distributor['run_ref'])
                stops.extend(second_leg)
            
            start_index = next(
                (i for i, stop in enumerate(stops) if stop["stop_id"] == str(self.stop_id)), 
                None
            )
            
            if start_index is None:
                logger.warning(f"Start stop {self.stop_id} not found in route")
                return stops[:8]  # Return first 8 if start not found
            
            # remove duplicates
            stops = stops[start_index:]
            seen_ids = set()
            unique_stops = []
            for stop in stops:
                stop_id = stop["stop_id"]
                if stop_id not in seen_ids:
                    unique_stops.append(stop)
                    seen_ids.add(stop_id)
            stops = unique_stops

            stops[-1]["is_terminus"] = True
            stops = self._chunk_stops(stops, 7)
            return stops

        except Exception as e:
            logger.error(f"Error getting PID stops: {str(e)}")
            return []
    
    def _chunk_stops(self, stops: List[Dict[str, Any]], chunk_size: int = 8) -> List[List[Dict[str, Any]]]:
        """
        Split stops into chunks of `chunk_size`.
        Pads with empty entries to ensure all chunks have exactly `chunk_size` elements.
        
        Args:
            stops: List of stop dictionaries
            chunk_size: Size of each chunk
        
        Returns:
            List of chunked stop lists
        """
        chunks = []
        empty_stop = {
            "name": "",
            "is_skipped": False,
            "is_terminus": False,
            "stop_id": None
        }

        for i in range(0, len(stops), chunk_size):
            chunk = stops[i:i + chunk_size]
            while len(chunk) < chunk_size:
                chunk.append(empty_stop.copy())
            chunks.append(chunk)

        return chunks
        
    def _get_stops_for_run(self, run_id: int) -> List[Dict[str, Any]]:
        """
        Return ordered list of stop dicts with keys: name, is_skipped, is_terminus, stop_id
        
        Args:
            run_id: PTV run ID
        
        Returns:
            List of stops in order for this run
        """
        """Return ordered list of stop dicts with keys: name, is_skipped, is_terminus, stop_id"""
        endpoint = (
            f"/v3/pattern/run/{run_id}/route_type/0"
            f"?expand=0&include_skipped_stops=true"
        )
        result = send_ptv_request(endpoint)

        if not result:
            logger.warning(f"No pattern data for run {run_id}")
            return []
        
        try:
            stops_dict = result.get("stops", {})
            departures = result.get("departures", [])

            if not departures:
                logger.warning(f"No departures found for run {run_id}")
                return []
            
            route_id = departures[0]["route_id"]

            invalid_stops = self._get_invalid_stops_for_route(route_id)

            departures = sorted(departures, key=lambda d: d["departure_sequence"])

            output = []
            for dep in departures:
                stop_id = str(dep["stop_id"])
                stop_info = stops_dict.get(stop_id)

                if stop_info:
                    name = stop_info["stop_name"]
                    name = name.replace(" Station", "")
                    if name not in invalid_stops:
                        output.append({
                            "name": name,
                            "is_skipped": False,
                            "is_terminus": False,
                            "stop_id": stop_id
                        })

                skipped_list = dep.get("skipped_stops", [])
                for skipped in skipped_list:
                    stop_name = skipped["stop_name"]
                    stop_name = stop_name.replace(" Station", "")
                    if stop_name not in invalid_stops:
                        output.append({
                            "name": stop_name,
                            "is_skipped": True,
                            "is_terminus": False,
                            "stop_id": skipped["stop_id"]
                        })
            
            logger.debug(f"Retrieved {len(output)} stops for run {run_id}")
            return output
        
        except Exception as e:
            logger.error(f"Error processing stops for run {run_id}: {str(e)}")
            return []
    
    def _get_invalid_stops_for_route(self, route_id: int) -> set:
        """
        Get set of invalid stop names for a given route.
        
        These are stops that appear in the API response but shouldn't be
        displayed (e.g., duplicate entries, test stops, or API anomalies).
        
        Known issues:
        - Route 11: "Darling" appears as phantom stop
        - Route 4: "Darling" appears as phantom stop
        - Route 6: "Burnley" appears as phantom stop
        
        Args:
            route_id: PTV route ID
        
        Returns:
            Set of stop names to filter out
        """
        invalid_map = {
            11: {"darling"},
            4: {"darling"},
            6: {"burnley"}
        }
        return invalid_map.get(route_id, set())

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
        target_suburb: Optional[str] = None,
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
        departures: List[Optional[Dict[str, Any]]],
        n_to_show: int,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Remove RRB services and pad the list with None up to n_to_show.
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

    