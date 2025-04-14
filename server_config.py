import json
import os

# Default server configuration
DEFAULT_CONFIG = {
    "server_url": "http://3.130.249.194:8000"
}

def load_server_config():
    """Load server configuration from file or use default."""
    try:
        with open("server_config.json", "r") as f:
            config = json.load(f)
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_CONFIG

def save_server_config(server_url):
    """Save server configuration to file."""
    config = {"server_url": server_url}
    with open("server_config.json", "w") as f:
        json.dump(config, f, indent=4)
    return config

def get_server_url():
    """Get the server URL from configuration."""
    config = load_server_config()
    return config.get("server_url", DEFAULT_CONFIG["server_url"]) 