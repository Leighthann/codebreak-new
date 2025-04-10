import pygame
import random
import json
import asyncio
import websockets
import math
from typing import Dict
from effects import GameEffects

class Enemy:
    def __init__(self, sprite_sheet, x, y, server_url):
        self.x = x
        self.y = y
        self.speed = 3
        self.health = 50
        self.max_health = 50
        self.damage = 10
        self.chase_range = 1000
        self.attack_range = 40
        self.state = "idle"
        self.direction = "down"  # Initialize direction attribute
        
        # Sprite and animation
        self.sprite_width = 48
        self.sprite_height = 48
        self.frame_index = 0
        self.animation_speed = 10
        self.frame_counter = 0
        
        # Initialize sprite variables
        self.walk_right = []
        self.walk_left = []
        self.walk_up = []
        self.walk_down = []
        self.idle_frames = []
        self.attack_frames = []
        
        self.server_url = server_url
        self.active = True  # Set active to True by default
        self.effects = GameEffects()
        self.width = 48  # Set default width for the enemy
        self.height = 48  # Set default height for the enemy
        
        # Load sprites
       
        if sprite_sheet.get_width() >= self.sprite_width * 4 and sprite_sheet.get_height() >= self.sprite_height * 6:
                # Full spritesheet format (4x6)
                self.walk_right = [self.get_frame(sprite_sheet, i, 0) for i in range(4)]
                self.walk_left = [self.get_frame(sprite_sheet, i, 1) for i in range(4)]
                self.walk_up = [self.get_frame(sprite_sheet, i, 2) for i in range(4)]
                self.walk_down = [self.get_frame(sprite_sheet, i, 3) for i in range(4)]
                self.idle_frames = [self.get_frame(sprite_sheet, i, 4) for i in range(4)]
                self.attack_frames = [self.get_frame(sprite_sheet, i, 5) for i in range(4)]
        else:
                # Create a fallback sprite
                fallback = pygame.Surface((48, 48), pygame.SRCALPHA)
                fallback.fill((255, 0, 0))  # Red color for visibility
                pygame.draw.rect(fallback, (255, 255, 255), fallback.get_rect(), 2)  # White border
                self.walk_right = [fallback] * 4
                self.walk_left = [fallback] * 4
                self.walk_up = [fallback] * 4
                self.walk_down = [fallback] * 4
                self.idle_frames = [fallback] * 4
                self.attack_frames = [fallback] * 4
       
        
        # Set initial sprite
        self.sprite = self.idle_frames[0] if self.idle_frames else None
        
        # Don't start websocket connection immediately
        self.ws = None

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
        """Update enemy state and animation."""
        if not player or not self.active:
            return

        # Calculate distance to player
        #dx = player.x - self.x
        #dy = player.y - self.y
        #distance = math.sqrt(dx*dx + dy*dy)
         # Calculate distance to player
        distance = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5

        # Debug print - uncomment if needed to troubleshoot
        print(f"Enemy state: {self.state}, distance: {distance}, chase range: {self.chase_range}, player position: ({player.x}, {player.y}), enemy position: ({self.x}, {self.y})")

        # Update state based on distance
        if distance < self.attack_range:
            self.state = "attack"
            await self.attack_player(player)
        elif distance < self.chase_range:
            self.state = "chase"
            # Use the chase_player method to update position
            self.chase_player(player)
        else:
            self.state = "idle"

        # Update animation only if sprite exists
        '''
        if self.sprite:
            self.frame_counter += 1
            if self.frame_counter >= self.animation_speed:
                self.frame_counter = 0
                self.frame_index = (self.frame_index + 1) % 4

            # Set sprite based on state and direction
            if self.state == "attack" and self.attack_frames:
                self.sprite = self.attack_frames[self.frame_index % len(self.attack_frames)]
            elif self.state == "chase":
                if self.direction == "right" and self.walk_right:
                    self.sprite = self.walk_right[self.frame_index % len(self.walk_right)]
                elif self.direction == "left" and self.walk_left:
                    self.sprite = self.walk_left[self.frame_index % len(self.walk_left)]
                elif self.direction == "up" and self.walk_up:
                    self.sprite = self.walk_up[self.frame_index % len(self.walk_up)]
                elif self.direction == "down" and self.walk_down:
                    self.sprite = self.walk_down[self.frame_index % len(self.walk_down)]
            elif self.idle_frames:
                self.sprite = self.idle_frames[self.frame_index % len(self.idle_frames)]
            '''

    def chase_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = max(0.1, ((dx ** 2) + (dy ** 2)) ** 0.5)
        dx = dx / distance * self.speed
        dy = dy / distance * self.speed
        
        # Debug print to confirm speed and movement
        print(f"Chasing player: speed={self.speed}, moving by dx={dx}, dy={dy}")
        
        self.x += dx
        self.y += dy
        
        '''
        # Update direction for animation
        if abs(dx) > abs(dy):
            if dx > 0:
                self.direction = "right"
            else:
                self.direction = "left"
        else:
            if dy > 0:
                self.direction = "down"
            else:
                self.direction = "up"
        '''
                
        # Don't wait for server sync - create task and continue
        try:
            asyncio.create_task(self.sync_enemy_state())
        except RuntimeError:
            # Ignore runtime errors related to event loop
            pass

    async def sync_enemy_state(self):
        """Synchronize enemy state to server - safely handle connection issues."""
        try:
            async with websockets.connect(self.server_url, timeout=1) as websocket:
                update_data = json.dumps({"type": "enemy_update", "x": self.x, "y": self.y, "health": self.health})
                await websocket.send(update_data)
        except (websockets.exceptions.WebSocketException, ConnectionRefusedError, asyncio.TimeoutError):
            # Silently fail if server connection fails - don't block the chase behavior
            pass

    async def attack_player(self, player):
        """Attack the player and deal damage."""
        try:
            current_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds
            # Check if player has the decrease_health method
            if hasattr(player, 'decrease_health') and callable(getattr(player, 'decrease_health')):
                damage_result = player.decrease_health(self.damage)
                # Handle if it's a coroutine
                if asyncio.iscoroutine(damage_result):
                    damage_result = await damage_result
                
                if damage_result:
                    self.effects.play_attack_sound()
            else:
                # Fallback - directly decrease health
                player.health = max(0, player.health - self.damage)
                self.effects.play_attack_sound()
        except Exception as e:
            print(f"Error in attack_player: {e}")
            # Don't let errors block enemy behavior

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

