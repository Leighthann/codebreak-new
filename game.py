# game.py
import pygame
import sys
import random
import math
import time
import os
import json
from player import Player
from enemy import Enemy
from effects import GameEffects
from world import WorldGenerator
from worldObject import WorldObjects

pygame.init()

# Game window settings
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
TILE_SIZE = 32  # Define TILE_SIZE here
BG_COLOR = (10, 10, 25)  # Dark blue background

# Fonts for UI elements

try:
    title_font = pygame.font.Font("fonts/cyberpunk.ttf", 60)
    button_font = pygame.font.Font("fonts/cyberpunk.ttf", 40)
    info_font = pygame.font.Font("fonts/cyberpunk.ttf", 24)
except:
    print("Warning: Could not load cyberpunk font, using system font")
    title_font = pygame.font.Font(None, 60)
    button_font = pygame.font.Font(None, 40)
    info_font = pygame.font.Font(None, 24)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)
NEON_BLUE = (0, 195, 255)
NEON_GREEN = (57, 255, 20)
NEON_PINK = (255, 41, 117)
NEON_RED = (255, 49, 49)
NEON_PURPLE = (190, 0, 255)  # Adding missing NEON_PURPLE color

class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False
        
    def draw(self, surface, font):
        # Colors
        base_color = NEON_BLUE
        hover_color = NEON_PINK
        text_color = WHITE
        
        # Draw button background
        color = hover_color if self.hovered else base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)  # Border
        
        # Draw text
        text_surf = font.render(self.text, True, text_color)
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


class Slider:
    def __init__(self, x, y, width, height, label, value, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = value  # 0.0 to 1.0
        self.callback = callback
        self.active = False
        self.handle_width = 15
        
    def draw(self, surface, font):
        # Draw label
        label_surf = font.render(f"{self.label}: {int(self.value * 100)}%", True, WHITE)
        label_rect = label_surf.get_rect(bottomleft=(self.rect.x, self.rect.y - 5))
        surface.blit(label_surf, label_rect)
        
        # Draw slider background
        pygame.draw.rect(surface, GRAY, self.rect, border_radius=3)
        
        # Draw slider fill
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, 
                               int(self.rect.width * self.value), self.rect.height)
        pygame.draw.rect(surface, NEON_BLUE, fill_rect, border_radius=3)
        
        # Draw handle
        handle_x = self.rect.x + int(self.rect.width * self.value) - self.handle_width // 2
        handle_rect = pygame.Rect(handle_x, self.rect.y - 2, 
                                 self.handle_width, self.rect.height + 4)
        pygame.draw.rect(surface, WHITE, handle_rect, border_radius=3)
    
    def update(self, mouse_pos):
        # Check if mouse is over the slider
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        # If active, update value based on mouse position
        if self.active:
            # Calculate value based on mouse x position
            rel_x = max(0, min(mouse_pos[0] - self.rect.x, self.rect.width))
            self.value = rel_x / self.rect.width
            # Call the callback with the new value
            self.callback(self.value)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.active = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active:
                self.active = False
                return True
        return False


class Toggle:
    def __init__(self, x, y, label, value, callback):
        self.rect = pygame.Rect(x, y, 50, 25)
        self.label = label
        self.value = value  # Boolean
        self.callback = callback
        self.hovered = False
        
    def draw(self, surface, font):
        # Draw label
        label_surf = font.render(self.label, True, WHITE)
        label_rect = label_surf.get_rect(bottomleft=(self.rect.x, self.rect.y - 5))
        surface.blit(label_surf, label_rect)
        
        # Draw toggle background
        bg_color = NEON_BLUE if self.value else GRAY
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=12)
        
        # Draw toggle switch
        switch_x = self.rect.x + 25 if self.value else self.rect.x + 5
        switch_rect = pygame.Rect(switch_x, self.rect.y + 2, 20, 20)
        pygame.draw.rect(surface, WHITE, switch_rect, border_radius=10)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.value = not self.value
                self.callback(self.value)
                return True
        return False


class Dropdown:
    def __init__(self, x, y, width, height, label, options, current_value, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.options = options
        self.current_value = current_value
        self.callback = callback
        self.hovered = False
        self.expanded = False
        self.option_height = height
        
        # Create option rects
        self.option_rects = []
        for i in range(len(options)):
            option_rect = pygame.Rect(x, y + (i + 1) * height, width, height)
            self.option_rects.append(option_rect)
    
    def draw(self, surface, font):
        # Draw label
        label_surf = font.render(self.label, True, WHITE)
        label_rect = label_surf.get_rect(bottomleft=(self.rect.x, self.rect.y - 5))
        surface.blit(label_surf, label_rect)
        
        # Draw dropdown
        pygame.draw.rect(surface, NEON_BLUE, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)  # Border
        
        # Draw current value
        value_surf = font.render(self.current_value, True, WHITE)
        value_rect = value_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(value_surf, value_rect)
        
        # Draw arrow
        arrow_points = [
            (self.rect.right - 20, self.rect.centery - 5),
            (self.rect.right - 10, self.rect.centery + 5),
            (self.rect.right - 30, self.rect.centery + 5)
        ]
        pygame.draw.polygon(surface, WHITE, arrow_points)
        
        # Draw options if expanded
        if self.expanded:
            for i, option_rect in enumerate(self.option_rects):
                # Draw option background
                hover_color = NEON_PINK if option_rect.collidepoint(pygame.mouse.get_pos()) else NEON_BLUE
                pygame.draw.rect(surface, hover_color, option_rect, border_radius=5)
                pygame.draw.rect(surface, WHITE, option_rect, 2, border_radius=5)  # Border
                
                # Draw option text
                option_surf = font.render(self.options[i], True, WHITE)
                option_rect_center = option_surf.get_rect(midleft=(option_rect.x + 10, option_rect.centery))
                surface.blit(option_surf, option_rect_center)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Toggle expanded state
            if self.hovered:
                self.expanded = not self.expanded
                return True
                
            # Check if clicked on an option
            if self.expanded:
                for i, option_rect in enumerate(self.option_rects):
                    if option_rect.collidepoint(event.pos):
                        self.current_value = self.options[i]
                        self.callback(self.current_value)
                        self.expanded = False
                        return True
                        
            # Close if clicked elsewhere
            if self.expanded:
                self.expanded = False
                
        return False

class Menu:
    def __init__(self, game):
        self.game = game
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.generate_cyberpunk_background()
        
        # Title animation properties
        self.title_y = -100
        self.title_target_y = 100
        self.subtitle_alpha = 0
        
        # Grid animation properties
        self.grid_offset = 0
        self.grid_speed = 0.5
        
        # Button animation properties
        self.buttons_alpha = 0
        
        # Centered menu with cyberpunk theme
        button_width = 250
        center_x = WIDTH // 2 - button_width // 2
        
        self.buttons = [
            Button(center_x, 220, button_width, 50, "PLAY GAME", self.play),
            Button(center_x, 300, button_width, 50, "LEADERBOARD", self.show_leaderboard),
            Button(center_x, 380, button_width, 50, "SETTINGS", self.show_settings),
            Button(center_x, 460, button_width, 50, "EXIT", self.exit_game)
        ]
        
        # Add floating data particles
        self.data_particles = []
        for _ in range(50):
            self.data_particles.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "size": random.randint(1, 3),
                "speed": random.uniform(0.2, 1.0),
                "color": random.choice([NEON_BLUE, NEON_GREEN, NEON_PINK, NEON_PURPLE])
            })

    def generate_cyberpunk_background(self):
        """Create a cyberpunk-style grid background."""
        self.background.fill(BG_COLOR)  # Dark blue base
        
        # Draw horizontal grid lines
        for y in range(0, HEIGHT, 20):
            alpha = random.randint(20, 100)
            line_color = (0, 100, 255, alpha)
            pygame.draw.line(self.background, line_color, (0, y), (WIDTH, y), 1)
        
        # Draw vertical grid lines
        for x in range(0, WIDTH, 40):
            alpha = random.randint(20, 100)
            line_color = (0, 100, 255, alpha)
            pygame.draw.line(self.background, line_color, (x, 0), (x, HEIGHT), 1)
        
        # Add some "data nodes" at grid intersections
        for x in range(0, WIDTH, 40):
            for y in range(0, HEIGHT, 20):
                if random.random() < 0.1:  # 10% chance
                    size = random.randint(1, 3)
                    color_choice = random.random()
                    if color_choice < 0.6:
                        color = NEON_BLUE
                    elif color_choice < 0.8:
                        color = NEON_PINK
                    else:
                        color = NEON_GREEN
                    pygame.draw.circle(self.background, color, (x, y), size)

    def update_animations(self):
        """Update menu animations."""
        # Update title animation
        if self.title_y < self.title_target_y:
            self.title_y += (self.title_target_y - self.title_y) * 0.1
        
        # Update subtitle fade-in
        if self.subtitle_alpha < 255:
            self.subtitle_alpha += 5
        
        # Update button fade-in
        if self.buttons_alpha < 255:
            self.buttons_alpha += 5
        
        # Update grid animation
        self.grid_offset += self.grid_speed
        if self.grid_offset > HEIGHT:
            self.grid_offset = 0
        
        # Update data particles
        for particle in self.data_particles:
            particle["y"] += particle["speed"]
            if particle["y"] > HEIGHT:
                particle["y"] = 0
                particle["x"] = random.randint(0, WIDTH)

    def draw(self, screen):
        # Update animations
        self.update_animations()
        
        # Draw cyberpunk background with animated grid
        screen.blit(self.background, (0, 0))
        
        # Draw animated grid overlay
        grid_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(int(-self.grid_offset), HEIGHT, 20):
            alpha = int(100 * (1 - (abs(y - HEIGHT/2) / (HEIGHT/2))))
            line_color = (0, 150, 255)  # Removed alpha channel
            pygame.draw.line(grid_surface, line_color, (0, y), (WIDTH, y), 1)
        screen.blit(grid_surface, (0, 0))
        
        # Draw data particles
        for particle in self.data_particles:
            pygame.draw.circle(screen, particle["color"], 
                             (int(particle["x"]), int(particle["y"])), 
                             particle["size"])
        
        # Draw title with glowing effect
        title = title_font.render("CODEBREAK", True, NEON_BLUE)
        subtitle = info_font.render("A Digital Survival Game", True, (180, 180, 255, self.subtitle_alpha))
        
        # Add glow effect to title
        glow_surf = pygame.Surface((title.get_width() + 20, title.get_height() + 20), pygame.SRCALPHA)
        for i in range(10, 0, -1):
            alpha = 20 - i*2
            size = i*2
            pygame.draw.rect(glow_surf, (*NEON_BLUE, alpha), 
                           (10-i, 10-i, title.get_width()+size, title.get_height()+size), 
                           border_radius=10)
        screen.blit(glow_surf, (WIDTH // 2 - (title.get_width() + 20) // 2, self.title_y - 10))
        
        # Draw title and subtitle
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, self.title_y))
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, self.title_y + 60))
        
        # Draw buttons
        for button in self.buttons:
            button.draw(screen, button_font)
        
        # Draw version info
        version_text = info_font.render("v1.0", True, (100, 100, 150))
        screen.blit(version_text, (WIDTH - version_text.get_width() - 10, HEIGHT - version_text.get_height() - 10))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.exit_game()
            for button in self.buttons:
                if button.handle_event(event):
                    return

    def play(self):
        print("Starting the game...")
        self.game.transition_to("play")

    def show_leaderboard(self):
        print("Showing leaderboard...")
        self.game.transition_to("leaderboard")

    def show_settings(self):
        print("Showing settings...")
        self.game.transition_to("settings")

    def exit_game(self):
        print("Exiting game...")
        pygame.quit()
        sys.exit()

class Game:
    def __init__(self):
        """Initialize the game state."""
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("CodeBreak")
        self.clock = pygame.time.Clock()
        self.FPS = 60
        
        # Game state
        self.current_state = "menu"
        self.previous_state = None
        self.transition_timer = 0
        self.transition_duration = 15
        self.fading_in = False
        self.fading_out = False
        self.next_state = None
        self.show_crafting = False  # New flag for crafting UI
        
        # Settings
        self.settings = {
            "sound_volume": 0.7,
            "music_volume": 0.5,
            "screen_shake": True,
            "show_damage": True,
            "difficulty": "Normal"
        }
        
        # Load settings if available
        self.load_settings()
        
        # Initialize game assets
        self.load_fonts()
        self.load_colors()
        self.load_sounds()
        self.create_ui_elements()
        
        # Create game objects
        self.player = None
        self.enemies = []
        self.resources = []
        self.power_ups = []
        self.projectiles = []
        self.effects_list = []  # For visual effects
        
        # Camera and effects
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        self.screen_shake_amount = 0
        self.screen_shake_duration = 0
        
        # Game metrics
        self.score = 0
        self.survival_time = 0
        
        # Wave system
        self.wave_number = 0
        self.enemies_to_spawn = 0
        self.spawn_timer = 0
        self.next_wave_timer = 0
        
        # World generation
        self.world_generator = None
        self.object_sprites = {}
        self.resource_sprites = {}
        self.power_up_sprites = {}
        self.enemy_sprite_sheet = None
        self.player_sprite_sheet = None
        
        # Initialize background elements
        self.bg_particles = []
        self.grid_offset_y = 0
        
        # Last frame time for delta time calculation
        self.last_frame_time = pygame.time.get_ticks()
        
        # Debug mode
        self.debug_mode = False
        
        # Game effects
        self.effects = GameEffects()

    def load_fonts(self):
        """Load fonts for the game."""
        # Try to load custom font, fall back to system font
        try:
            pygame.font.init()
            # Check if font file exists
            if os.path.exists("fonts/cyber.ttf"):
                self.font_xl = pygame.font.Font("fonts/cyber.ttf", 48)
                self.font_lg = pygame.font.Font("fonts/cyber.ttf", 36)
                self.font_md = pygame.font.Font("fonts/cyber.ttf", 24)
                self.font_sm = pygame.font.Font("fonts/cyber.ttf", 18)
            else:
                # Use default font
                print("Warning: Could not load cyberpunk font, using system font")
                self.font_xl = pygame.font.Font(None, 48)
                self.font_lg = pygame.font.Font(None, 36)
                self.font_md = pygame.font.Font(None, 24)
                self.font_sm = pygame.font.Font(None, 18)
        except Exception as e:
            print(f"Error loading fonts: {e}")
            # Fallback to system font
            self.font_xl = pygame.font.Font(None, 48)
            self.font_lg = pygame.font.Font(None, 36)
            self.font_md = pygame.font.Font(None, 24)
            self.font_sm = pygame.font.Font(None, 18)

    def load_colors(self):
        """Initialize color schemes."""
        # Colors already defined as constants
        pass

    def load_sounds(self):
        """Load sound effects."""
        # Using the GameEffects class for sound management
        self.effects = GameEffects(volume=self.settings["sound_volume"])

    def create_ui_elements(self):
        """Create UI elements like buttons."""
        # Create menu buttons
        button_width = 200
        button_height = 50
        button_x = WIDTH // 2 - button_width // 2
        
        self.menu_buttons = [
            Button(button_x, 250, button_width, button_height, "START GAME", lambda: self.transition_to("gameplay")),
            Button(button_x, 320, button_width, button_height, "SETTINGS", lambda: self.transition_to("settings")),
            Button(button_x, 390, button_width, button_height, "QUIT", pygame.quit)
        ]
        
        # Create pause menu buttons
        self.pause_buttons = [
            Button(button_x, 250, button_width, button_height, "RESUME", lambda: self.transition_to("gameplay")),
            Button(button_x, 320, button_width, button_height, "SETTINGS", lambda: self.transition_to("settings")),
            Button(button_x, 390, button_width, button_height, "QUIT TO MENU", lambda: self.transition_to("menu"))
        ]
        
        # Create game over buttons
        self.game_over_buttons = [
            Button(button_x, 350, button_width, button_height, "PLAY AGAIN", lambda: self.restart_game()),
            Button(button_x, 420, button_width, button_height, "QUIT TO MENU", lambda: self.transition_to("menu"))
        ]
        
        # Create settings controls
        self.settings_controls = []
        
        # Add back button
        self.settings_controls.append(
            Button(button_x, 450, button_width, button_height, "SAVE & RETURN", lambda: self.transition_to("menu"))
        )
        
        # Add sliders for volume
        self.settings_controls.append(
            Slider(WIDTH // 2 - 100, 150, 200, 20, "Sound Volume", 
                  self.settings["sound_volume"], lambda val: self.update_setting("sound_volume", val))
        )
        
        self.settings_controls.append(
            Slider(WIDTH // 2 - 100, 200, 200, 20, "Music Volume", 
                  self.settings["music_volume"], lambda val: self.update_setting("music_volume", val))
        )
        
        # Add toggles
        self.settings_controls.append(
            Toggle(WIDTH // 2 - 100, 250, "Screen Shake", 
                  self.settings["screen_shake"], lambda val: self.update_setting("screen_shake", val))
        )
        
        self.settings_controls.append(
            Toggle(WIDTH // 2 - 100, 300, "Show Damage", 
                  self.settings["show_damage"], lambda val: self.update_setting("show_damage", val))
        )
        
        # Add dropdown for difficulty
        self.settings_controls.append(
            Dropdown(WIDTH // 2 - 100, 350, 200, 30, "Difficulty", 
                    ["Easy", "Normal", "Hard"], 
                    self.settings["difficulty"], 
                    lambda val: self.update_setting("difficulty", val))
        )

    def handle_gameplay(self, events=None, dt=1/60):
        """Handle gameplay state."""
        if not self.player:
            return
            
        keys = pygame.key.get_pressed()
        
        # Handle events first to ensure menu toggles are responsive
        for event in events or []:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                # Crafting menu toggle
                if event.key == pygame.K_c:
                    self.show_crafting = not self.show_crafting
                    self.play_sound("menu_select")
                    print(f"Crafting menu {'opened' if self.show_crafting else 'closed'}")  # Debug print
                
                # ESC handling
                elif event.key == pygame.K_ESCAPE:
                    if self.show_crafting:
                        self.show_crafting = False
                        self.play_sound("menu_select")
                    else:
                        self.transition_to("pause")
                
                # Crafting selection (only when menu is open)
                elif self.show_crafting and event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    craft_index = event.key - pygame.K_1  # Convert to 0-based index
                    print(f"Attempting to craft item {craft_index + 1}")  # Debug print
                    self.handle_crafting_selection(craft_index)
                
                # E key - Tool usage (one-time press detection for feedback)
                elif event.key == pygame.K_e and not self.show_crafting:
                    if not self.player.equipped_tool:
                        self.add_effect("text", self.player.x, self.player.y - 30,
                                       text="No tool equipped!",
                                       color=RED,
                                       size=20,
                                       duration=2.0)
                        print("DEBUG: E key pressed but no tool equipped")
        
        # Handle continuous gameplay actions when crafting menu is closed
        if not self.show_crafting:
            # Process movement
            moving = self.player.move(keys, self.world_generator)
            
            # Handle tool usage with E key
            if keys[pygame.K_e] and self.player.equipped_tool:
                self.player.use_tool()
                self.play_sound("level_up")
                print("Using equipped tool")  # Debug print
                
                # Add visual effect to show tool was used
                tool_name = self.player.equipped_tool["name"]
                if tool_name == "data_shield":
                    effect_text = "Shield activated!"
                    effect_color = CYAN
                elif tool_name == "hack_tool":
                    effect_text = "Hack activated!"
                    effect_color = GREEN
                elif tool_name == "energy_sword":
                    effect_text = "Energy blade activated!"
                    effect_color = NEON_BLUE
                else:
                    effect_text = "Tool activated!"
                    effect_color = WHITE
                
                self.add_effect("text", self.player.x, self.player.y - 30,
                              text=effect_text,
                              color=effect_color,
                              size=20,
                              duration=1.0)
                
                # Add special visual effects based on tool type
                if tool_name == "energy_sword":
                    self.add_effect("explosion", self.player.x, self.player.y)
                elif tool_name == "hack_tool":
                    self.start_screen_shake(5, 0.5)
            
            # Update player animation
            self.player.animate(moving, keys, self.enemies)
            
            # Update game world
            self.update_game_world(dt)  # Pass the proper dt value
        
        # Update camera shake
        if self.screen_shake_duration > 0:
            self.screen_shake_duration -= 1
            if self.screen_shake_duration <= 0:
                self.camera_offset_x = 0
                self.camera_offset_y = 0
            else:
                self.camera_offset_x = random.randint(-2, 2)
                self.camera_offset_y = random.randint(-2, 2)
        
        # Draw game world
        self.draw_gameplay_elements()
        
        # Draw crafting UI on top if active
        if self.show_crafting:
            self.draw_crafting_ui()
        
        # Always draw UI
        self.draw_gameplay_ui()

    def draw_crafting_ui(self):
        """Draw the crafting interface."""
        if not self.player:
            return
            
        # Semi-transparent background
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)  # Make background more visible
        self.screen.blit(overlay, (0, 0))
        
        # Crafting menu title
        title = self.font_lg.render("Crafting Menu", True, NEON_BLUE)
        title_rect = title.get_rect(centerx=WIDTH//2, top=50)
        self.screen.blit(title, title_rect)
        
        # Available recipes
        y_pos = 150
        for i, (item_name, recipe) in enumerate(self.player.crafting_recipes.items()):
            # Item name with key binding
            can_craft = self.player.can_craft(item_name)
            color = GREEN if can_craft else RED
            text = self.font_md.render(f"[{i+1}] {item_name.replace('_', ' ').title()}", True, color)
            text_rect = text.get_rect(x=WIDTH//4, y=y_pos)
            self.screen.blit(text, text_rect)
            
            # Required resources
            resource_text = []
            for resource, amount in recipe.items():
                if resource != "stats":
                    has_amount = self.player.inventory.get(resource, 0)
                    color = GREEN if has_amount >= amount else RED
                    resource_text.append(self.font_sm.render(
                        f"{resource.replace('_', ' ').title()}: {has_amount}/{amount}",
                        True, color
                    ))
            
            # Display resource requirements
            for j, res_text in enumerate(resource_text):
                self.screen.blit(res_text, (WIDTH//4 + 20, y_pos + 30 + j*25))
            
            # Display item stats
            stats_text = []
            for stat, value in recipe["stats"].items():
                stats_text.append(self.font_sm.render(
                    f"{stat.title()}: {value}",
                    True, CYAN
                ))
            
            # Display stats
            for j, stat_text in enumerate(stats_text):
                self.screen.blit(stat_text, (WIDTH*3//4, y_pos + 30 + j*25))
            
            y_pos += 120
        
        # Instructions
        instructions = [
            "Press 1-3 to craft items",
            "Press C or ESC to close",
            "Press E to use equipped items"
        ]
        
        y_offset = HEIGHT - 100
        for instruction in instructions:
            text = self.font_sm.render(instruction, True, WHITE)
            text_rect = text.get_rect(centerx=WIDTH//2, y=y_offset)
            self.screen.blit(text, text_rect)
            y_offset += 25

    def handle_crafting_selection(self, index):
        """Handle crafting item selection."""
        if not self.player:
            return
            
        print(f"DEBUG: Crafting selection called with index {index}")
            
        # Get the item name from the recipe list
        recipes = list(self.player.crafting_recipes.keys())
        if 0 <= index < len(recipes):
            item_name = recipes[index]
            print(f"DEBUG: Attempting to craft {item_name}")
            print(f"DEBUG: Player inventory: {self.player.inventory}")
            
            # Attempt to craft the item
            if self.player.craft_item(item_name):
                self.play_sound("level_up")  # Success sound
                self.add_effect("text", self.player.x, self.player.y - 30,
                              text=f"Crafted {item_name.replace('_', ' ').title()}!",
                              color=GREEN,
                              size=20,
                              duration=2.0)
                print(f"DEBUG: Successfully crafted {item_name}")
                print(f"DEBUG: Updated inventory: {self.player.inventory}")
                print(f"DEBUG: Player crafted items: {self.player.crafted_items}")
            else:
                self.play_sound("menu_select")  # Failure sound
                self.add_effect("text", self.player.x, self.player.y - 30,
                              text="Not enough resources!",
                              color=RED,
                              size=20,
                              duration=2.0)
                print(f"DEBUG: Failed to craft {item_name}")
        else:
            print(f"DEBUG: Invalid craft index {index}, available recipes: {recipes}")

    def update_game_world(self, dt):
        """Update game world entities and check collisions."""
        # Update survival time
        self.survival_time += dt
        
        # Update wave spawning
        self.update_wave_spawning(dt)
        
        # Update enemies
        self.update_enemies(dt)
        
        # Update resources
        self.update_resources(dt)
        
        # Update power-ups
        self.update_power_ups(dt)
        
        # Update projectiles
        self.update_projectiles(dt)
        
        # Update visual effects
        self.update_visual_effects(dt)

    def update_enemies(self, dt):
        """Update all enemy entities."""
        # Use a copy of the list for safe iteration
        for enemy in self.enemies[:]:
            if enemy.active:
                # Update enemy logic
                if self.player:
                    enemy.update(self.player)
                
                # Check if enemy is defeated
                if enemy.health <= 0:
                    # Spawn resources at enemy position
                    if random.random() < 0.7:  # 70% chance to drop resources
                        self.spawn_resource_at(enemy.x, enemy.y)
                    
                    # Remove from active enemies
                    self.enemies.remove(enemy)
                    
                    # Update score
                    self.score += 100 * self.wave_number
                    
                    # Add effect
                    self.add_effect("explosion", enemy.x, enemy.y)

    def update_resources(self, dt):
        """Update all resource entities."""
        # Remove collected resources
        self.resources = [r for r in self.resources if not r["collected"]]
        
        # Update resource animations
        for resource in self.resources:
            # Pulse animation
            resource["pulse"] += 0.05 * resource["pulse_dir"]
            if resource["pulse"] >= 1.0:
                resource["pulse"] = 1.0
                resource["pulse_dir"] = -1
            elif resource["pulse"] <= 0.0:
                resource["pulse"] = 0.0
                resource["pulse_dir"] = 1
        
        # Check collection
        self.check_resource_collection()
        
        # Spawn new resources if needed
        min_resources = 5 + self.wave_number // 2  # Scale with wave number
        if len(self.resources) < min_resources:
            self.spawn_resources(min_resources - len(self.resources))

    def update_projectiles(self, dt):
        """Update all projectiles."""
        # No implementation needed - handled in player.animate()
        pass

    def update_wave_spawning(self, dt):
        """Handle enemy wave spawning."""
        # If no wave active, start first wave
        if self.wave_number == 0:
            self.start_new_wave()
            return
        
        # If still spawning enemies for current wave
        if self.enemies_to_spawn > 0:
            self.spawn_timer += dt
            if self.spawn_timer >= 1.0:  # Spawn every second
                self.spawn_timer = 0
                self.spawn_wave_enemy()
        # If all enemies are defeated, start new wave
        elif len(self.enemies) == 0:
            self.next_wave_timer += dt
            if self.next_wave_timer >= 3.0:  # 3 second pause between waves
                self.next_wave_timer = 0
                self.start_new_wave()

    def start_new_wave(self):
        """Start a new enemy wave."""
        self.wave_number += 1
        
        # Calculate enemies based on wave and difficulty
        base_enemies = 3 + self.wave_number
        difficulty_mult = {"Easy": 0.7, "Normal": 1.0, "Hard": 2.0}
        difficulty_factor = difficulty_mult.get(self.settings["difficulty"], 1.0)
        
        self.enemies_to_spawn = int(base_enemies * difficulty_factor)
        self.spawn_timer = 0
        
        # Show wave notification
        self.add_effect("text", WIDTH // 2, HEIGHT // 2, 
                        text=f"WAVE {self.wave_number}", 
                        color=NEON_BLUE, 
                        size=60, 
                        duration=2.0)
        
        # Play sound
        self.play_sound("level_up")
        
        # Start screen shake
        self.start_screen_shake(20, 0.5)
        
        # Spawn initial enemies immediately
        initial_spawn = min(3, self.enemies_to_spawn)
        for _ in range(initial_spawn):
            self.spawn_wave_enemy()
            self.enemies_to_spawn -= 1

    def spawn_wave_enemy(self):
        """Spawn a single enemy for the current wave."""
        if self.enemies_to_spawn <= 0:
            return
        
        # Always spawn at screen edge
        side = random.randint(0, 3)  # 0: top, 1: right, 2: bottom, 3: left
        if side == 0:  # Top
            x = random.randint(50, WIDTH - 50)
            y = -50
        elif side == 1:  # Right
            x = WIDTH + 50
            y = random.randint(50, HEIGHT - 50)
        elif side == 2:  # Bottom
            x = random.randint(50, WIDTH - 50)
            y = HEIGHT + 50
        else:  # Left
            x = -50
            y = random.randint(50, HEIGHT - 50)
        
        # Create enemy
        enemy = Enemy(self.enemy_sprite_sheet, x, y)
        enemy.active = True
        
        # Scale stats based on wave
        wave_factor = 1.0 + (self.wave_number - 1) * 0.1
        enemy.health = int(50 * wave_factor)
        enemy.max_health = enemy.health
        enemy.speed = int(2 * (1 + (self.wave_number - 1) * 0.05))
        
        self.enemies.append(enemy)
        self.enemies_to_spawn -= 1

    def spawn_resources(self, count):
        """Spawn resources in the world."""
        resource_types = ["code_fragments", "energy_cores", "data_shards"]
        weights = [0.5, 0.3, 0.2]  # Rarity weights
        
        for _ in range(count):
            # Determine position
            x = random.randint(100, WIDTH - 100)
            y = random.randint(100, HEIGHT - 100)
            
            # Ensure not too close to player
            if self.player:
                while ((x - self.player.x) ** 2 + (y - self.player.y) ** 2) < 150**2:
                    x = random.randint(100, WIDTH - 100)
                    y = random.randint(100, HEIGHT - 100)
            
            # Select resource type
            resource_type = random.choices(resource_types, weights=weights, k=1)[0]
            
            # Create resource
            self.resources.append({
                "type": resource_type,
                "x": x,
                "y": y,
                "collected": False,
                "pulse": 0,
                "pulse_dir": 1,
                "value": 1 if resource_type == "code_fragments" else 
                         2 if resource_type == "energy_cores" else
                         5 if resource_type == "data_shards" else 10
            })

    def spawn_resource_at(self, x, y):
        """Spawn a resource at a specific location."""
        resource_types = ["code_fragments", "energy_cores", "data_shards"]
        weights = [0.6, 0.3, 0.1]  # Adjusted weights to match number of resource types
        
        # Random offset
        x += random.randint(-10, 10)
        y += random.randint(-10, 10)
        
        # Select resource type
        resource_type = random.choices(resource_types, weights=weights, k=1)[0]
        
        # Create resource
        self.resources.append({
            "type": resource_type,
            "x": x,
            "y": y,
            "collected": False,
            "pulse": 0,
            "pulse_dir": 1,
            "value": 1 if resource_type == "code_fragments" else 
                     2 if resource_type == "energy_cores" else
                     5 if resource_type == "data_shards" else 10
        })

    def check_resource_collection(self):
        """Check if player has collected resources."""
        if not self.player:
            return
        
        # Collection radius
        collection_radius = TILE_SIZE * 1.5
        
        # Check each resource
        for resource in self.resources:
            if not resource["collected"]:
                # Calculate distance
                dist = ((self.player.x - resource["x"]) ** 2 + 
                       (self.player.y - resource["y"]) ** 2) ** 0.5
                
                if dist < collection_radius:
                    # Mark as collected
                    resource["collected"] = True
                    
                    # Update player stats
                    if resource["type"] == "code_fragments":
                        self.player.energy = min(self.player.max_energy, 
                                                self.player.energy + resource["value"])
                    
                    # Update player inventory
                    if not hasattr(self.player, "inventory"):
                        self.player.inventory = {}
                    if resource["type"] not in self.player.inventory:
                        self.player.inventory[resource["type"]] = 0
                    self.player.inventory[resource["type"]] += resource["value"]
                    
                    # Update score
                    self.score += resource["value"] * 10
                    
                    # Play sound
                    self.play_sound("collect")
                    
                    # Add effect
                    self.add_effect("text", resource["x"], resource["y"] - 20, 
                                    text=f"+{resource['value']}", 
                                    color=WHITE, 
                                    size=16, 
                                    duration=1.0)

    def update_camera_shake(self, dt):
        """Update screen shake effect."""
        if self.screen_shake_duration > 0:
            # Decrease duration
            self.screen_shake_duration -= dt
            
            # Calculate offset
            if self.settings["screen_shake"]:
                intensity = min(self.screen_shake_amount, 10)  # Cap intensity
                self.camera_offset_x = random.randint(-intensity, intensity)
                self.camera_offset_y = random.randint(-intensity, intensity)
            else:
                self.camera_offset_x = 0
                self.camera_offset_y = 0
                
            # Reset when done
            if self.screen_shake_duration <= 0:
                self.screen_shake_duration = 0
                self.camera_offset_x = 0
                self.camera_offset_y = 0
        else:
            self.camera_offset_x = 0
            self.camera_offset_y = 0

    def start_screen_shake(self, amount, duration):
        """Start screen shake effect."""
        self.screen_shake_amount = amount
        self.screen_shake_duration = duration
        
    def add_effect(self, effect_type, x, y, **kwargs):
        """Add a visual effect to the game."""
        effect = {
            "type": effect_type,
            "x": x,
            "y": y,
            "timer": 0
        }
        
        # Add type-specific properties
        if effect_type == "explosion":
            effect["radius"] = 0
            effect["max_radius"] = 20
            effect["color"] = NEON_RED
            effect["duration"] = 0.5
        elif effect_type == "text":
            effect["text"] = kwargs.get("text", "")
            effect["color"] = kwargs.get("color", WHITE)
            effect["size"] = kwargs.get("size", 20)
            effect["duration"] = kwargs.get("duration", 1.0)
            effect["fade_in"] = kwargs.get("fade_in", True)
            effect["fade_out"] = kwargs.get("fade_out", True)
        
        self.effects_list.append(effect)

    def update_visual_effects(self, dt):
        """Update all visual effects."""
        # Update each effect
        for effect in self.effects_list[:]:
            # Increment timer
            effect["timer"] += dt
            
            # Check if expired
            if effect["timer"] >= effect.get("duration", 1.0):
                self.effects_list.remove(effect)
                continue
                
            # Update type-specific logic
            if effect["type"] == "explosion":
                effect["radius"] = (effect["timer"] / effect["duration"]) * effect["max_radius"]
            
    def draw_gameplay_elements(self):
        """Draw all gameplay elements."""
        # Create world surface
        world_surface = pygame.Surface((WIDTH, HEIGHT))
        world_surface.fill(BG_COLOR)
        
        # Draw world map
        if self.world_generator:
            self.world_generator.draw_map(world_surface)
        
        # Draw world objects
        if self.world_generator:
            for obj in self.world_generator.objects:
                sprite = self.object_sprites.get(obj.type)
                if sprite:
                    world_surface.blit(sprite, (obj.x, obj.y))
        
        # Draw resources with pulse effect
        for resource in self.resources:
            if not resource["collected"]:
                sprite = self.resource_sprites.get(resource["type"])
                if sprite:
                    # Apply pulse effect
                    base_size = 48
                    pulse_scale = 1.0 + resource["pulse"] * 0.2
                    scaled_size = int(base_size * pulse_scale)
                    
                    # Scale the sprite
                    scaled_sprite = pygame.transform.scale(sprite, (scaled_size, scaled_size))
                    
                    # Center the scaled sprite
                    offset = (scaled_size - base_size) // 2
                    world_surface.blit(scaled_sprite, (resource["x"] - offset, resource["y"] - offset))
        
        # Draw power-ups
        for power_up in self.power_ups:
            sprite = self.power_up_sprites.get(power_up["type"])
            if sprite:
                world_surface.blit(sprite, (power_up["x"], power_up["y"]))
        
        # Draw enemies
        for enemy in self.enemies:
            if enemy.active and enemy.sprite:
                # Draw enemy sprite
                world_surface.blit(enemy.sprite, (enemy.x, enemy.y))
                
                # Draw health bar if damaged
                if enemy.health < enemy.max_health:
                    bar_width = 40
                    health_percent = enemy.health / enemy.max_health
                    pygame.draw.rect(world_surface, RED, 
                                     (enemy.x + 4, enemy.y - 8, bar_width, 5))
                    pygame.draw.rect(world_surface, GREEN, 
                                     (enemy.x + 4, enemy.y - 8, 
                                      int(bar_width * health_percent), 5))
        
        # Draw player
        if self.player and self.player.sprite:
            world_surface.blit(self.player.sprite, (self.player.x, self.player.y))
        
        # Draw projectiles
        if self.player:
            for projectile in self.player.projectiles:
                pygame.draw.circle(
                    world_surface, 
                    NEON_BLUE, 
                    (projectile["x"], projectile["y"]), 
                    5
                )
        
        # Draw effects
        for effect in self.effects_list:
            if effect["type"] == "explosion":
                pygame.draw.circle(
                    world_surface, 
                    effect["color"], 
                    (effect["x"], effect["y"]), 
                    int(effect["radius"])
                )
            elif effect["type"] == "text":
                # Calculate alpha based on fade
                duration = effect.get("duration", 1.0)
                progress = effect["timer"] / duration
                alpha = 255
                
                if effect.get("fade_in") and progress < 0.3:
                    alpha = int(255 * (progress / 0.3))
                elif effect.get("fade_out") and progress > 0.7:
                    alpha = int(255 * (1 - (progress - 0.7) / 0.3))
                
                # Render text
                font = pygame.font.Font(None, effect["size"])
                text = font.render(effect["text"], True, effect["color"])
                text.set_alpha(alpha)
                
                # Position text (centered)
                text_rect = text.get_rect(center=(effect["x"], effect["y"]))
                world_surface.blit(text, text_rect)
        
        # Apply camera shake
        self.screen.blit(world_surface, (self.camera_offset_x, self.camera_offset_y))
        
        # Draw UI elements on top of the world
        self.draw_gameplay_ui()

    def draw_gameplay_ui(self):
        """Draw the gameplay UI elements."""
        if not self.player:
            return
        
        # Draw health bar
        health_width = 200
        health_height = 20
        health_x = 20
        health_y = 20
        health_fill = max(0, min(1, self.player.health / self.player.max_health))
        
        # Background
        pygame.draw.rect(self.screen, GRAY, (health_x, health_y, health_width, health_height))
        
        # Fill
        pygame.draw.rect(self.screen, RED, 
                       (health_x, health_y, int(health_width * health_fill), health_height))
        
        # Border
        pygame.draw.rect(self.screen, WHITE, (health_x, health_y, health_width, health_height), 2)
        
        # Draw energy bar
        energy_width = 200
        energy_height = 10
        energy_x = health_x
        energy_y = health_y + health_height + 5
        energy_fill = max(0, min(1, self.player.energy / self.player.max_energy))
        
        # Background
        pygame.draw.rect(self.screen, GRAY, (energy_x, energy_y, energy_width, energy_height))
        
        # Fill
        pygame.draw.rect(self.screen, CYAN, 
                       (energy_x, energy_y, int(energy_width * energy_fill), energy_height))
        
        # Border
        pygame.draw.rect(self.screen, WHITE, (energy_x, energy_y, energy_width, energy_height), 1)
        
        # Draw shield bar if player has shield
        if self.player.shield > 0:
            shield_width = 200
            shield_height = 5
            shield_x = health_x
            shield_y = energy_y + energy_height + 5
            shield_fill = max(0, min(1, self.player.shield / 100))  # Assuming max shield is 100
            
            # Background
            pygame.draw.rect(self.screen, GRAY, (shield_x, shield_y, shield_width, shield_height))
            
            # Fill
            pygame.draw.rect(self.screen, YELLOW, 
                           (shield_x, shield_y, int(shield_width * shield_fill), shield_height))
            
            # Border
            pygame.draw.rect(self.screen, WHITE, (shield_x, shield_y, shield_width, shield_height), 1)
        
        # Draw score and wave
        score_text = self.font_md.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (WIDTH - score_text.get_width() - 20, 20))
        
        wave_text = self.font_md.render(f"Wave: {self.wave_number}", True, WHITE)
        self.screen.blit(wave_text, (WIDTH - wave_text.get_width() - 20, 50))
        
        # Draw survival time
        minutes = int(self.survival_time // 60)
        seconds = int(self.survival_time % 60)
        time_text = self.font_md.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
        self.screen.blit(time_text, (WIDTH - time_text.get_width() - 20, 80))
        
        # Draw inventory
        inventory_x = 20
        inventory_y = HEIGHT - 120
        
        # Draw inventory background
        inventory_width = 200
        inventory_height = 100
        pygame.draw.rect(self.screen, (0, 0, 0, 128), 
                       (inventory_x, inventory_y, inventory_width, inventory_height))
        pygame.draw.rect(self.screen, WHITE, 
                       (inventory_x, inventory_y, inventory_width, inventory_height), 1)
        
        # Draw inventory title
        inventory_title = self.font_sm.render("Inventory", True, WHITE)
        self.screen.blit(inventory_title, 
                       (inventory_x + 10, inventory_y + 5))
        
        # Draw inventory contents
        y_offset = inventory_y + 30
        for resource, amount in self.player.inventory.items():
            resource_text = self.font_sm.render(
                f"{resource.replace('_', ' ').title()}: {amount}", 
                True, WHITE
            )
            self.screen.blit(resource_text, (inventory_x + 20, y_offset))
            y_offset += 20
            
        # Draw equipped tool info
        if self.player.equipped_tool:
            tool_x = WIDTH - 220
            tool_y = HEIGHT - 100
            
            # Draw tool background
            pygame.draw.rect(self.screen, (0, 0, 0, 128), 
                           (tool_x, tool_y, 200, 80))
            pygame.draw.rect(self.screen, CYAN, 
                           (tool_x, tool_y, 200, 80), 1)
            
            # Tool title
            tool_name = self.player.equipped_tool["name"].replace("_", " ").title()
            tool_title = self.font_sm.render(f"Equipped: {tool_name}", True, CYAN)
            self.screen.blit(tool_title, (tool_x + 10, tool_y + 10))
            
            # Tool stats
            stats_y = tool_y + 30
            for stat, value in self.player.equipped_tool["stats"].items():
                stat_text = self.font_sm.render(f"{stat.title()}: {value}", True, WHITE)
                self.screen.blit(stat_text, (tool_x + 20, stats_y))
                stats_y += 20
                
            # Tool durability
            durability = self.player.equipped_tool["durability"]
            durability_color = GREEN if durability > 50 else YELLOW if durability > 25 else RED
            durability_text = self.font_sm.render(f"Durability: {durability}%", True, durability_color)
            self.screen.blit(durability_text, (tool_x + 20, stats_y))
            
            # Tool usage hint
            hint_text = self.font_sm.render("Press E to use", True, WHITE)
            self.screen.blit(hint_text, (tool_x + 50, tool_y + 70))
        
        # Draw FPS in top right if enabled
        if self.settings.get("show_fps", True):
            fps = int(self.clock.get_fps())
            fps_text = self.font_sm.render(f"FPS: {fps}", True, WHITE)
            self.screen.blit(fps_text, (WIDTH - fps_text.get_width() - 10, 110))

    def handle_player_defeat(self):
        """Handle player defeat logic."""
        # Play game over sound
        self.play_sound("game_over")
        
        # Create explosion particle effect
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            self.effects_list.append({
                "type": "particle",
                "position": (self.player.x + self.player.width // 2, 
                           self.player.y + self.player.height // 2) if self.player else (0, 0),
                "velocity": (math.cos(angle) * speed, math.sin(angle) * speed),
                "color": (255, 100, 50),
                "size": random.uniform(2, 6),
                "duration": random.randint(30, 60),
                "timer": 0
            })
        
        # Add game over text
        self.effects_list.append({
            "type": "text",
            "text": "GAME OVER",
            "position": (WIDTH // 2, HEIGHT // 2),
            "color": (255, 0, 0),
            "size": 80,
            "duration": 180,
            "timer": 0,
            "fade_in": True
        })
        
        # Add score text
        self.effects_list.append({
            "type": "text",
            "text": f"SCORE: {self.score}",
            "position": (WIDTH // 2, HEIGHT // 2 + 80),
            "color": (255, 255, 255),
            "size": 40,
            "duration": 180,
            "timer": 0,
            "fade_in": True
        })
        
        # Return to menu after delay
        self.player = None  # Remove player to prevent further updates
        pygame.time.set_timer(pygame.USEREVENT, 3000)  # 3 second timer
        
        # Set up one-time event handler
        def handle_game_over_event(event):
            if event.type == pygame.USEREVENT:
                pygame.time.set_timer(pygame.USEREVENT, 0)  # Disable timer
                pygame.event.set_allowed(None)  # Reset event filtering
                self.transition_to("menu")
                return True
            return False
        
        # Add event handler
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.USEREVENT])  # Filter events


    def update_transition(self, dt):
        """Update the screen transition effect."""
        if self.fading_in:
            self.transition_timer += dt
            if self.transition_timer >= self.transition_duration:
                self.fading_in = False
                self.current_state = "play"
        elif self.fading_out:
            self.transition_timer += dt
            if self.transition_timer >= self.transition_duration:
                self.fading_out = False
                self.current_state = self.previous_state
        
        # Draw the transition overlay
        if self.fading_in or self.fading_out:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(int(255 * (1 - self.transition_timer / self.transition_duration)))
            self.screen.blit(overlay, (0, 0))

    def draw_pause_menu(self):
        """Draw the pause menu."""
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause title
        title = title_font.render("PAUSED", True, NEON_BLUE)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
        
        # Draw continue button
        continue_btn = Button("CONTINUE", WIDTH // 2 - 100, 250, 200, 50, self.toggle_pause)
        continue_btn.draw(self.screen, button_font)
        
        # Draw settings button
        settings_btn = Button("SETTINGS", WIDTH // 2 - 100, 320, 200, 50, 
                             lambda: self.transition_to("settings"))
        settings_btn.draw(self.screen, button_font)
        
        # Draw quit button
        quit_btn = Button("QUIT TO MENU", WIDTH // 2 - 100, 390, 200, 50, 
                         lambda: self.transition_to("menu"))
        quit_btn.draw(self.screen, button_font)
        
        # Draw controls info
        controls_text = [
            "CONTROLS:",
            "Arrow Keys - Move",
            "SPACE - Melee Attack",
            "F - Ranged Attack",
            "ESC - Pause/Menu",
            "E - Use Tool",
            "C - Craft"
        ]
        
        for i, text in enumerate(controls_text):
            info = info_font.render(text, True, (200, 200, 200))
            self.screen.blit(info, (WIDTH // 2 - 250, 250 + i * 30))

    def handle_pause_events(self, events):
        """Handle events in the pause menu."""
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.toggle_pause()
                return
        
        # Find and handle button clicks (simplified)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Continue button
                if pygame.Rect(WIDTH // 2 - 100, 250, 200, 50).collidepoint(mouse_pos):
                    self.toggle_pause()
                
                # Settings button
                elif pygame.Rect(WIDTH // 2 - 100, 320, 200, 50).collidepoint(mouse_pos):
                    self.transition_to("settings")
                
                # Quit button
                elif pygame.Rect(WIDTH // 2 - 100, 390, 200, 50).collidepoint(mouse_pos):
                    self.transition_to("menu")

    def draw_leaderboard(self):
        """Draw a fancy leaderboard screen."""
        # Draw a dark background with grid pattern
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill((5, 10, 20))  # Dark blue
        
        # Add grid lines with perspective effect
        vanishing_point_x = WIDTH // 2
        vanishing_point_y = -100
        
        # Draw horizontal grid lines with perspective
        for y in range(0, HEIGHT + 100, 40):
            start_x_left = 0
            start_x_right = WIDTH
            end_x_left = (0 - vanishing_point_x) * (HEIGHT - y) / (HEIGHT - vanishing_point_y) + vanishing_point_x
            end_x_right = (WIDTH - vanishing_point_x) * (HEIGHT - y) / (HEIGHT - vanishing_point_y) + vanishing_point_x
            
            # Draw only if within screen
            if y < HEIGHT:
                color = (0, 100, 255, int(100 * (1 - y / HEIGHT)))
                pygame.draw.line(background, color, (start_x_left, y), (end_x_left, vanishing_point_y))
                pygame.draw.line(background, color, (start_x_right, y), (end_x_right, vanishing_point_y))
        
        # Add vertical grid lines
        for x in range(0, WIDTH, 80):
            color = (0, 100, 255, int(100 * (1 - abs(x - WIDTH/2) / (WIDTH/2))))
            pygame.draw.line(background, color, (x, 0), (x, HEIGHT))
        
        self.screen.blit(background, (0, 0))
        
        # Draw leaderboard title with glow effect
        title = title_font.render("LEADERBOARD", True, NEON_BLUE)
        
        # Add glow
        glow_surf = pygame.Surface((title.get_width() + 20, title.get_height() + 20), pygame.SRCALPHA)
        for i in range(10, 0, -1):
            alpha = 20 - i*2
            size = i*2
            pygame.draw.rect(glow_surf, (*NEON_BLUE, alpha), 
                           (10-i, 10-i, title.get_width()+size, title.get_height()+size), 
                           border_radius=10)
        self.screen.blit(glow_surf, (WIDTH // 2 - (title.get_width() + 20) // 2, 30))
        
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Draw table headers with cyberpunk style
        headers = ["RANK", "PLAYER", "SCORE", "TIME"]
        header_positions = [80, 180, 480, 600]
        
        header_bg = pygame.Surface((WIDTH - 160, 40))
        header_bg.fill((0, 50, 100))
        header_bg.set_alpha(200)
        self.screen.blit(header_bg, (80, 120))
        
        for i, header in enumerate(headers):
            header_text = button_font.render(header, True, (150, 200, 255))
            self.screen.blit(header_text, (header_positions[i], 125))
        
        # Draw glowing horizontal separator
        pygame.draw.rect(self.screen, NEON_BLUE, (60, 170, WIDTH - 120, 3))
        glow_surf = pygame.Surface((WIDTH - 100, 13), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*NEON_BLUE, 50), (0, 0, WIDTH - 100, 13))
        self.screen.blit(glow_surf, (50, 165))
        
        # Draw placeholder leaderboard entries with enhanced visuals
        entries = [
            {"name": "ByteMaster", "score": 10000, "time": 1800},
            {"name": "CodeBreaker", "score": 8500, "time": 1500},
            {"name": "CyberSlice", "score": 7200, "time": 1200},
            {"name": "DataRunner", "score": 6800, "time": 1100},
            {"name": "EncryptionKey", "score": 5500, "time": 900},
            {"name": "FirewallHacker", "score": 4200, "time": 800},
            {"name": "GlitchHunter", "score": 3600, "time": 700},
            {"name": "HexHacker", "score": 2800, "time": 600},
            {"name": "InfoSec", "score": 2000, "time": 500},
            {"name": "JavaScripter", "score": 1500, "time": 400}
        ]
        
        # Add the player's score if they've played
        if hasattr(self, 'score') and self.score > 0:
            player_entry = {"name": "YOU", "score": self.score, "time": int(self.survival_time)}
            
            # Insert at correct position
            inserted = False
            for i, entry in enumerate(entries):
                if player_entry["score"] > entry["score"]:
                    entries.insert(i, player_entry)
                    inserted = True
                    break
            
            if not inserted and len(entries) < 10:
                entries.append(player_entry)
            
            # Keep only top 10
            entries = entries[:10]
        
        # Draw entries with alternating row backgrounds
        for i, entry in enumerate(entries):
            y_pos = 180 + i * 40
            
            # Row background with alternating colors
            row_bg = pygame.Surface((WIDTH - 160, 40))
            if entry.get("name") == "YOU":
                row_bg.fill((50, 0, 100))  # Highlight player's score
            elif i % 2 == 0:
                row_bg.fill((30, 30, 50))
            else:
                row_bg.fill((20, 20, 40))
            row_bg.set_alpha(200)
            self.screen.blit(row_bg, (80, y_pos))
            
            # Draw rank with medal for top 3
            if i < 3:
                medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]  # Gold, Silver, Bronze
                pygame.draw.circle(self.screen, medal_colors[i], (80, y_pos + 20), 15)
                rank_text = info_font.render(str(i+1), True, (0, 0, 0))
                self.screen.blit(rank_text, (80 - rank_text.get_width()//2, y_pos + 20 - rank_text.get_height()//2))
            else:
                rank_text = info_font.render(f"{i+1}", True, (255, 255, 255))
                self.screen.blit(rank_text, (80 - rank_text.get_width()//2, y_pos + 20 - rank_text.get_height()//2))
            
            # Draw player name
            name_text = info_font.render(entry.get("name", "Unknown"), True, 
                                       (255, 255, 0) if entry.get("name") == "YOU" else (255, 255, 255))
            self.screen.blit(name_text, (180, y_pos + 12))
            
            # Draw score with formatting
            score_text = info_font.render(f"{entry.get('score', 0):,}", True, (255, 255, 255))
            self.screen.blit(score_text, (480, y_pos + 12))
            
            # Draw time with formatting
            minutes = entry.get('time', 0) // 60
            seconds = entry.get('time', 0) % 60
            time_text = info_font.render(f"{minutes}m {seconds}s", True, (255, 255, 255))
            self.screen.blit(time_text, (600, y_pos + 12))
        
        # Draw back button
        back_btn = Button("BACK", WIDTH // 2 - 75, HEIGHT - 80, 150, 40, 
                         lambda: self.transition_to("menu"))
        back_btn.draw(self.screen, button_font)
        
        # Draw instructions
        instructions = info_font.render("Press ESC to return to menu", True, (200, 200, 255))
        self.screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 30))

    def draw_settings(self):
        """Draw the settings screen."""
        # Draw a dark background with tech pattern
        background = pygame.Surface((WIDTH, HEIGHT))
        background.fill((5, 10, 20))  # Dark blue
        
        # Add grid lines with perspective effect
        vanishing_point_x = WIDTH // 2
        vanishing_point_y = -100
        
        # Draw horizontal grid lines with perspective
        for y in range(0, HEIGHT + 100, 40):
            start_x_left = 0
            start_x_right = WIDTH
            end_x_left = (0 - vanishing_point_x) * (HEIGHT - y) / (HEIGHT - vanishing_point_y) + vanishing_point_x
            end_x_right = (WIDTH - vanishing_point_x) * (HEIGHT - y) / (HEIGHT - vanishing_point_y) + vanishing_point_x
            
            # Draw only if within screen
            if y < HEIGHT:
                color = (0, 100, 255, int(100 * (1 - y / HEIGHT)))
                pygame.draw.line(background, color, (start_x_left, y), (end_x_left, vanishing_point_y))
                pygame.draw.line(background, color, (start_x_right, y), (end_x_right, vanishing_point_y))
        
        # Add vertical grid lines
        for x in range(0, WIDTH, 80):
            color = (0, 100, 255, int(100 * (1 - abs(x - WIDTH/2) / (WIDTH/2))))
            pygame.draw.line(background, color, (x, 0), (x, HEIGHT))
        
        # Add floating data particles
        for _ in range(50):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(1, 3)
            color = random.choice([NEON_BLUE, NEON_GREEN, NEON_PINK, NEON_PURPLE])
            pygame.draw.circle(background, color, (x, y), size)
        
        self.screen.blit(background, (0, 0))
        
        # Draw settings title with glow
        title = title_font.render("SETTINGS", True, NEON_BLUE)
        
        # Add glow
        glow_surf = pygame.Surface((title.get_width() + 20, title.get_height() + 20), pygame.SRCALPHA)
        for i in range(10, 0, -1):
            alpha = 20 - i*2
            size = i*2
            pygame.draw.rect(glow_surf, (*NEON_BLUE, alpha), 
                           (10-i, 10-i, title.get_width()+size, title.get_height()+size), 
                           border_radius=10)
        self.screen.blit(glow_surf, (WIDTH // 2 - (title.get_width() + 20) // 2, 30))
        
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        # Draw settings with sliders and toggles
        settings_x = WIDTH // 2 - 200
        settings_y = 150
        
        # Sound volume slider
        self.draw_setting_slider("Sound Volume", settings_x, settings_y, 
                               self.settings["sound_volume"], 
                               lambda v: self.update_setting("sound_volume", v))
        
        # Music volume slider
        self.draw_setting_slider("Music Volume", settings_x, settings_y + 70, 
                               self.settings["music_volume"], 
                               lambda v: self.update_setting("music_volume", v))
        
        # Screen shake toggle
        self.draw_setting_toggle("Screen Shake", settings_x, settings_y + 140, 
                               self.settings["screen_shake"], 
                               lambda: self.toggle_setting("screen_shake"))
        
        # Show damage toggle
        self.draw_setting_toggle("Show Damage Numbers", settings_x, settings_y + 210, 
                               self.settings["show_damage"], 
                               lambda: self.toggle_setting("show_damage"))
        
        # Difficulty dropdown
        self.draw_setting_dropdown("Difficulty", settings_x, settings_y + 280, 
                                 self.settings["difficulty"], 
                                 ["Easy", "Normal", "Hard"], 
                                 lambda v: self.update_setting("difficulty", v))
        
        # Draw back button
        back_btn = Button("SAVE & RETURN", WIDTH // 2 - 125, HEIGHT - 80, 250, 50, 
                         lambda: self.transition_to("menu"))
        back_btn.draw(self.screen, button_font)

    def draw_setting_slider(self, label, x, y, value, on_change):
        """Draw a slider setting control."""
        # Draw label
        label_text = info_font.render(label, True, (255, 255, 255))
        self.screen.blit(label_text, (x, y))
        
        # Draw slider track
        track_width = 300
        track_height = 6
        pygame.draw.rect(self.screen, (80, 80, 100), 
                       (x + 100, y + 30, track_width, track_height))
        
        # Draw slider position
        handle_pos = x + 100 + int(value * track_width)
        pygame.draw.rect(self.screen, NEON_BLUE, 
                       (handle_pos - 5, y + 25, 10, 16))
        
        # Add glow to handle
        glow_surf = pygame.Surface((20, 26), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*NEON_BLUE, 100), (0, 0, 20, 26))
        self.screen.blit(glow_surf, (handle_pos - 10, y + 20))
        
        # Draw value percentage
        value_text = info_font.render(f"{int(value * 100)}%", True, (200, 200, 200))
        self.screen.blit(value_text, (x + 410, y + 25))
        
        # Handle interaction
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        if mouse_pressed and y + 20 <= mouse_pos[1] <= y + 40:
            if x + 100 <= mouse_pos[0] <= x + 100 + track_width:
                new_value = (mouse_pos[0] - (x + 100)) / track_width
                new_value = max(0, min(1, new_value))
                on_change(new_value)

    def draw_setting_toggle(self, label, x, y, value, on_toggle):
        """Draw a toggle setting control."""
        # Draw label
        label_text = info_font.render(label, True, (255, 255, 255))
        self.screen.blit(label_text, (x, y))
        
        # Draw toggle background
        toggle_width = 60
        toggle_height = 30
        pygame.draw.rect(self.screen, (80, 80, 100), 
                         (x + 300, y + 5, toggle_width, toggle_height), 
                         border_radius=15)
        
        # Draw toggle position
        handle_pos = x + 300 + 10 if not value else x + 300 + toggle_width - 25
        if value:
            pygame.draw.rect(self.screen, NEON_BLUE, 
                             (x + 300, y + 5, toggle_width, toggle_height), 
                             border_radius=15)
        
        pygame.draw.circle(self.screen, (255, 255, 255), 
                           (handle_pos + 10, y + 5 + toggle_height // 2), 
                           12)
        
        # Create clickable area
        toggle_rect = pygame.Rect(x + 300, y, toggle_width + 50, toggle_height + 10)
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and toggle_rect.collidepoint(mouse_pos):
            on_toggle()
            return True
        return False

    def draw_setting_dropdown(self, label, x, y, value, options, on_change):
        """Draw a dropdown setting control."""
        # Draw label
        label_text = info_font.render(label, True, (255, 255, 255))
        self.screen.blit(label_text, (x, y))
        
        # Draw current value
        value_bg = pygame.Rect(x + 300, y, 150, 30)
        pygame.draw.rect(self.screen, (40, 40, 60), value_bg)
        pygame.draw.rect(self.screen, (100, 100, 150), value_bg, 1)
        
        value_text = info_font.render(value, True, (255, 255, 255))
        self.screen.blit(value_text, (x + 310, y + 5))
        
        # Draw dropdown arrow
        pygame.draw.polygon(self.screen, (200, 200, 200), 
                             [(x + 440, y + 10), (x + 430, y + 20), (x + 420, y + 10)])
        
        # Handle dropdown interaction with a mouse state check
        mouse_pos = pygame.mouse.get_pos()
        dropdown_rect = pygame.Rect(x + 300, y, 150, 30)
        if pygame.mouse.get_pressed()[0] and dropdown_rect.collidepoint(mouse_pos):
            self.show_dropdown_options(x + 300, y + 35, options, value, on_change)
            return True
        
        return False

    def show_dropdown_options(self, x, y, options, current_value, on_change):
        """Show dropdown options and handle selection."""
        # Create dropdown surface
        option_height = 30
        dropdown_height = len(options) * option_height
        dropdown = pygame.Surface((150, dropdown_height))
        dropdown.fill((50, 50, 70))
        
        # Draw options
        for i, option in enumerate(options):
            option_rect = pygame.Rect(0, i * option_height, 150, option_height)
            
            # Highlight current value
            if option == current_value:
                pygame.draw.rect(dropdown, (70, 70, 100), option_rect)
            
            # Highlight hovered option
            mouse_pos = pygame.mouse.get_pos()
            screen_rect = pygame.Rect(x, y + i * option_height, 150, option_height)
            if screen_rect.collidepoint(mouse_pos):
                pygame.draw.rect(dropdown, (90, 90, 120), option_rect)
            
            # Draw option text
            option_text = info_font.render(option, True, (255, 255, 255))
            dropdown.blit(option_text, (10, i * option_height + 5))
        
        # Draw border
        pygame.draw.rect(dropdown, (100, 100, 150), pygame.Rect(0, 0, 150, dropdown_height), 1)
        
        # Blit dropdown to screen
        self.screen.blit(dropdown, (x, y))
        
        # Handle option selection
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        if mouse_pressed:
            for i, option in enumerate(options):
                option_rect = pygame.Rect(x, y + i * option_height, 150, option_height)
                if option_rect.collidepoint(mouse_pos):
                    on_change(option)
                    return True
        
        return False

    def handle_settings_events(self, events):
        """Handle events in the settings screen."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.transition_to("menu")
                    return
            
            # Handle mouse events for settings controls
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check if clicking the back button
                back_btn_rect = pygame.Rect(WIDTH // 2 - 125, HEIGHT - 80, 250, 50)
                if back_btn_rect.collidepoint(mouse_pos):
                    self.transition_to("menu")
                    return
                
                # Check if clicking any settings controls
                settings_x = WIDTH // 2 - 200
                settings_y = 150
                
                # Sound volume slider
                if settings_y <= mouse_pos[1] <= settings_y + 40:
                    if settings_x + 100 <= mouse_pos[0] <= settings_x + 400:
                        new_value = (mouse_pos[0] - (settings_x + 100)) / 300
                        new_value = max(0, min(1, new_value))
                        self.update_setting("sound_volume", new_value)
                
                # Music volume slider
                if settings_y + 70 <= mouse_pos[1] <= settings_y + 110:
                    if settings_x + 100 <= mouse_pos[0] <= settings_x + 400:
                        new_value = (mouse_pos[0] - (settings_x + 100)) / 300
                        new_value = max(0, min(1, new_value))
                        self.update_setting("music_volume", new_value)
                
                # Screen shake toggle
                if settings_y + 140 <= mouse_pos[1] <= settings_y + 180:
                    if settings_x + 300 <= mouse_pos[0] <= settings_x + 360:
                        self.toggle_setting("screen_shake")
                
                # Show damage toggle
                if settings_y + 210 <= mouse_pos[1] <= settings_y + 250:
                    if settings_x + 300 <= mouse_pos[0] <= settings_x + 360:
                        self.toggle_setting("show_damage")
                
                # Difficulty dropdown
                if settings_y + 280 <= mouse_pos[1] <= settings_y + 320:
                    if settings_x + 300 <= mouse_pos[0] <= settings_x + 450:
                        self.show_dropdown_options(
                            settings_x + 300,
                            settings_y + 315,
                            ["Easy", "Normal", "Hard"],
                            self.settings["difficulty"],
                            lambda v: self.update_setting("difficulty", v)
                        )

    
    def toggle_setting(self, setting_name):
        """Toggle a boolean setting."""
        if setting_name in self.settings and isinstance(self.settings[setting_name], bool):
            self.settings[setting_name] = not self.settings[setting_name]

    def apply_camera_shake(self, intensity=5):
        """Apply a subtle camera shake effect."""
        if not self.settings.get('screen_shake', True):
            return
            
        # Only apply shake with 30% probability to make it less frequent
        if random.random() < 0.3:
            # Reduce intensity and make it more subtle
            shake_x = random.randint(-intensity//2, intensity//2)
            shake_y = random.randint(-intensity//2, intensity//2)
            self.screen_offset = (shake_x, shake_y)
        else:
            self.screen_offset = (0, 0)

    def run(self):
        """Main game loop."""
        running = True
        while running:
            # Calculate delta time
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_frame_time) / 1000.0  # Convert to seconds
            self.last_frame_time = current_time
            
            # Handle events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
            
            # Handle game state
            self.handle_state(events, dt)
            
            # Update display
            pygame.display.flip()
            
            # Cap the frame rate
            self.clock.tick(self.FPS)
        
        # Clean up and quit
        pygame.quit()

    def handle_state(self, events, dt):
        """Handle the current game state."""
        # Handle state transitions
        if self.fading_out or self.fading_in:
            self.handle_transition()
            return
            
        # Handle current state
        if self.current_state == "menu":
            self.handle_menu(events, dt)
        elif self.current_state == "gameplay":
            self.handle_gameplay(events, dt)
        elif self.current_state == "pause":
            self.handle_pause(events, dt)
        elif self.current_state == "settings":
            self.handle_settings(events, dt)
        elif self.current_state == "game_over":
            self.handle_game_over(events, dt)

    def handle_menu(self, events, dt):
        """Handle the menu state."""
        # Draw menu background
        self.draw_menu_background(dt)
        
        # Draw game title
        title_text = self.font_xl.render("CODEBREAK", True, NEON_BLUE)
        title_shadow = self.font_xl.render("CODEBREAK", True, NEON_PINK)
        shadow_pos = (WIDTH // 2 - title_shadow.get_width() // 2 + 3, 
                     100 + 3)
        title_pos = (WIDTH // 2 - title_text.get_width() // 2, 100)
        self.screen.blit(title_shadow, shadow_pos)
        self.screen.blit(title_text, title_pos)
        
        # Draw subtitle
        subtitle = self.font_md.render("CYBER SURVIVAL", True, WHITE)
        subtitle_pos = (WIDTH // 2 - subtitle.get_width() // 2, 160)
        self.screen.blit(subtitle, subtitle_pos)
        
        # Update and draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            button.update(mouse_pos)
            button.draw(self.screen, self.font_md)
        
        # Handle button events
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in self.menu_buttons:
                    if button.handle_event(event):
                        break
        
        # Draw version info
        version_text = self.font_sm.render("v0.1", True, GRAY)
        self.screen.blit(version_text, (WIDTH - version_text.get_width() - 10, 
                                      HEIGHT - version_text.get_height() - 10))

    def handle_pause(self, events, dt):
        """Handle the pause state."""
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause title
        title_text = self.font_lg.render("PAUSED", True, NEON_BLUE)
        title_pos = (WIDTH // 2 - title_text.get_width() // 2, 150)
        self.screen.blit(title_text, title_pos)
        
        # Update and draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.pause_buttons:
            button.update(mouse_pos)
            button.draw(self.screen, self.font_md)
        
        # Handle button events
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in self.pause_buttons:
                    if button.handle_event(event):
                        break
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.transition_to("gameplay")

    def handle_game_over(self, events, dt):
        """Handle the game over state."""
        # Draw background
        self.draw_menu_background(dt)
        
        # Draw game over title
        title_text = self.font_xl.render("GAME OVER", True, NEON_RED)
        title_pos = (WIDTH // 2 - title_text.get_width() // 2, 150)
        self.screen.blit(title_text, title_pos)
        
        # Draw score
        score_text = self.font_md.render(f"SCORE: {self.score}", True, WHITE)
        score_pos = (WIDTH // 2 - score_text.get_width() // 2, 220)
        self.screen.blit(score_text, score_pos)
        
        # Draw survival time
        minutes = int(self.survival_time // 60)
        seconds = int(self.survival_time % 60)
        time_text = self.font_md.render(f"SURVIVAL TIME: {minutes:02d}:{seconds:02d}", 
                                       True, WHITE)
        time_pos = (WIDTH // 2 - time_text.get_width() // 2, 260)
        self.screen.blit(time_text, time_pos)
        
        # Update and draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.game_over_buttons:
            button.update(mouse_pos)
            button.draw(self.screen, self.font_md)
        
        # Handle button events
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in self.game_over_buttons:
                    if button.handle_event(event):
                        break

    def handle_settings(self, events, dt):
        """Handle the settings state."""
        # Draw animated background
        self.draw_menu_background(dt)
        
        # Draw settings title
        title_text = self.font_lg.render("SETTINGS", True, NEON_BLUE)
        title_pos = (WIDTH // 2 - title_text.get_width() // 2, 80)
        self.screen.blit(title_text, title_pos)
        
        # Update and draw settings controls
        mouse_pos = pygame.mouse.get_pos()
        for control in self.settings_controls:
            control.update(mouse_pos)
            control.draw(self.screen, self.font_md)
        
        # Handle control events
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
                for control in self.settings_controls:
                    if control.handle_event(event):
                        break
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.transition_to("menu")
                
        # Show settings saved message if needed
        # Implement if needed

    def draw_menu_background(self, dt):
        """Draw animated cyberpunk background for menus."""
        # Fill background
        self.screen.fill(BG_COLOR)
        
        # Draw perspective grid
        self.grid_offset_y = (self.grid_offset_y + 30 * dt) % 30
        grid_spacing = 30
        vanishing_point_y = HEIGHT // 2
        
        # Draw horizontal grid lines
        for y in range(int(self.grid_offset_y), HEIGHT, grid_spacing):
            line_width = max(1, int(3 * (y / HEIGHT)))
            perspective = 0.3 + 0.7 * (y / HEIGHT)
            x1 = WIDTH // 2 - int(WIDTH * 0.5 * perspective)
            x2 = WIDTH // 2 + int(WIDTH * 0.5 * perspective)
            pygame.draw.line(self.screen, NEON_BLUE, (x1, y), (x2, y), line_width)
        
        # Draw vertical grid lines
        vanishing_point_x = WIDTH // 2
        num_lines = 20
        for i in range(num_lines):
            angle = i * (math.pi / num_lines)
            x = vanishing_point_x + int(WIDTH * math.cos(angle))
            y = vanishing_point_y + int(HEIGHT * math.sin(angle))
            pygame.draw.line(self.screen, NEON_BLUE, (vanishing_point_x, vanishing_point_y), 
                            (x, y), 1)
        
        # Add floating data particles
        if len(self.bg_particles) < 50:
            if random.random() < 0.1:
                particle = {
                    "x": random.randint(0, WIDTH),
                    "y": random.randint(0, HEIGHT),
                    "size": random.randint(2, 6),
                    "color": random.choice([NEON_BLUE, NEON_PINK, NEON_GREEN]),
                    "speed": random.uniform(10, 30),
                    "direction": random.uniform(0, 2 * math.pi)
                }
                self.bg_particles.append(particle)
        
        # Update and draw particles
        for particle in self.bg_particles[:]:
            # Move particle
            particle["x"] += particle["speed"] * dt * math.cos(particle["direction"])
            particle["y"] += particle["speed"] * dt * math.sin(particle["direction"])
            
            # Remove if off-screen
            if (particle["x"] < 0 or particle["x"] > WIDTH or 
                particle["y"] < 0 or particle["y"] > HEIGHT):
                self.bg_particles.remove(particle)
                continue
                
            # Draw particle
            pygame.draw.circle(self.screen, particle["color"], 
                              (int(particle["x"]), int(particle["y"])), 
                              particle["size"])

    def handle_transition(self):
        """Handle state transitions with fade effect."""
        if self.fading_out:
            # Increment transition timer
            self.transition_timer += 1
            
            # Calculate alpha
            alpha = min(255, int(255 * (self.transition_timer / self.transition_duration)))
            
            # Draw fade overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            self.screen.blit(overlay, (0, 0))
            
            # Check if fade out is complete
            if self.transition_timer >= self.transition_duration:
                self.fading_out = False
                self.fading_in = True
                self.transition_timer = 0
                self.current_state = self.next_state
                
                # Initialize new state if needed
                if self.current_state == "gameplay" and not self.player:
                    self.initialize_game_world()
                
        elif self.fading_in:
            # Increment transition timer
            self.transition_timer += 1
            
            # Calculate alpha
            alpha = max(0, int(255 * (1 - self.transition_timer / self.transition_duration)))
            
            # Draw fade overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            self.screen.blit(overlay, (0, 0))
            
            # Check if fade in is complete
            if self.transition_timer >= self.transition_duration:
                self.fading_in = False
                self.transition_timer = 0

    def transition_to(self, state):
        """Transition to a new game state."""
        if state == self.current_state:
            return
            
        self.next_state = state
        self.previous_state = self.current_state
        self.fading_out = True
        self.transition_timer = 0
        
        # Play transition sound
        self.effects.play_sound("menu_select")


    def update_setting(self, setting, value):
        """Update a game setting."""
        self.settings[setting] = value
        
        # Apply setting changes
        if setting == "sound_volume":
            self.effects.set_volume(value)
        
        # Save settings
        self.save_settings()

    def save_settings(self):
        """Save settings to file."""
        try:
            with open("settings.json", "w") as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        """Load settings from file."""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    loaded_settings = json.load(f)
                    # Update settings, keeping defaults for any missing keys
                    for key, value in loaded_settings.items():
                        self.settings[key] = value
        except Exception as e:
            print(f"Error loading settings: {e}")

    def restart_game(self):
        """Restart the game."""
        self.score = 0
        self.survival_time = 0
        self.wave_number = 0
        self.enemies = []
        self.resources = []
        self.power_ups = []
        self.effects_list = []
        self.transition_to("gameplay")

    def initialize_game_world(self):
        """Initialize the game world and player."""
        # Create world generator
        self.world_generator = WorldGenerator(WIDTH, HEIGHT, TILE_SIZE)
        
        # Reset game metrics
        self.score = 0
        self.survival_time = 0
        self.wave_number = 0
        
        # Clear game objects
        self.enemies = []
        self.resources = []
        self.power_ups = []
        self.effects_list = []
        
        # Load sprites
        self.load_sprites()
        
        # Create player at center of screen
        if not self.player_sprite_sheet:
            # Create a placeholder sprite
            player_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            player_surface.fill((0, 200, 0))  # Green square
            pygame.draw.circle(player_surface, (255, 255, 255), 
                              (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 3)
            self.player_sprite_sheet = player_surface
        
        # Create player
        self.player = Player(self.player_sprite_sheet, 
                            WIDTH // 2 - TILE_SIZE // 2, 
                            HEIGHT // 2 - TILE_SIZE // 2)
        
        # Initialize player attributes
        self.player.health = 100
        self.player.max_health = 100
        self.player.energy = 100
        self.player.max_energy = 100
        self.player.is_dashing = False
        
        # Initialize player inventory with DEBUG resources for testing
        # Comment these out when testing resource collection
        self.player.inventory = {
            "code_fragments": 10,  # DEBUG: Add some resources for testing crafting
            "energy_cores": 5,     # DEBUG: Add some resources for testing crafting
            "data_shards": 3       # DEBUG: Add some resources for testing crafting
        }
        
        # Reset crafting menu state
        self.show_crafting = False
        
        # Spawn initial resources (increased amount)
        self.spawn_resources(10)  # Spawn resources in the world
        
        # Debug print available recipes and inventory
        print("DEBUG: Player inventory initialized with:")
        for resource, amount in self.player.inventory.items():
            print(f"  {resource}: {amount}")
        
        print("DEBUG: Available crafting recipes:")
        for item_name, recipe in self.player.crafting_recipes.items():
            print(f"  {item_name}: {recipe}")
        
        # Start first wave
        self.start_new_wave()

    def load_sprites(self):
        """Load all game sprites."""
        # Object sprites
        object_types = ["console", "crate", "terminal", "debris"]
        for obj_type in object_types:
            # Create placeholder sprites
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # Use different colors for different object types
            color = {
                "console": (0, 255, 255),  # Cyan
                "crate": (139, 69, 19),    # Brown
                "terminal": (0, 255, 0),   # Green
                "debris": (128, 128, 128)  # Gray
            }.get(obj_type, (255, 255, 255))
            
            surface.fill(color)
            self.object_sprites[obj_type] = surface
        
        # Resource sprites
        resource_types = ["code_fragments", "energy_cores", "data_shards"]
        for res_type in resource_types:
            try:
                # Load resource image (single image, not spritesheet)
                sprite_path = f"spritesheets/resources/{res_type}.png"
                image = pygame.image.load(sprite_path).convert_alpha()
                
                # Verify dimensions (single 48x48 image)
                expected_size = 48
                
                if image.get_width() != expected_size or image.get_height() != expected_size:
                    print(f"Warning: Resource image dimensions incorrect for {res_type}. Expected {expected_size}x{expected_size}, got {image.get_width()}x{image.get_height()}")
                    raise ValueError("Invalid dimensions")
                    
                # Store the image
                self.resource_sprites[res_type] = image
                
            except (pygame.error, FileNotFoundError, ValueError) as e:
                print(f"Error loading resource image for {res_type}: {e}")
                # Create fallback sprite (48x48)
                surface = pygame.Surface((48, 48), pygame.SRCALPHA)
                color = {
                    "code_fragments": (0, 255, 255),    # Cyan
                    "energy_cores": (255, 255, 0),      # Yellow
                    "data_shards": (255, 0, 255),       # Magenta
                }.get(res_type, (255, 255, 255))
                pygame.draw.circle(surface, color, (24, 24), 20)  # Centered circle
                self.resource_sprites[res_type] = surface
        
        # Power-up sprites
        power_up_types = ["health", "energy", "shield", "damage"]
        for pu_type in power_up_types:
            # Create placeholder sprites
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # Use different colors for different power-up types
            color = {
                "health": (255, 0, 0),      # Red
                "energy": (0, 255, 255),    # Cyan
                "shield": (255, 255, 0),    # Yellow
                "damage": (255, 0, 255)     # Magenta
            }.get(pu_type, (255, 255, 255))
            
            pygame.draw.rect(surface, color, pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(surface, (255, 255, 255), 
                            pygame.Rect(2, 2, TILE_SIZE - 4, TILE_SIZE - 4), 2)
            self.power_up_sprites[pu_type] = surface
        
        # Enemy sprite sheet
        if not self.enemy_sprite_sheet:
            try:
                # Load the enemy spritesheet with the correct path
                sprite_path = "spritesheets/enemy-spritesheet.png"
                self.enemy_sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
                
                # Verify dimensions
                expected_width = 4 * 48  # 4 frames wide
                expected_height = 6 * 48  # 6 rows high
                
                if self.enemy_sprite_sheet.get_width() != expected_width or self.enemy_sprite_sheet.get_height() != expected_height:
                    print(f"Warning: Enemy spritesheet dimensions incorrect. Expected {expected_width}x{expected_height}, got {self.enemy_sprite_sheet.get_width()}x{self.enemy_sprite_sheet.get_height()}")
                
            except (pygame.error, FileNotFoundError) as e:
                print(f"Error loading enemy spritesheet: {e}")
                # Create a placeholder sprite sheet
                sheet_width = 4 * 48  # 4 columns
                sheet_height = 6 * 48  # 6 rows
                sheet = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
                
                # Fill with different colored squares for different animations
                for row in range(6):
                    for col in range(4):
                        color = (255, 0, 0)  # Default red
                        if row < 4:  # Walking animations
                            color = (255, 100 * row, 100 * row)
                        elif row == 4:  # Idle
                            color = (0, 255, 0)
                        else:  # Attack
                            color = (255, 0, 255)
                        
                        rect = pygame.Rect(col * 48, row * 48, 48, 48)
                        pygame.draw.rect(sheet, color, rect)
                        pygame.draw.rect(sheet, (255, 255, 255), rect, 2)
                
                self.enemy_sprite_sheet = sheet

        # Player sprite sheet
        if not self.player_sprite_sheet:
            try:
                # Load the player spritesheet with the correct path
                sprite_path = "spritesheets/player-spritesheet.png"
                self.player_sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
                
                # Verify dimensions
                expected_width = 4 * 48  # 4 frames wide
                expected_height = 6 * 48  # 6 rows high
                
                if self.player_sprite_sheet.get_width() != expected_width or self.player_sprite_sheet.get_height() != expected_height:
                    print(f"Warning: Player spritesheet dimensions incorrect. Expected {expected_width}x{expected_height}, got {self.player_sprite_sheet.get_width()}x{self.player_sprite_sheet.get_height()}")
                
            except (pygame.error, FileNotFoundError) as e:
                print(f"Error loading player spritesheet: {e}")
                # Create a placeholder sprite sheet
                sheet_width = 4 * 48  # 4 columns
                sheet_height = 6 * 48  # 6 rows
                sheet = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
                
                # Fill with different colored squares for different animations
                for row in range(6):
                    for col in range(4):
                        color = (0, 255, 0)  # Default green for player
                        if row < 4:  # Walking animations
                            color = (0, 255 - 50 * row, 0)  # Different shades of green for walking
                        elif row == 4:  # Idle
                            color = (0, 200, 200)  # Cyan-ish for idle
                        else:  # Attack
                            color = (200, 255, 0)  # Yellow-green for attack
                        
                        rect = pygame.Rect(col * 48, row * 48, 48, 48)
                        pygame.draw.rect(sheet, color, rect)
                        pygame.draw.rect(sheet, (255, 255, 255), rect, 2)
                
                self.player_sprite_sheet = sheet

    def play_sound(self, sound_name):
        """Play a sound by name."""
        self.effects.play_sound(sound_name)

    def update_power_ups(self, dt):
        """Update power-ups and check for collection."""
        # Initialize spawn timer if not exists
        if not hasattr(self, 'power_up_spawn_timer'):
            self.power_up_spawn_timer = 0
            self.power_up_spawn_interval = 45.0  # Spawn every 45 seconds
            self.power_up_spawn_chance = 0.7     # 70% chance to spawn when timer is up
            self.max_power_ups = 3               # Maximum number of power-ups at once
        
        # Update spawn timer
        self.power_up_spawn_timer += dt
        
        # Check if it's time to try spawning a power-up
        if self.power_up_spawn_timer >= self.power_up_spawn_interval:
            self.power_up_spawn_timer = 0
            if len(self.power_ups) < self.max_power_ups and random.random() < self.power_up_spawn_chance:
                self.spawn_random_power_up()
        
        # Update each power-up
        for power_up in self.power_ups[:]:
            # Update animation if needed
            if "pulse" in power_up:
                power_up["pulse"] += 0.05 * power_up["pulse_dir"]
                if power_up["pulse"] >= 1.0:
                    power_up["pulse"] = 1.0
                    power_up["pulse_dir"] = -1
                elif power_up["pulse"] <= 0.0:
                    power_up["pulse"] = 0.0
                    power_up["pulse_dir"] = 1
            
            # Check if expired
            if "timer" in power_up:
                power_up["timer"] += dt
                if power_up["timer"] >= power_up.get("duration", 20.0):
                    self.power_ups.remove(power_up)
        
        # Check collection
        self.check_power_up_collection()

    def spawn_random_power_up(self):
        """Spawn a power-up at a random location away from the player."""
        if not self.player:
            return
            
        # Find a suitable spawn position
        max_attempts = 10
        min_distance = 200  # Minimum distance from player
        max_distance = 400  # Maximum distance from player
        
        for _ in range(max_attempts):
            # Generate random position
            x = random.randint(100, WIDTH - 100)
            y = random.randint(100, HEIGHT - 100)
            
            # Calculate distance from player
            dist = ((self.player.x - x) ** 2 + (self.player.y - y) ** 2) ** 0.5
            
            # Check if position is valid
            if min_distance <= dist <= max_distance:
                # Spawn power-up
                self.spawn_power_up(x, y)
                
                # Add spawn effect
                self.add_effect("text", x, y - 20, 
                              text="Power-up!", 
                              color=NEON_BLUE, 
                              size=20, 
                              duration=1.0)
                return
                
        # If no suitable position found after max attempts, spawn at a default position
        edge_spawn = random.choice([
            (random.randint(100, WIDTH - 100), 100),                  # Top
            (random.randint(100, WIDTH - 100), HEIGHT - 100),        # Bottom
            (100, random.randint(100, HEIGHT - 100)),                # Left
            (WIDTH - 100, random.randint(100, HEIGHT - 100))         # Right
        ])
        self.spawn_power_up(edge_spawn[0], edge_spawn[1])

    def spawn_power_up(self, x, y):
        """Spawn a power-up at the specified position."""
        power_up_types = ["health", "energy", "shield", "damage"]
        weights = [0.4, 0.3, 0.2, 0.1]  # Probability weights
        
        # Choose random type
        power_up_type = random.choices(power_up_types, weights=weights, k=1)[0]
        
        # Create power-up
        power_up = {
            "type": power_up_type,
            "x": x,
            "y": y,
            "collected": False,
            "pulse": 0,
            "pulse_dir": 1,
            "timer": 0,
            "duration": 30.0  # 30 seconds before disappearing
        }
        
        self.power_ups.append(power_up)

    def check_power_up_collection(self):
        """Check if player has collected power-ups."""
        if not self.player:
            return
        
        # Collection radius
        collection_radius = TILE_SIZE * 1.5
        
        # Check each power-up
        for power_up in self.power_ups[:]:
            if not power_up.get("collected", False):
                # Calculate distance
                dist = ((self.player.x - power_up["x"]) ** 2 + 
                       (self.player.y - power_up["y"]) ** 2) ** 0.5
                
                if dist < collection_radius:
                    # Apply power-up effect
                    self.apply_power_up(power_up)
                    
                    # Remove power-up
                    self.power_ups.remove(power_up)
                    
                    # Play sound
                    self.play_sound("collect")

    def apply_power_up(self, power_up):
        """Apply power-up effect to player."""
        if not self.player:
            return
            
        power_up_type = power_up["type"]
        
        if power_up_type == "health":
            # Restore health
            heal_amount = 25  # Heal 25 health
            self.player.health = min(self.player.max_health, self.player.health + heal_amount)
            
            # Show text effect
            self.add_effect("text", self.player.x, self.player.y - 30, 
                           text=f"+{heal_amount} HP", color=GREEN, size=20, duration=1.0)
                           
        elif power_up_type == "energy":
            # Restore energy
            energy_amount = 30  # Restore 30 energy
            self.player.energy = min(self.player.max_energy, self.player.energy + energy_amount)
            
            # Show text effect
            self.add_effect("text", self.player.x, self.player.y - 30, 
                           text=f"+{energy_amount} ENERGY", color=NEON_BLUE, size=20, duration=1.0)
                           
        elif power_up_type == "shield":
            # Add shield
            shield_amount = 50
            if not hasattr(self.player, "shield"):
                self.player.shield = 0
            self.player.shield = min(100, self.player.shield + shield_amount)
            
            # Show text effect
            self.add_effect("text", self.player.x, self.player.y - 30, 
                           text=f"+{shield_amount} SHIELD", color=YELLOW, size=20, duration=1.0)
                           
        elif power_up_type == "damage":
            # Temporary damage boost
            # Would need to implement buff system
            # For now, just show text
            self.add_effect("text", self.player.x, self.player.y - 30, 
                           text="DAMAGE BOOST!", color=NEON_RED, size=20, duration=1.0)
        
        # Add particles for visual effect
        self.effects.create_particles(self.player.x + self.player.width // 2, 
                                     self.player.y + self.player.height // 2, 
                                     NEON_BLUE, count=20, speed=5)

    def toggle_pause(self):
        """Toggle between pause and gameplay states."""
        if self.current_state == "gameplay":
            self.transition_to("pause")
        elif self.current_state == "pause":
            self.transition_to("gameplay")

# This ensures the Game class is only instantiated when the script is run directly
if __name__ == "__main__":
    game = Game()
    game.run()
