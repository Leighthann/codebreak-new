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
        
        # Equipment
        self.equipped_weapon = None
        self.equipped_tool = None
        self.crafted_items = []
        
        # Crafting recipes
        self.crafting_recipes = {
            "energy_sword": {
                "code_fragments": 5,
                "energy_cores": 3,
                "data_shards": 1,
                "stats": {"damage": 20, "speed": 1.5}
            },
            "data_shield": {
                "code_fragments": 3,
                "energy_cores": 2,
                "data_shards": 3,
                "stats": {"defense": 15, "duration": 10}
            },
            "hack_tool": {
                "code_fragments": 4,
                "energy_cores": 4,
                "data_shards": 2,
                "stats": {"range": 100, "cooldown": 5}
            }
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

    def move(self, keys, world_generator):
        """Handle player movement based on key input."""
        moving = False
        
        # Store original position in case we need to revert
        original_x = self.x
        original_y = self.y
        
        # Handle movement keys
        if keys[pygame.K_UP]:
            self.y -= self.speed
            self.direction = "up"
            moving = True
            
        if keys[pygame.K_DOWN]:
            self.y += self.speed
            self.direction = "down"
            moving = True
            
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.direction = "left"
            moving = True
            
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.direction = "right"
            moving = True
            
        # Check if new position is valid
        if moving and world_generator:
            # Create player collision rect
            player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            
            # Check collision with world blocks
            if not world_generator.is_valid_position(self.x, self.y):
                # Revert position if collision detected
                self.x = original_x
                self.y = original_y
                moving = False
                return moving
            
            # Check collision with world objects
            for obj in world_generator.objects:
                if obj.collides_with(player_rect):
                    # Revert position if collision detected
                    self.x = original_x
                    self.y = original_y
                    moving = False
                    return moving
            
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
            
            # Apply weapon damage if equipped
            self.damage = self.use_equipped_item()
        
        # Handle projectile input
        if keys[pygame.K_f] and current_time - self.last_projectile_time >= self.projectile_cooldown:
            self.fire_projectile()
            self.last_projectile_time = current_time
            
        # Handle tool input (e.g., shield)
        if keys[pygame.K_e] and self.equipped_tool:
            self.use_tool()
        
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
                self.damage = 10  # Reset to base damage
                
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

    def can_craft(self, item_name):
        """Check if player has enough resources to craft an item."""
        if item_name not in self.crafting_recipes:
            return False
            
        recipe = self.crafting_recipes[item_name]
        for resource, amount in recipe.items():
            if resource != "stats" and self.inventory.get(resource, 0) < amount:
                return False
        return True
    
    def craft_item(self, item_name):
        """Attempt to craft an item using resources."""
        print(f"DEBUG: Player.craft_item called for {item_name}")
        
        if item_name not in self.crafting_recipes:
            print(f"DEBUG: Recipe {item_name} not found in recipes: {self.crafting_recipes.keys()}")
            return False
            
        if not self.can_craft(item_name):
            print(f"DEBUG: Cannot craft {item_name}, insufficient resources")
            for resource, amount in self.crafting_recipes[item_name].items():
                if resource != "stats":
                    has_amount = self.inventory.get(resource, 0)
                    print(f"DEBUG:   {resource}: have {has_amount}, need {amount}")
            return False
            
        # Deduct resources
        recipe = self.crafting_recipes[item_name]
        for resource, amount in recipe.items():
            if resource != "stats":
                self.inventory[resource] -= amount
        
        # Create the crafted item
        crafted_item = {
            "name": item_name,
            "stats": recipe["stats"].copy(),
            "durability": 100
        }
        
        # Add to crafted items
        self.crafted_items.append(crafted_item)
        print(f"DEBUG: Added {item_name} to crafted_items: {self.crafted_items}")
        
        # Auto-equip the newly crafted item - always equip as tool regardless of type
        # This allows all items to be used with the E key
        self.equipped_tool = crafted_item
        print(f"DEBUG: Auto-equipped {item_name} as tool")
            
        return True

    def equip_item(self, item_index):
        """Equip a crafted item."""
        if 0 <= item_index < len(self.crafted_items):
            item = self.crafted_items[item_index]
            if item["name"].endswith(("sword", "blade")):
                self.equipped_weapon = item
            else:
                self.equipped_tool = item
                
    def use_equipped_item(self):
        """Use the currently equipped item."""
        if self.equipped_weapon:
            # Apply weapon effects (e.g., increased damage)
            base_damage = 10
            weapon_damage = self.equipped_weapon["stats"].get("damage", 0)
            total_damage = base_damage + weapon_damage
            
            # Decrease durability
            self.equipped_weapon["durability"] -= 1
            if self.equipped_weapon["durability"] <= 0:
                self.crafted_items.remove(self.equipped_weapon)
                self.equipped_weapon = None
                
            return total_damage
            
        return 10  # Base damage if no weapon equipped

    def use_tool(self):
        """Use the currently equipped tool."""
        print(f"DEBUG: Player.use_tool called")
        
        if not self.equipped_tool:
            print("DEBUG: No tool equipped")
            return
        
        print(f"DEBUG: Using tool: {self.equipped_tool['name']}")
            
        # Apply tool effects based on type
        if self.equipped_tool["name"] == "data_shield":
            # Apply shield effect
            shield_amount = self.equipped_tool["stats"]["defense"]
            duration = self.equipped_tool["stats"]["duration"]
            self.shield = min(100, self.shield + shield_amount)
            print(f"DEBUG: Applied data_shield, shield now at {self.shield}")
            
            # Decrease durability
            self.equipped_tool["durability"] -= 1
            print(f"DEBUG: Tool durability now: {self.equipped_tool['durability']}")
            if self.equipped_tool["durability"] <= 0:
                self.crafted_items.remove(self.equipped_tool)
                self.equipped_tool = None
                print("DEBUG: Tool broke and was removed")
        elif self.equipped_tool["name"] == "hack_tool":
            # Apply hack effect (e.g., temporarily disable nearby enemies)
            hack_range = self.equipped_tool["stats"]["range"]
            cooldown = self.equipped_tool["stats"]["cooldown"]
            
            # Temporary effect - increases energy
            self.energy = min(self.max_energy, self.energy + 20)
            print(f"DEBUG: Used hack_tool with range {hack_range}, energy now at {self.energy}")
            
            # Decrease durability
            self.equipped_tool["durability"] -= 1
            print(f"DEBUG: Tool durability now: {self.equipped_tool['durability']}")
            if self.equipped_tool["durability"] <= 0:
                self.crafted_items.remove(self.equipped_tool)
                self.equipped_tool = None
                print("DEBUG: Tool broke and was removed")
        elif self.equipped_tool["name"] == "energy_sword":
            # Apply damage boost effect
            damage_boost = self.equipped_tool["stats"]["damage"]
            speed_boost = self.equipped_tool["stats"]["speed"]
            
            # Temporary effect - provides temporary invincibility
            self.is_invincible = True
            self.invincibility_timer = pygame.time.get_ticks()
            self.invincibility_duration = 2000  # 2 seconds of invincibility
            
            print(f"DEBUG: Used energy_sword with damage {damage_boost}, invincibility activated")
            
            # Decrease durability
            self.equipped_tool["durability"] -= 1
            print(f"DEBUG: Tool durability now: {self.equipped_tool['durability']}")
            if self.equipped_tool["durability"] <= 0:
                self.crafted_items.remove(self.equipped_tool)
                self.equipped_tool = None
                print("DEBUG: Tool broke and was removed")

