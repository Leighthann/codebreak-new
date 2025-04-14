import subprocess
import sys
import time
import os
import threading
import json
import argparse
import socket
import requests
import signal

# Global variables
server_process = None
running = True
TOKEN_FOLDER = "loginTokens"  # Define the token folder path

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def initialize_database():
    """Initialize the database using the functions from simple_run.py"""
    try:
        from simple_run import initialize_database, check_and_install_dependencies
        print("Checking dependencies...")
        if not check_and_install_dependencies():
            print("Failed to install dependencies. Please run install_dependencies.py manually.")
            return False
        
        print("Initializing database...")
        if not initialize_database():
            print("Failed to initialize database. Please check your PostgreSQL connection.")
            return False
        
        print("Database initialized successfully.")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def start_server():
    """Start the server in a separate process"""
    global server_process
    
    python_exe = sys.executable
    
    # Check if the server is already running
    if is_port_in_use(8000):
        print("Server appears to be running already on port 8000.")
        return True
    
    print("Starting server...")
    
    # Start the server process
    server_cmd = [
        python_exe, 
        "-m", "uvicorn", 
        "backend.server_postgres:app",  # Make sure the path is correct
        "--host", "127.0.0.1", 
        "--port", "8000",
        "--reload"  # Includes auto-reload for development
    ]
    
    # For Windows, hide the console window
    startupinfo = None
    if sys.platform.startswith('win'):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        except:
            pass
    
    try:
        server_process = subprocess.Popen(
            server_cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait for server to start
        max_attempts = 10
        for attempt in range(max_attempts):
            print(f"Waiting for server to start ({attempt+1}/{max_attempts})...")
            time.sleep(2)
            
            try:
                response = requests.get("http://3.130.249.194:8000/")
                if response.status_code == 200:
                    print("Server started successfully.")
                    return True
            except:
                pass
        
        print("Server failed to start in the expected time.")
        return False
        
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

def log_server_output():
    """Thread function to log server output"""
    global server_process, running
    
    if not server_process:
        return
    
    while running and server_process.poll() is None:
        if server_process.stdout:
            line = server_process.stdout.readline()
            if line:
                print(f"SERVER: {line.strip()}")
                
        if server_process.stderr:
            line = server_process.stderr.readline()
            if line:
                print(f"SERVER ERROR: {line.strip()}")
                
        time.sleep(0.1)

def start_client(token_file=None):
    """Start a game client with an optional token file"""
    python_exe = sys.executable
    game_process = None  # Initialize this variable
    
    # If a token file is specified, copy it to auth_token.json
    if token_file:
        # If token is just a name, assume it's in the token folder
        if not os.path.dirname(token_file):
            full_token_path = os.path.join(TOKEN_FOLDER, token_file)
            if os.path.exists(full_token_path):
                token_file = full_token_path
                
        if os.path.exists(token_file) and token_file != "auth_token.json":
            import shutil
            try:
                # Make a backup of existing auth_token.json if it exists
                if os.path.exists("auth_token.json"):
                    shutil.copy("auth_token.json", "auth_token_backup.json")
                    print("Backed up existing auth_token.json")
                
                # Copy the new token file
                shutil.copy(token_file, "auth_token.json")
                print(f"Using credentials from {token_file}")
            except Exception as e:
                print(f"Error copying token file: {e}")
                return False
    
    try:
        # Start with login page if no token is provided
        if not token_file:
            print("Starting login page...")
            # Use wait=True for Windows to ensure window opens properly
            if sys.platform.startswith('win'):
                process = subprocess.Popen([python_exe, "login.py"])
                print(f"Login process started with PID: {process.pid}")
            else:
                subprocess.Popen([python_exe, "login.py"])
        else:
            # Start the game directly if token is provided
            print("Starting game client with direct launch...")
            if sys.platform.startswith('win'):
                # For Windows, use a more direct approach
                game_process = subprocess.Popen(
                    [python_exe, "main.py"], 
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                print(f"Game process started with PID: {game_process.pid}")
            else:
                # For non-Windows
                subprocess.Popen([python_exe, "game.py"])
            
            # Wait a moment to ensure process starts
            time.sleep(1)
            
            # Verify the process started
            if game_process and game_process.poll() is not None:
                print("Warning: Game process may have terminated immediately")
                return False
            
        return True
    except Exception as e:
        print(f"Error starting client: {e}")
        return False

def create_user(username, password):
    """Create a new user and return the token file path"""
    try:
       
        # Ensure token folder exists
        os.makedirs(TOKEN_FOLDER, exist_ok=True)

        server_url = "http://3.130.249.194:8000"
        if os.path.exists("client_config.json"):
            with open("client_config.json", "r") as f:
                config = json.load(f)
                server_url = config.get("server_url", server_url)
        
        print(f"Using server: {server_url}")
        print(f"Registering user: {username}")
        print(f"Payload: {{'username': '{username}', 'password': '{password}'}}")  # Log the payload
        
        # # Register user
        # register_response = requests.post(
        #     "http://3.130.249.194:8000/register/user", 
        #     json={"username": username, "password": password}
        # )
        register_response = requests.post(
            f"{server_url}/register", 
            json={"username": username, "password": password}
        )
        
        if register_response.status_code != 200:
            if "Username already registered" in register_response.text:
                print(f"User {username} already exists, trying to log in.")
            else:
                print(f"Failed to register user: {register_response.text}")
                return None
        
        # Login and get token
        login_response = requests.post(
            "http://3.130.249.194:8000/token", 
            data={"username": username, "password": password}
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token_filename = f"{username}_token.json"
            token_file = os.path.join(TOKEN_FOLDER, token_filename)
            
            with open(token_file, "w") as f:
                json.dump({
                    "username": username,
                    "password": password,
                    "token": token_data["access_token"],
                    "token_type": token_data["token_type"]
                }, f)
            
            print(f"Created token file for {username}: {token_file}")
            return token_file
        else:
            print(f"Failed to get token: {login_response.text}")
            return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def multiplayer_mode():
    """Start multiplayer mode with multiple clients"""
    # Get usernames for players
    player1 = input("Enter username for Player 1: ")
    password1 = input("Enter password for Player 1: ")
    
    player2 = input("Enter username for Player 2: ")
    password2 = input("Enter password for Player 2: ")
    
    # Create users and get token files
    print("\nCreating/logging in players...")
    player1_token = create_user(player1, password1)
    if not player1_token:
        print("Failed to create/login Player 1.")
        return
    
    player2_token = create_user(player2, password2)
    if not player2_token:
        print("Failed to create/login Player 2.")
        return
    
    # Save original auth_token.json if it exists
    if os.path.exists("auth_token.json"):
        with open("auth_token.json", "r") as f:
            try:
                original_token = json.load(f)
                backup_file = os.path.join(TOKEN_FOLDER, "auth_token_original.json")
                with open(backup_file, "w") as f2:
                    json.dump(original_token, f2)
                print(f"Backed up original auth_token.json to {backup_file}")
            except:
                pass
    
    # Start first client and confirm
    print("\nStarting game for Player 1...")
    if not start_client(player1_token):
        print("Failed to start game for Player 1.")
        return
    
    # Ask for confirmation before starting second client
    input("\nPress Enter when Player 1's game window is open to start Player 2's game...")
    
    # Start second client
    print("Starting game for Player 2...")
    if not start_client(player2_token):
        print("Failed to start game for Player 2.")
        return
    
    print("\nBoth players should now be in the game!")
    print("Players can now interact with each other in the multiplayer environment.")
    print(f"\nNote: All player tokens are stored in the '{TOKEN_FOLDER}' folder.")
    print(f"You can use them directly with: --token {player1} or --token {player2}")
    print(f"When finished, you can restore your original credentials with: --token auth_token_original")

def handle_shutdown():
    """Handle clean shutdown of all processes"""
    global server_process, running
    
    running = False
    print("\nShutting down...")
    
    if server_process:
        print("Stopping server...")
        try:
            if sys.platform.startswith('win'):
                server_process.terminate()
            else:
                server_process.send_signal(signal.SIGTERM)
            
            # Wait for server to terminate
            server_process.wait(timeout=5)
            print("Server stopped.")
        except:
            print("Server did not stop gracefully, forcing termination.")
            server_process.kill()
    
    print("Shutdown complete.")

def load_token_from_folder(token_name):
    """Helper function to load a token from the tokens folder by name"""
    if not token_name.endswith('.json'):
        token_name += '.json'
    
    token_file = os.path.join(TOKEN_FOLDER, token_name)
    
    if os.path.exists(token_file):
        return token_file
    
    return None

def list_available_tokens():
    """List all available tokens in the token folder"""
    if not os.path.exists(TOKEN_FOLDER):
        print(f"Token folder '{TOKEN_FOLDER}' does not exist.")
        return
    
    token_files = [f for f in os.listdir(TOKEN_FOLDER) if f.endswith('.json')]
    
    if not token_files:
        print(f"No token files found in '{TOKEN_FOLDER}' folder.")
        return
    
    print(f"\nAvailable tokens in '{TOKEN_FOLDER}' folder:")
    for i, token_file in enumerate(token_files, 1):
        # Try to extract username from file
        try:
            with open(os.path.join(TOKEN_FOLDER, token_file), 'r') as f:
                data = json.load(f)
                username = data.get('username', 'Unknown')
                print(f"{i}. {token_file} - User: {username}")
        except:
            print(f"{i}. {token_file}")
    
    print("\nYou can use any of these tokens with: --token <token_name>")

def main():
    """Main function to run the CodeBreak game launcher"""
    parser = argparse.ArgumentParser(description="CodeBreak Game Launcher")
    parser.add_argument("--skip-server", action="store_true", help="Skip starting the server")
    parser.add_argument("--multiplayer", action="store_true", help="Start in multiplayer mode")
    parser.add_argument("--client-only", action="store_true", help="Start only the client (login)")
    parser.add_argument("--token", help="Use a specific token file from the loginTokens folder")
    parser.add_argument("--list-tokens", action="store_true", help="List all available tokens")
    args = parser.parse_args()
    
    try:
        # Ensure token folder exists
        os.makedirs(TOKEN_FOLDER, exist_ok=True)
        
        # List tokens if requested
        if args.list_tokens:
            list_available_tokens()
            return
            
        # Initialize database if needed
        if not args.skip_server and not args.client_only:
            if not initialize_database():
                print("Database initialization failed. Continue anyway? (y/n)")
                if input().lower() != 'y':
                    return
        
        # Start server if needed
        if not args.skip_server and not args.client_only:
            if not start_server():
                print("Server failed to start. Continue anyway? (y/n)")
                if input().lower() != 'y':
                    return
            
            # Start server logging thread
            log_thread = threading.Thread(target=log_server_output)
            log_thread.daemon = True
            log_thread.start()
        
        # Create client config
        if not os.path.exists("client_config.json"):
            with open("client_config.json", "w") as f:
                f.write('{"server_url": "http://3.130.249.194:8000"}')
        
        # Choose mode
        if args.token:
            token_file = load_token_from_folder(args.token)
            if token_file:
                start_client(token_file)
            else:
                print(f"Token file '{args.token}' not found in {TOKEN_FOLDER} folder.")
                start_client()  # Fall back to login
        elif args.multiplayer:
            multiplayer_mode()
        elif args.client_only:
            start_client()
        else:
            # Interactive menu
            while True:
                print("\nCodeBreak Launcher Menu:")
                print("1. Start Single Player Game")
                print("2. Start Multiplayer Game")
                print("3. List Available Login Tokens")
                print("4. Exit")
                choice = input("Select an option (1-4): ")
                
                if choice == "1":
                    start_client()
                    break
                elif choice == "2":
                    multiplayer_mode()
                    break
                elif choice == "3":
                    list_available_tokens()
                elif choice == "4":
                    break
                else:
                    print("Invalid choice. Please try again.")
        
        # Keep the main thread alive while server is running
        if not args.skip_server and not args.client_only:
            print("\nServer is running. Press Ctrl+C to stop.")
            try:
                while server_process and server_process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                handle_shutdown()
    
    except KeyboardInterrupt:
        handle_shutdown()
    except Exception as e:
        print(f"An error occurred: {e}")
        handle_shutdown()

if __name__ == "__main__":
    main() 