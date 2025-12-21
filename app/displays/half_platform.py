import pygame
from datetime import datetime
from .base import Display
from .ui_components import UIComponents

class HalfPlatformDisplay(Display):
    def __init__(self, ctx, platform_top=1, platform_bottom=2):
        super().__init__(ctx)
        self.departures = []
        self.stops = []
        self.last_update = 0
        self.platform_top = platform_top
        self.platform_bottom = platform_bottom


    def on_show(self):
        self.last_update = 0  # force refresh on entry

    def _to_rgb(self, colour_hex):
        if not colour_hex:
            return (0, 0, 0)
        return pygame.Color(colour_hex)

    def update(self, now):
        if now - self.last_update >= 10 or not self.departures:
            self.departures_top, next_run_top = self.ctx['stop'].get_next_departures(3, [self.platform_top], return_next_run = True)
            if self.departures_top != []:
                self.stops_top = self.ctx["ptv_api"].get_pid_stops(next_run_top, self.ctx['stop'].stop_id)
            self.departures_bottom, next_run_bottom = self.ctx['stop'].get_next_departures(3, [self.platform_bottom], return_next_run = True)
            if self.departures_bottom != []:
                self.stops_bottom = self.ctx["ptv_api"].get_pid_stops(next_run_bottom, self.ctx['stop'].stop_id)
            self.last_update = now

    def draw(self, screen):
        config = self.ctx["config"]
        fonts = self.ctx["fonts"]
        colourMap = self.ctx["colourMap"]
        screen.fill(config.LIGHT_WARM_GREY)

        self.half_draw(screen, self.departures_top, 16)
        self.half_draw(screen, self.departures_bottom, 168)


    def half_draw(self, screen, departures, y=0):
        config = self.ctx["config"]
        fonts = self.ctx["fonts"]
        colourMap = self.ctx["colourMap"]

        # If no departures, overwrite screen with no trains
        if departures == []:
            UIComponents.no_trains_departing_black(screen, config, 480,320,fonts["f_reg_35"])
            return

        # Subsequent departures are drawn no matter what
        sub_y = y
        for i in range(1,3): 
            dep = departures[i]
            if dep:
                colour = self._to_rgb(colourMap.get(dep["route_gtfs_id"]))
                dep_item = UIComponents.departure_item_short(config, colour, 
                                          x=0,
                                          y=0,
                                          departure_time=dep["departure_time"],
                                          time_to_departure=dep["time_to_departure"],
                                          destination=dep["destination"],
                                          note=dep["express_note"]
                                          )
            else:
                colour = config.MID_GREY
                dep_item = UIComponents.departure_item_short(config, colour, 
                                          x=0,
                                          y=0,
                                          departure_time="--",
                                          time_to_departure="-- min",
                                          destination="--",
                                          note=""
                                          )                
            r = dep_item.get_rect()
            r.x = 340
            r.y = sub_y
            sub_y = r.bottom + 20
            screen.blit(dep_item, r)
        
        # Center bar
        pygame.draw.rect(screen, config.BLACK, (6,y+50,324,1))
        pygame.draw.rect(screen, config.BLACK, (340,y+50,135,1))

        # Clock drawn always
        current_time = UIComponents.get_current_time_string()
        UIComponents.draw_clock(screen, config, 340, y + 104, 135, 27, 1, fonts["f_med_17"], current_time)

        # Main departures
        departure = departures[0]
        colour = self._to_rgb(colourMap.get(departure["route_gtfs_id"]))
        UIComponents.metro_departure_header(config, screen, 
                                   colour, 
                                   x=0, 
                                   y=y, 
                                   w=324, 
                                   h= 40, 
                                   ttd_y = 6, 
                                   ttdw = 68, 
                                   ttd_h = 25, 
                                   dep_time_font = fonts["f_reg_15"], 
                                   dep_time = departure.get("departure_time", "--:--"), 
                                   time_to_dep_font = fonts["f_reg_17"], 
                                   time_to_dep = departure.get("time_to_departure", "-"), 
                                   dest_font = fonts["f_bold_27"], 
                                   dest = departure["destination"], 
                                   dep_note_font = fonts["f_reg_9"], 
                                   dep_note = f"{departure['express_note']} {departure['departure_note']}", 
        )

       
        #pygame.draw.rect(screen, config.BLACK, (11,77, config.SCREEN_RES[0] - 11*2, 1))

       #UIComponents.draw_stop_list(screen, config, self.stops, colour, x=11, y=78, stop_h=15, stop_w=116, bar_width=4, v_padding=7, font=fonts["stops"], tick=(3,2), text_offset=9)
        






