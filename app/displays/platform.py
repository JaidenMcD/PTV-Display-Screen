import pygame
from datetime import datetime
from .base import Display

class PlatformDisplay(Display):
    def __init__(self, ctx, platform = None):
        super().__init__(ctx)
        self.departures = []
        self.stops = []
        self.platform_no = platform
        self.last_update = 0

    def on_show(self):
        self.last_update = 0  # force refresh on entry

    def _to_rgb(self, colour_hex):
        if not colour_hex:
            return (0, 0, 0)
        return pygame.Color(colour_hex)

    def update(self, now):
        if now - self.last_update >= 10 or not self.departures:
            self.departures, next_run = self.ctx['stop'].get_next_departures(5, return_next_run = True, platform = self.platform_no)
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

        for c_idx, stop_chunk in enumerate(self.stops):
            for r_idx, stop in enumerate(stop_chunk):
                container = pygame.Rect(0, 0, 116, 14)
                container.x = 11 + 116 * c_idx
                container.y = 78 + 14 * r_idx

                if c_idx == 0 and r_idx == 0:
                    t = fonts["stops"].render(stop[0], True, config.WHITE)
                    tr = t.get_rect(); tr.centery = container.centery; tr.x = container.x + 12
                    r_box = pygame.Rect(0, 0, tr.size[0] + 4, 16)
                    r_box.centery = container.centery; r_box.x = container.x + 10
                    pygame.draw.rect(screen, colour, r_box)
                    screen.blit(t, tr.topleft)
                else:
                    t = fonts["stops"].render(stop[0], True, config.BLACK)
                    tr = t.get_rect(); tr.centery = container.centery; tr.x = container.x + 12
                    screen.blit(t, tr)

                r = pygame.Rect(0, 0, 3, 4); r.midleft = (container.x + 4, container.centery)
                pygame.draw.rect(screen, colour, r)

                if r_idx == 0 and stop[2]:
                    r = pygame.Rect(0, 0, 9, 4); r.centery = container.centery; r.x = container.x - 2
                    pygame.draw.rect(screen, colour, r)
                    r = pygame.Rect(0, 0, 4, 5); r.bottomleft = container.bottomleft
                    pygame.draw.rect(screen, colour, r)
                elif r_idx == len(stop_chunk) - 1 and stop[2]:
                    r = pygame.Rect(0, 0, 9, 4); r.centery = container.centery; r.x = container.x - 2
                    pygame.draw.rect(screen, colour, r)
                    pygame.draw.rect(screen, colour, (container.x, container.y, 4, 5))
                else:
                    r = pygame.Rect(0, 0, 4, 14); r.midleft = (container.x, container.centery)
                    pygame.draw.rect(screen, colour, r)

                if r_idx == 0 and not stop[2]:
                    for h, y_off in [(3, 0), (1, -4), (2, -7)]:
                        r = pygame.Rect(0, 0, 4, h); r.bottomleft = (container.x, container.y + y_off)
                        pygame.draw.rect(screen, colour, r)
                if r_idx == len(stop_chunk) - 1 and not stop[2]:
                    for h, y_off in [(2, container.height), (1, container.height + 4), (3, container.height + 7)]:
                        r = pygame.Rect(0, 0, 4, h)
                        r.topleft = (container.x, container.y + y_off)
                        pygame.draw.rect(screen, colour, r)

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
