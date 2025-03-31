import pygame

class GameEffects:
    def __init__(self):
        pygame.mixer.init()
        self.attack_sound = pygame.mixer.Sound("laser.wav")
        self.hit_sound = pygame.mixer.Sound("sword.wav")

    def play_attack_sound(self):
        self.attack_sound.play()

    def play_hit_sound(self):
        self.hit_sound.play()
