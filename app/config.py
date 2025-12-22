import logging
import logging.handlers
import os
import pytz
from pathlib import Path

# --- DO NOT CHANGE THESE VALUES ---
BACKGROUND_COLOR = (0, 0, 0)
FPS = 1


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
NETWORK_GREY = (51, 52, 52)
MID_GREY = (112, 115, 114)
LIGHT_WARM_GREY = (215, 210, 203)

SCREEN_RES = (480, 320)   # display resolution


# PTV API Values
route_type_train = 0
route_type_tram = 1
route_type_bus = 2
route_type_vline = 3

# Tram Alert Mappings
tram_alert_mappings = {
    "SpecialEvent": {
        "header": "Special Event Services",
        "icon_path": "assets/icons/special-event-info.png",
    }
}

# --------- LOGGING CONFIG ----------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "ptv_display.log"

def setup_logging(level=logging.INFO):
    """
    Configure logging with both file and console handlers.
    
    Args:
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("ptv_display")
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler (rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# ----- CONFIG VALIDATION -----
def validate_required_env_vars():
    """
    Validate that all required environment variables are set.
    
    Raises:
        EnvironmentError: If any required var is missing
    """
    required_vars = {
        "USER_ID": "PTV API Developer ID",
        "API_KEY": "PTV API Key",
        "TIMEZONE": "Local timezone (e.g., 'Australia/Melbourne')"
    }

    missing = []
    invalid = []

    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({desc})")

    # validate timezone
    tz_str = os.getenv("TIMEZONE")
    if tz_str:
        try:
            pytz.timezone(tz_str)
        except pytz.exceptions.UnknownTimeZoneError:
            invalid.append(f"TIMEZONE='{tz_str}' is not a valid timezone")

    if missing or invalid:
        error_msg = "Missing or invalid environment variables:\n"
        if missing:
            error_msg += "Missing: " + ", ".join(missing) + "\n"
        if invalid:
            error_msg += "Invalid: " + ", ".join(invalid)
        raise EnvironmentError(error_msg)

# Initialize logging at module load
logger = setup_logging()