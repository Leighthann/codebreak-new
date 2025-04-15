#!/usr/bin/env python3
"""
Script to deploy database tables to remote PostgreSQL server
"""

import os
import sys
import argparse
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy database tables to remote server')
    parser.add_argument('--host', default=os.getenv('DB_HOST', 'localhost'), 
                        help='Database host (default from .env or localhost)')
    parser.add_argument('--port', type=int, default=int(os.getenv('DB_PORT', '5432')), 
                        help='Database port (default from .env or 5432)')
    parser.add_argument('--user', default=os.getenv('DB_USER', 'postgres'),
                        help='Database user (default from .env or postgres)')
    parser.add_argument('--password', default=os.getenv('DB_PASSWORD', 'L3igh-@Ann22'),
                        help='Database password (default from .env)')
    parser.add_argument('--dbname', default=os.getenv('DB_NAME', 'codebreak_db'),
                        help='Database name (default from .env or codebreak_db)')
    return parser.parse_args()

def deploy_tables(conn_params):
    try:
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Read SQL script
        script_path = Path(__file__).parent / 'create_tables.sql'
        
        if not script_path.exists():
            print(f"Error: SQL script not found at {script_path}")
            return False
        
        print(f"Executing SQL script: {script_path}")
        with open(script_path, 'r') as f:
            sql_script = f.read()
        
        # Execute the script
        cursor.execute(sql_script)
        
        # Get result of confirmation message
        if cursor.description:  # Check if there's a result set
            result = cursor.fetchone()
            if result:
                print(result[0])  # Print the confirmation message
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database tables deployed successfully!")
        return True
    
    except Exception as e:
        print(f"Error deploying database tables: {e}")
        return False

def main():
    args = parse_args()
    
    # Connection parameters
    conn_params = {
        'host': args.host,
        'port': args.port,
        'user': args.user,
        'password': args.password,
        'dbname': args.dbname
    }
    
    # Display connection info (without password)
    safe_params = {k: v if k != 'password' else '[HIDDEN]' for k, v in conn_params.items()}
    print(f"Deploying tables with connection: {safe_params}")
    
    # Deploy tables
    success = deploy_tables(conn_params)
    
    if success:
        print("Table deployment complete.")
        return 0
    else:
        print("Table deployment failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())