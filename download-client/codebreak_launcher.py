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

def start_client():
    """Start a game client using credentials from client_config.json"""
    python_exe = sys.executable
    game_process = None  # Initialize this variable
    
    # Check if client_config.json exists with credentials
    config_path = "client_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                if config.get("token") and config.get("username"):
                    # We have authentication in client_config.json
                    print(f"Using credentials from client_config.json for user: {config.get('username')}")
                    
                    # Start the game directly 
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
                        subprocess.Popen([python_exe, "main.py"])
                    
                    # Wait a moment to ensure process starts
                    time.sleep(1)
                    
                    # Verify the process started
                    if game_process and game_process.poll() is not None:
                        print("Warning: Game process may have terminated immediately")
                        return False
                    
                    return True
                else:
                    print("client_config.json found but missing token or username")
        except Exception as e:
            print(f"Error reading client_config.json: {e}")
    
    # If we get here, there's no valid client_config.json
    print("No valid credentials found in client_config.json")
    print("Starting login page...")
    
    # Use wait=True for Windows to ensure window opens properly
    if sys.platform.startswith('win'):
        process = subprocess.Popen([python_exe, "login.py"])
        print(f"Login process started with PID: {process.pid}")
    else:
        subprocess.Popen([python_exe, "login.py"])
    
    return True

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

def main():
    """Main function to run the CodeBreak game launcher with simplified flow"""
    parser = argparse.ArgumentParser(description="CodeBreak Game Launcher")
    parser.add_argument("--skip-server", action="store_true", help="Skip starting the server")
    parser.add_argument("--client-only", action="store_true", help="Start only the client (login)")
    args = parser.parse_args()
    
    try:
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
        
        # Launch client using client_config.json
        start_client()
        
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