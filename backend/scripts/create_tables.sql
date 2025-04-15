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