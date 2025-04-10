import subprocess
import sys
import time
import os

def start_game_client(token_file=None):
    """Start a game client with an optional token file"""
    python_exe = sys.executable
    
    # If a token file is specified and it's not the auth_token.json itself, copy it
    if token_file and os.path.exists(token_file) and token_file != "auth_token.json":
        import shutil
        shutil.copy(token_file, "auth_token.json")
        print(f"Using token from {token_file}")
    
    # Start the game
    print("Starting game client...")
    subprocess.Popen([python_exe, "game.py"])

def main():
    """Test multiplayer functionality by launching multiple clients"""
    # Start server if needed (uncomment if not already running)
    # server_process = subprocess.Popen([sys.executable, "simple_run.py"])
    # print("Starting server...")
    # time.sleep(5)  # Wait for server to start
    
    # For testing, create two different login tokens or use existing ones
    # We'll assume you're using the previously created testuser123
    # and we'll create a new test user for the second player
    
    # Option 1: Use existing token for player 1
    player1_token = "auth_token.json"
    
    # Option 2: Log in as another user for player 2
    # For this we'll need to create player2_token.json
    import requests
    import json
    
    # Create a second test user if not exists
    player2_username = "testuser456"
    player2_password = "password456"
    
    # Try to register player2
    register_response = requests.post(
        "http://127.0.0.1:8000/register/user", 
        json={"username": player2_username, "password": player2_password}
    )
    
    # Log in as player2
    login_response = requests.post(
        "http://127.0.0.1:8000/token", 
        data={"username": player2_username, "password": player2_password}
    )
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        with open("player2_token.json", "w") as f:
            json.dump({
                "username": player2_username,
                "password": player2_password,
                "token": token_data["access_token"],
                "token_type": token_data["token_type"]
            }, f)
        print(f"Created token for player2 ({player2_username})")
        player2_token = "player2_token.json"
    else:
        print(f"Failed to create token for player2: {login_response.text}")
        return
    
    # Start two game clients
    print("Starting game client for player 1...")
    start_game_client(player1_token)
    
    # Wait a bit before starting the second client
    time.sleep(2)
    
    # Save original auth_token.json
    if os.path.exists("auth_token.json"):
        with open("auth_token.json", "r") as f:
            player1_data = json.load(f)
    
    # Start client for player 2
    print("Starting game client for player 2...")
    start_game_client(player2_token)
    
    # Restore player 1's token
    with open("auth_token_backup.json", "w") as f:
        json.dump(player1_data, f)
    
    print("Both game clients started. Test multiplayer functionality.")
    print("Press Ctrl+C to exit.")
    print("Once done, copy auth_token_backup.json back to auth_token.json to restore player 1's login.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting test...")

if __name__ == "__main__":
    main() 