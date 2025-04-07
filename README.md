# CodeBreak

A cyberpunk-themed roguelike survival game built with Python and Pygame.

## Overview

CodeBreak is a top-down action game where you fight against waves of enemies, collect resources, craft tools, and try to survive as long as possible in a hostile cyber environment.

## Features

- Fast-paced gameplay with waves of increasingly difficult enemies
- Resource collection and power-ups
- Comprehensive crafting system for creating and using tools
- Multiple enemy types with different behaviors
- Cyberpunk-inspired visual style with neon colors and grid effects
- Settings panel to customize game experience

## Controls

- **Movement**: Arrow keys
- **Melee Attack**: Space
- **Ranged Attack**: F key
- **Crafting Menu**: C key
- **Use Equipped Tool**: E key
- **Pause**: ESC key

## Game Mechanics

### Resources

The game features three types of collectible resources:
- **Code Fragments**: Common resources, found throughout the world
- **Energy Cores**: Moderately rare resources that power most crafted items
- **Data Shards**: Rare resources required for advanced crafting

### Crafting System

Press C to open the crafting menu where you can craft various tools:

1. **Energy Sword**
   - Uses: 5 Code Fragments, 3 Energy Cores, 1 Data Shard
   - Effect: Provides temporary invincibility when activated
   - Usage: Press E to activate invincibility for 2 seconds

2. **Data Shield**
   - Uses: 3 Code Fragments, 2 Energy Cores, 3 Data Shards
   - Effect: Increases your shield value to absorb damage
   - Usage: Press E to activate shield protection

3. **Hack Tool**
   - Uses: 4 Code Fragments, 4 Energy Cores, 2 Data Shards
   - Effect: Replenishes energy and affects nearby enemies
   - Usage: Press E to restore energy and create a disruptive effect

All crafted items have limited durability and will break after multiple uses.

### Power-ups

Occasionally, power-ups will appear that provide temporary boosts:
- **Health**: Restores your health
- **Energy**: Restores your energy
- **Shield**: Provides temporary damage protection
- **Damage**: Increases your attack power

### Waves

Enemies spawn in waves, with each wave being more difficult than the last. Survive as long as you can to achieve the highest score! The game tracks your survival time, which is displayed in the top-right corner.

## UI Elements

- **Health Bar**: Displays current health (red)
- **Energy Bar**: Shows current energy level (cyan)
- **Shield Bar**: Appears when you have active shield protection (yellow)
- **Score and Wave**: Displayed in the top-right corner
- **Survival Time**: Shows how long you've survived
- **Inventory**: Located in the bottom-left, shows your collected resources
- **Equipped Tool**: Shown in the bottom-right when a tool is equipped

## Settings

The game includes several customizable settings:
- Sound volume
- Music volume
- Screen shake toggle
- Show damage numbers toggle
- Difficulty level (Easy, Normal, Hard)

## Strategy Tips

1. **Resource Management**: Collect resources strategically and craft the right tools for your playstyle.
2. **Tool Usage**: Use the E key at the right moment to maximize the effectiveness of your tools.
3. **Crafting Menu**: Remember that the game doesn't pause when the crafting menu is open, so find a safe spot first!
4. **Shield Protection**: The Data Shield provides the best protection against enemy attacks.
5. **Energy Conservation**: The Hack Tool can help restore energy in critical situations.

## Installation

1. Ensure you have Python 3.6+ installed
2. Install Pygame: `pip install pygame`
3. Run the game: `python game.py`

## Development

This game is still in development. Future updates may include:
- Additional enemy types
- More tool varieties and abilities
- Enhanced crafting system
- Level progression
- Boss encounters

## Known Issues

- Melee attacks (Space key) currently don't cause damage to enemies
- Some visual effects may not display correctly on certain systems