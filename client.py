import pygame
from pygame import mixer
import socket
import json
from threading import Thread

# ---PYGAME НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Пінг-Понг")

# ---ГЛОБАЛЬНІ ЗМІННІ ---
buffer = ""
game_state = {}
game_over = False
winner = None
you_winner = None
client = None

# ---СЕРВЕР ---
def connect_to_server():
    global client
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080)) # ---- Підключення до сервера
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass


def receive():
    global buffer, game_state, game_over, client
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# --- ШРИФТИ ---
font_win = pygame.font.Font(None, 72)
font_main = pygame.font.Font(None, 36)

# --- ЗОБРАЖЕННЯ ----
try:
    background = pygame.image.load("assets/background.png")
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
except:
    background = None

try:
    platform_img = pygame.image.load("assets/platform.png")
    platform_img = pygame.transform.scale(platform_img, (20, 100))
except:
    platform_img = None

mixer.init()


try:
    wall_hit_sound = mixer.Sound("assets/wall_hit.ogg")
except:
    wall_hit_sound = None


# --- ГРА ---
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exit()

    if "countdown" in game_state and game_state["countdown"] > 0:
        # Малюємо фон
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill((0, 0, 0))
        
        countdown_text = font_win.render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        pygame.display.update()
        continue  # Не малюємо гру до завершення відліку

    if "winner" in game_state and game_state["winner"] is not None:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill((20, 20, 20))

        if you_winner is None:  # Встановлюємо тільки один раз
            if game_state["winner"] == my_id:
                you_winner = True
            else:
                you_winner = False

        if you_winner:
            text = "Ти переміг!"
        else:
            text = "Пощастить наступним разом!"

        win_text = font_win.render(text, True, (255, 215, 0))
        text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(win_text, text_rect)

        text = font_win.render('К - рестарт', True, (255, 215, 0))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
        screen.blit(text, text_rect)

        pygame.display.update()
        continue  # Блокує гру після перемоги

    if game_state:
        # Малюємо фон
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill((30, 30, 30))
        
        # Отримуємо позиції платформ
        paddle_left_y = int(game_state['paddles'].get('0', 250))
        paddle_right_y = int(game_state['paddles'].get('1', 250))
        
        # Малюємо платформи (зі зображенням або прямокутниками)
        if platform_img:
            screen.blit(platform_img, (20, paddle_left_y))
            screen.blit(platform_img, (WIDTH - 40, paddle_right_y))
        else:
            pygame.draw.rect(screen, (0, 255, 0), (20, paddle_left_y, 20, 100))
            pygame.draw.rect(screen, (255, 0, 255), (WIDTH - 40, paddle_right_y, 20, 100))
        
        # Малюємо м'яч
        pygame.draw.circle(screen, (255, 255, 255), (int(game_state['ball']['x']), int(game_state['ball']['y'])), 10)
        
        # Відображаємо рахунок
        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - 25, 20))

        if game_state.get('sound_event'):
            if game_state['sound_event'] == 'wall_hit':
                if wall_hit_sound:
                    wall_hit_sound.play()
            if game_state['sound_event'] == 'platform_hit':
                pass  # Додай звук при необхідності

    else:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill((0, 0, 0))
        
        waiting_text = font_main.render(f"Очікування гравців...", True, (255, 255, 255))
        screen.blit(waiting_text, (WIDTH // 2 - 150, 20))

    pygame.display.update()
    clock.tick(60)

    # Управління платформою
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        if client:
            client.send(b"UP")
    elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
        if client:
            client.send(b"DOWN")
