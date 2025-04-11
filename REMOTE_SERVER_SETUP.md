# Remote Server Setup Guide for CodeBreak

This guide will walk you through setting up the CodeBreak game server on a remote machine, allowing players to connect from anywhere.

## Prerequisites

- A remote server or VPS with:
  - Python 3.8+ installed
  - PostgreSQL database
  - Public IP address or domain name - 69.160.115.243
  - Open firewall ports (8000 for the API server)
- Basic knowledge of server administration and command line

## Step 1: Set Up the Server Environment

1. SSH into your server:
   ```
   ssh username@your-server-ip
   ```

2. Clone the repository:
   ```
   git clone https://github.com/yourusername/codebreak.git
   cd codebreak
   ```

3. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Step 2: Configure PostgreSQL Database

1. Install PostgreSQL if not already installed:
   ```
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   ```

2. Access PostgreSQL:
   ```
   sudo -u postgres psql
   ```

3. Create a database and user:
   ```sql
   CREATE DATABASE codebreak_db;
   CREATE USER codebreak_user WITH ENCRYPTED PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE codebreak_db TO codebreak_user;
   \q
   ```

4. Create a `.env` file in the `backend` directory with your database credentials:
   ```
   DB_NAME=codebreak_db
   DB_USER=codebreak_user
   DB_PASSWORD=your_secure_password
   DB_HOST=localhost
   DB_PORT=5432
   SECRET_KEY=your_secure_random_key
   ```

## Step 3: Set Up the Server for HTTPS (Recommended)

1. Install Certbot for Let's Encrypt SSL certificates:
   ```
   sudo apt-get install certbot
   ```

2. Obtain SSL certificate for your domain:
   ```
   sudo certbot certonly --standalone -d yourdomain.com
   ```

3. Set up a reverse proxy (Nginx or Apache) to handle SSL termination.

## Step 4: Configure CORS for Remote Connections

1. Edit the CORS settings in `backend/server_postgres.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # In production, specify actual origins like ["https://yourdomain.com"]
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

## Step 5: Start the Server

1. Run the server with appropriate network binding:
   ```
   cd backend
   uvicorn server_postgres:app --host 0.0.0.0 --port 8000
   ```

2. For production use, set up a service manager like systemd to keep the server running.

   Create a file `/etc/systemd/system/codebreak.service`:
   ```
   [Unit]
   Description=CodeBreak Game Server
   After=network.target

   [Service]
   User=yourusername
   WorkingDirectory=/path/to/codebreak/backend
   ExecStart=/path/to/codebreak/venv/bin/uvicorn server_postgres:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```
   sudo systemctl enable codebreak
   sudo systemctl start codebreak
   ```

## Step 6: Configure Clients to Use Remote Server

1. On each client machine, run the setup utility:
   ```
   python setup_remote_server.py
   ```

2. Enter your server's public IP or domain:
   ```
   http://your-server-domain.com:8000
   ```
   or
   ```
   https://your-server-domain.com  # If using SSL with proper proxy
   ```

## Troubleshooting

### Connection Issues
- Verify the server is running: `sudo systemctl status codebreak`
- Check firewall settings: `sudo ufw status`
- Ensure port 8000 is open: `sudo ufw allow 8000/tcp`

### Database Issues
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check database connection: `psql -U codebreak_user -d codebreak_db -h localhost`

### Server Logs
- Check the server logs: `sudo journalctl -u codebreak`

## Security Considerations

1. Use strong passwords for database and user accounts
2. Implement HTTPS with valid SSL certificates
3. Restrict CORS to specific origins in production
4. Set up a firewall to restrict access to necessary ports only
5. Regularly update the server and dependencies 