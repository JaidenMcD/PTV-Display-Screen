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

