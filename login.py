import stat
import pygame
import requests
import json
import sys
import os
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CodeBreak - Login")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
DARK_BLUE = (10, 10, 25)
NEON_BLUE = (0, 195, 255)
NEON_PINK = (255, 41, 117)

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

class InputBox:
    def __init__(self, x, y, w, h, text='', password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = GRAY
        self.text = text
        self.masked_text = '*' * len(text) if password else text
        self.password = password
        self.txt_surface = font_sm.render(self.masked_text, True, WHITE)
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_speed = 30  # Frames per blink

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable
                self.active = True
            else:
                self.active = False
            # Change the current color
            self.color = NEON_BLUE if self.active else GRAY
        
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                
                # Re-render the text
                self.masked_text = '*' * len(self.text) if self.password else self.text
                self.txt_surface = font_sm.render(self.masked_text, True, WHITE)
        
        return False

    def update(self):
        # Update cursor blinking
        self.cursor_timer += 1
        if self.cursor_timer >= self.cursor_blink_speed:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible
        
        # Resize the box if the text is too long
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        
        # Draw the cursor if active
        if self.active and self.cursor_visible:
            cursor_pos = self.rect.x + 5 + self.txt_surface.get_width()
            pygame.draw.line(screen, WHITE, 
                           (cursor_pos, self.rect.y + 5),
                           (cursor_pos, self.rect.y + self.rect.h - 5), 2)
        
        # Draw the rect
        pygame.draw.rect(screen, self.color, self.rect, 2)

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


def login_or_register(username, password, mode="login"):
    """Function to login or register a user with the server"""
    # Load server URL from configuration
    try:
        with open("server_config.json", "r") as f:
            config = json.load(f)
            base_url = config.get("server_url", "http://3.130.249.194:8000")
    except (FileNotFoundError, json.JSONDecodeError):
        base_url = "http://3.130.249.194:8000"  # Default fallback
    
    print(f"Using server: {base_url}")
    
    max_retries = 10  # Increase number of retries
    retry_delay = 5  # Increase delay between retries in seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries}: Connecting to {base_url}...")
            if mode == "register":
                url = f"{base_url}/register/user"
                print(f"Registering user at URL: {url}")
                response = requests.post(url, json={"username": username, "password": password})
                
                if response.status_code == 200:
                    print("Registration successful")
                    mode = "login"  # Proceed to login after registration
                else:
                    return False, f"Registration failed: {response.text}"
            
            if mode == "login":
                url = f"{base_url}/token"
                print(f"Logging in user at URL: {url}")
                response = requests.post(url, data={"username": username, "password": password})
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Save token to a file for the game to use
                    with open("auth_token.json", "w") as f:
                        json.dump({
                            "username": username,
                            "password":password,
                            "token": token_data["access_token"],
                            "token_type": token_data["token_type"]
                        }, f)
                    
                    return True, "Login successful"
                else:
                    return False, f"Login failed: {response.text}"
        
        except requests.ConnectionError as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Unable to connect to the server.")
            print("Details:", str(e))
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return False, f"Error: Unable to connect to the server after {max_retries} attempts. Details: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    return False, "Unknown error"


def main():
    """Main login screen function"""
    clock = pygame.time.Clock()
    running = True

    # Draw title and subtitle first
    title = font_lg.render("CODEBREAK", True, NEON_BLUE)
    title_y = HEIGHT // 4
    subtitle = font_md.render("LOGIN / REGISTER", True, NEON_PINK)
    subtitle_y = title_y + title.get_height() + 20  # 20px below title

    # Recalculate positions relative to the subtitle
    username_box_y = subtitle_y + subtitle.get_height() + 40
    password_box_y = username_box_y + 80
    button_y = password_box_y + 80
    status_message_y = button_y + 80

    # Create input boxes using the new positions
    username_box = InputBox(WIDTH // 2 - 100, username_box_y, 200, 40)
    password_box = InputBox(WIDTH // 2 - 100, password_box_y, 200, 40, password=True)
    
    # Create login and register buttons
    login_btn = Button(WIDTH // 2 - 110, button_y, 100, 40, "LOGIN", 
                       lambda: handle_auth(username_box.text, password_box.text, "login"))
    
    register_btn = Button(WIDTH // 2 + 10, button_y, 100, 40, "REGISTER", 
                          lambda: handle_auth(username_box.text, password_box.text, "register"))
    
    # Status message
    status_message = ""
    status_color = WHITE

    def handle_auth(username, password, mode):
        nonlocal status_message, status_color
        if not username or not password:
            status_message = "Username and password are required"
            status_color = NEON_PINK
            return
        
        success, message = login_or_register(username, password, mode)
        
        if success:
            status_message = message
            status_color = NEON_BLUE
            pygame.time.delay(1000)  # Show success message for 1 second
            import subprocess
            subprocess.Popen([sys.executable, "main.py"])
            pygame.quit()
            sys.exit()
        else:
            status_message = message
            status_color = NEON_PINK
        print(status_message)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle events for both input boxes
            username_box.handle_event(event)
            if password_box.handle_event(event):  # if the event triggers login (e.g. Enter key)
                handle_auth(username_box.text, password_box.text, "login")
            
            # Handle button clicks
            login_btn.handle_event(event)
            register_btn.handle_event(event)
        
        # Update UI elements
        username_box.update()
        password_box.update()
        login_btn.update(mouse_pos)
        register_btn.update(mouse_pos)
        
        # Clear screen and draw background
        screen.fill(DARK_BLUE)
        
        # Draw Title and Subtitle
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, title_y))
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, subtitle_y))
        
        # Draw labels above the input boxes
        username_label = font_sm.render("Username", True, WHITE)
        screen.blit(username_label, (WIDTH // 2 - 100, username_box_y - 30))
        
        password_label = font_sm.render("Password", True, WHITE)
        screen.blit(password_label, (WIDTH // 2 - 100, password_box_y - 30))
        
        # Draw input boxes, buttons and status message
        username_box.draw(screen)
        password_box.draw(screen)
        login_btn.draw(screen)
        register_btn.draw(screen)
        
        if status_message:
            status_text = font_sm.render(status_message, True, status_color)
            screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, status_message_y))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()