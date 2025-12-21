import os
import time

from dotenv import load_dotenv
import pygame
load_dotenv()
device = int(os.getenv("DEVICE", "0"))
if device == 1:
    # Must set these BEFORE pygame imports SDL
    os.environ["DISPLAY"] = ":0"
    os.environ["XAUTHORITY"] = "/home/admin/.Xauthority"

pygame.init()
import fonts

import config
from api import ptv_api
from data import gtfs_loader

# Register displays here
from displays.platform import PlatformDisplay  # keep filename as-is; rename when convenient
from displays.half_platform import HalfPlatformDisplay
from displays.altdisplay import AltDisplay

from models.stop import Stop




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

# Register Stop
search_term = input("Enter station: ")
platforms = input("Comma seperated platforms to show (skip with 'enter' for all): ")
platforms = platforms.split(',')
print(platforms)
stop = Stop(search_term)


ctx = {
    "stop": stop,
    "ptv_api": ptv_api,
    "config": config,
    "train_stop_id": stop.stop_id,
    "colourMap": colourMap,
    "fonts": fonts.font_list,
}


displays = [
    HalfPlatformDisplay(ctx),
    PlatformDisplay(ctx, platforms),
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
