import pygame
import random

class Resource:
    def __init__(self, x, y, resource_type):
        self.x = x
        self.y = y
        self.resource_type = resource_type
        self.size = 10  # Size of the resource icon
        self.collected = False  # Whether the resource has been collected
        self.resources: list[Resource] = []

    def draw(self, screen):
        """Render the resource on the screen."""
        if not self.collected:
            color_map = {
                "code_fragments": (0, 255, 0),  # Green
                "energy_cores": (0, 0, 255),   # Blue
                "data_shards": (255, 255, 0)   # Yellow
            }
            pygame.draw.circle(screen, color_map[self.resource_type], (self.x, self.y), self.size)



class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item_name):
        if item_name in self.items:
            self.items[item_name] += 1
        else:
            self.items[item_name] = 1

    def has_items(self, required_items):
        return all(self.items.get(item, 0) >= required_items[item] for item in required_items)

    def use_items(self, required_items):
        if self.has_items(required_items):
            for item in required_items:
                self.items[item] -= required_items[item]
            return True
        return False
    
class CraftingSystem:
    def __init__(self, inventory):
        self.inventory = inventory
        self.recipes = {
            "Data Blaster": {"code_fragment": 2, "energy_core": 1},
            "Shield Module": {"data_shard": 3, "energy_core": 1}
        }

    def craft(self, item_name):
        if item_name in self.recipes and self.inventory.use_items(self.recipes[item_name]):
            print(f"Crafted {item_name}!")
            return item_name
        else:
            print("Not enough resources!")
            return None