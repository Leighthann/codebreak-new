-- Create active_games table
CREATE TABLE IF NOT EXISTS active_games (
    game_id VARCHAR(36) PRIMARY KEY,
    host_username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create game_players table
CREATE TABLE IF NOT EXISTS game_players (
    game_id VARCHAR(36) REFERENCES active_games(game_id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, username)
);

-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) PRIMARY KEY,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create players table if it doesn't exist
CREATE TABLE IF NOT EXISTS players (
    username VARCHAR(255) PRIMARY KEY REFERENCES users(username),
    health INTEGER DEFAULT 100,
    x INTEGER DEFAULT 0,
    y INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    inventory JSONB DEFAULT '{"code_fragments": 0, "energy_cores": 0, "data_shards": 0}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create leaderboard table if it doesn't exist
CREATE TABLE IF NOT EXISTS leaderboard (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) REFERENCES users(username),
    score INTEGER NOT NULL,
    date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create game_sessions table if it doesn't exist
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) REFERENCES users(username),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    score INTEGER DEFAULT 0,
    enemies_defeated INTEGER DEFAULT 0,
    waves_completed INTEGER DEFAULT 0
);

-- Create items table if it doesn't exist
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    value INTEGER DEFAULT 1,
    spawned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
); 