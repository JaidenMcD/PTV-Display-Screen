import os
import time
import logging
from dotenv import load_dotenv

import pygame

import config
from api import ptv_api
from data import gtfs_loader
from displays.platform import PlatformDisplay  # keep filename as-is; rename when convenient
from displays.altdisplay import AltDisplay
from displays.tram_display import TramDisplay
from models.train_stop import TrainStop
from models.tram_stop import TramStop

logger = config.setup_logging()

# Validate Enviroment
try:
    config.validate_required_env_vars()
except EnvironmentError as e:
    logger.error(str(e))
    exit(1)

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

info = pygame.display.Info()

clock = pygame.time.Clock()
running = True

screen.fill(config.BACKGROUND_COLOR)

# Route Colour Map (hex strings)
try:
    colourMap = gtfs_loader.build_colour_map("data/gtfs_static/routes.txt")
    colourMap_tram = gtfs_loader.build_tram_colour_map("data/gtfs_static/tram/routes.txt")
    logger.info(f"Loaded color maps: {len(colourMap)} train routes, {len(colourMap_tram)} tram routes")
except Exception as e:
    logger.error(f"Failed to load color maps: {str(e)}")
    colourMap = {}
    colourMap_tram = {}

# Fonts
f_destination_large = pygame.font.Font("assets/fonts/NETWORKSANS-2019-BOLD.TTF", 27)
f_destination_small = pygame.font.Font("assets/fonts/NETWORKSANS-2019-BOLD.TTF", 14)
f_depTime_small = pygame.font.Font("assets/fonts/NETWORKSANS-2019-MEDIUM.TTF", 14)
f_stopsList = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 12)

f_bold_25 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-BOLD.TTF", 25)
f_bold_27 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-BOLD.TTF", 27)

f_med_12 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-MEDIUM.TTF", 12)
f_med_14 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-MEDIUM.TTF", 14)
f_reg_21 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-MEDIUM.TTF", 21)
f_med_22 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-MEDIUM.TTF", 22)

f_reg_9 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 9)
f_reg_10 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 10)
f_reg_12 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 12)
f_reg_13 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 13)
f_reg_15 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 15)
f_reg_23 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 23)
f_reg_35 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 35)

ctx_base = {
    "ptv_api": ptv_api,
    "config": config,
    "fonts": {
        "dest_large": f_destination_large,
        "dest_small": f_destination_small,
        "dep_small": f_depTime_small,
        "stops": f_stopsList,

        "f_bold_25": f_bold_25,
        "f_bold_27": f_bold_27,

        "f_med_12": f_med_12,
        "f_med_14": f_med_14,
        "f_reg_21": f_reg_21,
        "f_med_22":  f_med_22,

        "f_reg_9":  f_reg_9,
        "f_reg_10": f_reg_10,
        "f_reg_12":  f_reg_12,
        "f_reg_13": f_reg_13,
        "f_reg_15":  f_reg_15,
        "f_reg_23": f_reg_23,
        "f_reg_35": f_reg_35,
    },
}

# Register Stops from config
stops = {}
displays = []

# Prompt user for transit types AND locations
tram_enabled = input("Enable trams? (y/n): ").lower() == 'y'
train_enabled = input("Enable trains? (y/n): ").lower() == 'y'
#bus_enabled = input("Enable buses? (y/n): ").lower() == 'y'

if train_enabled:
    search_term = input("Enter train station: ")
    platforms = input("Comma separated platforms (or Enter for all): ").split(',')
    stops['train'] = TrainStop(search_term)
    displays.append(PlatformDisplay({**ctx_base, "stop": stops['train'], "colourMap": colourMap}, platforms))

if tram_enabled:
    search_term = input("Enter tram stop: ")
    stops['tram'] = TramStop(search_term)
    displays.append(TramDisplay({**ctx_base, "stop": stops['tram'], "colourMap": colourMap_tram}))
"""
if bus_enabled:
    search_term = input("Enter bus stop: ")
    stops['bus'] = BusStop(search_term)
    displays.append(BusDisplay({**ctx, "stop": stops['bus']}))
"""

active_idx = 0
active = displays[active_idx]
active.on_show()

logger.info(f"Application started with {len(displays)} display(s)")

# Main Loop
frame_count = 0
while running:
    now = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            logger.info("Quit event received")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            active_idx = (active_idx + 1) % len(displays)
            active = displays[active_idx]
            active.on_show()
            logger.debug(f"Switched to display {active_idx}")
        active.handle_event(event)

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
        logger.debug(f"Application running normally ({frame_count} frames)")

pygame.quit()
logger.info("Application closed")