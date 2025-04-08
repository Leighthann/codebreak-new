# main.py
import pygame
from game import Game

def main():
    # Initialize pygame
    pygame.init()
    
    # Initialize and run the game
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
