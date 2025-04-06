import pygame

from effects import GameEffects
from enemy import Enemy

# Handles player animations, movement, and actions.

# player.py
import pygame

class Player:
    def __init__(self, sprite_sheet, x, y, speed=5):
        # Position and movement
        self.x = x
        self.y = y
        self.speed = speed
        self.direction = "down"  # Default direction
        self.width = 48
        self.height = 48
        
        # Stats
        self.health = 100
        self.max_health = 100
        self.energy = 100
        self.max_energy = 100
        self.shield = 0
        
        # State
        self.attacking = False
        self.is_dashing = False
        self.is_invincible = False
        
        # Timers
        self.attack_start_time = 0
        self.attack_duration = 300  # milliseconds
        self.invincibility_timer = 0
        self.invincibility_duration = 1000  # milliseconds
        self.last_projectile_time = 0
        self.projectile_cooldown = 500  # milliseconds
        
        # Projectiles
        self.projectiles = []
        self.projectile_speed = 7
        
        # Animation
        self.sprite_width = 48
        self.sprite_height = 48
        self.frame_index = 0
        self.sprite = None
        
        # Inventory
        self.inventory = {
            "code_fragments": 0,
            "energy_cores": 0,
            "data_shards": 0
        }
        
        # Check if sprite_sheet is a single surface or a sheet
        if sprite_sheet.get_width() == self.sprite_width and sprite_sheet.get_height() == self.sprite_height:
            # It's a single sprite
            self.is_single_sprite = True
            self.sprite = sprite_sheet
            # Create placeholder animations using the single sprite
            self.walk_right = [sprite_sheet] * 4
            self.walk_left = [sprite_sheet] * 4
            self.walk_up = [sprite_sheet] * 4
            self.walk_down = [sprite_sheet] * 4
            self.crafting = [sprite_sheet] * 4
            self.attack = [sprite_sheet] * 4
            self.idle = sprite_sheet
        else:
            # It's a sprite sheet
            self.is_single_sprite = False
            # Load animations from sprite sheet
            self.load_animations(sprite_sheet)
        
        # Effects
        self.effects = GameEffects()
        
        # Active effects
        self.active_effects = {}

    def load_animations(self, sheet):
        """Load all animation frames from sprite sheet."""
        try:
            # Check if sheet is large enough for all frames
            if sheet.get_width() >= self.sprite_width * 4 and sheet.get_height() >= self.sprite_height * 6:
                # Extract animation frames
                self.walk_right = [self.get_frame(sheet, i, 0) for i in range(4)]
                self.walk_left = [self.get_frame(sheet, i, 1) for i in range(4)]
                self.walk_up = [self.get_frame(sheet, i, 2) for i in range(4)]
                self.walk_down = [self.get_frame(sheet, i, 3) for i in range(4)]
                self.crafting = [self.get_frame(sheet, i, 4) for i in range(4)]
                self.attack = [self.get_frame(sheet, i, 5) for i in range(4)]
                self.idle = self.walk_down[0]  # Default idle sprite
            else:
                # Sheet is too small, use it as a single sprite for all animations
                print("Warning: Sprite sheet too small, using as single sprite")
                self.walk_right = [sheet] * 4
                self.walk_left = [sheet] * 4
                self.walk_up = [sheet] * 4
                self.walk_down = [sheet] * 4
                self.crafting = [sheet] * 4
                self.attack = [sheet] * 4
                self.idle = sheet
        except Exception as e:
            print(f"Error loading animations: {e}")
            # Create a fallback sprite
            fallback = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
            fallback.fill((255, 0, 255))  # Magenta for visibility
            self.walk_right = [fallback] * 4
            self.walk_left = [fallback] * 4
            self.walk_up = [fallback] * 4
            self.walk_down = [fallback] * 4
            self.crafting = [fallback] * 4
            self.attack = [fallback] * 4
            self.idle = fallback
            
        # Set initial sprite
        self.sprite = self.idle

    def get_frame(self, sheet, frame, row):
        """Extract a single frame from sprite sheet."""
        return sheet.subsurface(pygame.Rect(
            frame * self.sprite_width,
            row * self.sprite_height,
            self.sprite_width,
            self.sprite_height
        ))

    def move(self, keys):
        """Handle player movement based on key input."""
        moving = False
        
        # Handle movement keys
        if keys[pygame.K_w]:
            self.y -= self.speed
            self.direction = "up"
            moving = True
            
        if keys[pygame.K_s]:
            self.y += self.speed
            self.direction = "down"
            moving = True
            
        if keys[pygame.K_a]:
            self.x -= self.speed
            self.direction = "left"
            moving = True
            
        if keys[pygame.K_d]:
            self.x += self.speed
            self.direction = "right"
            moving = True
            
        return moving

    def animate(self, moving, keys, enemies):
        """Update player animation and handle actions."""
        current_time = pygame.time.get_ticks()
        
        # Update invincibility
        if self.is_invincible and current_time - self.invincibility_timer >= self.invincibility_duration:
            self.is_invincible = False
        
        # Handle attack input
        if keys[pygame.K_SPACE] and not self.attacking:
            self.attacking = True
            self.attack_start_time = current_time
            self.effects.play_attack_sound()
        
        # Handle projectile input
        if keys[pygame.K_f] and current_time - self.last_projectile_time >= self.projectile_cooldown:
            self.fire_projectile()
            self.last_projectile_time = current_time
        
        # Choose sprite based on state
        if self.attacking:
            # Attack animation
            self.frame_index = (current_time // 100) % 3
            if self.direction in ["right", "left"]:
                self.sprite = self.attack[self.frame_index]
            else:
                # Default to idle for other directions
                self.sprite = self.idle
            
            # Check if attack is finished
            if current_time - self.attack_start_time > self.attack_duration:
                self.attacking = False
                
        elif moving:
            # Walking animation
            self.frame_index = (current_time // 150) % 4
            
            if self.direction == "right":
                self.sprite = self.walk_right[self.frame_index]
            elif self.direction == "left":
                self.sprite = self.walk_left[self.frame_index]
            elif self.direction == "up":
                self.sprite = self.walk_up[self.frame_index]
            elif self.direction == "down":
                self.sprite = self.walk_down[self.frame_index]
        else:
            # Idle animation - use direction-appropriate first frame
            if self.direction == "right":
                self.sprite = self.walk_right[0]
            elif self.direction == "left":
                self.sprite = self.walk_left[0]
            elif self.direction == "up":
                self.sprite = self.walk_up[0]
            else:  # down or default
                self.sprite = self.walk_down[0]
        
        # Update projectiles
        self.update_projectiles(enemies)
        
        return self.sprite

    def fire_projectile(self):
        """Create a new projectile in the current direction."""
        # Calculate spawn position (center of player)
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        # Create projectile
        self.projectiles.append({
            "x": center_x,
            "y": center_y,
            "dir": self.direction,
            "width": 5,
            "height": 5
        })
        
        # Play sound
        self.effects.play_hit_sound()

    def update_projectiles(self, enemies):
        """Update projectile positions and check for collisions."""
        # Get screen dimensions
        screen = pygame.display.get_surface()
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Update each projectile
        for projectile in self.projectiles[:]:
            # Move projectile
            if projectile["dir"] == "right":
                projectile["x"] += self.projectile_speed
            elif projectile["dir"] == "left":
                projectile["x"] -= self.projectile_speed
            elif projectile["dir"] == "up":
                projectile["y"] -= self.projectile_speed
            elif projectile["dir"] == "down":
                projectile["y"] += self.projectile_speed
            
            # Check if out of bounds
            if (projectile["x"] < 0 or
                projectile["x"] > screen_width or
                projectile["y"] < 0 or
                projectile["y"] > screen_height):
                # Remove projectile
                self.projectiles.remove(projectile)
                continue
            
            # Check collisions with enemies
            for enemy in enemies[:]:
                if enemy.collides_with(projectile):
                    # Remove projectile
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    break

    def decrease_health(self, amount):
        """Decrease player health if not invincible."""
        if not self.is_invincible:
            # Apply shield if available
            if self.shield > 0:
                # Absorb damage with shield
                absorbed = min(self.shield, amount)
                self.shield -= absorbed
                amount -= absorbed
            
            # Apply remaining damage to health
            if amount > 0:
                self.health = max(0, self.health - amount)
                
                # Become invincible briefly
                self.is_invincible = True
                self.invincibility_timer = pygame.time.get_ticks()
                
                return True  # Damage was dealt
                
        return False  # No damage was dealt

