"""
Script to install dependencies for CodeBreak game client
"""
import subprocess
import sys
import socket
import importlib.util

def check_internet_connection():
    """Check if the internet is accessible"""
    try:
        # Try to connect to Google's DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def is_package_installed(package_name):
    """Check if a package is already installed"""
    try:
        importlib.util.find_spec(package_name.replace("-", "_"))
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install required dependencies with error handling"""
    packages = [
        "pygame",
        "websockets",
        "requests",
        "python-dotenv",
        "pyperclip"
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
    
    print("Checking and installing dependencies...")
    all_installed = True
    
    for package in packages:
        if is_package_installed(package):
            print(f"{package} is already installed, skipping...")
            continue
            
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
                all_installed = False
    
    if all_installed:
        print("\nAll dependencies are installed and ready!")
    else:
        print("\nSome dependencies could not be installed.")
    return all_installed

if __name__ == "__main__":
    print("CodeBreak Dependency Installer")
    print("=============================")
    
    if install_dependencies():
        print("\nSuccessfully installed all required packages.")
    else:
        print("\nFailed to install some dependencies.")
        print("Please resolve the issues and try running this script again.")
