print("Starting debug script")

# Try imports one by one
try:
    print("Importing subprocess...")
    import subprocess
    print("Subprocess imported successfully")
    
    print("Importing sys...")
    import sys
    print("Sys imported successfully")
    
    print("Importing time...")
    import time
    print("Time imported successfully")
    
    print("Importing os...")
    import os
    print("Os imported successfully")
    
    print("Importing webbrowser...")
    import webbrowser
    print("Webbrowser imported successfully")
    
    print("Importing signal...")
    import signal
    print("Signal imported successfully")
    
    print("Importing Path from pathlib...")
    from pathlib import Path
    print("Path imported successfully")
    
    # Now try the more complex imports
    print("Trying to start the server process...")
    python_exe = sys.executable
    print(f"Python executable: {python_exe}")
    
    # Check if the required files exist
    print("Checking if server.py exists...")
    server_path = os.path.join("backend", "server.py")
    print(f"Server path: {server_path}")
    print(f"Exists: {os.path.exists(server_path)}")
    
    print("Checking if login.py exists...")
    login_path = "login.py"
    print(f"Login path: {login_path}")
    print(f"Exists: {os.path.exists(login_path)}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("Debug script completed")