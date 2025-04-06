import pygame
import random
from typing import Dict  # Import for type annotations
from effects import GameEffects  # Import GameEffects

class Enemy:
    def __init__(self, sprite_sheet, x, y):
        # Position and movement
        self.x = x
        self.y = y
        self.last_x = x  # For animation direction
        self.last_y = y  # For animation direction
        self.speed = 2
        
        # Stats
        self.health = 50
        self.max_health = 50
        self.damage = 10
        self.attack_cooldown = 1.0  # Seconds between attacks
        self.chase_range = 300
        self.attack_range = 40
        
        # State
        self.active = True
        self.state = "idle"  # "idle", "chase", or "attack"
        self.last_attack_time = 0
        
        # Sprite and animation
        self.sprite_width = 48
        self.sprite_height = 48
        self.frame_index = 0
        self.animation_speed = 10
        self.frame_counter = 0
        self.sprite = None
        
        # Load animations from 4x6 spritesheet
        if sprite_sheet.get_width() >= self.sprite_width * 4 and sprite_sheet.get_height() >= self.sprite_height * 6:
            # Full spritesheet format (4x6)
            self.walk_right = [self.get_frame(sprite_sheet, i, 0) for i in range(4)]
            self.walk_left = [self.get_frame(sprite_sheet, i, 1) for i in range(4)]
            self.walk_up = [self.get_frame(sprite_sheet, i, 2) for i in range(4)]
            self.walk_down = [self.get_frame(sprite_sheet, i, 3) for i in range(4)]
            self.idle_frames = [self.get_frame(sprite_sheet, i, 4) for i in range(4)]
            self.attack_frames = [self.get_frame(sprite_sheet, i, 5) for i in range(4)]
        else:
            # Fallback to single sprite if spritesheet is invalid
            print("Warning: Enemy sprite sheet too small, using fallback")
            fallback = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
            fallback.fill((255, 0, 0))  # Red for enemy visibility
            self.walk_right = [fallback] * 4
            self.walk_left = [fallback] * 4
            self.walk_up = [fallback] * 4
            self.walk_down = [fallback] * 4
            self.idle_frames = [fallback] * 4
            self.attack_frames = [fallback] * 4
        
        self.sprite = self.idle_frames[0]  # Initial sprite
        
        # Effects
        self.effects = GameEffects()

    def get_frame(self, sheet, frame, row):
        """Extract a single frame from a sprite sheet."""
        return sheet.subsurface(pygame.Rect(
            frame * self.sprite_width, 
            row * self.sprite_height, 
            self.sprite_width, 
            self.sprite_height
        ))

    def update(self, player):
        """Update enemy behavior based on player position."""
        if not self.active or not player:
            return
            
        # Calculate distance to player
        distance = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5
        
        # Determine state based on distance
        if distance < self.attack_range:
            self.state = "attack"
            # Attack the player
            self.attack_player(player)
        elif distance < self.chase_range:
            self.state = "chase"
            # Chase the player
            self.chase_player(player)
        else:
            self.state = "idle"

    def chase_player(self, player):
        """Move towards the player."""
        # Determine direction to player
        dx = player.x - self.x
        dy = player.y - self.y
        
        # Normalize the vector (maintain constant speed regardless of direction)
        distance = max(0.1, ((dx ** 2) + (dy ** 2)) ** 0.5)
        dx = dx / distance * self.speed
        dy = dy / distance * self.speed
        
        # Update position
        self.x += dx
        self.y += dy

    def attack_player(self, player):
        """Attack the player if cooldown has elapsed."""
        current_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds
        
        # Check if attack cooldown has elapsed
        if current_time - self.last_attack_time >= self.attack_cooldown:
            # Deal damage
            if player.decrease_health(self.damage):
                # Only play sound if damage was actually dealt
                self.effects.play_attack_sound()
            
            # Reset cooldown
            self.last_attack_time = current_time

    def animate(self):
        """Update animation based on current state."""
        # Update animation frame
        self.frame_counter += 1
        if self.frame_counter >= self.animation_speed:
            self.frame_counter = 0
            self.frame_index = (self.frame_index + 1) % 4
        
        # Set sprite based on state and direction
        if self.state == "idle":
            self.sprite = self.idle_frames[self.frame_index]
        elif self.state == "chase":
            # Use the last movement direction for animation
            dx = self.x - self.last_x if hasattr(self, 'last_x') else 0
            dy = self.y - self.last_y if hasattr(self, 'last_y') else 0
            
            if abs(dx) > abs(dy):
                if dx > 0:
                    self.sprite = self.walk_right[self.frame_index]
                else:
                    self.sprite = self.walk_left[self.frame_index]
            else:
                if dy > 0:
                    self.sprite = self.walk_down[self.frame_index]
                else:
                    self.sprite = self.walk_up[self.frame_index]
                    
            # Store current position for next frame
            self.last_x = self.x
            self.last_y = self.y
        elif self.state == "attack":
            self.sprite = self.attack_frames[self.frame_index]
        else:
            # Default to idle if state is unknown
            self.sprite = self.idle_frames[0]
            
        return self.sprite

    def collides_with_player(self, player):
        """Check if enemy collides with player."""
        enemy_rect = pygame.Rect(self.x, self.y, self.sprite_width, self.sprite_height)
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        return enemy_rect.colliderect(player_rect)

    def collides_with(self, projectile):
        """Check if enemy collides with a projectile."""
        # Create enemy rectangle
        enemy_rect = pygame.Rect(self.x, self.y, self.sprite_width, self.sprite_height)
        
        # Create projectile rectangle
        projectile_width = projectile.get("width", 5)
        projectile_height = projectile.get("height", 5)
        projectile_rect = pygame.Rect(
            projectile["x"], 
            projectile["y"], 
            projectile_width, 
            projectile_height
        )
        
        # Check collision
        if enemy_rect.colliderect(projectile_rect):
            # Take damage
            self.health -= 10
            
            # Play hit sound
            self.effects.play_hit_sound()
            
            # Return True if enemy is defeated
            return self.health <= 0
            
        return False

    def decrease_player_health(self, player):
        """Decrease the player's health incrementally."""
        if not hasattr(self, "last_health_decrease_time"):
            self.last_health_decrease_time = pygame.time.get_ticks()

        current_time = pygame.time.get_ticks()
        if current_time - self.last_health_decrease_time >= 1000:  # Decrease health every 1 second
            player.health -= 10  # Decrease player's health by 10
            if player.health < 0:
                player.health = 0  # Ensure health doesn't go below 0
            self.last_health_decrease_time = current_time

    def play_hit_sound(self):
        """Play the hit sound."""
        self.effects.play_hit_sound()
        # Play the hit sound if it exists
        #if self.hit_sound:
         #   self.hit_sound.play()

    def play_attack_sound(self):
        """Play the attack sound."""
        self.effects.play_attack_sound()
        # Play the attack sound if it exists
        #if self.attack_sound:
         #   self.attack_sound.play()


