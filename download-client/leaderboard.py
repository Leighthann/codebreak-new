import pygame
import requests
import json
import time
import os
from datetime import datetime

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CodeBreak - Leaderboard")


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
DARK_BLUE = (10, 10, 25)
NEON_BLUE = (0, 195, 255)
NEON_PINK = (255, 41, 117)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)

# Load fonts
try:
    title_font = pygame.font.Font("fonts/cyberpunk.ttf", 48)
    header_font = pygame.font.Font("fonts/cyberpunk.ttf", 32)
    info_font = pygame.font.Font("fonts/cyberpunk.ttf", 24)
    small_font = pygame.font.Font("fonts/cyberpunk.ttf", 18)
except:
    print("Warning: Could not load cyberpunk font, using system font")
    title_font = pygame.font.Font(None, 48)
    header_font = pygame.font.Font(None, 32)
    info_font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 18)

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
        text_surf = info_font.render(self.text, True, text_color)
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

class Leaderboard:
    def __init__(self, server_url="http://3.130.249.194:8000"):
        self.server_url = server_url
        self.leaderboard_data = []
        self.player_username = None
        self.last_refresh_time = 0
        self.error_message = None
        self.loading = False
        self.auth_token = None
        
        # Load token if exists
        self.load_auth_token()
        
        # Create buttons
        self.refresh_button = Button(WIDTH - 150, 40, 120, 40, "REFRESH", self.refresh_leaderboard)
        self.return_button = Button(WIDTH//2 - 60, HEIGHT - 60, 120, 40, "RETURN", self.return_to_game)
        
    def load_auth_token(self):
        """Load auth token from file if exists"""
        try:
    
            # If not found, try the token folder
            config_path = "client_config.json"
        
            if os.path.exists(config_path):
                print(f"Found configuration at {config_path}")
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                    self.auth_token = config_data.get("token")
                    self.player_username = config_data.get("username")
                    print(f"Loaded token for {self.player_username}")
                    return
            else:
                print("client_config.json not found")
                self.auth_token = None
                self.player_username = None
                        
        except Exception as e:
            print(f"Error loading auth token: {e}")
            self.auth_token = None
            self.player_username = None
            
    def refresh_leaderboard(self):
        """Fetch latest leaderboard data from server"""
        if time.time() - self.last_refresh_time < 2:  # Rate limiting
            return
            
        self.loading = True
        self.error_message = None
        
        try:
            # Send request to get leaderboard data
            url = f"{self.server_url}/leaderboard"
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
                
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.leaderboard_data = data.get("leaderboard", [])
                self.last_refresh_time = time.time()
            else:
                self.error_message = f"Failed to fetch leaderboard: {response.status_code}"
        except Exception as e:
            self.error_message = f"Error: {str(e)}"
        finally:
            self.loading = False
            
    def submit_score(self, score, wave_reached=0, survival_time=0):
        """Submit a new score to the server"""
        if not self.auth_token:
            self.error_message = "You must be logged in to submit scores"
            return False
            
        try:
            url = f"{self.server_url}/leaderboard"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            data = {
                "score": score,
                "wave_reached": wave_reached,
                "survival_time": survival_time
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                print("Score submitted successfully")
                self.refresh_leaderboard()  # Refresh to see updated leaderboard
                return True
            else:
                self.error_message = f"Failed to submit score: {response.text}"
                return False
        except Exception as e:
            self.error_message = f"Error submitting score: {str(e)}"
            return False
            
    def return_to_game(self):
        """Return to the main game"""
        if __name__ == "__main__":
            pygame.quit()
        return False  # Signal to return to game
        
    def draw_background(self, screen):
        """Draw cyberpunk-style background with grid and glow effects"""
        # Draw a dark background with grid pattern
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill(DARK_BLUE)
        
        # Draw grid lines with cyberpunk style
        for x in range(0, WIDTH + 1, 40):
            alpha = min(255, 100 + abs(((x % 120) - 60)))
            color = (0, 70, 100, alpha // 2)
            pygame.draw.line(background, color, (x, 0), (x, HEIGHT))
            
        for y in range(0, HEIGHT + 1, 40):
            alpha = min(255, 100 + abs(((y % 120) - 60)))
            color = (0, 70, 100, alpha // 2)
            pygame.draw.line(background, color, (0, y), (WIDTH, y))
        
        screen.blit(background, (0, 0))
        
        # Add a neon glow effect at the top
        glow_surf = pygame.Surface((WIDTH, 200), pygame.SRCALPHA)
        for i in range(10):
            alpha = 20 - i*2
            pygame.draw.rect(glow_surf, (*NEON_BLUE, alpha), (0, i*5, WIDTH, 10))
        screen.blit(glow_surf, (0, 0))
        
    def draw(self, screen):
        """Draw the leaderboard screen"""
        # Draw background
        self.draw_background(screen)
        
        # Draw title
        title = title_font.render("LEADERBOARD", True, NEON_BLUE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        self.refresh_button.update(mouse_pos)
        self.refresh_button.draw(screen)
        self.return_button.update(mouse_pos)
        self.return_button.draw(screen)
        
        # Draw loading or error message
        if self.loading:
            loading_text = info_font.render("Loading...", True, NEON_PINK)
            screen.blit(loading_text, (WIDTH // 2 - loading_text.get_width() // 2, 100))
            return
            
        if self.error_message:
            error_text = info_font.render(self.error_message, True, NEON_PINK)
            screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, 100))
        
        # Draw table headers
        headers = ["RANK", "PLAYER", "SCORE", "LAST PLAYED"]
        header_positions = [100, 160, 400, 550]
        
        # Draw header background
        header_bg = pygame.Surface((WIDTH - 150, 40))
        header_bg.fill((0, 30, 60))
        header_bg.set_alpha(200)
        screen.blit(header_bg, (75, 120))
        
        for i, header in enumerate(headers):
            header_text = info_font.render(header, True, NEON_BLUE)
            screen.blit(header_text, (header_positions[i], 130))
        
        # Draw separator line with glow
        pygame.draw.rect(screen, NEON_PINK, (75, 170, WIDTH - 150, 3))
        for i in range(5):
            pygame.draw.rect(screen, (*NEON_PINK, 50 - i*10), 
                          (75, 170 + i, WIDTH - 150, 1))
        
        # If no data, prompt user to refresh
        if not self.leaderboard_data:
            no_data = info_font.render("No leaderboard data available. Click REFRESH to update.", True, WHITE)
            screen.blit(no_data, (WIDTH // 2 - no_data.get_width() // 2, 250))
            return
        
        # Draw leaderboard entries
        for i, entry in enumerate(self.leaderboard_data):
            if i >= 10:  # Only show top 10
                break
                
            y_pos = 180 + i * 40
            
            # Row background with alternating colors
            row_bg = pygame.Surface((WIDTH - 150, 40))
            
            # Highlight the player's score
            is_player = entry.get("username") == self.player_username
            
            if is_player:
                row_bg.fill((50, 10, 80))  # Brighter for player
            elif i % 2 == 0:
                row_bg.fill((20, 20, 40))
            else:
                row_bg.fill((10, 10, 30))
                
            row_bg.set_alpha(200)
            screen.blit(row_bg, (75, y_pos))
            
            # Draw rank with medal for top 3
            if i < 3:
                medal_colors = [GOLD, SILVER, BRONZE]  # Gold, Silver, Bronze
                pygame.draw.circle(screen, medal_colors[i], (100, y_pos + 20), 15)
                rank_text = info_font.render(str(i+1), True, BLACK)
                screen.blit(rank_text, (100 - rank_text.get_width()//2, y_pos + 20 - rank_text.get_height()//2))
            else:
                rank_text = info_font.render(f"{i+1}", True, WHITE)
                screen.blit(rank_text, (100 - rank_text.get_width()//2, y_pos + 20 - rank_text.get_height()//2))
            
            # Draw player name
            name_color = NEON_PINK if is_player else WHITE
            name_text = info_font.render(entry.get("username", "Unknown"), True, name_color)
            screen.blit(name_text, (160, y_pos + 10))
            
            # Draw score
            score_text = info_font.render(f"{entry.get('score', 0):,}", True, WHITE)
            screen.blit(score_text, (400, y_pos + 10))
            
            # Draw last login time if available
            if entry.get("last_login"):
                try:
                    # Parse timestamp and format
                    timestamp = entry.get("last_login")
                    if isinstance(timestamp, str):
                        # Convert string format to datetime
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        date_str = dt.strftime("%m/%d/%Y")
                    else:
                        date_str = "Unknown"
                except:
                    date_str = "Unknown"
            else:
                date_str = "Unknown"
                
            date_text = small_font.render(date_str, True, GRAY)
            screen.blit(date_text, (550, y_pos + 12))
        
        # Draw additional information
        if self.player_username:
            player_info = small_font.render(f"Logged in as: {self.player_username}", True, NEON_BLUE)
            screen.blit(player_info, (20, HEIGHT - 30))
        
        # Draw last refresh time
        if self.last_refresh_time > 0:
            time_str = datetime.fromtimestamp(self.last_refresh_time).strftime("%H:%M:%S")
            refresh_info = small_font.render(f"Last updated: {time_str}", True, GRAY)
            screen.blit(refresh_info, (WIDTH - refresh_info.get_width() - 20, HEIGHT - 30))
    
    def handle_events(self):
        """Handle pygame events for the leaderboard"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_F5:
                    self.refresh_leaderboard()
            
            # Handle button clicks
            self.refresh_button.handle_event(event)
            if self.return_button.handle_event(event):
                return False
                
        return True

def main():
    """Run the leaderboard as a standalone app"""
    leaderboard = Leaderboard()
    
    # Initial leaderboard data fetch
    leaderboard.refresh_leaderboard()
    
    # Main loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # Handle events
        running = leaderboard.handle_events()
        
        # Draw everything
        leaderboard.draw(screen)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()         