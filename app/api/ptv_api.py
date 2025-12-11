from hashlib import sha1
import hmac
from dotenv import load_dotenv
import os
import requests
import requests_cache
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
cache_name = os.getenv("PTV_CACHE_NAME", "ptv_cache")
try:
    cache_expire_seconds = int(os.getenv("PTV_CACHE_SECONDS", "30"))
except ValueError:
    cache_expire_seconds = 30
cache_disabled = os.getenv("PTV_CACHE_DISABLED", "false").lower() in ("1", "true", "yes")
session = (
    requests.Session()
    if cache_disabled
    else requests_cache.CachedSession(
        cache_name=cache_name,
        backend="sqlite",
        expire_after=cache_expire_seconds,
        allowable_methods=("GET",),
        allowable_codes=(200,),
    )
)


def getUrl(endpoint: str) -> str:
    """Generate a properly signed PTV API URL."""
    request_str = endpoint + ('&' if '?' in endpoint else '?') + f"devid={devId}"
    signature = hmac.new(key.encode(), request_str.encode(), sha1).hexdigest()
    return f"{BASE_URL}{request_str}&signature={signature}"

def send_ptv_request(endpoint: str):
    """Send a GET request to the PTV API and return the JSON response."""
    url = getUrl(endpoint)
    response = session.get(url)
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


def get_stops_for_run(run_id: int, route_type: int):
    """Return ordered list: [[name, is_skipped], ...] including express stops."""
    endpoint = (
        f"/v3/pattern/run/{run_id}/route_type/{route_type}"
        f"?expand=0&include_skipped_stops=true"
    )
    result = send_ptv_request(endpoint)

    if not result:
        return []

    stops_dict = result.get("stops", {})
    departures = result.get("departures", [])
    route_id = departures[0]["route_id"] if departures else None
    def is_invalid_stop(stop_name):
        if route_id == 11 and stop_name.lower() == "darling station":
            return True
        elif route_id == 6 and stop_name.lower() == "burnley station":
            return True
        return False
    # Sort departures by correct order
    departures = sorted(departures, key=lambda d: d["departure_sequence"])
    # Determine first + last actual stops (termini for this run)
    first_stop_id = str(departures[0]["stop_id"]) if departures else None
    last_stop_id = str(departures[-1]["stop_id"]) if departures else None
    output = []
    found = False

    for dep in departures:
        stop_id = str(dep["stop_id"])

        # Start once we reach *your current train stop*
        if stop_id == str(train_stop_id):
            found = True

        if not found:
            continue
        skipped_list = dep.get("skipped_stops", [])
        for skipped in skipped_list:
            stop_name = skipped["stop_name"]

            # Apply the Darling filter
            if not is_invalid_stop(stop_name):
                output.append([stop_name, True, False])


        stop_info = stops_dict.get(stop_id)
        if stop_info:
            name = stop_info["stop_name"]

            if not is_invalid_stop(name):
                is_terminus = (stop_id == first_stop_id) or (stop_id == last_stop_id)
                output.append([name, False, is_terminus])
    
     # --------- Chunk into groups of 8 ----------
    chunk_size = 8
    chunks = []

    for i in range(0, len(output), chunk_size):
        chunks.append(output[i:i + chunk_size])

    return chunks

def get_departures(stop_id: int, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch and parse upcoming departures for a given metro train stop ID

    This function requests departure data from the PTV API, converts the 
    scheduled/estimated UTC times to local time, derives a countdown label 
    (e.g., "now", "3 min"), determines the PID-frienly destination, and
    attaches the GTFS route ID for styling or downstream logic.

    Args:
        stop_id: PTV stop ID to fetch departures for.
        max_results: Maximum number of departures to request
    
    Returns:
        A list of dictionaries, each containing:
            - platform: Platform number as a string (default "0").
            - destination: PID destination string
            - departure_time: Local time formatted like "07:35pm" or "--:--"
            - time_to_departure: Countdown string like "now", "5 min", or "-".
            - run_id: Run ID integer or None.
            - route_id: Route ID integer.
            - GTFS_id: GTFS route ID string.
    
    Notes:
        - Uses `estimated_departure_utc` when available; otherwise falls back 
          to `scheduled_departure_utc`.
        - If the API request fails or returns no usable data, returns an empty list.
        - Relies on global `tz`, `utc`, and helper functions:
          `send_ptv_request`, `get_pid_destination`, `get_GTFS_route_id`.
    
    """
    endpoint = (
        f"/v3/departures/route_type/0/stop/{stop_id}"
        f"?max_results={max_results}&expand=0&include_skipped_stops=true"
    )

    logger.debug(f"Fetching next {max_results} departures for stop_id={stop_id}")
    result = send_ptv_request(endpoint)

    if not result:
        return []

    departures = result.get("departures", [])
    runs = result.get("runs", {}) or {}

    # Parse Results
    departures_list: List[Dict[str, Any]] = []
    now_local = datetime.now(tz)

    for departure in departures:
        departure_time, time_to_departure = _parse_departure_time(
            departure=departure,
            now_local=now_local,
        )

        run_id = departure.get("run_id")
        run_info = runs.get(str(run_id)) if run_id is not None else None
        destination = get_pid_destination(run_info or {})

        route_id = departure.get("route_id")
        gtfs_id = get_GTFS_route_id(route_id) if route_id is not None else None

        departures_list.append(
            {
                "platform": departure.get("platform_number", "0") or "0",
                "destination": destination,
                "departure_time": departure_time,
                "time_to_departure": time_to_departure,
                "run_id": run_id,
                "route_id": route_id,
                "GTFS_id": gtfs_id,
                "departure_note": departure["departure_note"]
            }
        )

    return departures_list


def _parse_departure_time(
    departure: Dict[str, Any],
    now_local: datetime,
) -> (str, str):
    """
    Convert a departure's UTC time fields into local display strings.

    Args:
        departure: A single departure dict from the PTV API.
        now_local: The current local time for countdown calculations.

    Returns:
        A tuple of:
            (departure_time_str, time_to_departure_str)
    """
    scheduled_utc_str: Optional[str] = departure.get("scheduled_departure_utc")
    estimated_utc_str: Optional[str] = departure.get("estimated_departure_utc")

    if not scheduled_utc_str and not estimated_utc_str:
        return "--:--", "-"

    # Prefer estimated time when present.
    departure_utc_str = estimated_utc_str or scheduled_utc_str

    # Parse ISO string and normalize to UTC tz-aware datetime.
    departure_utc = datetime.fromisoformat(departure_utc_str.replace("Z", "+00:00"))
    departure_utc = departure_utc.replace(tzinfo=utc)

    # Convert to local timezone.
    departure_local = departure_utc.astimezone(tz)

    # Compute countdown label.
    diff_seconds = (departure_local - now_local).total_seconds()

    if diff_seconds < 60:
        time_to_departure = "now"
    else:
        mins = int(diff_seconds // 60)
        time_to_departure = f"{mins} min"

    departure_time = departure_local.strftime("%I:%M%p").lower()
    return departure_time, time_to_departure
        
def searchPTVAPI(term):
    endpoint = f"/v3/search/{term}?route_types=0"
    result = send_ptv_request(endpoint)
    return result
