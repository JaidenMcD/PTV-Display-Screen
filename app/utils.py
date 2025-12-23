from datetime import datetime, timezone
import pygame
from typing import Any, Dict, List, Optional, Tuple
import pytz
import os

tz = pytz.timezone(os.getenv("TIMEZONE"))
utc = pytz.utc


def parse_departure_time(
    departure: Dict[str, Any],
    now_local: datetime,
) -> Tuple[str, str]:
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

def wrap_text(text, font, width):
    """Wrap text to fit inside a given width when rendered.

    :param text: The text to be wrapped.
    :param font: The font the text will be rendered in.
    :param width: The width to wrap to.

    """
    text_lines = text.replace('\t', '    ').split('\n')
    if width is None or width == 0:
        return text_lines

    wrapped_lines = []
    for line in text_lines:
        line = line.rstrip() + ' '
        if line == ' ':
            wrapped_lines.append(line)
            continue

        # Get the leftmost space ignoring leading whitespace
        start = len(line) - len(line.lstrip())
        start = line.index(' ', start)
        while start + 1 < len(line):
            # Get the next potential splitting point
            next = line.index(' ', start + 1)
            if font.size(line[:next])[0] <= width:
                start = next
            else:
                wrapped_lines.append(line[:start])
                line = line[start+1:]
                start = line.index(' ')
        line = line[:-1]
        if line:
            wrapped_lines.append(line)
    return wrapped_lines


def get_current_time_string(format_str="%I:%M:%S %p"):
    """
    Get the current time as a formatted string.
    
    Args:
        format_str: Python datetime format string
        
    Returns:
        Formatted time string in lowercase
    """
    return datetime.now().strftime(format_str).lower()