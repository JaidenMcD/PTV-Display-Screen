import pygame
from datetime import datetime
from .base import Display
from .ui_components import UIComponents

class TramDisplay(Display):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.departures = []
        self.stops = []
        self.last_update = 0

    def on_show(self):
        self.last_update = 0  # force refresh on entry

    def _to_rgb(self, colour_hex):
        if not colour_hex:
            return (0, 0, 0)
        return pygame.Color(colour_hex)

    def update(self, now):
        if now - self.last_update >= 10 or not self.departures:
            self.departures = self.ctx['stop'].get_next_departures_per_route(5)
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
            dep_item = UIComponents.tram_departure_item(config, 320, 60, route_number, destination, time_to_departure, colour, text_colour, font, destination_padding)
            dep_item = pygame.transform.rotate(dep_item, 90)
            screen.blit(dep_item, (x, 0))
            x += 62
        
        # Footer
        current_time = UIComponents.get_current_time_string()
        footer = UIComponents.tram_footer(320,30,current_time,config,fonts['f_reg_9'],h_padding=10)
        footer = pygame.transform.rotate(footer, 90)
        footer_rect = footer.get_rect()
        footer_rect.bottomright = (480,320)
        screen.blit(footer, footer_rect.topleft)

