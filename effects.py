import pygame

class GameEffects:
    def __init__(self):
        # Load sound effects
        self.attack_sound = pygame.mixer.Sound("sound_effects/sword.wav")
        self.hit_sound = pygame.mixer.Sound("sound_effects/laser.wav")

    def play_attack_sound(self):
        """Play attack sound effect."""
        self.attack_sound.play()

    def play_hit_sound(self):
        """Play hit sound effect."""
        self.hit_sound.play()

    def draw_health_bar(self, screen, x, y, width, height, health, max_health):
        """Draws a health bar at the given position."""
        pygame.draw.rect(screen, (255, 0, 0), (x, y, width, height))  # Red background
        pygame.draw.rect(screen, (0, 255, 0), (x, y, width * (health / max_health), height))  # Green health fill
