# This module handles the game loop and manages the game state.
# It initializes the game, handles events, and updates the display.
# Manages game logic, screen updates, and events.
# game.py
import pygame
from player import Player
from enemy import Enemy

class Game:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 800, 600
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("CodeBreak - Survival")
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.BG_COLOR = (30, 30, 30)
        
        # Load player sprite sheet
        sprite_sheet = pygame.image.load("spritesheets/player-spritesheet.png")
        self.player = Player(sprite_sheet, self.WIDTH//2, self.HEIGHT//2)
        
        # Load enemy sprite
        enemy_sprite = pygame.image.load("spritesheets/enemy-spritesheet.png")  # Corrected file path
        self.enemies = [Enemy(enemy_sprite, 200, 200)]

    def run(self):
        running = True
        while running:
            self.screen.fill(self.BG_COLOR)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            keys = pygame.key.get_pressed()
            moving = self.player.move(keys)
            player_sprite = self.player.animate(moving, keys, self.enemies)  # Pass self.enemies
            self.screen.blit(player_sprite, (self.player.x, self.player.y))
            
            # Update and draw enemies
            for enemy in self.enemies:
                enemy.update(self.player)
                self.screen.blit(enemy.image, (enemy.x, enemy.y))
                
                # Check for projectile collisions
                for projectile in self.player.projectiles[:]:
                    if enemy.collides_with(projectile):
                        enemy.health -= 10
                        self.player.projectiles.remove(projectile)
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
            
            pygame.display.flip()
            self.clock.tick(self.FPS)
        pygame.quit()

