import os
from config import *
import time 
from dotenv import load_dotenv


load_dotenv()
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
    screen = pygame.display.set_mode((480, 320), pygame.FULLSCREEN | pygame.NOFRAME)
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

px12_font = pygame.font.Font('assets/fonts/NETWORKSANS-2019-MEDIUM.TTF', 9)

while running:
    print('main loop')
    screen.fill(LIGHT_WARM_GREY)

    # Top Accent Bar
    pygame.draw.rect(screen, FRANKSTON, (0, 0, SCREEN_RES[0], 10))

    # Platform Number Box
    pygame.draw.rect(screen, FRANKSTON, (345, 15, 33, 33))

    # Time to next train Box
    pygame.draw.rect(screen, BLACK, (379, 15, 91, 33))

    # Top hline
    pygame.draw.line(screen, BLACK, (11, 70), (SCREEN_RES[0] - 11, 70), 2)

    # Bottom hline
    pygame.draw.line(screen, BLACK, (11, 213), (353, 213), 2)
    pygame.draw.line(screen, BLACK, (11, 238), (353, 238), 2)

    # Bottom line indicators
    pygame.draw.rect(screen, FRANKSTON, (11, 218, 4, 17))
    pygame.draw.rect(screen, FRANKSTON, (11, 243, 4, 17))

    # Bottom train countdowns
    pygame.draw.rect(screen, BLACK, (303, 217, 51, 18))
    pygame.draw.rect(screen, BLACK, (303, 243, 51, 18))
    # Bottom train platforms
    pygame.draw.rect(screen, FRANKSTON, (283, 217, 18, 18))
    pygame.draw.rect(screen, FRANKSTON, (283, 243, 18, 18))

    # Current time
    pygame.draw.rect(screen, BLACK, (358, 213, 113, 48))
    pygame.draw.rect(screen, LIGHT_WARM_GREY, (360, 215, 109, 44))
    text = px12_font.render("12:42:08 pm", True, BLACK) # Text, antialias, color (white)
    screen.blit(text, (373, 231)) # Blit at a specific position

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()