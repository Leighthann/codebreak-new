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
        # Draw the red background
        pygame.draw.rect(screen, (255, 0, 0), (x, y, width, height))
        # Draw the green health fill
        pygame.draw.rect(screen, (0, 255, 0), (x, y, width * (health / max_health), height))
        
        # Display the health number as text
        font = pygame.font.Font(None, 20)  # Use a small font size
        health_text = font.render(f"{health}/{max_health}", True, (255, 255, 255))  # White text
        text_x = x + (width - health_text.get_width()) // 2  # Center the text horizontally
        text_y = y + (height - health_text.get_height()) // 2  # Center the text vertically
        screen.blit(health_text, (text_x, text_y))
