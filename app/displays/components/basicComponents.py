import pygame

class BasicComponents:

    @staticmethod
    def headerBar(width, height, colour):
        s = pygame.Surface((width,height))
        s.fill(colour)
        return s