# Player Development System

## Overview

The player development system simulates realistic player attribute changes over time based on age, talent, and club quality. Development occurs automatically during season transitions (Saisonwechsel).

## Key Concepts

### Age-Based Development Curve

Players follow a realistic development curve throughout their careers:

| Age Range | Development Pattern | Typical Change per Season |
|-----------|---------------------|---------------------------|
| 16-17 | Rapid improvement | +4 to +6 strength |
| 18-19 | Fast improvement | +3 to +5 strength |
| 20-21 | Good improvement | +2 to +4 strength |
| 22-23 | Moderate improvement | +1 to +3 strength |
| 24-27 | Peak years (maintenance) | -1 to +2 strength |
| 28-29 | Early decline | -1 to -2 strength |
| 30-31 | Moderate decline | -2 to -3 strength |
| 32-34 | Significant decline | -3 to -4 strength |
| 35+ | Steep decline | -4 to -5 strength |

### Talent System

Talent (1-10) determines two critical factors:

1. **Maximum Potential**: `talent × 9`
   - Talent 10 → Maximum 90 strength
   - Talent 8 → Maximum 72 strength
   - Talent 5 → Maximum 45 strength
   - Talent 3 → Maximum 27 strength

2. **Development Speed**: Players approaching their potential develop slower
   - Below 80% of potential: Normal development speed
   - 80-90% of potential: 60% development speed
   - 90-100% of potential: 30% development speed
   - Above potential: 10% development speed (maintenance only)

**Example**: A 20-year-old player with Talent 7 and Strength 40:
- Maximum potential: 7 × 9 = 63
- Current ratio: 40/63 = 63% (below 80%)
- Development: Full speed (base +3 to +5 per year)

### Club Quality Influence

Club training facilities and coaching quality provide development bonuses:

| Average Quality | Development Bonus |
|----------------|-------------------|
| 0-20 | +0% to +4% |
| 21-40 | +4% to +8% |
| 41-60 | +8% to +12% |
| 61-80 | +12% to +16% |
| 81-100 | +16% to +20% |

**Calculation**: `bonus = 1.0 + (avg_quality / 100) × 0.2`

Where `avg_quality = (training_facilities + coaching) / 2`

**Example**: Club with training facilities 70 and coaching 80:
- Average quality: (70 + 80) / 2 = 75
- Development bonus: 1.0 + (75/100) × 0.2 = 1.15 (15% faster development)

### Randomness Factor

Each player's development includes ±15% randomness to simulate individual variation:
- Base change: 3.0
- With randomness: 2.55 to 3.45 (random.uniform(0.85, 1.15))

This ensures that not all players of the same age/talent develop identically.

## Development Formula

The complete formula for strength change:

```
strength_change = age_factor × talent_multiplier × club_bonus × randomness

Where:
- age_factor: Based on age curve (see table above)
- talent_multiplier: Based on distance from potential (0.1 to 1.0)
- club_bonus: Based on club quality (1.0 to 1.2)
- randomness: Random value between 0.85 and 1.15
```

## Attribute Development

All player attributes develop proportionally to strength changes:

- **Development Rate**: 70-90% of strength change (randomized per attribute)
- **Attributes Affected**: 
  - Ausdauer (Stamina)
  - Konstanz (Consistency)
  - Drucksicherheit (Pressure Resistance)
  - Volle (Full Pins)
  - Räumer (Clearing Pins)
  - Sicherheit (Safety)
  - Auswärts (Away Performance)
  - Start (Start Position)
  - Mitte (Middle Position)
  - Schluss (End Position)

**Example**: If strength increases by +4:
- Ausdauer might increase by +3 (75% rate)
- Konstanz might increase by +3 (80% rate)
- Volle might increase by +4 (90% rate)
- etc.

This creates natural variation between attributes while maintaining correlation with overall strength.

## Implementation Details

### When Development Occurs

Player development happens during `create_new_season()` in `simulation.py`:

1. Players age by 1 year
2. Retirement checks are performed
3. **Player development is applied** ← New step
4. Players are redistributed to age-appropriate teams

### Code Integration

```python
# In simulation.py - create_new_season()
from player_development import develop_all_players

# After aging and retirement
development_stats = develop_all_players()
```

### Main Functions

#### `develop_all_players()`
- Develops all active (non-retired) players
- Returns summary statistics
- Called during season transitions

#### `develop_player(player)`
- Develops a single player's attributes
- Returns detailed change summary
- Can be called manually for testing

#### `calculate_strength_change(player, club=None)`
- Calculates how much strength should change
- Combines age, talent, club quality, and randomness
- Returns integer change value

## Examples

### Example 1: Young Talented Player

**Player Profile:**
- Name: Max Müller
- Age: 19
- Talent: 9
- Current Strength: 55
- Club Quality: 80 (excellent facilities)

**Development Calculation:**
```
Maximum Potential: 9 × 9 = 81
Potential Ratio: 55/81 = 68% (full development speed)

Age Factor: 2.0 (age 19)
Talent Multiplier: 1.0 (below 80% of potential)
Club Bonus: 1.16 (80% quality)
Randomness: 1.05 (example)

Strength Change: 2.0 × 1.0 × 1.16 × 1.05 = +2.44 → +2

New Strength: 55 + 2 = 57
```

### Example 2: Peak-Age Average Player

**Player Profile:**
- Name: Thomas Schmidt
- Age: 26
- Talent: 5
- Current Strength: 44
- Club Quality: 50 (average facilities)

**Development Calculation:**
```
Maximum Potential: 5 × 9 = 45
Potential Ratio: 44/45 = 98% (near potential)

Age Factor: 0.1 (age 26, peak years)
Talent Multiplier: 0.3 (90-100% of potential)
Club Bonus: 1.10 (50% quality)
Randomness: 0.92 (example)

Strength Change: 0.1 × 0.3 × 1.10 × 0.92 = +0.03 → 0

New Strength: 44 (unchanged)
```

### Example 3: Declining Veteran

**Player Profile:**
- Name: Klaus Weber
- Age: 33
- Talent: 7
- Current Strength: 58
- Club Quality: 60 (good facilities)

**Development Calculation:**
```
Maximum Potential: 7 × 9 = 63
Potential Ratio: 58/63 = 92% (near potential)

Age Factor: -1.25 (age 33, declining)
Talent Multiplier: 0.3 (90-100% of potential)
Club Bonus: 1.12 (60% quality)
Randomness: 1.08 (example)

Strength Change: -1.25 × 0.3 × 1.12 × 1.08 = -0.45 → 0

Note: Club bonus applies to absolute value, so decline is:
-1.25 × 0.3 = -0.375 (before club/randomness)
Final: -0.45 → -1 (rounded)

New Strength: 58 - 1 = 57
```

## Configuration

The system uses values from `game_config.json`:

```json
{
  "player_generation": {
    "attributes": {
      "min_attribute_value": 1,
      "max_attribute_value": 99
    },
    "talent": {
      "min": 1,
      "max": 10
    }
  }
}
```

All development respects these bounds (1-99 for all attributes).

## Output and Logging

During season transitions, the system prints:

```
============================================================
PLAYER DEVELOPMENT SYSTEM
============================================================

Development Summary:
  Total players: 1247
  Improved: 523 players (+1456 total strength)
  Declined: 398 players (-892 total strength)
  Unchanged: 326 players

  Biggest improvement: Max Müller (Age 19, Talent 9)
    55 → 60 (+5)

  Biggest decline: Klaus Weber (Age 35, Talent 6)
    62 → 58 (-4)
============================================================
```

## Testing

To test player development manually:

```python
from player_development import develop_player
from models import Player

# Get a specific player
player = Player.query.get(123)

# Develop the player
result = develop_player(player)

# View results
print(f"{result['player_name']}: {result['old_strength']} → {result['new_strength']}")
print(f"Change: {result['strength_change']:+d}")
```

## Future Enhancements

Potential improvements to consider:

1. **Injury Impact**: Players recovering from injuries develop slower
2. **Playing Time**: Players who play more matches develop faster
3. **Performance-Based**: Exceptional performances boost development
4. **Training Focus**: Allow clubs to focus training on specific attributes
5. **Youth Academy**: Special development bonuses for youth team players
6. **Mentorship**: Veteran players boost development of younger teammates

