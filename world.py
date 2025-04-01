import pygame
import random
import noise

# Constants
TILE_SIZE = 32  # Size of each tile
WORLD_WIDTH, WORLD_HEIGHT = 25, 20  # Size of the world in tiles
BIOME_COLORS = {
    "forest": (34, 139, 34),  # Green for forest
    "desert": (255, 255, 0),  # Yellow for desert
    "ocean": (0, 0, 255),  # Blue for ocean
    "mountain": (139, 137, 137)  # Grey for mountains
}
TERRAIN_COLORS = {
    "grass": (0, 255, 0),
    "sand": (255, 204, 0),
    "water": (0, 0, 255),
    "rock": (139, 137, 137)
}

class WorldGenerator:
    def __init__(self):
        self.world_map = self.generate_world()
        self.world_map = []  # Example placeholder for the world map
        self.tile_size = 32  # Define tile_size with an appropriate value

    def generate_world(self):
        """Generate the world map using noise for biome generation."""
        world_map = []

        for y in range(WORLD_HEIGHT):
            row = []
            for x in range(WORLD_WIDTH):
                biome = self.get_biome(x, y)
                row.append(biome)
            world_map.append(row)
        return world_map

    def get_biome(self, x, y):
        """Determine the biome for a given position using Perlin noise."""
        noise_value = noise.pnoise2(x * 0.1, y * 0.1, octaves=6, persistence=0.5, lacunarity=2.0)
        
        # Threshold values to determine biome
        if noise_value < -0.1:
            return "ocean"
        elif noise_value < 0.3:
            return "desert"
        elif noise_value < 0.7:
            return "forest"
        else:
            return "mountain"

    def draw_world(self, screen):
        """Draw the generated world on the screen."""
        for y, row in enumerate(self.world_map):
            for x, biome in enumerate(row):
                color = BIOME_COLORS[biome]  # Select biome color
                pygame.draw.rect(screen, color, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

