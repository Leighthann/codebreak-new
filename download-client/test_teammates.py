import os
import sys
import json
import asyncio
import pygame
import time
import math
import random

# Import game components
from game import Game, WIDTH, HEIGHT, NEON_BLUE, NEON_GREEN, WHITE

class TeammateTest:
    def __init__(self):
        self.games = []
        self.test_resources_spawned = False
        self.screens = []
        
    async def setup_test_players(self):
        """Create test player configurations"""
        # Test player configurations
        players = [
            {"username": "Player1", "password": "test123"},
            {"username": "Player2", "password": "test123"}
        ]
        
        # Initialize pygame first
        pygame.init()
        
        for i, player in enumerate(players):
            config = {
                "server_url": "http://3.130.249.194:8000",
                "username": player["username"],
                "password": player["password"]
            }
            
            # Create config file for this player
            config_file = f"client_config_{i+1}.json"
            with open(config_file, "w") as f:
                json.dump(config, f)
            
            print(f"Created configuration for {player['username']}")
            
            # Create window for this player
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption(f"CodeBreak - {player['username']}")
            self.screens.append(screen)
            
            # Create and initialize game instance
            game = Game()
            game.screen = screen  # Set the screen for this game instance
            await game.initialize_game_world()  # Initialize the game world
            self.games.append(game)
            
            # Create a new display for the second window
            if i == 0:
                # Create a second window by changing the display mode
                pygame.display.set_mode((WIDTH, HEIGHT))
    
    async def run_test(self):
        """Run the teammate and resource sharing test"""
        print("\n=== CodeBreak Teammate Test ===")
        print("This test will launch two game instances to test:")
        print("1. Teammate visibility")
        print("2. Resource sharing")
        print("\nControls:")
        print("R - Spawn test resources")
        print("T - Send chat message")
        print("ESC - Exit test")
        print("\nWaiting for game instances to initialize...\n")
        
        await self.setup_test_players()
        
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        # Spawn test resources around Player 1
                        if len(self.games) > 0 and self.games[0].player:
                            await self.spawn_test_resources(self.games[0])
                    elif event.key == pygame.K_t:
                        # Test chat message
                        for game in self.games:
                            if game.chat_system:
                                game.chat_system.toggle_chat()
            
            # Update and render each game instance
            for i, (game, screen) in enumerate(zip(self.games, self.screens)):
                if game.player:
                    # Set the current screen for this game
                    pygame.display.set_mode((WIDTH, HEIGHT))
                    game.screen = screen
                    
                    # Update game state
                    await game.handle_gameplay([], 1/60)
                    
                    # Clear the screen
                    screen.fill((0, 0, 0))
                    
                    # Draw game
                    game.draw_gameplay_elements()
                    
                    # Draw debug info
                    self.draw_debug_overlay(game)
                    
                    # Update display for this window
                    pygame.display.flip()
            
            # Cap framerate
            clock.tick(60)
        
        # Cleanup
        pygame.quit()
        
    async def spawn_test_resources(self, game):
        """Spawn test resources around the specified player"""
        if not game.player:
            return
            
        print("Spawning test resources...")
        
        # Spawn different resource types in a circle
        resource_types = ["code_fragments", "energy_cores", "data_shards"]
        count = 8
        radius = 100
        
        for i in range(count):
            angle = 2 * 3.14159 * i / count
            x = game.player.x + radius * math.cos(angle)
            y = game.player.y + radius * math.sin(angle)
            
            resource_type = resource_types[i % len(resource_types)]
            
            # Spawn resource
            game.spawn_resource_at(
                x, y,
                resource_type=resource_type,
                amount=5 if resource_type == "data_shards" else 10
            )
            
            # Add visual indicator
            game.add_effect("text", x, y - 20,
                          text=f"Test {resource_type}",
                          color=NEON_BLUE,
                          size=14,
                          duration=3.0)
        
        print(f"Spawned {count} test resources around player")
    
    def draw_debug_overlay(self, game):
        """Draw debug information overlay"""
        if not game.screen or not game.player:
            return
            
        # Create debug surface
        debug_surf = pygame.Surface((200, HEIGHT), pygame.SRCALPHA)
        debug_surf.fill((0, 0, 0, 100))
        
        # Draw connection status
        status_text = f"Server: {'Connected' if game.connected_to_server else 'Disconnected'}"
        status_color = NEON_GREEN if game.connected_to_server else (255, 0, 0)
        status_surf = game.font_sm.render(status_text, True, status_color)
        debug_surf.blit(status_surf, (10, 10))
        
        # Draw teammate info
        y = 40
        for username, player_data in game.other_players.items():
            player_text = f"{username}"
            color = NEON_GREEN if player_data.get("has_shared", False) else WHITE
            text_surf = game.font_sm.render(player_text, True, color)
            debug_surf.blit(text_surf, (10, y))
            y += 20
        
        # Draw inventory
        y += 20
        inventory_text = game.font_sm.render("Inventory:", True, WHITE)
        debug_surf.blit(inventory_text, (10, y))
        y += 20
        
        for resource, amount in game.player.inventory.items():
            text = f"{resource}: {amount}"
            text_surf = game.font_sm.render(text, True, WHITE)
            debug_surf.blit(text_surf, (20, y))
            y += 20
        
        # Blit debug overlay
        game.screen.blit(debug_surf, (WIDTH - 210, 10))

if __name__ == "__main__":
    # Run the test
    test = TeammateTest()
    asyncio.run(test.run_test())