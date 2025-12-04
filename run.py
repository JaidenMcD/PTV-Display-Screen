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
    os.environ["DISPLAY"] = ":0"
    os.environ["SDL_FBDEV"] = "/dev/fb1"
    os.environ["SDL_VIDEODRIVER"] = "fbcon"
    os.environ["SDL_NOMOUSE"] = "1" 

import pygame

pygame.init()
pygame.mouse.set_visible(False)

if device == 1:
    screen = pygame.display.set_mode(SCREEN_RES, pygame.FULLSCREEN | pygame.NOFRAME)
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
    screen.fill(BACKGROUND_COLOR)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()