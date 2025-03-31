import pygame
import random

class Enemy:
    def __init__(self, sprite_sheet, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.health = 100
        self.sprite_width, self.sprite_height = 48, 48
        self.frame_index = 0
        self.animation_speed = 10
        self.frame_counter = 0
        self.state = "idle"  # Can be "idle", "chase", "attack"

        # Extract animation frames
        self.idle_frames = [self.get_frame(sprite_sheet, i, 0) for i in range(4)]
        self.walk_frames = [self.get_frame(sprite_sheet, i, 1) for i in range(4)]
        self.attack_frames = [self.get_frame(sprite_sheet, i, 2) for i in range(4)]
        self.image = self.idle_frames[0]

    def get_frame(self, sheet, frame, row):
        """Extract a single frame from a sprite sheet."""
        return sheet.subsurface(pygame.Rect(frame * self.sprite_width, row * self.sprite_height, self.sprite_width, self.sprite_height))

    def update(self, player):
        """Update enemy behavior."""
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
        """Update animation frames."""
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


    def collides_with(self, projectile):
        """Check for collision with a projectile."""
        enemy_rect = pygame.Rect(self.x, self.y, self.sprite_width, self.sprite_height)

        # Use default width and height if not provided
        projectile_width = projectile.get("width", 5)  # Default width is 5
        projectile_height = projectile.get("height", 5)  # Default height is 5

        return enemy_rect.colliderect(pygame.Rect(
            projectile["x"], projectile["y"], projectile_width, projectile_height
        ))


