""" Font handler """
import pygame
import re
from pathlib import Path

class FontManager:
    FONT_PATH = Path(__file__).resolve().parent / "assets" / "fonts"

    # Weight -> filename mapping
    WEIGHT_MAP = {
        "bold": "NETWORKSANS-2019-BOLD.TTF",
        "medium": "NETWORKSANS-2019-MEDIUM.TTF",
        "regular": "NETWORKSANS-2019-REGULAR.TTF",
        "regular-italic": "NETWORKSANS-2019-REGULARITALIC.TTF",
        "light": "NETWORKSANS-2019-LIGHT.TTF"
    }

    # Valid size range
    MIN_SIZE = 6
    MAX_SIZE = 100

    _cache = {}

    @classmethod
    def get(cls, weight, size):
        """Get a font by weight and size, creating/caching it as needed."""
        if weight not in cls.WEIGHT_MAP:
            raise ValueError(
                f"Invalid weight '{weight}'. Must be one of: {list(cls.WEIGHT_MAP.keys())}"
            )
        
        if size < cls.MIN_SIZE or size > cls.MAX_SIZE:
            raise ValueError(
                f"Font size {size} out of range [{cls.MIN_SIZE}, {cls.MAX_SIZE}]"
            )
        
        cache_key = f"{weight}-{size}"
        if cache_key not in cls._cache:
            filename = cls.WEIGHT_MAP[weight]
            cls._cache[cache_key] = pygame.font.Font(
                str(cls.FONT_PATH / filename), 
                size
            )
        return cls._cache[cache_key]
    
    @classmethod
    def get_all(cls):
        """Return a dictionary of all cached fonts."""
        return dict(cls._cache)

