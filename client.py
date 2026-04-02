from pygame import *
import socket
import json
from threading import Thread
import os

# --- ШЛЯХ ДО РЕСУРСІВ ---
ASSETS_PATH = "assets/"

# --- PYGAME НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")

# --- СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080))
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass

def receive():
    global buffer, game_state, game_over
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
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)

# --- ЗОБРАЖЕННЯ ----
back = image.load(ASSETS_PATH + "back.png")
back = transform.scale(back, (WIDTH, HEIGHT))
platform_img = image.load(ASSETS_PATH + "platform.png")
platform_img = transform.rotate(platform_img, 90)
platform_img = transform.scale(platform_img, (20, 100))

# --- ЗВУКИ ---
mixer.init()
# Використовуємо файли які реально існують!
hit_sound = mixer.Sound(ASSETS_PATH + "wall_hit.ogg")
backsound = mixer.Sound(ASSETS_PATH + "background_music.ogg")
backsound.set_volume(0.5)  # Фонова музика тихіше
backsound.play(-1)
# Якщо немає другого звуку - використовуємо той самий
hit_sound_2 = mixer.Sound(ASSETS_PATH + "wall_hit.ogg")

# --- ГРА ---
game_over = False
winner = None
you_winner = None
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()

running = True
while running:
    for e in event.get():
        if e.type == QUIT:
            running = False
        
        # Рестарт гри по клавіші K
        if e.type == KEYDOWN:
            if e.key == K_k and "winner" in game_state and game_state["winner"] is not None:
                # Перепідключення до сервера
                try:
                    client.close()
                except:
                    pass
                you_winner = None
                game_state = {}
                my_id, game_state, buffer, client = connect_to_server()
                Thread(target=receive, daemon=True).start()

    # --- COUNTDOWN ---
    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.fill((0, 0, 0))
        countdown_text = font_win.render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        display.update()
        clock.tick(60)
        continue

    # --- WINNER SCREEN ---
    if "winner" in game_state and game_state["winner"] is not None:
        screen.fill((20, 20, 20))

        if you_winner is None:
            you_winner = (game_state["winner"] == my_id)

        if you_winner:
            text = "Ти переміг!"
            color = (255, 215, 0)
        else:
            text = "Пощастить наступним разом!"
            color = (200, 100, 100)

        win_text = font_win.render(text, True, color)
        text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(win_text, text_rect)

        restart_text = font_main.render('Натисни K для рестарту', True, (150, 150, 150))
        text_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
        screen.blit(restart_text, text_rect)

        display.update()
        clock.tick(60)
        continue

    # --- GAME SCREEN ---
    if game_state and 'ball' in game_state:
        screen.blit(back, (0, 0))
        screen.blit(platform_img, (20, game_state['paddles']['0']))
        screen.blit(platform_img, (WIDTH - 40, game_state['paddles']['1']))
        draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)
        
        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - 25, 20))

        # Звуки
        if 'sound_event' in game_state and game_state['sound_event']:
            if game_state['sound_event'] == 'wall_hit':
                hit_sound.play()
            elif game_state['sound_event'] == 'platform_hit':
                hit_sound_2.play()
    else:
        screen.fill((30, 30, 30))
        waiting_text = font_main.render("Очікування гравців...", True, (255, 255, 255))
        text_rect = waiting_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(waiting_text, text_rect)

    display.update()
    clock.tick(60)

    # --- КЕРУВАННЯ ---
    keys = key.get_pressed()
    try:
        if keys[K_w]:
            client.send(b"UP")
        elif keys[K_s]:
            client.send(b"DOWN")
    except:
        pass

# --- ЗАВЕРШЕННЯ ---
backsound.stop()
client.close()
quit()
