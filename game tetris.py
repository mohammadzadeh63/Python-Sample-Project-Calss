"""
Tetris – Single-file Python (Pygame)
Controls:
  ←/→ : move
  ↓    : soft drop
  ↑ or X : rotate clockwise
  Z       : rotate counter‑clockwise
  Space   : hard drop
  C       : hold (swap) piece
  P       : pause
  R       : restart
  Q or Esc: quit

Requirements:
  pip install pygame

Run:
  python tetris.py
"""
from __future__ import annotations
import math
import random
import sys
import pygame as pg

# --------------------------- Config ---------------------------
COLS, ROWS = 10, 20
CELL = 30
SIDEBAR = 200
MARGIN = 18
WIDTH = COLS * CELL + SIDEBAR + MARGIN * 3
HEIGHT = ROWS * CELL + MARGIN * 2
FPS = 60

# Colors
BG = (11, 13, 20)
GRID = (28, 33, 50)
TEXT = (227, 232, 240)
MUTED = (150, 160, 180)
OUTLINE = (25, 31, 47)

COLORS = {
    'I': (0, 199, 255),
    'J': (59, 130, 246),
    'L': (245, 158, 11),
    'O': (252, 211, 77),
    'S': (34, 197, 94),
    'T': (168, 85, 247),
    'Z': (239, 68, 68),
}

SHAPES = {
    'I': [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    'J': [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
    'L': [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
    'O': [[1, 1], [1, 1]],
    'S': [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
    'T': [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
    'Z': [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
}

SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


# --------------------------- Helpers ---------------------------

def rotate_matrix(m):
    n = len(m)
    res = [[0] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            res[x][n - 1 - y] = m[y][x]
    return trim_matrix(res)


def trim_matrix(m):
    # Remove empty rows/cols around a shape
    if not m:
        return [[1]]
    top = 0
    bottom = len(m) - 1
    left = 0
    right = len(m[0]) - 1

    while top <= bottom and all(v == 0 for v in m[top]):
        top += 1
    while bottom >= top and all(v == 0 for v in m[bottom]):
        bottom -= 1
    while left <= right and all(row[left] == 0 for row in m):
        left += 1
    while right >= left and all(row[right] == 0 for row in m):
        right -= 1

    if top > bottom or left > right:
        return [[1]]
    out = [row[left:right + 1] for row in m[top:bottom + 1]]
    return out


# --------------------------- Core classes ---------------------------
class Piece:
    def __init__(self, kind: str):
        self.kind = kind
        self.matrix = trim_matrix([row[:] for row in SHAPES[kind]])
        self.color = COLORS[kind]
        self.x = COLS // 2 - len(self.matrix[0]) // 2
        self.y = -1  # spawn slightly above
        self.lock_delay_ms = 0

    def clone(self) -> 'Piece':
        p = Piece(self.kind)
        p.matrix = [row[:] for row in self.matrix]
        p.color = self.color
        p.x = self.x
        p.y = self.y
        return p


class Game:
    def __init__(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.bag: list[str] = []
        self.hold: Piece | None = None
        self.hold_used = False
        self.next_queue: list[str] = []
        self.paused = False
        self.game_over = False
        self.drop_ms = 900
        self.gravity_timer = 0
        self.spawn_new()
        # preload next
        while len(self.next_queue) < 5:
            self.refill_bag()
        self.update_speed()

    # --- bag / spawn ---
    def refill_bag(self):
        if not self.bag:
            self.bag = ['I', 'J', 'L', 'O', 'S', 'T', 'Z']
            random.shuffle(self.bag)
        while self.bag and len(self.next_queue) < 5:
            self.next_queue.append(self.bag.pop())

    def spawn_new(self):
        if not self.next_queue:
            self.refill_bag()
        kind = self.next_queue.pop(0) if self.next_queue else random.choice(list(SHAPES))
        self.current = Piece(kind)
        self.hold_used = False
        # collision on spawn => game over
        if self.collide(self.current):
            self.game_over = True

    # --- mechanics ---
    def collide(self, piece: Piece) -> bool:
        m = piece.matrix
        for y, row in enumerate(m):
            for x, v in enumerate(row):
                if not v:
                    continue
                ny = piece.y + y
                nx = piece.x + x
                if ny < 0:
                    continue
                if nx < 0 or nx >= COLS or ny >= ROWS:
                    return True
                if self.board[ny][nx] is not None:
                    return True
        return False

    def merge(self, piece: Piece):
        for y, row in enumerate(piece.matrix):
            for x, v in enumerate(row):
                if v:
                    ny = piece.y + y
                    nx = piece.x + x
                    if 0 <= ny < ROWS and 0 <= nx < COLS:
                        self.board[ny][nx] = piece.color

    def clear_lines(self):
        cleared = 0
        y = ROWS - 1
        while y >= 0:
            if all(self.board[y][x] is not None for x in range(COLS)):
                del self.board[y]
                self.board.insert(0, [None for _ in range(COLS)])
                cleared += 1
            else:
                y -= 1
        if cleared:
            self.score += (SCORES.get(cleared, 1000)) * self.level
            self.lines += cleared
            self.level = 1 + self.lines // 10
            self.update_speed()

    def update_speed(self):
        # Faster per level, clamp to 80ms
        self.drop_ms = max(80, 900 - (self.level - 1) * 70)

    def hard_drop_y(self, piece: Piece) -> int:
        test = piece.clone()
        while not self.collide(test):
            test.y += 1
        return test.y - 1

    def step_gravity(self, dt_ms: int):
        if self.game_over or self.paused:
            return
        self.gravity_timer += dt_ms
        if self.gravity_timer >= self.drop_ms:
            self.gravity_timer = 0
            self.current.y += 1
            if self.collide(self.current):
                self.current.y -= 1
                self.merge(self.current)
                self.clear_lines()
                self.spawn_new()

    # --- actions ---
    def move(self, dx: int):
        if self.game_over or self.paused:
            return
        self.current.x += dx
        if self.collide(self.current):
            self.current.x -= dx

    def soft_drop(self):
        if self.game_over or self.paused:
            return
        self.current.y += 1
        if self.collide(self.current):
            self.current.y -= 1
        else:
            self.score += 1

    def hard_drop(self):
        if self.game_over or self.paused:
            return
        self.current.y = self.hard_drop_y(self.current)
        self.merge(self.current)
        self.clear_lines()
        self.spawn_new()
        self.score += 2  # small reward per hard drop use

    def rotate(self, ccw=False):
        if self.game_over or self.paused:
            return
        prev = [row[:] for row in self.current.matrix]
        self.current.matrix = rotate_matrix(self.current.matrix)
        if ccw:
            # rotate three times to simulate CCW
            self.current.matrix = rotate_matrix(self.current.matrix)
            self.current.matrix = rotate_matrix(self.current.matrix)
        # wall kicks (simple offsets)
        for off in [0, 1, -1, 2, -2]:
            self.current.x += off
            if not self.collide(self.current):
                return
            self.current.x -= off
        # revert
        self.current.matrix = prev

    def swap_hold(self):
        if self.game_over or self.paused or self.hold_used:
            return
        if self.hold is None:
            self.hold = Piece(self.current.kind)
            self.spawn_new()
        else:
            self.current, self.hold = self.hold, self.current
            # reset current position
            self.current.x = COLS // 2 - len(self.current.matrix[0]) // 2
            self.current.y = -1
            if self.collide(self.current):
                self.game_over = True
        self.hold_used = True

    def restart(self):
        self.__init__()


# --------------------------- Drawing ---------------------------
class Renderer:
    def __init__(self, screen: pg.Surface, game: Game, font: pg.font.Font):
        self.screen = screen
        self.game = game
        self.font = font
        self.small = pg.font.Font(None, 22)

    def draw(self):
        self.screen.fill(BG)
        ox, oy = MARGIN, MARGIN
        # board bg
        pg.draw.rect(self.screen, (13, 16, 25), (ox - 4, oy - 4, COLS * CELL + 8, ROWS * CELL + 8), border_radius=12)
        # grid
        for y in range(ROWS):
            for x in range(COLS):
                rect = (ox + x * CELL, oy + y * CELL, CELL - 1, CELL - 1)
                pg.draw.rect(self.screen, GRID, rect)
                color = self.game.board[y][x]
                if color is not None:
                    self.draw_cell(rect, color)
        # current
        if not self.game.game_over:
            self.draw_piece(self.game.current, ghost=True)
        # sidebar
        sx = ox + COLS * CELL + MARGIN
        self.draw_sidebar(sx, oy)
        # overlays
        if self.game.game_over:
            self.center_label("GAME OVER — Press R", (240, 80, 80))
        elif self.game.paused:
            self.center_label("PAUSED — Press P", (200, 200, 200))

    def draw_cell(self, rect, color):
        x, y, w, h = rect
        r = pg.Rect(x, y, w, h)
        pg.draw.rect(self.screen, color, r, border_radius=4)
        pg.draw.rect(self.screen, OUTLINE, r, 1, border_radius=4)

    def draw_piece(self, piece: Piece, ghost=False):
        m = piece.matrix
        # ghost
        if ghost:
            ghost_y = self.game.hard_drop_y(piece)
            for y, row in enumerate(m):
                for x, v in enumerate(row):
                    if v:
                        gx = MARGIN + (piece.x + x) * CELL
                        gy = MARGIN + (ghost_y + y) * CELL
                        pg.draw.rect(self.screen, (255, 255, 255), (gx, gy, CELL - 1, CELL - 1), 1, border_radius=4)
        # current
        for y, row in enumerate(m):
            for x, v in enumerate(row):
                if v:
                    rx = MARGIN + (piece.x + x) * CELL
                    ry = MARGIN + (piece.y + y) * CELL
                    if ry >= MARGIN:
                        self.draw_cell((rx, ry, CELL - 1, CELL - 1), piece.color)

    def draw_sidebar(self, sx, sy):
        # panel
        panel = pg.Rect(sx - 4, sy - 4, SIDEBAR + 8, ROWS * CELL + 8)
        pg.draw.rect(self.screen, (18, 21, 33), panel, border_radius=12)

        def label(text, y, color=TEXT, size=None):
            f = self.font if size is None else pg.font.Font(None, size)
            surf = f.render(text, True, color)
            self.screen.blit(surf, (sx + 8, y))

        label("TETRIS", sy + 6)
        label(f"Score", sy + 40, MUTED)
        label(f"{self.game.score}", sy + 64)
        label("Level", sy + 96, MUTED)
        label(f"{self.game.level}", sy + 120)
        label("Lines", sy + 152, MUTED)
        label(f"{self.game.lines}", sy + 176)

        # Next
        label("Next", sy + 210, MUTED)
        self.draw_mini_matrix(self.peek_next_matrix(), sx + 10, sy + 236)

        # Hold
        label("Hold (C)", sy + 360, MUTED)
        self.draw_mini_matrix(self.hold_matrix(), sx + 10, sy + 386)

        # Help
        help_y = sy + 510
        label("←/→ move  ↓ drop", help_y, MUTED, 20)
        label("↑/X rotate  Z ccw", help_y + 20, MUTED, 20)
        label("Space hard drop", help_y + 40, MUTED, 20)
        label("P pause  R restart", help_y + 60, MUTED, 20)

    def peek_next_matrix(self):
        if not self.game.next_queue:
            return [[0]]
        kind = self.game.next_queue[0]
        return trim_matrix([row[:] for row in SHAPES[kind]])

    def hold_matrix(self):
        if self.game.hold is None:
            return [[0]]
        return trim_matrix([row[:] for row in SHAPES[self.game.hold.kind]])

    def draw_mini_matrix(self, m, x, y):
        # fit in 4x4 grid
        s = 18
        color = None
        # find color
        for k, v in SHAPES.items():
            if trim_matrix([row[:] for row in v]) == m:
                color = COLORS[k]
                break
        for yy, row in enumerate(m):
            for xx, v in enumerate(row):
                rx = x + xx * (s + 2)
                ry = y + yy * (s + 2)
                if v:
                    pg.draw.rect(self.screen, color or (200, 200, 200), (rx, ry, s, s), border_radius=4)
                    pg.draw.rect(self.screen, OUTLINE, (rx, ry, s, s), 1, border_radius=4)
                else:
                    pg.draw.rect(self.screen, (22, 26, 40), (rx, ry, s, s), 1, border_radius=4)

    def center_label(self, text, color):
        surf = self.font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(surf, rect)


# --------------------------- Main loop ---------------------------

def main():
    pg.init()
    pg.display.set_caption("Tetris – Python/Pygame")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()

    font = pg.font.Font(None, 32)

    game = Game()
    renderer = Renderer(screen, game, font)

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key in (pg.K_ESCAPE, pg.K_q):
                    running = False
                elif event.key == pg.K_LEFT:
                    game.move(-1)
                elif event.key == pg.K_RIGHT:
                    game.move(1)
                elif event.key == pg.K_DOWN:
                    game.soft_drop()
                elif event.key in (pg.K_UP, pg.K_x):
                    game.rotate(ccw=False)
                elif event.key == pg.K_z:
                    game.rotate(ccw=True)
                elif event.key == pg.K_SPACE:
                    game.hard_drop()
                elif event.key == pg.K_c:
                    game.swap_hold()
                elif event.key == pg.K_p:
                    if not game.game_over:
                        game.paused = not game.paused
                elif event.key == pg.K_r:
                    game.restart()

        game.step_gravity(dt)
        renderer.draw()
        pg.display.flip()

    pg.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
