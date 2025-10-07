"""
Game Configuration Package

This package contains all configuration-related files for the Kegelmanager game.
"""

from .config import (
    GameConfig,
    get_config,
    get_retirement_config,
    get_simulation_config,
    get_player_generation_config
)

__all__ = [
    'GameConfig',
    'get_config',
    'get_retirement_config',
    'get_simulation_config',
    'get_player_generation_config'
]

