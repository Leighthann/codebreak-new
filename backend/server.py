from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import uuid
from datetime import datetime, timedelta
import jwt  # Import the jwt module for token decoding

# uvicorn backend.server:app --host 127.0.0.1 --port 8000 --log-level debug
# Define a secret key for JWT token encoding/decoding
SECRET_KEY = "your-secure-random-secret-key"
ALGORITHM = "HS256"

# Import database models and functions
from backend.db import (
    PlayerModel, LeaderboardEntry, GameSession, Item,
    get_player, create_or_update_player, update_player_position,
    add_to_leaderboard, get_top_leaderboard, record_game_session,
    spawn_item, collect_item, create_indexes, db
)

# Import authentication
from backend.auth import (
    Token, UserInDB, get_password_hash, authenticate_user, 
    create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(title="CodeBreak Game API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create User Model
class UserCreate(BaseModel):
    username: str
    password: str

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        # Notify all users that a new player has connected
        await self.broadcast({
            "event": "player_joined",
            "username": username,
            "timestamp": datetime.now().isoformat()
        })
        
    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
            
    async def send_personal_message(self, message: Dict, username: str):
        if username in self.active_connections:
            await self.active_connections[username].send_json(message)
            
    async def broadcast(self, message: Dict, exclude: Optional[str] = None):
        for username, connection in list(self.active_connections.items()):
            if exclude is None or username != exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to {username}: {e}")
                    self.disconnect(username)

manager = ConnectionManager()

# Routes
@app.on_event("startup")
async def startup_event():
    # Create database indexes
    await create_indexes()

# Authentication routes
@app.post("/register/user", response_model=dict)
async def register_user(user: UserCreate):
    """Register a new user with username and password"""
    # Check if username already exists
    existing_user = await db["users"].find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "username": user.username,
        "hashed_password": hashed_password,
        "created_at": datetime.now()
    }
    
    result = await db["users"].insert_one(user_dict)
    
    # Initialize player data
    player = {
        "username": user.username,
        "health": 100,
        "x": 0, 
        "y": 0,
        "score": 0,
        "inventory": {"code_fragments": 0, "energy_cores": 0, "data_shards": 0},
        "last_login": datetime.now()
    }
    
    await create_or_update_player(player)
    
    return {"status": "success", "message": "User registered successfully"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login to get access token"""
    user = await authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Update last login
    await db["players"].update_one(
        {"username": user.username},
        {"$set": {"last_login": datetime.now()}}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Player routes
@app.post("/player/")
async def register_player(username: str = Query(...), 
                         health: int = 100, 
                         x: int = 0, 
                         y: int = 0, 
                         current_user: UserInDB = Depends(get_current_user)):
    """Register or update player game data (requires authentication)"""
    # Ensure player can only modify their own data
    if username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another player's data"
        )
    
    player = {
        "username": username,
        "health": health,
        "x": x, 
        "y": y,
        "score": 0,
        "inventory": {"code_fragments": 0, "energy_cores": 0, "data_shards": 0},
        "last_login": datetime.now()
    }
    
    result = await create_or_update_player(player)
    return {"status": "success", "message": "Player registered", "player": player}

@app.get("/players/{username}")
async def get_player_info(username: str):
    """Get a specific player by username"""
    player = await get_player(username)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Convert ObjectId to string for JSON serialization
    player["_id"] = str(player["_id"])
    return player

@app.get("/players/me")
async def get_current_player_info(current_user: UserInDB = Depends(get_current_user)):
    """Get the current authenticated player's info"""
    player = await get_player(current_user.username)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Convert ObjectId to string for JSON serialization
    player["_id"] = str(player["_id"])
    return player

@app.put("/players/position")
async def update_position(x: int, y: int, current_user: UserInDB = Depends(get_current_user)):
    """Update player position (requires authentication)"""
    result = await update_player_position(current_user.username, x, y)
    return {"status": "success", "message": "Position updated"}

# Leaderboard routes
@app.get("/leaderboard/")
async def get_leaderboard(limit: int = 10):
    """Get the global leaderboard"""
    leaderboard = await get_top_leaderboard(limit)
    for entry in leaderboard:
        entry["_id"] = str(entry["_id"])
    return {"leaderboard": leaderboard}

@app.post("/leaderboard/")
async def update_leaderboard(score: int, 
                           wave_reached: int = 0, 
                           survival_time: float = 0, 
                           current_user: UserInDB = Depends(get_current_user)):
    """Add a new entry to the leaderboard (requires authentication)"""
    entry = {
        "username": current_user.username,
        "score": score,
        "wave_reached": wave_reached,
        "survival_time": survival_time,
        "date": datetime.now()
    }
    
    result = await add_to_leaderboard(entry)
    return {"status": "success", "message": "Leaderboard updated"}

# Game session routes
@app.post("/game-sessions/")
async def start_game_session(current_user: UserInDB = Depends(get_current_user)):
    """Start a new game session (requires authentication)"""
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "username": current_user.username,
        "start_time": datetime.now(),
        "end_time": None,
        "score": 0,
        "enemies_defeated": 0,
        "waves_completed": 0
    }
    
    result = await record_game_session(session)
    return {"status": "success", "session_id": session_id}

@app.put("/game-sessions/{session_id}")
async def end_game_session(session_id: str, 
                         score: int, 
                         enemies_defeated: int, 
                         waves_completed: int,
                         current_user: UserInDB = Depends(get_current_user)):
    """End a game session and record results (requires authentication)"""
    # Verify session belongs to user
    session = await db["game_sessions"].find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["username"] != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another player's session"
        )
    
    # Update session
    result = await db["game_sessions"].update_one(
        {"session_id": session_id},
        {"$set": {
            "end_time": datetime.now(),
            "score": score,
            "enemies_defeated": enemies_defeated,
            "waves_completed": waves_completed
        }}
    )
    
    # Add to leaderboard
    leaderboard_entry = {
        "username": current_user.username,
        "score": score,
        "wave_reached": waves_completed,
        "survival_time": (datetime.now() - session["start_time"]).total_seconds(),
        "date": datetime.now()
    }
    await add_to_leaderboard(leaderboard_entry)
    
    return {"status": "success", "message": "Game session completed"}

# WebSocket endpoint
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str, token: Optional[str] = None):
    """WebSocket endpoint for real-time game updates with token-based auth"""
    # Validate token if provided
    valid_user = False
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_username = payload.get("sub")
            if token_username == username:
                valid_user = True
        except:
            pass
    
    # For development ease, allow connection without token, but in production enforce it
    # Uncomment the next line to enforce authentication
    # if not valid_user: await websocket.close(code=1008)
    
    await manager.connect(websocket, username)
    
    # Get player data and send initial state
    player = await get_player(username)
    if player:
        player["_id"] = str(player["_id"])
        await websocket.send_json({
            "event": "player_data",
            "player": player
        })
    
    # Get top players and send leaderboard
    leaderboard = await get_top_leaderboard(10)
    for entry in leaderboard:
        entry["_id"] = str(entry["_id"])
    await websocket.send_json({
        "event": "leaderboard_data",
        "leaderboard": leaderboard
    })
    
    # Get active players and send to new player
    active_players = []
    for active_username in manager.active_connections.keys():
        if active_username != username:
            active_player = await get_player(active_username)
            if active_player:
                active_player["_id"] = str(active_player["_id"])
                active_players.append(active_player)
    
    if active_players:
        await websocket.send_json({
            "event": "active_players",
            "players": active_players
        })
    
    try:
        # Start a game session
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "username": username,
            "start_time": datetime.now()
        }
        await record_game_session(session)
        
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()
            
            # Handle different action types
            if "action" in data:
                action = data["action"]
                
                if action == "update_position":
                    # Update player position in database
                    if "location" in data:
                        x = data["location"]["x"]
                        y = data["location"]["y"]
                        await update_player_position(username, x, y)
                        
                        # Broadcast position update to other players
                        await manager.broadcast({
                            "event": "player_moved",
                            "username": username,
                            "position": {"x": x, "y": y}
                        }, exclude=username)
                
                elif action == "collect_resource":
                    # Handle resource collection
                    if "item_id" in data:
                        item = await collect_item(data["item_id"], username)
                        if item:
                            await websocket.send_json({
                                "event": "resource_collected",
                                "item_type": item["type"],
                                "value": item["value"]
                            })
                            
                            # Get updated player for inventory
                            updated_player = await get_player(username)
                            await websocket.send_json({
                                "event": "inventory_updated",
                                "inventory": updated_player.get("inventory", {}) if updated_player else {}
                            })
                
                elif action == "attack":
                    # Handle player attack
                    if "target" in data:
                        target_username = data["target"]
                        damage = data.get("damage", 10)
                        
                        # Notify the target player about the attack
                        await manager.send_personal_message({
                            "event": "damaged",
                            "attacker": username,
                            "damage": damage
                        }, target_username)
                        
                        # Broadcast attack event to all players
                        await manager.broadcast({
                            "event": "player_attacked",
                            "username": username,
                            "target": target_username,
                            "damage": damage
                        })
                
                elif action == "chat_message":
                    # Handle chat messages
                    if "message" in data:
                        message = data["message"]
                        # Broadcast chat message to all players
                        await manager.broadcast({
                            "event": "chat_message",
                            "username": username,
                            "message": message,
                            "timestamp": datetime.now().isoformat()
                        })
                
                elif action == "player_died":
                    # Handle player death
                    # Update game session
                    if "session_data" in data:
                        session_data = data["session_data"]
                        await db["game_sessions"].update_one(
                            {"session_id": session_id},
                            {"$set": {
                                "end_time": datetime.now(),
                                "score": session_data.get("score", 0),
                                "enemies_defeated": session_data.get("enemies_defeated", 0),
                                "waves_completed": session_data.get("waves_completed", 0)
                            }}
                        )
                        
                        # Add to leaderboard
                        await add_to_leaderboard({
                            "username": username,
                            "score": session_data.get("score", 0),
                            "wave_reached": session_data.get("waves_completed", 0),
                            "survival_time": session_data.get("survival_time", 0),
                            "date": datetime.now()
                        })
                    
                    # Broadcast player death to all players
                    await manager.broadcast({
                        "event": "player_died",
                        "username": username
                    })
                
                # Add more action handlers as needed
    
    except WebSocketDisconnect:
        # End game session
        await db["game_sessions"].update_one(
            {"session_id": session_id},
            {"$set": {"end_time": datetime.now()}}
        )
        
        # Remove player from active connections
        manager.disconnect(username)
        
        # Notify others
        await manager.broadcast({
            "event": "player_left",
            "username": username
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)