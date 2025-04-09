"""
Modified version of db.py with TLS configuration fix for MongoDB Atlas
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import certifi  # Add this import for CA certificates

# Load environment variables
load_dotenv()

# MongoDB connection with TLS/SSL configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://CodebreakAdmin:codebreak123@codebreak.hqnfeao.mongodb.net/?retryWrites=true&w=majority&appName=Codebreak")
db_client = AsyncIOMotorClient(
    MONGO_URL,
    tls=True,
    tlsCAFile=certifi.where(),  # Use the Mozilla CA certificate bundle
    serverSelectionTimeoutMS=5000  # Reduce timeout for faster feedback
)
db = db_client.get_database("codebreak_db")  # Use actual database name
print("MongoDB client initialized successfully")

# Test MongoDB connection
async def test_mongo_connection():
    try:
        # Attempt to list collections to verify the connection
        collections = await db.list_collection_names()
        print("MongoDB connection successful. Collections:", collections)
    except Exception as e:
        print("MongoDB connection failed:", e)

# Ensure this is called in an async context
if __name__ == "__main__":
    import asyncio

    async def main():
        await test_mongo_connection()
    asyncio.run(main())

# Collections
db = db_client["codebreak_db"]
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
    if not await test_mongo_connection():
        print("Skipping index creation due to connection failure")
        return False
    try:
        await players_collection.create_index("username", unique=True)
        await leaderboard_collection.create_index([("score", -1)])
        await game_sessions_collection.create_index("username")
        await items_collection.create_index("item_id", unique=True)
        await items_collection.create_index([("spawned_at", 1)], expireAfterSeconds=3600)  # TTL index
        print("Basic indexes created successfully")
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")
        # You can re-raise or handle the exception as needed


# async def create_indexes():
#         if not await test_mongo_connection():
#             print("Skipping index creation due to connection failure")
#             return False
#         try:
#             # Create basic indexes
#             await db["players"].create_index("username", unique=True)
#             await db["users"].create_index("username", unique=True)
#             print("Basic indexes created successfully")
#             return True
#         except Exception as e:
#             print(f"Error creating indexes: {e}")
#             return False