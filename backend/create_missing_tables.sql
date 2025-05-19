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