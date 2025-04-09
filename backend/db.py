"""
Updated db.py - PostgreSQL with Async SQLAlchemy
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, JSON, DateTime, func
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL connection URL from .env file
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/codebreak_db")

# Create async database engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create session factory
from sqlalchemy.ext.asyncio import async_sessionmaker

async_session = async_sessionmaker(engine, expire_on_commit=False)

# Base class for defining models
Base = declarative_base()

async def get_db():
    """Dependency to get a database session for FastAPI routes"""
    async with async_session() as session:
        yield session

# Database Models
class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    health = Column(Integer, default=100)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    score = Column(Integer, default=0)
    inventory = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, server_default=func.now(), onupdate=func.now())

class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    date = Column(DateTime, server_default=func.now())

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    start_time = Column(DateTime, server_default=func.now())
    end_time = Column(DateTime, nullable=True)
    score = Column(Integer, default=0)
    enemies_defeated = Column(Integer, default=0)
    waves_completed = Column(Integer, default=0)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # "resource", "weapon", "tool"
    name = Column(String, nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    value = Column(Integer, default=1)
    spawned_at = Column(DateTime, server_default=func.now())

# Create tables (if running without Alembic migrations)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Database Operations
async def get_player(username: str, db: AsyncSession):
    """Retrieve player details by username"""
    from sqlalchemy.future import select

    stmt = select(Player).where(Player.username == username)
    result = await db.execute(stmt)
    return result.fetchone()

async def create_or_update_player(player_data: dict, db: AsyncSession):
    """Create or update player details"""
    query = """
        INSERT INTO players (username, health, x, y, score, inventory, created_at, last_login)
        VALUES (:username, :health, :x, :y, :score, :inventory, NOW(), NOW())
        ON CONFLICT (username) DO UPDATE 
        SET health = EXCLUDED.health, x = EXCLUDED.x, y = EXCLUDED.y, score = EXCLUDED.score, inventory = EXCLUDED.inventory, last_login = NOW();
    """
    from sqlalchemy.sql import text
    await db.execute(text(query), player_data)
    await db.commit()

async def update_player_position(username: str, x: int, y: int, db: AsyncSession):
    """Update player position"""
    query = "UPDATE players SET x = :x, y = :y, last_login = NOW() WHERE username = :username"
    from sqlalchemy.sql import text
    await db.execute(text(query), {"username": username, "x": x, "y": y})
    await db.commit()

async def add_to_leaderboard(entry: dict, db: AsyncSession):
    """Insert a new leaderboard entry"""
    query = "INSERT INTO leaderboard (username, score, date) VALUES (:username, :score, NOW())"
    from sqlalchemy.sql import text
    await db.execute(text(query), entry)
    await db.commit()

async def get_top_leaderboard(limit: int, db: AsyncSession):
    """Retrieve top leaderboard scores"""
    from sqlalchemy.sql import text
    query = text("SELECT * FROM leaderboard ORDER BY score DESC LIMIT :limit")
    result = await db.execute(query, {"limit": limit})
    return result.fetchall()

async def record_game_session(session_data: dict, db: AsyncSession):
    """Insert a new game session record"""
    query = """
        INSERT INTO game_sessions (username, start_time, end_time, score, enemies_defeated, waves_completed)
        VALUES (:username, :start_time, :end_time, :score, :enemies_defeated, :waves_completed)
    """
    from sqlalchemy.sql import text
    await db.execute(text(query), session_data)
    await db.commit()

async def spawn_item(item_data: dict, db: AsyncSession):
    """Spawn a new item in the game world"""
    query = """
        INSERT INTO items (type, name, x, y, value, spawned_at)
        VALUES (:type, :name, :x, :y, :value, NOW())
    """
    from sqlalchemy.sql import text
    await db.execute(text(query), item_data)
    await db.commit()

async def collect_item(item_id: int, username: str, db: AsyncSession):
    """Collect an item and update the player's inventory"""
    # Retrieve the item
    query = "SELECT * FROM items WHERE id = :item_id"
    from sqlalchemy.sql import text
    result = await db.execute(text(query), {"item_id": item_id})
    item = result.fetchone()

    if not item:
        return None
    
    # Remove the item from the game world
    delete_query = "DELETE FROM items WHERE id = :item_id"
    from sqlalchemy.sql import text
    await db.execute(text(delete_query), {"item_id": item_id})

    # Update player inventory
    update_query = """
        UPDATE players 
        SET inventory = jsonb_set(
            inventory, 
            '{' || :type || '}', 
            (COALESCE(inventory->>:type, '0')::int + :value)::text::jsonb
        ) 
        WHERE username = :username
    """
    from sqlalchemy.sql import text
    await db.execute(text(update_query), {"type": item.type, "value": item.value, "username": username})
    await db.commit()

    return item
