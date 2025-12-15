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
                include_platform=self.multi_platform and departure['platform']
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

        self.draw_stop_list(screen, config, colour, x=11, y=78, stop_h=15, stop_w=116, bar_width=4, v_padding=7, font=fonts["stops"], tick=(3,2), text_offset=9)


        
        

    def draw_stop_list(self, screen, config, colour, x, y, stop_h, stop_w, bar_width, v_padding, font, tick, text_offset):
        """
        bar_width should be an even number 
          """
        pygame.draw.rect(screen, colour, (x, y, bar_width, v_padding))
        # Divide the height up into chunk
        all_stops = [s for chunk in self.stops for s in chunk]
        skip_block_active = False
        stop_index = 0
        for c_idx, stop_chunk in enumerate(self.stops):
            for r_idx, stop in enumerate(stop_chunk):
                container = pygame.Rect(0,0, stop_w, stop_h)
                container.x = x + stop_w * c_idx
                container.y = y + v_padding + stop_h * r_idx

                if stop["stop_id"] is not None: # actual stop
                    # Determine s
                    if stop["is_terminus"]: # terminus
                        # Cap
                        r_temp = pygame.Rect(container.x,container.y,bar_width,stop_h)
                        r = pygame.Rect(0,0, 9, 3)
                        r.centerx = r_temp.centerx
                        r.centery = container.centery
                        pygame.draw.rect(screen, colour, r)
                        # Main bar
                        pygame.draw.rect(screen, colour, (container.x,container.y,bar_width,round(stop_h / 2)))
                    else:
                        # if skipped and the next station is not skipped
                        if stop["is_skipped"] and not all_stops[stop_index+1]["is_skipped"]:
                            UIComponents.draw_express_arrow(screen, container, colour, bar_width=4, arrowtip_y=10)
                            skip_block_active = False
                        # If skipped and already inside skip block:
                        elif stop["is_skipped"] and skip_block_active:
                            # Main Bar
                            r = pygame.draw.rect(screen, colour, (container.x,container.y,bar_width,stop_h))
                        # if skipped and not yet inside a skip block:
                        elif stop["is_skipped"] and not skip_block_active:
                            skip_block_active = True
                            UIComponents.draw_express_arrow(screen, container, colour, bar_width=4, arrowtip_y=10)
                        # if not skipped and not inside a skip block
                        elif not stop["is_skipped"] and not skip_block_active:
                            skip_block_active = False
                            # Main Bar
                            r = pygame.draw.rect(screen, colour, (container.x,container.y,bar_width,stop_h))
                            # Tick
                            r = pygame.Rect(0,0, tick[0], tick[1])
                            r.centery = container.centery
                            r.x = container.x + bar_width
                            pygame.draw.rect(screen, colour, r)
        

                    # Station name
                    if c_idx == 0 and r_idx == 0:
                        t = font.render(stop["name"], True, (255, 255, 255))
                        tr = t.get_rect(); tr.centery = container.centery; tr.x = container.x + text_offset
                        r_box = pygame.Rect(0, 0, tr.size[0] + 4, tr.size[1]+2)
                        r_box.centery = container.centery; r_box.x = container.x + text_offset - 2
                        pygame.draw.rect(screen, colour, r_box)
                        screen.blit(t, tr.topleft)
                    else:
                        textcol = config.MID_GREY if stop["is_skipped"] else config.BLACK
                        t = font.render(stop["name"], True, textcol)
                        tr = t.get_rect(); tr.centery = container.centery; tr.x = container.x + text_offset
                        screen.blit(t, tr)
                        # Top dot dot lones
                        if r_idx == 0 and stop != all_stops[0]:
                            pygame.draw.rect(screen, colour, (container.x, y, bar_width, 2))
                            pygame.draw.rect(screen, colour, (container.x, y+3, bar_width, 2))
                            pygame.draw.rect(screen, colour, (container.x, y+6, bar_width, v_padding-6))
                        if r_idx == len(stop_chunk) - 1 and stop != all_stops[-1]:
                            base_y = container.y + container.height
                            pygame.draw.rect(screen, colour, (container.x, base_y, bar_width, v_padding-6))
                            pygame.draw.rect(screen, colour, (container.x, base_y + v_padding - 5, bar_width, 2))
                            pygame.draw.rect(screen, colour, (container.x, base_y + v_padding - 2, bar_width, 2))
                stop_index = stop_index + 1
    
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
        






