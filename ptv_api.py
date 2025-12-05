from hashlib import sha1
import hmac
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone
import pytz

load_dotenv()

devId = os.getenv("USER_ID")
key = os.getenv("API_KEY")
BASE_URL = "https://timetableapi.ptv.vic.gov.au"

tram_stop_id = os.getenv("TRAM_STOP_ID")
train_stop_id = os.getenv("TRAIN_STOP_ID")
tz = pytz.timezone(os.getenv("TIMEZONE"))
utc = pytz.utc



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

def get_departures(route_type: int, stop_id: int, max_results: int = 5):
    """Fetch departures for a given route type and stop ID."""
    endpoint = f"/v3/departures/route_type/{route_type}/stop/{stop_id}?max_results={max_results}&expand=0"
    result = send_ptv_request(endpoint)
    # Parse Results
    departures_list = []
    now = datetime.now(tz)  # current local time
    for departure in result.get('departures', []):
        # Departure Time
        scheduled_time_utc = departure.get('scheduled_departure_utc', None)
        estimated_time_utc = departure.get('estimated_departure_utc', None)
        if not scheduled_time_utc and not estimated_time_utc:
            departure_time = "--:--"
            time_to_departure = "-"
        else:
            if estimated_time_utc:
                departure_time_utc = estimated_time_utc
            else:
                departure_time_utc = scheduled_time_utc
            departure_time_utc = datetime.fromisoformat(departure_time_utc.replace("Z", "+00:00"))
            departure_time_utc = departure_time_utc.replace(tzinfo=utc)
            departure_time_local = departure_time_utc.astimezone(tz)
            diff = (departure_time_local - now).total_seconds()
            if diff < 60:
                time_to_departure = "now"
            else:
                mins = int(diff // 60)
                time_to_departure = f"{mins} min"
            departure_time = departure_time_local.strftime("%I:%M%p").lower()

        # Destination Logic
        run_id = departure.get('run_id')
        run_info = result["runs"].get(str(run_id))
        destination = get_pid_destination(run_info)

        # Append to list
        departures_list.append({
            "platform": departure.get("platform_number", "0"),
            "destination": destination,
            "departure_time": departure_time,
            "time_to_departure": time_to_departure,
        })
    return departures_list
        