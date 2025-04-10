import pygame
import requests
import asyncio
import websockets
import json
from effects import GameEffects

# Handles player animations, movement, and actions.

# player.py
import pygame

class Player:
    def __init__(self, sprite_sheet, x, y, speed=5):
        # Position and movement
        self.x = x                                  
        self.y = y
        self.speed = speed
        self.direction = "down"  # Default direction
        self.width = 48
        self.height = 48
        self.game_ref = None 
        
        # Stats
        self.health = 100
        self.max_health = 100
        self.energy = 100
        self.max_energy = 100
        self.shield = 0
        
        # State
        self.attacking = False
        self.is_dashing = False
        self.is_invincible = False
        self.is_moving = False  # Add movement state tracking
        
        
        # Timers
        self.attack_start_time = 0
        self.attack_duration = 300  # milliseconds
        self.invincibility_timer = 0
        self.invincibility_duration = 1000  # milliseconds
        self.last_projectile_time = 0
        self.projectile_cooldown = 500  # milliseconds
        
        # Projectiles
        self.projectiles = []
        self.projectile_speed = 7
        
        # Animation
        self.sprite_width = 48
        self.sprite_height = 48
        self.frame_index = 0
        self.sprite = None
        
        # Inventory
        self.inventory = {
            "code_fragments": 0,
            "energy_cores": 0,
            "data_shards": 0
        }
        self.username = "Player1"  # Replace with a dynamic username input
        self.server_url = "http://localhost:8000"
        self.ws = None
        self.connected = False

        # DO NOT use asyncio.run() here as it creates a new event loop
        # Instead, store the coroutines to be run later
        self.pending_init = True
        
        # Equipment
        self.equipped_weapon = None
        self.equipped_tool = None
        self.crafted_items = []
        
        # Crafting recipes
        self.crafting_recipes = {
            "energy_sword": {
                "code_fragments": 5,
                "energy_cores": 3,
                "data_shards": 1,
                "stats": {"damage": 20, "speed": 1.5}
            },
            "data_shield": {
                "code_fragments": 3,
                "energy_cores": 2,
                "data_shards": 3,
                "stats": {"defense": 15, "duration": 10}
            },
            "hack_tool": {
                "code_fragments": 4,
                "energy_cores": 4,
                "data_shards": 2,
                "stats": {"range": 100, "cooldown": 5}
            }
        }
        
        # Check if sprite_sheet is a single surface or a sheet
        if sprite_sheet.get_width() == self.sprite_width and sprite_sheet.get_height() == self.sprite_height:
            # It's a single sprite
            self.is_single_sprite = True
            self.sprite = sprite_sheet
            # Create placeholder animations using the single sprite
            self.walk_right = [sprite_sheet] * 4
            self.walk_left = [sprite_sheet] * 4
            self.walk_up = [sprite_sheet] * 4
            self.walk_down = [sprite_sheet] * 4
            self.crafting = [sprite_sheet] * 4
            self.attack = [sprite_sheet] * 4
            self.idle = sprite_sheet
        else:
            # It's a sprite sheet
            self.is_single_sprite = False
            # Load animations from sprite sheet
            self.load_animations(sprite_sheet)
        
        # Effects
        self.effects = GameEffects()
        
        # Active effects
        self.active_effects = {}



    def set_game_reference(self, game):
        """Set a reference to the game instance"""
        self.game_ref = game
        # Add these methods to your Player class for authentication

    async def register_user(self, username, password):
        """Register a new user with the backend"""
        try:
            url = f"{self.server_url}/register/user"
            data = {
                "username": username,
                "password": password
            }
            response = requests.post(url, json=data)
        
            if response.status_code == 200:
                print(f"Successfully registered user: {username}")
                self.username = username
                return response.json()
            else:
                print(f"Failed to register user. Status code: {response.status_code}")
                print(response.text)
            return None
        except Exception as e:
            print(f"Error registering user: {e}")
        return None

    async def login(self, username, password):
        """Login and get authentication token"""
        try:
            url = f"{self.server_url}/token"
            data = {
                "username": username,
                "password": password
            }
            # Use form data for OAuth2 password flow
            response = requests.post(url, data=data)
        
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                self.username = username
                print(f"Successfully logged in as: {username}")
                return token_data
            else:
                print(f"Failed to login. Status code: {response.status_code}")
                print(response.text)
            return None
        except Exception as e:
            print(f"Error logging in: {e}")
        return None

    async def connect_to_server_with_auth(self):
        """Opens WebSocket connection with authentication token"""
        try:
            if not hasattr(self, 'auth_token'):
                print("Not authenticated, connecting without token")
                self.ws = await websockets.connect(f"ws://localhost:8000/ws/{self.username}")
            else:
                # Include token in the connection
                self.ws = await websockets.connect(
                    f"ws://localhost:8000/ws/{self.username}?token={self.auth_token}"
                )
            
            self.connected = True
            print(f"Connected to WebSocket as {self.username}")
            
            # Request all current players
            if self.ws:
                try:
                    request_data = {
                        "action": "get_all_players"
                    }
                    await self.ws.send(json.dumps(request_data))
                except Exception as e:
                    print(f"Failed to request player list: {e}")
        
            # Start background task to listen for server messages
            self.listener_task = asyncio.create_task(self.listen_for_server_messages())
            
            # Start background task to periodically refresh player list
            self.refresh_task = asyncio.create_task(self.periodic_refresh())
            
        except Exception as e:
            self.connected = False
            print(f"Failed to connect to WebSocket: {e}")
            
    async def periodic_refresh(self):
        """Periodically requests all players from the server"""
        refresh_interval = 10  # Seconds between refreshes
        
        try:
            while self.connected and self.ws:
                # Wait for the specified interval
                await asyncio.sleep(refresh_interval)
                
                # Request all players
                if self.ws:
                    try:
                        request_data = {
                            "action": "get_all_players"
                        }
                        await self.ws.send(json.dumps(request_data))
                    except Exception as e:
                        print(f"Failed to request player list during refresh: {e}")
                        if not self.connected:
                            break
        except asyncio.CancelledError:
            # Task was cancelled, clean exit
            pass
        except Exception as e:
            print(f"Error in periodic refresh: {e}")
            if self.connected:
                self.connected = False

    async def end_game_session(self, session_id, score, enemies_defeated, waves_completed):
        """End the current game session with stats"""
        if not hasattr(self, 'auth_token'):
            print("Not authenticated, cannot end game session")
            return None    
        try:
            url = f"{self.server_url}/game-sessions/{session_id}"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            data = {
                "score": score,
                "enemies_defeated": enemies_defeated,
                "waves_completed": waves_completed
            }
            response = requests.put(url, json=data, headers=headers)
        
            if response.status_code == 200:
                print("Successfully ended game session")
                return response.json()
            else:
                print(f"Failed to end game session. Status code: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Error ending game session: {e}")
        return None

    # Update the existing initialize_server_connection method to use authentication
    async def initialize_server_connection(self, username=None, password=None):
        """Initialize all server connections with optional authentication"""
        try:
            if username and password:
                # First try to login
                login_result = await self.login(username, password)
                if not login_result:
                    # If login fails, try to register
                    register_result = await self.register_user(username, password)
                    if register_result:
                        # After registration, login again
                        login_result = await self.login(username, password)
        
            # Connect to WebSocket with authentication if available
            await self.connect_to_server_with_auth()
        
            # Send initial state
            await self.send_update()
        
            # Mark initialization as complete
            self.pending_init = False
        except Exception as e:
            print(f"Failed to initialize server connection: {e}")

    
    def register_player(self):
        """Registers player with the FastAPI backend"""
        try:
            url = f"{self.server_url}/register/"
            data = {
                "username": self.username,
                "health": self.health,
                "x": self.x,
                "y": self.y
            }
            response = requests.post(url, params=data)
            if response.status_code == 200:
                print(f"Successfully registered player: {self.username}")
                print(response.json())
            else:
                print(f"Failed to register player. Status code: {response.status_code}")
                print(response.text)  # Print response text for debugging
        except Exception as e:
            print(f"Error registering player: {e}")
            return None
        return response.json()  # Return the response

    async def connect_to_server(self):
        """Opens WebSocket connection for real-time interactions"""
        try:
            self.ws = await websockets.connect(f"ws://localhost:8000/ws/{self.username}")
            self.connected = True
            print(f"Connected to WebSocket as {self.username}")
            
            # Start background task to listen for server messages
            # Store the task so it's not garbage collected
            self.listener_task = asyncio.create_task(self.listen_for_server_messages())
        except Exception as e:
            self.connected = False
            print(f"Failed to connect to WebSocket: {e}")

    async def disconnect(self):
        """Gracefully disconnect from the server and clean up tasks"""
        self.connected = False
        
        # Cancel refresh task if it exists
        if hasattr(self, 'refresh_task') and self.refresh_task:
            try:
                self.refresh_task.cancel()
                await asyncio.sleep(0.1)  # Give it a moment to cancel
            except Exception as e:
                print(f"Error cancelling refresh task: {e}")
                
        # Close websocket if it exists
        if hasattr(self, 'ws') and self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                print(f"Error closing websocket: {e}")
                
        print("Disconnected from server")

    async def listen_for_server_messages(self):
        """Listen for incoming messages from the server"""
        if not self.connected or not self.ws:
            print("WebSocket not connected, cannot listen for messages")
            return
            
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                print(f"Received from server: {data}")
                
                # Handle different message types
                if "event" in data:
                    await self.handle_server_event(data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
            await self.disconnect()
        except Exception as e:
            print(f"Error in WebSocket listener: {e}")
            await self.disconnect()

    async def handle_server_event(self, data):
        """Handle different types of server events"""
        event_type = data.get("event")
    
        if event_type == "player_joined":
            joined_username = data.get('username')
            print(f"Player joined: {joined_username}")
            if joined_username != self.username:  # Don't show for self
                if hasattr(self, "game_ref") and self.game_ref:
                    # Add player to other_players list
                    self.game_ref.other_players[joined_username] = {
                        "x": 0,  # Default position until we get an update
                        "y": 0,
                        "direction": "down",
                        "last_update": pygame.time.get_ticks(),
                        "sprite": self.idle  # Use player's idle sprite
                    }
                if hasattr(self, "game_ref") and hasattr(self.game_ref, "chat_system"):
                    if self.game_ref and hasattr(self.game_ref, "chat_system"):
                        self.game_ref.chat_system.add_message("", f"{joined_username} joined the game", system_message=True)
    
        elif event_type == "player_left":
            left_username = data.get("username", "Unknown")
            print(f"Player left: {left_username}")
            # Remove player from other_players list
            if hasattr(self, "game_ref") and self.game_ref and left_username in self.game_ref.other_players:
                del self.game_ref.other_players[left_username]
            if hasattr(self, "game_ref") and hasattr(self.game_ref, "chat_system"):
                if self.game_ref and hasattr(self.game_ref, "chat_system") and self.game_ref.chat_system:
                    self.game_ref.chat_system.add_message("", f"{left_username} left the game", system_message=True)
    
        elif event_type == "item_drop":
            print(f"Item dropped at x:{data.get('x')}, y:{data.get('y')}")
    
        elif event_type == "server_message":
            print(f"Server message: {data.get('message')}")
    
        elif event_type == "update":
            print(f"{data['player']['username']} moved to {data['player']['position']}")
    
        elif event_type == "chat_message":
            sender = data.get("username", "Unknown")
            message = data.get("message", "")
            if hasattr(self, "game_ref") and hasattr(self.game_ref, "chat_system"):
                if self.game_ref and hasattr(self.game_ref, "chat_system") and self.game_ref.chat_system:
                    self.game_ref.chat_system.add_message(sender, message)
            print(f"Chat: {sender}: {message}")

        elif event_type == "player_moved":
            username = data.get("username")
            position = data.get("position")
            direction = data.get("direction", "down")  # Get direction with default
            
            if username != self.username and position:  # Only track other players
                # Update other player position in the game
                if hasattr(self, "game_ref") and self.game_ref:
                    # Create player data if not exists
                    if not hasattr(self.game_ref, "other_players"):
                        self.game_ref.other_players = {}
                        
                    if username not in self.game_ref.other_players:
                        self.game_ref.other_players[username] = {
                            "x": position["x"],
                            "y": position["y"],
                            "direction": direction,  # Use direction from server
                            "last_update": pygame.time.get_ticks(),
                            "sprite": self.idle  # Use a copy of the player's sprite for now
                        }
                    else:
                        # Update existing player data
                        self.game_ref.other_players[username]["x"] = position["x"]
                        self.game_ref.other_players[username]["y"] = position["y"]
                        self.game_ref.other_players[username]["direction"] = direction  # Use direction from server
                        self.game_ref.other_players[username]["last_update"] = pygame.time.get_ticks()
                        
                        # Store previous position for next update
                        self.game_ref.other_players[username]["prev_x"] = position["x"]
                        self.game_ref.other_players[username]["prev_y"] = position["y"]

        elif event_type == "all_players":
            players_list = data.get("players", [])
            print(f"Received list of {len(players_list)} players from server")
            
            if hasattr(self, "game_ref") and self.game_ref:
                # Make sure other_players exists
                if not hasattr(self.game_ref, "other_players"):
                    self.game_ref.other_players = {}
                
                # Add all players to our tracking dict
                for player_data in players_list:
                    player_username = player_data.get("username")
                    
                    # Skip ourselves
                    if player_username == self.username:
                        continue
                        
                    # Create or update player entry
                    if player_username not in self.game_ref.other_players:
                        self.game_ref.other_players[player_username] = {
                            "x": player_data.get("x", 0),
                            "y": player_data.get("y", 0),
                            "direction": "down",  # Default direction
                            "last_update": pygame.time.get_ticks(),
                            "sprite": self.idle  # Use a copy of the player's sprite for now
                        }
                    else:
                        # Just update position if we're already tracking this player
                        self.game_ref.other_players[player_username]["x"] = player_data.get("x", 0)
                        self.game_ref.other_players[player_username]["y"] = player_data.get("y", 0)
                        self.game_ref.other_players[player_username]["last_update"] = pygame.time.get_ticks()

    async def send_update(self):
        """Sends updated player data to the server"""
        if self.ws:
            update_data = {
                "action": "update_position",
                "x": self.x,
                "y": self.y,
                "health": self.health,
                "inventory": self.inventory,
                "direction": self.direction  # Include player direction
            }
            await self.ws.send(json.dumps(update_data))

    def load_animations(self, sheet):
        """Load all animation frames from sprite sheet."""
        try:
            # Check if sheet is large enough for all frames
            if sheet.get_width() >= self.sprite_width * 4 and sheet.get_height() >= self.sprite_height * 6:
                # Extract animation frames
                self.walk_right = [self.get_frame(sheet, i, 0) for i in range(4)]
                self.walk_left = [self.get_frame(sheet, i, 1) for i in range(4)]
                self.walk_up = [self.get_frame(sheet, i, 2) for i in range(4)]
                self.walk_down = [self.get_frame(sheet, i, 3) for i in range(4)]
                self.crafting = [self.get_frame(sheet, i, 4) for i in range(4)]
                self.attack = [self.get_frame(sheet, i, 5) for i in range(4)]
                self.idle = self.walk_down[0]  # Default idle sprite
            else:
                # Sheet is too small, use it as a single sprite for all animations
                print("Warning: Sprite sheet too small, using as single sprite")
                self.walk_right = [sheet] * 4
                self.walk_left = [sheet] * 4
                self.walk_up = [sheet] * 4
                self.walk_down = [sheet] * 4
                self.crafting = [sheet] * 4
                self.attack = [sheet] * 4
                self.idle = sheet
        except Exception as e:
            print(f"Error loading animations: {e}")
            # Create a fallback sprite
            fallback = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
            fallback.fill((255, 0, 255))  # Magenta for visibility
            self.walk_right = [fallback] * 4
            self.walk_left = [fallback] * 4
            self.walk_up = [fallback] * 4
            self.walk_down = [fallback] * 4
            self.crafting = [fallback] * 4
            self.attack = [fallback] * 4
            self.idle = fallback
            
        # Set initial sprite
        self.sprite = self.idle

    def get_frame(self, sheet, frame, row):
        """Extract a single frame from sprite sheet."""
        return sheet.subsurface(pygame.Rect(
            frame * self.sprite_width,
            row * self.sprite_height,
            self.sprite_width,
            self.sprite_height
        ))

    async def move(self, keys, world_generator):
        """Handle player movement based on key input."""
        moving = False
        
        # Store original position in case we need to revert
        original_x = self.x
        original_y = self.y
        
        # Handle movement keys
        if keys[pygame.K_UP]:
            self.y -= self.speed
            self.direction = "up"
            moving = True
            
        if keys[pygame.K_DOWN]:
            self.y += self.speed
            self.direction = "down"
            moving = True
            
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.direction = "left"
            moving = True
            
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.direction = "right"
            moving = True
        
        # Check if new position is valid
        if moving and world_generator:
            # Create player collision rect
            player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            
            # Check collision with world blocks
            if not world_generator.is_valid_position(self.x, self.y):
                # Revert position if collision detected
                self.x = original_x
                self.y = original_y
                moving = False
                return moving
            
            # Check collision with world objects
            for obj in world_generator.objects:
                if obj.collides_with(player_rect):
                    # Revert position if collision detected
                    self.x = original_x
                    self.y = original_y
                    moving = False
                    return moving
        
        # Only if the player actually moved, send an update
        if moving:
            await self.send_update()
            
        return moving

    async def animate(self, moving, keys, enemies):
        """Update player animation and handle actions."""
        current_time = pygame.time.get_ticks()
        action_taken = False  # Initialize action_taken
        
        # Update invincibility
        if self.is_invincible and current_time - self.invincibility_timer >= self.invincibility_duration:
            self.is_invincible = False
        
        # Handle attack input
        if keys[pygame.K_SPACE]:
            self.attacking = True
            action_taken = True  # Mark action as taken
            self.attack_start_time = current_time
            self.effects.play_attack_sound()
            
            # Apply weapon damage if equipped
            self.damage = self.use_equipped_item()
        
        if keys[pygame.K_f] and current_time - self.last_projectile_time >= self.projectile_cooldown:
            await self.fire_projectile()
            self.last_projectile_time = current_time
            action_taken = True  # Mark action as taken
            
        # Handle tool input (e.g., shield)
        if keys[pygame.K_e] and self.equipped_tool:
            await self.use_tool()
            action_taken = True  # Mark action as taken
        
        # Choose sprite based on state
        if self.attacking:
            # Attack animation
            self.frame_index = (current_time // 100) % 3
            if self.direction in ["right", "left"]:
                self.sprite = self.attack[self.frame_index]
            else:
                # Default to idle for other directions
                self.sprite = self.idle
            
            # Check if attack is finished
            if current_time - self.attack_start_time > self.attack_duration:
                self.attacking = False
                self.damage = 10  # Reset to base damage
                
        elif moving:
            # Walking animation
            self.frame_index = (current_time // 150) % 4
            
            if self.direction == "right":
                self.sprite = self.walk_right[self.frame_index]
            elif self.direction == "left":
                self.sprite = self.walk_left[self.frame_index]
            elif self.direction == "up":
                self.sprite = self.walk_up[self.frame_index]
            elif self.direction == "down":
                self.sprite = self.walk_down[self.frame_index]
        else:
            # Idle animation - use direction-appropriate first frame
            if self.direction == "right":
                self.sprite = self.walk_right[0]
            elif self.direction == "left":
                self.sprite = self.walk_left[0]
            elif self.direction == "up":
                self.sprite = self.walk_up[0]
            else:  # down or default
                self.sprite = self.walk_down[0]
        
        # Update projectiles
        await self.update_projectiles(enemies)

        # Send state update if any action was taken
        if action_taken:
            await self.send_update()
        
        return self.sprite
    
       
    async def fire_projectile(self):
        """Create a new projectile in the current direction."""
        projectile_cost = 10.0  # Energy cost for firing projectile
        
        # Check if player has enough energy
        if self.energy < projectile_cost:
            return False
        
        # Consume energy
        self.energy = max(0, self.energy - projectile_cost)
        
        # Calculate spawn position (center of player)
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        # Create projectile
        self.projectiles.append({
            "x": center_x,
            "y": center_y,
            "dir": self.direction,
            "width": 5,
            "height": 5
        })
        
        # Play sound
        self.effects.play_hit_sound()

        # Send update to server
        await self.send_update()

        return True  # Indicate projectile was fired    

    async def update_projectiles(self, enemies):
        """Update projectile positions and check for collisions."""
        # Get screen dimensions
        screen = pygame.display.get_surface()
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Update each projectile
        projectile_hit = False  # Initialize projectile_hit
        for projectile in self.projectiles[:]:
            # Move projectile
            if projectile["dir"] == "right":
                projectile["x"] += self.projectile_speed
            elif projectile["dir"] == "left":
                projectile["x"] -= self.projectile_speed
            elif projectile["dir"] == "up":
                projectile["y"] -= self.projectile_speed
            elif projectile["dir"] == "down":
                projectile["y"] += self.projectile_speed
            
            # Check if out of bounds
            if (projectile["x"] < 0 or
                projectile["x"] > screen_width or
                projectile["y"] < 0 or
                projectile["y"] > screen_height):
                # Remove projectile
                self.projectiles.remove(projectile)
                continue
            
            # Check collisions with enemies
            for enemy in enemies[:]:
                if enemy.collides_with(projectile):
                    # Remove projectile
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    projectile_hit = True  # Set projectile_hit to True
                    break
        
        # If a projectile hit something, we'll update the server
        if projectile_hit:
            await self.send_update()

    async def decrease_health(self, amount):
        """Decrease player health if not invincible."""
        if not self.is_invincible:
            # Apply shield if available
            if self.shield > 0:
                # Absorb damage with shield
                absorbed = min(self.shield, amount)
                self.shield -= absorbed
                amount -= absorbed
            
            # Apply remaining damage to health
            if amount > 0:
                self.health = max(0, self.health - amount)
                
                # Become invincible briefly
                self.is_invincible = True
                self.invincibility_timer = pygame.time.get_ticks()

                # Check if player died
                if self.health <= 0 and self.game_ref:
                    self.game_ref.handle_player_defeat()
                
                # Notify server of damage taken
                if self.connected and self.ws:
                    try:
                        damage_data = {
                            "action": "damage_taken",
                            "amount": amount,
                            "health": self.health
                        }
                        await self.ws.send(json.dumps(damage_data))
                    except Exception as e:
                        print(f"Failed to send damage data: {e}")
                        self.connected = False
                
                # Send general update
                await self.send_update()
                
                return True  # Damage was dealt
                
        return False  # No damage was dealt

    def can_craft(self, item_name):
        """Check if player has enough resources to craft an item."""
        if item_name not in self.crafting_recipes:
            return False
            
        recipe = self.crafting_recipes[item_name]
        for resource, amount in recipe.items():
            if resource != "stats" and self.inventory.get(resource, 0) < amount:
                return False
        return True
    
    async def craft_item(self, item_name):
        """Attempt to craft an item using resources."""
        print(f"DEBUG: Player.craft_item called for {item_name}")
        
        if item_name not in self.crafting_recipes:
            print(f"DEBUG: Recipe {item_name} not found in recipes: {self.crafting_recipes.keys()}")
            return False
            
        if not self.can_craft(item_name):
            print(f"DEBUG: Cannot craft {item_name}, insufficient resources")
            for resource, amount in self.crafting_recipes[item_name].items():
                if resource != "stats":
                    has_amount = self.inventory.get(resource, 0)
                    print(f"DEBUG:   {resource}: have {has_amount}, need {amount}")
            return False
            
        # Deduct resources
        recipe = self.crafting_recipes[item_name]
        for resource, amount in recipe.items():
            if resource != "stats":
                self.inventory[resource] -= amount
        
        # Create the crafted item
        crafted_item = {
            "name": item_name,
            "stats": recipe["stats"].copy(),
            "durability": 100
        }
        
        # Add to crafted items
        self.crafted_items.append(crafted_item)
        print(f"DEBUG: Added {item_name} to crafted_items: {self.crafted_items}")
        
        # Auto-equip the newly crafted item - always equip as tool regardless of type
        # This allows all items to be used with the E key
        self.equipped_tool = crafted_item
        print(f"DEBUG: Auto-equipped {item_name} as tool")

        await self.send_update()
        return True

    async def equip_item(self, item_index):
        """Equip a crafted item."""
        if 0 <= item_index < len(self.crafted_items):
            item = self.crafted_items[item_index]
            if item["name"].endswith(("sword", "blade")):
                self.equipped_weapon = item
            else:
                self.equipped_tool = item
             # Notify server of equipment change
            if self.connected and self.ws:
                try:
                    equip_data = {
                        "action": "equip_item",
                        "item_name": item["name"],
                        "item_type": "weapon" if item["name"].endswith(("sword", "blade")) else "tool"
                    }
                    await self.ws.send(json.dumps(equip_data))
                except Exception as e:
                    print(f"Failed to send equip data: {e}")
                    self.connected = False
            
            await self.send_update()
                
    def use_equipped_item(self):
        """Use the currently equipped item."""
        if self.equipped_weapon:
            # Apply weapon effects (e.g., increased damage)
            base_damage = 10
            weapon_damage = self.equipped_weapon["stats"].get("damage", 0)
            total_damage = base_damage + weapon_damage
            
            # Decrease durability
            self.equipped_weapon["durability"] -= 1
            if self.equipped_weapon["durability"] <= 0:
                self.crafted_items.remove(self.equipped_weapon)
                self.equipped_weapon = None
                
            return total_damage
            
        return 10  # Base damage if no weapon equipped

    async def use_tool(self):
        """Use the currently equipped tool."""
        print(f"DEBUG: Player.use_tool called")
        
        if not self.equipped_tool:
            print("DEBUG: No tool equipped")
            return False
        
        # Define energy costs for tools
        tool_costs = {
            "energy_sword": 20,
            "data_shield": 25,
            "hack_tool": 15
        }
        
        # Get energy cost for current tool
        energy_cost = tool_costs.get(self.equipped_tool["name"], 10)
        
        # Check if player has enough energy
        if self.energy < energy_cost:
            print("DEBUG: Not enough energy to use tool")
            return False
        
        # Consume energy
        self.energy = max(0, self.energy - energy_cost)
        
        print(f"DEBUG: Using tool: {self.equipped_tool['name']}")
            
        # Apply tool effects based on type
        if self.equipped_tool["name"] == "data_shield":
            # Apply shield effect
            shield_amount = self.equipped_tool["stats"]["defense"]
            duration = self.equipped_tool["stats"]["duration"]
            self.shield = min(100, self.shield + shield_amount)
            print(f"DEBUG: Applied data_shield, shield now at {self.shield}")
            
            # Decrease durability
            self.equipped_tool["durability"] -= 1
            print(f"DEBUG: Tool durability now: {self.equipped_tool['durability']}")
            if self.equipped_tool["durability"] <= 0:
                self.crafted_items.remove(self.equipped_tool)
                self.equipped_tool = None
                print("DEBUG: Tool broke and was removed")
        elif self.equipped_tool["name"] == "hack_tool":
            # Apply hack effect (e.g., temporarily disable nearby enemies)
            hack_range = self.equipped_tool["stats"]["range"]
            cooldown = self.equipped_tool["stats"]["cooldown"]
            
            # Temporary effect - increases energy
            self.energy = min(self.max_energy, self.energy + 20)
            print(f"DEBUG: Used hack_tool with range {hack_range}, energy now at {self.energy}")
            
            # Decrease durability
            self.equipped_tool["durability"] -= 1
            print(f"DEBUG: Tool durability now: {self.equipped_tool['durability']}")
            if self.equipped_tool["durability"] <= 0:
                self.crafted_items.remove(self.equipped_tool)
                self.equipped_tool = None
                print("DEBUG: Tool broke and was removed")
        elif self.equipped_tool["name"] == "energy_sword":
            # Apply damage boost effect
            damage_boost = self.equipped_tool["stats"]["damage"]
            speed_boost = self.equipped_tool["stats"]["speed"]
            
            # Temporary effect - provides temporary invincibility
            self.is_invincible = True
            self.invincibility_timer = pygame.time.get_ticks()
            self.invincibility_duration = 2000  # 2 seconds of invincibility
            
            print(f"DEBUG: Used energy_sword with damage {damage_boost}, invincibility activated")
            
            # Decrease durability
            self.equipped_tool["durability"] -= 1
            print(f"DEBUG: Tool durability now: {self.equipped_tool['durability']}")
            if self.equipped_tool["durability"] <= 0:
                self.crafted_items.remove(self.equipped_tool)
                self.equipped_tool = None
                print("DEBUG: Tool broke and was removed")
            
        # Notify server of tool use
        if self.connected and self.ws:
            try:
                tool_data = {
                    "action": "use_tool",
                    "tool_name": self.equipped_tool["name"] if self.equipped_tool else "none",
                    "energy": self.energy,
                    "shield": self.shield
                }
                await self.ws.send(json.dumps(tool_data))
            except Exception as e:
                print(f"Failed to send tool use data: {e}")
                self.connected = False
        
        # Send general update
        await self.send_update()
        
        return True  # Indicate tool was used

    def update_energy(self, dt):
        """Update player energy regeneration."""
        # Base regeneration rate (energy per second)
        base_regen_rate = 2.0
        
        # Modify regeneration based on conditions
        if hasattr(self, 'is_moving') and self.is_moving:
            regen_rate = base_regen_rate * 0.5  # Reduced regeneration while moving
        elif self.attacking:
            regen_rate = base_regen_rate * 0.25  # Greatly reduced while attacking
        else:
            regen_rate = base_regen_rate  # Full regeneration while idle
        
        # Apply regeneration
        self.energy = min(self.max_energy, self.energy + regen_rate * dt)

    async def collect_energy_core(self, amount):
        """Handle energy core collection."""
        base_energy_restore = 20
        bonus_energy = amount * 5  # Scale with core value
        
        self.energy = min(self.max_energy, self.energy + base_energy_restore + bonus_energy)

        # Send update to server
        await self.send_update()