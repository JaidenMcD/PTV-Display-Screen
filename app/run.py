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
from displays.default_display import DefaultDisplay
from models.train_stop import TrainStop
from models.tram_stop import TramStop

from server.app import display_state as display_state

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
            colourMap_metropolitan_train = gtfs_loader.build_colour_map(str(app_dir / "data" / "gtfs_static" / "routes.txt"))
            colourMap_tram = gtfs_loader.build_tram_colour_map(str(app_dir / "data" / "gtfs_static" / "tram" / "routes.txt"))
            logger.info(f"Loaded color maps: {len(colourMap_metropolitan_train)} train routes, {len(colourMap_tram)} tram routes")
        except Exception as e:
            logger.error(f"Failed to load color maps: {str(e)}")
            colourMap_metropolitan_train = {}
            colourMap_tram = {}

        ctx_base = {
            "ptv_api": ptv_api,
            "config": config,
        }

        display = DefaultDisplay(ctx_base)
        display.on_show()
    

        display_state['running'] = True

        logger.info(f"Display loop started")

        # Main Loop
        frame_count = 0
        last_version = display_state.get('version', 0)
        while running and display_state['running']:
            now = time.time()
            print(display_state)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    logger.info("Quit event received")

            # Check if display_state has changed
            if display_state.get('version', 0) != last_version:
                logger.info(f'Display state changed')
                if display_state['transit_type'] == 'Metropolitan-Train':
                    stop = TrainStop(display_state['stop'], display_state['train_platforms'])
                    if display_state['display_type'] == 'platform':
                        display = PlatformDisplay({**ctx_base, "stop": stop, "colourMap": colourMap_metropolitan_train}, display_state['train_platforms'])
                        display.on_show()

                elif display_state['transit_type'] == 'Tram':
                    stop = TramStop(display_state['stop'])
                    if display_state['display_type'] == 'tram_display':
                        display = TramDisplay({**ctx_base, "stop": stop, "colourMap": colourMap_tram})
                        display.on_show()
                else: 
                    display = DefaultDisplay(ctx_base)
                    display.on_show()
                
                last_version = display_state['version']

            try:
                display.update(now)
                display.draw(screen)
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