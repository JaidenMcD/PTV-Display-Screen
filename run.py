import os
from config import *
import time 
from dotenv import load_dotenv


load_dotenv()
print("env file loaded")
device = int(os.getenv("DEVICE"))
print(f"device = {device}")

if device == 1:
    print('setting enviroment variables')
    os.environ["SDL_FBDEV"] = "/dev/fb0"
    os.environ["SDL_VIDEODRIVER"] = "fbcon"
    os.environ["SDL_NOMOUSE"] = "1" 
    os.environ.pop("DISPLAY", None)   # REMOVE X11 DISPLAY

import pygame



pygame.init()
pygame.mouse.set_visible(False)

if device == 1:
    # --- Read actual framebuffer resolution ---
    with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
        w, h = f.read().strip().split(",")
        fb_w = int(w)
        fb_h = int(h)

    print("REAL FRAMEBUFFER SIZE:", fb_w, fb_h)
    screen = pygame.display.set_mode((fb_w, fb_h))
else:
    screen = pygame.display.set_mode(SCREEN_RES)



update_interval = 5 # seconds
last_update = 0


clock = pygame.time.Clock()
running = True

print('starting up')
screen.fill(BACKGROUND_COLOR)
time.sleep(1)
screen.fill(TEXT_COLOR)
time.sleep(1)
screen.fill(BACKGROUND_COLOR)


while running:
    screen.fill((0, 120, 255))
    pygame.draw.rect(screen, (0, 0, 0), (0, 0, fb_w, fb_h), 8)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()