# Configuration Directory

This directory contains all configuration-related files for the Kegelmanager game.

## Files

### Core Files

- **`config.py`** - Configuration module with GameConfig class
- **`game_config.json`** - Main configuration file (used by the game)
- **`__init__.py`** - Python package initialization

### Documentation

- **`README.md`** - This file
- **`CONFIG_README.md`** - Comprehensive configuration documentation
- **`CONFIG_IMPLEMENTATION_SUMMARY.md`** - Implementation details

### Examples

- **`game_config.example.json`** - Example configuration with detailed comments

## Quick Start

### 1. View Current Configuration

Open `game_config.json` to see current settings.

### 2. Modify Configuration

Edit `game_config.json`:

```json
{
  "player_generation": {
    "retirement": {
      "mean_age": 40,
      "std_dev": 2.5
    }
  }
}
```

### 3. Test Configuration

```bash
cd ..
python -c "from config import get_config; c = get_config(); print(c.get('player_generation.retirement.mean_age'))"
```

### 4. Use in Code

```python
from config import get_config

config = get_config()
mean_age = config.get('player_generation.retirement.mean_age')
```

## Documentation

For detailed documentation, see:
- **`CONFIG_README.md`** - Full configuration guide
- **`game_config.example.json`** - All available parameters with descriptions

## Configuration Sections

1. **player_generation** - Player creation settings
2. **team_generation** - Team creation settings
3. **club_generation** - Club creation settings
4. **simulation** - Match simulation parameters
5. **form_system** - Player form system
6. **lane_quality** - Lane quality by league level
7. **player_rating** - Rating formula weights
8. **season** - Season settings
9. **validation** - Config validation settings

## Support

For questions or issues:
1. Check `CONFIG_README.md`
2. Review `game_config.example.json`
3. Test with: `python config.py`

