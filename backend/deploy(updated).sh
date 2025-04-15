#!/bin/bash
# Combined deployment script for CodeBreak application
# Combines database deployment with server management

# Constants - update these if needed
EC2_HOST="ec2-3-130-249-194.us-east-2.compute.amazonaws.com"
KEY_PATH="codebreak-key.pem"
REMOTE_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/codebreak-new"
BACKEND_DIR="$REMOTE_DIR/backend"

echo "=========================================="
echo "CodeBreak Comprehensive Deployment Script"
echo "=========================================="

echo "============================================"
echo "STEP 1: Creating Database Tables"
echo "============================================"

# Create a temporary SQL file with all the table definitions
cat > create_tables.sql << 'EOF'
-- Database tables for CodeBreak application

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create players table
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    health INTEGER DEFAULT 100,
    x INTEGER DEFAULT 0,
    y INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    inventory JSONB DEFAULT '{"code_fragments": 0, "energy_cores": 0, "data_shards": 0}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create leaderboard table
CREATE TABLE IF NOT EXISTS leaderboard (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL,
    wave_reached INTEGER DEFAULT 0,
    survival_time REAL DEFAULT 0,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create game_sessions table
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(50) NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    score INTEGER DEFAULT 0,
    enemies_defeated INTEGER DEFAULT 0,
    waves_completed INTEGER DEFAULT 0
);

-- Create items table
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(50) NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    value INTEGER DEFAULT 1,
    username VARCHAR(50) REFERENCES users(username),
    spawned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    collected_at TIMESTAMP NULL
);

-- Confirm tables were created
SELECT 'Database schema created successfully' AS message;
EOF

# Copy the SQL script directly to the remote server
echo "Copying SQL script to remote server..."
copy_to_server "create_tables.sql" "$BACKEND_DIR/"

# Check if tables exist before creating them (to avoid duplicate creation)
echo "Checking if tables already exist before creating them..."
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
    
    # Check for required tables
    required_tables = ['leaderboard', 'game_sessions', 'items']
    missing_tables = [table for table in required_tables if table not in tables]
    
    if missing_tables:
        print(f'Tables missing: {missing_tables}. Creation needed.')
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
    echo "Some tables are missing. Running database creation script..."
    run_ssh_command "cd $BACKEND_DIR && sudo -u postgres psql -d codebreak_db -f create_tables.sql"
elif [ $TABLES_CHECK -eq 1 ]; then
    echo "Error checking tables. Will attempt to run creation script anyway..."
    run_ssh_command "cd $BACKEND_DIR && sudo -u postgres psql -d codebreak_db -f create_tables.sql"
else
    echo "All required database tables already exist. Skipping creation."
fi

echo "================================================"
echo "STEP 2: Server Management and Code Deployment"
echo "================================================"

# Original nano.ssh script functionality
run_ssh_command "cd $BACKEND_DIR && echo '>>> [1] Switching to backend directory'"

echo ">>> [2] Stopping the CodeBreak service"
run_ssh_command "sudo systemctl stop codebreak"

echo ">>> [3] Pulling latest code from GitHub"
run_ssh_command "cd $REMOTE_DIR && git pull origin sub-branch"

echo ">>> [4] Activating virtual environment"
run_ssh_command "cd $REMOTE_DIR && source venv/bin/activate"

echo ">>> [5] Installing/updating dependencies"
run_ssh_command "cd $REMOTE_DIR && source venv/bin/activate && pip install -r backend/requirements.txt"

echo ">>> [6] Installing WebSocket dependencies for real-time gameplay"
run_ssh_command "cd $REMOTE_DIR && source venv/bin/activate && pip install websockets python-socketio"

echo ">>> [7] Configuring real-time server settings"
run_ssh_command "sudo sed -i 's/ExecStart=.*/ExecStart=\/home\/ubuntu\/codebreak-new\/venv\/bin\/python -m uvicorn server_postgres:app --host 0.0.0.0 --port 8000 --ws-ping-interval 20 --ws-ping-timeout 30/' /etc/systemd/system/codebreak.service && sudo systemctl daemon-reload"

echo ">>> [8] Restarting the CodeBreak service"
run_ssh_command "sudo systemctl start codebreak"

echo ">>> [9] Checking service status"
run_ssh_command "sudo systemctl status codebreak"

echo ">>> Server is running as a system service with real-time support"

# Check server logs for specific errors:
echo ">>> [10] Checking server logs for errors"
run_ssh_command "sudo journalctl -u codebreak -n 100"

echo "================================================"
echo "Deployment complete!"
echo "================================================"
echo "The server is now running with the latest code and database tables."
echo "You can access the API at: http://$EC2_HOST:8000"
echo "================================================"

# Remove local temporary files
rm -f create_tables.sql

echo "Local cleanup completed."