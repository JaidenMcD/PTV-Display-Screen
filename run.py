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
    platform_rect = pygame.draw.rect(screen, FRANKSTON, (344, 14, 31, 31))
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
    # Time to Departure
    r = pygame.draw.rect(screen, BLACK, (379, 15, 91, 31))
    f = pygame.font.Font('assets/fonts/NETWORKSANS-2019-MEDIUM.TTF', 24)
    t = f.render(departure['time_to_departure'] if departure else "-", True, WHITE) # Text, antialias, color
    tr = t.get_rect()
    tr.center = r.center
    screen.blit(t, tr.topleft)


    """ SUBSEQUENT DEPARTURES """
    gap = 26
    for i in range(1, 3):
        offset = (i-1) * gap
        container = pygame.Rect(11, 212 + offset, 342,26)
        # Bottom line indicators
        r = pygame.Rect(0,0,4,17)
        r.midleft = container.midleft
        pygame.draw.rect(screen, FRANKSTON, r)
        # Platform Number Box
        r = pygame.Rect(283,0,18,18)
        r.centery = container.centery
        r = pygame.draw.rect(screen, FRANKSTON, r)
        f = pygame.font.Font('assets/fonts/NETWORKSANS-2019-REGULAR.TTF', 13)
        t = f.render(departures[i]['platform'] if len(departures) > i else "-", True, WHITE) # Text, antialias, color
        tr = t.get_rect()
        tr.center = r.center
        screen.blit(t, tr.topleft)
        # Time to Departure Box
        r = pygame.Rect(303,0,50,18)
        r.centery = container.centery
        r = pygame.draw.rect(screen, BLACK, r)
        f = pygame.font.Font('assets/fonts/NETWORKSANS-2019-REGULAR.TTF', 13)
        t = f.render(departures[i]['time_to_departure'] if len(departures) > i else "-", True, WHITE) # Text, antialias, color
        tr = t.get_rect()
        tr.center = r.center
        screen.blit(t, tr.topleft)
        # Time of Departure
        f = pygame.font.Font('assets/fonts/NETWORKSANS-2019-MEDIUM.TTF', 14)
        t = f.render(departures[i]['departure_time'] if len(departures) > i else "--:--", True, BLACK) # Text, antialias, color
        tr = t.get_rect()
        tr.centery = container.centery
        screen.blit(t, (16, tr.top))
        # Destination
        f = pygame.font.Font('assets/fonts/NETWORKSANS-2019-BOLD.TTF', 14)
        t = f.render(departures[i]['destination'] if len(departures) > i else "-", True, BLACK) # Text, antialias, color
        tr = t.get_rect()
        tr.centery = container.centery
        screen.blit(t, (75, tr.top))
        


    # Top hline
    pygame.draw.line(screen, BLACK, (11, 70), (SCREEN_RES[0] - 11, 70), 2)

    # Bottom hline
    pygame.draw.line(screen, BLACK, (11, 213), (353, 213), 2)
    pygame.draw.line(screen, BLACK, (11, 238), (353, 238), 2)

    # Bottom line indicators
    pygame.draw.rect(screen, FRANKSTON, (11, 218, 4, 17))
    pygame.draw.rect(screen, FRANKSTON, (11, 243, 4, 17))

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