import random
import pygame

class WorldObjects:
    def __init__(self):
        self.objects = []

    def generate_objects(self, world_map):
        """Randomly place objects in biomes."""
        for y in range(len(world_map)):
            for x in range(len(world_map[y])):
                biome = world_map[y][x]
                if biome == "forest" and random.random() < 0.1:  # 10% chance to spawn a tree
                    self.objects.append(("tree", x, y))
                elif biome == "desert" and random.random() < 0.05:  # 5% chance for cactus
                    self.objects.append(("cactus", x, y))
                elif biome == "mountain" and random.random() < 0.05:  # 5% chance for rock
                    self.objects.append(("rock", x, y))

    def draw_objects(self, screen, tile_size):
        """Render the objects in the world."""
        for obj, x, y in self.objects:
            if obj == "tree":
                pygame.draw.circle(screen, (34, 139, 34), (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2), 10)
            elif obj == "cactus":
                pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(x * tile_size + 8, y * tile_size + 8, 16, 24))
            elif obj == "rock":
                pygame.draw.circle(screen, (139, 137, 137), (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2), 12)
