# Age-Based Strength Generation

## Overview

The age-based strength generation system ensures that newly generated players have realistic initial strength values based on their age. This creates a more authentic player development experience where young players start weaker but have room to grow, while peak-age players are already well-developed.

## Key Features

### 1. Age-Based Development Curve

Players are categorized into four age groups, each with different strength ranges:

| Age Group | Age Range | Initial Strength | Description |
|-----------|-----------|------------------|-------------|
| **Young Players** | 16-23 years | 50-70% of max potential | Just starting their careers, significant room to develop |
| **Peak Players** | 24-27 years | 80-95% of max potential | In their prime, near full development |
| **Mature Players** | 28-32 years | 75-90% of max potential | Experienced but starting to decline slightly |
| **Veteran Players** | 33+ years | 65-85% of max potential | Past their peak, lower strength |

### 2. Talent Integration

The system respects the talent-based maximum potential system:
- **Maximum Potential** = Talent × 9
- A player's strength will **never exceed** their maximum potential
- Example: A player with Talent 8 can have a maximum strength of 72

### 3. Realistic Development Opportunities

Young talented players have significant room to develop:
- An 18-year-old with Talent 9 might start with strength 45 (55% of max 81)
- Through the player development system, they can grow to reach their full potential of 81
- This creates strategic value in scouting and developing young talent

## Configuration

The system is configured in `game_config.json`:

```json
{
  "player_generation": {
    "age_based_strength": {
      "enabled": true,
      "young_players": {
        "age_min": 16,
        "age_max": 23,
        "potential_min": 0.50,
        "potential_max": 0.70
      },
      "peak_players": {
        "age_min": 24,
        "age_max": 27,
        "potential_min": 0.80,
        "potential_max": 0.95
      },
      "mature_players": {
        "age_min": 28,
        "age_max": 32,
        "potential_min": 0.75,
        "potential_max": 0.90
      },
      "veteran_players": {
        "age_min": 33,
        "age_max": 45,
        "potential_min": 0.65,
        "potential_max": 0.85
      }
    }
  }
}
```

### Customization Options

You can adjust the following parameters:

1. **Age Ranges**: Modify `age_min` and `age_max` for each category
2. **Potential Ranges**: Adjust `potential_min` and `potential_max` to change strength distribution
3. **Enable/Disable**: Set `enabled: false` to use the old system without age-based modifiers

## Examples

### Example 1: Young Talent

**Player Profile:**
- Age: 18 years
- Talent: 9
- League: Bundesliga (Level 1)
- Team Strength: 70

**Result:**
- Maximum Potential: 9 × 9 = 81
- Age Modifier: ~60% (young player range: 50-70%)
- Initial Strength: ~45-50
- **Development Room**: 31-36 points (38-44% growth potential)

### Example 2: Peak Player

**Player Profile:**
- Age: 26 years
- Talent: 7
- League: Regionalliga (Level 3)
- Team Strength: 60

**Result:**
- Maximum Potential: 7 × 9 = 63
- Age Modifier: ~87% (peak player range: 80-95%)
- Initial Strength: ~55-60
- **Development Room**: 3-8 points (5-13% growth potential)

### Example 3: Veteran Player

**Player Profile:**
- Age: 35 years
- Talent: 8
- League: Oberliga (Level 5)
- Team Strength: 50

**Result:**
- Maximum Potential: 8 × 9 = 72
- Age Modifier: ~75% (veteran range: 65-85%)
- Initial Strength: ~50-55
- **Development Room**: Limited (player will likely decline with age)

## Integration with Player Development System

The age-based strength generation works seamlessly with the player development system:

1. **Initial Generation**: Young players start with lower strength based on their age
2. **Season-End Development**: Players develop according to age-based curves
3. **Career Progression**: 
   - Young players (16-23): Rapid improvement
   - Peak players (24-27): Minimal change
   - Older players (28+): Gradual decline

### Example Career Progression

**Player: Max Müller**
- Talent: 9 (Max Potential: 81)

| Age | Strength | Change | Phase |
|-----|----------|--------|-------|
| 18  | 45       | -      | Young (55% of max) |
| 19  | 50       | +5     | Rapid development |
| 20  | 55       | +5     | Rapid development |
| 22  | 63       | +8     | Continued growth |
| 24  | 70       | +7     | Approaching peak |
| 26  | 75       | +5     | Peak years |
| 28  | 77       | +2     | Peak maintained |
| 30  | 76       | -1     | Slight decline |
| 32  | 73       | -3     | Decline begins |
| 35  | 68       | -5     | Veteran decline |

## Technical Implementation

### Files Modified

1. **`init_db.py`**: Initial database creation with age-based strength
2. **`extend_existing_db.py`**: Database extension with age-based strength
3. **`simulation.py`**: Replacement player generation with age-based strength
4. **`game_config.json`**: Configuration for age-based strength parameters

### Key Functions

#### `get_age_based_strength_modifier(age, talent)`

Calculates the age-based modifier for initial strength generation.

**Parameters:**
- `age`: Player's age
- `talent`: Player's talent (1-10)

**Returns:**
- `float`: Percentage of maximum potential (0.0-1.0)

#### `calculate_player_attribute_by_league_level(..., age=None, talent=None)`

Enhanced to accept age and talent parameters for age-based strength calculation.

**New Parameters:**
- `age`: Player's age (optional)
- `talent`: Player's talent (optional)

**Behavior:**
- If `age` is provided: Applies age-based strength modifier
- If `age` is `None`: Uses old system (backward compatible)

## Testing

Run the test suite to verify the implementation:

```bash
cd kegelmanager/backend
python test_age_based_strength.py
```

The test suite validates:
1. Age-based strength modifiers are within expected ranges
2. Young players have lower initial strength
3. Peak players have higher initial strength
4. Strength respects talent-based maximum
5. Young talented players have room to develop

## Benefits

### Gameplay Benefits

1. **Realistic Career Progression**: Players follow authentic development curves
2. **Strategic Depth**: Scouting young talent becomes more valuable
3. **Long-Term Planning**: Building a team requires balancing youth and experience
4. **Player Stories**: Each player has a unique career arc

### Balance Benefits

1. **No Overpowered Youngsters**: 16-year-olds can't start with 70+ strength
2. **Veteran Realism**: Older players are appropriately weaker
3. **Development Value**: Young players have clear growth potential
4. **Talent Matters**: High-talent players have higher ceilings

## Troubleshooting

### Issue: All players start at maximum strength

**Solution**: Check that `age_based_strength.enabled` is set to `true` in `game_config.json`

### Issue: Young players are too weak

**Solution**: Adjust `young_players.potential_min` and `potential_max` to higher values (e.g., 0.60-0.80)

### Issue: Veteran players are too strong

**Solution**: Lower `veteran_players.potential_min` and `potential_max` (e.g., 0.55-0.75)

## Future Enhancements

Potential improvements for future versions:

1. **Position-Specific Curves**: Different development curves for different positions
2. **Injury Impact**: Injuries could affect development potential
3. **Training Impact**: Better training facilities could improve young player development rates
4. **Genetic Variation**: Some players could be "early bloomers" or "late bloomers"

