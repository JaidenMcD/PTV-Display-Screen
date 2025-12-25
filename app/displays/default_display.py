import pygame
from pathlib import Path
from datetime import datetime
from .base import Display
from .components.trainUI import TrainUI
import utils
from fonts import FontManager as Fonts


class DefaultDisplay(Display):
    def __init__(self, ctx):
        super().__init__(ctx)

    def on_show(self):
        self.last_update = 0  # force refresh on entry

    def _to_rgb(self, colour_hex):
        if not colour_hex:
            return (0, 0, 0)
        return pygame.Color(colour_hex)

    def update(self, now):
        if now - self.last_update >= 10:
            self.last_update = now

    def draw(self, screen):
        config = self.ctx["config"]

        screen.fill(config.LIGHT_WARM_GREY)
    
    
        






