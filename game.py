import pygame
import sys
import random
import math
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
FPS = 60

class Color:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    SKY_BLUE = (135, 206, 250)
    DARK_BLUE = (25, 25, 112)
    YELLOW = (255, 223, 0)
    ORANGE = (255, 165, 0)
    RED = (255, 69, 58)
    BRIGHT_RED = (255, 50, 50)
    DARK_RED = (180, 30, 30)
    GREEN = (52, 199, 89)
    DARK_GREEN = (34, 139, 34)
    PURPLE = (175, 82, 222)
    CYAN = (90, 200, 250)
    GOLD = (255, 215, 0)
    SILVER = (192, 192, 192)
    DARK_GRAY = (40, 40, 40)
    LIGHT_GRAY = (180, 180, 180)

class GameState(Enum):
    LANDING = 0
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    HOW_TO_PLAY = 4
    CREDITS = 5
    SETTINGS = 6

GRAVITY = 0.6
FLAP_STRENGTH = -10
MAX_FALL_SPEED = 12
PIPE_SPEED = 4
PIPE_GAP = 200
PIPE_SPAWN_TIME = 90
BULLET_SPEED = 12
FIRE_RATE = 15
ENEMY_SPEED = 2

class MenuButton:
    def __init__(self, x, y, width, height, text, font, color=Color.CYAN, hover_color=Color.YELLOW):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.is_hovered = False
        self.scale = 1.0
        self.target_scale = 1.0
        
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.is_hovered:
            self.current_color = self.hover_color
            self.target_scale = 1.05
        else:
            self.current_color = self.color
            self.target_scale = 1.0
        self.scale += (self.target_scale - self.scale) * 0.2
        
    def draw(self, surface):
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_rect = pygame.Rect(
            self.rect.centerx - scaled_width // 2,
            self.rect.centery - scaled_height // 2,
            scaled_width,
            scaled_height
        )
        
        shadow_rect = scaled_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(surface, (0, 0, 0, 100), shadow_rect, border_radius=10)
        
        for i in range(scaled_height):
            alpha = int(50 + (i / scaled_height) * 50)
            color = (*self.current_color[:3], alpha)
            pygame.draw.rect(surface, color, 
                           (scaled_rect.x, scaled_rect.y + i, scaled_width, 1))
        
        border_color = Color.WHITE if self.is_hovered else self.current_color
        pygame.draw.rect(surface, border_color, scaled_rect, 3, border_radius=10)
        
        text_surf = self.font.render(self.text, True, Color.WHITE)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        
        shadow_surf = self.font.render(self.text, True, Color.BLACK)
        shadow_rect = text_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        surface.blit(shadow_surf, shadow_rect)
        surface.blit(text_surf, text_rect)
        
    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed

class ToggleButton:
    def __init__(self, x, y, width, height, label, initial_state=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.state = initial_state
        self.is_hovered = False
        
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
    def toggle(self):
        self.state = not self.state
        
    def draw(self, surface, font):
        label_surf = font.render(self.label, True, Color.WHITE)
        surface.blit(label_surf, (self.rect.x - 150, self.rect.y + 5))
        
        bg_color = Color.GREEN if self.state else Color.DARK_GRAY
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=self.rect.height // 2)
        pygame.draw.rect(surface, Color.WHITE, self.rect, 2, border_radius=self.rect.height // 2)
        
        circle_x = self.rect.right - self.rect.height // 2 if self.state else self.rect.left + self.rect.height // 2
        circle_y = self.rect.centery
        pygame.draw.circle(surface, Color.WHITE, (circle_x, circle_y), self.rect.height // 2 - 4)
        
        state_text = "ON" if self.state else "OFF"
        state_surf = font.render(state_text, True, Color.WHITE)
        surface.blit(state_surf, (self.rect.right + 20, self.rect.y + 5))

class Particle:
    def __init__(self, x, y, color, velocity=None, size=None, lifetime=None):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        
        if velocity:
            self.vel_x, self.vel_y = velocity
        else:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            self.vel_x = math.cos(angle) * speed
            self.vel_y = math.sin(angle) * speed
            
        self.size = size or random.randint(2, 5)
        self.lifetime = lifetime or random.randint(20, 50)
        self.max_lifetime = self.lifetime
        self.alpha = 255
        
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += 0.2
        self.vel_x *= 0.98
        self.lifetime -= 1
        self.alpha = int(255 * (self.lifetime / self.max_lifetime))
        return self.lifetime > 0
        
    def draw(self, surface):
        if self.alpha > 0:
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            color_with_alpha = (*self.color[:3], self.alpha)
            pygame.draw.circle(s, color_with_alpha, (self.size, self.size), self.size)
            surface.blit(s, (int(self.x) - self.size, int(self.y) - self.size))

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.velocity_y = 0
        self.rotation = 0
        self.target_rotation = 0
        self.animation_frame = 0
        self.animation_timer = 0
        self.base_image = self.create_bird_sprite()
        self.image = self.base_image
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        self.can_shoot = True
        self.shoot_cooldown = 0
        self.health = 3
        self.invincible = False
        self.invincible_timer = 0
        self.alive = True
        
    def create_bird_sprite(self):
        size = 40
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        for i in range(15):
            radius = 18 - i
            color_val = 255 - i * 10
            pygame.draw.circle(surface, (255, color_val, 0), (20, 20), radius)
            
        wing_offset = int(math.sin(self.animation_frame * 0.3) * 3)
        pygame.draw.ellipse(surface, Color.ORANGE, (5, 15 + wing_offset, 15, 10))
        pygame.draw.circle(surface, Color.WHITE, (28, 15), 5)
        pygame.draw.circle(surface, Color.BLACK, (30, 15), 3)
        
        beak_points = [(35, 20), (45, 18), (45, 22)]
        pygame.draw.polygon(surface, Color.ORANGE, beak_points)
        return surface
        
    def update(self):
        if not self.alive:
            return
            
        self.velocity_y += GRAVITY
        self.velocity_y = min(self.velocity_y, MAX_FALL_SPEED)
        self.y += self.velocity_y
        
        self.target_rotation = -self.velocity_y * 3
        self.target_rotation = max(-45, min(45, self.target_rotation))
        
        rotation_diff = self.target_rotation - self.rotation
        self.rotation += rotation_diff * 0.2
        self.rect.centery = int(self.y)
        
        self.animation_frame += 1
        self.animation_timer += 1
        if self.animation_timer >= 5:
            self.animation_timer = 0
            self.base_image = self.create_bird_sprite()
            
        self.image = pygame.transform.rotate(self.base_image, self.rotation)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        else:
            self.can_shoot = True
            
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer == 0:
                self.invincible = False
                
        if self.y < -50 or self.y > SCREEN_HEIGHT + 50:
            self.health = 0
            self.alive = False
            
    def flap(self):
        if self.alive:
            self.velocity_y = FLAP_STRENGTH
        
    def shoot(self):
        if self.can_shoot and self.alive:
            self.can_shoot = False
            self.shoot_cooldown = FIRE_RATE
            return Bullet(self.x + 25, self.y)
        return None
        
    def take_damage(self):
        if not self.invincible and self.alive:
            self.health -= 1
            if self.health <= 0:
                self.alive = False
            self.invincible = True
            self.invincible_timer = 60
            return True
        return False
        
    def draw(self, surface):
        if not self.invincible or self.invincible_timer % 6 < 3:
            surface.blit(self.image, self.rect)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.image = pygame.Surface((12, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, Color.CYAN, (0, 0, 12, 6))
        pygame.draw.ellipse(self.image, Color.WHITE, (0, 1, 10, 4))
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        self.trail = []
        
    def update(self):
        self.x += BULLET_SPEED
        self.rect.centerx = int(self.x)
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 5:
            self.trail.pop(0)
        if self.x > SCREEN_WIDTH + 20:
            self.kill()
            
    def draw(self, surface):
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i + 1) / len(self.trail))
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*Color.CYAN[:3], alpha), (3, 3), 3)
            surface.blit(s, (pos[0] - 3, pos[1] - 3))
        surface.blit(self.image, self.rect)

class Pipe:
    def __init__(self, x, gap_y, destroyable=False):
        self.x = float(x)
        self.gap_y = gap_y
        self.destroyable = destroyable
        self.scored = False
        self.width = 70
        self.gap = PIPE_GAP
        self.top_height = gap_y - self.gap // 2
        self.bottom_y = gap_y + self.gap // 2
        self.bottom_height = SCREEN_HEIGHT - self.bottom_y
        self.health = 3 if destroyable else 999
        self.max_health = self.health
        self.create_images()
        
    def create_images(self):
        self.top_image = pygame.Surface((self.width, self.top_height))
        for y in range(self.top_height):
            progress = y / max(1, self.top_height)
            r = int(52 + progress * 30)
            g = int(199 - progress * 50)
            b = int(89 - progress * 30)
            pygame.draw.line(self.top_image, (r, g, b), (0, y), (self.width, y))
        
        cap_height = 35
        pygame.draw.rect(self.top_image, Color.DARK_GREEN, 
                        (0, max(0, self.top_height - cap_height), self.width, cap_height))
        pygame.draw.rect(self.top_image, Color.GREEN, 
                        (0, 0, self.width, self.top_height), 3)
        
        self.bottom_image = pygame.Surface((self.width, self.bottom_height))
        for y in range(self.bottom_height):
            progress = y / max(1, self.bottom_height)
            r = int(82 - progress * 30)
            g = int(199 - progress * 50)
            b = int(89 - progress * 30)
            pygame.draw.line(self.bottom_image, (r, g, b), (0, y), (self.width, y))
        
        pygame.draw.rect(self.bottom_image, Color.DARK_GREEN, (0, 0, self.width, cap_height))
        pygame.draw.rect(self.bottom_image, Color.GREEN, 
                        (0, 0, self.width, self.bottom_height), 3)
        
        if self.destroyable:
            if self.top_height > 40:
                center_y = self.top_height - 20
                pygame.draw.circle(self.top_image, Color.RED, 
                                 (self.width // 2, center_y), 10)
                pygame.draw.circle(self.top_image, Color.YELLOW, 
                                 (self.width // 2, center_y), 6)
            
            if self.bottom_height > 40:
                center_y = 20
                pygame.draw.circle(self.bottom_image, Color.RED, 
                                 (self.width // 2, center_y), 10)
                pygame.draw.circle(self.bottom_image, Color.YELLOW, 
                                 (self.width // 2, center_y), 6)
        
    def update(self):
        self.x -= PIPE_SPEED
        
    def get_rects(self):
        top_rect = pygame.Rect(int(self.x), 0, self.width, self.top_height)
        bottom_rect = pygame.Rect(int(self.x), self.bottom_y, self.width, self.bottom_height)
        return top_rect, bottom_rect
        
    def check_collision(self, player_rect):
        top_rect, bottom_rect = self.get_rects()
        return top_rect.colliderect(player_rect) or bottom_rect.colliderect(player_rect)
        
    def check_bullet_collision(self, bullet_rect):
        top_rect, bottom_rect = self.get_rects()
        return top_rect.colliderect(bullet_rect) or bottom_rect.colliderect(bullet_rect)
        
    def take_damage(self):
        if self.destroyable:
            self.health -= 1
            if self.health <= 0:
                return True
        return False
        
    def draw(self, surface):
        surface.blit(self.top_image, (int(self.x), 0))
        surface.blit(self.bottom_image, (int(self.x), self.bottom_y))
        
        if self.destroyable and self.health < self.max_health:
            bar_width = self.width - 10
            health_ratio = self.health / self.max_health
            health_width = int(bar_width * health_ratio)
            bar_x = self.x + 5
            bar_y = self.gap_y - 15
            pygame.draw.rect(surface, Color.RED, (bar_x, bar_y, bar_width, 8))
            pygame.draw.rect(surface, Color.GREEN, (bar_x, bar_y, health_width, 8))
            pygame.draw.rect(surface, Color.WHITE, (bar_x, bar_y, bar_width, 8), 2)
            
    def is_off_screen(self):
        return self.x < -self.width

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="wave"):
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.enemy_type = enemy_type
        self.health = 2
        self.max_health = 2
        self.velocity_x = -ENEMY_SPEED
        self.velocity_y = 0
        self.timer = random.randint(0, 60)
        
        if enemy_type == "chase":
            self.base_color = Color.BRIGHT_RED
            self.dark_color = Color.DARK_RED
        else:
            self.base_color = Color.PURPLE
            self.dark_color = (120, 50, 150)
        
        self.image = self.create_enemy_sprite()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        self.animation_frame = 0
        
    def create_enemy_sprite(self):
        size = 35
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        for i in range(8):
            radius = 15 - i
            if self.enemy_type == "chase":
                color_r = 255 - i * 20
                color_g = 50 - i * 5
                color_b = 50 - i * 5
                pygame.draw.circle(surface, (color_r, color_g, color_b), 
                                 (size // 2, size // 2), radius)
            else:
                color_val = 200 - i * 15
                pygame.draw.circle(surface, (color_val, 50, 200), 
                                 (size // 2, size // 2), radius)
            
        eye_x = size // 2 - 5
        pygame.draw.circle(surface, Color.WHITE, (eye_x, size // 2 - 3), 4)
        
        if self.enemy_type == "chase":
            pygame.draw.circle(surface, Color.YELLOW, (eye_x, size // 2 - 3), 2)
        else:
            pygame.draw.circle(surface, Color.RED, (eye_x, size // 2 - 3), 2)
        
        spike_color = self.dark_color
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            spike_x = size // 2 + math.cos(rad) * 18
            spike_y = size // 2 + math.sin(rad) * 18
            pygame.draw.circle(surface, spike_color, (int(spike_x), int(spike_y)), 3)
        return surface
        
    def update(self, player_y=None):
        self.timer += 1
        self.animation_frame += 1
        
        if self.enemy_type == "wave":
            self.velocity_y = math.sin(self.timer * 0.05) * 2
        elif self.enemy_type == "chase" and player_y:
            diff = player_y - self.y
            self.velocity_y = max(-4, min(4, diff * 0.08))
            
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.y = max(20, min(SCREEN_HEIGHT - 20, self.y))
        self.rect.center = (int(self.x), int(self.y))
        
        if self.animation_frame % 10 == 0:
            self.image = self.create_enemy_sprite()
            
        if self.x < -50:
            self.kill()
            
    def take_damage(self):
        self.health -= 1
        return self.health <= 0
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
        if self.health < self.max_health:
            bar_width = 30
            health_ratio = self.health / self.max_health
            health_width = int(bar_width * health_ratio)
            bar_x = self.x - bar_width // 2
            bar_y = self.y - 25
            pygame.draw.rect(surface, Color.RED, (bar_x, bar_y, bar_width, 5))
            pygame.draw.rect(surface, Color.GREEN, (bar_x, bar_y, health_width, 5))

class StarField:
    def __init__(self):
        self.stars = []
        for _ in range(50):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            speed = random.uniform(0.5, 2)
            size = random.randint(1, 3)
            self.stars.append([x, y, speed, size])
            
    def update(self):
        for star in self.stars:
            star[0] -= star[2]
            if star[0] < 0:
                star[0] = SCREEN_WIDTH
                star[1] = random.randint(0, SCREEN_HEIGHT)
                
    def draw(self, surface):
        for star in self.stars:
            alpha = int(150 + random.randint(-50, 50))
            color = (*Color.WHITE[:3], alpha)
            s = pygame.Surface((star[3] * 2, star[3] * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (star[3], star[3]), star[3])
            surface.blit(s, (int(star[0]) - star[3], int(star[1]) - star[3]))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Shooter - New Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.LANDING
        self.score = 0
        self.high_score = 0
        self.death_reason = ""
        self.sound_enabled = True
        self.how_to_play_scroll = 0
        self.credits_scroll = 0
        self.max_how_to_play_scroll = 0
        self.max_credits_scroll = 0
        self.player = None
        self.pipes = []
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.particles = []
        self.pipe_timer = 0
        self.enemy_timer = 0
        self.difficulty = 1
        self.starfield = StarField()
        self.background_gradient_offset = 0
        self.shake_amount = 0
        
        try:
            self.font_title = pygame.font.Font(None, 100)
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 32)
            self.font_tiny = pygame.font.Font(None, 24)
        except:
            self.font_title = pygame.font.Font(None, 100)
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 32)
            self.font_tiny = pygame.font.Font(None, 24)
        
        self.setup_menu_buttons()
        self.create_sounds()
        
    def setup_menu_buttons(self):
        center_x = SCREEN_WIDTH // 2
        self.btn_play = MenuButton(center_x - 150, 250, 300, 60, "PLAY GAME", self.font_medium)
        self.btn_how_to = MenuButton(center_x - 150, 330, 300, 60, "HOW TO PLAY", self.font_medium)
        self.btn_settings = MenuButton(center_x - 150, 410, 300, 60, "SETTINGS", self.font_medium)
        self.btn_credits = MenuButton(center_x - 150, 490, 300, 60, "CREDITS", self.font_medium)
        self.btn_back = MenuButton(30, 30, 120, 50, "◄ BACK", self.font_small, Color.ORANGE, Color.YELLOW)
        self.toggle_sound = ToggleButton(center_x + 50, 300, 80, 40, "Sound Effects:", self.sound_enabled)
        
    def create_sounds(self):
        try:
            self.flap_sound = pygame.mixer.Sound(buffer=self.generate_tone(440, 0.1))
            self.flap_sound.set_volume(0.3)
            self.shoot_sound = pygame.mixer.Sound(buffer=self.generate_tone(880, 0.05))
            self.shoot_sound.set_volume(0.2)
            self.hit_sound = pygame.mixer.Sound(buffer=self.generate_tone(220, 0.1))
            self.hit_sound.set_volume(0.4)
            self.explosion_sound = pygame.mixer.Sound(buffer=self.generate_noise(0.2))
            self.explosion_sound.set_volume(0.3)
        except:
            self.flap_sound = None
            self.shoot_sound = None
            self.hit_sound = None
            self.explosion_sound = None
            
    def generate_tone(self, frequency, duration):
        sample_rate = 22050
        samples = int(sample_rate * duration)
        wave = [int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate)) 
                for i in range(samples)]
        import array
        sound_array = array.array('h', wave)
        return sound_array.tobytes()
        
    def generate_noise(self, duration):
        sample_rate = 22050
        samples = int(sample_rate * duration)
        import array
        noise = array.array('h', [random.randint(-32767, 32767) for _ in range(samples)])
        return noise.tobytes()
        
    def play_sound(self, sound):
        if sound and self.sound_enabled:
            try:
                sound.play()
            except:
                pass
                
    def reset_game(self):
        self.player = Player(150, SCREEN_HEIGHT // 2)
        self.pipes = []
        self.bullets.empty()
        self.enemies.empty()
        self.particles.clear()
        self.score = 0
        self.pipe_timer = 0
        self.enemy_timer = 0
        self.difficulty = 1
        self.death_reason = ""
        
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.MOUSEWHEEL:
                if self.state == GameState.HOW_TO_PLAY:
                    self.how_to_play_scroll -= event.y * 20
                    self.how_to_play_scroll = max(0, min(self.how_to_play_scroll, self.max_how_to_play_scroll))
                elif self.state == GameState.CREDITS:
                    self.credits_scroll -= event.y * 20
                    self.credits_scroll = max(0, min(self.credits_scroll, self.max_credits_scroll))
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pressed = True
                if self.state == GameState.SETTINGS:
                    if self.toggle_sound.rect.collidepoint(mouse_pos):
                        self.toggle_sound.toggle()
                        self.sound_enabled = self.toggle_sound.state
                
            if event.type == pygame.KEYDOWN:
                if self.state == GameState.HOW_TO_PLAY:
                    if event.key == pygame.K_UP:
                        self.how_to_play_scroll -= 30
                        self.how_to_play_scroll = max(0, self.how_to_play_scroll)
                    elif event.key == pygame.K_DOWN:
                        self.how_to_play_scroll += 30
                        self.how_to_play_scroll = min(self.how_to_play_scroll, self.max_how_to_play_scroll)
                elif self.state == GameState.CREDITS:
                    if event.key == pygame.K_UP:
                        self.credits_scroll -= 30
                        self.credits_scroll = max(0, self.credits_scroll)
                    elif event.key == pygame.K_DOWN:
                        self.credits_scroll += 30
                        self.credits_scroll = min(self.credits_scroll, self.max_credits_scroll)
                
                if self.state == GameState.PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.player.flap()
                        self.play_sound(self.flap_sound)
                    if event.key == pygame.K_RSHIFT or event.key == pygame.K_f:
                        bullet = self.player.shoot()
                        if bullet:
                            self.bullets.add(bullet)
                            self.play_sound(self.shoot_sound)
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_r:
                        self.state = GameState.LANDING
                    elif event.key == pygame.K_RETURN:
                        self.reset_game()
                        self.state = GameState.PLAYING
                        
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == GameState.PLAYING:
                    bullet = self.player.shoot()
                    if bullet:
                        self.bullets.add(bullet)
                        self.play_sound(self.shoot_sound)
        
        if self.state == GameState.LANDING:
            self.btn_play.update(mouse_pos)
            self.btn_how_to.update(mouse_pos)
            self.btn_settings.update(mouse_pos)
            self.btn_credits.update(mouse_pos)
            
            if mouse_pressed:
                if self.btn_play.is_clicked(mouse_pos, True):
                    self.reset_game()
                    self.state = GameState.PLAYING
                elif self.btn_how_to.is_clicked(mouse_pos, True):
                    self.how_to_play_scroll = 0
                    self.state = GameState.HOW_TO_PLAY
                elif self.btn_settings.is_clicked(mouse_pos, True):
                    self.state = GameState.SETTINGS
                elif self.btn_credits.is_clicked(mouse_pos, True):
                    self.credits_scroll = 0
                    self.state = GameState.CREDITS
                    
        elif self.state in [GameState.HOW_TO_PLAY, GameState.CREDITS, GameState.SETTINGS]:
            self.btn_back.update(mouse_pos)
            if self.state == GameState.SETTINGS:
                self.toggle_sound.update(mouse_pos)
            if mouse_pressed and self.btn_back.is_clicked(mouse_pos, True):
                self.state = GameState.LANDING
                
    def update(self):
        if self.state == GameState.LANDING:
            self.starfield.update()
            self.background_gradient_offset += 0.5
            
        elif self.state == GameState.PLAYING:
            self.starfield.update()
            self.background_gradient_offset += 0.5
            self.player.update()
            
            if not self.player.alive:
                if self.player.y < -50:
                    self.death_reason = "Flew too high!"
                elif self.player.y > SCREEN_HEIGHT + 50:
                    self.death_reason = "Fell off the screen!"
                self.game_over()
                return
            
            self.bullets.update()
            
            for enemy in self.enemies:
                enemy.update(self.player.y)
                
            self.particles = [p for p in self.particles if p.update()]
            
            self.pipe_timer += 1
            if self.pipe_timer >= PIPE_SPAWN_TIME:
                self.pipe_timer = 0
                gap_y = random.randint(150, SCREEN_HEIGHT - 150)
                destroyable = random.random() < 0.3
                pipe = Pipe(SCREEN_WIDTH, gap_y, destroyable)
                self.pipes.append(pipe)
                
            for pipe in self.pipes[:]:
                pipe.update()
                if pipe.is_off_screen():
                    self.pipes.remove(pipe)
                    
            self.enemy_timer += 1
            spawn_rate = max(120 - self.difficulty * 10, 60)
            if self.enemy_timer >= spawn_rate:
                self.enemy_timer = 0
                y = random.randint(100, SCREEN_HEIGHT - 100)
                enemy_type = random.choice(["wave", "chase"])
                enemy = Enemy(SCREEN_WIDTH + 50, y, enemy_type)
                self.enemies.add(enemy)
                
            for bullet in self.bullets:
                for pipe in self.pipes[:]:
                    if pipe.check_bullet_collision(bullet.rect):
                        bullet.kill()
                        if pipe.take_damage():
                            self.score += 5
                            self.create_explosion(pipe.x + pipe.width // 2, pipe.gap_y, Color.GREEN)
                            self.play_sound(self.explosion_sound)
                            self.pipes.remove(pipe)
                        else:
                            self.create_hit_particles(bullet.x, bullet.y)
                            self.play_sound(self.hit_sound)
                        break
                            
            for bullet in self.bullets:
                for enemy in self.enemies:
                    if bullet.rect.colliderect(enemy.rect):
                        bullet.kill()
                        if enemy.take_damage():
                            self.score += 10
                            explosion_color = Color.BRIGHT_RED if enemy.enemy_type == "chase" else Color.PURPLE
                            self.create_explosion(enemy.x, enemy.y, explosion_color)
                            self.play_sound(self.explosion_sound)
                            enemy.kill()
                        else:
                            self.create_hit_particles(bullet.x, bullet.y)
                            self.play_sound(self.hit_sound)
                        break
                            
            for pipe in self.pipes:
                if pipe.check_collision(self.player.rect):
                    if self.player.take_damage():
                        self.screen_shake(10)
                        self.play_sound(self.hit_sound)
                        if self.player.health <= 0:
                            self.death_reason = "Hit a pipe!"
                            self.game_over()
                            
                if not pipe.scored and pipe.x + pipe.width < self.player.x:
                    pipe.scored = True
                    self.score += 1
                    
            for enemy in self.enemies:
                if self.player.rect.colliderect(enemy.rect):
                    enemy.kill()
                    if self.player.take_damage():
                        explosion_color = Color.BRIGHT_RED if enemy.enemy_type == "chase" else Color.PURPLE
                        self.create_explosion(enemy.x, enemy.y, explosion_color)
                        self.screen_shake(15)
                        self.play_sound(self.explosion_sound)
                        if self.player.health <= 0:
                            enemy_name = "red chaser" if enemy.enemy_type == "chase" else "purple enemy"
                            self.death_reason = f"Killed by {enemy_name}!"
                            self.game_over()
                            
            if self.score > 0 and self.score % 10 == 0:
                self.difficulty = min(self.score // 10 + 1, 5)
                
            if self.shake_amount > 0:
                self.shake_amount -= 1
                
        elif self.state == GameState.GAME_OVER:
            self.starfield.update()
        elif self.state in [GameState.HOW_TO_PLAY, GameState.CREDITS, GameState.SETTINGS]:
            self.starfield.update()
            self.background_gradient_offset += 0.5
            
    def create_explosion(self, x, y, color):
        for _ in range(30):
            self.particles.append(Particle(x, y, color))
            
    def create_hit_particles(self, x, y):
        for _ in range(10):
            self.particles.append(Particle(x, y, Color.WHITE, size=3, lifetime=20))
            
    def screen_shake(self, amount):
        self.shake_amount = amount
        
    def game_over(self):
        self.state = GameState.GAME_OVER
        self.high_score = max(self.high_score, self.score)
        if not self.death_reason:
            self.death_reason = "Game Over!"
        
    def draw_gradient_background(self):
        offset = int(self.background_gradient_offset) % 256
        
        for y in range(SCREEN_HEIGHT):
            progress = (y / SCREEN_HEIGHT)
            time = (offset / 256)
            r = int(25 + progress * 20)
            g = int(25 + progress * 40)
            b = int(112 - progress * 50)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
            
    def draw(self):
        shake_x = random.randint(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        shake_y = random.randint(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        
        self.draw_gradient_background()
        self.starfield.draw(self.screen)
        
        if self.state == GameState.LANDING:
            self.draw_landing_page()
        elif self.state == GameState.PLAYING:
            for pipe in self.pipes:
                pipe.draw(self.screen)
            for particle in self.particles:
                particle.draw(self.screen)
            for bullet in self.bullets:
                bullet.draw(self.screen)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            self.player.draw(self.screen)
            self.draw_ui()
        elif self.state == GameState.GAME_OVER:
            for pipe in self.pipes:
                pipe.draw(self.screen)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            if self.player:
                self.player.draw(self.screen)
            self.draw_game_over()
        elif self.state == GameState.HOW_TO_PLAY:
            self.draw_how_to_play()
        elif self.state == GameState.CREDITS:
            self.draw_credits()
        elif self.state == GameState.SETTINGS:
            self.draw_settings()
            
        pygame.display.flip()
        
    def draw_landing_page(self):
        title = "FLAPPY SHOOTER"
        
        for offset in range(8, 0, -1):
            glow_surf = self.font_title.render(title, True, Color.CYAN)
            glow_surf.set_alpha(30 * (9 - offset))
            rect = glow_surf.get_rect(center=(SCREEN_WIDTH // 2 + offset, 120 + offset))
            self.screen.blit(glow_surf, rect)
        
        title_surf = self.font_title.render(title, True, Color.WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title_surf, title_rect)
        
        subtitle = self.font_small.render("--Made by MANMEET--", True, Color.GOLD)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 190))
        self.screen.blit(subtitle, subtitle_rect)
        
        self.btn_play.draw(self.screen)
        self.btn_how_to.draw(self.screen)
        self.btn_settings.draw(self.screen)
        self.btn_credits.draw(self.screen)
        
        if self.high_score > 0:
            hs_text = self.font_small.render(f"High Score: {self.high_score}", True, Color.GOLD)
            hs_rect = hs_text.get_rect(center=(SCREEN_WIDTH // 2, 570))
            hs_shadow = self.font_small.render(f"High Score: {self.high_score}", True, Color.BLACK)
            shadow_rect = hs_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            self.screen.blit(hs_shadow, shadow_rect)
            self.screen.blit(hs_text, hs_rect)
            
    def draw_how_to_play(self):
        self.btn_back.draw(self.screen)
        
        title = self.font_large.render("HOW TO PLAY", True, Color.YELLOW)
        title_shadow = self.font_large.render("HOW TO PLAY", True, Color.BLACK)
        self.screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, 63))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
        
        instructions = [
            ("CONTROLS", Color.CYAN, self.font_medium, "title"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("SPACE - Make the bird flap upward", Color.WHITE, self.font_small, "normal"),
            ("Right Shift / F / Click - Shoot bullets", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("OBJECTIVE", Color.CYAN, self.font_medium, "title"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("• Navigate through pipes without crashing", Color.WHITE, self.font_small, "bullet"),
            ("• Shoot enemies to earn points", Color.WHITE, self.font_small, "bullet"),
            ("• Destroy pipes with marks for bonus point", Color.WHITE, self.font_small, "bullet"),
            ("• Stay on screen - don't fly too high or fall", Color.WHITE, self.font_small, "bullet"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("ENEMIES", Color.CYAN, self.font_medium, "title"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("Purple Alien - Moves in wave patterns", Color.PURPLE, self.font_small, "bullet"),
            ("Red Alien - Chases your position", Color.BRIGHT_RED, self.font_small, "bullet"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("SCORING", Color.CYAN, self.font_medium, "title"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("Pass pipe: +1 point", Color.GREEN, self.font_small, "bullet"),
            ("Destroy marked pipe: +5 points", Color.YELLOW, self.font_small, "bullet"),
            ("Kill enemy: +10 points", Color.ORANGE, self.font_small, "bullet"),
        ]
        
        total_height = len(instructions) * 30 + 50
        content_start_y = 130
        visible_height = SCREEN_HEIGHT - content_start_y - 30
        self.max_how_to_play_scroll = max(0, total_height - visible_height)
        
        y = content_start_y - self.how_to_play_scroll
        for text, color, font, text_type in instructions:
            if text:
                surf = font.render(text, True, color)
                if y > content_start_y - 50 and y < SCREEN_HEIGHT:
                    if text_type == "bullet":
                        x = SCREEN_WIDTH // 2 - 200
                        self.screen.blit(surf, (x, y))
                    else:
                        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
                        self.screen.blit(surf, rect)
            y += 30
            
        if self.max_how_to_play_scroll > 0:
            bar_x = SCREEN_WIDTH - 15
            bar_y = content_start_y
            bar_height = visible_height
            pygame.draw.rect(self.screen, Color.DARK_GRAY, (bar_x, bar_y, 10, bar_height))
            thumb_height = max(30, int(visible_height * (visible_height / total_height)))
            thumb_y = bar_y + int((visible_height - thumb_height) * (self.how_to_play_scroll / self.max_how_to_play_scroll))
            pygame.draw.rect(self.screen, Color.CYAN, (bar_x, thumb_y, 10, thumb_height))
            hint = self.font_tiny.render("Use mouse wheel or arrow keys to scroll", True, Color.LIGHT_GRAY)
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 25))
            
    def draw_credits(self):
        self.btn_back.draw(self.screen)
        
        title = self.font_large.render("CREDITS", True, Color.GOLD)
        title_shadow = self.font_large.render("CREDITS", True, Color.BLACK)
        self.screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, 63))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
        
        credits = [
            ("DEVELOPER", Color.CYAN, self.font_medium, "title"),
            ("Manmeet Singh", Color.WHITE, self.font_large, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("GAME DESIGN & PROGRAMMING", Color.CYAN, self.font_medium, "title"),
            ("Manmeet Singh", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("GRAPHICS & VISUAL EFFECTS", Color.CYAN, self.font_medium, "title"),
            ("System Generated", Color.WHITE, self.font_small, "normal"),
            ("Pygame Library", Color.WHITE, self.font_tiny, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("SOUND EFFECTS", Color.CYAN, self.font_medium, "title"),
            ("System Generated Tones", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("SPECIAL THANKS", Color.CYAN, self.font_medium, "title"),
            ("All players who enjoy this game!", Color.YELLOW, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("CONTACT & INFO", Color.CYAN, self.font_medium, "title"),
            ("GitHub: github.com/Manmeet2405", Color.WHITE, self.font_small, "normal"),
            ("Email: manmeet24m@gmail.com", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("", Color.WHITE, self.font_small, "normal"),
            ("2026 - Manmeet Singh", Color.WHITE, self.font_medium, "normal"),
            ("~Was originally made in 2023", Color.GOLD, self.font_small, "normal"),
            (" ", Color.WHITE, self.font_small, "normal"),
            ("Version 1.0 - Flappy Shooter", Color.WHITE, self.font_medium, "normal"),
        ]
        
        line_heights = []
        for text, color, font, text_type in credits:
            if font == self.font_large:
                line_heights.append(45)
            elif font == self.font_medium:
                line_heights.append(40)
            elif font == self.font_small:
                line_heights.append(32)
            else:
                line_heights.append(28)
                
        total_height = sum(line_heights) + 50
        content_start_y = 130
        visible_height = SCREEN_HEIGHT - content_start_y - 30
        self.max_credits_scroll = max(0, total_height - visible_height)
        
        y = content_start_y - self.credits_scroll
        for i, (text, color, font, text_type) in enumerate(credits):
            if text:
                surf = font.render(text, True, color)
                if y > content_start_y - 50 and y < SCREEN_HEIGHT:
                    rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y))
                    if font == self.font_large or font == self.font_medium:
                        shadow = font.render(text, True, Color.BLACK)
                        shadow_rect = rect.copy()
                        shadow_rect.x += 2
                        shadow_rect.y += 2
                        self.screen.blit(shadow, shadow_rect)
                    self.screen.blit(surf, rect)
            y += line_heights[i]
            
        if self.max_credits_scroll > 0:
            bar_x = SCREEN_WIDTH - 15
            bar_y = content_start_y
            bar_height = visible_height
            pygame.draw.rect(self.screen, Color.DARK_GRAY, (bar_x, bar_y, 10, bar_height))
            thumb_height = max(30, int(visible_height * (visible_height / total_height)))
            thumb_y = bar_y + int((visible_height - thumb_height) * (self.credits_scroll / self.max_credits_scroll))
            pygame.draw.rect(self.screen, Color.GOLD, (bar_x, thumb_y, 10, thumb_height))
            hint = self.font_tiny.render("Use mouse wheel or arrow keys to scroll", True, Color.LIGHT_GRAY)
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 25))
            
    def draw_settings(self):
        self.btn_back.draw(self.screen)
        
        title = self.font_large.render("SETTINGS", True, Color.CYAN)
        title_shadow = self.font_large.render("SETTINGS", True, Color.BLACK)
        self.screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, 63))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
        
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 200, 500, 200)
        pygame.draw.rect(self.screen, (40, 40, 60, 200), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, Color.WHITE, panel_rect, 3, border_radius=15)
        
        audio_title = self.font_medium.render("AUDIO", True, Color.YELLOW)
        self.screen.blit(audio_title, (SCREEN_WIDTH // 2 - audio_title.get_width() // 2, 230))
        self.toggle_sound.draw(self.screen, self.font_small)
        
            
    def draw_ui(self):
        score_text = self.font_large.render(str(self.score), True, Color.WHITE)
        score_shadow = self.font_large.render(str(self.score), True, Color.BLACK)
        self.screen.blit(score_shadow, (SCREEN_WIDTH // 2 - score_text.get_width() // 2 + 3, 33))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 30))
        
        heart_size = 30
        for i in range(self.player.health):
            x = 20 + i * (heart_size + 10)
            y = 20
            surf = pygame.Surface((heart_size, heart_size), pygame.SRCALPHA)
            points = [
                (heart_size // 2, heart_size - 5),
                (5, heart_size // 3),
                (heart_size // 2, 5),
                (heart_size - 5, heart_size // 3)
            ]
            pygame.draw.polygon(surf, Color.RED, points)
            self.screen.blit(surf, (x, y))
            
        diff_text = self.font_small.render(f"Level: {self.difficulty}", True, Color.YELLOW)
        self.screen.blit(diff_text, (SCREEN_WIDTH - 150, 30))
        
    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        game_over = self.font_large.render("GAME OVER", True, Color.RED)
        shadow = self.font_large.render("GAME OVER", True, Color.BLACK)
        
        y_pos = SCREEN_HEIGHT // 2 - 150
        self.screen.blit(shadow, (SCREEN_WIDTH // 2 - game_over.get_width() // 2 + 3, y_pos + 3))
        self.screen.blit(game_over, (SCREEN_WIDTH // 2 - game_over.get_width() // 2, y_pos))
        
        reason = self.font_medium.render(self.death_reason, True, Color.ORANGE)
        self.screen.blit(reason, (SCREEN_WIDTH // 2 - reason.get_width() // 2, y_pos + 80))
        
        score = self.font_medium.render(f"Score: {self.score}", True, Color.WHITE)
        self.screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, y_pos + 150))
        
        high_score = self.font_medium.render(f"High Score: {self.high_score}", True, Color.GOLD)
        self.screen.blit(high_score, (SCREEN_WIDTH // 2 - high_score.get_width() // 2, y_pos + 200))
        
        pygame.draw.line(self.screen, Color.WHITE, 
                        (SCREEN_WIDTH // 2 - 150, y_pos + 250),
                        (SCREEN_WIDTH // 2 + 150, y_pos + 250), 2)
        
        restart1 = self.font_small.render("Press ENTER to Play Again", True, Color.GREEN)
        restart2 = self.font_small.render("Press SPACE to Menu", True, Color.CYAN)
        self.screen.blit(restart1, (SCREEN_WIDTH // 2 - restart1.get_width() // 2, y_pos + 270))
        self.screen.blit(restart2, (SCREEN_WIDTH // 2 - restart2.get_width() // 2, y_pos + 310))
        
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
