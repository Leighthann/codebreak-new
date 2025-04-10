import pygame
import random
import math
import os

class GameEffects:
    def __init__(self, volume=0.7):
        self.volume = volume
        
        # Initialize Pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Load sound effects
        self.sounds = {}
        self.load_sounds()
        
        # Visual effect properties
        self.particles = []
        self.text_effects = []

    def load_sounds(self):
        """Load all sound effects."""
        sound_files = {
            "attack": "sound_effects/sword.wav",
            "hit": "sound_effects/laser.wav",
            "collect": "sound_effects/collection_sound.wav",
            "level_up": "sound_effects/health_recharge.wav",
            "menu_select": "sound_effects/laser.wav",
            "game_over": "sound_effects/hurt_man.mp3"
        }
        
        # Try to load each sound
        for name, path in sound_files.items():
            try:
                if os.path.exists(path):
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(self.volume)
                    self.sounds[name] = sound
                else:
                    print(f"Warning: Sound file not found: {path}")
            except Exception as e:
                print(f"Error loading sound: {path}, {e}")
                
        # If no sounds were loaded, add empty dummy sounds
        if not self.sounds:
            print("Warning: No sounds loaded, using dummy sounds")
            dummy_sound = pygame.mixer.Sound(buffer=bytearray(100))
            dummy_sound.set_volume(0)
            for name in sound_files.keys():
                self.sounds[name] = dummy_sound

    def set_volume(self, volume):
        """Set volume for all sound effects."""
        self.volume = max(0.0, min(1.0, volume))
        
        # Update volume for all loaded sounds
        for sound in self.sounds.values():
            sound.set_volume(self.volume)

    def play_sound(self, sound_name):
        """Play a sound by name."""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def play_attack_sound(self):
        """Play the attack sound."""
        self.play_sound("attack")

    def play_hit_sound(self):
        """Play the hit sound."""
        self.play_sound("hit")

    def play_collect_sound(self):
        """Play the collect sound."""
        self.play_sound("collect")
    
    def play_game_over_sound(self):
        """Play the game over sound."""
        self.play_sound("game_over")

    def create_particles(self, x, y, color, count=10, speed=3, size_range=(1, 3), lifetime=30):
        """Create particle effect at the specified position."""
        for _ in range(count):
            angle = random.uniform(0, 2 * 3.14159)
            speed_val = random.uniform(1, speed)
            size = random.randint(size_range[0], size_range[1])
            
            self.particles.append({
                "x": x,
                "y": y,
                "dx": speed_val * math.cos(angle),
                "dy": speed_val * math.sin(angle),
                "size": size,
                "color": color,
                "lifetime": lifetime,
                "time": 0
            })

    def create_text_effect(self, text, x, y, color, size=20, duration=60, rise=True):
        """Create a floating text effect."""
        self.text_effects.append({
            "text": text,
            "x": x,
            "y": y,
            "color": color,
            "size": size,
            "duration": duration,
            "time": 0,
            "rise": rise
        })

    def update(self):
        """Update all active effects."""
        # Update particles
        for particle in self.particles[:]:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["time"] += 1
            
            # Remove expired particles
            if particle["time"] >= particle["lifetime"]:
                self.particles.remove(particle)
        
        # Update text effects
        for effect in self.text_effects[:]:
            effect["time"] += 1
            
            # Move rising text upward
            if effect["rise"]:
                effect["y"] -= 1
            
            # Remove expired effects
            if effect["time"] >= effect["duration"]:
                self.text_effects.remove(effect)

    def draw(self, surface):
        """Draw all active effects."""
        # Draw particles
        for particle in self.particles:
            # Calculate alpha (fade out)
            alpha = 255 * (1 - particle["time"] / particle["lifetime"])
            
            # Draw the particle
            pygame.draw.circle(
                surface, 
                particle["color"], 
                (int(particle["x"]), int(particle["y"])), 
                particle["size"]
            )
        
        # Draw text effects
        for effect in self.text_effects:
            # Calculate alpha (fade out)
            alpha = 255
            if effect["time"] < effect["duration"] * 0.2:
                # Fade in
                alpha = 255 * (effect["time"] / (effect["duration"] * 0.2))
            elif effect["time"] > effect["duration"] * 0.8:
                # Fade out
                alpha = 255 * (1 - (effect["time"] - effect["duration"] * 0.8) / (effect["duration"] * 0.2))
            
            # Create font and render text
            font = pygame.font.Font(None, effect["size"])
            text_surface = font.render(effect["text"], True, effect["color"])
            text_surface.set_alpha(int(alpha))
            
            # Draw centered text
            text_rect = text_surface.get_rect(center=(effect["x"], effect["y"]))
            surface.blit(text_surface, text_rect)

    def draw_health_bar(self, screen, x, y, width, height, health, max_health):
        """Draws a health bar at the given position."""
        pygame.draw.rect(screen, (255, 0, 0), (x, y, width, height))  # Red background
        pygame.draw.rect(screen, (0, 255, 0), (x, y, width * (health / max_health), height))  # Green health fill
