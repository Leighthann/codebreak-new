# main.py
import pygame
from game import Game

async def main():
    # Initialize pygame
    pygame.init()
    
    # Initialize and run the game
    game = Game()
    await game.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
