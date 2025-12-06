import os
from config import *
import time 
from datetime import datetime
from dotenv import load_dotenv
from ptv_api import *
from data.gtfs_loader import load_route_data

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


# Load colours in config
routeinfo = load_route_data("data/routes.txt")
newRouteInfo = []
for route in routeinfo:
    route_id = route['route_id'].split('02-')[1]
    # Remove bus replacements
    if '-R' in route_id:
        continue
    route_id = route_id.split(':')[0]
    output = {
        'route_id': route_id,
        'colour': route['color'],
        'text_colour': route['text_color']
    }
    newRouteInfo.append(output)


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

    """ STOPS LIST """
    stops = get_stops_for_run(departures[0]['run_id'], 0)
    for c_idx, stop_chunk in enumerate(stops):
        for r_idx, stop in enumerate(stop_chunk):
            container = pygame.Rect(0, 0 ,116, 14)
            container.x = 11 + 116 * c_idx
            container.y = 78 + 14 * r_idx
            if c_idx == 0 and r_idx == 0:
                # Box Surrounding current station, in white
                f = pygame.font.Font('assets/fonts/NETWORKSANS-2019-REGULAR.TTF', 12)
                t = f.render(stop[0], True, WHITE) # Text, antialias, color
                tr = t.get_rect()
                tr.centery = container.centery
                tr.x = container.x + 12

                r = pygame.Rect(0, 0, tr.size[0] + 4,16)
                r.centery = container.centery
                r.x = container.x + 10

                pygame.draw.rect(screen, FRANKSTON, r)
                screen.blit(t, tr.topleft)
            else:
                f = pygame.font.Font('assets/fonts/NETWORKSANS-2019-REGULAR.TTF', 12)
                t = f.render(stop[0], True, BLACK) # Text, antialias, color
                tr = t.get_rect()
                tr.centery = container.centery
                tr.x = container.x + 12
                screen.blit(t, tr)
            # Ticks
            r = pygame.Rect(0,0,3,4)
            r.midleft = (container.x + 4, container.centery)
            pygame.draw.rect(screen, FRANKSTON, r)
            # Rick Lines
            if r_idx == 0 and stop[2]:
                # First stop, terminus
                r = pygame.Rect(0,0,9,4)
                r.centery = container.centery
                r.x = container.x -2
                pygame.draw.rect(screen, FRANKSTON, r)
                r = pygame.Rect(0,0,4,5)
                r.bottomleft = container.bottomleft
                pygame.draw.rect(screen, FRANKSTON, r)
            elif r_idx == len(stop_chunk) -1 and stop[2]:
                # Last stop, terminus
                r = pygame.Rect(0,0,9,4)
                r.centery = container.centery
                r.x = container.x -2
                pygame.draw.rect(screen, FRANKSTON, r)
                pygame.draw.rect(screen, FRANKSTON, (container.x, container.y,4,5))
            else:
                r = pygame.Rect(0,0,4,14)
                r.midleft = (container.x, container.centery)
                pygame.draw.rect(screen, FRANKSTON, r)
            if r_idx == 0 and not stop[2]:
                # First stop, not terminus
                r = pygame.Rect(0,0,4,3)
                r.bottomleft = (container.x, container.y)
                pygame.draw.rect(screen, FRANKSTON, r)
                r = pygame.Rect(0,0,4,1)
                r.bottomleft = (container.x, container.y -4)
                pygame.draw.rect(screen, FRANKSTON, r)
                r = pygame.Rect(0,0,4,2)
                r.bottomleft = (container.x, container.y -7)
                pygame.draw.rect(screen, FRANKSTON, r)
            if r_idx == len(stop_chunk) -1 and not stop[2]:
                # Last stop, not terminus
                r = pygame.Rect(0,0,4,2)
                r.topleft = (container.x, container.y + container.height)
                pygame.draw.rect(screen, FRANKSTON, r)
                r = pygame.Rect(0,0,4,1)
                r.topleft = (container.x, container.y + container.height +4)
                pygame.draw.rect(screen, FRANKSTON, r)
                r = pygame.Rect(0,0,4,3)
                r.topleft = (container.x, container.y + container.height +7)
                pygame.draw.rect(screen, FRANKSTON, r)
                

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