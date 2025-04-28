# main.py
import pygame
import os
import sys
import json
import asyncio
import websockets
import time
from datetime import datetime
from typing import Optional

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2
SESSION_FILE = "current_game.json"
CONFIG_FILE = "client_config.json"

class GameSessionManager:
    def __init__(self):
        self.config = None
        self.game_data = None
        self.last_state = None
    
    def load_config(self):
        """Load and validate client configuration"""
        if not os.path.exists(CONFIG_FILE):
            print("No config found. Please set up client_config.json")
            sys.exit(1)
        
        try:
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)
            
            # Validate required fields
            required_fields = ["token", "server_url", "username"]
            missing_fields = [field for field in required_fields if not self.config.get(field)]
            
            if missing_fields:
                print(f"Missing required fields in config: {', '.join(missing_fields)}")
                sys.exit(1)
                
            return self.config
        except json.JSONDecodeError:
            print("Invalid JSON in client_config.json")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading configuration: {str(e)}")
            sys.exit(1)
    
    def save_game_state(self, state):
        """Save current game state"""
        self.last_state = state
        try:
            with open(SESSION_FILE, "w") as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Warning: Could not save game state: {str(e)}")
    
    def load_game_state(self):
        """Load saved game state"""
        try:
            if os.path.exists(SESSION_FILE):
                with open(SESSION_FILE, "r") as f:
                    self.game_data = json.load(f)
                return self.game_data
            return None
        except Exception as e:
            print(f"Warning: Could not load game state: {str(e)}")
            return None
    
    def clear_session(self):
        """Clean up session data"""
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except Exception as e:
                print(f"Warning: Could not clear session: {str(e)}")

class GameConnection:
    def __init__(self, config):
        self.config = config
        self.ws = None
        self.connected = False
        self.last_ping = time.time()
    
    async def connect(self):
        """Connect to game server with retry mechanism"""
        for attempt in range(MAX_RETRIES):
            try:
                ws_url = f"ws://{self.config['server_url'].replace('http://', '')}/ws/{self.config['username']}"
                self.ws = await websockets.connect(
                    ws_url,
                    extra_headers={"Authorization": f"Bearer {self.config['token']}"}
                )
                self.connected = True
                print("Successfully connected to game server")
                return True
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"Connection attempt {attempt + 1} failed: {str(e)}")
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    print(f"Failed to connect after {MAX_RETRIES} attempts")
                    return False
    
    async def disconnect(self):
        """Gracefully disconnect from server"""
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            finally:
                self.ws = None
                self.connected = False

async def main():
    # Initialize session manager
    session_manager = GameSessionManager()
    config = session_manager.load_config()
    
    # Initialize game connection
    connection = GameConnection(config)
    
    # Try to connect to server
    if not await connection.connect():
        print("Could not establish connection to game server")
        sys.exit(1)
    
    try:
        # Load or create game session
        game_data = session_manager.load_game_state()
        if not game_data:
            print("No active game session found")
            # Here you would typically show the game menu/launcher UI
            # For now, we'll exit
            await connection.disconnect()
            sys.exit(0)
        
        # Initialize pygame
        pygame.init()
        
        # Import game class here to avoid circular imports
        from game import Game
        
        # Initialize and run the game with session data
        game = Game()
        game.game_id = game_data.get("game_id")
        game.is_host = game_data.get("is_host", False)
        game.connection = connection
        
        print(f"Starting game with session ID: {game.game_id}, Host: {game.is_host}")
        
        # Run the game
        await game.run()
    
    except Exception as e:
        print(f"Game error: {str(e)}")
        # Try to save game state before exiting
        if hasattr(game, 'get_state'):
            session_manager.save_game_state(game.get_state())
    
    finally:
        # Cleanup
        await connection.disconnect()
        session_manager.clear_session()
        pygame.quit()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGame terminated by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        sys.exit(0)
