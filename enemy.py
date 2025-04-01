import pygame
import random
from typing import Dict  # Import for type annotations
from effects import GameEffects  # Import GameEffects

class Enemy:
    def __init__(self, sprite_sheet, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.health = 200  # Increase health to 200
        self.max_health = 200  # Increase max health to 200
        self.sprite_width, self.sprite_height = 48, 48
        self.frame_index = 0
        self.animation_speed = 10
        self.frame_counter = 0
        self.state = "idle"  # Can be "idle", "chase", "attack"
        self.effects = GameEffects()  # Initialize GameEffects

        # Extract animation frames
        self.idle_frames = [self.get_frame(sprite_sheet, i, 0) for i in range(4)]
        self.walk_frames = [self.get_frame(sprite_sheet, i, 1) for i in range(4)]
        self.attack_frames = [self.get_frame(sprite_sheet, i, 2) for i in range(4)]
        self.image = self.idle_frames[0]

       
       # self.hit_sound = pygame.mixer.Sound("sound_effects/sword.wav")  # Load hit sound

    def get_frame(self, sheet, frame, row):
        """Extract a single frame from a sprite sheet."""
        return sheet.subsurface(pygame.Rect(frame * self.sprite_width, row * self.sprite_height, self.sprite_width, self.sprite_height))

    def update(self, player):
        """Update enemy behavior."""
        # Check for collision with the player
        if self.collides_with_player(player):
            self.decrease_player_health(player)

        distance = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5
        if distance < 150:
            self.state = "chase"
            if distance < 40:
                self.state = "attack"
        else:
            self.state = "idle"
        
        if self.state == "chase":
            self.chase_player(player)
        elif self.state == "attack":
            self.attack()

        # Animate
        self.animate()

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

    def collides_with_player(self, player) -> bool:
        """Check for collision with the player.

        Args:
            player: The player object with x, y, width, and height attributes.

        Returns:
            bool: True if the enemy collides with the player, False otherwise.
        """
        enemy_rect = pygame.Rect(self.x, self.y, self.sprite_width, self.sprite_height)
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        return enemy_rect.colliderect(player_rect)

    def chase_player(self, player):
        """Move towards the player."""
        if self.x < player.x:
            self.x += self.speed
        elif self.x > player.x:
            self.x -= self.speed
        if self.y < player.y:
            self.y += self.speed
        elif self.y > player.y:
            self.y -= self.speed

    def attack(self):
        """Attack behavior."""
        pass  # Implement attack logic

    def animate(self):
        """Update animation frames and return the current sprite."""
        self.frame_counter += 1
        if self.frame_counter >= self.animation_speed:
            self.frame_counter = 0
            self.frame_index = (self.frame_index + 1) % 4

        if self.state == "idle":
            self.image = self.idle_frames[self.frame_index]
        elif self.state == "chase":
            self.image = self.walk_frames[self.frame_index]
        elif self.state == "attack":
            self.image = self.attack_frames[self.frame_index]
        else:
            print(f"Warning: Unknown state '{self.state}' for enemy at ({self.x}, {self.y})")  # Debug: Log unknown state
            self.image = self.idle_frames[0]  # Default to idle frame

        return self.image  # Ensure a valid sprite is always returned

    def collides_with(self, projectile: Dict[str, int]) -> bool:
        """Check for collision with a projectile.

        Args:
            projectile (Dict[str, int]): A dictionary containing the projectile's x, y, width, and height.

        Returns:
            bool: True if the enemy collides with the projectile, False otherwise.
        """
        enemy_rect = pygame.Rect(self.x, self.y, self.sprite_width, self.sprite_height)

        # Use default width and height if not provided
        projectile_width = projectile.get("width", 5)  # Default width is 5
        projectile_height = projectile.get("height", 5)  # Default height is 5

        collision = enemy_rect.colliderect(pygame.Rect(
            projectile["x"], projectile["y"], projectile_width, projectile_height
        ))

        if collision:
            self.health -= 10  # Decrease health by 10 on collision
            print(f"Enemy at ({self.x}, {self.y}) health: {self.health}")  # Debug: Log health
            self.effects.play_hit_sound()  # Play hit sound
            if self.health <= 0:
                return True  # Indicate that the enemy should be removed
        return False

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


