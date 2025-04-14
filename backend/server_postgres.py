"""
PostgreSQL-compatible server for CodeBreak application.
This version uses direct psycopg2 connections for simplicity.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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
                            "position": {"x": x, "y": y}
                        }, exclude=username)
                
                elif action == "chat_message":
                    if "message" in data:
                        await manager.broadcast({
                            "event": "chat_message",
                            "username": username,
                            "message": data["message"],
                            "timestamp": datetime.now().isoformat()
                        })
                
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
