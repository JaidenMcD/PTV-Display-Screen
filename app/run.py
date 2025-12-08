import os
import time
from datetime import datetime
from dotenv import load_dotenv

import pygame

import config
from api import ptv_api
from data import gtfs_loader
from displays.platform import PlatformDisplay  # keep filename as-is; rename when convenient
from displays.altdisplay import AltDisplay

load_dotenv()
device = int(os.getenv("DEVICE", "0"))
train_stop_id = int(os.getenv("TRAIN_STOP_ID", "0"))

if device == 1:
    # Must set these BEFORE pygame imports SDL
    os.environ["DISPLAY"] = ":0"
    os.environ["XAUTHORITY"] = "/home/admin/.Xauthority"

pygame.init()

if device == 1:
    screen = pygame.display.set_mode((480, 320), pygame.FULLSCREEN | pygame.NOFRAME)
    # Hide the mouse cursor
    pygame.mouse.set_visible(False)
else:
    screen = pygame.display.set_mode(config.SCREEN_RES)


info = pygame.display.Info()
print("Pygame display info:", info.current_w, info.current_h)

clock = pygame.time.Clock()
running = True

print("starting up")
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

ctx = {
    "ptv_api": ptv_api,
    "config": config,
    "train_stop_id": train_stop_id,
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
