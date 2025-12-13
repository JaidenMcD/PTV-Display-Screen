import pygame
from datetime import datetime
from .base import Display

class PlatformDisplay(Display):
    def __init__(self, ctx, platform = None):
        super().__init__(ctx)
        self.departures = []
        self.stops = []
        self.platforms = platform
        self.last_update = 0

    def on_show(self):
        self.last_update = 0  # force refresh on entry

    def _to_rgb(self, colour_hex):
        if not colour_hex:
            return (0, 0, 0)
        return pygame.Color(colour_hex)

    def update(self, now):
        if now - self.last_update >= 10 or not self.departures:
            self.departures, next_run = self.ctx['stop'].get_next_departures(5, return_next_run = True)
            self.stops = self.ctx["ptv_api"].get_pid_stops(next_run, self.ctx['stop'].stop_id)
            self.last_update = now

    def draw(self, screen):
        config = self.ctx["config"]
        fonts = self.ctx["fonts"]
        colourMap = self.ctx["colourMap"]

        screen.fill(config.LIGHT_WARM_GREY)
        if not self.departures:
            return

        departure = self.departures[0]
        colour = self._to_rgb(colourMap.get(departure["route_gtfs_id"]))

        pygame.draw.rect(screen, colour, (0, 0, config.SCREEN_RES[0], 10))
        platform_rect = pygame.draw.rect(screen, colour, (344, 14, 31, 31))
        text = fonts["platform_large"].render(departure.get("platform", "-"), True, config.WHITE)
        text_rect = text.get_rect(); text_rect.center = platform_rect.center
        screen.blit(text, text_rect.topleft)

        text = fonts["dest_large"].render(departure["destination"], True, config.BLACK)
        screen.blit(text, (113, 19))

        text = fonts["dep_large"].render(departure.get("departure_time", "--:--"), True, config.BLACK)
        screen.blit(text, (11, 21))

        r = pygame.draw.rect(screen, config.BLACK, (379, 15, 91, 31))
        t = fonts["ttd_large"].render(departure.get("time_to_departure", "-"), True, config.WHITE)
        tr = t.get_rect(); tr.center = r.center
        screen.blit(t, tr.topleft)

        formatted = f"{departure['express_note']} {departure['departure_note']}"
        t = fonts["f_reg_15"].render(formatted, True, config.BLACK)
        screen.blit(t, (10,51))
        self.draw_stop_list(screen, config, colour, x=11, y=78, stop_h=15, stop_w=116, bar_width=3, v_padding=7, font=fonts["stops"], tick=(3,2), text_offset=9)

        gap = 26
        for i in range(1, 3):
            if len(self.departures) <= i:
                continue
            dep = self.departures[i]
            colour = self._to_rgb(colourMap.get(dep["route_gtfs_id"]))
            offset = (i - 1) * gap
            container = pygame.Rect(11, 212 + offset, 342, 26)

            r = pygame.Rect(0, 0, 4, 17); r.midleft = container.midleft
            pygame.draw.rect(screen, colour, r)

            r = pygame.Rect(283, 0, 18, 18); r.centery = container.centery
            r = pygame.draw.rect(screen, colour, r)
            t = fonts["platform_small"].render(dep.get("platform", "-"), True, config.WHITE)
            tr = t.get_rect(); tr.center = r.center
            screen.blit(t, tr.topleft)

            t = fonts["f_reg_10"].render(dep['express_note'], True, config.BLACK)
            tr = t.get_rect()
            tr.centery = container.centery
            tr.right = 275
            screen.blit(t, tr.topleft)

            r = pygame.Rect(303, 0, 50, 18); r.centery = container.centery
            r = pygame.draw.rect(screen, config.BLACK, r)
            t = fonts["ttd_small"].render(dep.get("time_to_departure", "-"), True, config.WHITE)
            tr = t.get_rect(); tr.center = r.center
            screen.blit(t, tr.topleft)

            t = fonts["dep_small"].render(dep.get("departure_time", "--:--"), True, config.BLACK)
            tr = t.get_rect(); tr.centery = container.centery
            screen.blit(t, (16, tr.top))

            t = fonts["dest_small"].render(dep.get("destination", "-"), True, config.BLACK)
            tr = t.get_rect(); tr.centery = container.centery
            screen.blit(t, (75, tr.top))

        pygame.draw.line(screen, config.BLACK, (11, 70), (config.SCREEN_RES[0] - 11, 70), 2)
        pygame.draw.line(screen, config.BLACK, (11, 213), (353, 213), 2)
        pygame.draw.line(screen, config.BLACK, (11, 238), (353, 238), 2)

        time_rect = pygame.draw.rect(screen, config.BLACK, (358, 213, 113, 48))
        pygame.draw.rect(screen, config.LIGHT_WARM_GREY, (360, 215, 109, 44))
        current_time = datetime.now().strftime("%I:%M:%S %p").lower()
        text = fonts["clock"].render(current_time, True, config.BLACK)
        text_rect = text.get_rect(); text_rect.center = time_rect.center
        screen.blit(text, text_rect.topleft)

    def draw_stop_list(self, screen, config, colour, x, y, stop_h, stop_w, bar_width, v_padding, font, tick, text_offset):
        pygame.draw.rect(screen, colour, (x, y, bar_width, v_padding))
        # Divide the height up into chunk
        for c_idx, stop_chunk in enumerate(self.stops):
            for r_idx, stop in enumerate(stop_chunk):
                container = pygame.Rect(0,0, stop_w, stop_h)
                container.x = x + stop_w * c_idx
                container.y = y + v_padding + stop_h * r_idx
                if stop[3] is not None: # actual stop
                    if stop[2]: # terminus
                        # Cap
                        r_temp = pygame.Rect(container.x,container.y,bar_width,stop_h)
                        r = pygame.Rect(0,0, 9, 3)
                        r.centerx = r_temp.centerx
                        r.centery = container.centery
                        pygame.draw.rect(screen, colour, r)
                        # Main bar
                        pygame.draw.rect(screen, colour, (container.x,container.y,bar_width,round(stop_h / 2)))
                    else:    
                        # Main Bar
                        r = pygame.draw.rect(screen, colour, (container.x,container.y,bar_width,stop_h))
                        # Tick
                        r = pygame.Rect(0,0, tick[0], tick[1])
                        r.centery = container.centery
                        r.x = container.x + bar_width
                        pygame.draw.rect(screen, colour, r)
                    # Station name
                    if c_idx == 0 and r_idx == 0:
                        t = font.render(stop[0], True, (255, 255, 255))
                        tr = t.get_rect(); tr.centery = container.centery; tr.x = container.x + text_offset
                        r_box = pygame.Rect(0, 0, tr.size[0] + 4, tr.size[1]+2)
                        r_box.centery = container.centery; r_box.x = container.x + text_offset - 2
                        pygame.draw.rect(screen, colour, r_box)
                        screen.blit(t, tr.topleft)
                    else:
                        textcol = config.MID_GREY if stop[1] else config.BLACK
                        t = font.render(stop[0], True, textcol)
                        tr = t.get_rect(); tr.centery = container.centery; tr.x = container.x + text_offset
                        screen.blit(t, tr)
                        if (r_idx == 0 or r_idx == len(stop_chunk) - 1) and not stop[2]:
                            if r_idx == 0:
                                pygame.draw.rect(screen, colour, (container.x, y, bar_width, 2))
                                pygame.draw.rect(screen, colour, (container.x, y+3, bar_width, 2))
                                pygame.draw.rect(screen, colour, (container.x, y+6, bar_width, v_padding-6))
                            if r_idx == len(stop_chunk) - 1:
                                # --- BOTTOM DOT-DOT LINES ---
                                # Bottom starts at bottom of container
                                base_y = container.y + container.height

                                pygame.draw.rect(screen, colour, (container.x, base_y, bar_width, v_padding-6))
                                pygame.draw.rect(screen, colour, (container.x, base_y + v_padding - 5, bar_width, 2))
                                pygame.draw.rect(screen, colour, (container.x, base_y + v_padding - 2, bar_width, 2))

        def draw_subsequent_departure(screen, colour, x, y, w, bar_thickness, departure_time, departure_time_font, departure_dest, departure_dest_font, note, note_font):
            h = 24
            container = pygame.Rect(x,y,w,h)
            inner_container = pygame.Rect(x, y + bar_thickness, w, h-bar_thickness)
            # Top Bar
            pygame.draw.rect(screen, colour, (x, y, w, bar_thickness))
            # Colour Bar
            r = pygame.Rect(0,0, 18, 4)
            r.centery = inner_container.centery
            pygame.draw.rect(screen, colour, r)
            # Text (departure time)
            t = departure_time_font.render(f'{departure_time}', True, (0,0,0))
            tr = t.get_rect()
            tr.centery = inner_container.centery
            tr.x = x + 9
            screen.blit(t, tr.topleft)
            # Text (departure destination)
            t = departure_dest_font.render(f'{departure_dest}', True, (0,0,0))
            tr = t.get_rect()
            tr.centery = inner_container.centery
            tr.x = x + 66
            screen.blit(t, tr.topleft)
            # Text (departure note)
            t = note_font.render(f'{note}', True, (0,0,0))
            tr = t.get_rect()
            tr.centery = inner_container.centery
            tr.x = x + 161
            screen.blit(t, tr.topleft)




        def express_stop():
            return



