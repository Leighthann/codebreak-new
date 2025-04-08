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
        self.sprite = None
        self.server_url = server_url
        self.active = False  # Initialize the 'active' attribute
        self.effects = GameEffects()
        self.width = 48  # Set default width for the enemy
        self.height = 48  # Set default height for the enemy
        
        if sprite_sheet.get_width() >= 192 and sprite_sheet.get_height() >= 288:
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

    def collides_with(self, projectile):
        """Check if this enemy collides with a projectile or other object"""
        # Simple rectangular collision detection
        enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # If projectile is a dictionary (as in the Player class)
        if isinstance(projectile, dict):
            # Assume projectile has x, y coordinates and is circular with radius 5
            projectile_x = projectile.get("x", 0)
            projectile_y = projectile.get("y", 0)
            projectile_radius = 5  # Default radius for projectiles
            
            # Check if the projectile's center is inside the enemy's rectangle
            # or if it's close enough to the edges (within radius distance)
            if (projectile_x >= self.x - projectile_radius and 
                projectile_x <= self.x + self.width + projectile_radius and
                projectile_y >= self.y - projectile_radius and
                projectile_y <= self.y + self.height + projectile_radius):
                return True
                
        # If projectile is another game object with x, y, width, height
        elif hasattr(projectile, 'x') and hasattr(projectile, 'y'):
            if hasattr(projectile, 'width') and hasattr(projectile, 'height'):
                projectile_rect = pygame.Rect(projectile.x, projectile.y, 
                                           projectile.width, projectile.height)
                return enemy_rect.colliderect(projectile_rect)
            
        return False
