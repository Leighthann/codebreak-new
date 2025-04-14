"""
Simple script to run the CodeBreak application with PostgreSQL.
"""

import subprocess
import sys
import time
import os
import webbrowser
import signal
from pathlib import Path
import importlib.util
from dotenv import load_dotenv

# Try to import psycopg2, but don't fail if not found
# This will be used to check if dependencies are installed
try:
    import psycopg2
    dependencies_installed = True
except ImportError:
    dependencies_installed = False

def check_and_install_dependencies():
    """Check if dependencies are installed and install them if needed"""
    global dependencies_installed
    
    if not dependencies_installed:
        print("Required dependencies not found. Running install_dependencies.py...")
        try:
            # Run the install_dependencies.py script
            python_exe = sys.executable
            subprocess.run([python_exe, "install_dependencies.py"], check=True)
            
            # Try to import psycopg2 again after installation
            try:
                import psycopg2
                dependencies_installed = True
                print("Dependencies installed successfully.")
                
                # Reload environment variables since .env file may have been created
                load_dotenv(override=True)
            except ImportError:
                print("Failed to install dependencies. Please run install_dependencies.py manually.")
                return False
        except subprocess.CalledProcessError:
            print("Failed to run install_dependencies.py. Please run it manually.")
            return False
    
    return dependencies_installed

# Load environment variables
load_dotenv()

print("Starting CodeBreak with PostgreSQL")

def initialize_database():
    """Initialize PostgreSQL database if needed"""
    try:
        # Database connection parameters
        DB_PARAMS = {
            "database": os.getenv("DB_NAME", "codebreak_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": "L3igh-@Ann22",  # Temporarily hardcoded for testing
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432"))
}
        print("Attempting to connect with parameters:")
        #print(password)
        #safe_params = {k: v if k != "password" else "[HIDDEN]" for k, v in DB_PARAMS.items()}
        safe_params = {k: v if k != "password" else "[HIDDEN]" for k, v in DB_PARAMS.items()}
        print(safe_params)
        
        # Connect to default postgres database
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True  # For creating database
        cursor = conn.cursor()
        
        db_name = os.getenv("DB_NAME", "codebreak_db")
        
        # Check if our database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating {db_name} database...")
            cursor.execute(f"CREATE DATABASE {db_name}")
        else:
            print(f"Database {db_name} already exists.")
        
        cursor.close()
        conn.close()
        
        # Connect to our database
        DB_PARAMS["database"] = db_name
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Create users table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create players table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                health INTEGER DEFAULT 100,
                x INTEGER DEFAULT 0,
                y INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                inventory JSONB DEFAULT '{"code_fragments": 0, "energy_cores": 0, "data_shards": 0}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create other tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                score INTEGER NOT NULL,
                wave_reached INTEGER DEFAULT 0,
                survival_time REAL DEFAULT 0,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(50) UNIQUE NOT NULL,
                username VARCHAR(50) NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP NULL,
                score INTEGER DEFAULT 0,
                enemies_defeated INTEGER DEFAULT 0,
                waves_completed INTEGER DEFAULT 0
            )
        """)
        
        # Create or update items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                name VARCHAR(50) NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                value INTEGER DEFAULT 1,
                username VARCHAR(50) REFERENCES users(username),
                spawned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                collected_at TIMESTAMP NULL
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def main():
    # Check and install dependencies first
    if not check_and_install_dependencies():
        print("Cannot continue without required dependencies.")
        user_input = input("Do you want to try continuing anyway? (y/n): ")
        if user_input.lower() != 'y':
            print("Exiting application.")
            return
    
    # Check PostgreSQL connection and initialize database
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        if initialize_database():
            break
        
        retry_count += 1
        if retry_count < max_retries:
            print(f"Retrying database initialization ({retry_count}/{max_retries})...")
            time.sleep(2)
    
    if retry_count >= max_retries:
        print("Failed to initialize database after multiple attempts.")
        print("Please make sure PostgreSQL is running and check your credentials.")
        
        user_input = input("Do you want to continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            print("Exiting application.")
            return
    
    # Determine command to start server
    python_exe = sys.executable
    
    print("Starting server...")
    
    # Start the server process
    server_cmd = [
        python_exe, 
        "-m", "uvicorn", 
        "server_postgres:app",  # Use PostgreSQL-compatible server
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