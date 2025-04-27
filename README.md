# CodeBreak

CodeBreak is a multiplayer action game where players battle against waves of enemies while collecting resources and crafting power-ups. The game features real-time multiplayer functionality, resource sharing between players, and a wave-based enemy system.

## Game Features

- **Multiplayer Gameplay**: Play with other players in real-time
- **Resource Collection**: Gather different types of resources:
  - Code Fragments
  - Energy Cores
  - Data Shards
- **Crafting System**: Craft power-ups and upgrades using collected resources
- **Wave-based Combat**: Fight against increasingly difficult waves of enemies
- **Chat System**: Communicate with other players in-game
- **Leaderboard**: Compete for high scores
- **Power-ups**: Various power-ups to enhance your gameplay

## Technical Features

- Real-time WebSocket communication for multiplayer
- PostgreSQL database for player data and leaderboards
- JWT authentication for secure player sessions
- Sprite-based animation system
- Particle effects system
- Screen shake and visual feedback effects

## Server Architecture

The game uses a client-server architecture:
- Backend: FastAPI server with PostgreSQL database
- WebSocket server for real-time communication
- Default server URL: http://3.130.249.194:8000

## Requirements

- Python 3.7+
- PostgreSQL database
- Required Python packages (install via pip):
  - pygame
  - websockets
  - fastapi
  - uvicorn
  - psycopg2-binary
  - python-jose[cryptography]
  - requests

## Installation & Setup

1. Clone the repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the PostgreSQL database
4. Configure the server URL in `server_config.json` (if needed)
5. Run the game:
   ```bash
   python main.py
   ```

## Game Controls

- **Movement**: Arrow keys or WASD
- **Attack**: Space bar
- **Chat**: T to open chat, Enter to send message
- **Crafting**: C to open crafting menu
- **Pause**: ESC

## Multiplayer Features

- Real-time player position updates
- Resource sharing between players
- Team chat system
- Player join/leave notifications
- Shared leaderboard

## Development

The game is built using:
- **Frontend**: Pygame for game rendering and input handling
- **Backend**: FastAPI for the server
- **Database**: PostgreSQL for data persistence
- **Networking**: WebSocket for real-time communication

## File Structure

- `main.py`: Game entry point
- `game.py`: Main game logic and state management
- `player.py`: Player class and movement logic
- `enemy.py`: Enemy AI and behavior
- `server_postgres.py`: Backend server implementation
- `spritesheets/`: Game graphics and animations
- `sound_effects/`: Game audio files
- `fonts/`: Game fonts

## Contributing

Feel free to contribute to the project by:
1. Forking the repository
2. Creating a feature branch
3. Committing your changes
4. Opening a pull request

## License

This project is open source and available under the MIT License. 