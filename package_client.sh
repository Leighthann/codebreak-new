#!/bin/bash

echo "Creating game client package..."

# Navigate to project directory
cd ~/codebreak-new

# Create client directory if it doesn't exist
mkdir -p client

# Create temporary files for packaging
echo '{
    "server_url": "http://3.130.249.194:8000"
}' > client/client_config.json

echo '@echo off
echo Starting CodeBreak...
python codebreak_launcher.py --skip-server
pause' > client/start_game.bat

echo "CODEBREAK GAME
==============

Installation:
1. Extract all files to a folder
2. Install Python 3.8 or newer
3. Install required packages: pip install -r requirements.txt
4. Run start_game.bat or python codebreak_launcher.py --skip-server

For help, contact the game administrator." > client/README.txt

# Create the ZIP file
echo "Creating client package..."
cd ~/codebreak-new
zip -r client/codebreak_client.zip \
    codebreak_launcher.py \
    login.py \
    main.py \
    game.py \
    player.py \
    enemy.py \
    effects.py \
    world.py \
    worldObject.py \
    requirements.txt \
    simple_run.py \
    fonts/ \
    spritesheets/ \
    sound_effects/ \
    client/client_config.json \
    client/start_game.bat \
    client/README.txt

# Clean up temporary files
rm client/client_config.json
rm client/start_game.bat
rm client/README.txt

echo "Client package created at ~/codebreak-new/client/codebreak_client.zip"
echo "Size: $(du -h ~/codebreak-new/client/codebreak_client.zip | cut -f1)"
echo "Done!"