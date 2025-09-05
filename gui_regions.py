# gui_regions.py
import pygame
from config import MARGIN, SCROLLBAR_WIDTH

class GUIRegions:
    def __init__(self, surface, chat_window, input_box):
        self.surface = surface
        self.chat_window = chat_window
        self.input_box = input_box
        self.update_rects()

    def update_rects(self):
        self.player_rect = pygame.Rect(
            MARGIN, MARGIN,
            self.surface.get_width() - 2 * MARGIN,
            int(self.surface.get_height() * 0.1) - 2 * MARGIN
        )
        chat_rect = self.chat_window.get_chat_rect()
        x = chat_rect.right + SCROLLBAR_WIDTH + MARGIN
        width = self.surface.get_width() - x - MARGIN
        self.game_rect = pygame.Rect(
            x,
            self.player_rect.bottom + MARGIN,
            width,
            int(self.surface.get_height() * 0.8) - 2 * MARGIN - (self.player_rect.bottom + MARGIN)
        )

    def get_area_at_pos(self, pos):
        if self.chat_window.get_chat_rect().collidepoint(pos):
            return 'chat'
        if self.input_box.rect.collidepoint(pos):
            return 'input'
        if self.player_rect.collidepoint(pos):
            return 'player'
        if self.game_rect.collidepoint(pos):
            return 'game'
        return None

    def draw_active_highlight(self, active_area):
        if active_area == 'chat':
            rect = self.chat_window.get_chat_rect()
        elif active_area == 'input':
            rect = self.input_box.rect
        elif active_area == 'player':
            rect = self.player_rect
        elif active_area == 'game':
            rect = self.game_rect
        else:
            return
        pygame.draw.rect(self.surface, (255, 255, 0), rect, 3)