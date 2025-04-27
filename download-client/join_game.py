import pygame
import sys
import json
import requests
import asyncio
import os
from game import Game, WIDTH, HEIGHT

# Initialize Pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BLUE = (10, 10, 25)
NEON_BLUE = (0, 195, 255)
NEON_PINK = (255, 41, 117)
GRAY = (100, 100, 100)

# Load fonts
try:
    font_lg = pygame.font.Font("fonts/cyberpunk.ttf", 48)
    font_md = pygame.font.Font("fonts/cyberpunk.ttf", 32)
    font_sm = pygame.font.Font("fonts/cyberpunk.ttf", 24)
except:
    print("Warning: Could not load cyberpunk font, using system font")
    font_lg = pygame.font.Font(None, 48)
    font_md = pygame.font.Font(None, 32)
    font_sm = pygame.font.Font(None, 24)

class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False
        
    def draw(self, surface):
        # Colors
        base_color = NEON_BLUE
        hover_color = NEON_PINK
        text_color = WHITE
        
        # Draw button background
        color = hover_color if self.hovered else base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)  # Border
        
        # Draw text
        text_surf = font_sm.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def update(self, mouse_pos):
        # Update hover state
        self.hovered = self.rect.collidepoint(mouse_pos)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.callback()
                return True
        return False

class GameList:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.active_games = []
        self.selected_game = None
        self.scroll_offset = 0
        self.max_visible_items = 5
        
    def update(self, server_url):
        """Fetch active games from server"""
        try:
            response = requests.get(f"{server_url}/active_games")
            if response.status_code == 200:
                self.active_games = response.json().get("games", [])
            else:
                print(f"Failed to get active games: {response.status_code}")
        except Exception as e:
            print(f"Error fetching active games: {e}")
    
    def draw(self, surface):
        # Draw background
        pygame.draw.rect(surface, DARK_BLUE, self.rect)
        pygame.draw.rect(surface, NEON_BLUE, self.rect, 2)
        
        # Draw title
        title = font_md.render("ACTIVE GAMES", True, WHITE)
        surface.blit(title, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw separator
        pygame.draw.line(surface, NEON_BLUE, 
                        (self.rect.x + 10, self.rect.y + 50),
                        (self.rect.x + self.rect.width - 10, self.rect.y + 50), 2)
        
        # Draw games list
        if not self.active_games:
            no_games = font_sm.render("No active games found", True, WHITE)
            surface.blit(no_games, (self.rect.x + 20, self.rect.y + 70))
        else:
            for i, game in enumerate(self.active_games[self.scroll_offset:self.scroll_offset + self.max_visible_items]):
                y_pos = self.rect.y + 70 + (i * 40)
                
                # Draw selection highlight
                if self.selected_game == game:
                    pygame.draw.rect(surface, NEON_PINK, 
                                    pygame.Rect(self.rect.x + 5, y_pos - 5, self.rect.width - 10, 40),
                                    border_radius=5)
                
                # Draw game info
                host = game.get("host", "Unknown")
                players = game.get("player_count", 0)
                text = f"{host}'s Game  ({players} players)"
                game_text = font_sm.render(text, True, WHITE)
                surface.blit(game_text, (self.rect.x + 20, y_pos))
    
    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos):
                # Check if clicked on a game entry
                for i, game in enumerate(self.active_games[self.scroll_offset:self.scroll_offset + self.max_visible_items]):
                    y_pos = self.rect.y + 70 + (i * 40)
                    if self.rect.y + 70 <= mouse_pos[1] <= y_pos + 30:
                        self.selected_game = game
                        return True
                
                # Scroll handling
                if event.button == 4:  # Scroll up
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                elif event.button == 5:  # Scroll down
                    max_offset = max(0, len(self.active_games) - self.max_visible_items)
                    self.scroll_offset = min(max_offset, self.scroll_offset + 1)
        
        return False

async def join_game_screen():
    """Display the join game screen"""
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CodeBreak - Join Game")
    
    # Load server URL from configuration
    try:
        with open("server_config.json", "r") as f:
            config = json.load(f)
            server_url = config.get("server_url", "http://3.130.249.194:8000")
    except (FileNotFoundError, json.JSONDecodeError):
        server_url = "http://3.130.249.194:8000"  # Default fallback
    
    # Check auth token
    auth_data = None
    try:
        with open("auth_token.json", "r") as f:
            auth_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No auth token found. Please login first.")
        import subprocess
        subprocess.Popen([sys.executable, "login.py"])
        pygame.quit()
        sys.exit()
    
    username = auth_data.get("username", "Player")
    
    # Create UI elements
    game_list = GameList(WIDTH // 2 - 200, 150, 400, 300)
    
    # Create buttons
    new_game_btn = Button(WIDTH // 2 - 200, 480, 180, 50, "NEW GAME", 
                         lambda: start_new_game(server_url, auth_data))
    
    join_game_btn = Button(WIDTH // 2 + 20, 480, 180, 50, "JOIN GAME", 
                          lambda: join_selected_game(game_list.selected_game, server_url, auth_data))
    
    refresh_btn = Button(WIDTH // 2 - 60, 550, 120, 40, "REFRESH", 
                        lambda: game_list.update(server_url))
    
    back_btn = Button(20, 20, 100, 40, "BACK", 
                     lambda: show_login())
    
    # Status message
    status_message = ""
    status_color = WHITE
    
    # Initial game list update
    game_list.update(server_url)
    
    # Main loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # Background
        screen.fill(DARK_BLUE)
        
        # Draw grid lines effect
        for i in range(0, WIDTH, 40):
            pygame.draw.line(screen, (30, 30, 50), (i, 0), (i, HEIGHT), 1)
        for i in range(0, HEIGHT, 40):
            pygame.draw.line(screen, (30, 30, 50), (0, i), (WIDTH, i), 1)
        
        # Draw title
        title = font_lg.render("CODEBREAK", True, NEON_BLUE)
        title_shadow = font_lg.render("CODEBREAK", True, NEON_PINK)
        screen.blit(title_shadow, (WIDTH // 2 - title_shadow.get_width() // 2 + 3, 50 + 3))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Draw logged in as
        logged_in_text = font_sm.render(f"Logged in as: {username}", True, WHITE)
        screen.blit(logged_in_text, (WIDTH - logged_in_text.get_width() - 20, 20))
        
        # Draw game list
        game_list.draw(screen)
        
        # Update and draw buttons
        for btn in [new_game_btn, join_game_btn, refresh_btn, back_btn]:
            btn.update(mouse_pos)
            btn.draw(screen)
        
        # Draw status message
        if status_message:
            status_text = font_sm.render(status_message, True, status_color)
            screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, 600))
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle button events
            for btn in [new_game_btn, join_game_btn, refresh_btn, back_btn]:
                if btn.handle_event(event):
                    break
            
            # Handle game list events
            game_list.handle_event(event, mouse_pos)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

def start_new_game(server_url, auth_data):
    """Start a new game as host"""
    try:
        # Create a new game on the server
        headers = {"Authorization": f"Bearer {auth_data.get('token')}"}
        response = requests.post(f"{server_url}/create_game", headers=headers)
        
        if response.status_code == 200:
            game_data = response.json()
            game_id = game_data.get("game_id")
            
            # Save game ID to a file
            with open("current_game.json", "w") as f:
                json.dump({
                    "game_id": game_id,
                    "is_host": True
                }, f)
            
            # Start the game
            pygame.quit()
            import subprocess
            subprocess.Popen([sys.executable, "main.py"])
            sys.exit()
        else:
            print(f"Failed to create game: {response.text}")
            return False
    except Exception as e:
        print(f"Error creating game: {e}")
        return False

def join_selected_game(game_data, server_url, auth_data):
    """Join the selected game"""
    if not game_data:
        print("No game selected")
        return False
    
    try:
        game_id = game_data.get("game_id")
        
        # Join the game on the server
        headers = {"Authorization": f"Bearer {auth_data.get('token')}"}
        response = requests.post(f"{server_url}/join_game/{game_id}", headers=headers)
        
        if response.status_code == 200:
            # Save game ID to a file
            with open("current_game.json", "w") as f:
                json.dump({
                    "game_id": game_id,
                    "is_host": False
                }, f)
            
            # Start the game
            pygame.quit()
            import subprocess
            subprocess.Popen([sys.executable, "main.py"])
            sys.exit()
        else:
            print(f"Failed to join game: {response.text}")
            return False
    except Exception as e:
        print(f"Error joining game: {e}")
        return False

def show_login():
    """Go back to login screen"""
    pygame.quit()
    import subprocess
    subprocess.Popen([sys.executable, "login.py"])
    sys.exit()

if __name__ == "__main__":
    asyncio.run(join_game_screen()) 