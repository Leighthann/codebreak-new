import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

import certifi
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

MONGO_URL = "mongodb+srv://CodebreakAdmin:codebreak123@codebreak.hqnfeao.mongodb.net/?retryWrites=true&w=majority&appName=Codebreak"

async def test_mongo_connection():
    try:
        client = AsyncIOMotorClient(MONGO_URL, tls=True, tlsCAFile=certifi.where())
        db = client.get_database("codebreak_db")
        collections = await db.list_collection_names()
        print("✅ MongoDB connected! Collections:", collections)
    except Exception as e:
        print("❌ MongoDB connection failed:", e)

asyncio.run(test_mongo_connection())


if __name__ == "__main__":
    asyncio.run(test_mongo_connection())