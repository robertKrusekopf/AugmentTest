"""
Game Configuration Module

This module handles loading and validation of game configuration from JSON files.
It provides a centralized way to access all game parameters.
"""

import json
import os
from typing import Any, Dict, Optional


class GameConfig:
    """
    Game configuration manager.
    
    Loads configuration from game_config.json and provides easy access to all parameters.
    """
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance exists."""
        if cls._instance is None:
            cls._instance = super(GameConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration."""
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: Optional[str] = None):
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to config file. If None, uses default 'game_config.json'
        """
        if config_path is None:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, 'game_config.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            # Validate config if enabled
            if self.get('validation.enabled', True):
                self._validate_config()
            
            print(f"✓ Configuration loaded from {config_path}")
            
        except FileNotFoundError:
            print(f"⚠ Config file not found: {config_path}")
            print("  Using default values")
            self._config = self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing config file: {e}")
            print("  Using default values")
            self._config = self._get_default_config()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the config value (e.g., 'player_generation.retirement.mean_age')
            default: Default value if key not found
            
        Returns:
            The configuration value or default
            
        Examples:
            >>> config = GameConfig()
            >>> config.get('player_generation.retirement.mean_age')
            37.5
            >>> config.get('simulation.home_advantage.factor')
            1.02
        """
        if self._config is None:
            self.load_config()
        
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name (e.g., 'player_generation', 'simulation')
            
        Returns:
            Dictionary containing the section data
        """
        return self.get(section, {})
    
    def reload(self):
        """Reload configuration from file."""
        self._config = None
        self.load_config()
    
    def _validate_config(self):
        """Validate configuration values."""
        strict_mode = self.get('validation.strict_mode', False)
        errors = []
        warnings = []
        
        # Validate retirement settings
        retirement = self.get_section('player_generation.retirement')
        if retirement:
            mean = retirement.get('mean_age', 0)
            min_age = retirement.get('min_age', 0)
            max_age = retirement.get('max_age', 0)
            
            if not (min_age <= mean <= max_age):
                errors.append(f"Retirement mean_age ({mean}) must be between min_age ({min_age}) and max_age ({max_age})")
        
        # Validate player rating weights
        rating = self.get_section('player_rating')
        if rating:
            weights_sum = (
                rating.get('strength_weight', 0) +
                rating.get('konstanz_weight', 0) +
                rating.get('drucksicherheit_weight', 0) +
                rating.get('volle_weight', 0) +
                rating.get('raeumer_weight', 0)
            )
            if abs(weights_sum - 1.0) > 0.01:
                warnings.append(f"Player rating weights sum to {weights_sum:.2f}, should be 1.0")
        
        # Validate home advantage
        home_adv = self.get('simulation.home_advantage.factor', 1.0)
        if home_adv < 0.9 or home_adv > 1.2:
            warnings.append(f"Home advantage factor ({home_adv}) seems unusual (expected 0.9-1.2)")
        
        # Validate attribute ranges
        attr = self.get_section('player_generation.attributes')
        if attr:
            min_val = attr.get('min_attribute_value', 1)
            max_val = attr.get('max_attribute_value', 99)
            if min_val >= max_val:
                errors.append(f"min_attribute_value ({min_val}) must be less than max_attribute_value ({max_val})")
        
        # Print validation results
        if warnings:
            print("\n⚠ Configuration Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        
        if errors:
            print("\n❌ Configuration Errors:")
            for error in errors:
                print(f"  - {error}")
            
            if strict_mode:
                raise ValueError("Configuration validation failed in strict mode")
        
        if not warnings and not errors:
            print("✓ Configuration validation passed")
    
    def _get_default_config(self) -> Dict:
        """
        Get default configuration values.
        
        Returns:
            Dictionary with default configuration
        """
        return {
            "player_generation": {
                "retirement": {
                    "mean_age": 37.5,
                    "std_dev": 1.95,
                    "min_age": 30,
                    "max_age": 45
                },
                "age_ranges": {
                    "youth_min": 16,
                    "youth_max": 19,
                    "adult_min": 20,
                    "adult_max": 35
                },
                "attributes": {
                    "base_std_dev": 5.0,
                    "league_level_factor": 0.5,
                    "min_attribute_value": 1,
                    "max_attribute_value": 99
                },
                "talent": {
                    "min": 1,
                    "max": 10
                }
            },
            "simulation": {
                "home_advantage": {
                    "factor": 1.02
                },
                "player_availability": {
                    "unavailability_min": 0.0,
                    "unavailability_max": 0.30
                }
            },
            "validation": {
                "enabled": True,
                "strict_mode": False
            }
        }
    
    def save_config(self, config_path: Optional[str] = None):
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to save config file. If None, uses default 'game_config.json'
        """
        if config_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, 'game_config.json')
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            print(f"✓ Configuration saved to {config_path}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def __repr__(self):
        """String representation of config."""
        return f"GameConfig(loaded={self._config is not None})"


# Global config instance
_global_config = None


def get_config() -> GameConfig:
    """
    Get the global configuration instance.
    
    Returns:
        GameConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = GameConfig()
    return _global_config


# Convenience functions for common config access
def get_retirement_config():
    """Get retirement configuration."""
    return get_config().get_section('player_generation.retirement')


def get_simulation_config():
    """Get simulation configuration."""
    return get_config().get_section('simulation')


def get_player_generation_config():
    """Get player generation configuration."""
    return get_config().get_section('player_generation')


if __name__ == '__main__':
    # Test the configuration system
    print("="*60)
    print("Testing Game Configuration System")
    print("="*60)
    
    config = GameConfig()
    
    print("\n1. Testing dot notation access:")
    print(f"   Retirement mean age: {config.get('player_generation.retirement.mean_age')}")
    print(f"   Home advantage: {config.get('simulation.home_advantage.factor')}")
    print(f"   Talent range: {config.get('player_generation.talent.min')}-{config.get('player_generation.talent.max')}")
    
    print("\n2. Testing section access:")
    retirement = config.get_section('player_generation.retirement')
    print(f"   Retirement config: {retirement}")
    
    print("\n3. Testing default values:")
    print(f"   Non-existent key: {config.get('does.not.exist', 'DEFAULT_VALUE')}")
    
    print("\n" + "="*60)

