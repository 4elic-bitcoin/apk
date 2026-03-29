import pygame
import random
import sys
import json
import os
from datetime import datetime

# Для Android
try:
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
    ANDROID = True
except ImportError:
    ANDROID = False

# Инициализация
pygame.init()

# Константы - адаптация под мобильные экраны
if ANDROID:
    info = pygame.display.Info()
    SCREEN_WIDTH = min(info.current_w, info.current_h)
    SCREEN_HEIGHT = max(info.current_w, info.current_h)
    BLOCK_SIZE = SCREEN_WIDTH // 12
else:
    BLOCK_SIZE = 30
    SCREEN_WIDTH = 480
    SCREEN_HEIGHT = 800

COLS = 10
ROWS = 20
SIDEBAR_WIDTH = SCREEN_WIDTH - (COLS * BLOCK_SIZE)
FPS = 60

# Файл для сохранения результатов
if ANDROID:
    from android.storage import app_storage_path
    SAVE_FILE = os.path.join(app_storage_path(), "tetris_scores.json")
else:
    SAVE_FILE = "tetris_scores.json"

# Цвета (без изменений)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)
GREEN = (0, 255, 0)

COLORS = {
    'I': (0, 255, 255),
    'O': (255, 255, 0),
    'T': (128, 0, 128),
    'S': (0, 255, 0),
    'Z': (255, 0, 0),
    'J': (0, 0, 255),
    'L': (255, 165, 0),
}

# Фигуры тетрамино (без изменений)
SHAPES = {
    'I': [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    'O': [
        [(0, 0), (1, 0), (0, 1), (1, 1)],
    ] * 4,
    'T': [
        [(0, 1), (1, 1), (2, 1), (1, 0)],
        [(1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (1, 1), (1, 2), (0, 1)],
    ],
    'S': [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    'Z': [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    'J': [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    'L': [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}


class ScoreManager:
    """Менеджер для работы с сохранёнными результатами"""
    
    @staticmethod
    def load_scores():
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    @staticmethod
    def save_score(score, level, lines, player_name="Player"):
        scores = ScoreManager.load_scores()
        
        new_score = {
            'player': player_name,
            'score': score,
            'level': level,
            'lines': lines,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        scores.append(new_score)
        scores.sort(key=lambda x: x['score'], reverse=True)
        scores = scores[:10]
        
        try:
            # Создаём директорию если её нет
            os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(scores, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving score: {e}")
            return False
    
    @staticmethod
    def get_high_score():
        scores = ScoreManager.load_scores()
        if scores:
            return scores[0]['score']
        return 0


class TouchButton:
    """Кнопка для сенсорного управления"""
    def __init__(self, x, y, width, height, text, color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.active_color = tuple(min(c + 50, 255) for c in color)
        self.pressed = False
        
    def draw(self, screen, font):
        color = self.active_color if self.pressed else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=10)
        
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.pressed = False
        return False


class Piece:
    def __init__(self, shape_name=None):
        self.shape_name = shape_name or random.choice(list(SHAPES.keys()))
        self.color = COLORS[self.shape_name]
        self.rotation = 0
        self.x = COLS // 2 - 2
        self.y = 0

    def get_blocks(self):
        shape = SHAPES[self.shape_name][self.rotation]
        return [(self.x + bx, self.y + by) for bx, by in shape]

    def get_blocks_at(self, x, y, rotation):
        shape = SHAPES[self.shape_name][rotation]
        return [(x + bx, y + by) for bx, by in shape]


class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        
        # Адаптивные шрифты
        font_size = max(16, BLOCK_SIZE // 2)
        self.font = pygame.font.SysFont('Arial', font_size)
        self.small_font = pygame.font.SysFont('Arial', max(14, font_size - 4))
        self.big_font = pygame.font.SysFont('Arial', font_size * 2, bold=True)
        
        self.reset_game()
        self.high_score = ScoreManager.get_high_score()
        self.show_save_message = False
        self.save_message_time = 0
        
        # Кнопки управления для Android
        if ANDROID:
            self.setup_touch_controls()

    def setup_touch_controls(self):
        """Создание сенсорных кнопок для Android"""
        button_height = BLOCK_SIZE * 2
        button_width = COLS * BLOCK_SIZE // 4
        y_pos = SCREEN_HEIGHT - button_height - 10
        
        self.buttons = {
            'left': TouchButton(10, y_pos, button_width, button_height, "◄"),
            'right': TouchButton(button_width + 20, y_pos, button_width, button_height, "►"),
            'rotate': TouchButton(button_width * 2 + 30, y_pos, button_width, button_height, "↻"),
            'drop': TouchButton(button_width * 3 + 40, y_pos, button_width, button_height, "▼"),
        }
        
        # Дополнительные кнопки
        top_button_width = COLS * BLOCK_SIZE // 3
        self.buttons['pause'] = TouchButton(10, 10, top_button_width, button_height // 2, "⏸")
        self.buttons['restart'] = TouchButton(top_button_width + 20, 10, top_button_width, button_height // 2, "↻ R")

    def reset_game(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.current_piece = Piece()
        self.next_piece = Piece()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.fall_time = 0
        self.fall_speed = 1000
        self.fast_fall = False

    def valid_position(self, piece, x, y, rotation):
        blocks = piece.get_blocks_at(x, y, rotation)
        for bx, by in blocks:
            if bx < 0 or bx >= COLS or by >= ROWS:
                return False
            if by >= 0 and self.board[by][bx] is not None:
                return False
        return True

    def lock_piece(self):
        blocks = self.current_piece.get_blocks()
        for bx, by in blocks:
            if by < 0:
                self.game_over = True
                return
            self.board[by][bx] = self.current_piece.color

        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = Piece()

        if not self.valid_position(self.current_piece,
                                   self.current_piece.x,
                                   self.current_piece.y,
                                   self.current_piece.rotation):
            self.game_over = True

    def clear_lines(self):
        lines_to_clear = []
        for y in range(ROWS):
            if all(self.board[y][x] is not None for x in range(COLS)):
                lines_to_clear.append(y)

        for y in lines_to_clear:
            del self.board[y]
            self.board.insert(0, [None for _ in range(COLS)])

        count = len(lines_to_clear)
        if count > 0:
            points = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += points.get(count, 800) * self.level
            self.lines_cleared += count
            self.level = self.lines_cleared // 10 + 1
            self.fall_speed = max(100, 1000 - (self.level - 1) * 80)
            
            if self.score > self.high_score:
                self.high_score = self.score

    def move(self, dx, dy):
        new_x = self.current_piece.x + dx
        new_y = self.current_piece.y + dy
        if self.valid_position(self.current_piece, new_x, new_y,
                               self.current_piece.rotation):
            self.current_piece.x = new_x
            self.current_piece.y = new_y
            return True
        return False

    def rotate(self):
        new_rotation = (self.current_piece.rotation + 1) % 4
        if self.valid_position(self.current_piece,
                               self.current_piece.x,
                               self.current_piece.y,
                               new_rotation):
            self.current_piece.rotation = new_rotation
        elif self.valid_position(self.current_piece,
                                 self.current_piece.x - 1,
                                 self.current_piece.y,
                                 new_rotation):
            self.current_piece.x -= 1
            self.current_piece.rotation = new_rotation
        elif self.valid_position(self.current_piece,
                                 self.current_piece.x + 1,
                                 self.current_piece.y,
                                 new_rotation):
            self.current_piece.x += 1
            self.current_piece.rotation = new_rotation

    def hard_drop(self):
        while self.move(0, 1):
            self.score += 2
        self.lock_piece()

    def get_ghost_y(self):
        ghost_y = self.current_piece.y
        while self.valid_position(self.current_piece,
                                  self.current_piece.x,
                                  ghost_y + 1,
                                  self.current_piece.rotation):
            ghost_y += 1
        return ghost_y

    def save_current_score(self):
        if self.score > 0:
            success = ScoreManager.save_score(
                self.score, 
                self.level, 
                self.lines_cleared
            )
            if success:
                self.show_save_message = True
                self.save_message_time = pygame.time.get_ticks()
                self.high_score = ScoreManager.get_high_score()
                return True
        return False

    def draw_block(self, x, y, color, alpha=255):
        rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE,
                           BLOCK_SIZE, BLOCK_SIZE)
        s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
        s.fill(color)
        s.set_alpha(alpha)
        self.screen.blit(s, rect)
        pygame.draw.rect(self.screen, DARK_GRAY, rect, 1)
        
        if alpha == 255:
            highlight = tuple(min(c + 40, 255) for c in color)
            pygame.draw.line(self.screen, highlight,
                           (rect.left + 1, rect.top + 1),
                           (rect.right - 2, rect.top + 1))
            pygame.draw.line(self.screen, highlight,
                           (rect.left + 1, rect.top + 1),
                           (rect.left + 1, rect.bottom - 2))

    def draw_board(self):
        field_rect = pygame.Rect(0, 0, COLS * BLOCK_SIZE, ROWS * BLOCK_SIZE)
        pygame.draw.rect(self.screen, BLACK, field_rect)

        for x in range(COLS):
            for y in range(ROWS):
                rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE,
                                   BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(self.screen, DARK_GRAY, rect, 1)

        for y in range(ROWS):
            for x in range(COLS):
                if self.board[y][x] is not None:
                    self.draw_block(x, y, self.board[y][x])

    def draw_piece(self, piece):
        blocks = piece.get_blocks()
        for bx, by in blocks:
            if by >= 0:
                self.draw_block(bx, by, piece.color)

    def draw_ghost(self):
        ghost_y = self.get_ghost_y()
        blocks = self.current_piece.get_blocks_at(
            self.current_piece.x, ghost_y,
            self.current_piece.rotation)
        for bx, by in blocks:
            if by >= 0:
                self.draw_block(bx, by, self.current_piece.color, alpha=50)

    def draw_sidebar(self):
        sidebar_x = COLS * BLOCK_SIZE
        sidebar_rect = pygame.Rect(sidebar_x, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, (30, 30, 30), sidebar_rect)
        pygame.draw.line(self.screen, WHITE,
                        (sidebar_x, 0), (sidebar_x, SCREEN_HEIGHT), 2)

        title = self.font.render("NEXT:", True, WHITE)
        self.screen.blit(title, (sidebar_x + 10, 20))

        shape = SHAPES[self.next_piece.shape_name][0]
        offset_x = sidebar_x + SIDEBAR_WIDTH // 4
        offset_y = 60
        for bx, by in shape:
            rect = pygame.Rect(offset_x + bx * (BLOCK_SIZE // 2),
                              offset_y + by * (BLOCK_SIZE // 2),
                              BLOCK_SIZE // 2, BLOCK_SIZE // 2)
            pygame.draw.rect(self.screen, self.next_piece.color, rect)
            pygame.draw.rect(self.screen, DARK_GRAY, rect, 1)

        y_pos = 140
        labels = [
            ("SCORE", str(self.score)),
            ("HIGH", str(self.high_score)),
            ("LEVEL", str(self.level)),
            ("LINES", str(self.lines_cleared)),
        ]
        for label, value in labels:
            text = self.small_font.render(label, True, GRAY)
            self.screen.blit(text, (sidebar_x + 10, y_pos))
            y_pos += 18
            
            color = GREEN if label == "HIGH" and self.score >= self.high_score and self.score > 0 else WHITE
            text = self.font.render(value, True, color)
            self.screen.blit(text, (sidebar_x + 10, y_pos))
            y_pos += 30

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        text = self.big_font.render("GAME OVER", True, (255, 50, 50))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(text, rect)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_text, rect)

        if self.score > 0 and self.score == self.high_score:
            new_record = self.font.render("NEW RECORD!", True, GREEN)
            rect = new_record.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(new_record, rect)

        restart_text = self.font.render("Tap to restart", True, GRAY)
        rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        self.screen.blit(restart_text, rect)

    def draw_pause(self):
        overlay = pygame.Surface((COLS * BLOCK_SIZE, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        text = self.big_font.render("PAUSED", True, WHITE)
        rect = text.get_rect(center=(COLS * BLOCK_SIZE // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, rect)

    def draw_save_message(self):
        if self.show_save_message:
            current_time = pygame.time.get_ticks()
            if current_time - self.save_message_time < 2000:
                message = self.font.render("Score saved!", True, GREEN)
                x = (COLS * BLOCK_SIZE) // 2 - message.get_width() // 2
                y = 30
                
                bg_rect = pygame.Rect(x - 10, y - 5, message.get_width() + 20, message.get_height() + 10)
                pygame.draw.rect(self.screen, (0, 100, 0), bg_rect)
                pygame.draw.rect(self.screen, GREEN, bg_rect, 2)
                
                self.screen.blit(message, (x, y))
            else:
                self.show_save_message = False

    def draw_touch_controls(self):
        """Рисует сенсорные кнопки"""
        if ANDROID:
            for button in self.buttons.values():
                button.draw(self.screen, self.font)

    def run(self):
        while True:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_current_score()
                    pygame.quit()
                    sys.exit()

                # Обработка сенсорного управления
                if ANDROID and not self.game_over and not self.paused:
                    if self.buttons['left'].handle_event(event):
                        self.move(-1, 0)
                    elif self.buttons['right'].handle_event(event):
                        self.move(1, 0)
                    elif self.buttons['rotate'].handle_event(event):
                        self.rotate()
                    elif self.buttons['drop'].handle_event(event):
                        self.hard_drop()
                
                if ANDROID:
                    if self.buttons['pause'].handle_event(event):
                        self.paused = not self.paused
                    if self.buttons['restart'].handle_event(event):
                        self.save_current_score()
                        self.reset_game()

                # Обработка экрана Game Over
                if event.type == pygame.MOUSEBUTTONDOWN and self.game_over:
                    self.save_current_score()
                    self.reset_game()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.save_current_score()
                        self.reset_game()
                        continue

                    if event.key == pygame.K_s:
                        self.save_current_score()
                        continue

                    if self.game_over:
                        continue

                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                        continue

                    if self.paused:
                        continue

                    if event.key == pygame.K_LEFT:
                        self.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.move(1, 0)
                    elif event.key == pygame.K_DOWN:
                        self.fast_fall = True
                    elif event.key == pygame.K_UP:
                        self.rotate()
                    elif event.key == pygame.K_SPACE:
                        self.hard_drop()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_DOWN:
                        self.fast_fall = False

            if self.game_over or self.paused:
                self.draw_board()
                self.draw_piece(self.current_piece)
                self.draw_sidebar()
                if ANDROID:
                    self.draw_touch_controls()
                if self.game_over:
                    self.draw_game_over()
                elif self.paused:
                    self.draw_pause()
                self.draw_save_message()
                pygame.display.flip()
                continue

            self.fall_time += dt
            speed = self.fall_speed // 5 if self.fast_fall else self.fall_speed

            if self.fall_time >= speed:
                self.fall_time = 0
                if not self.move(0, 1):
                    self.lock_piece()
                elif self.fast_fall:
                    self.score += 1

            self.screen.fill(BLACK)
            self.draw_board()
            self.draw_ghost()
            self.draw_piece(self.current_piece)
            self.draw_sidebar()
            if ANDROID:
                self.draw_touch_controls()
            self.draw_save_message()
            pygame.display.flip()


if __name__ == "__main__":
    game = Tetris()
    game.run()