import pygame
from config import (
    FONT_SIZE, PLAYER_INFO_HEIGHT_RATIO, CHATBOX_WIDTH_RATIO, MAIN_AREA_HEIGHT_RATIO,
    BORDER_COLOR, BORDER_WIDTH, BLACK, USER_COLOR, BOT_COLOR, MARGIN, SCROLLBAR_WIDTH
)
from scrollable_panel import ScrollablePanel

class ChatWindow:
    def __init__(self, surface):
        self.surface = surface
        self.line_height = FONT_SIZE + 5
        self.messages = []  # list of dicts {sender, text}
        self._create_panel()
        self._rebuild_lines_from_messages()

    def _create_panel(self):
        rect = self.get_chat_rect()
        self.panel = ScrollablePanel(rect, self.line_height)

    def get_player_info_rect(self):
        return pygame.Rect(
            MARGIN, MARGIN,
            self.surface.get_width() - 2 * MARGIN,
            int(self.surface.get_height() * PLAYER_INFO_HEIGHT_RATIO) - 2 * MARGIN
        )

    def get_chat_rect(self):
        y = self.get_player_info_rect().bottom + MARGIN
        height = int(self.surface.get_height() * MAIN_AREA_HEIGHT_RATIO) - 2 * MARGIN
        width = int(self.surface.get_width() * CHATBOX_WIDTH_RATIO) - MARGIN - SCROLLBAR_WIDTH
        return pygame.Rect(MARGIN, y, width, height)

    def get_game_info_rect(self):
        y = self.get_player_info_rect().bottom + MARGIN
        height = int(self.surface.get_height() * MAIN_AREA_HEIGHT_RATIO) - 2 * MARGIN
        x = self.get_chat_rect().right + SCROLLBAR_WIDTH + 2 * MARGIN
        width = self.surface.get_width() - x - MARGIN
        return pygame.Rect(x, y, width, height)

    def rebuild_cache(self):
        self.panel.set_rect(self.get_chat_rect())
        self._rebuild_lines_from_messages()
        self.panel._ensure_scroll_bounds()
        self.panel.auto_scroll_to_bottom()  # Forçar rolagem ao final após redimensionamento

    def _rebuild_lines_from_messages(self):
        flat = []
        for msg in self.messages:
            color = USER_COLOR if msg["sender"] == "user" else BOT_COLOR
            lines = msg["text"].split("\n") if msg["text"] != "" else [""]
            prefix = f'{msg["sender"].capitalize()}: '
            flat.append((prefix + lines[0], color))
            indent = " " * len(prefix)
            for ln in lines[1:]:
                flat.append((indent + ln, color))
        self.panel.set_lines(flat)

    def add_message(self, sender, text):
        self.messages.append({"sender": sender, "text": text})
        self._rebuild_lines_from_messages()
        self.panel._ensure_scroll_bounds()
        self.panel.auto_scroll_to_bottom()  # Forçar rolagem ao final após nova mensagem

    def process_event(self, event):
        chat_rect = self.get_chat_rect()
        if event.type == pygame.MOUSEWHEEL:
            if chat_rect.collidepoint(pygame.mouse.get_pos()) and not self.panel.dragging:
                self.panel.process_event(event)
            return

        bar, handle = self.panel._scrollbar_rects()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if handle.height > 0 and handle.collidepoint(event.pos):
                self.panel.process_event(event)
                return

        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
            if self.panel.dragging:
                self.panel.process_event(event)

    def update(self, dt):
        pass

    def draw(self, font, active_area):
        p_rect = self.get_player_info_rect()
        pygame.draw.rect(self.surface, BORDER_COLOR, p_rect, BORDER_WIDTH)
        player_text = font.render("Informações do Jogador", True, (0, 200, 0))
        self.surface.blit(player_text, (p_rect.x + MARGIN, p_rect.y + MARGIN))

        chat_rect = self.get_chat_rect()
        pygame.draw.rect(self.surface, BORDER_COLOR, chat_rect, BORDER_WIDTH)
        if self.panel.rect != chat_rect:
            self.panel.set_rect(chat_rect)
            self.panel._ensure_scroll_bounds()
            self.panel.auto_scroll_to_bottom()  # Forçar rolagem ao final após atualização do retângulo
        self.panel.draw(font, self.surface)

        g_rect = self.get_game_info_rect()
        pygame.draw.rect(self.surface, BORDER_COLOR, g_rect, BORDER_WIDTH)
        game_text = font.render("Informações do Jogo", True, (200, 0, 0))
        self.surface.blit(game_text, (g_rect.x + MARGIN, g_rect.y + MARGIN))

        if active_area == 'chat':
            pygame.draw.rect(self.surface, (255, 255, 0), chat_rect, 3)