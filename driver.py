#!/usr/bin/env python3
"""
CodeBreak Game - Main Launcher
This script serves as the entry point for the CodeBreak game, handling server startup
and client initialization.
"""

import os
import sys
import subprocess
import time
import argparse
import threading
import webbrowser
import signal
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_HOST = os.getenv("HOST", "127.0.0.1")  # Ensure host is a string
DEFAULT_PORT = int(os.getenv("PORT", 8000))  # Port remains an integer
SERVER_STARTUP_WAIT = 2  # seconds to wait for server to start

def check_venv_activation():
    """Check if virtual environment is properly activated and provide guidance if there are issues"""
    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    
    if not in_venv:
        print("\n====== Virtual Environment Warning ======")
        print("It appears you may not be running in an activated virtual environment.")
        print("\nIf you encountered a PowerShell execution policy error, you can:")
        print("1. Run PowerShell as administrator and execute:")
        print("   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser")
        print("\n2. Or use one of these alternative activation methods:")
        print("   - Use Command Prompt: .venv\\Scripts\\activate.bat")
        print("   - Directly run with Python: python -m driver")
        print("   - Or use: & .venv\\Scripts\\python driver.py")
        print("========================================\n")
        
        user_input = input("Continue anyway? (y/n): ")
        if user_input.lower() != "y":
            sys.exit(1)

def check_dependencies():
    """Check if all required dependencies are installed"""
    # Package name to import name mapping (for packages where they differ)
    package_import_map = {
        "python-jose": "jose",
        "python-multipart": "multipart",
        "python-dotenv": "dotenv",
    }
    
    required_packages = [
        "fastapi", "uvicorn", "motor", "python-jose", "passlib", 
        "python-multipart", "websockets", "pygame", "requests", "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Use the import name if it's in the mapping, otherwise use package name
            import_name = package_import_map.get(package, package)
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required dependencies:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_mongodb_config():
    """Check if MongoDB connection string is configured"""
    mongo_url = os.getenv("MONGO_URL")
    
    if not mongo_url:
        print("WARNING: MONGO_URL environment variable not found.")
        print("Please configure your MongoDB connection in a .env file:")
        print('MONGO_URL="mongodb+srv://username:password@cluster.mongodb.net/codebreak_db?retryWrites=true&w=majority"')
        return False
    
    return True

def check_secret_key():
    """Check if a secret key is configured for JWT authentication"""
    secret_key = os.getenv("SECRET_KEY")
    
    if not secret_key or secret_key == "your-secret-key-here":
        print("WARNING: SECRET_KEY not properly configured.")
        print("Please set a strong random string for SECRET_KEY in your .env file.")
        return False
    
    return True

def start_server(host, port, headless=False):
    """Start the FastAPI server"""
    print(f"Starting CodeBreak server on {host}:{port}...")
    
    # Prepare the command
    cmd = [sys.executable, "-m", "uvicorn", "backend.server:app", "--host", host, "--port", str(port)]
    print(f"Command to start server: {' '.join(cmd)}")
    
    if not headless:
        # Run in a new terminal window if not headless
        if sys.platform.startswith('win'):
            # Windows
            cmd = ["start", "cmd", "/k"] + cmd
            subprocess.Popen(" ".join(cmd), shell=True)
        elif sys.platform.startswith('darwin'):
            # macOS
            applescript = f'tell application "Terminal" to do script "{" ".join(cmd)}"'
            subprocess.Popen(["osascript", "-e", applescript])
        else:
            # Linux and other Unix-like systems
            term_cmd = None
            for terminal in ["gnome-terminal", "konsole", "xterm"]:
                if subprocess.call(["which", terminal], stdout=subprocess.DEVNULL) == 0:
                    if terminal == "gnome-terminal":
                        term_cmd = [terminal, "--", " ".join(cmd)]
                    else:
                        term_cmd = [terminal, "-e", " ".join(cmd)]
                    break
            
            if term_cmd:
                subprocess.Popen(term_cmd)
            else:
                # Fallback to running in the background
                print("Could not find a suitable terminal emulator. Running server in the background.")
                subprocess.Popen(cmd)
    else:
        # Run headless (same process or background)
        process = subprocess.Popen(cmd)
        print(f"Server process started with PID: {process.pid}")
        return process
    
    # Give the server some time to start up
    time.sleep(SERVER_STARTUP_WAIT)
    print("Server startup wait complete.")
    return None

def launch_login(server_url=None):
    """Launch the login page"""
    print("Starting CodeBreak login page...")
    
    # If a server URL is provided, update a temporary config file
    if server_url:
        config = {"server_url": server_url}
        with open("client_config.json", "w") as f:
            json.dump(config, f)
    
    # Start the login page
    if sys.platform.startswith('win'):
        subprocess.Popen([sys.executable, "login.py"])
    else:
        subprocess.Popen([sys.executable, "login.py"])

def open_docs(host, port):
    """Open the API documentation"""
    docs_url = f"http://{host}:{port}/docs"
    print(f"Opening API documentation: {docs_url}")
    webbrowser.open(docs_url)

def main():
    """Main function to start the application"""
    parser = argparse.ArgumentParser(description="CodeBreak Game Launcher")
    parser.add_argument("--server-only", action="store_true", help="Start only the server")
    parser.add_argument("--client-only", action="store_true", help="Start only the client")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Server host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--headless", action="store_true", help="Run server without new terminal window")
    parser.add_argument("--docs", action="store_true", help="Open API documentation in browser")
    
    args = parser.parse_args()
    
    # Check virtual environment activation 
    check_venv_activation()
    
    # Check dependencies and configuration
    if not check_dependencies():
        sys.exit(1)
    
    if not args.client_only:
        if not check_mongodb_config() or not check_secret_key():
            user_input = input("Continue anyway? (y/n): ")
            if user_input.lower() != "y":
                sys.exit(1)
    
    # Determine server URL
    server_url = f"http://{args.host}:{args.port}"
    if args.host == "0.0.0.0":
        server_url = f"http://localhost:{args.port}"  # Adjust for client connection
    
    # Start the server if requested
    server_process = None
    if not args.client_only:
        server_process = start_server(args.host, args.port, args.headless)
        print(f"Server started at {server_url}")
        
        if args.docs:
            open_docs(args.host if args.host != "0.0.0.0" else "localhost", args.port)
    
    # Start the client if requested
    if not args.server_only:
        # Give the server a moment to start before launching the client
        time.sleep(1)
        launch_login(server_url)
    
    # If headless, keep the main thread running to maintain the server
    if server_process and args.headless:
        try:
            print("Server running. Press Ctrl+C to stop.")
            while True:  # Keep the script running until interrupted
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print("\nStopping server...")
            server_process.terminate()
            server_process.wait()
            print("Server stopped.")

if __name__ == "__main__":
    main()



# Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
# .venv\scripts\activate