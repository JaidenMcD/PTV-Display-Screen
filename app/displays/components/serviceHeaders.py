import pygame
from fonts import FontManager as Fonts
from .trainUI import TrainUI

class ServiceHeaders():

    @staticmethod
    def metro_departure_header(
        config,
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
        time_dest_gap=12,
        v_margin = 16,
        dep_time_font=None,
        time_to_dep_font=None,
        dest_font=None,
        dep_note_font=None,
        platform_font=None
    ):

        """
        Render a single metro departure header as a Pygame surface.

        Args:
            config: Configuration object containing colour definitions.
            colour: RGB colour tuple used for the platform indicator box.
            time_to_dep: Time until departure (e.g. ``"5 min"``).
            dep_time: Scheduled departure time (e.g. ``"10:30"``).
            dest: Destination name.
            dep_note: Supplementary note text (e.g. ``"Express"``).
            platform: Platform number to display. If ``None``, the platform
                indicator is omitted.
            width: Width of the rendered surface in pixels.
            h: Base height of the rendered surface in pixels.
            ttd_box: ``(width, height)`` of the time-to-departure box.
            h_margin: Horizontal margin used for left-aligned elements.
            title_spacing: Horizontal offset for the destination text.
            v_margin: Vertical margin from the top of the surface.
            dep_time_font: Font used for the scheduled departure time.
            time_to_dep_font: Font used for the time-to-departure text.
            dest_font: Font used for the destination name.
            dep_note_font: Font used for the departure note.
            platform_font: Font used for the platform number.

        Returns:
            pygame.Surface: A transparent surface containing the rendered
            departure header.
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
        
        # Normalise departure time (remove leading zero from hour if present)
        if dep_time and dep_time[0] == "0":
            dep_time = dep_time[1:]

        # Adjust height to account for font descent
        gap = dep_note_font.get_descent()
        h = h + gap

        surface = pygame.Surface((width, h), pygame.SRCALPHA)
        surface.fill((0,0,0,0))

        # Time-to-departure box
        TrainUI.time_to_departure(
            surface,
            config,
            width - (ttd_box[0] + h_margin),
            v_margin, ttd_box[0],
            ttd_box[1],
            time_to_dep_font,
            time_to_dep,
            bg_color=config.BLACK
        )

        # Destination
        dest_text = dest_font.render(dest, True, config.BLACK)
        dest_rect = dest_text.get_rect()
        dest_rect.centery = v_margin + (ttd_box[1] // 2)
        #dest_rect.x = title_spacing
        #surface.blit(dest_text, dest_rect.topleft)

        baseline_y = dest_rect.y + dest_font.get_ascent()
        
        # Scheduled departure time
        time_y = baseline_y - dep_time_font.get_ascent()
        dep_time_text = dep_time_font.render(dep_time, True, config.BLACK)
        dep_time_rect = dep_time_text.get_rect()

        dep_time_rect.x = h_margin
        dep_time_rect.y = time_y

        dest_rect.x = dep_time_rect.right + time_dest_gap

        surface.blit(dep_time_text, dep_time_rect.topleft)
        surface.blit(dest_text, dest_rect.topleft)

        # Platform indicator
        if platform is not None:
            platform_rect = pygame.draw.rect(
                surface,
                colour,
                (
                    width - (ttd_box[0] + h_margin),
                    v_margin,
                    ttd_box[1],
                    ttd_box[1],
                ),
            )
            platform_text = platform_font.render(str(platform), True, config.WHITE)
            text_rect = platform_text.get_rect(center=platform_rect.center)
            surface.blit(platform_text, text_rect.topleft)

        ## Departure note
        note_text = dep_note_font.render(dep_note, True, config.BLACK)
        note_rect = note_text.get_rect()
        note_rect.bottom = h
        note_rect.x = h_margin
        surface.blit(note_text, note_rect.topleft)

        return surface