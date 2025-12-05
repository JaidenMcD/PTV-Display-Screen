import os
from config import *
import time 
from datetime import datetime
from dotenv import load_dotenv
from ptv_api import get_departures

load_dotenv()
device = int(os.getenv("DEVICE"))
train_stop_id = os.getenv("TRAIN_STOP_ID")

if device == 1:
    # Must set these BEFORE pygame imports SDL
    os.environ["DISPLAY"] = ":0"
    os.environ["XAUTHORITY"] = "/home/admin/.Xauthority"

import pygame

pygame.init()

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

# Departure data
update_interval = 10  # seconds
last_update = 0
departures = [] 

while running:
    now = time.time()

    # API Update 
    if now - last_update >= update_interval:
        departures = get_departures(0, train_stop_id, max_results=5)
        last_update = now

    # Drawing
    screen.fill(LIGHT_WARM_GREY)

    # Top Accent Bar
    pygame.draw.rect(screen, FRANKSTON, (0, 0, SCREEN_RES[0], 10))

    """ NEXT DEPARTURE """
    # Platform Number Box
    platform_rect = pygame.draw.rect(screen, FRANKSTON, (344, 14, 33, 33))
    platform_font = pygame.font.Font('assets/fonts/NETWORKSANS-2019-BOLD.TTF', 25)
    platform_text = departures[0]['platform'] if departures else "-"
    text = platform_font.render(platform_text, True, WHITE) # Text, antialias, color    
    text_rect = text.get_rect()
    text_rect.center = platform_rect.center
    screen.blit(text, text_rect.topleft)
    # Destination
    departure = departures[0] if departures else None
    dest_font = pygame.font.Font('assets/fonts/NETWORKSANS-2019-BOLD.TTF', 27)
    text = dest_font.render(departure['destination'], True, BLACK) # Text, antialias, color 
    screen.blit(text, (113,19))
    # Departure Time
    departure_time_font = pygame.font.Font('assets/fonts/NETWORKSANS-2019-MEDIUM.TTF', 24)
    departure_time_text = departure['departure_time'] if departure else "--:--"
    text = departure_time_font.render(departure_time_text, True, BLACK) # Text, antialias, color
    screen.blit(text, (11, 21))
    


    

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
    time_rect = pygame.draw.rect(screen, BLACK, (358, 213, 113, 48))
    pygame.draw.rect(screen, LIGHT_WARM_GREY, (360, 215, 109, 44))
    time_font = pygame.font.Font('assets/fonts/NETWORKSANS-2019-MEDIUM.TTF', 15)
    current_time = datetime.now().strftime("%I:%M:%S %p").lower()
    text = time_font.render(current_time, True, BLACK) # Text, antialias, color 
    text_rect = text.get_rect()
    text_rect.center = time_rect.center
    screen.blit(text, text_rect.topleft)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()