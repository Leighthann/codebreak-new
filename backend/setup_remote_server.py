#!/usr/bin/env python3
"""
Remote Server Setup Utility for CodeBreak

This script helps you configure your game to connect to a remote server.
It updates the necessary configuration files and tests the connection.
"""

import os
import sys
import json
import requests
import time
from server_config import save_server_config, load_server_config

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the script header."""
    clear_screen()
    print("=" * 80)
    print(" " * 25 + "CODEBREAK REMOTE SERVER SETUP")
    print("=" * 80)
    print("\nThis utility will help you configure your game to connect to a remote server.\n")

def test_server_connection(server_url):
    """Test the connection to the server."""
    print(f"Testing connection to {server_url}...")
    try:
        response = requests.get(f"{server_url}/", timeout=5)
        if response.status_code == 200:
            print("✓ Connection successful!")
            return True
        else:
            print(f"✗ Connection failed with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Connection error: Could not connect to the server.")
        return False
    except requests.exceptions.Timeout:
        print("✗ Connection timeout: The server took too long to respond.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request error: {e}")
        return False

def setup_remote_server():
    """Run the setup process."""
    print_header()
    
    # Load current configuration
    current_config = load_server_config()
    current_url = current_config.get("server_url", "http://3.130.249.194:8000")
    
    print(f"Current server URL: {current_url}\n")
    
    # Get new server URL
    new_url = input("Enter the new server URL (or press Enter to keep current): ")
    if not new_url:
        new_url = current_url
    
    # Make sure URL has correct format
    if not new_url.startswith("http://") and not new_url.startswith("https://"):
        new_url = "http://" + new_url
    if not ':' in new_url.split('/')[-1]:
        new_url = new_url.rstrip('/') + ':8000'
    
    # Test connection
    if test_server_connection(new_url):
        # Save configuration
        save_server_config(new_url)
        print("\nConfiguration saved successfully!")
        print(f"The game will now connect to: {new_url}")
    else:
        print("\nWarning: Could not connect to the server.")
        confirm = input("Do you want to save this configuration anyway? (y/n): ")
        if confirm.lower() == 'y':
            save_server_config(new_url)
            print("\nConfiguration saved despite connection issues.")
        else:
            print("\nConfiguration not saved. Using previous settings.")
    
    print("\nSetup complete. Press Enter to exit.")
    input()

if __name__ == "__main__":
    setup_remote_server() 