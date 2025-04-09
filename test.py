import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

async def test_connection():
    load_dotenv()
    mongo_url = os.getenv("MONGO_URL")
    print(f"Connecting to: {mongo_url}")
    client = AsyncIOMotorClient(mongo_url)
    try:
        await client.admin.command('ping')
        print("MongoDB connection successful!")
        dbs = await client.list_database_names()
        print(f"Available databases: {dbs}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())