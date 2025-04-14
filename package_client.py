import os
import zipfile
import sys

def package_client():
    """Package the game client for distribution"""
    os.makedirs("client", exist_ok=True)

    # Essential files
    files = [
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
        "client_config.json"
    ]

    # Essential directories
    dirs = [
        "fonts",
        "spritesheets",
        "sound_effects"
    ]

    # Create zip
    with zipfile.ZipFile("client/codebreak_client.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            if os.path.exists(file):
                zipf.write(file)
            else:
                print(f"Warning: {file} not found")

        for directory in dirs:
            if os.path.exists(directory):
                for root, _, dir_files in os.walk(directory):
                    for file in dir_files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path)
            else:
                print(f"Warning: {directory} not found")

    # Create installer batch file
    installer_path = "client/install_codebreak.bat"
    with open(installer_path, "w") as f:
        f.write("""@echo off
echo Installing CodeBreak...
python codebreak_launcher.py --register
echo Installation complete!
echo You can now launch the game from the web interface.
pause
""")

    # Add installer to zip
    with zipfile.ZipFile("client/codebreak_client.zip", "a") as zipf:
        zipf.write(installer_path, "install_codebreak.bat")
