import os
import sys
import time
import logging
import threading
from dotenv import load_dotenv
from pathlib import Path

import pygame

# Add parent directory to path for imports from server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from api import ptv_api
from data import gtfs_loader
from displays.platform import PlatformDisplay
from displays.tram_display import TramDisplay
from models.train_stop import TrainStop
from models.tram_stop import TramStop

logger = config.setup_logging()
app_dir = Path(__file__).resolve().parent

def run_display_loop(display_state):
    """
    Run the main Pygame display loop.
    Runs in a separate thread from the Flask web server.
    
    Args:
        display_state: Shared dictionary with display configuration
    """
    try:
        # Validate Environment
        try:
            config.validate_required_env_vars()
        except EnvironmentError as e:
            logger.error(str(e))
            return

        load_dotenv()

        device = int(os.getenv("DEVICE", "0"))

        if device == 1:
            # Must set these BEFORE pygame imports SDL
            os.environ["DISPLAY"] = ":0"
            os.environ["XAUTHORITY"] = "/home/admin/.Xauthority"

        pygame.init()

        if device == 1:
            screen = pygame.display.set_mode((480, 320), pygame.FULLSCREEN | pygame.NOFRAME)
            pygame.mouse.set_visible(False)
            logger.info("Running on embedded device (fullscreen)")
        else:
            screen = pygame.display.set_mode(config.SCREEN_RES)
            logger.info(f"Running in windowed mode ({config.SCREEN_RES[0]}x{config.SCREEN_RES[1]})")

        clock = pygame.time.Clock()
        running = True

        screen.fill(config.BACKGROUND_COLOR)

        # Route Colour Map (hex strings)
        try:
            colourMap = gtfs_loader.build_colour_map(str(app_dir / "data" / "gtfs_static" / "routes.txt"))
            colourMap_tram = gtfs_loader.build_tram_colour_map(str(app_dir / "data" / "gtfs_static" / "tram" / "routes.txt"))
            logger.info(f"Loaded color maps: {len(colourMap)} train routes, {len(colourMap_tram)} tram routes")
        except Exception as e:
            logger.error(f"Failed to load color maps: {str(e)}")
            colourMap = {}
            colourMap_tram = {}

        ctx_base = {
            "ptv_api": ptv_api,
            "config": config,
        }

        # Register Stops from config
        stops = {}
        displays = []

        # Use configuration from display_state
        if display_state['train_enabled'] and display_state['train_stop']:
            stops['train'] = TrainStop(display_state['train_stop'])
            displays.append(PlatformDisplay({**ctx_base, "stop": stops['train'], "colourMap": colourMap}, display_state['train_platforms']))

        if display_state['tram_enabled'] and display_state['tram_stop']:
            stops['tram'] = TramStop(display_state['tram_stop'])
            displays.append(TramDisplay({**ctx_base, "stop": stops['tram'], "colourMap": colourMap_tram}))

        if not displays:
            logger.error("No displays configured!")
            pygame.quit()
            return

        # Update display_state with display list
        display_state['display_list'] = [
            {'type': 'train', 'stop': display_state['train_stop'], 'platforms': display_state['train_platforms']}
            if display_state['train_enabled'] else None,
            {'type': 'tram', 'stop': display_state['tram_stop'], 'platforms': []}
            if display_state['tram_enabled'] else None
        ]
        display_state['display_list'] = [d for d in display_state['display_list'] if d]
        display_state['running'] = True

        active_idx = 0
        active = displays[active_idx]
        display_state['active_display'] = active_idx
        active.on_show()

        logger.info(f"Display loop started with {len(displays)} display(s)")

        # Main Loop
        frame_count = 0
        while running and display_state['running']:
            now = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    logger.info("Quit event received")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    active_idx = (active_idx + 1) % len(displays)
                    active = displays[active_idx]
                    display_state['active_display'] = active_idx
                    active.on_show()
                    logger.debug(f"Switched to display {active_idx}")
                active.handle_event(event)

            # Check if display index changed from web server
            if display_state['active_display'] != active_idx:
                active_idx = display_state['active_display']
                active = displays[active_idx]
                active.on_show()
                logger.debug(f"Display switched via web server to {active_idx}")

            try:
                active.update(now)
                active.draw(screen)
                pygame.display.flip()
            except Exception as e:
                logger.error(f"Error in display loop: {str(e)}")
                screen.fill(config.BACKGROUND_COLOR)
                pygame.display.flip()

            clock.tick(config.FPS)
            frame_count += 1

            if frame_count % 300 == 0:  # Every 5 minutes at 1 FPS
                logger.debug(f"Display loop running normally ({frame_count} frames)")

    except KeyboardInterrupt:
        logger.info("Display loop: KeyboardInterrupt received")
    except Exception as e:
        logger.critical(f"Critical error in display loop: {str(e)}", exc_info=True)
    finally:
        display_state['running'] = False
        pygame.quit()
        logger.info("Display loop closed")