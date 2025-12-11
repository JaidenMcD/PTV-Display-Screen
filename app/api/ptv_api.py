from hashlib import sha1
import hmac
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone
import pytz
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

load_dotenv()

devId = os.getenv("USER_ID")
key = os.getenv("API_KEY")
BASE_URL = "https://timetableapi.ptv.vic.gov.au"

train_stop_id = os.getenv("TRAIN_STOP_ID")
tz = pytz.timezone(os.getenv("TIMEZONE"))
utc = pytz.utc
# Cache PTV GET requests to reduce API calls; disable via PTV_CACHE_DISABLED=1

def getUrl(endpoint: str) -> str:
    """Generate a properly signed PTV API URL."""
    request_str = endpoint + ('&' if '?' in endpoint else '?') + f"devid={devId}"
    signature = hmac.new(key.encode(), request_str.encode(), sha1).hexdigest()
    return f"{BASE_URL}{request_str}&signature={signature}"

def send_ptv_request(endpoint: str):
    """Send a GET request to the PTV API and return the JSON response."""
    url = getUrl(endpoint)
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def get_GTFS_route_id(route_id):
    endpoint = f"/v3/routes/{route_id}"
    result = send_ptv_request(endpoint)
    return result['route']['route_gtfs_id']

def get_pid_destination(run: dict) -> str:
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


def chunk_stops(stops):
    # --------- Chunk into groups of 8 ----------
    chunk_size = 8
    chunks = []

    for i in range(0, len(stops), chunk_size):
        chunks.append(stops[i:i + chunk_size])
    return chunks

def get_stops_for_run(run_id):
    """Return ordered list: [[name, is_skipped], ...] including express stops."""
    endpoint = (
        f"/v3/pattern/run/{run_id}/route_type/0"
        f"?expand=0&include_skipped_stops=true"
    )
    result = send_ptv_request(endpoint)

    if not result:
        return []
    
    stops_dict = result.get("stops", {})
    departures = result.get("departures", [])
    route_id = departures[0]["route_id"] if departures else None
    def is_invalid_stop(stop_name):
        if route_id == 11 and stop_name.lower() == "darling":
            return True
        elif route_id == 6 and stop_name.lower() == "burnley":
            return True
        return False
    # Sort departures by correct order
    departures = sorted(departures, key=lambda d: d["departure_sequence"])
    # Determine first + last actual stops (termini for this run)
    first_stop_id = str(departures[0]["stop_id"]) if departures else None
    last_stop_id = str(departures[-1]["stop_id"]) if departures else None
    output = []
    for dep in departures:
        stop_id = str(dep["stop_id"])
        stop_info = stops_dict.get(stop_id)

        if stop_info:
            name = stop_info["stop_name"]
            name = name.replace(" Station", "")
            if not is_invalid_stop(name):
                output.append([name, False, False, stop_id])

        skipped_list = dep.get("skipped_stops", [])
        for skipped in skipped_list:
            stop_name = skipped["stop_name"]
            stop_name = stop_name.replace(" Station", "")
            if not is_invalid_stop(stop_name):
                output.append([stop_name, True, False, skipped["stop_id"]])


        
        

    return output

def get_pid_stops(run, start_stop_id):
    interchange = run.get("interchange") or {}
    distributor = interchange.get("distributor")
    stops = get_stops_for_run(run["run_id"])

    # 1. Distributor takes priority for departures
    if distributor and distributor.get("advertised"):
        second_leg = get_stops_for_run(distributor['run_ref'])
        stops.extend(second_leg)

    # Find the index of the start_stop_id
    start_index = next((i for i, stop in enumerate(stops) if stop[3] == str(start_stop_id)), None)
    stops = stops[start_index:]
    # remove duplicates
    seen_ids = set()
    unique_stops = []
    for stop in stops:
        stop_id = stop[3]
        if stop_id not in seen_ids:
            unique_stops.append(stop)
            seen_ids.add(stop_id)
    stops = unique_stops

    stops[-1][2] = True
    stops = chunk_stops(stops)
    return stops
        
def searchPTVAPI(term):
    endpoint = f"/v3/search/{term}?route_types=0"
    result = send_ptv_request(endpoint)
    return result
