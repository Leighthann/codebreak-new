# main.py
import pygame
from game import Game

def main():
    pygame.init()  # Ensure pygame is initialized at the start
    screen = pygame.display.set_mode((800, 600))  # Example screen size
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)  # Font for FPS display

    game = Game()

    while True:
        game.run()

        # Calculate and display FPS
        fps = int(clock.get_fps())
        fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))  # Display FPS at the top-left corner

        pygame.display.flip()
        clock.tick(60)  # Limit to 60 FPS

if __name__ == "__main__":
    main()
