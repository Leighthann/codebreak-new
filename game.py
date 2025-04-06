# game.py
import pygame
import sys
from player import Player
from enemy import Enemy
from effects import GameEffects
from world import WorldGenerator
from worldObject import WorldObjects

pygame.init()

# Game window settings
WIDTH, HEIGHT = 800, 600
BG_COLOR = (30, 30, 30)

# Fonts for buttons
font = pygame.font.Font(None, 50)

class Button:
    def __init__(self, text, x, y, width, height, action=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 255), self.rect)
        label = font.render(self.text, True, (255, 255, 255))
        screen.blit(label, (self.rect.x + (self.rect.width - label.get_width()) // 2,
                            self.rect.y + (self.rect.height - label.get_height()) // 2))

    def is_hovered(self):
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)
        print(f"Mouse position: {mouse_pos}, Button '{self.text}' rect: {self.rect}, Hovered: {hovered}")  # Debug: Log hover state
        return hovered

    def handle_event(self, event):
        """Handle mouse click events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            print(f"Mouse clicked at {pygame.mouse.get_pos()}")  # Debug: Log mouse click position
            if self.is_hovered():
                print(f"Button '{self.text}' clicked!")  # Debug: Log button click
                if self.action:
                    print(f"Executing action for button '{self.text}'")  # Debug: Log action execution
                    self.action()
                    return True  # Indicate that the action was executed
        return False

class Menu:
    def __init__(self, game):
        self.game = game
        self.buttons = [
            Button("Play", 300, 200, 200, 50, self.play),
            Button("Leaderboard", 300, 300, 200, 50, self.show_leaderboard),
            Button("Exit", 300, 400, 200, 50, self.exit_game)
        ]

    def draw(self, screen):
        screen.fill((255, 255, 255))  # White background for the menu
        for button in self.buttons:
            button.draw(screen)

    def handle_events(self, events):
        for event in events:
            print(f"Menu processing event: {event}")  # Debug: Log events being processed by menu
            if event.type == pygame.QUIT:
                self.exit_game()
            for button in self.buttons:
                if button.handle_event(event):
                    return  # Stop processing if a button action was executed

    def play(self):
        print("Starting the game...")
        self.game.game_state = "play"

    def show_leaderboard(self):
        print("Showing leaderboard...")
        self.game.game_state = "leaderboard"

    def exit_game(self):
        print("Exiting game...")
        pygame.quit()
        sys.exit()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("CodeBreak - Survival")
        self.clock = pygame.time.Clock()
        self.FPS = 60

        # Create the world generator and objects
        self.world_generator = WorldGenerator()
        self.world_objects = WorldObjects()
        self.world_objects.generate_objects(self.world_generator.world_map)

        # Load player sprite sheet
        sprite_sheet = pygame.image.load("spritesheets/player-spritesheet.png")
        self.player = Player(sprite_sheet, WIDTH // 2, HEIGHT // 2)

        # Load enemy sprite
        enemy_sprite = pygame.image.load("spritesheets/enemy-spritesheet.png")
        self.enemies = [Enemy(enemy_sprite, 200, 200)]

        self.effects = GameEffects()

        self.menu = Menu(self)  # Pass the Game instance to the Menu
        self.game_state = "menu"  # Start with the menu state

    def run(self):
        """Main game loop."""
        running = True
        while running:
            # Collect events once per frame
            events = pygame.event.get()
            
            # Process quit events at the top level
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()

            # Clear the screen
            self.screen.fill((255, 255, 255))

            # Handle the current game state
            if self.game_state == "menu":
                self.menu.handle_events(events)  # Pass the collected events to the menu
                self.menu.draw(self.screen)
            elif self.game_state == "play":
                self.handle_gameplay(events)
            elif self.game_state == "leaderboard":
                # Future leaderboard implementation
                self.draw_leaderboard()
                # Add a way to go back to the menu
                for event in events:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.game_state = "menu"

            pygame.display.flip()  # Update the screen after all drawing and event handling
            self.clock.tick(self.FPS)

    def handle_gameplay(self, events):
        """Handle the gameplay state."""
        # Process gameplay-specific events
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_state = "menu"  # Return to the menu when escape is pressed
                return

        # Handle player movement
        keys = pygame.key.get_pressed()
        moving = self.player.move(keys)
        player_sprite = self.player.animate(moving, keys, self.enemies)

        # Draw game elements
        self.screen.fill(BG_COLOR)
        self.screen.blit(player_sprite, (self.player.x, self.player.y))

        # Draw player health bar
        self.effects.draw_health_bar(self.screen, 10, 10, 200, 20, self.player.health, self.player.max_health)

        # Update and draw enemies
        for enemy in self.enemies:
            enemy.update(self.player)
            enemy_sprite = enemy.animate()
            if enemy_sprite:  # Ensure enemy_sprite is not None
                self.screen.blit(enemy_sprite, (enemy.x, enemy.y))
                self.effects.draw_health_bar(self.screen, enemy.x, enemy.y - 10, 50, 5, enemy.health, enemy.max_health)
            else:
                print(f"Warning: Enemy animation returned None for enemy at ({enemy.x}, {enemy.y})")  # Debug: Log missing sprite

        # Handle projectiles
        for projectile in self.player.projectiles[:]:
            pygame.draw.circle(self.screen, (255, 255, 255), (projectile["x"], projectile["y"]), 5)
            for enemy in self.enemies[:]:
                if enemy.collides_with(projectile):
                    self.player.projectiles.remove(projectile)  # Remove projectile on collision
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)  # Remove enemy only when health is depleted

    def draw_leaderboard(self):
        """Draw the leaderboard screen."""
        self.screen.fill((0, 0, 0))  # Black background for leaderboard
        title = font.render("Leaderboard", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Add placeholder text
        instructions = pygame.font.Font(None, 30).render("Press ESC to return to menu", True, (255, 255, 255))
        self.screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 50))

# This ensures the Game class is only instantiated when the script is run directly
if __name__ == "__main__":
    game = Game()
    game.run()