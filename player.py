import pygame

from effects import GameEffects
from enemy import Enemy

# Handles player animations, movement, and actions.

# player.py
import pygame
from enemy import Enemy

class Player:
    def __init__(self, sprite_sheet, x, y, speed=5):
        self.x, self.y = x, y
        self.speed = speed
        self.direction = "idle"
        self.frame_index = 0
        self.sprite_width, self.sprite_height = 48, 48
        self.width = self.sprite_width  # Add width attribute
        self.height = self.sprite_height  # Add height attribute
        self.load_animations(sprite_sheet)
        self.attacking = False
        self.attack_start_time = 0
        self.projectiles = []
        self.attack_duration = 300  # Duration of attack in milliseconds
        self.projectile_speed = 7
        self.health = 100
        self.max_health = 100
        self.enemies = []  # Initialize enemies as an empty list or populate it as needed
        self.effects = GameEffects()  # Initialize GameEffects instance
        self.last_projectile_time = 0  # Track the last time a projectile was fired
        self.projectile_cooldown = 500  # Cooldown in milliseconds (e.g., 500ms)

    def load_animations(self, sheet):
        """Extracts frames for different animations."""
        self.walk_right = [self.get_frame(sheet, i, 0) for i in range(4)]
        self.walk_left = [self.get_frame(sheet, i, 1) for i in range(4)]
        self.walk_up = [self.get_frame(sheet, i, 2) for i in range(4)]
        self.walk_down = [self.get_frame(sheet, i, 3) for i in range(4)]
        self.crafting = [self.get_frame(sheet, i, 4) for i in range(4)]
        self.attack = [self.get_frame(sheet, i, 5) for i in range(4)]
        self.idle = self.get_frame(sheet, 0, 0)
    
    def get_frame(self, sheet, frame, row):
        return sheet.subsurface(pygame.Rect(frame * self.sprite_width, row * self.sprite_height, self.sprite_width, self.sprite_height))
    
    def move(self, keys):
        """Handles movement logic."""
        moving = False
        if keys[pygame.K_w]: self.y -= self.speed; self.direction = "up"; moving = True
        if keys[pygame.K_s]: self.y += self.speed; self.direction = "down"; moving = True
        if keys[pygame.K_a]: self.x -= self.speed; self.direction = "left"; moving = True
        if keys[pygame.K_d]: self.x += self.speed; self.direction = "right"; moving = True
        return moving
    
    def animate(self, moving, keys, enemies):
        """Updates sprite based on movement or actions."""
        current_time = pygame.time.get_ticks()

        if keys[pygame.K_SPACE] and not self.attacking:  # Melee attack
            self.attacking = True
            self.attack_start_time = current_time
            self.effects.play_attack_sound()  # Play attack sound

        if keys[pygame.K_f] and current_time - self.last_projectile_time >= self.projectile_cooldown:
            # Ranged attack (shoot projectile)
            self.projectiles.append({
                "x": self.x + self.sprite_width // 2,
                "y": self.y + self.sprite_height // 2,
                "dir": self.direction,
                "width": 5,
                "height": 5
            })
            self.effects.play_hit_sound()  # Play projectile sound
            self.last_projectile_time = current_time  # Update the last projectile time

        # Update attack animation
        if self.attacking:
            self.frame_index = (self.frame_index + 1) % 3
            if self.direction == "right":
                player_sprite = self.attack[self.frame_index]
            elif self.direction == "left":
                player_sprite = self.attack[self.frame_index]
            else:
                player_sprite = self.idle  # Default to idle if attack frames are unavailable

            # Check if attack animation is done
            if pygame.time.get_ticks() - self.attack_start_time > self.attack_duration:
                self.attacking = False
        elif moving:
            self.frame_index = (self.frame_index + 1) % 4
            if self.direction == "right":
                player_sprite = self.walk_right[self.frame_index]
            elif self.direction == "left":
                player_sprite = self.walk_left[self.frame_index]
            elif self.direction == "up":
                player_sprite = self.walk_up[self.frame_index]
            elif self.direction == "down":
                player_sprite = self.walk_down[self.frame_index]
        else:
            player_sprite = self.idle  # Idle animation

        # Update and draw projectiles
        for projectile in self.projectiles[:]:
            if projectile["dir"] == "right":
                projectile["x"] += self.projectile_speed
            elif projectile["dir"] == "left":
                projectile["x"] -= self.projectile_speed
            elif projectile["dir"] == "up":
                projectile["y"] -= self.projectile_speed
            elif projectile["dir"] == "down":
                projectile["y"] += self.projectile_speed

            pygame.draw.circle(pygame.display.get_surface(), (255, 255, 255), (projectile["x"], projectile["y"]), 5)

            # Check collision with enemies
            for enemy in self.enemies:  # Assuming enemies is a list of Enemy objects
                if enemy.collides_with(projectile):
                    enemies.remove(enemy)  # Remove enemy on collision
                    self.projectiles.remove(projectile)  # Remove projectile on collision
                    break

            # Remove projectiles that go off-screen
            if projectile["x"] > pygame.display.get_surface().get_width() or projectile["x"] < 0 or projectile["y"] > pygame.display.get_surface().get_height() or projectile["y"] < 0:
                self.projectiles.remove(projectile)

        return player_sprite

