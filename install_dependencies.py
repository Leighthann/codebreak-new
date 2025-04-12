"""
Script to install dependencies for PostgreSQL-based CodeBreak application
"""
import subprocess
import sys
import os
import time
import socket

def check_internet_connection():
    """Check if the internet is accessible"""
    try:
        # Try to connect to Google's DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def install_dependencies():
    """Install required dependencies with error handling"""
    packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg2-binary",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "asyncpg",
        "python-dotenv",
        "pyjwt",
        "requests",
        "psycopg2-binary",
        "pygame",
        "websockets"
    ]    
    python_exe = sys.executable
    
    print("Checking internet connection...")
    if not check_internet_connection():
        print("ERROR: No internet connection detected.")
        print("Please check your network settings and try again.")
        print("\nAlternative options:")
        print("1. Download the packages manually and install them offline")
        print("2. Check your firewall/proxy settings")
        print("3. Use a mobile hotspot or alternative network")
        return False
    
    print("Installing dependencies...")
    for package in packages:
        print(f"Installing {package}...")
        try:
            # First try with pip
            result = subprocess.run(
                [python_exe, "-m", "pip", "install", package],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {e}")
            print("Output:", e.stdout)
            print("Error:", e.stderr)
            print(f"\nTrying alternative installation method for {package}...")
            
            try:
                # Try with pip and additional parameters
                result = subprocess.run(
                    [python_exe, "-m", "pip", "install", "--no-cache-dir", "--trusted-host", "pypi.org", "--trusted-host", "files.pythonhosted.org", package],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"Successfully installed {package} with alternative method")
            except subprocess.CalledProcessError as e2:
                print(f"Failed to install {package}: {e2}")
                print("You may need to install this package manually or check your internet connection.")
                return False
    
    print("\nAll dependencies installed successfully!")
    return True

def setup_database_connection():
    """Create a .env file for database configuration"""
    print("Setting up database connection configuration...")
    
    # Create .env file with PostgreSQL connection details
    with open(".env", "w") as f:
        f.write("""# Database Configuration
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=codebreak_db
DATABASE_URL=postgresql+asyncpg://postgres:your-password@localhost:5432/codebreak_db
SECRET_KEY=your-secure-random-secret-key
""")
    
    print("Database configuration created. Edit .env file to update your credentials.")
    return True

if __name__ == "__main__":
    print("CodeBreak PostgreSQL Dependency Installer")
    print("=========================================")
    
    # First try installing dependencies
    if install_dependencies():
        print("\nSuccessfully installed all required packages.")
        
        # Set up database configuration
        setup_database_connection()
        
        print("\nYou can now run 'python simple_run.py' to start the application.")
        print("Make sure PostgreSQL is running and you've updated your credentials in the .env file.")
    else:
        print("\nFailed to install some dependencies.")
        print("Please resolve the issues and try running this script again.")
