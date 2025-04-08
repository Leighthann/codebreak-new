from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection (use environment variables for production)
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
client = AsyncIOMotorClient(MONGO_URL)
db = client["codebreak_db"]

# Collections
players_collection = db["players"]
leaderboard_collection = db["leaderboard"]
game_sessions_collection = db["game_sessions"]
items_collection = db["items"]

# Pydantic Models for data validation
class PlayerModel(BaseModel):
    username: str
    health: int = 100
    x: int = 0
    y: int = 0
    score: int = 0
    inventory: Optional[Dict] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: datetime = Field(default_factory=datetime.now)

class LeaderboardEntry(BaseModel):
    username: str
    score: int
    wave_reached: int = 0
    survival_time: float = 0.0
    date: datetime = Field(default_factory=datetime.now)

class GameSession(BaseModel):
    session_id: str
    username: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    score: int = 0
    enemies_defeated: int = 0
    waves_completed: int = 0

class Item(BaseModel):
    item_id: str
    type: str  # "resource", "weapon", "tool"
    name: str
    x: int
    y: int
    value: int = 1
    spawned_at: datetime = Field(default_factory=datetime.now)

# Database operations
async def get_player(username: str):
    player = await players_collection.find_one({"username": username})
    return player

async def create_or_update_player(player_data: dict):
    result = await players_collection.update_one(
        {"username": player_data["username"]},
        {"$set": player_data},
        upsert=True
    )
    return result

async def update_player_position(username: str, x: int, y: int):
    result = await players_collection.update_one(
        {"username": username},
        {"$set": {"x": x, "y": y, "last_updated": datetime.now()}}
    )
    return result

async def add_to_leaderboard(entry: dict):
    result = await leaderboard_collection.insert_one(entry)
    return result

async def get_top_leaderboard(limit: int = 10):
    cursor = leaderboard_collection.find().sort("score", -1).limit(limit)
    return await cursor.to_list(limit)

async def record_game_session(session: dict):
    result = await game_sessions_collection.insert_one(session)
    return result

async def spawn_item(item: dict):
    result = await items_collection.insert_one(item)
    return result

async def collect_item(item_id: str, username: str):
    # First get the item
    item = await items_collection.find_one({"item_id": item_id})
    if not item:
        return None
    
    # Remove the item from the collection
    await items_collection.delete_one({"item_id": item_id})
    
    # Update player inventory
    await players_collection.update_one(
        {"username": username},
        {"$inc": {f"inventory.{item['type']}": item['value']}}
    )
    
    return item

# Create database indexes for better performance
async def create_indexes():
    await players_collection.create_index("username", unique=True)
    await leaderboard_collection.create_index([("score", -1)])
    await game_sessions_collection.create_index("username")
    await items_collection.create_index("item_id", unique=True)
    await items_collection.create_index([("spawned_at", 1)], expireAfterSeconds=3600)  # TTL index

# Example function
async def get_user(username):
    return await db.users.find_one({"username": username})