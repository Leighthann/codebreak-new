"""
Test script for PostgreSQL database connection
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    "database": os.getenv("DB_NAME", "codebreak_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432"))
}

print("Attempting to connect with parameters:")
safe_params = {k: v if k != "password" else "[HIDDEN]" for k, v in DB_PARAMS.items()}
print(safe_params)

try:
    # Try connecting to the database directly
    conn = psycopg2.connect(**DB_PARAMS)
    print("Connection successful!")
    
    # Check if we can execute a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0]}")
    
    # Check if the necessary tables exist
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    print("Existing tables:")
    for table in tables:
        print(f"- {table[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Connection failed: {e}")
    
    # Try connecting to postgres default database to check if PostgreSQL is running
    try:
        test_params = DB_PARAMS.copy()
        test_params["database"] = "postgres"
        conn = psycopg2.connect(**test_params)
        print("Successfully connected to default 'postgres' database.")
        print("This suggests the 'codebreak_db' database might not exist.")
        conn.close()
    except Exception as e2:
        print(f"Could not connect to default database either: {e2}")
        print("This suggests a deeper connection issue (password, host, etc.)")
