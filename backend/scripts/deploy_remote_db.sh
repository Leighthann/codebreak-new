#!/bin/bash
# Script to deploy database tables to remote server

# Constants - update these with your AWS instance details
EC2_HOST="ec2-3-130-249-194.us-east-2.compute.amazonaws.com"
KEY_PATH="../codebreak-key.pem"
REMOTE_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/codebreak-new/backend"

echo "Deploying database tables to remote server..."

# Check if the key file exists
if [ ! -f "$KEY_PATH" ]; then
    echo "Error: SSH key file not found at $KEY_PATH"
    exit 1
fi

# 1. Copy the SQL script to the server
echo "Copying SQL script to remote server..."
scp -i "$KEY_PATH" create_tables.sql $REMOTE_USER@$EC2_HOST:$REMOTE_DIR/scripts/

# 2. Copy the Python deployment script
echo "Copying deployment script to remote server..."
scp -i "$KEY_PATH" deploy-tables.py $REMOTE_USER@$EC2_HOST:$REMOTE_DIR/scripts/

# 3. Run the Python script on the server
echo "Running deployment script on remote server..."
ssh -i "$KEY_PATH" $REMOTE_USER@$EC2_HOST "cd $REMOTE_DIR && source venv/bin/activate && python scripts/deploy-tables.py"

echo "Database deployment complete!"