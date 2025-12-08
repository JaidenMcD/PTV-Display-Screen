import os
import config
import time 
from datetime import datetime
from dotenv import load_dotenv
from api import ptv_api
from data import gtfs_loader

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
    screen = pygame.display.set_mode(config.SCREEN_RES)

info = pygame.display.Info()
print("Pygame display info:", info.current_w, info.current_h)


clock = pygame.time.Clock()
running = True

print('starting up')
screen.fill(config.BACKGROUND_COLOR)


# Departure data
update_interval = 10  # seconds
last_update = 0
departures = [] 

""" LOADING STATION DATA """
""" 
train_stop = os.getenv('TRAIN_STOP')
print(f'Searching for {train_stop}...')
res = searchPTVAPI(train_stop)
stop = []
for stopOption in res['stops']:
    if train_stop in stopOption['stop_name']:
        stop = stopOption
        break
    else:
        stop = res['stops'][0]
gtfs = get_GTFS_stop_ids(stop['stop_name'])
stop["gtfs_stops"] = gtfs
print(stop) """

""" Route Colour Map """
colourMap = gtfs_loader.build_colour_map('data/gtfs_static/routes.txt')

""" Setup Fonts """
f_platformNumber_large = pygame.font.Font('assets/fonts/NETWORKSANS-2019-BOLD.TTF', 25)
f_platformNumber_small = pygame.font.Font('assets/fonts/NETWORKSANS-2019-REGULAR.TTF', 13)
f_destination_large = pygame.font.Font('assets/fonts/NETWORKSANS-2019-BOLD.TTF', 27)
f_destination_small =  pygame.font.Font('assets/fonts/NETWORKSANS-2019-BOLD.TTF', 14)
f_depTime_large = pygame.font.Font('assets/fonts/NETWORKSANS-2019-MEDIUM.TTF', 24)
f_depTime_small = pygame.font.Font('assets/fonts/NETWORKSANS-2019-MEDIUM.TTF', 14)
f_timeToDep_large = pygame.font.Font('assets/fonts/NETWORKSANS-2019-MEDIUM.TTF', 24)
f_timeToDep_small = pygame.font.Font('assets/fonts/NETWORKSANS-2019-REGULAR.TTF', 13)
f_stopsList = pygame.font.Font('assets/fonts/NETWORKSANS-2019-REGULAR.TTF', 12)
f_currentTime = pygame.font.Font('assets/fonts/NETWORKSANS-2019-MEDIUM.TTF', 15)


while running:
    now = time.time()

    # API Update 
    if now - last_update >= update_interval:
        departures = ptv_api.get_departures(0, train_stop_id, max_results=5)
        last_update = now

    # Drawing
    screen.fill(config.LIGHT_WARM_GREY)


    """ NEXT DEPARTURE """
    colour = colourMap.get(departures[0]['GTFS_id'])
    # Top Accent Bar
    pygame.draw.rect(screen, colour, (0, 0, config.SCREEN_RES[0], 10))
    # Platform Number Box
    platform_rect = pygame.draw.rect(screen, colour, (344, 14, 31, 31))
    platform_font = f_platformNumber_large
    platform_text = departures[0]['platform'] if departures else "-"
    text = platform_font.render(platform_text, True, config.WHITE) # Text, antialias, color    
    text_rect = text.get_rect()
    text_rect.center = platform_rect.center
    screen.blit(text, text_rect.topleft)
    # Destination
    departure = departures[0] if departures else None
    dest_font = f_destination_large
    text = dest_font.render(departure['destination'], True, config.BLACK) # Text, antialias, color 
    screen.blit(text, (113,19))
    # Departure Time
    departure_time_font = f_depTime_large
    departure_time_text = departure['departure_time'] if departure else "--:--"
    text = departure_time_font.render(departure_time_text, True, config.BLACK) # Text, antialias, color
    screen.blit(text, (11, 21))
    # Time to Departure
    r = pygame.draw.rect(screen, config.BLACK, (379, 15, 91, 31))
    f = f_timeToDep_large
    t = f.render(departure['time_to_departure'] if departure else "-", True, config.WHITE) # Text, antialias, color
    tr = t.get_rect()
    tr.center = r.center
    screen.blit(t, tr.topleft)

    """ STOPS LIST """
    stops = ptv_api.get_stops_for_run(departures[0]['run_id'], 0)
    for c_idx, stop_chunk in enumerate(stops):
        for r_idx, stop in enumerate(stop_chunk):
            container = pygame.Rect(0, 0 ,116, 14)
            container.x = 11 + 116 * c_idx
            container.y = 78 + 14 * r_idx
            if c_idx == 0 and r_idx == 0:
                # Box Surrounding current station, in white
                f = f_stopsList
                t = f.render(stop[0], True, config.WHITE) # Text, antialias, color
                tr = t.get_rect()
                tr.centery = container.centery
                tr.x = container.x + 12

                r = pygame.Rect(0, 0, tr.size[0] + 4,16)
                r.centery = container.centery
                r.x = container.x + 10

                pygame.draw.rect(screen, colour, r)
                screen.blit(t, tr.topleft)
            else:
                f = f_stopsList
                t = f.render(stop[0], True, config.BLACK) # Text, antialias, color
                tr = t.get_rect()
                tr.centery = container.centery
                tr.x = container.x + 12
                screen.blit(t, tr)
            # Ticks
            r = pygame.Rect(0,0,3,4)
            r.midleft = (container.x + 4, container.centery)
            pygame.draw.rect(screen, colour, r)
            # Rick Lines
            if r_idx == 0 and stop[2]:
                # First stop, terminus
                r = pygame.Rect(0,0,9,4)
                r.centery = container.centery
                r.x = container.x -2
                pygame.draw.rect(screen, colour, r)
                r = pygame.Rect(0,0,4,5)
                r.bottomleft = container.bottomleft
                pygame.draw.rect(screen, colour, r)
            elif r_idx == len(stop_chunk) -1 and stop[2]:
                # Last stop, terminus
                r = pygame.Rect(0,0,9,4)
                r.centery = container.centery
                r.x = container.x -2
                pygame.draw.rect(screen, colour, r)
                pygame.draw.rect(screen, colour, (container.x, container.y,4,5))
            else:
                r = pygame.Rect(0,0,4,14)
                r.midleft = (container.x, container.centery)
                pygame.draw.rect(screen, colour, r)
            if r_idx == 0 and not stop[2]:
                # First stop, not terminus
                r = pygame.Rect(0,0,4,3)
                r.bottomleft = (container.x, container.y)
                pygame.draw.rect(screen, colour, r)
                r = pygame.Rect(0,0,4,1)
                r.bottomleft = (container.x, container.y -4)
                pygame.draw.rect(screen, colour, r)
                r = pygame.Rect(0,0,4,2)
                r.bottomleft = (container.x, container.y -7)
                pygame.draw.rect(screen, colour, r)
            if r_idx == len(stop_chunk) -1 and not stop[2]:
                # Last stop, not terminus
                r = pygame.Rect(0,0,4,2)
                r.topleft = (container.x, container.y + container.height)
                pygame.draw.rect(screen, colour, r)
                r = pygame.Rect(0,0,4,1)
                r.topleft = (container.x, container.y + container.height +4)
                pygame.draw.rect(screen, colour, r)
                r = pygame.Rect(0,0,4,3)
                r.topleft = (container.x, container.y + container.height +7)
                pygame.draw.rect(screen, colour, r)
                

    """ SUBSEQUENT DEPARTURES """
    gap = 26
    for i in range(1, 3):
        colour = colourMap.get(departures[i]['GTFS_id'])
        offset = (i-1) * gap
        container = pygame.Rect(11, 212 + offset, 342,26)
        # Bottom line indicators
        r = pygame.Rect(0,0,4,17)
        r.midleft = container.midleft
        pygame.draw.rect(screen, colour, r)
        # Platform Number Box
        r = pygame.Rect(283,0,18,18)
        r.centery = container.centery
        r = pygame.draw.rect(screen, colour, r)
        f = f_platformNumber_small
        t = f.render(departures[i]['platform'] if len(departures) > i else "-", True, config.WHITE) # Text, antialias, color
        tr = t.get_rect()
        tr.center = r.center
        screen.blit(t, tr.topleft)
        # Time to Departure Box
        r = pygame.Rect(303,0,50,18)
        r.centery = container.centery
        r = pygame.draw.rect(screen, config.BLACK, r)
        f = f_timeToDep_small
        t = f.render(departures[i]['time_to_departure'] if len(departures) > i else "-", True, config.WHITE) # Text, antialias, color
        tr = t.get_rect()
        tr.center = r.center
        screen.blit(t, tr.topleft)
        # Time of Departure
        f = f_depTime_small
        t = f.render(departures[i]['departure_time'] if len(departures) > i else "--:--", True, config.BLACK) # Text, antialias, color
        tr = t.get_rect()
        tr.centery = container.centery
        screen.blit(t, (16, tr.top))
        # Destination
        f = f_destination_small
        t = f.render(departures[i]['destination'] if len(departures) > i else "-", True, config.BLACK) # Text, antialias, color
        tr = t.get_rect()
        tr.centery = container.centery
        screen.blit(t, (75, tr.top))
        
   


    # Top hline
    pygame.draw.line(screen, config.BLACK, (11, 70), (config.SCREEN_RES[0] - 11, 70), 2)

    # Bottom hline
    pygame.draw.line(screen, config.BLACK, (11, 213), (353, 213), 2)
    pygame.draw.line(screen, config.BLACK, (11, 238), (353, 238), 2)

    # Current time
    time_rect = pygame.draw.rect(screen, config.BLACK, (358, 213, 113, 48))
    pygame.draw.rect(screen, config.LIGHT_WARM_GREY, (360, 215, 109, 44))
    time_font = f_currentTime
    current_time = datetime.now().strftime("%I:%M:%S %p").lower()
    text = time_font.render(current_time, True, config.BLACK) # Text, antialias, color 
    text_rect = text.get_rect()
    text_rect.center = time_rect.center
    screen.blit(text, text_rect.topleft)



    pygame.display.flip()
    clock.tick(config.FPS)

pygame.quit()