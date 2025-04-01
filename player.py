import pygame
import random
from enemy import Enemy
from effects import GameEffects
from resource_crafting_inventory import Resource  # Import the Resource class from the appropriate module

class Player:
    def __init__(self, sprite_sheet, x, y, tile_size, speed=5):
        self.x, self.y = x, y
        self.tile_size = tile_size
        self.speed = self.tile_size // 8
        self.direction = "idle"
        self.frame_index = 0
        self.sprite_width, self.sprite_height = 48, 48
        self.width = self.sprite_width
        self.height = self.sprite_height
        self.load_animations(sprite_sheet)
        self.attacking = False
        self.attack_start_time = 0
        self.projectiles = []
        self.attack_duration = 300
        self.projectile_speed = 7
        self.health = 100
        self.max_health = 100
        self.enemies = []
        self.effects = GameEffects()
        self.last_projectile_time = 0
        self.projectile_cooldown = 500
        
        # Resource Gathering & Crafting System
        self.inventory = {"code_fragments": 0, "energy_cores": 0, "data_shards": 0}
        self.crafted_items = []
        self.resources = self.spawn_resources()

    def spawn_resources(self, num_resources=5):
        resource_types = ["code_fragments", "energy_cores", "data_shards"]
        return [Resource(random.randint(50, 750), random.randint(50, 550), random.choice(resource_types)) for _ in range(num_resources)]

    def load_animations(self, sheet):
        self.walk_right = [self.get_frame(sheet, i, 0) for i in range(4)]
        self.walk_left = [self.get_frame(sheet, i, 1) for i in range(4)]
        self.walk_up = [self.get_frame(sheet, i, 2) for i in range(4)]
        self.walk_down = [self.get_frame(sheet, i, 3) for i in range(4)]
        self.crafting = [self.get_frame(sheet, i, 4) for i in range(4)]
        self.attack = [self.get_frame(sheet, i, 5) for i in range(4)]
        self.idle = self.get_frame(sheet, 0, 0)
    
    def get_frame(self, sheet, frame, row):
        return sheet.subsurface(pygame.Rect(frame * self.sprite_width, row * self.sprite_height, self.sprite_width, self.sprite_height))
    
    def move(self, keys):
        moving = False
        if keys[pygame.K_w]: self.y -= self.speed; self.direction = "up"; moving = True
        if keys[pygame.K_s]: self.y += self.speed; self.direction = "down"; moving = True
        if keys[pygame.K_a]: self.x -= self.speed; self.direction = "left"; moving = True
        if keys[pygame.K_d]: self.x += self.speed; self.direction = "right"; moving = True
        return moving
    
    def gather_resource(self):
        for resource in self.resources:
            if not resource.collected and abs(self.x - resource.x) < 20 and abs(self.y - resource.y) < 20:
                self.inventory[resource.resource_type] += 1
                resource.collected = True
                print(f"Collected {resource.resource_type}. Total: {self.inventory[resource.resource_type]}")
    
    def craft_item(self, item_name, recipe):
        if all(self.inventory[res] >= count for res, count in recipe.items()):
            for res, count in recipe.items():
                self.inventory[res] -= count
            self.crafted_items.append(item_name)
            print(f"Crafted {item_name}!")
        else:
            print("Not enough materials!")
    
    def animate(self, moving, keys, enemies):
        """Updates sprite based on movement or actions."""
        current_time = pygame.time.get_ticks()

        if keys[pygame.K_SPACE] and not self.attacking:
            self.attacking = True
            self.attack_start_time = current_time
            self.effects.play_attack_sound()

        if keys[pygame.K_f] and current_time - self.last_projectile_time >= self.projectile_cooldown:
            self.projectiles.append({
                "x": self.x + self.sprite_width // 2,
                "y": self.y + self.sprite_height // 2,
                "dir": self.direction,
                "width": 5,
                "height": 5
            })
            self.effects.play_hit_sound()
            self.last_projectile_time = current_time

        if self.attacking:
            self.frame_index = (self.frame_index + 1) % 3
            player_sprite = self.attack[self.frame_index] if self.direction in ["right", "left"] else self.idle
            if pygame.time.get_ticks() - self.attack_start_time > self.attack_duration:
                self.attacking = False
        elif moving:
            self.frame_index = (self.frame_index + 1) % 4
            animations = {"right": self.walk_right, "left": self.walk_left, "up": self.walk_up, "down": self.walk_down}
            player_sprite = animations[self.direction][self.frame_index]
        else:
            player_sprite = self.idle

        # Update projectiles
        for projectile in self.projectiles[:]:
            directions = {"right": (self.projectile_speed, 0), "left": (-self.projectile_speed, 0), "up": (0, -self.projectile_speed), "down": (0, self.projectile_speed)}
            projectile["x"] += directions[projectile["dir"]][0]
            projectile["y"] += directions[projectile["dir"]][1]
            pygame.draw.circle(pygame.display.get_surface(), (255, 255, 255), (projectile["x"], projectile["y"]), self.tile_size // 8)

            for enemy in self.enemies:
                if enemy.collides_with(projectile):
                    enemies.remove(enemy)
                    self.projectiles.remove(projectile)
                    break

            if projectile["x"] > pygame.display.get_surface().get_width() or projectile["x"] < 0 or projectile["y"] > pygame.display.get_surface().get_height() or projectile["y"] < 0:
                self.projectiles.remove(projectile)

        # Check for resource collection
        self.gather_resource()

        return player_sprite





