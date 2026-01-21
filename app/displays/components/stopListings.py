import pygame
from fonts import FontManager as Fonts

class StopListings:

    @staticmethod
    def metro_stop_listing_large(
        config,
        stops,
        colour,
        h_padding = 11,
        stop_h = 15,
        stop_w = 116,
        bar_width = 4,
        v_padding = 7,
        font = None,
        tick = (3,2),
        text_offset = 9
    ):
        """
        Render a large metro stop listing and return it as a Surface.

        bar_width should be an even number
        """
        # Fonts
        if font is None:
            font = Fonts.get("regular", 12)

        # --- Calculate surface size ---
        cols = len(stops)
        rows = max(len(chunk) for chunk in stops)

        width = stop_w * cols
        height = v_padding + (stop_h * rows)

        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))

        # --- Top bar ---
        pygame.draw.rect(surface, colour, (0, 0, bar_width, v_padding))

        all_stops = [s for chunk in stops for s in chunk]
        skip_block_active = False
        stop_index = 0

        for c_idx, stop_chunk in enumerate(stops):
            for r_idx, stop in enumerate(stop_chunk):

                container = pygame.Rect(
                    c_idx * stop_w,
                    v_padding + r_idx * stop_h,
                    stop_w,
                    stop_h
                )

                if stop["stop_id"] is not None:

                    if stop["is_terminus"]:
                        # Terminus cap
                        r_temp = pygame.Rect(
                            container.x,
                            container.y,
                            bar_width,
                            stop_h
                        )
                        r = pygame.Rect(0, 0, 9, 3)
                        r.center = r_temp.center
                        pygame.draw.rect(surface, colour, r)

                        # Terminus bar
                        pygame.draw.rect(
                            surface,
                            colour,
                            (container.x, container.y, bar_width, round(stop_h / 2))
                        )

                    else:
                        next_stop = (
                            all_stops[stop_index + 1]
                            if stop_index + 1 < len(all_stops)
                            else None
                        )
                        # Skipped logic
                        if stop["is_skipped"] and next_stop and not next_stop["is_skipped"]:
                            StopListings.draw_express_arrow(
                                surface, container, colour, bar_width=4, arrowtip_y=10
                            )
                            skip_block_active = False

                        elif stop["is_skipped"] and skip_block_active:
                            pygame.draw.rect(
                                surface,
                                colour,
                                (container.x, container.y, bar_width, stop_h)
                            )

                        elif stop["is_skipped"] and not skip_block_active:
                            skip_block_active = True
                            StopListings.draw_express_arrow(
                                surface, container, colour, bar_width=4, arrowtip_y=10
                            )

                        elif not stop["is_skipped"] and not skip_block_active:
                            pygame.draw.rect(
                                surface,
                                colour,
                                (container.x, container.y, bar_width, stop_h)
                            )

                            # Tick
                            r = pygame.Rect(0, 0, tick[0], tick[1])
                            r.centery = container.centery
                            r.x = container.x + bar_width
                            pygame.draw.rect(surface, colour, r)

                    # --- Station name ---
                    if c_idx == 0 and r_idx == 0:
                        t = font.render(stop["name"], True, config.WHITE)
                        tr = t.get_rect()
                        tr.centery = container.centery
                        tr.x = container.x + text_offset

                        r_box = pygame.Rect(
                            tr.x - 2,
                            tr.y - 1,
                            tr.width + 4,
                            tr.height + 2
                        )
                        pygame.draw.rect(surface, colour, r_box)
                        surface.blit(t, tr.topleft)

                    else:
                        textcol = config.MID_GREY if stop["is_skipped"] else config.BLACK
                        t = font.render(stop["name"], True, textcol)
                        tr = t.get_rect()
                        tr.centery = container.centery
                        tr.x = container.x + text_offset
                        surface.blit(t, tr.topleft)

                        # Top dotted continuation
                        if r_idx == 0 and stop != all_stops[0]:
                            pygame.draw.rect(surface, colour, (container.x, 0, bar_width, 2))
                            pygame.draw.rect(surface, colour, (container.x, 3, bar_width, 2))
                            pygame.draw.rect(
                                surface,
                                colour,
                                (container.x, 6, bar_width, v_padding - 6)
                            )

                        # Bottom dotted continuation
                        if r_idx == len(stop_chunk) - 1 and stop != all_stops[-1]:
                            base_y = container.bottom
                            pygame.draw.rect(
                                surface,
                                colour,
                                (container.x, base_y, bar_width, v_padding - 6)
                            )
                            pygame.draw.rect(
                                surface,
                                colour,
                                (container.x, base_y + v_padding - 5, bar_width, 2)
                            )
                            pygame.draw.rect(
                                surface,
                                colour,
                                (container.x, base_y + v_padding - 2, bar_width, 2)
                            )

                stop_index += 1

        return surface
    
    @staticmethod
    def draw_express_arrow(screen, container, colour, bar_width=4, arrowtip_y=10):
        """
        Draw an express/skip arrow indicator.
        
        Args:
            screen: Pygame surface to draw on
            container: Pygame Rect for the container
            colour: Color for the arrow
            bar_width: Width of the bar (should be even)
            arrowtip_y: Y offset for arrow tip
        """
        x = container.x
        y = container.y
        arrowtip_y = y + arrowtip_y
        
        # Arrow tip
        r = pygame.Rect(0, arrowtip_y - 0, 2, 1)
        r.centerx = x + bar_width // 2
        pygame.draw.rect(screen, colour, r)
        
        r = pygame.Rect(0, arrowtip_y - 1, 4, 1)
        r.centerx = x + bar_width // 2
        pygame.draw.rect(screen, colour, r)
        
        r = pygame.Rect(0, arrowtip_y - 2, 6, 1)
        r.centerx = x + bar_width // 2
        pygame.draw.rect(screen, colour, r)
        
        r = pygame.Rect(0, arrowtip_y - 3, 8, 1)
        r.centerx = x + bar_width // 2
        pygame.draw.rect(screen, colour, r)
        
        r = pygame.Rect(0, arrowtip_y - 4, 10, 1)
        r.centerx = x + bar_width // 2
        pygame.draw.rect(screen, colour, r)
        
        r = pygame.Rect(0, arrowtip_y - 5, 8, 1)
        r.centerx = x + bar_width // 2
        pygame.draw.rect(screen, colour, r)
        
        pygame.draw.rect(screen, colour, (x, y, bar_width, r.top - y))
        
        # Arrow bottom
        r = pygame.Rect(0, arrowtip_y + 3, 2, 1)
        r.centerx = x + bar_width // 2
        pygame.draw.rect(screen, colour, r)
        
        r = pygame.Rect(0, arrowtip_y + 2, 1, 2)
        r.x = x
        pygame.draw.rect(screen, colour, r)
        
        r = pygame.Rect(0, arrowtip_y + 2, 1, 2)
        r.x = x + bar_width - 1
        pygame.draw.rect(screen, colour, r)
        
        pygame.draw.rect(screen, colour, (x, r.bottom, bar_width, container.bottom - r.bottom))