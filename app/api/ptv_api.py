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
