# Kegelmanager Game Configuration System

## Overview

The Kegelmanager game configuration system allows you to customize game behavior without modifying code. All configurable parameters are stored in `game_config.json`.

## Quick Start

1. **View current configuration**: `game_config.json`
2. **See all available options**: `game_config.example.json`
3. **Test configuration**: `python config.py`

## Configuration File Structure

```json
{
  "player_generation": { ... },
  "team_generation": { ... },
  "club_generation": { ... },
  "simulation": { ... },
  "form_system": { ... },
  "lane_quality": { ... },
  "player_rating": { ... },
  "season": { ... },
  "validation": { ... }
}
```

## Key Configuration Sections

### 1. Player Generation

#### Retirement System
```json
"retirement": {
  "mean_age": 37.5,      // Average retirement age
  "std_dev": 1.95,       // Standard deviation
  "min_age": 30,         // Minimum retirement age
  "max_age": 45          // Maximum retirement age
}
```

**Example Scenarios:**
- **Realistic Long Careers**: `mean_age: 40, std_dev: 2.5`
- **Short Careers**: `mean_age: 35, std_dev: 1.5`
- **High Variation**: `mean_age: 37.5, std_dev: 3.5`

#### Age Ranges
```json
"age_ranges": {
  "youth_min": 16,
  "youth_max": 19,
  "adult_min": 20,
  "adult_max": 35
}
```

#### Attributes
```json
"attributes": {
  "base_std_dev": 5.0,              // Base variation in strength
  "league_level_factor": 0.5,       // League level impact
  "min_attribute_value": 1,
  "max_attribute_value": 99
}
```

#### Salary
```json
"salary": {
  "base_multiplier": 100,           // salary = strength * 100 * age_factor
  "prime_age_min": 25,
  "prime_age_max": 30,
  "prime_age_factor": 1.5,          // 50% bonus for prime age
  "normal_age_factor": 1.0
}
```

### 2. Team Generation

```json
"players_per_team": {
  "level_1_4_min": 8,
  "level_1_4_max": 10,    // Top leagues: 8-10 players
  "level_5_8_min": 7,
  "level_5_8_max": 9,     // Mid leagues: 7-9 players
  "level_9_plus_min": 7,
  "level_9_plus_max": 8   // Lower leagues: 7-8 players
}
```

### 3. Club Generation

```json
"club_generation": {
  "founded_year_min": 1900,
  "founded_year_max": 1980,
  "reputation_min": 50,
  "reputation_max": 90,
  "fans_min": 500,
  "fans_max": 10000,
  "initial_balance_min": 500000,
  "initial_balance_max": 2000000
}
```

### 4. Simulation

#### Home Advantage
```json
"home_advantage": {
  "factor": 1.02          // 2% bonus for home team
}
```

#### Player Availability
```json
"player_availability": {
  "unavailability_min": 0.0,
  "unavailability_max": 0.30    // 0-30% unavailability rate
}
```

#### Scoring
```json
"scoring": {
  "base_score": 120,
  "strength_factor": 0.6,
  "away_factor_base": 0.98,
  "position_factor_base": 0.8
}
```

#### Stroh Player (Substitute)
```json
"stroh_player": {
  "strength_penalty": 0.10,       // 10% weaker than weakest real player
  "konstanz_penalty": 0.05,
  "volle_penalty": 0.03
}
```

### 5. Player Rating Formula

```json
"player_rating": {
  "strength_weight": 0.5,
  "konstanz_weight": 0.1,
  "drucksicherheit_weight": 0.1,
  "volle_weight": 0.15,
  "raeumer_weight": 0.15
}
```

**Formula**: `rating = strength*0.5 + konstanz*0.1 + drucksicherheit*0.1 + volle*0.15 + raeumer*0.15`

## Usage in Code

### Basic Usage

```python
from config import get_config

config = get_config()

# Get a single value
mean_age = config.get('player_generation.retirement.mean_age')

# Get with default value
home_advantage = config.get('simulation.home_advantage.factor', 1.02)

# Get entire section
retirement_config = config.get_section('player_generation.retirement')
```

### Convenience Functions

```python
from config import get_retirement_config, get_simulation_config

# Get specific sections
retirement = get_retirement_config()
simulation = get_simulation_config()
```

## Validation

The configuration system includes automatic validation:

```json
"validation": {
  "enabled": true,        // Enable validation
  "strict_mode": false    // false = warnings, true = errors
}
```

**Validation Checks:**
- Retirement mean_age must be between min_age and max_age
- Player rating weights must sum to 1.0
- Home advantage should be between 0.9-1.2
- Attribute min must be less than max

## Testing Configuration

Run the configuration test:

```bash
python config.py
```

This will:
1. Load the configuration
2. Run validation
3. Display sample values
4. Show any warnings or errors

## Example Configurations

### Realistic Mode
```json
{
  "player_generation": {
    "retirement": {
      "mean_age": 40,
      "std_dev": 2.5
    },
    "salary": {
      "base_multiplier": 150
    }
  },
  "simulation": {
    "home_advantage": {
      "factor": 1.01
    }
  }
}
```

### Arcade Mode
```json
{
  "player_generation": {
    "retirement": {
      "mean_age": 35,
      "std_dev": 1.0
    },
    "age_ranges": {
      "adult_max": 30
    }
  },
  "simulation": {
    "home_advantage": {
      "factor": 1.05
    }
  }
}
```

### Hardcore Mode
```json
{
  "player_generation": {
    "retirement": {
      "mean_age": 36,
      "std_dev": 1.5
    },
    "salary": {
      "base_multiplier": 200
    }
  },
  "club_generation": {
    "initial_balance_min": 100000,
    "initial_balance_max": 500000
  },
  "simulation": {
    "player_availability": {
      "unavailability_max": 0.40
    }
  }
}
```

## Troubleshooting

### Configuration Not Loading

1. Check file exists: `game_config.json`
2. Validate JSON syntax: Use a JSON validator
3. Check console for error messages

### Values Not Applied

1. Restart the application after changing config
2. Check if validation is rejecting values
3. Verify correct key path (use dot notation)

### Validation Errors

1. Check validation messages in console
2. Compare with `game_config.example.json`
3. Disable strict_mode to see warnings instead of errors

## Best Practices

1. **Backup**: Always backup `game_config.json` before major changes
2. **Test**: Test configuration changes with `python config.py`
3. **Document**: Add comments (using `_comment` or `_description` keys)
4. **Validate**: Keep validation enabled
5. **Version**: Track config changes in version control

## Advanced Usage

### Creating Custom Profiles

Create multiple config files for different game modes:

```
game_config.json          # Default
game_config_realistic.json
game_config_arcade.json
game_config_hardcore.json
```

Load specific config:

```python
config = GameConfig()
config.load_config('game_config_realistic.json')
```

### Dynamic Configuration

Reload configuration without restarting:

```python
config = get_config()
config.reload()
```

## Configuration Reference

See `game_config.example.json` for complete list of all available parameters with detailed descriptions and examples.

## Support

For questions or issues with configuration:
1. Check `game_config.example.json` for parameter descriptions
2. Run `python config.py` to test configuration
3. Check console output for validation messages

