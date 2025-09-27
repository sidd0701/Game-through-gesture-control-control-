import pygame
import cv2
import numpy as np
import mediapipe as mp
import math
import sys
import time


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)


GET_PLAYER_COUNT = 0
GET_PLAYER_NAMES = 1
TURN_TRANSITION = 2
GAME_PLAYING = 3
GAME_OVER = 4
pygame.init()
infoObject = pygame.display.Info()
FULL_SCREEN_WIDTH = infoObject.current_w
FULL_SCREEN_HEIGHT = infoObject.current_h
screen = pygame.display.set_mode((FULL_SCREEN_WIDTH, FULL_SCREEN_HEIGHT), pygame.NOFRAME)

pygame.display.set_caption("Multi-Player Spaceship Gesture Control")
clock = pygame.time.Clock()
FPS = 60
FONT = pygame.font.Font(None, 36)
BIG_FONT = pygame.font.Font(None, 72)


class Player(pygame.sprite.Sprite):
    """
    Represents the player's spaceship.
    Controls movement, shooting, and power-ups.
    """
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT - 50))
        
        self.velocity_x = 0
        self.acceleration = 0.5
        self.deceleration = 0.95
        self.max_speed = 8

        self.fire_rate = 300
        self.last_shot_time = pygame.time.get_ticks()

        self.is_power_up_active = False
        self.power_up_start_time = 0
        self.power_up_duration = 5000
        self.is_accelerating = False
    
    def update(self, target_x_position=None):
        self.is_accelerating = False
        if target_x_position is not None:
  
            if target_x_position < self.rect.centerx - 20:
                self.velocity_x -= self.acceleration
                self.is_accelerating = True
            elif target_x_position > self.rect.centerx + 20:
                self.velocity_x += self.acceleration
                self.is_accelerating = True
            else:
                self.velocity_x *= self.deceleration
        else:
            self.velocity_x *= self.deceleration

        self.velocity_x = max(-self.max_speed, min(self.velocity_x, self.max_speed))
        
        self.rect.x += self.velocity_x
        
        if self.rect.left < 0:
            self.rect.left = 0
            self.velocity_x = 0
        if self.rect.right > FULL_SCREEN_WIDTH:
            self.rect.right = FULL_SCREEN_WIDTH
            self.velocity_x = 0

        if self.is_power_up_active and pygame.time.get_ticks() - self.power_up_start_time > self.power_up_duration:
            self.is_power_up_active = False
            self.fire_rate = 300

    def shoot(self):
        current_time = pygame.time.get_ticks()
        effective_fire_rate = self.fire_rate / (2 if self.is_power_up_active else 1)
        if current_time - self.last_shot_time > effective_fire_rate:
            projectile = Projectile(self.rect.centerx, self.rect.top)
            all_sprites.add(projectile)
            projectiles_group.add(projectile)
            self.last_shot_time = current_time

    def activate_power_up(self):
        if not self.is_power_up_active:
            self.is_power_up_active = True
            self.power_up_start_time = pygame.time.get_ticks()

    def draw(self, screen):
        color = YELLOW if self.is_power_up_active else BLUE
        
        points = [
            (self.rect.centerx, self.rect.top),
            (self.rect.left, self.rect.bottom),
            (self.rect.centerx, self.rect.bottom - 10),
            (self.rect.right, self.rect.bottom)
        ]
        
        pygame.draw.polygon(screen, color, points)
        
        if self.is_accelerating:
            thruster_points = [
                (self.rect.centerx, self.rect.bottom - 5),
                (self.rect.centerx - 10, self.rect.bottom + 10),
                (self.rect.centerx + 10, self.rect.bottom + 10)
            ]
            pygame.draw.polygon(screen, RED, thruster_points)

class Projectile(pygame.sprite.Sprite):
    """
    A projectile fired by the player.
    """
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 15), pygame.SRCALPHA)
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -10

    def update(self, *args, **kwargs):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    """
    A simple enemy that moves downwards.
    """
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(np.random.randint(50, FULL_SCREEN_WIDTH - 50), 0))
        self.speed = np.random.randint(1, 4)

    def update(self, *args, **kwargs):
        self.rect.y += self.speed
        if self.rect.top > FULL_SCREEN_HEIGHT:
            self.kill()

class WhiteCircle(pygame.sprite.Sprite):
    """
    A score-reducing object that moves downwards.
    """
    def __init__(self):
        super().__init__()
        self.radius = 20
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=(np.random.randint(50, FULL_SCREEN_WIDTH - 50), 0))
        self.speed = np.random.randint(2, 5)

    def update(self, *args, **kwargs):
        self.rect.y += self.speed
        if self.rect.top > FULL_SCREEN_HEIGHT:
            self.kill()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = None
for i in range(3):
    try:
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            break
    except:
        continue

if not cap or not cap.isOpened():
    print("FATAL ERROR: Could not open any webcam. Please ensure your camera is connected and not in use by another application.")
    pygame.quit()
    cv2.destroyAllWindows()
    exit()

def get_hand_landmarks(image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            return hand_landmarks
    return None

def get_landmark_coords(hand_landmarks, landmark_id, frame_width, frame_height):
    if hand_landmarks:
        lm = hand_landmarks.landmark[landmark_id]
        x = int(lm.x * frame_width)
        y = int(lm.y * frame_height)
        return (x, y)
    return None

def is_fist(hand_landmarks):
    if hand_landmarks:
        if (hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y and
            hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y and
            hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP].y and
            hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y > hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP].y):
            return True
    return False

THUMB_INDEX_PROXIMITY_THRESHOLD = 0.08
_thumb_tapped_in_prev_frame = False

def is_thumb_tapping(hand_landmarks):
    global _thumb_tapped_in_prev_frame
    if hand_landmarks:
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        distance = math.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        
        is_currently_close = distance < THUMB_INDEX_PROXIMITY_THRESHOLD
        
        if is_currently_close and not _thumb_tapped_in_prev_frame:
            _thumb_tapped_in_prev_frame = True
            return True
        elif not is_currently_close:
            _thumb_tapped_in_prev_frame = False
    return False


all_sprites = pygame.sprite.Group()
players_group = pygame.sprite.Group()
projectiles_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
white_circles_group = pygame.sprite.Group()

player = Player()

game_state = GET_PLAYER_COUNT
num_players = 0
players_data = [] 
current_player_index = 0
input_text = ""

game_timer_start = 0
game_timer_duration = 30
last_enemy_spawn_time = pygame.time.get_ticks()
enemy_spawn_delay = 1000
last_white_circle_spawn_time = pygame.time.get_ticks()
white_circle_spawn_delay = 2000


def start_new_turn():
    """Resets the game state for the next player's turn."""
    global game_state, game_timer_start, last_enemy_spawn_time, last_white_circle_spawn_time

    for sprite in all_sprites:
        sprite.kill()
    

    player.__init__()
    all_sprites.add(player)
    players_group.add(player)

  
    game_state = GAME_PLAYING
    game_timer_start = pygame.time.get_ticks()
    last_enemy_spawn_time = pygame.time.get_ticks()
    last_white_circle_spawn_time = pygame.time.get_ticks()

def find_winner():
    """Finds the player with the highest score."""
    if not players_data:
        return None
    
    winner = max(players_data, key=lambda p: p['score'])
    return winner

def get_final_scores_string():
    """Generates a formatted string of all players' final scores."""
    score_list = ""
    sorted_players = sorted(players_data, key=lambda p: p['score'], reverse=True)
    for i, p in enumerate(sorted_players):
        score_list += f"{i+1}. {p['name']}: {p['score']}\n"
    return score_list


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            running = False

        if game_state == GET_PLAYER_COUNT:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_2, pygame.K_3, pygame.K_4]:
                    num_players = int(event.unicode)
                    players_data = [{'name': '', 'score': 0} for _ in range(num_players)]
                    current_player_index = 0
                    game_state = GET_PLAYER_NAMES

        elif game_state == GET_PLAYER_NAMES:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if len(input_text) > 0:
                        players_data[current_player_index]['name'] = input_text
                        current_player_index += 1
                        input_text = ""
                        if current_player_index >= num_players:
                            current_player_index = 0
                            game_state = TURN_TRANSITION
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
        
        elif game_state == TURN_TRANSITION:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                start_new_turn()

        elif game_state == GAME_OVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
          
                game_state = GET_PLAYER_COUNT
                num_players = 0
                players_data = []
                current_player_index = 0
                input_text = ""
        
                all_sprites.empty()
                players_group.empty()
                projectiles_group.empty()
                enemies_group.empty()
                white_circles_group.empty()

 
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame. Reconnecting...")
        cap.release()
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"Successfully reconnected with index {i}.")
                break
        if not cap or not cap.isOpened():
            print("Fatal error: Could not re-establish webcam connection. Exiting.")
            running = False
            break
        continue

    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape
    hand_landmarks = get_hand_landmarks(frame)
    player_target_x = None
    gesture_text = ""

    if hand_landmarks and game_state == GAME_PLAYING:
        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        wrist_coords = get_landmark_coords(hand_landmarks, mp_hands.HandLandmark.WRIST, frame_width, frame_height)
        if wrist_coords:
            player_target_x = wrist_coords[0]

        if is_thumb_tapping(hand_landmarks):
            player.shoot()
            gesture_text = "FIRE!"
        
        if is_fist(hand_landmarks):
            player.activate_power_up()
            gesture_text = "POWER-UP!"
    
    if gesture_text:
        cv2.putText(frame, gesture_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)


    screen.fill(BLACK)
    
    if game_state == GET_PLAYER_COUNT:
        text_surface = BIG_FONT.render("Select Number of Players", True, WHITE)
        text_rect = text_surface.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 - 100))
        screen.blit(text_surface, text_rect)

        options_surface = FONT.render("Press '2', '3', or '4'", True, WHITE)
        options_rect = options_surface.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2))
        screen.blit(options_surface, options_rect)

    elif game_state == GET_PLAYER_NAMES:
        prompt_text = f"Player {current_player_index + 1}, enter your name:"
        prompt_surface = FONT.render(prompt_text, True, WHITE)
        prompt_rect = prompt_surface.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 - 100))
        screen.blit(prompt_surface, prompt_rect)
        
        input_box = pygame.Rect(FULL_SCREEN_WIDTH // 2 - 200, FULL_SCREEN_HEIGHT // 2, 400, 50)
        pygame.draw.rect(screen, WHITE, input_box, 2)
        
        input_surface = FONT.render(input_text, True, WHITE)
        screen.blit(input_surface, (input_box.x + 5, input_box.y + 5))
        input_box.w = max(400, input_surface.get_width() + 10)
        
        cursor_pos = (input_box.x + 5 + input_surface.get_width(), input_box.y + 5)
        if time.time() % 1 > 0.5:
            pygame.draw.line(screen, WHITE, cursor_pos, (cursor_pos[0], cursor_pos[1] + FONT.get_height()), 2)
    
    elif game_state == TURN_TRANSITION:
 
        is_first_turn = all(p['score'] == 0 for p in players_data)
        
        if is_first_turn and current_player_index == 0:
            turn_text = "Get Ready!"
        else:
            turn_text = f"Turn over for {players_data[(current_player_index - 1 + num_players) % num_players]['name']}!"
        
        turn_surface = BIG_FONT.render(turn_text, True, WHITE)
        turn_rect = turn_surface.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 - 50))
        screen.blit(turn_surface, turn_rect)

        score_text = FONT.render(f"Current Score: {players_data[(current_player_index - 1 + num_players) % num_players]['score']}", True, WHITE)
        score_rect = score_text.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 + 20))
        screen.blit(score_text, score_rect)
        
        next_player_text = f"It's {players_data[current_player_index]['name']}'s turn."
        next_player_surface = FONT.render(next_player_text, True, YELLOW)
        next_player_rect = next_player_surface.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 + 80))
        screen.blit(next_player_surface, next_player_rect)

        press_enter_text = "Press ENTER to begin."
        press_enter_surface = FONT.render(press_enter_text, True, LIGHT_GRAY)
        press_enter_rect = press_enter_surface.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 + 150))
        screen.blit(press_enter_surface, press_enter_rect)

    elif game_state == GAME_PLAYING:
  
        player.update(player_target_x) 
        projectiles_group.update() 
        enemies_group.update()
        white_circles_group.update()

        current_time = pygame.time.get_ticks()
        
        if current_time - last_enemy_spawn_time > enemy_spawn_delay:
            if np.random.rand() > 0.5:
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies_group.add(enemy)
            last_enemy_spawn_time = current_time
        
        if current_time - last_white_circle_spawn_time > white_circle_spawn_delay:
            if np.random.rand() > 0.7:
                white_circle = WhiteCircle()
                all_sprites.add(white_circle)
                white_circles_group.add(white_circle)
            last_white_circle_spawn_time = current_time

        elapsed_time = (current_time - game_timer_start) // 1000
        if elapsed_time > 15:
            enemy_spawn_delay = 500
            white_circle_spawn_delay = 1000
            
        hits = pygame.sprite.groupcollide(projectiles_group, enemies_group, True, True)
        for _ in hits:
            players_data[current_player_index]['score'] += 10

        player_hits = pygame.sprite.spritecollide(player, enemies_group, True)
        if player_hits:
            current_player_index += 1
            if current_player_index >= num_players:
                game_state = GAME_OVER
            else:
                game_state = TURN_TRANSITION

        white_circle_hits = pygame.sprite.spritecollide(player, white_circles_group, True)
        if white_circle_hits:
            players_data[current_player_index]['score'] -= 10
            if players_data[current_player_index]['score'] < 0:
                players_data[current_player_index]['score'] = 0

        remaining_time = game_timer_duration - elapsed_time
        if remaining_time <= 0:
            remaining_time = 0
            current_player_index += 1
            if current_player_index >= num_players:
                game_state = GAME_OVER
            else:
                game_state = TURN_TRANSITION
        screen.fill(BLACK)
        player.draw(screen)
        projectiles_group.draw(screen)
        enemies_group.draw(screen)
        white_circles_group.draw(screen)
        if current_player_index < num_players:
            score_text_surface = FONT.render(f"Score: {players_data[current_player_index]['score']}", True, WHITE)
            screen.blit(score_text_surface, (10, 10))
            turn_text_surface = FONT.render(f"Player: {players_data[current_player_index]['name']}", True, WHITE)
            screen.blit(turn_text_surface, (10, 50))
            timer_surface = FONT.render(f"Time: {remaining_time}s", True, WHITE)
            screen.blit(timer_surface, (10, 90))
    elif game_state == GAME_OVER:
        screen.fill(BLACK)
        game_over_text = BIG_FONT.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 - 200))
        screen.blit(game_over_text, game_over_rect)
        scoreboard_text = "Final Scores:"
        scoreboard_surface = FONT.render(scoreboard_text, True, WHITE)
        scoreboard_rect = scoreboard_surface.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 - 120))
        screen.blit(scoreboard_surface, scoreboard_rect)
        scores_string = get_final_scores_string()
        scores_lines = scores_string.split('\n')
        for i, line in enumerate(scores_lines):
            score_line_surface = FONT.render(line, True, WHITE)
            score_line_rect = score_line_surface.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 - 80 + i * 40))
            screen.blit(score_line_surface, score_line_rect)
        winner_data = find_winner()
        if winner_data:
            winner_text = f"The winner is {winner_data['name']} with {winner_data['score']} points!"
            winner_surface = FONT.render(winner_text, True, YELLOW)
            winner_rect = winner_surface.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 + 100))
            screen.blit(winner_surface, winner_rect)
        restart_text = FONT.render("Press ENTER to play again.", True, LIGHT_GRAY)
        restart_rect = restart_text.get_rect(center=(FULL_SCREEN_WIDTH // 2, FULL_SCREEN_HEIGHT // 2 + 180))
        screen.blit(restart_text, restart_rect)
    cv_display_width = 240
    cv_display_height = 180
    cv_feed = pygame.transform.scale(pygame.surfarray.make_surface(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).swapaxes(0, 1)), (cv_display_width, cv_display_height))
    screen.blit(cv_feed, (FULL_SCREEN_WIDTH - cv_display_width - 10, 10))
    pygame.display.flip()
    clock.tick(FPS)
cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()
