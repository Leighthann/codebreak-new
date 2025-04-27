# main.py
import pygame
import os
import sys
import json
import asyncio

def check_login():
    """Check if user is logged in and redirect to login screen if not"""
    if not os.path.exists("auth_token.json"):
        print("No login token found. Redirecting to login screen...")
        import subprocess
        subprocess.Popen([sys.executable, "login.py"])
        sys.exit()
    
    # Load token to verify it exists
    try:
        with open("auth_token.json", "r") as f:
            auth_data = json.load(f)
        
        if not auth_data.get("token"):
            print("Invalid login token. Redirecting to login screen...")
            import subprocess
            subprocess.Popen([sys.executable, "login.py"])
            sys.exit()
    except:
        print("Error reading login token. Redirecting to login screen...")
        import subprocess
        subprocess.Popen([sys.executable, "login.py"])
        sys.exit()

def check_game_session():
    """Check if joining a game session or creating a new one"""
    # If no current_game.json exists, show the join game screen
    if not os.path.exists("current_game.json"):
        print("No active game session. Redirecting to join game screen...")
        import subprocess
        subprocess.Popen([sys.executable, "join_game.py"])
        sys.exit()
    
    # Load game session data
    try:
        with open("current_game.json", "r") as f:
            game_data = json.load(f)
        
        # We have valid game data, proceed to game
        return game_data
    except:
        print("Error reading game session data. Redirecting to join game screen...")
        import subprocess
        subprocess.Popen([sys.executable, "join_game.py"])
        sys.exit()

async def main():
    # Check if logged in
    check_login()
    
    # Check game session
    game_data = check_game_session()
    game_id = game_data.get("game_id")
    is_host = game_data.get("is_host", False)
    
    print(f"Starting game with session ID: {game_id}, Host: {is_host}")
    
    # Initialize pygame
    pygame.init()
    
    # Import game class here to avoid circular imports
    from game import Game
    
    # Initialize and run the game with session data
    game = Game()
    game.game_id = game_id
    game.is_host = is_host
    await game.run()
    
    # Clean up session data when exiting
    if os.path.exists("current_game.json"):
        os.remove("current_game.json")

if __name__ == "__main__":
    asyncio.run(main())
