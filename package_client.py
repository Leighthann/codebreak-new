import os
import zipfile
import sys
import shutil

def package_client():
    """Package the game client files into a ZIP archive for download"""
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    client_dir = os.path.join(base_dir, "client")
    zip_path = os.path.join(client_dir, "codebreak_client.zip")
    
    # Create client directory if it doesn't exist
    os.makedirs(client_dir, exist_ok=True)
    
    # Files to include in the package
    essential_files = [
        "codebreak_launcher.py",
        "login.py",
        "main.py",
        "game.py",
        "player.py",
        "enemy.py",
        "effects.py",
        "world.py",
        "worldObject.py",
        "requirements.txt",
        "simple_run.py"
        "start_game.bat"
    ]
    
    # Directories to include
    essential_dirs = [
        "fonts",
        "spritesheets",
        "sound_effects"
    ]
    
    # Create or update client config to point to the server
    client_config = os.path.join(client_dir, "client_config.json")
    with open(client_config, "w") as f:
        f.write('{\n    "server_url": "http://3.130.249.194:8000"\n}')
    
    # Create a batch file to run the game
    start_game_bat = os.path.join(client_dir, "start_game.bat")
    with open(start_game_bat, "w") as f:
        f.write('@echo off\n')
        f.write('echo Starting CodeBreak...\n')
        f.write('python codebreak_launcher.py\n')
        f.write('pause\n')
    
    # Create a simple readme file
    readme_file = os.path.join(client_dir, "README.txt")
    with open(readme_file, "w") as f:
        f.write("CODEBREAK GAME\n")
        f.write("==============\n\n")
        f.write("Installation:\n")
        f.write("1. Extract all files to a folder\n")
        f.write("2. Install Python 3.8 or newer if not already installed\n")
        f.write("3. Install required packages: pip install -r requirements.txt\n")
        f.write("4. Run the game by double-clicking start_game.bat or running python codebreak_launcher.py\n\n")
        f.write("For help or issues, contact the game administrator.\n")
    
    # Create the zip file
    print(f"Creating client package at {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the config file
        zipf.write(client_config, os.path.basename(client_config))
        
        # Add the batch file
        zipf.write(start_game_bat, os.path.basename(start_game_bat))
        
        # Add the readme
        zipf.write(readme_file, os.path.basename(readme_file))
        
        # Add essential files
        for file in essential_files:
            file_path = os.path.join(base_dir, file)
            if os.path.exists(file_path):
                print(f"Adding {file}")
                zipf.write(file_path, file)
            else:
                print(f"Warning: File not found: {file}")
        
        # Add directories
        for directory in essential_dirs:
            dir_path = os.path.join(base_dir, directory)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                print(f"Adding directory: {directory}")
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, base_dir)
                        print(f"  - {arcname}")
                        zipf.write(file_path, arcname)
            else:
                print(f"Warning: Directory not found: {directory}")
    
    # Clean up temporary files
    os.remove(client_config)
    os.remove(start_game_bat)
    os.remove(readme_file)
    
    print(f"Client package created successfully: {zip_path}")
    print(f"Size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    package_client()