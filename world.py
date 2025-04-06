import pygame
import random
from worldObject import WorldObject

class WorldGenerator:
    def __init__(self, width, height, tile_size):
        # World dimensions
        self.width = width
        self.height = height
        self.tile_size = tile_size
        
        # Map representation
        self.map = []
        self.objects = []
        
        # Grid dimensions
        self.grid_width = width // tile_size
        self.grid_height = height // tile_size
        
        # Appearance
        self.bg_color = (10, 10, 25)  # Dark blue background
        self.grid_color = (30, 30, 60)  # Slightly lighter grid lines
        
        # Generate world
        self.generate_map()
        self.place_objects()

    def generate_map(self):
        """Generate a grid-based map."""
        # Initialize empty map
        self.map = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Add random obstacles (1 = obstacle, 0 = empty)
        obstacle_chance = 0.05  # 5% chance for each cell
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Keep the center area clear for player spawn
                center_x = self.grid_width // 2
                center_y = self.grid_height // 2
                distance_from_center = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                
                if distance_from_center > 5 and random.random() < obstacle_chance:
                    self.map[y][x] = 1

    def place_objects(self):
        """Place objects in the world."""
        # Clear existing objects
        self.objects = []
        
        # Types of objects with their probabilities
        object_types = ["console", "crate", "terminal", "debris"]
        probabilities = [0.2, 0.5, 0.2, 0.1]  # Sum must be 1.0
        
        # Number of objects to place
        num_objects = random.randint(10, 20)
        
        # Place objects
        for _ in range(num_objects):
            # Random position
            x = random.randint(1, self.grid_width - 2) * self.tile_size
            y = random.randint(1, self.grid_height - 2) * self.tile_size
            
            # Random type
            obj_type = random.choices(object_types, weights=probabilities, k=1)[0]
            
            # Create object
            new_object = WorldObject(x, y, obj_type)
            self.objects.append(new_object)

    def draw_map(self, surface):
        """Draw the world map on the provided surface."""
        # Fill background
        surface.fill(self.bg_color)
        
        # Draw grid lines
        for x in range(0, self.width, self.tile_size):
            pygame.draw.line(surface, self.grid_color, (x, 0), (x, self.height))
        for y in range(0, self.height, self.tile_size):
            pygame.draw.line(surface, self.grid_color, (0, y), (self.width, y))
        
        # Draw obstacles
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.map[y][x] == 1:
                    # Draw obstacle
                    pygame.draw.rect(
                        surface, 
                        (50, 50, 80),  # Dark purple for obstacles
                        (x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                    )

    def is_valid_position(self, x, y):
        """Check if a position is valid (not an obstacle)."""
        # Convert to grid coordinates
        grid_x = x // self.tile_size
        grid_y = y // self.tile_size
        
        # Check bounds
        if (grid_x < 0 or grid_x >= self.grid_width or 
            grid_y < 0 or grid_y >= self.grid_height):
            return False
            
        # Check if cell is empty (0)
        return self.map[grid_y][grid_x] == 0

