import pygame
import random
from worldObject import WorldObject

class WorldGenerator:
    def __init__(self, width, height, tile_size):
        # World dimensions
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.block_height = 32  # Actual 3D height of blocks
        
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
        """Draw the world map on the provided surface with true 3D blocks."""
        # Fill background
        surface.fill(self.bg_color)
        
        # Draw grid lines
        for x in range(0, self.width, self.tile_size):
            pygame.draw.line(surface, self.grid_color, (x, 0), (x, self.height))
        for y in range(0, self.height, self.tile_size):
            pygame.draw.line(surface, self.grid_color, (0, y), (self.width, y))
        
        # Draw obstacles as 3D blocks
        # Draw from back to front to handle overlapping correctly
        for y in range(self.grid_height - 1, -1, -1):
            for x in range(self.grid_width):
                if self.map[y][x] == 1:
                    # Base coordinates
                    base_x = x * self.tile_size
                    base_y = y * self.tile_size
                    
                    # Calculate all faces of the 3D block
                    front_rect = pygame.Rect(base_x, base_y, self.tile_size, self.tile_size)
                    
                    # Top face points (drawn as a polygon)
                    top_points = [
                        (base_x, base_y),  # Front-left
                        (base_x + self.tile_size, base_y),  # Front-right
                        (base_x + self.tile_size, base_y - self.block_height),  # Back-right
                        (base_x, base_y - self.block_height)  # Back-left
                    ]
                    
                    # Left face points
                    left_points = [
                        (base_x, base_y),  # Front-top
                        (base_x, base_y + self.tile_size),  # Front-bottom
                        (base_x, base_y + self.tile_size - self.block_height),  # Back-bottom
                        (base_x, base_y - self.block_height)  # Back-top
                    ]
                    
                    # Draw faces in correct order (back to front)
                    # Top face (lighter)
                    pygame.draw.polygon(surface, (80, 80, 120), top_points)
                    
                    # Left face (medium)
                    pygame.draw.polygon(surface, (60, 60, 100), left_points)
                    
                    # Front face (normal)
                    pygame.draw.rect(surface, (50, 50, 80), front_rect)

    def is_valid_position(self, x, y):
        """Check if a position is valid (not colliding with obstacles)."""
        # Convert to grid coordinates for the corners of the player
        # Check all four corners of the player's collision box
        player_size = 32  # Assuming player size is 32x32
        corners = [
            (x, y),  # Top-left
            (x + player_size, y),  # Top-right
            (x, y + player_size),  # Bottom-left
            (x + player_size, y + player_size)  # Bottom-right
        ]
        
        for corner_x, corner_y in corners:
            grid_x = corner_x // self.tile_size
            grid_y = corner_y // self.tile_size
            
            # Check bounds
            if (grid_x < 0 or grid_x >= self.grid_width or 
                grid_y < 0 or grid_y >= self.grid_height):
                return False
            
            # If any corner intersects with a block, position is invalid
            if self.map[grid_y][grid_x] == 1:
                return False
        
        return True

    def get_block_height(self, x, y):
        """Get the height of the block at the given position."""
        grid_x = x // self.tile_size
        grid_y = y // self.tile_size
        
        if (0 <= grid_x < self.grid_width and 
            0 <= grid_y < self.grid_height and 
            self.map[grid_y][grid_x] == 1):
            return self.block_height
        return 0

