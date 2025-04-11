# CodeBreak Multiplayer Launcher

This launcher provides an easy way to run the CodeBreak game with multiplayer functionality.

## Features

- **All-in-one launcher**: Starts the server and game clients from a single interface
- **Multiplayer mode**: Easily start multiple game clients with different user accounts
- **Interactive menu**: Choose between single player and multiplayer modes
- **Command-line options**: Start specific components with command-line arguments

## Requirements

- Python 3.7 or higher
- PostgreSQL database server
- Required Python packages (automatically installed by the launcher)

## Quick Start

To launch the game with all features:

```
python codebreak_launcher.py
```

This will:
1. Initialize the PostgreSQL database if needed
2. Start the game server
3. Present a menu to choose between single player and multiplayer modes

## Multiplayer Mode

To directly start in multiplayer mode:

```
python codebreak_launcher.py --multiplayer
```

This will:
1. Start the server
2. Prompt for usernames and passwords for two players
3. Create the user accounts if they don't exist
4. Launch two game clients, one for each player

## Command-line Options

- `--skip-server`: Skip starting the server (use if the server is already running)
- `--multiplayer`: Start directly in multiplayer mode
- `--client-only`: Start only the client (login screen)

## How Multiplayer Works

1. The launcher starts the backend server which handles:
   - User authentication
   - Player state synchronization
   - Game world state

2. It then creates or logs in user accounts as needed

3. Game clients connect to the server via WebSockets for real-time communication

4. Players can see each other in the game world and interact

## Troubleshooting

- **Server doesn't start**: Make sure PostgreSQL is running and accessible
- **Registration fails**: Check the server output for specific error messages
- **Game clients don't connect**: Ensure the server is running on port 8000

## Manual Components

If needed, you can still start components manually:

- Start server only: `python -m uvicorn backend.server_postgres:app --host 127.0.0.1 --port 8000`
- Start login page: `python login.py`
- Start game directly: `python game.py`

## Development

To modify the launcher:
1. Edit `codebreak_launcher.py` to change behavior
2. The multiplayer implementation relies on the WebSocket endpoint in `backend/server_postgres.py` 