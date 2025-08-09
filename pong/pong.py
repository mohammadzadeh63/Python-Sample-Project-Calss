import math
import random
import sys
import pygame

# -------------------- Config --------------------
WIDTH, HEIGHT = 900, 600
FPS = 60
WIN_SCORE = 10

PADDLE_W, PADDLE_H = 12, 100
BALL_SIZE = 14

PLAYER_SPEED = 420
AI_BASE_SPEED = 360
AI_REACTION = 0.20   # 0..1 (واکنش کندتر = آسان‌تر)

BALL_SPEED = 480
BALL_SPEED_GROWTH = 1.02  # افزایش سرعت بعد از هر برخورد با پدال
MAX_BOUNCE_DEG = 50       # بیشینه زاویه انحراف (درجه)

FONT_NAME = "freesansbold.ttf"
BG_COLOR = (18, 18, 20)
FG_COLOR = (235, 235, 245)
MIDLINE_COLOR = (60, 60, 70)
ACCENT = (80, 180, 255)

# -------------------- Helpers --------------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def sign(x):
    return -1 if x < 0 else 1

# -------------------- Entities --------------------
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_W, PADDLE_H)
        self.speed = PLAYER_SPEED
        self.target_y = self.rect.centery

    def move(self, dy, dt):
        self.rect.y += dy * self.speed * dt
        self.rect.y = clamp(self.rect.y, 0, HEIGHT - self.rect.height)

    def ai_update(self, ball, dt, difficulty=1.0):
        # AI هدف می‌گیرد به نقطه پیش‌بینی‌شده با کمی تأخیر/لرزش
        predict_y = ball.rect.centery + (ball.vy * AI_REACTION / max(1e-3, abs(ball.vx))) * WIDTH
        # کمی نویز برای طبیعی شدن
        predict_y += random.uniform(-40, 40) * (1.0 - difficulty)
        # سرعت AI متناسب با سرعت توپ
        ai_speed = (AI_BASE_SPEED + 0.25 * math.hypot(ball.vx, ball.vy)) * difficulty
        dir = 0
        if self.rect.centery < predict_y - 12:
            dir = 1
        elif self.rect.centery > predict_y + 12:
            dir = -1
        self.rect.y += dir * ai_speed * dt
        self.rect.y = clamp(self.rect.y, 0, HEIGHT - self.rect.height)

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.reset(direction=random.choice([-1, 1]))

    def reset(self, direction=1):
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        angle = math.radians(random.uniform(-18, 18))  # سرویس با زاویه کم
        speed = BALL_SPEED
        self.vx = direction * speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.serving = True   # برای شمارش معکوس
        self.serve_timer = 1.3

    def update(self, dt):
        if self.serving:
            self.serve_timer -= dt
            if self.serve_timer <= 0:
                self.serving = False
            return
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)

        # دیوار بالا/پایین
        if self.rect.top <= 0:
            self.rect.top = 0
            self.vy = -self.vy
        elif self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.vy = -self.vy

    def collide_paddle(self, paddle):
        if not self.rect.colliderect(paddle.rect):
            return False

        # برگرداندن توپ و محاسبه زاویه بسته به نقطه برخورد
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        # فاصله نسبی برخورد (0 بالای پدال، 1 پایین)
        rel = (self.rect.centery - paddle.rect.top) / paddle.rect.height
        rel = clamp(rel, 0.0, 1.0)
        # نگاشت به زاویه [-MAX_BOUNCE_DEG, +MAX_BOUNCE_DEG]
        theta = math.radians((rel - 0.5) * 2 * MAX_BOUNCE_DEG)

        speed = math.hypot(self.vx, self.vy) * BALL_SPEED_GROWTH
        direction = 1 if self.vx > 0 else -1
        # معکوس جهت افقی
        direction *= -1

        self.vx = direction * speed * math.cos(theta)
        # جهت عمودی از زاویه
        self.vy = speed * math.sin(theta)

        # جلوگیری از گیر کردن داخل پدال
        if direction > 0:
            self.rect.left = paddle.rect.right
        else:
            self.rect.right = paddle.rect.left
        return True

# -------------------- Game --------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pong - 1P vs CPU")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.Font(FONT_NAME, 64)
        self.font_med = pygame.font.Font(FONT_NAME, 28)
        self.font_small = pygame.font.Font(FONT_NAME, 20)

        # Entities
        margin = 30
        self.player = Paddle(margin, HEIGHT//2 - PADDLE_H//2)
        self.cpu = Paddle(WIDTH - margin - PADDLE_W, HEIGHT//2 - PADDLE_H//2)
        self.ball = Ball()

        self.player_score = 0
        self.cpu_score = 0
        self.paused = False
        # دشواری (0.6 آسان، 1.0 عادی، 1.2 سخت)
        self.difficulty = 1.0

    def draw_center_line(self):
        for y in range(0, HEIGHT, 18):
            pygame.draw.rect(self.screen, MIDLINE_COLOR, (WIDTH//2 - 2, y, 4, 10))

    def draw_score(self):
        ps = self.font_big.render(str(self.player_score), True, FG_COLOR)
        cs = self.font_big.render(str(self.cpu_score), True, FG_COLOR)
        self.screen.blit(ps, (WIDTH*0.25 - ps.get_width()//2, 30))
        self.screen.blit(cs, (WIDTH*0.75 - cs.get_width()//2, 30))

    def handle_input(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.player.move(-1, dt)
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.player.move(+1, dt)

    def check_score(self):
        if self.ball.rect.left <= 0:
            self.cpu_score += 1
            self.ball.reset(direction=-1)
        elif self.ball.rect.right >= WIDTH:
            self.player_score += 1
            self.ball.reset(direction=+1)

    def maybe_show_win(self):
        if self.player_score >= WIN_SCORE or self.cpu_score >= WIN_SCORE:
            winner = "You Win! 🏆" if self.player_score > self.cpu_score else "CPU Wins!"
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            txt = self.font_big.render(winner, True, ACCENT)
            sub = self.font_med.render("Press R to Restart — Esc to Quit", True, FG_COLOR)
            self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 60))
            self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 10))
            pygame.display.flip()

            # انتظار تا ریست یا خروج
            waiting = True
            while waiting:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                        if e.key == pygame.K_r:
                            self.reset_match()
                            waiting = False
                self.clock.tick(30)
            return True
        return False

    def reset_match(self):
        self.player_score = 0
        self.cpu_score = 0
        self.player.rect.centery = HEIGHT//2
        self.cpu.rect.centery = HEIGHT//2
        self.ball.reset(direction=random.choice([-1, 1]))

    def draw_hud(self):
        # راهنما
        hud = self.font_small.render("W/S or ↑/↓ to move  |  P: Pause  |  R: Reset round  |  Esc: Quit", True, (180, 180, 190))
        self.screen.blit(hud, (WIDTH//2 - hud.get_width()//2, HEIGHT - 28))

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    if event.key == pygame.K_r and not self.ball.serving:
                        # ریست فقط توپ/راند
                        self.ball.reset(direction=sign(self.ball.vx))

            if not self.paused:
                # ورودی بازیکن
                self.handle_input(dt)
                # AI
                self.cpu.ai_update(self.ball, dt, difficulty=self.difficulty)

                # به‌روزرسانی توپ و برخورد
                self.ball.update(dt)
                if not self.ball.serving:
                    # برخورد با پدال‌ها
                    if self.ball.vx < 0:
                        self.ball.collide_paddle(self.player)
                    else:
                        self.ball.collide_paddle(self.cpu)

                # امتیاز
                self.check_score()

            # رسم
            self.screen.fill(BG_COLOR)
            self.draw_center_line()
            pygame.draw.rect(self.screen, FG_COLOR, self.player.rect, border_radius=6)
            pygame.draw.rect(self.screen, FG_COLOR, self.cpu.rect, border_radius=6)
            pygame.draw.rect(self.screen, ACCENT if self.ball.serving else FG_COLOR, self.ball.rect, border_radius=7)
            self.draw_score()
            self.draw_hud()

            # نمایش Pause
            if self.paused:
                t = self.font_med.render("PAUSED", True, ACCENT)
                self.screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - t.get_height()//2))

            # شمارش معکوس سرویس
            if self.ball.serving:
                n = math.ceil(self.ball.serve_timer)
                if n > 0:
                    c = self.font_big.render(str(n), True, ACCENT)
                    self.screen.blit(c, (WIDTH//2 - c.get_width()//2, HEIGHT//2 - c.get_height()//2))

            pygame.display.flip()

            # برنده؟
            if self.maybe_show_win():
                continue

# -------------------- Main --------------------
if __name__ == "__main__":
    Game().run()
