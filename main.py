# main.py
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, FONT_NAME, FONT_SIZE, BLACK
from chat_window import ChatWindow
from input_box import InputBox
from gui_regions import GUIRegions

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Fox-idle Chat Game")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)

    # habilita key repeat (mantém comportamento de repetir teclas)
    pygame.key.set_repeat(400, 40)

    chat_window = ChatWindow(screen)
    input_box = InputBox(screen, chat_window)  # Passa chat_window como argumento
    gui_regions = GUIRegions(screen, chat_window, input_box)

    active_area = 'input'
    area_order = ['chat', 'input', 'player', 'game']

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                chat_window.surface = screen
                chat_window.rebuild_cache()
                input_box.surface = screen
                input_box.update_rects()
                gui_regions.surface = screen
                gui_regions.update_rects()

            # clique ativa a area (apenas click)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = gui_regions.get_area_at_pos(event.pos)
                if clicked:
                    active_area = clicked

            # Tab alterna areas
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                idx = (area_order.index(active_area) + 1) % len(area_order)
                active_area = area_order[idx]

            # encaminhar eventos
            # chat recebe scroll/drag se mouse estiver sobre ela ou se handle está sendo arrastado
            chat_window.process_event(event)

            # input recebe eventos somente quando está ativa (controla digitação e scroll)
            if active_area == 'input':
                sent = input_box.process_event(event)
                if sent is not None and sent != "":
                    chat_window.add_message("user", sent)
                    # bot responde "N/D"
                    chat_window.add_message("bot", "N/D")

        # updates
        input_box.update(dt)
        chat_window.update(dt)

        # draw
        screen.fill(BLACK)
        chat_window.draw(font, active_area)
        input_box.draw(active_area, font)
        gui_regions.draw_active_highlight(active_area)

        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()