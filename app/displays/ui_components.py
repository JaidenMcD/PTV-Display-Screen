import pygame
from datetime import datetime

class UIComponents:
    """Reusable UI drawing components for all displays."""
    
    @staticmethod
    def draw_clock(screen, config, x, y, w, h, border_width, font, time):
        """
        Draw a clock display with border and centered time text.
        
        Args:
            screen: Pygame surface to draw on
            config: Config object with color definitions
            x, y: Top-left coordinates
            w, h: Width and height
            border_width: Width of the border
            font: Pygame font for time text
            time: Time string (e.g., "10:30:45 am")
        """
        pygame.draw.rect(screen, config.BLACK, (x, y, w, h))
        r = pygame.draw.rect(screen, config.LIGHT_WARM_GREY, 
                            (x+border_width, y+border_width, 
                             w-border_width*2, h-border_width*2))
        t = font.render(time, True, config.BLACK)
        tr = t.get_rect()
        tr.center = r.center
        screen.blit(t, tr.topleft)

    @staticmethod
    def time_to_departure(screen, config, x, y, w, h, font, time_text, bg_color=None):
        """
        Draw a simple time display box with optional background color.
        
        Args:
            screen: Pygame surface to draw on
            config: Config object with color definitions
            x, y: Top-left coordinates
            w, h: Width and height
            font: Pygame font
            time_text: Text to display
            bg_color: Background color (defaults to BLACK)
        """
        bg_color = bg_color or config.BLACK
        pygame.draw.rect(screen, bg_color, (x, y, w, h))
        t = font.render(time_text, True, config.WHITE)
        tr = t.get_rect()
        tr.center = (x + w//2, y + h//2)
        screen.blit(t, tr.topleft)

    @staticmethod
    def draw_departure_item(screen, config, colour, y, departure_time, departure_time_font, 
                           departure_dest, departure_dest_font, note, note_font, 
                           time_until_departure, platform=None, 
                           w=351, bar_thickness=2, x=9, include_platform=True):
        """
        Draw a single departure item (used for subsequent departures).
        
        Args:
            screen: Pygame surface to draw on
            config: Config object with color definitions
            colour: Color for the left bar and platform box (route color)
            y: Y coordinate
            departure_time: Time string (e.g., "10:30am")
            departure_time_font: Pygame font for time
            departure_dest: Destination name
            departure_dest_font: Pygame font for destination
            note: Note text (e.g., "Express", "Stops all")
            note_font: Pygame font for note
            time_until_departure: Time until departure (e.g., "5 min")
            platform: Platform number (optional)
            w, h: Width and height
            bar_thickness: Thickness of top separator bar
            x: X coordinate
            include_platform: Whether to show platform box
            
        Returns:
            Y coordinate of the bottom of the drawn item
        """
        h = 24
        container = pygame.Rect(x, y, w, h)
        inner_container = pygame.Rect(x, y + bar_thickness, w, h - bar_thickness)
        
        # Top separator bar
        pygame.draw.rect(screen, config.BLACK, (x, y, w, bar_thickness))
        
        # Left colour bar
        r = pygame.Rect(0, 0, 4, 18)
        r.centery = inner_container.centery
        r.x = inner_container.x
        pygame.draw.rect(screen, colour, r)
        
        # Departure time
        departure_time_clean = departure_time.lstrip('0')
        t = departure_time_font.render(f'{departure_time_clean}', True, config.BLACK)
        tr = t.get_rect()
        tr.centery = inner_container.centery
        tr.x = x + 9
        screen.blit(t, tr.topleft)
        
        # Destination
        xpos = tr.right + 14
        t = departure_dest_font.render(f'{departure_dest}', True, config.BLACK)
        tr = t.get_rect()
        tr.centery = inner_container.centery
        tr.x = xpos
        screen.blit(t, tr.topleft)
        
        # Time until departure box
        r = pygame.Rect(302, 0, 49, 18)
        r.centery = inner_container.centery
        pygame.draw.rect(screen, config.BLACK, r)
        info_xlim = r.x
        
        # Time until departure text
        t = departure_time_font.render(f'{time_until_departure}', True, config.WHITE)
        tr = t.get_rect()
        tr.centery = r.centery
        tr.centerx = r.centerx
        screen.blit(t, tr.topleft)
        
        # Platform number box
        if include_platform and platform is not None:
            rp = pygame.Rect(0, 0, 18, 18)
            rp.centery = inner_container.centery
            rp.right = r.left - 5
            pygame.draw.rect(screen, colour, rp)
            info_xlim = rp.x
            
            # Platform number
            t = departure_time_font.render(f'{platform}', True, config.WHITE)
            tr = t.get_rect()
            tr.centery = inner_container.centery
            tr.centerx = rp.centerx
            screen.blit(t, tr.topleft)
        
        # Departure note
        t = note_font.render(f'{note}', True, config.BLACK)
        tr = t.get_rect()
        tr.centery = inner_container.centery
        tr.right = info_xlim - 10
        screen.blit(t, tr.topleft)
        
        return inner_container.bottom

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

    @staticmethod
    def get_current_time_string(format_str="%I:%M:%S %p"):
        """
        Get the current time as a formatted string.
        
        Args:
            format_str: Python datetime format string
            
        Returns:
            Formatted time string in lowercase
        """
        return datetime.now().strftime(format_str).lower()