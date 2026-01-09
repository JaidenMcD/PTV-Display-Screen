import pygame
from fonts import FontManager as Fonts
from .trainUI import TrainUI

class ServiceHeaders():

    @staticmethod
    def metro_departure_header(config,
                                colour,
                                time_to_dep,
                                dep_time, 
                                dest, 
                                dep_note,
                                platform = None, 
                                width = 480,
                                h = 62,
                                ttd_box = (98,30),
                                h_margin = 10,
                                title_spacing = 84,
                                v_margin = 16,
                                dep_time_font=None,
                                time_to_dep_font=None,
                                dest_font=None,
                                dep_note_font=None,
                                platform_font=None
                                ):

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

        # Fonts

        if dep_time_font is None:
            dep_time_font = Fonts.get("regular", 21)
        if time_to_dep_font is None:
            time_to_dep_font = Fonts.get("regular", 23)
        if dest_font is None:
            dest_font = Fonts.get("bold", 27)
        if dep_note_font is None:
            dep_note_font = Fonts.get("regular", 12)
        if platform_font is None:
            platform_font = Fonts.get("bold", 25)

        # Calculate Screen Height
        gap = dep_note_font.get_descent()
        h = h + gap
        surface = pygame.Surface((width, h), pygame.SRCALPHA)
        surface.fill((0,0,0,0))

        # Time to departure
        TrainUI.time_to_departure(surface, config, width - (ttd_box[0] + h_margin), v_margin, ttd_box[0], ttd_box[1], time_to_dep_font, time_to_dep, bg_color=config.BLACK)

        # Destination
        t = dest_font.render(dest, True, config.BLACK)
        tr = t.get_rect()
        tr.centery = v_margin + (ttd_box[1]//2)
        tr.x = title_spacing
        surface.blit(t, tr.topleft)

        baseline_y = tr.y + dest_font.get_ascent()

        # Departure Time
        time_y = baseline_y - dep_time_font.get_ascent()
        text = dep_time_font.render(dep_time, True, config.BLACK)
        surface.blit(text, (h_margin, time_y))

        # Draw platform number only if multiple platforms
        if platform is not None:
            platform_rect = pygame.draw.rect(
                surface, colour,
                (width - (ttd_box[0] + h_margin), v_margin, ttd_box[1], ttd_box[1])
            )
            text = platform_font.render(str(platform), True, config.WHITE)
            text_rect = text.get_rect()
            text_rect.center = platform_rect.center
            surface.blit(text, text_rect.topleft)

        # Dep note
        t = dep_note_font.render(dep_note, True, config.BLACK)
        tr = t.get_rect()
        tr.bottom = h
        tr.x = h_margin
        surface.blit(t, tr.topleft)

        return surface