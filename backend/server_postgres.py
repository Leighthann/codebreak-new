"""
PostgreSQL-compatible server for CodeBreak application.
This version uses direct psycopg2 connections for simplicity.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Optional, List
import json
import uuid
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
print(f"Current directory: {os.getcwd()}")
print(f"Looking for .env at: {os.path.join(os.path.dirname(__file__), '.env')}")
load_dotenv()  # Added override=True to ensure variables are loaded

# Database connection parameters - using direct password from env for debugging
#password = os.getenv("DB_PASSWORD", "")
#print(f"Password loaded from env: {'*' * len(password) if password else 'NO PASSWORD FOUND'}")

DB_PARAMS = {
    "database": os.getenv("DB_NAME", "codebreak_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": "L3igh-@Ann22",  # Temporarily hardcoded for testing
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432"))
}


print("Attempting to connect with parameters:")
safe_params = {k: v if k != "password" else "[HIDDEN]" for k, v in DB_PARAMS.items()}
print(safe_params)

# Function to get database connection with hardcoded fallback
def get_db_connection():
    """Create a new database connection"""
    try:
        connection = psycopg2.connect(**DB_PARAMS)
        return connection
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

# JWT Config
SECRET_KEY = os.getenv("SECRET_KEY", "your-secure-random-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create FastAPI app
app = FastAPI(title="CodeBreak Game API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user is None:
        raise credentials_exception
    return user

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str

class PlayerModel(BaseModel):
    username: str
    health: int = 100
    x: int = 0
    y: int = 0
    score: int = 0
    inventory: Optional[Dict] = None

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
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
                    logger.error(f"Error sending to {username}: {e}")
                    self.disconnect(username)

manager = ConnectionManager()

# Routes
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up server...")
    try:
        # Test database connection
        conn = get_db_connection()
        conn.close()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the CodeBreak API!"}

# Authentication
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Handle user login and token generation"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (form_data.username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/register/user", response_model=dict)
async def register_user(user: UserCreate):
    """Register a new user with username and password"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute("SELECT username FROM users WHERE username = %s", (user.username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Hash the password
        hashed_password = get_password_hash(user.password)
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, hashed_password, created_at) VALUES (%s, %s, %s)",
            (user.username, hashed_password, datetime.now())
        )
        
        # Initialize player data
        cursor.execute("""
            INSERT INTO players (username, health, x, y, score, inventory, created_at, last_login)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user.username, 100, 0, 0, 0,
            json.dumps({"code_fragments": 0, "energy_cores": 0, "data_shards": 0}),
            datetime.now(), datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "User registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.get("/players/{username}")
async def get_player_info(username: str):
    """Get a specific player by username"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM players WHERE username = %s", (username,))
        player = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return dict(player)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving player: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving player")

# New routes added below
@app.get("/players/me")
async def get_current_player_info(current_user = Depends(get_current_user)):
    """Get the current authenticated player's info"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM players WHERE username = %s", (current_user["username"],))
        player = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return dict(player)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving player: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving player")

@app.put("/players/position")
async def update_position(x: int, y: int, current_user = Depends(get_current_user)):
    """Update player position (requires authentication)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE players SET x = %s, y = %s, last_login = %s WHERE username = %s",
            (x, y, datetime.now(), current_user["username"])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Position updated"}
    except Exception as e:
        logger.error(f"Error updating position: {e}")
        raise HTTPException(status_code=500, detail="Failed to update position")

@app.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    """Get the global leaderboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT username, score, last_login FROM players ORDER BY score DESC LIMIT %s",
            (limit,)
        )
        leaderboard = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return {"leaderboard": leaderboard}
    except Exception as e:
        logger.error(f"Error retrieving leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve leaderboard")

@app.post("/leaderboard")
async def submit_leaderboard_score(
    score: int, 
    wave_reached: int = 0, 
    survival_time: float = 0,
    current_user = Depends(get_current_user)
):
    """Submit a new score to the leaderboard (requires authentication)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert into leaderboard table
        cursor.execute(
            """
            INSERT INTO leaderboard (username, score, wave_reached, survival_time, date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (current_user["username"], score, wave_reached, survival_time, datetime.now())
        )
        
        # Update player's best score if this one is higher
        cursor.execute(
            """
            UPDATE players SET 
                score = GREATEST(score, %s),
                last_login = %s
            WHERE username = %s
            """,
            (score, datetime.now(), current_user["username"])
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Score submitted successfully"}
    except Exception as e:
        logger.error(f"Error submitting leaderboard score: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit score")

# Game session model
class GameSession(BaseModel):
    session_id: Optional[str] = None
    username: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    score: int = 0
    enemies_defeated: int = 0
    waves_completed: int = 0

@app.post("/game-sessions")
async def start_game_session(current_user = Depends(get_current_user)):
    """Start a new game session (requires authentication)"""
    try:
        session_id = str(uuid.uuid4())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO game_sessions (session_id, username, start_time, score, enemies_defeated, waves_completed)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (session_id, current_user["username"], datetime.now(), 0, 0, 0)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error starting game session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start game session")

@app.put("/game-sessions/{session_id}")
async def end_game_session(
    session_id: str, 
    score: int, 
    enemies_defeated: int, 
    waves_completed: int,
    current_user = Depends(get_current_user)
):
    """End a game session and record results (requires authentication)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verify session exists and belongs to the user
        cursor.execute(
            "SELECT * FROM game_sessions WHERE session_id = %s",
            (session_id,)
        )
        session = cursor.fetchone()
        
        if not session:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session["username"] != current_user["username"]:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify another player's session"
            )
        
        # Update session
        cursor.execute(
            """
            UPDATE game_sessions SET 
                end_time = %s, 
                score = %s, 
                enemies_defeated = %s, 
                waves_completed = %s 
            WHERE session_id = %s
            """,
            (datetime.now(), score, enemies_defeated, waves_completed, session_id)
        )
        
        # Update player's score if this score is higher
        cursor.execute(
            """
            UPDATE players SET 
                score = GREATEST(score, %s),
                last_login = %s
            WHERE username = %s
            """,
            (score, datetime.now(), current_user["username"])
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Game session completed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending game session: {e}")
        raise HTTPException(status_code=500, detail="Failed to end game session")

@app.get("/players/{username}/stats")
async def get_player_stats(username: str):
    """Get player statistics including game session history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get player data
        cursor.execute("SELECT * FROM players WHERE username = %s", (username,))
        player = cursor.fetchone()
        
        if not player:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get player stats from game sessions
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_sessions,
                MAX(score) as highest_score,
                SUM(enemies_defeated) as total_enemies_defeated,
                MAX(waves_completed) as highest_wave
            FROM game_sessions 
            WHERE username = %s AND end_time IS NOT NULL
            """,
            (username,)
        )
        stats = cursor.fetchone()
        
        # Get recent sessions
        cursor.execute(
            """
            SELECT session_id, start_time, end_time, score, enemies_defeated, waves_completed
            FROM game_sessions
            WHERE username = %s AND end_time IS NOT NULL
            ORDER BY start_time DESC
            LIMIT 5
            """,
            (username,)
        )
        recent_sessions = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {
            "player": dict(player),
            "stats": dict(stats) if stats else {},
            "recent_sessions": recent_sessions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving player stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving player stats")

@app.put("/players/{username}/inventory")
async def update_inventory(
    username: str,
    item_type: str,
    quantity: int = 1,
    current_user = Depends(get_current_user)
):
    """Update player inventory (add or remove items)"""
    if current_user["username"] != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another player's inventory"
        )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get current inventory
        cursor.execute("SELECT inventory FROM players WHERE username = %s", (username,))
        player = cursor.fetchone()
        
        if not player:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Update inventory
        inventory = player["inventory"]
        if item_type not in inventory:
            inventory[item_type] = 0
        
        inventory[item_type] += quantity
        if inventory[item_type] < 0:
            inventory[item_type] = 0
        
        # Save updated inventory
        cursor.execute(
            "UPDATE players SET inventory = %s WHERE username = %s",
            (json.dumps(inventory), username)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Inventory updated",
            "inventory": inventory
        }
    except Exception as e:
        logger.error(f"Error updating inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to update inventory")

@app.post("/items/collect")
async def record_item_collection(
    type: str = Body(...), 
    name: str = Body(...), 
    x: int = Body(...), 
    y: int = Body(...), 
    value: int = Body(1),
    current_user = Depends(get_current_user)
):
    """Record a collected item in the items table"""
    try:
        username = current_user["username"]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert into items table
        cursor.execute("""
            INSERT INTO items (type, name, x, y, value, username, collected_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            type, name, x, y, value, username, datetime.now()
        ))
        
        # If it's a resource, also update player inventory
        if type in ["code_fragments", "energy_cores", "data_shards"]:
            # First get current inventory
            cursor.execute(
                "SELECT inventory FROM players WHERE username = %s",
                (username,)
            )
            player_data = cursor.fetchone()
            
            if player_data:
                inventory = player_data[0] if isinstance(player_data[0], dict) else json.loads(player_data[0])
                
                # Update inventory count
                if type not in inventory:
                    inventory[type] = 0
                inventory[type] += value
                
                # Save updated inventory
                cursor.execute(
                    "UPDATE players SET inventory = %s WHERE username = %s",
                    (json.dumps(inventory), username)
                )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"success": True, "message": f"Item collected: {type}"}
    except Exception as e:
        logger.error(f"Error recording item collection: {e}")
        raise HTTPException(status_code=500, detail=f"Error recording item: {str(e)}")

@app.post("/items/spawn")
async def record_item_spawn(
    type: str = Body(...), 
    name: str = Body(...), 
    x: int = Body(...), 
    y: int = Body(...), 
    value: int = Body(1),
    current_user = Depends(get_current_user)
):
    """Record a spawned item in the items table"""
    try:
        username = current_user["username"]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert into items table
        cursor.execute("""
            INSERT INTO items (type, name, x, y, value, username, spawned_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            type, name, x, y, value, username, datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"success": True, "message": f"Item spawn recorded: {type}"}
    except Exception as e:
        logger.error(f"Error recording item spawn: {e}")
        raise HTTPException(status_code=500, detail=f"Error recording item spawn: {str(e)}")

# More routes can be added here...

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str, token: Optional[str] = None):
    """WebSocket endpoint for real-time game updates"""
    # Token validation (optional for development)
    valid_user = False
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_username = payload.get("sub")
            if token_username == username:
                valid_user = True
        except:
            pass
    
    # In development, we allow connecting without token
    # For production, uncomment: if not valid_user: return
    
    await manager.connect(websocket, username)
    
    try:
        # Get player data
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM players WHERE username = %s", (username,))
        player = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if player:
            await websocket.send_json({
                "event": "player_data",
                "player": dict(player)
            })
        
        # Main communication loop
        while True:
            data = await websocket.receive_json()
            
            # Handle different action types
            if "action" in data:
                action = data["action"]
                
                if action == "update_position":
                    if "x" in data and "y" in data:
                        x = data["x"]
                        y = data["y"]
                        direction = data.get("direction", "down")  # Get direction with default
                        
                        # Update in database
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE players SET x = %s, y = %s, last_login = %s WHERE username = %s",
                            (x, y, datetime.now(), username)
                        )
                        conn.commit()
                        cursor.close()
                        conn.close()
                        
                        # Broadcast to other players
                        await manager.broadcast({
                            "event": "player_moved",
                            "username": username,
                            "position": {"x": x, "y": y},
                            "direction": direction
                        }, exclude=username)
                
                elif action == "chat_message":
                    if "message" in data:
                        await manager.broadcast({
                            "event": "chat_message",
                            "username": username,
                            "message": data["message"],
                            "timestamp": datetime.now().isoformat()
                        })
                
                elif action == "get_all_players":
                    # Get all active players from database
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                        # Get players who have logged in within the last hour
                        cursor.execute(
                            "SELECT username, x, y FROM players WHERE last_login > NOW() - INTERVAL '1 hour'"
                        )
                        all_players = cursor.fetchall()
                        cursor.close()
                        conn.close()
                        
                        # Send player list to the requesting client
                        players_list = [{"username": p["username"], "x": p["x"], "y": p["y"]} for p in all_players]
                        await websocket.send_json({
                            "event": "all_players",
                            "players": players_list
                        })
                        logger.info(f"Sent list of {len(players_list)} players to {username}")
                    except Exception as e:
                        logger.error(f"Error fetching all players: {e}")
                
                # Add other action handlers as needed
    
    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast({
            "event": "player_left",
            "username": username
        })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(username)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
