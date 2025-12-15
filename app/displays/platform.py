import pygame
from datetime import datetime
from .base import Display

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
        r = pygame.draw.rect(screen, config.BLACK, (379, 15, 91, 31))
        t = fonts["f_reg_23"].render(departure.get("time_to_departure", "-"), True, config.WHITE)
        tr = t.get_rect(); tr.center = r.center
        screen.blit(t, tr.topleft)

        # Draw platform number onyl if multiple platforms
        if self.multi_platform:
            platform_rect = pygame.draw.rect(screen, colour, (344, 14, 31, 31))
            text = fonts["f_bold_25"].render(departure.get("platform", "-"), True, config.WHITE)
            text_rect = text.get_rect(); text_rect.center = platform_rect.center
            screen.blit(text, text_rect.topleft)

        formatted = f"{departure['express_note']} {departure['departure_note']}"
        t = fonts["f_reg_12"].render(formatted, True, config.BLACK)
        screen.blit(t, (10,51))

        pygame.draw.rect(screen, config.BLACK, (11,77, config.SCREEN_RES[0] - 11*2, 1))

        self.draw_stop_list(screen, config, colour, x=11, y=78, stop_h=15, stop_w=116, bar_width=4, v_padding=7, font=fonts["stops"], tick=(3,2), text_offset=9)

        current_time = datetime.now().strftime("%I:%M:%S %p").lower()
        self.draw_clock(screen, config, 369, 216, 102, 46, 2, fonts["f_med_14"], current_time)


        gap = 3
        y = 216
        for i in range(1,3): 
            dep = self.departures[i]
            colour = self._to_rgb(colourMap.get(dep["route_gtfs_id"]))
            y = self.draw_subsequent_departure(screen, colour, y, departure_time=dep["departure_time"], 
                                               departure_time_font = fonts["f_reg_13"], departure_dest = dep["destination"], 
                                               departure_dest_font=fonts["f_med_12"], note = dep["express_note"], note_font=fonts["f_reg_9"], 
                                               time_until_departure = dep["time_to_departure"], 
                                               platform=dep["platform"], w=351, bar_thickness=1, x=9, include_platform = self.multi_platform)
            y = y + gap
        
        
        #pygame.draw.line(screen, config.BLACK, (11, 213), (353, 213), 2)
        #pygame.draw.line(screen, config.BLACK, (11, 238), (353, 238), 2)

        
        

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

                if stop[3] is not None: # actual stop
                    # Determine s
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
                        # if skipped and the next station is not skipped
                        if stop[1] and not all_stops[stop_index+1][1]:
                            self.draw_express_arrow(screen, container, colour, arrowtip_y = 10, b_w = 4)
                            skip_block_active = False
                        # If skipped and already inside skip block:
                        elif stop[1] and skip_block_active:
                            # Main Bar
                            r = pygame.draw.rect(screen, colour, (container.x,container.y,bar_width,stop_h))
                        # if skipped and not yet inside a skip block:
                        elif stop[1] and not skip_block_active:
                            skip_block_active = True
                            self.draw_express_arrow(screen, container, colour, arrowtip_y = 10, b_w = 4)
                        # if not skipped and not inside a skip block
                        elif not stop[1] and not skip_block_active:
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
    def draw_express_arrow(self,screen, container, colour, arrowtip_y, b_w):
       # arrow
       x = container.x
       y = container.y
       arrowtip_y = y + arrowtip_y
       
       r = pygame.Rect(0,arrowtip_y - 0 ,2,1); r.centerx = x + b_w // 2; pygame.draw.rect(screen, colour, r)
       r = pygame.Rect(0,arrowtip_y - 1 ,4,1); r.centerx = x + b_w // 2; pygame.draw.rect(screen, colour, r)
       r = pygame.Rect(0,arrowtip_y - 2 ,6,1); r.centerx = x + b_w // 2; pygame.draw.rect(screen, colour, r)
       r = pygame.Rect(0,arrowtip_y - 3 ,8,1); r.centerx = x + b_w // 2; pygame.draw.rect(screen, colour, r)
       r = pygame.Rect(0,arrowtip_y - 4 ,10,1); r.centerx = x + b_w // 2; pygame.draw.rect(screen, colour, r)
       r = pygame.Rect(0,arrowtip_y - 5 ,8,1); r.centerx = x + b_w // 2; pygame.draw.rect(screen, colour, r)
       pygame.draw.rect(screen, colour, (x, y, b_w, r.top - y))

       r = pygame.Rect(0,arrowtip_y + 3 ,2,1); r.centerx = x + b_w // 2; pygame.draw.rect(screen, colour, r)
       r = pygame.Rect(0,arrowtip_y + 2 ,1,2); r.x = x; pygame.draw.rect(screen, colour, r)
       r = pygame.Rect(0,arrowtip_y + 2 ,1,2); r.x = x+b_w-1; pygame.draw.rect(screen, colour, r)
       pygame.draw.rect(screen, colour, (x, r.bottom, b_w, container.bottom - r.bottom))



    def draw_subsequent_departure(self, screen, colour, y, departure_time, departure_time_font, departure_dest, departure_dest_font,
                                note, note_font, time_until_departure, platform,
                                w=351, bar_thickness=2, x=9, include_platform=True):
        h = 24
        container = pygame.Rect(x,y,w,h)
        inner_container = pygame.Rect(x, y + bar_thickness, w, h-bar_thickness)
        # Top Bar
        pygame.draw.rect(screen, (0,0,0), (x, y, w, bar_thickness))
        # Colour Bar
        r = pygame.Rect(0,0, 4, 18)
        r.centery = inner_container.centery
        r.x = inner_container.x
        pygame.draw.rect(screen, colour, r)
        # Text (departure time)
        departure_time = departure_time.lstrip('0')
        t = departure_time_font.render(f'{departure_time}', True, (0,0,0))
        tr = t.get_rect()
        tr.centery = inner_container.centery
        tr.x = x + 9
        screen.blit(t, tr.topleft)
        # Text (departure destination)
        xpos = tr.right + 14
        t = departure_dest_font.render(f'{departure_dest}', True, (0,0,0))
        tr = t.get_rect()
        tr.centery = inner_container.centery
        tr.x = xpos
        screen.blit(t, tr.topleft)
        # Time until departure box
        r = pygame.Rect(302,0,49,18)
        r.centery = inner_container.centery
        pygame.draw.rect(screen, (0,0,0), r)
        info_xlim = r.x
        # time until departure
        t = departure_time_font.render(f'{time_until_departure}', True, (255,255,255))
        tr = t.get_rect()
        tr.centery = r.centery
        tr.centerx = r.centerx
        screen.blit(t, tr.topleft)
        # Platform number box
        if include_platform:
            rp = pygame.Rect(0,0,18,18)
            rp.centery = inner_container.centery
            rp.right = r.left - 5
            pygame.draw.rect(screen, colour, rp)
            info_xlim = rp.x
            # Platform number
            t = departure_time_font.render(f'{platform}', True, (255,255,255))
            tr = t.get_rect()
            tr.centery = inner_container.centery
            tr.centerx = rp.centerx
            screen.blit(t, tr.topleft)
            
        # Text (departure note)
        t = note_font.render(f'{note}', True, (0,0,0))
        tr = t.get_rect()
        tr.centery = inner_container.centery
        tr.right = info_xlim - 10
        screen.blit(t, tr.topleft)
        return inner_container.bottom


    def draw_clock(self, screen, config, x, y, w, h, border_width, font, time):
        pygame.draw.rect(screen, config.BLACK, (x,y,w,h))
        r = pygame.draw.rect(screen, config.LIGHT_WARM_GREY, (x+border_width, y+border_width, w-border_width*2, h-border_width*2))
        t = font.render(time, True, config.BLACK)
        tr = t.get_rect(); tr.center = r.center
        screen.blit(t, tr.topleft)

        def express_stop():
            return



