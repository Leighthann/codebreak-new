#!/bin/bash
# Combined deployment script for CodeBreak application
# Combines database deployment with server management

# Constants - update these if needed
EC2_HOST="ec2-3-130-249-194.us-east-2.compute.amazonaws.com"
KEY_PATH="../codebreak-key.pem"
REMOTE_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/codebreak-new"
BACKEND_DIR="$REMOTE_DIR/backend"

echo "=========================================="
echo "CodeBreak Comprehensive Deployment Script"
echo "=========================================="

# Ensure key file is accessible
if [ ! -f "$KEY_PATH" ]; then
    echo "Error: SSH key file not found at $KEY_PATH"
    exit 1
fi

# Make sure key has correct permissions
chmod 400 "$KEY_PATH"

# Function to run SSH commands on remote server
run_ssh_command() {
    echo ">>> Running command: $1"
    ssh -i "$KEY_PATH" "$REMOTE_USER@$EC2_HOST" "$1"
}

# Function to copy files to remote server
copy_to_server() {
    echo ">>> Copying $1 to $2"
    scp -i "$KEY_PATH" "$1" "$REMOTE_USER@$EC2_HOST:$2"
}

echo "============================================"
echo "STEP 1: Deploying Database Tables (One-Time)"
echo "============================================"

# Copy the database scripts to the server
echo "Copying SQL script to remote server..."
copy_to_server "create_tables.sql" "$BACKEND_DIR/scripts/"

# Copy the Python deployment script
echo "Copying deployment script to remote server..."
copy_to_server "deploy-tables.py" "$BACKEND_DIR/scripts/"

# Check if tables exist before creating them (to avoid duplicate creation)
echo "Creating tables only if they don't exist..."
run_ssh_command "cd $BACKEND_DIR && source ../venv/bin/activate && python -c \"
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn_params = {
    'dbname': os.getenv('DB_NAME', 'codebreak_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'L3igh-@Ann22'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

try:
    # Check if tables exist
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    cursor.execute(\\\"SELECT table_name FROM information_schema.tables WHERE table_schema='public'\\\")
    tables = cursor.fetchall()
    tables = [t[0] for t in tables]
    
    # If leaderboard and game_sessions don't exist, run the script
    if 'leaderboard' not in tables or 'game_sessions' not in tables or 'items' not in tables:
        print('Tables missing, running creation script...')
        # We'll exit with status 2 to indicate tables need to be created
        exit(2)
    else:
        print('All required tables exist, skipping creation')
        # Exit with status 0 to indicate no need to create tables
        exit(0)
except Exception as e:
    print(f'Error checking tables: {e}')
    # Exit with status 1 to indicate error
    exit(1)
\""

# Store the exit code
TABLES_CHECK=$?

# Run the database creation script only if needed (exit code 2)
if [ $TABLES_CHECK -eq 2 ]; then
    echo "Some tables are missing. Running full database creation script..."
    run_ssh_command "cd $BACKEND_DIR && source ../venv/bin/activate && python scripts/deploy-tables.py"
elif [ $TABLES_CHECK -eq 1 ]; then
    echo "Error checking tables. Will attempt to run creation script anyway..."
    run_ssh_command "cd $BACKEND_DIR && source ../venv/bin/activate && python scripts/deploy-tables.py"
else
    echo "All required database tables already exist. Skipping creation."
fi

echo "================================================"
echo "STEP 2: Server Management and Code Deployment"
echo "================================================"

# Original nano.ssh script functionality
run_ssh_command "cd $BACKEND_DIR && echo '>>> [1] Switching to backend directory'"

# Stop the service
run_ssh_command "sudo systemctl stop codebreak && echo '>>> [2] Stopping the CodeBreak service'"

# Pull latest code
run_ssh_command "cd $REMOTE_DIR && git pull origin sub-branch && echo '>>> [3] Pulling latest code from GitHub'"

# Activate virtual environment and install dependencies
run_ssh_command "cd $REMOTE_DIR && source venv/bin/activate && pip install -r backend/requirements.txt && echo '>>> [4-5] Virtual environment activated and dependencies installed'"

# Restart and check service
run_ssh_command "sudo systemctl start codebreak && echo '>>> [8] CodeBreak service restarted'"
run_ssh_command "sudo systemctl status codebreak && echo '>>> [9] Service status checked'"

# Check logs
run_ssh_command "echo '>>> [10] Checking server logs for errors' && sudo journalctl -u codebreak -n 20"

echo "================================================"
echo "Deployment complete!"
echo "================================================"
echo "The server is now running with the latest code and database tables."
echo "You can access the API at: http://$EC2_HOST:8000"
echo "================================================"