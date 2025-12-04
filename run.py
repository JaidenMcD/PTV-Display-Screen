import os
from config import *
import time 
from dotenv import load_dotenv


load_dotenv()
device = int(os.getenv("DEVICE"))
print(f"device = {device}")

if device == 1:
    os.environ["SDL_FBDEV"] = "/dev/fb0"
    os.environ["SDL_VIDEODRIVER"] = "fbcon"
    os.environ["SDL_NOMOUSE"] = "1" 
    os.environ.pop("DISPLAY", None)   # REMOVE X11 DISPLAY

import pygame



pygame.init()
pygame.mouse.set_visible(False)

if device == 1:
    screen = pygame.display.set_mode(SCREEN_RES)
else:
    screen = pygame.display.set_mode(SCREEN_RES)

info = pygame.display.Info()
print("Pygame display info:", info.current_w, info.current_h)



clock = pygame.time.Clock()
running = True

print('starting up')
screen.fill(BACKGROUND_COLOR)
time.sleep(1)
screen.fill(TEXT_COLOR)
time.sleep(1)
screen.fill(BACKGROUND_COLOR)


while running:
    screen.fill(LIGHT_WARM_GREY)

    # Top Accent Bar
    pygame.draw.rect(screen, FRANKSTON, (0, 0, SCREEN_RES[0], 10))

    # Platform Number Box
    pygame.draw.rect(screen, FRANKSTON, (345, 15, 33, 33))

    # Time to next train Box
    pygame.draw.rect(screen, BLACK, (379, 15, 91, 33))


    pygame.draw.rect(screen, SHOWGROUNDS, (100, 100, 380, 100))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()