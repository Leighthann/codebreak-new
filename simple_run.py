"""
Simple script to run the CodeBreak application without complex startup logic
"""

import subprocess
import sys
import time
import os
import webbrowser
import signal
from pathlib import Path

# MongoDB should be set up in .env file
# Make sure you've installed certifi:
# pip install certifi

print("Starting")

def main():
    # Determine command to start server
    python_exe = sys.executable
    
    print("Starting server...")
    
    # Start the server process
    server_cmd = [
        python_exe, 
        "-m", "uvicorn", 
        "backend.server:app", 
        "--host", "127.0.0.1", 
        "--port", "8000",
        "--reload"  # Includes auto-reload for development
    ]
    
    # For Windows, use this to hide the console window
    startupinfo = None
    if sys.platform.startswith('win'):
        try:
            import subprocess
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        except:
            pass
    
    # Start the server
    try:
        server_process = subprocess.Popen(
            server_cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Initialize client config file
        with open("client_config.json", "w") as f:
            f.write('{"server_url": "http://127.0.0.1:8000"}')
        
        print(f"Server starting, please wait...")
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Try to open the API docs to verify server is running
        try:
            webbrowser.open("http://127.0.0.1:8000/docs")
        except:
            print("Could not open browser automatically. If server is running, access docs at http://127.0.0.1:8000/docs")
        
        # Start the client
        print("Starting login page...")
        try:
            client_process = subprocess.Popen([python_exe, "login.py"])
            print("Login page process started.")
        except FileNotFoundError:
            print("Error: login.py not found. Ensure the file exists in the correct location.")
        except Exception as e:
            print(f"Error starting login page: {e}")
        
        # Show server output in real-time
        print("Server is running. Press Ctrl+C to stop both server and client.")
        while server_process.poll() is None:
            # Read and display server output
            if server_process.stdout:
                line = server_process.stdout.readline()
            else:
                line = ""
            if line:
                print(f"SERVER: {line.strip()}")
            
            # Also check for errors
            error = server_process.stderr.readline() if server_process.stderr else ""
            if error:
                print(f"SERVER ERROR: {error.strip()}")
            
            # Small delay to prevent high CPU usage
            time.sleep(0.1)
        
        print("Server process has ended.")
        
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Cleanup
        try:
            server_process.terminate()
            client_process.terminate()
            print("Application shutdown complete.")
        except:
            pass

if __name__ == "__main__":
    main()