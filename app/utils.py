from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pytz
import os
tz = pytz.timezone(os.getenv("TIMEZONE"))
utc = pytz.utc


def parse_departure_time(
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