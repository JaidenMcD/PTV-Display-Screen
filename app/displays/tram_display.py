import pygame
import utils
from datetime import datetime
from .base import Display
from .components.tramUI import TramUI

class TramDisplay(Display):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.departures = []
        self.stops = []
        self.last_update = 0
        self.alerts = []

    def on_show(self):
        self.last_update = 0  # force refresh on entry

    def _to_rgb(self, colour_hex):
        if not colour_hex:
            return (0, 0, 0)
        return pygame.Color(colour_hex)

    def update(self, now):
        if now - self.last_update >= 10 or not self.departures:
            self.departures, self.alerts = self.ctx['stop'].get_next_departures_per_route(4)
            self.last_update = now

    def draw(self, screen):
        config = self.ctx["config"]
        fonts = self.ctx["fonts"]
        colourMap = self.ctx["colourMap"]
        screen.fill(config.LIGHT_WARM_GREY)

        # Departure items
        
        x = 0
        for departure in self.departures:
            destination = departure["destination"]
            time_to_departure = departure["time_to_departure"]
            route_number = departure["route_number"] 
            colour = self._to_rgb(colourMap.get(route_number)["route_col"])
            text_colour = self._to_rgb(colourMap.get(route_number)["text_col"])
            font = fonts["f_med_14"]
            destination_padding = 10
            dep_item = TramUI.tram_departure_item(config, 320, 60, route_number, destination, time_to_departure, colour, text_colour, font, destination_padding)
            dep_item = pygame.transform.rotate(dep_item, 90)
            screen.blit(dep_item, (x, 0))
            x += 62

        

        # Footer
        current_time = TramUI.get_current_time_string()
        footer = TramUI.tram_footer(320,30,current_time,config,fonts['f_reg_9'],h_padding=10)
        footer = pygame.transform.rotate(footer, 90)
        footer_rect = footer.get_rect()
        footer_rect.bottomright = (480,320)
        screen.blit(footer, footer_rect.topleft)

        # alert area
        n_departures = len(self.departures)
        departures_right = n_departures * 62
        footer_left = footer_rect.x
        alert_area_height = footer_left - departures_right

        # Alerts icon
        alert = self.alerts[0]
        icon_path = config.tram_alert_mappings.get(alert["header"])["icon_path"]
        header = config.tram_alert_mappings.get(alert["header"])["header"]

        alert_screen = TramUI.alert( config, fonts, header, alert["description"], icon_path, 320, alert_area_height)

        alert_screen = pygame.transform.rotate(alert_screen, 90)
        alert_rect = alert_screen.get_rect()
        alert_rect.topleft = (departures_right,0)
        screen.blit(alert_screen, alert_rect.topleft)
