import os
import time
from dotenv import load_dotenv

import pygame

import config
from api import ptv_api
from data import gtfs_loader
from displays.platform import PlatformDisplay  # keep filename as-is; rename when convenient
from displays.altdisplay import AltDisplay
from models.stop import Stop

load_dotenv()
device = int(os.getenv("DEVICE", "0"))

# Register Stop
search_term = input("Enter station: ")
platforms = input("Comma seperated platforms to show (skip with 'enter' for all): ")
platforms = platforms.split(',')
print(platforms)
stop = Stop(search_term, platforms)



if device == 1:
    # Must set these BEFORE pygame imports SDL
    os.environ["DISPLAY"] = ":0"
    os.environ["XAUTHORITY"] = "/home/admin/.Xauthority"
    os.environ["PYGAME_DETECT_AVX2"] = 1 

pygame.init()

if device == 1:
    screen = pygame.display.set_mode((480, 320), pygame.FULLSCREEN | pygame.NOFRAME)
    # Hide the mouse cursor
    pygame.mouse.set_visible(False)
else:
    screen = pygame.display.set_mode(config.SCREEN_RES)


info = pygame.display.Info()

clock = pygame.time.Clock()
running = True

screen.fill(config.BACKGROUND_COLOR)

# Route Colour Map (hex strings)
colourMap = gtfs_loader.build_colour_map("data/gtfs_static/routes.txt")

# Fonts
f_platformNumber_large = pygame.font.Font("assets/fonts/NETWORKSANS-2019-BOLD.TTF", 25)
f_platformNumber_small = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 13)
f_destination_large = pygame.font.Font("assets/fonts/NETWORKSANS-2019-BOLD.TTF", 27)
f_destination_small = pygame.font.Font("assets/fonts/NETWORKSANS-2019-BOLD.TTF", 14)
f_depTime_large = pygame.font.Font("assets/fonts/NETWORKSANS-2019-MEDIUM.TTF", 24)
f_depTime_small = pygame.font.Font("assets/fonts/NETWORKSANS-2019-MEDIUM.TTF", 14)
f_timeToDep_large = pygame.font.Font("assets/fonts/NETWORKSANS-2019-MEDIUM.TTF", 24)
f_timeToDep_small = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 13)
f_stopsList = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 12)
f_currentTime = pygame.font.Font("assets/fonts/NETWORKSANS-2019-MEDIUM.TTF", 15)
f_reg_15 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 15)
f_reg_10 = pygame.font.Font("assets/fonts/NETWORKSANS-2019-REGULAR.TTF", 10)

ctx = {
    "stop": stop,
    "ptv_api": ptv_api,
    "config": config,
    "train_stop_id": stop.stop_id,
    "colourMap": colourMap,
    "fonts": {
        "platform_large": f_platformNumber_large,
        "platform_small": f_platformNumber_small,
        "dest_large": f_destination_large,
        "dest_small": f_destination_small,
        "dep_large": f_depTime_large,
        "dep_small": f_depTime_small,
        "ttd_large": f_timeToDep_large,
        "ttd_small": f_timeToDep_small,
        "stops": f_stopsList,
        "clock": f_currentTime,
        "f_reg_15": f_reg_15,
        "f_reg_10": f_reg_10,
    },
}

# Register displays here
displays = [
    PlatformDisplay(ctx),
    AltDisplay(ctx)
    # Add more displays later, e.g., AltDisplay(ctx)
]
active_idx = 0
active = displays[active_idx]
active.on_show()

while running:
    now = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            active_idx = (active_idx + 1) % len(displays)
            active = displays[active_idx]
            active.on_show()
        # Per-display event handling if needed
        active.handle_event(event)

    active.update(now)
    active.draw(screen)

    pygame.display.flip()
    clock.tick(config.FPS)

pygame.quit()
