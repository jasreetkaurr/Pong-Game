# pong.py
import sys
import random
import pygame

# ---------------------------
# Config
# ---------------------------
WIDTH, HEIGHT = 900, 600
MARGIN = 20
PADDLE_W, PADDLE_H = 14, 110
BALL_SIZE = 14
PADDLE_SPEED = 7
BALL_SPEED = 6
WIN_SCORE = 11
FPS = 60

BG_COLOR = (16, 18, 23)
FG_COLOR = (235, 235, 235)
MIDLINE_COLOR = (80, 84, 94)
ACCENT = (120, 190, 255)

# ---------------------------
# Objects
# ---------------------------
class Paddle(pygame.Rect):
    def __init__(self, x, y):
        super().__init__(x, y, PADDLE_W, PADDLE_H)
        self.vel = 0

    def update(self, bounds: pygame.Rect):
        self.y += self.vel
        if self.top < bounds.top:
            self.top = bounds.top
        if self.bottom > bounds.bottom:
            self.bottom = bounds.bottom

class Ball(pygame.Rect):
    def __init__(self, x, y):
        super().__init__(x, y, BALL_SIZE, BALL_SIZE)
        self.reset(center=(x, y))

    def reset(self, center):
        self.center = center
        # Randomize initial direction but ensure non-zero vertical component
        dir_x = random.choice([-1, 1])
        dir_y = random.uniform(-0.8, 0.8)
        speed = BALL_SPEED
        mag = (dir_x**2 + dir_y**2) ** 0.5
        self.vx = speed * (dir_x / mag)
        self.vy = speed * (dir_y / mag)

    def update(self):
        self.x += self.vx
        self.y += self.vy

# ---------------------------
# Helpers
# ---------------------------
def draw_center_line(surf):
    dash_h = 14
    gap = 10
    y = 0
    while y < HEIGHT:
        pygame.draw.rect(surf, MIDLINE_COLOR, (WIDTH//2 - 2, y, 4, dash_h))
        y += dash_h + gap

def draw_score(surf, font, score_l, score_r):
    left_text = font.render(str(score_l), True, FG_COLOR)
    right_text = font.render(str(score_r), True, FG_COLOR)
    surf.blit(left_text, (WIDTH//2 - 60 - left_text.get_width(), 20))
    surf.blit(right_text, (WIDTH//2 + 60, 20))

def ball_paddle_collision(ball: Ball, paddle: Paddle, ping_sound=None):
    if ball.colliderect(paddle):
        # Move ball out of the paddle to avoid tunneling
        if ball.vx < 0:
            ball.left = paddle.right
        else:
            ball.right = paddle.left
        # Reflect X and add "spin" based on where it hit the paddle
        offset = (ball.centery - paddle.centery) / (PADDLE_H / 2)
        ball.vx *= -1
        ball.vy = (BALL_SPEED + 0.5) * offset
        # Normalize to maintain speed budget
        speed = (ball.vx**2 + ball.vy**2) ** 0.5
        factor = BALL_SPEED / speed
        ball.vx *= factor
        ball.vy *= factor
        if ping_sound: 
            try:
                ping_sound.play()
            except Exception:
                pass

def clamp_ball_vertical(ball: Ball, bounds: pygame.Rect, wall_sound=None):
    if ball.top <= bounds.top:
        ball.top = bounds.top
        ball.vy *= -1
        if wall_sound:
            try:
                wall_sound.play()
            except Exception:
                pass
    elif ball.bottom >= bounds.bottom:
        ball.bottom = bounds.bottom
        ball.vy *= -1
        if wall_sound:
            try:
                wall_sound.play()
            except Exception:
                pass

def ai_move(paddle: Paddle, ball: Ball):
    # Simple AI: track ball with a small reaction band
    target = ball.centery
    band = 12
    if paddle.centery < target - band:
        paddle.vel = PADDLE_SPEED * 0.9
    elif paddle.centery > target + band:
        paddle.vel = -PADDLE_SPEED * 0.9
    else:
        paddle.vel = 0

# ---------------------------
# Main
# ---------------------------
def main():
    pygame.init()
    pygame.display.set_caption("Pong (Pygame)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Surfaces & fonts
    play_area = pygame.Rect(MARGIN, MARGIN, WIDTH - 2*MARGIN, HEIGHT - 2*MARGIN)
    score_font = pygame.font.SysFont("Arial", 56, bold=True)
    small_font = pygame.font.SysFont("Arial", 22)

    # Sounds (optional; safe if mixer not available)
    ping_sound = wall_sound = score_sound = None
    try:
        pygame.mixer.init()
        # Generate short beeps by loading tiny silent sounds if needed; here we use built-in tone fallback
        # For portability without assets, we’ll skip custom sound files.
    except Exception:
        pass

    # Entities
    left = Paddle(MARGIN + 18, HEIGHT//2 - PADDLE_H//2)
    right = Paddle(WIDTH - MARGIN - 18 - PADDLE_W, HEIGHT//2 - PADDLE_H//2)
    ball = Ball(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2)

    score_l = 0
    score_r = 0
    running = True
    paused = False
    show_help = True

    while running:
        dt = clock.tick(FPS)

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_r:
                    score_l, score_r = 0, 0
                    ball.reset((WIDTH//2, HEIGHT//2))
                if event.key == pygame.K_h:
                    show_help = not show_help

        # Human controls (Left paddle: W/S; Right paddle: Up/Down)
        keys = pygame.key.get_pressed()
        left.vel = (keys[pygame.K_s] - keys[pygame.K_w]) * PADDLE_SPEED

        # Choose whether right paddle is AI or human:
        human_right = False
        if human_right:
            right.vel = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * PADDLE_SPEED
        else:
            ai_move(right, ball)

        if not paused:
            left.update(play_area)
            right.update(play_area)

            ball.update()
            clamp_ball_vertical(ball, play_area, wall_sound)
            ball_paddle_collision(ball, left, ping_sound)
            ball_paddle_collision(ball, right, ping_sound)

            # Scoring
            if ball.left <= play_area.left - 4:
                score_r += 1
                if score_sound:
                    try:
                        score_sound.play()
                    except Exception:
                        pass
                ball.reset((WIDTH//2, HEIGHT//2))

            if ball.right >= play_area.right + 4:
                score_l += 1
                if score_sound:
                    try:
                        score_sound.play()
                    except Exception:
                        pass
                ball.reset((WIDTH//2, HEIGHT//2))

        # Draw
        screen.fill(BG_COLOR)
        draw_center_line(screen)
        pygame.draw.rect(screen, FG_COLOR, left)
        pygame.draw.rect(screen, FG_COLOR, right)
        pygame.draw.rect(screen, ACCENT, ball)

        # Border
        pygame.draw.rect(screen, MIDLINE_COLOR, play_area, 2, border_radius=8)

        draw_score(screen, score_font, score_l, score_r)

        if show_help:
            help_lines = [
                "Controls: W/S (Left), Up/Down (Right) — Space: Pause — R: Reset — H: Hide help — Esc: Quit",
                f"First to {WIN_SCORE} wins.",
            ]
            y = HEIGHT - 20 - len(help_lines)*22
            for line in help_lines:
                txt = small_font.render(line, True, (190, 195, 205))
                screen.blit(txt, (MARGIN + 8, y))
                y += 22

        # Win banner
        if score_l >= WIN_SCORE or score_r >= WIN_SCORE:
            paused = True
            winner = "Left" if score_l >= WIN_SCORE else "Right"
            banner = score_font.render(f"{winner} Wins! Press R to restart", True, ACCENT)
            screen.blit(banner, (WIDTH//2 - banner.get_width()//2, HEIGHT//2 - 40))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
