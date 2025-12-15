import pygame
from datetime import datetime
from .base import Display
from .ui_components import UIComponents

class PlatformDisplay(Display):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.departures = []
        self.stops = []
        self.last_update = 0
        self.multi_platform = len(self.ctx['stop'].platforms) != 1 or self.ctx['stop'].platforms == ['']

    def on_show(self):
        self.last_update = 0  # force refresh on entry

    def _to_rgb(self, colour_hex):
        if not colour_hex:
            return (0, 0, 0)
        return pygame.Color(colour_hex)

    def update(self, now):
        if now - self.last_update >= 10 or not self.departures:
            self.departures, next_run = self.ctx['stop'].get_next_departures(3, return_next_run = True)
            self.departures = self.filter_departure_list(self.departures, 3)
            self.stops = self.ctx["ptv_api"].get_pid_stops(next_run, self.ctx['stop'].stop_id)
            self.last_update = now

    def draw(self, screen):
        config = self.ctx["config"]
        fonts = self.ctx["fonts"]
        colourMap = self.ctx["colourMap"]


        screen.fill(config.LIGHT_WARM_GREY)

        # Subsequent departures are drawn no matter what
        gap = 3
        y = 216
        for i in range(1,3): 
            dep = self.departures[i]
            if dep:
                colour = self._to_rgb(colourMap.get(dep["route_gtfs_id"]))
                y = UIComponents.draw_departure_item(
                screen, config, colour, y, 
                departure_time=dep["departure_time"],
                departure_time_font=fonts["f_reg_13"],
                departure_dest=dep["destination"],
                departure_dest_font=fonts["f_med_12"],
                note=dep["express_note"],
                note_font=fonts["f_reg_9"],
                time_until_departure=dep["time_to_departure"],
                platform=dep["platform"],
                w=351, bar_thickness=1, x=9, 
                include_platform=self.multi_platform and dep['platform']
                )
            else:
                colour = config.MID_GREY
                y = UIComponents.draw_departure_item(
                    screen, config, colour, y, 
                    departure_time="--",
                    departure_time_font=fonts["f_reg_13"],
                    departure_dest="--",
                    departure_dest_font=fonts["f_med_12"],
                    note="",
                    note_font=fonts["f_reg_9"],
                    time_until_departure="-- min",
                    platform=None,
                    w=351, bar_thickness=1, x=9, 
                    include_platform=False
                )
            y = y + gap
        
        # Clock drawn always
        current_time = UIComponents.get_current_time_string()
        UIComponents.draw_clock(screen, config, 369, 216, 102, 46, 1, fonts["f_med_14"], current_time)

        # Check if no departures
        if all(x is None for x in self.departures):
            pygame.draw.rect(screen, config.MID_GREY, (0, 0, config.SCREEN_RES[0], 10))
            t = fonts["f_med_22"].render('No trains are departing from this platform', True, config.BLACK)
            tr = t.get_rect()
            tr.centerx = 480//2
            tr.y = 147
            screen.blit(t, tr.topleft)

            img = pygame.image.load('assets/icons/no-trains.png').convert_alpha()
            img = pygame.transform.scale(img, (87,87))
            img_r = img.get_rect()
            img_r.centerx = 480//2
            img_r.y = 57
            screen.blit(img, img_r)
            return

        departure = self.departures[0]
        colour = self._to_rgb(colourMap.get(departure["route_gtfs_id"]))
        pygame.draw.rect(screen, colour, (0, 0, config.SCREEN_RES[0], 10))


        """ Top Section """
        # Destination
        coords = (100, 12)
        text = fonts["f_bold_27"].render(departure["destination"], True, config.BLACK)
        screen.blit(text, coords)
        baseline_y = coords[1] + fonts["f_bold_27"].get_ascent()

        # Departure Time
        time_y = baseline_y - fonts["f_reg_21"].get_ascent()
        text = fonts["f_reg_21"].render(departure.get("departure_time", "--:--"), True, config.BLACK)
        screen.blit(text, (11, time_y))

        # Time to departure
        UIComponents.time_to_departure(screen, config, 379, 15, 91, 31, fonts["f_reg_23"], departure.get("time_to_departure", "-"), bg_color=config.BLACK)

        # Draw platform number onyl if multiple platforms
        if self.multi_platform and departure['platform']:
            platform_rect = pygame.draw.rect(screen, colour, (344, 14, 31, 31))
            text = fonts["f_bold_25"].render(departure.get("platform", "-"), True, config.WHITE)
            text_rect = text.get_rect(); text_rect.center = platform_rect.center
            screen.blit(text, text_rect.topleft)

        formatted = f"{departure['express_note']} {departure['departure_note']}"
        t = fonts["f_reg_12"].render(formatted, True, config.BLACK)
        screen.blit(t, (10,51))

        pygame.draw.rect(screen, config.BLACK, (11,77, config.SCREEN_RES[0] - 11*2, 1))

        UIComponents.draw_stop_list(screen, config, self.stops, colour, x=11, y=78, stop_h=15, stop_w=116, bar_width=4, v_padding=7, font=fonts["stops"], tick=(3,2), text_offset=9)


    
    def filter_departure_list(self, departures, n_to_show):
        new_departure_list = []

        for dep in departures:
            if 'RRB' not in dep.get('flag', ''):
                new_departure_list.append(dep)
            if len(new_departure_list) == n_to_show:
                break

        # Top up with None
        while len(new_departure_list) < n_to_show:
            new_departure_list.append(None)

        return new_departure_list
        






