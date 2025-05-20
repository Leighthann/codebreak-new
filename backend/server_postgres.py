"""
PostgreSQL-compatible server for CodeBreak application.
This version uses direct psycopg2 connections for simplicity.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil
import os
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
import json
from uuid import uuid4
import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)  # Added override=True to ensure variables are loaded

# Database connection parameters - using direct password from env for debugging
password = os.getenv("DB_PASSWORD", "L3igh-@Ann22")  # Default password for debugging
print(f"Password loaded from env: {'*' * len(password) if password else 'NO PASSWORD FOUND'}")

DB_PARAMS = {
    "database": os.getenv("DB_NAME", "codebreak_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": password,  # Direct assignment from variable
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432"))
}

#safe_params = {k: v if k != "password" else "[HIDDEN]" for k, v in DB_PARAMS.items()}
safe_params = DB_PARAMS.copy()

# Function to get database connection with hardcoded fallback
def get_db_connection():
    """Create a new database connection"""
    try:
        # First try with parameters from environment
        try:
            connection = psycopg2.connect(**DB_PARAMS)
            print("Connection successful with env parameters!")
            return connection
        except Exception as e:
            print(f"First connection attempt failed: {e}")
            print("Attempting to connect with parameters:")
            print(safe_params)
            
            # If that fails, try with hardcoded password as last resort
            hardcoded_params = DB_PARAMS.copy()
            hardcoded_params["password"] = "L3igh-@Ann22"  # Temporary for debugging
            print("Trying with hardcoded password as fallback...")
            connection = psycopg2.connect(**hardcoded_params)
            print("Connection successful with hardcoded password!")
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

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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
        self.active_games: Dict[str, Dict[str, Any]] = {}
        self.game_players: Dict[str, List[str]] = {}
        
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

    async def create_game(self, host_username: str) -> str:
        """Create a new game session"""
        game_id = str(uuid4())
        self.active_games[game_id] = {
            "host": host_username,
            "created_at": datetime.now().isoformat()
        }
        self.game_players[game_id] = [host_username]
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO active_games (game_id, host_username) VALUES (%s, %s)",
            (game_id, host_username)
        )
        cursor.execute(
            "INSERT INTO game_players (game_id, username) VALUES (%s, %s)",
            (game_id, host_username)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return game_id

    async def join_game(self, game_id: str, username: str) -> bool:
        """Join an existing game session"""
        if game_id not in self.active_games:
            return False
        
        if username in self.game_players.get(game_id, []):
            return True  # Already in the game
        
        # Add player to the game
        if game_id not in self.game_players:
            self.game_players[game_id] = []
        self.game_players[game_id].append(username)
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO game_players (game_id, username) VALUES (%s, %s)",
            (game_id, username)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Notify other players in the game
        await self.broadcast_to_game(game_id, {
            "event": "player_joined_game",
            "username": username,
            "timestamp": datetime.now().isoformat()
        }, exclude=username)
        
        return True

    async def leave_game(self, game_id: str, username: str) -> bool:
        """Leave a game session"""
        if game_id not in self.active_games or username not in self.game_players.get(game_id, []):
            return False
        
        # Remove player from the game
        self.game_players[game_id].remove(username)
        
        # Delete from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM game_players WHERE game_id = %s AND username = %s",
            (game_id, username)
        )
        conn.commit()
        
        # If host left, delete the game if no players remain
        if username == self.active_games[game_id]["host"]:
            if not self.game_players[game_id]:
                cursor.execute(
                    "DELETE FROM active_games WHERE game_id = %s",
                    (game_id,)
                )
                del self.active_games[game_id]
                del self.game_players[game_id]
        
        cursor.close()
        conn.close()
        
        # Notify other players in the game
        await self.broadcast_to_game(game_id, {
            "event": "player_left_game",
            "username": username,
            "timestamp": datetime.now().isoformat()
        })
        
        return True

    async def broadcast_to_game(self, game_id: str, message: Dict, exclude: Optional[str] = None):
        """Broadcast message to all players in a specific game"""
        players = self.game_players.get(game_id, [])
        
        for username in players:
            if exclude is None or username != exclude:
                if username in self.active_connections:
                    try:
                        await self.active_connections[username].send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending to {username}: {e}")

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
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
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

@app.get("/play-game", response_class=HTMLResponse)
async def play_game(request: Request, token: str, username: str):
    """
    Provide instructions for launching the game client through main.py.
    This endpoint is called when a user clicks the "Launch Game" button.
    """
    try:
        # Verify token validity
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_username = payload.get("sub")
        
        if not token_username or token_username != username:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "message": "Invalid authentication token"
            })
        
        # Get player data from database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM players WHERE username = %s", (username,))
        player = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not player:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "message": "Player not found"
            })
        
        # Create a config file with connection details for the client
        config_data = {
            "server_url": f"{request.url.scheme}://{request.headers.get('host')}",
            "token": token,
            "username": username
        }
        
        # Generate a content for client_config.json that the user needs to save
        config_json = json.dumps(config_data, indent=2)
        
        # Return simple instructions template
        return templates.TemplateResponse("launch_instructions.html", {
            "request": request, 
            "username": username,
            "token": token,
            "config_json": config_json,
            "server_url": f"{request.url.scheme}://{request.headers.get('host')}"
        })
    
    except jwt.PyJWTError:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "Invalid or expired token"
        })
    except Exception as e:
        logger.error(f"Error rendering launch instructions: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "An error occurred"
        })

# More routes can be added here...

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, message: Optional[str] = None):
    """Render the login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": message
    })

@app.post("/web-login")
async def web_login(request: Request):
    """Handle web form-based login"""
    try:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        
        # Log the login attempt for debugging
        logger.info(f"Web login attempt for user: {username}")
        
        # Verify credentials
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            logger.warning(f"Login failed: User {username} not found")
            return RedirectResponse(url=f"/login?message=Invalid+username+or+password", status_code=303)
        
        # Verify password
        if not password or not verify_password(str(password), user["hashed_password"]):
            logger.warning(f"Login failed: Incorrect password for {username}")
            return RedirectResponse(url=f"/login?message=Invalid+username+or+password", status_code=303)
        
        # Generate token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        
        # Successful login - redirect to launch page with token
        logger.info(f"Web login successful for user: {username}")
        return templates.TemplateResponse("launch.html", {
            "request": request,
            "username": username,
            "token": access_token
        })
    
    except Exception as e:
        logger.error(f"Web login error: {str(e)}")
        return RedirectResponse(url=f"/login?message=An+error+occurred", status_code=303)

# Optional: Registration page endpoint
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, message: Optional[str] = None):
    """Render the registration page"""
    return templates.TemplateResponse("register.html", {
        "request": request,
        "message": message
    })

@app.post("/web-register")
async def web_register(request: Request):
    """Handle web form-based registration"""
    try:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        confirm_password = form_data.get("confirm_password")
        
        # Validate input
        if not username or not password:
            return RedirectResponse(url="/register?message=Username+and+password+required", status_code=303)
            
        if password != confirm_password:
            return RedirectResponse(url="/register?message=Passwords+do+not+match", status_code=303)
        
        # Create user using existing function
        user_data = UserCreate(username=str(username), password=str(password))
        try:
            await register_user(user_data)
            # Registration successful, redirect to login
            return RedirectResponse(url="/login?message=Registration+successful+Please+login", status_code=303)
        except HTTPException as e:
            return RedirectResponse(url=f"/register?message={e.detail}", status_code=303)
            
    except Exception as e:
        logger.error(f"Web registration error: {str(e)}")
        return RedirectResponse(url="/register?message=Registration+failed", status_code=303)

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str, token: Optional[str] = None, game_id: Optional[str] = None):
    """WebSocket endpoint for real-time game updates with game session support"""
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
        # Join game if specified
        if game_id and valid_user:
            await manager.join_game(game_id, username)
        
        # Main communication loop
        while True:
            data = await websocket.receive_json()
            
            # Handle different action types
            if "action" in data:
                action = data["action"]
                
                if action == "update_position":
                    # Add handling for game_id to only broadcast to players in same game
                    current_game_id = data.get("game_id")
                    
                    if "x" in data and "y" in data:
                        x = data["x"]
                        y = data["y"]
                        
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
                        
                        # Broadcast to other players in the same game
                        position_data = {
                            "event": "player_moved",
                            "username": username,
                            "position": {"x": x, "y": y, "direction": data.get("direction", "down")}
                        }
                        
                        if current_game_id:
                            await manager.broadcast_to_game(current_game_id, position_data, exclude=username)
                        else:
                            await manager.broadcast(position_data, exclude=username)
                
                elif action == "chat_message":
                    if "message" in data:
                        current_game_id = data.get("game_id")
                        chat_data = {
                            "event": "chat_message",
                            "username": username,
                            "message": data["message"],
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        if current_game_id:
                            await manager.broadcast_to_game(current_game_id, chat_data)
                        else:
                            await manager.broadcast(chat_data)
                
                elif action == "share_resource":
                    # Handle resource sharing within a game
                    if "resource_type" in data and "amount" in data:
                        resource_type = data["resource_type"]
                        amount = data["amount"]
                        current_game_id = data.get("game_id")
                        
                        share_data = {
                            "event": "share_resource",
                            "resource_type": resource_type,
                            "amount": amount,
                            "shared_by": username
                        }
                        
                        if current_game_id:
                            await manager.broadcast_to_game(current_game_id, share_data, exclude=username)
                        else:
                            await manager.broadcast(share_data, exclude=username)
                
                elif action == "leave_game":
                    # Handle a player leaving a game
                    if "game_id" in data:
                        await manager.leave_game(data["game_id"], username)
                
                # Add other action handlers as needed
    
    except WebSocketDisconnect:
        manager.disconnect(username)
        
        # Notify other players the user has disconnected
        if game_id:
            await manager.leave_game(game_id, username)
            await manager.broadcast_to_game(game_id, {
                "event": "player_left",
                "username": username
            })
        else:
            await manager.broadcast({
                "event": "player_left",
                "username": username
            })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(username)

# After the web-register endpoint, add these database viewer endpoints

@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request, message: Optional[str] = None):
    """Admin login page"""
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "message": message
    })

@app.post("/admin-login")
async def process_admin_login(request: Request):
    """Process admin login and return a JWT token"""
    try:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        
        # Very simple admin authentication - consider using a more secure method
        if username == "admin" and password == "L3igh-@Ann22":
            # Issue a JWT token for admin
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": username, "is_admin": True}, 
                expires_delta=access_token_expires
            )
            
            # Return JSON response with token
            return JSONResponse(
                content={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "message": "Login successful"
                },
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                }
            )
        else:
            return JSONResponse(
                status_code=401,
                content={"message": "Invalid credentials"}
            )
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": "Error logging in"}
        )

@app.get("/db-viewer", response_class=HTMLResponse)
async def db_viewer(request: Request):
    """Database viewer page"""
    try:
        # Get list of tables
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get data from users table
        cursor.execute("SELECT * FROM users")
        users_data = cursor.fetchall()
        users_columns = [desc[0] for desc in cursor.description]
        
        # Get data from players table
        cursor.execute("SELECT * FROM players")
        players_data = cursor.fetchall()
        players_columns = [desc[0] for desc in cursor.description]
        
        # Get data from leaderboard table
        cursor.execute("""
            SELECT l.*, p.last_login 
            FROM leaderboard l
            LEFT JOIN players p ON l.username = p.username
            ORDER BY l.score DESC
        """)
        leaderboard_data = cursor.fetchall()
        leaderboard_columns = [desc[0] for desc in cursor.description]
        
        # Fetch active games from the database
        cursor.execute("""
            SELECT ag.game_id, ag.host_username, ag.created_at, COUNT(gp.username) as player_count
            FROM active_games ag
            JOIN game_players gp ON ag.game_id = gp.game_id
            GROUP BY ag.game_id, ag.host_username, ag.created_at
            ORDER BY ag.created_at DESC
        """)
        games = []
        for row in cursor.fetchall():
            games.append({
                "game_id": row["game_id"],
                "host": row["host_username"],
                "created_at": row["created_at"].isoformat(),
                "player_count": row["player_count"]
            })
        
        cursor.close()
        conn.close()
        
        return templates.TemplateResponse("db_viewer.html", {
            "request": request,
            "tables": tables,
            "users_data": users_data,
            "users_columns": users_columns,
            "players_data": players_data,
            "players_columns": players_columns,
            "leaderboard_data": leaderboard_data,
            "leaderboard_columns": leaderboard_columns,
            "games": games
        })
    except Exception as e:
        logger.error(f"DB viewer error: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": f"Database error: {str(e)}"
        })

@app.get("/api/db/{table_name}")
async def get_table_data(table_name: str, current_user = Depends(get_current_user)):
    """API endpoint to get table data"""
    try:
        # Basic SQL injection protection
        allowed_tables = ["users", "players"]
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail="Invalid table name")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        
        # Mask sensitive data
        if table_name == "users":
            for row in result:
                if "hashed_password" in row:
                    row["hashed_password"] = "[HIDDEN]"
        
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"API db error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# After the other route handlers, add this endpoint for client download
@app.get("/download-client")
async def download_client():

    """Serve the client zip file for download"""
    try:
        # Define source and target paths
        download_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "download-client")
        temp_zip_path = os.path.join(os.path.dirname(__file__), "codebreak_client.zip")
        
        # Check if the download_client directory exists
        if not os.path.exists(download_dir):
            logger.error(f"Client directory not found at: {download_dir}")
            raise HTTPException(status_code=404, detail="Game client not available")
        
        # Create a zip file from the download_client directory
        shutil.make_archive(
            os.path.join(os.path.dirname(__file__), "codebreak_client"),
            'zip', 
            download_dir
        )
        
        # Check if the zip was created
        if not os.path.exists(temp_zip_path):
            logger.error("Failed to create client zip file")
            raise HTTPException(status_code=500, detail="Failed to prepare download")
        
        # Return the file as a downloadable response
        return FileResponse(
            path=temp_zip_path, 
            filename="codebreak_client.zip",
            media_type="application/zip"
        )
    except Exception as e:
        logger.error(f"Error serving client download: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")

@app.get("/leaderboard")
async def get_leaderboard(limit: int = 10, current_user = Depends(get_current_user)):
    """Get top leaderboard entries"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get top scores
        cursor.execute("""
            SELECT l.*, p.last_login 
            FROM leaderboard l
            LEFT JOIN players p ON l.username = p.username
            ORDER BY l.score DESC
            LIMIT %s
        """, (limit,))
        
        entries = []
        for row in cursor.fetchall():
            entry = dict(row)
            # Format dates as ISO strings for JSON serialization
            if entry.get("date"):
                entry["date"] = entry["date"].isoformat()
            if entry.get("last_login"):
                entry["last_login"] = entry["last_login"].isoformat()
                
            entries.append(entry)
        
        cursor.close()
        conn.close()
        
        return {"leaderboard": entries}
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching leaderboard: {str(e)}")

@app.post("/leaderboard")
async def submit_score(score_data: dict, current_user = Depends(get_current_user)):
    """Submit a new score to the leaderboard"""
    try:
        username = current_user["username"]
        score = score_data.get("score", 0)
        wave_reached = score_data.get("wave_reached", 0)
        survival_time = score_data.get("survival_time", 0)
        
        # Validate score data
        if score <= 0:
            raise HTTPException(status_code=400, detail="Score must be greater than 0")
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already has a score
        cursor.execute("SELECT id, score FROM leaderboard WHERE username = %s", (username,))
        existing_score = cursor.fetchone()
        
        # Insert or update score
        if existing_score:
            # Only update if new score is higher
            if score > existing_score[1]:
                cursor.execute(
                    """UPDATE leaderboard 
                       SET score = %s, wave_reached = %s, survival_time = %s, date = %s 
                       WHERE id = %s""",
                    (score, wave_reached, survival_time, datetime.now(), existing_score[0])
                )
                updated = True
            else:
                updated = False
        else:
            # Insert new score
            cursor.execute(
                """INSERT INTO leaderboard 
                   (username, score, wave_reached, survival_time, date) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (username, score, wave_reached, survival_time, datetime.now())
            )
            updated = True
            
        # Update player score in players table too
        cursor.execute(
            "UPDATE players SET score = GREATEST(score, %s) WHERE username = %s",
            (score, username)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": "Score updated successfully" if updated else "Score not updated (current score is higher)",
            "score": score
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting score: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting score: {str(e)}")

# Public version of leaderboard endpoint (no auth required)
@app.get("/leaderboard/public")
async def get_public_leaderboard(limit: int = 10):
    """Get top leaderboard entries (public endpoint, no auth required)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get top scores
        cursor.execute("""
            SELECT l.*, p.last_login
            FROM leaderboard l
            LEFT JOIN players p ON l.username = p.username
            ORDER BY l.score DESC
            LIMIT %s
        """, (limit,))
        
        entries = []
        for row in cursor.fetchall():
            entry = dict(row)
            # Format dates as ISO strings for JSON serialization
            if entry.get("date"):
                entry["date"] = entry["date"].isoformat()
            if entry.get("last_login"):
                entry["last_login"] = entry["last_login"].isoformat()
                
            entries.append(entry)
        
        cursor.close()
        conn.close()
        
        return {"leaderboard": entries}
    except Exception as e:
        logger.error(f"Error fetching public leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching leaderboard: {str(e)}")

@app.post("/create_game")
async def create_new_game(current_user = Depends(get_current_user)):
    """Create a new game session"""
    # Convert DictRow to dict if needed
    if hasattr(current_user, 'items'):
        username = current_user['username']
    else:
        username = current_user.username
    
    game_id = await manager.create_game(username)
    
    return {
        "game_id": game_id,
        "host": username,
        "created_at": datetime.now().isoformat()
    }

@app.post("/join_game/{game_id}")
async def join_existing_game(game_id: str, current_user = Depends(get_current_user)):
    """Join an existing game session"""
    # Convert DictRow to dict if needed
    if hasattr(current_user, 'items'):
        username = current_user['username']
    else:
        username = current_user.username
    
    success = await manager.join_game(game_id, username)
    
    if not success:
        raise HTTPException(status_code=404, detail="Game not found or cannot join")
    
    return {"message": "Successfully joined the game"}

@app.get("/active_games")
async def get_active_games(current_user = Depends(get_current_user)):
    """Get list of active games"""
    games = []
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get games with player count
    cursor.execute("""
        SELECT ag.game_id, ag.host_username, ag.created_at, COUNT(gp.username) as player_count
        FROM active_games ag
        JOIN game_players gp ON ag.game_id = gp.game_id
        GROUP BY ag.game_id, ag.host_username, ag.created_at
        ORDER BY ag.created_at DESC
    """)
    
    for row in cursor.fetchall():
        games.append({
            "game_id": row["game_id"],
            "host": row["host_username"],
            "created_at": row["created_at"].isoformat(),
            "player_count": row["player_count"]
        })
    
    cursor.close()
    conn.close()
    
    return {"games": games}

def is_admin_user(current_user = Depends(get_current_user)):
    # Example: check if the user has an 'is_admin' attribute or username
    if hasattr(current_user, 'items'):
        username = current_user['username']
        is_admin = current_user.get('is_admin', False)
    else:
        username = current_user.username
        is_admin = getattr(current_user, 'is_admin', False)
    if not is_admin and username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

@app.delete("/admin/delete_game/{game_id}")
async def admin_delete_game(game_id: str, current_user = Depends(is_admin_user)):
    """Admin endpoint to delete a game session by game_id"""
    # Remove from in-memory manager
    if game_id in manager.active_games:
        del manager.active_games[game_id]
    if game_id in manager.game_players:
        del manager.game_players[game_id]
    # Remove from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_games WHERE game_id = %s", (game_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": f"Game {game_id} deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
