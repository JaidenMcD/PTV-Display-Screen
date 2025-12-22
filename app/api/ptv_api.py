from hashlib import sha1
import hmac
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone
import pytz
import logging
from typing import Any, Dict, List, Optional

load_dotenv()

logger = logging.getLogger(__name__)

devId = os.getenv("USER_ID")
key = os.getenv("API_KEY")
BASE_URL = "https://timetableapi.ptv.vic.gov.au"

train_stop_id = os.getenv("TRAIN_STOP_ID")
tz = pytz.timezone(os.getenv("TIMEZONE"))
utc = pytz.utc

def getUrl(endpoint: str) -> str:
    """Generate a properly signed PTV API URL."""
    request_str = endpoint + ('&' if '?' in endpoint else '?') + f"devid={devId}"
    signature = hmac.new(key.encode(), request_str.encode(), sha1).hexdigest()
    return f"{BASE_URL}{request_str}&signature={signature}"

def send_ptv_request(endpoint: str) -> Optional[Dict[str, Any]]:
    """
    Send a GET request to the PTV API and return the JSON response.
    
    Args:
        endpoint: PTV API endpoint (e.g., "/v3/departures/...")
    
    Returns:
        Parsed JSON response or None on error
    """
    try:
        url = getUrl(endpoint)
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            logger.debug(f"PTV API request successful: {endpoint}")
            return response.json()
        else:
            logger.error(
                f"PTV API error {response.status_code}: {response.text} "
                f"(endpoint: {endpoint})"
            )
        return None

    except requests.exceptions.Timeout:
        logger.error(f"API request timeout for {endpoint}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to PTV API for {endpoint}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {endpoint}: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"Invalid JSON response from API: {str(e)}")
        return None

def get_GTFS_route_id(route_id: str) -> Optional[str]:
    """
    Fetch GTFS route ID for a given route.
    
    Args:
        route_id: PTV route ID
    
    Returns:
        GTFS route ID or None on error
    """
    endpoint = f"/v3/routes/{route_id}"
    result = send_ptv_request(endpoint)

    if result is None:
        logger.warning(f"Failed to fetch route info for route_id {route_id}")
        return None
    
    try:
        return result['route']['route_gtfs_id']
    except KeyError:
        logger.error(f"GTFS route ID not found in response for route_id {route_id}")
        return None

def get_pid_destination(run: dict) -> str:
    """
    Given a PTV 'run' object, return the PID destination.
    
    Args:
        run: Run object from PTV API
    
    Returns:
        Destination name
    """
    try:
        interchange = run.get("interchange") or {}
        distributor = interchange.get("distributor")

        # 1. Distributor takes priority for departures
        if distributor and distributor.get("advertised"):
            return distributor.get("destination_name") or "Unknown"

        # 2. If no distributor advertised, fallback to run destination
        return run.get("destination_name", "Unknown")
    except Exception as e:
        logger.error(f"Error extracting destination: {str(e)}")
        return "Unknown"


def chunk_stops(stops: List[Dict[str, Any]], chunk_size: int = 8) -> List[List[Dict[str, Any]]]:
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

def get_stops_for_run(run_id: int) -> List[Dict[str, Any]]:
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

        invalid_stops = get_invalid_stops_for_route(route_id)

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
    

def get_invalid_stops_for_route(route_id: int) -> set:
    """
    Get set of invalid stop names for a given route.
    Centralized from hardcoded logic.
    
    Args:
        route_id: PTV route ID
    
    Returns:
        Set of stop names to skip
    """
    invalid_map = {
        11: {"darling"},
        4: {"darling"},
        6: {"burnley"}
    }
    return invalid_map.get(route_id, set())


def get_pid_stops(run: dict, start_stop_id: int) -> List[Dict[str, Any]]:
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
        stops = get_stops_for_run(run["run_id"])

        if distributor and distributor.get("advertised"):
            second_leg = get_stops_for_run(distributor['run_ref'])
            stops.extend(second_leg)
        
        start_index = next(
            (i for i, stop in enumerate(stops) if stop["stop_id"] == str(start_stop_id)), 
            None
        )
        
        if start_index is None:
            logger.warning(f"Start stop {start_stop_id} not found in route")
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
        stops = chunk_stops(stops, 7)
        return stops

    except Exception as e:
        logger.error(f"Error getting PID stops: {str(e)}")
        return []
        
def searchPTVAPI(term):
    endpoint = f"/v3/search/{term}?route_types=0"
    result = send_ptv_request(endpoint)
    return result
