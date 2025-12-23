import pygame
from datetime import datetime
import utils

class TramUI:
    """Reusable UI drawing components for all displays."""

    @staticmethod
    def tram_departure_item(config, w, h, route_no, destination, time_to_departure, colour, text_colour, font, destination_padding):
        """ Create a surface for a tram departure item """
        screen = pygame.Surface((w, h))

        # Route Number Box
        r = pygame.draw.rect(screen, colour, (0, 0, h, h))
        t = font.render(route_no, True, text_colour)
        tr = t.get_rect()
        tr.center = r.center
        screen.blit(t, tr.topleft)

        # TTD box
        r = pygame.draw.rect(screen, config.NETWORK_GREY, (w - h, 0, h, h))
        t = font.render(time_to_departure, True, config.WHITE)
        tr = t.get_rect()
        tr.center = r.center
        screen.blit(t, tr.topleft)

        # Destination Text
        r = pygame.draw.rect(screen, config.WHITE, (h, 0, w - h*2, h))
        t = font.render(destination, True, config.BLACK)
        tr = t.get_rect()
        tr.centery = h // 2
        tr.x = h + destination_padding   
        screen.blit(t, tr.topleft)

        return screen

    @staticmethod
    def tram_footer(w,h,time,config,font,h_padding):
        """ Create a surface for the tram footer """
        screen = pygame.Surface((w, h))
        screen.fill(config.NETWORK_GREY)

        # Current Time
        t = font.render(time, True, config.WHITE)
        tr = t.get_rect()
        tr.x = h_padding
        tr.centery = h // 2
        screen.blit(t, tr.topleft)

        # Logo
        t = font.render('tramtracker', True, config.WHITE)
        tr = t.get_rect()
        tr.right = w - h_padding
        tr.centery = h // 2
        screen.blit(t, tr.topleft)
        return screen
    
    @staticmethod
    def alert(config, fonts, header, description, url, w, h):
        """ Create a surface for special event alert """
        screen = pygame.Surface((w, h), pygame.SRCALPHA)
        
        header_height = 75
        # info img
        img = pygame.transform.smoothscale(pygame.image.load(url),(header_height,header_height))

        # Header
        header_surf = pygame.Surface((w - header_height, header_height), pygame.SRCALPHA)
        wrapped_lines = utils.wrap_text(header, fonts['f_bold_25'], w - header_height)
        for i, line in enumerate(wrapped_lines):
            t = fonts['f_bold_25'].render(line, True, config.BLACK)
            tr = t.get_rect()
            tr.x = 0
            tr.y = 20 + (i * 22)
            header_surf.blit(t, tr.topleft)

        r = header_surf.get_rect()
        img_r = img.get_rect()
        screen.blit(img, (0, 0))
        r.centery = img_r.centery
        screen.blit(header_surf, (header_height + 10, 0))

        #info
        info_surf = pygame.Surface((w, h - header_height), pygame.SRCALPHA)
        wrapped_lines = utils.wrap_text(description, fonts['f_reg_12'], w - 20)
        for i, line in enumerate(wrapped_lines):
            t = fonts['f_reg_12'].render(line, True, config.BLACK)
            tr = t.get_rect()
            tr.x = 10
            tr.y = 10 + (i * 16)
            info_surf.blit(t, tr.topleft)
        info_r = info_surf.get_rect()
        info_r.top = header_height
        screen.blit(info_surf, info_r.topleft)

   

        return screen