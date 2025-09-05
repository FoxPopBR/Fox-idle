# scrollable_panel.py
import pygame
from config import MARGIN, SCROLLBAR_WIDTH, SCROLLBAR_COLOR, SCROLLBAR_HANDLE_COLOR, BLACK

class ScrollablePanel:
    """Reusable scrollable panel. Holds lines as (text, color).
    scroll is the index of the first visible line (top)."""

    def __init__(self, rect: pygame.Rect, line_height: int):
        self.rect = rect
        self.line_height = line_height
        self.lines = []  # list[(text, color)]
        self.scroll = 0  # top index (first visible line)
        self.dragging = False
        self.drag_offset_delta = 0

    def set_rect(self, rect: pygame.Rect):
        self.rect = rect
        self._ensure_scroll_bounds()

    def set_lines(self, lines):
        self.lines = list(lines)
        self._ensure_scroll_bounds()

    def add_lines(self, lines):
        self.lines.extend(lines)
        self._ensure_scroll_bounds()

    def add_line(self, line):
        self.lines.append(line)
        self._ensure_scroll_bounds()

    def visible_lines_count(self):
        return max(1, (self.rect.height - 2 * MARGIN) // self.line_height)

    def auto_scroll_to_bottom(self):
        total = len(self.lines)
        visible = self.visible_lines_count()
        # desired top index to show last `visible` lines:
        self.scroll = max(0, total - visible)
        self._ensure_scroll_bounds()

    def ensure_line_visible(self, index):
        """Ensure that the given line index (0..len-1) is visible.
        Adjusts self.scroll (top index) if necessary."""
        total = len(self.lines)
        visible = self.visible_lines_count()
        if total <= visible:
            self.scroll = 0
            return
        start = self.scroll
        end = start + visible
        if index < start:
            self.scroll = index
        elif index >= end:
            self.scroll = index - visible + 1
        self._ensure_scroll_bounds()

    def _scrollbar_rects(self):
        bar = pygame.Rect(self.rect.right + MARGIN, self.rect.y, SCROLLBAR_WIDTH, self.rect.height)
        total = len(self.lines)
        visible = self.visible_lines_count()
        if total <= visible:
            handle = pygame.Rect(0, 0, 0, 0)
        else:
            handle_h = max(16, int(bar.height * (visible / total)))
            max_off = max(0, total - visible)
            ratio = 0 if max_off == 0 else (self.scroll / max_off)
            handle_y = bar.y + ratio * (bar.height - handle_h)
            handle = pygame.Rect(bar.x, int(handle_y), bar.width, int(handle_h))
        return bar, handle

    def process_event(self, event):
        """Process wheel and drag of handle."""
        bar, handle = self._scrollbar_rects()
        total = len(self.lines)
        visible = self.visible_lines_count()
        max_off = max(0, total - visible)

        if event.type == pygame.MOUSEWHEEL:
            # wheel up: event.y >0 -> scroll up (show earlier lines) => decrease scroll
            self.scroll = max(0, min(self.scroll - event.y, max_off))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if handle.height > 0 and handle.collidepoint(event.pos):
                self.dragging = True
                self.drag_offset_delta = event.pos[1] - handle.y

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            y_in_bar = event.pos[1] - (bar.y + self.drag_offset_delta)
            y_in_bar = max(0, min(y_in_bar, bar.height - handle.height))
            denom = (bar.height - handle.height)
            ratio = 0 if denom == 0 else (y_in_bar / denom)
            self.scroll = int(ratio * max_off)
            self._ensure_scroll_bounds()

    def _ensure_scroll_bounds(self):
        total = len(self.lines)
        visible = self.visible_lines_count()
        max_off = max(0, total - visible)
        if self.scroll < 0:
            self.scroll = 0
        elif self.scroll > max_off:
            self.scroll = max_off

    def draw(self, font: pygame.font.Font, target_surface: pygame.Surface):
        inner_w = max(1, self.rect.width - 2 * MARGIN)
        inner_h = max(1, self.rect.height - 2 * MARGIN)
        panel_surf = pygame.Surface((inner_w, inner_h))
        panel_surf.fill(BLACK)

        visible = self.visible_lines_count()
        start = max(0, min(self.scroll, max(0, len(self.lines) - visible)))
        end = start + visible

        y = 0
        for text, color in self.lines[start:end]:
            try:
                # se a string está vazia, renderizamos um espaço para evitar erro
                if not text:
                    rendered = font.render(" ", True, color)
                else:
                    rendered = font.render(text, True, color)
            except Exception:
                # fallback: remover caracteres estranhos
                safe = ''.join(ch for ch in text if 32 <= ord(ch) < 0x10FFFF)
                if not safe:
                    safe = " "  # evita zero width
                rendered = font.render(safe, True, color)

            panel_surf.blit(rendered, (0, y))
            y += self.line_height

        target_surface.blit(panel_surf, (self.rect.x + MARGIN, self.rect.y + MARGIN))

        # scrollbar
        bar, handle = self._scrollbar_rects()
        pygame.draw.rect(target_surface, SCROLLBAR_COLOR, bar)
        if handle.height > 0:
            pygame.draw.rect(target_surface, SCROLLBAR_HANDLE_COLOR, handle)