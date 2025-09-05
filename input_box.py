# input_box.py
import pygame
import pyperclip
from config import (
    FONT_NAME, FONT_SIZE, MARGIN, SEND_BUTTON_WIDTH, SEND_BUTTON_HEIGHT,
    SCROLLBAR_WIDTH, BLACK, BORDER_COLOR
)
from scrollable_panel import ScrollablePanel
from chat_window import ChatWindow  # Adicionado para acesso a get_game_info_rect

class InputBox:
    def __init__(self, surface, chat_window):
        self.surface = surface
        self.chat_window = chat_window  # Referência para calcular o y correto
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
        self.line_height = FONT_SIZE + 6
        # text_lines represents the visible lines (including wrapped lines)
        self.text_lines = ['']
        # cursor: line index and column index within that line
        self.cursor_line = 0
        self.cursor_col = 0

        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.cursor_interval = 0.5
        self.active = True  # start active for convenience

        self.panel = None
        self.update_rects()

    def get_input_rect(self):
        # Posiciona a input com 5 pixels de margem acima, após o fim da região game_info
        game_info_bottom = self.chat_window.get_game_info_rect().bottom
        y = game_info_bottom + MARGIN  # Margem de 5 pixels acima da input
        height = int(self.surface.get_height() * 0.12) - 2 * MARGIN  # Ajusta altura com margens internas
        width = self.surface.get_width() - 2 * MARGIN
        return pygame.Rect(MARGIN, y, width, height)

    def update_rects(self):
        self.rect = self.get_input_rect()

        total_text_width = self.rect.width - SEND_BUTTON_WIDTH - 4 * MARGIN
        self.text_panel_rect = pygame.Rect(
            self.rect.x + MARGIN,
            self.rect.y + MARGIN,
            total_text_width - SCROLLBAR_WIDTH,
            self.rect.height - 2 * MARGIN
        )
        self.scrollbar_rect = pygame.Rect(
            self.text_panel_rect.right + MARGIN,
            self.rect.y + MARGIN,
            SCROLLBAR_WIDTH,
            self.rect.height - 2 * MARGIN
        )
        self.send_button_rect = pygame.Rect(
            self.rect.x + self.rect.width - SEND_BUTTON_WIDTH - MARGIN,
            self.rect.y + (self.rect.height - SEND_BUTTON_HEIGHT) // 2,
            SEND_BUTTON_WIDTH, SEND_BUTTON_HEIGHT
        )

        if self.panel is None:
            self.panel = ScrollablePanel(self.text_panel_rect, self.line_height)
        else:
            self.panel.set_rect(self.text_panel_rect)
            self._sync_panel_lines(keep_scroll=True)

    def _sync_panel_lines(self, keep_scroll=False):
        arr = [(ln, (255, 255, 255)) for ln in self.text_lines]
        self.panel.set_lines(arr)
        if keep_scroll:
            self.panel._ensure_scroll_bounds()

    def _cursor_absolute_index(self):
        return self.cursor_line

    def _auto_scroll_to_cursor(self):
        self.panel.ensure_line_visible(self._cursor_absolute_index())

    def _reflow_from(self, start_idx=0):
        """Reflow wrapping starting from start_idx. Uses pixel width from font and text_panel_rect width."""
        max_w = max(4, self.text_panel_rect.width)
        i = start_idx
        while i < len(self.text_lines):
            line = self.text_lines[i]
            # if fits, advance
            if self.font.size(line)[0] <= max_w:
                i += 1
                continue
            # find overflow position: smallest j such that width(line[:j]) > max_w
            j = 1
            L = len(line)
            while j <= L and self.font.size(line[:j])[0] <= max_w:
                j += 1
            overflow_pos = j - 1
            # try to break at last space before overflow_pos
            split_at = None
            for k in range(overflow_pos, 0, -1):
                if line[k-1] == ' ':
                    split_at = k
                    break
            if split_at is None:
                split_at = overflow_pos
            left = line[:split_at].rstrip()
            right = line[split_at:].lstrip()
            self.text_lines[i] = left
            self.text_lines.insert(i+1, right)
            # adjust cursor
            if self.cursor_line == i:
                if self.cursor_col > len(left):
                    self.cursor_line += 1
                    self.cursor_col -= len(left)
            elif self.cursor_line > i:
                self.cursor_line += 1
            # continue checking the new right part in next iteration
            i += 1

    def _reflow_all(self):
        # Reflow entire buffer (used after paste or big edits)
        # We'll re-merge and then re-wrap paragraphs separated by explicit newlines
        paragraphs = "\n".join(self.text_lines).split("\n")
        self.text_lines = []
        for p in paragraphs:
            # break paragraph into wrapped lines
            cur = p
            if cur == "":
                self.text_lines.append("")
                continue
            while True:
                if self.font.size(cur)[0] <= self.text_panel_rect.width:
                    self.text_lines.append(cur)
                    break
                # find split
                j = 1
                L = len(cur)
                while j <= L and self.font.size(cur[:j])[0] <= self.text_panel_rect.width:
                    j += 1
                overflow_pos = j - 1
                split_at = None
                for k in range(overflow_pos, 0, -1):
                    if cur[k-1] == ' ':
                        split_at = k
                        break
                if split_at is None:
                    split_at = overflow_pos
                left = cur[:split_at].rstrip()
                right = cur[split_at:].lstrip()
                self.text_lines.append(left)
                cur = right

    def process_event(self, event):
        # click send button
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.send_button_rect.collidepoint(event.pos):
                text = "\n".join(self.text_lines)
                # reset
                self.text_lines = ['']
                self.cursor_line = 0
                self.cursor_col = 0
                self._sync_panel_lines()
                return text

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            # forward to panel if clicking scrollbar/handle
            if self.panel:
                bar, handle = self.panel._scrollbar_rects()
                if handle.height > 0 and handle.collidepoint(event.pos):
                    self.panel.process_event(event)
            return None

        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
            if self.panel and self.panel.dragging:
                self.panel.process_event(event)

        if event.type == pygame.MOUSEWHEEL:
            if self.text_panel_rect.collidepoint(pygame.mouse.get_pos()) or self.panel.dragging:
                self.panel.process_event(event)
            return None

        if not self.active:
            return None

        # KEY INPUT
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()

            # Behavior: ENTER -> new line; SHIFT+ENTER -> SEND (reverted to original)
            if event.key == pygame.K_RETURN:
                if mods & pygame.KMOD_SHIFT:
                    # Send (Shift+Enter)
                    text = "\n".join(self.text_lines)
                    self.text_lines = ['']
                    self.cursor_line = 0
                    self.cursor_col = 0
                    self._sync_panel_lines()
                    return text
                else:
                    # Insert newline at cursor
                    current = self.text_lines[self.cursor_line]
                    left = current[:self.cursor_col]
                    right = current[self.cursor_col:]
                    self.text_lines[self.cursor_line] = left
                    self.text_lines.insert(self.cursor_line + 1, right)
                    self.cursor_line += 1
                    self.cursor_col = 0
                    # reflow from previous line just in case
                    start = max(0, self.cursor_line - 1)
                    self._reflow_from(start)
                    self._sync_panel_lines(keep_scroll=True)
                    self._auto_scroll_to_cursor()
                    return None

            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_col > 0:
                    line = self.text_lines[self.cursor_line]
                    self.text_lines[self.cursor_line] = line[:self.cursor_col - 1] + line[self.cursor_col:]
                    self.cursor_col -= 1
                    self._reflow_from(self.cursor_line)
                else:
                    if self.cursor_line > 0:
                        prev = self.text_lines[self.cursor_line - 1]
                        curr = self.text_lines[self.cursor_line]
                        new_col = len(prev)
                        self.text_lines[self.cursor_line - 1] = prev + curr
                        self.text_lines.pop(self.cursor_line)
                        self.cursor_line -= 1
                        self.cursor_col = new_col
                        self._reflow_from(max(0, self.cursor_line - 1))
                self._sync_panel_lines(keep_scroll=True)
                self._auto_scroll_to_cursor()

            elif event.key == pygame.K_DELETE:
                line = self.text_lines[self.cursor_line]
                if self.cursor_col < len(line):
                    self.text_lines[self.cursor_line] = line[:self.cursor_col] + line[self.cursor_col + 1:]
                    self._reflow_from(self.cursor_line)
                else:
                    if self.cursor_line + 1 < len(self.text_lines):
                        self.text_lines[self.cursor_line] = line + self.text_lines[self.cursor_line + 1]
                        self.text_lines.pop(self.cursor_line + 1)
                        self._reflow_from(max(0, self.cursor_line - 1))
                self._sync_panel_lines(keep_scroll=True)
                self._auto_scroll_to_cursor()

            elif event.key == pygame.K_LEFT:
                if self.cursor_col > 0:
                    self.cursor_col -= 1
                elif self.cursor_line > 0:
                    self.cursor_line -= 1
                    self.cursor_col = len(self.text_lines[self.cursor_line])
                self._auto_scroll_to_cursor()

            elif event.key == pygame.K_RIGHT:
                if self.cursor_col < len(self.text_lines[self.cursor_line]):
                    self.cursor_col += 1
                elif self.cursor_line + 1 < len(self.text_lines):
                    self.cursor_line += 1
                    self.cursor_col = 0
                self._auto_scroll_to_cursor()

            elif event.key == pygame.K_UP:
                if self.cursor_line > 0:
                    self.cursor_line -= 1
                    self.cursor_col = min(self.cursor_col, len(self.text_lines[self.cursor_line]))
                    self._auto_scroll_to_cursor()

            elif event.key == pygame.K_DOWN:
                if self.cursor_line + 1 < len(self.text_lines):
                    self.cursor_line += 1
                    self.cursor_col = min(self.cursor_col, len(self.text_lines[self.cursor_line]))
                    self._auto_scroll_to_cursor()

            elif event.key == pygame.K_HOME:
                self.cursor_col = 0
                self._auto_scroll_to_cursor()

            elif event.key == pygame.K_END:
                self.cursor_col = len(self.text_lines[self.cursor_line])
                self._auto_scroll_to_cursor()

            # paste / copy
            elif event.key == pygame.K_v and (mods & pygame.KMOD_CTRL):
                paste = pyperclip.paste()
                if paste:
                    parts = paste.split("\n")
                    current = self.text_lines[self.cursor_line]
                    left = current[:self.cursor_col]
                    right = current[self.cursor_col:]
                    left += parts[0]
                    if len(parts) == 1:
                        self.text_lines[self.cursor_line] = left + right
                        self.cursor_col = len(left)
                        self._reflow_from(self.cursor_line)
                    else:
                        self.text_lines[self.cursor_line] = left
                        for i, p in enumerate(parts[1:]):
                            self.text_lines.insert(self.cursor_line + 1 + i, p)
                        self.text_lines[self.cursor_line + len(parts) - 1] += right
                        self.cursor_line += len(parts) - 1
                        self.cursor_col = len(self.text_lines[self.cursor_line]) - len(right)
                        self._reflow_from(max(0, self.cursor_line - len(parts)))
                    self._sync_panel_lines(keep_scroll=True)
                    self._auto_scroll_to_cursor()

            elif event.key == pygame.K_c and (mods & pygame.KMOD_CTRL):
                pyperclip.copy("\n".join(self.text_lines))

            else:
                # normal character insertion
                if event.unicode:
                    line = self.text_lines[self.cursor_line]
                    self.text_lines[self.cursor_line] = line[:self.cursor_col] + event.unicode + line[self.cursor_col:]
                    self.cursor_col += 1
                    self._reflow_from(self.cursor_line)
                    self._sync_panel_lines(keep_scroll=True)
                    self._auto_scroll_to_cursor()

        return None

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_interval:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.0

    def draw(self, active_area, font):
        # draw input background / border
        pygame.draw.rect(self.surface, BORDER_COLOR, self.rect, 2)
        if active_area == 'input' and self.active:
            pygame.draw.rect(self.surface, (255, 255, 0), self.rect, 3)

        # ensure panel holds lines but don't destroy panel.lines permanently
        old_lines = list(self.panel.lines)
        panel_lines = [(ln, (255, 255, 255)) for ln in self.text_lines]

        # insert cursor visual
        if self.cursor_visible and self.active:
            idx = self._cursor_absolute_index()
            if 0 <= idx < len(panel_lines):
                text, col = panel_lines[idx]
                cpos = max(0, min(self.cursor_col, len(text)))
                text_with_cursor = text[:cpos] + "|" + text[cpos:]
                panel_lines[idx] = (text_with_cursor, col)

        self.panel.lines = panel_lines
        self.panel.draw(self.font, self.surface)
        self.panel.lines = old_lines

        # draw send button
        pygame.draw.rect(self.surface, (0, 128, 0), self.send_button_rect)
        label = self.font.render("Enviar", True, (255, 255, 255))
        self.surface.blit(label, label.get_rect(center=self.send_button_rect.center))