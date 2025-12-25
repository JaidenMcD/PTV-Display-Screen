#!/usr/bin/env python3
"""
PTV Display Screen - Main Entry Point
Starts both the web server and the display in separate threads.
"""

import os
import sys
import threading
import time
import logging
import signal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ptv_display_main')

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Global flag for shutdown
shutdown_event = threading.Event()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    logger.info("Shutdown signal received (Ctrl+C)")
    shutdown_event.set()

def get_display_config():
    """
    Return default display_state - controlled via webpage only.
    """
    display_state = {
        'stop': False,
        'transit_type': False,
        'display_type': 'default_display',
        'train_platforms': [],
        'running': False,
        'version': 0,
    }
    
    logger.info("Display state initialized - awaiting webpage control")
    return display_state

def start_flask_server(display_state):
    """Start Flask web server in a separate thread."""
    try:
        from server.app import app
        
        # Share the display_state with Flask app
        import server.app as server_app
        server_app.display_state = display_state
        
        logger.info("Starting Flask web server on http://0.0.0.0:5000")
        
        # Run Flask with threading enabled
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False,
            threaded=True
        )
    except ImportError as e:
        logger.error(f"Failed to import Flask server: {e}")
        logger.error("Make sure Flask is installed: pip install -r requirements.txt")
    except Exception as e:
        logger.critical(f"Flask server error: {e}", exc_info=True)
    finally:
        shutdown_event.set()

def start_display_loop(display_state):
    """Start display loop in a separate thread."""
    try:
        from app.run import run_display_loop
        logger.info("Starting display loop")
        run_display_loop(display_state)
    except ImportError as e:
        logger.error(f"Failed to import display loop: {e}")
    except Exception as e:
        logger.critical(f"Display loop error: {e}", exc_info=True)
    finally:
        shutdown_event.set()

def main():
    """Main entry point."""
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("PTV Display Screen initializing...")
    
    # Get display configuration
    display_state = get_display_config()
    if not display_state:
        logger.error("Configuration failed")
        sys.exit(1)
    
    # Create threads as daemons so they exit when main exits
    flask_thread = threading.Thread(target=start_flask_server, args=(display_state,), daemon=True)
    display_thread = threading.Thread(target=start_display_loop, args=(display_state,), daemon=True)
    
    try:
        logger.info("Starting application threads...")
        flask_thread.start()
        time.sleep(1)  # Give Flask a moment to start
        display_thread.start()
        
        logger.info("All threads started successfully")
        logger.info("Web interface available at http://localhost:5000")
        logger.info("Press Ctrl+C to stop the application")
        
        # Wait for shutdown signal
        while not shutdown_event.is_set():
            time.sleep(0.5)
        
        # Signal threads to stop
        display_state['running'] = False
        
        # Wait for threads to finish (with timeout)
        logger.info("Waiting for threads to shut down...")
        flask_thread.join(timeout=3)
        display_thread.join(timeout=3)
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        display_state['running'] = False
        logger.info("Application closed")
        sys.exit(0)

if __name__ == '__main__':
    main()