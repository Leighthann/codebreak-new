import pygame
import sys
import json
import requests
import asyncio
import os
import subprocess
import webbrowser
import time
import pyperclip
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = ["pygame", "websockets", "requests", "python-dotenv", "pyperclip"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:", ", ".join(missing_packages))
        print("Running dependency installer...")
        
        # Run install_dependencies.py
        try:
            result = subprocess.run([sys.executable, "install_dependencies.py"], check=True)
            if result.returncode == 0:
                print("Dependencies installed successfully!")
                # Re-import pygame since we need it for the launcher
                import pygame
            else:
                print("Failed to install dependencies. Please run install_dependencies.py manually.")
                sys.exit(1)
        except subprocess.CalledProcessError as e:
            print("Error running dependency installer:", str(e))
            sys.exit(1)
        except Exception as e:
            print("Unexpected error:", str(e))
            sys.exit(1)

# Check dependencies before initializing pygame
check_dependencies()

# Initialize Pygame
pygame.init()

# Game dimensions
WIDTH, HEIGHT = 1024, 768
BUTTON_WIDTH, BUTTON_HEIGHT = 250, 60

# Window states - add extra height for title bar
WINDOWED_SIZE = (WIDTH + 16, HEIGHT + 39)  # Add padding for window borders and title bar
is_fullscreen = False

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BLUE = (10, 10, 25)
NEON_BLUE = (0, 195, 255)
NEON_PINK = (255, 41, 117)
GRAY = (100, 100, 100)
LIGHT_GRAY = (150, 150, 150)
GREEN = (0, 255, 0)

# Server URL and auth file paths
CONFIG_FILE = "client_config.json"
GAME_FILE = "current_game.json"  # Used to track current game session

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
    def __init__(self, x, y, width, height, text, callback, disabled=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False
        self.disabled = disabled
        
    def draw(self, surface):
        # Colors
        base_color = LIGHT_GRAY if self.disabled else NEON_BLUE
        hover_color = LIGHT_GRAY if self.disabled else NEON_PINK
        text_color = GRAY if self.disabled else WHITE
        
        # Draw button background
        color = hover_color if self.hovered and not self.disabled else base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)  # Border
        
        # Draw text
        text_surf = font_sm.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def update(self, mouse_pos):
        # Update hover state
        self.hovered = self.rect.collidepoint(mouse_pos) and not self.disabled
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and not self.disabled:
                self.callback()
                return True
        return False

class GameList:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.active_games = []
        self.selected_game = None
        self.scroll_offset = 0
        self.max_visible_items = 8
        self.status = "Loading..."
        
    def update(self, config_data):
        """Fetch active games from server"""
        try:
            headers = {"Authorization": f"Bearer {config_data.get('token')}"}
            server_url = config_data.get("server_url", "http://3.130.249.194:8000")
            response = requests.get(f"{server_url}/active_games", headers=headers)
            if response.status_code == 200:
                self.active_games = response.json().get("games", [])
                self.status = f"{len(self.active_games)} games available" if self.active_games else "No active games"
            else:
                self.status = f"Error: {response.status_code}"
        except Exception as e:
            self.status = f"Connection error: {str(e)}"
    
    def draw(self, surface):
        # Draw background
        pygame.draw.rect(surface, DARK_BLUE, self.rect)
        pygame.draw.rect(surface, NEON_BLUE, self.rect, 2)
        
        # Draw title
        title = font_md.render("ACTIVE GAMES", True, WHITE)
        surface.blit(title, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw status
        status_text = font_sm.render(self.status, True, GRAY)
        surface.blit(status_text, (self.rect.x + 10, self.rect.y + 50))
        
        # Draw separator
        pygame.draw.line(surface, NEON_BLUE, 
                        (self.rect.x + 10, self.rect.y + 75),
                        (self.rect.x + self.rect.width - 10, self.rect.y + 75), 2)
        
        # Draw games list
        if not self.active_games:
            no_games = font_sm.render("No active games found", True, WHITE)
            surface.blit(no_games, (self.rect.x + 20, self.rect.y + 100))
        else:
            for i, game in enumerate(self.active_games[self.scroll_offset:self.scroll_offset + self.max_visible_items]):
                y_pos = self.rect.y + 90 + (i * 40)
                
                # Draw selection highlight
                if self.selected_game == game:
                    pygame.draw.rect(surface, NEON_PINK, 
                                    pygame.Rect(self.rect.x + 5, y_pos - 5, self.rect.width - 10, 40),
                                    border_radius=5)
                
                # Draw game info
                host = game.get("host", "Unknown")
                players = game.get("player_count", 0)
                text = f"{host}'s Game ({players} players)"
                game_text = font_sm.render(text, True, WHITE)
                surface.blit(game_text, (self.rect.x + 20, y_pos))
    
    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos):
                # Check if clicked on a game entry
                for i, game in enumerate(self.active_games[self.scroll_offset:self.scroll_offset + self.max_visible_items]):
                    y_pos = self.rect.y + 90 + (i * 40)
                    game_rect = pygame.Rect(self.rect.x + 5, y_pos - 5, self.rect.width - 10, 40)
                    if game_rect.collidepoint(mouse_pos):
                        self.selected_game = game
                        return True
                
                # Scroll handling
                if event.button == 4:  # Scroll up
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                elif event.button == 5:  # Scroll down
                    max_offset = max(0, len(self.active_games) - self.max_visible_items)
                    self.scroll_offset = min(max_offset, self.scroll_offset + 1)
        
        return False

class PopupDialog:
    def __init__(self, title, game_id, screen, clock, width=600, height=250):
        self.width = width
        self.height = height
        self.title = title
        self.game_id = game_id
        self.screen = screen
        self.clock = clock
        self.rect = pygame.Rect(WIDTH//2 - width//2, HEIGHT//2 - height//2, width, height)
        self.copy_btn = Button(self.rect.x + width//2 - 100, self.rect.y + height - 60, 200, 40, "COPY ID", self.copy_to_clipboard)
        self.close_btn = Button(self.rect.x + width//2 - 100, self.rect.y + height - 110, 200, 40, "CLOSE", self.close)
        self.is_open = True
        self.copied = False
        self.copy_text = "COPY ID"
        
    def copy_to_clipboard(self):
        try:
            pyperclip.copy(self.game_id)
            self.copied = True
            self.copy_text = "COPIED!"
        except:
            self.copy_text = "COPY FAILED"
    
    def close(self):
        self.is_open = False
    
    def draw(self):
        # Draw semi-transparent background
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # Draw popup background
        pygame.draw.rect(self.screen, DARK_BLUE, self.rect)
        pygame.draw.rect(self.screen, NEON_BLUE, self.rect, 2)
        
        # Draw title
        title = font_md.render(self.title, True, WHITE)
        self.screen.blit(title, (self.rect.x + 20, self.rect.y + 20))
        
        # Draw Game ID on its own line
        id_label = font_sm.render("Game ID:", True, NEON_BLUE)
        self.screen.blit(id_label, (self.rect.x + 20, self.rect.y + 70))
        id_value = font_sm.render(self.game_id, True, WHITE)
        self.screen.blit(id_value, (self.rect.x + 120, self.rect.y + 70))
        
        # Draw instructions on a new line
        instructions = font_sm.render("Share this ID with other players to join your game.", True, NEON_BLUE)
        self.screen.blit(instructions, (self.rect.x + 20, self.rect.y + 120))
        
        # Draw buttons
        self.copy_btn.text = self.copy_text
        self.copy_btn.draw(self.screen)
        self.close_btn.draw(self.screen)
    
    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.copy_btn.update(mouse_pos)
            self.close_btn.update(mouse_pos)
            if self.copy_btn.handle_event(event):
                return True
            if self.close_btn.handle_event(event):
                return True
        return False
    
    def show(self):
        while self.is_open:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_event(event, mouse_pos)
            
            # Draw everything
            self.screen.fill(DARK_BLUE)
            
            # Draw grid lines effect
            for i in range(0, WIDTH, 40):
                pygame.draw.line(self.screen, (30, 30, 50), (i, 0), (i, HEIGHT), 1)
            for i in range(0, HEIGHT, 40):
                pygame.draw.line(self.screen, (30, 30, 50), (0, i), (WIDTH, i), 1)
            
            # Draw title
            title = font_lg.render("CODEBREAK", True, NEON_BLUE)
            title_shadow = font_lg.render("CODEBREAK", True, NEON_PINK)
            self.screen.blit(title_shadow, (WIDTH // 2 - title_shadow.get_width() // 2 + 3, 70 + 3))
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))
            
            # Draw popup
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(60)

def is_logged_in():
    """Check if a valid config with credentials exists"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return bool(config.get('token') and config.get('username'))
    except:
        pass
    return False

def open_login_page():
    """Open the login page in the default browser"""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            server_url = config.get("server_url", "http://3.130.249.194:8000")
    except:
        server_url = "http://3.130.249.194:8000"
    webbrowser.open(f"{server_url}/login")

def check_login_status():
    """Check if login was successful by polling for auth token file"""
    start_time = time.time()
    timeout = 300  # 5 minutes
    
    while time.time() - start_time < timeout:
        if is_logged_in():
            return True
        time.sleep(1)
    
    return False

def start_single_player(config_data):
    """Start a single player game"""
    try:
        # Save game state for solo play
        with open(GAME_FILE, "w") as f:
            json.dump({
                "is_host": True,
                "is_solo": True,
                "server_url": config_data.get("server_url", "http://3.130.249.194:8000"),
                "token": config_data.get("token"),
                "username": config_data.get("username")
            }, f)
        
        # Start the game
        pygame.quit()
        # Use the correct path to main.py
        subprocess.Popen([sys.executable, "main.py"])
        sys.exit()
    except Exception as e:
        return f"Error starting solo game: {str(e)}"

def join_multiplayer_game(game_data, config_data):
    """Join the selected multiplayer game"""
    if not game_data:
        return "No game selected"
    
    try:
        game_id = game_data.get("game_id")
        server_url = config_data.get("server_url", "http://3.130.249.194:8000")
        
        # Join the game on the server
        headers = {"Authorization": f"Bearer {config_data.get('token')}"}
        response = requests.post(f"{server_url}/join_game/{game_id}", headers=headers)
        
        if response.status_code == 200:
            # Save game ID to track the current session
            with open(GAME_FILE, "w") as f:
                json.dump({
                    "game_id": game_id,
                    "is_host": False,
                    "is_solo": False,
                    "server_url": server_url,
                    "token": config_data.get("token"),
                    "username": config_data.get("username")
                }, f)
            
            # Start the game
            pygame.quit()
            # Use the correct path to main.py
            subprocess.Popen([sys.executable, "main.py"])
            sys.exit()
        else:
            error_message = response.text if response.text else f"Server error: {response.status_code}"
            return f"Failed to join game: {error_message}"
    except Exception as e:
        return f"Error: {str(e)}"

def create_multiplayer_game(config_data, screen, clock):
    """Create a new multiplayer game"""
    try:
        # Create a new game on the server
        headers = {"Authorization": f"Bearer {config_data.get('token')}"}
        server_url = config_data.get("server_url", "http://3.130.249.194:8000")
        response = requests.post(f"{server_url}/create_game", headers=headers)
        
        if response.status_code == 200:
            game_data = response.json()
            game_id = game_data.get("game_id")
            
            # Save game ID to track the current session
            with open(GAME_FILE, "w") as f:
                json.dump({
                    "game_id": game_id,
                    "is_host": True,
                    "is_solo": False,
                    "server_url": server_url,
                    "token": config_data.get("token"),
                    "username": config_data.get("username")
                }, f)
            
            # Create and show popup with game ID
            popup = PopupDialog(
                "Game Created!",
                game_id,
                screen,
                clock
            )
            
            # Show popup and wait for user to close it
            popup.show()
            
            # Start the game after popup is closed
            pygame.quit()
            subprocess.Popen([sys.executable, "main.py"])
            sys.exit()
        else:
            error_message = response.text if response.text else f"Server error: {response.status_code}"
            return f"Error creating game: {error_message}"
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to server. Please check your internet connection."
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

async def main():
    """Main launcher function"""

    global is_fullscreen
    flags = pygame.RESIZABLE | pygame.DOUBLEBUF
    screen = pygame.display.set_mode(WINDOWED_SIZE, flags)
    pygame.display.set_caption("CodeBreak Game Launcher")
    clock = pygame.time.Clock()
    current_width = WIDTH
    current_height = HEIGHT

    def update_ui_positions():
        nonlocal current_width, current_height, game_list, single_player_btn, create_game_btn, join_game_btn, refresh_btn
        # Update game list position and size
        game_list.rect.x = current_width // 2 - 300
        game_list.rect.y = 150
        game_list.rect.width = min(600, current_width - 100)
        game_list.rect.height = min(400, current_height - 300)

        # Update button positions
        center_x = current_width // 2
        button_y = current_height - 150  # Position from bottom
        spacing = BUTTON_WIDTH + 30

        # Update button positions
        single_player_btn.rect.x = center_x - spacing
        single_player_btn.rect.y = button_y
        create_game_btn.rect.x = center_x
        create_game_btn.rect.y = button_y
        join_game_btn.rect.x = center_x + spacing
        join_game_btn.rect.y = button_y
        refresh_btn.rect.x = center_x - 60
        refresh_btn.rect.y = button_y + BUTTON_HEIGHT + 30

     # Function to toggle fullscreen
    def toggle_fullscreen():
        global is_fullscreen
        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
            nonlocal current_width, current_height
            current_width, current_height = screen.get_size()
            update_ui_positions()
            return screen
        else:
            screen = pygame.display.set_mode(WINDOWED_SIZE, flags)
            current_width, current_height = WINDOWED_SIZE
            update_ui_positions()
            return screen

    # Check if player is logged in via client_config.json
    if not is_logged_in():
        # Show login screen
        open_login_page()
        
        # Wait for login to complete or timeout
        login_screen = True
        start_time = time.time()
        timeout = 300  # 5 minutes timeout
        
        while login_screen and time.time() - start_time < timeout:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            # Check if login completed
            if is_logged_in():
                login_screen = False
                break
                
            # Draw waiting screen
            screen.fill(DARK_BLUE)
            
            # Draw title
            title = font_lg.render("CODEBREAK", True, NEON_BLUE)
            title_shadow = font_lg.render("CODEBREAK", True, NEON_PINK)
            screen.blit(title_shadow, (WIDTH // 2 - title_shadow.get_width() // 2 + 3, 150 + 3))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
            
            # Draw login message
            msg = font_md.render("Please login in your browser", True, WHITE)
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 250))
            
            # Draw timer
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            timer = font_sm.render(f"Waiting for login... {remaining}s", True, GRAY)
            screen.blit(timer, (WIDTH // 2 - timer.get_width() // 2, 300))
            
            pygame.display.flip()
            await asyncio.sleep(0.1)
            
        if time.time() - start_time >= timeout:
            # Login timeout
            pygame.quit()
            print("Login timeout. Please try again.")
            sys.exit()
    
    # User is logged in, load config data
    with open(CONFIG_FILE, "r") as f:
        config_data = json.load(f)
        
    username = config_data.get("username", "Player")
    
    # Create game list
    game_list = GameList(WIDTH // 2 - 300, 150, 600, 400)
    game_list.update(config_data)  # Pass config_data instead of auth_data
    
    # Create buttons
    center_x = WIDTH // 2
    button_y = 580
    spacing = BUTTON_WIDTH + 30  # 30 pixels between buttons

    single_player_btn = Button(center_x - spacing, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, 
                              "PLAY SOLO", lambda: start_single_player(config_data))
    
    create_game_btn = Button(center_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, 
                            "CREATE GAME", lambda: create_multiplayer_game(config_data, screen, clock))
    
    join_game_btn = Button(center_x + spacing, button_y, BUTTON_WIDTH, BUTTON_HEIGHT, 
                          "JOIN GAME", lambda: join_multiplayer_game(game_list.selected_game, config_data))
    
    refresh_btn = Button(center_x - 60, button_y + BUTTON_HEIGHT + 30, 120, 40, 
                        "REFRESH", lambda: game_list.update(config_data))
    
    # Status message
    status_message = ""
    status_color = WHITE
    
    # Main loop
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
        screen.blit(title_shadow, (WIDTH // 2 - title_shadow.get_width() // 2 + 3, 70 + 3))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))
        
        # Draw logged in as
        logged_in_text = font_sm.render(f"Logged in as: {username}", True, WHITE)
        screen.blit(logged_in_text, (WIDTH - logged_in_text.get_width() - 20, 20))
        
        # Draw game list
        game_list.draw(screen)
        
        # Update button states
        join_game_btn.disabled = game_list.selected_game is None
        
        # Update and draw buttons
        for btn in [single_player_btn, create_game_btn, join_game_btn, refresh_btn]:
            btn.update(mouse_pos)
            btn.draw(screen)
        
        # Draw status message
        if status_message:
            status_text = font_sm.render(status_message, True, status_color)
            screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, HEIGHT - 50))
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT):
                    screen = toggle_fullscreen()
            
            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                screen = pygame.display.set_mode((event.w, event.h), flags)
                current_width, current_height = event.w, event.h
                update_ui_positions()
            
            # Handle button events
            button_result = None
            for btn in [single_player_btn, create_game_btn, join_game_btn, refresh_btn]:
                if btn.handle_event(event):
                    if btn == single_player_btn:
                        button_result = start_single_player(config_data)
                    elif btn == create_game_btn:
                        button_result = create_multiplayer_game(config_data, screen, clock)
                    elif btn == join_game_btn:
                        button_result = join_multiplayer_game(game_list.selected_game, config_data)
                    break
            
            if button_result:
                status_message = button_result
                status_color = NEON_PINK
            
            # Handle game list events
            game_list.handle_event(event, mouse_pos)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
    
    pygame.quit()
    sys.exit()

def run_async_main():
    """Helper function to run asyncio main"""
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

if __name__ == "__main__":
    run_async_main() 