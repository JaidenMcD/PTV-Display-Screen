import pygame
from datetime import datetime
from .base import Display

class AltDisplay(Display):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.message = "Alt display placeholder"
        self.last_seen = None

    def on_show(self):
        # Record when this screen was shown
        self.last_seen = datetime.now()

    def update(self, now):
        # Nothing to update yet; keeps interface parity
        pass

    def draw(self, screen):
        config = self.ctx["config"]
        fonts = self.ctx["fonts"]

        screen.fill(config.NETWORK_GREY)

        title = fonts["dest_large"].render("Next screen coming soon", True, config.WHITE)
        sub = fonts["dest_small"].render(self.message, True, config.WHITE)

        title_rect = title.get_rect(center=(config.SCREEN_RES[0] // 2, 120))
        sub_rect = sub.get_rect(center=(config.SCREEN_RES[0] // 2, 160))

        screen.blit(title, title_rect.topleft)
        screen.blit(sub, sub_rect.topleft)

        if self.last_seen:
            ts = self.last_seen.strftime("%I:%M:%S %p").lower()
            ts_text = fonts["dep_small"].render(f"Shown: {ts}", True, config.WHITE)
            ts_rect = ts_text.get_rect(center=(config.SCREEN_RES[0] // 2, 200))
            screen.blit(ts_text, ts_rect.topleft)
