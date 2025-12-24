from hashlib import sha1
import hmac
from dotenv import load_dotenv
import os
import requests
import logging
from typing import Any, Dict, List, Optional
import json

load_dotenv()

logger = logging.getLogger(__name__)

devId = os.getenv("USER_ID")
key = os.getenv("API_KEY")
BASE_URL = "https://timetableapi.ptv.vic.gov.au"

train_stop_id = os.getenv("TRAIN_STOP_ID")

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


def get_routes(route_type_id):
    endpoint = f'/v3/routes?route_types={route_type_id}'
    result = send_ptv_request(endpoint)
    return result

def get_stops(route_type_id):
    stops = []
    routes = get_routes(route_type_id)
    for route in routes["routes"]:
        endpoint = f"/v3/stops/route/{route["route_id"]}/route_type/{route_type_id}"
        result = send_ptv_request(endpoint)
        for stop in result["stops"]:
            stops.append(stop["stop_name"])

    # Remove duplicates
    stops = list(set(stops))

    # sort alphabetically
    stops.sort()
    return stops

def update_metropolitan_train_stops():
    stops = get_stops(0)
    file_path = 'data/Metropolitan-Train-Stops.json'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # Open the file and save the list as JSON
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            # Use 'indent=4' for pretty-printing (human-readable formatting)
            json.dump(stops, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved list to {file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")

def update_tram_stops():
    stops = get_stops(1)
    file_path = 'data/Tram-Stops.json'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # Open the file and save the list as JSON
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            # Use 'indent=4' for pretty-printing (human-readable formatting)
            json.dump(stops, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved list to {file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")

def update_bus_stops():
    stops = get_stops(2)
    file_path = 'data/Bus-Stops.json'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # Open the file and save the list as JSON
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            # Use 'indent=4' for pretty-printing (human-readable formatting)
            json.dump(stops, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved list to {file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")

update_bus_stops()


