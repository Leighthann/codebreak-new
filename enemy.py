import pygame
import random
import json
import asyncio
import websockets
from typing import Dict
from effects import GameEffects

class Enemy:
    def __init__(self, sprite_sheet, x, y, server_url):
        self.x = x
        self.y = y
        self.speed = 2
        self.health = 50
        self.max_health = 50
        self.damage = 10
        self.chase_range = 300
        self.attack_range = 40
        self.state = "idle"
        
        # Sprite and animation
        self.sprite_width = 48
        self.sprite_height = 48
        self.frame_index = 0
        self.animation_speed = 10
        self.frame_counter = 0
        self.sprite = None

        self.server_url = server_url
        self.active = False  # Initialize the 'active' attribute
        self.effects = GameEffects()
        self.width = 48  # Set default width for the enemy
        self.height = 48  # Set default height for the enemy
        
        if sprite_sheet.get_width() >= self.sprite_width * 4 and sprite_sheet.get_height() >= self.sprite_height * 6:
            # Full spritesheet format (4x6)
            self.walk_right = [self.get_frame(sprite_sheet, i, 0) for i in range(4)]
            self.walk_left = [self.get_frame(sprite_sheet, i, 1) for i in range(4)]
            self.walk_up = [self.get_frame(sprite_sheet, i, 2) for i in range(4)]
            self.walk_down = [self.get_frame(sprite_sheet, i, 3) for i in range(4)]
            self.idle_frames = [self.get_frame(sprite_sheet, i, 4) for i in range(4)]
            self.attack_frames = [self.get_frame(sprite_sheet, i, 5) for i in range(4)]
        else:
            fallback = pygame.Surface((48, 48), pygame.SRCALPHA)
            fallback.fill((255, 0, 0))
            self.walk_right = [fallback] * 4
            self.walk_left = [fallback] * 4
            self.walk_up = [fallback] * 4
            self.walk_down = [fallback] * 4
            self.idle_frames = [fallback] * 4
            self.attack_frames = [fallback] * 4
        
        self.sprite = self.idle_frames[0]
        asyncio.create_task(self.listen_for_updates())

    def get_frame(self, sheet, frame, row):
        return sheet.subsurface(pygame.Rect(frame * 48, row * 48, 48, 48))

    async def listen_for_updates(self):
        async with websockets.connect(self.server_url) as websocket:
            while True:
                data = await websocket.recv()
                update = json.loads(data)
                if update["type"] == "enemy_update":
                    self.x, self.y, self.health = update["x"], update["y"], update["health"]
                elif update["type"] == "resource_collected":
                    self.handle_resource_collection(update)

    def handle_resource_collection(self, update):
        if update["resource_type"] == "health_potion":
            self.health = min(self.max_health, self.health + 10)

    async def update(self, player):
        if not player:
            return
        distance = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5
        if distance < self.attack_range:
            self.state = "attack"
            await self.attack_player(player)
        elif distance < self.chase_range:
            self.state = "chase"
            self.chase_player(player)
        else:
            self.state = "idle"

    def chase_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = max(0.1, ((dx ** 2) + (dy ** 2)) ** 0.5)
        dx = dx / distance * self.speed
        dy = dy / distance * self.speed
        self.x += dx
        self.y += dy
        asyncio.create_task(self.sync_enemy_state())

    async def sync_enemy_state(self):
        async with websockets.connect(self.server_url) as websocket:
            update_data = json.dumps({"type": "enemy_update", "x": self.x, "y": self.y, "health": self.health})
            await websocket.send(update_data)

    async def attack_player(self, player):
        if player.decrease_health(self.damage):
            self.effects.play_attack_sound()


    def collides_with_player(self, player):
        """Check if enemy collides with player."""
        enemy_rect = pygame.Rect(self.x, self.y, self.sprite_width, self.sprite_height)
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        return enemy_rect.colliderect(player_rect)

    def collides_with(self, projectile):
        """Check if enemy collides with a projectile."""
        """Check if this enemy collides with a projectile or other object"""
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

