# Player Regeneration System

## Overview

The player regeneration system automatically generates new players when existing players retire, ensuring that clubs maintain a stable player population throughout the seasons.

## Implementation

### Key Features

1. **Automatic Generation**: When a player retires during season transition, a new player is automatically generated for the same club
2. **Age-Appropriate Players**: The new player's age is determined based on the club's youngest team's age group (Altersklasse)
3. **Attribute Generation**: Player attributes are generated based on the club's team strength and league level
4. **Seamless Integration**: The system is integrated into the existing retirement workflow in `start_new_season()`
5. **Manager Notifications**: If the club is the manager's club, a notification is automatically created to inform about the new player (see `NEW_PLAYER_NOTIFICATIONS.md`)

### Age Determination Logic

The system determines the appropriate age for new players using the following logic:

1. **Find Youngest Team**: Identifies the club's youngest team by checking all teams and finding the one with the youngest Altersklasse
2. **Age Range Mapping**: Uses the youngest team's Altersklasse to determine the appropriate age range:
   - **F-Jugend**: 7-8 years
   - **E-Jugend**: 9-10 years
   - **D-Jugend**: 11-12 years
   - **C-Jugend**: 13-14 years
   - **B-Jugend**: 15-16 years
   - **A-Jugend**: 17-18 years
   - **Herren**: 18-35 years
3. **Fallback**: If the club has no youth teams, generates a young adult player (17-18 years old)

### Example Scenarios

#### Scenario 1: Club with Youth Teams
- **Club**: 1. FC Zeitz II
- **Teams**: Herren, C-Jugend, D-Jugend, E-Jugend (2 teams)
- **Youngest Team**: E-Jugend
- **Generated Player Age**: 9-10 years old

#### Scenario 2: Club with Only Adult Teams
- **Club**: SG Großgrimma/Hohenmölsen
- **Teams**: Herren only
- **Youngest Team**: Herren
- **Generated Player Age**: 18-35 years old

## Modified Files

### 1. `simulation.py`

#### New Functions

**`get_age_range_for_altersklasse(altersklasse)`**
- Determines the age range for a given Altersklasse
- Returns tuple (min_age, max_age)
- Supports both long form ("A-Jugend") and short form ("A")

**`generate_retirement_age()`**
- Generates retirement age for new players
- Uses configuration from `game_config.json`
- Default: Normal distribution with mean 37.5, std dev 1.95 (80% between 35-40 years)

**`calculate_player_attribute_by_league_level(league_level, team_staerke)`**
- Calculates player attributes based on league level and team strength
- Uses configuration values from `game_config.json`
- Generates all player attributes (strength, talent, ausdauer, konstanz, etc.)

**`generate_player_name()`**
- Generates a random German player name
- Uses lists of common first names and last names

**`generate_replacement_player(club_id)`**
- Main function that generates a new player for a club
- Determines appropriate age based on youngest team
- Generates all player attributes
- Creates Player object (not yet saved to database)
- Returns the new Player object

**`create_new_player_message(player)`**
- Creates a notification message when a new player is generated
- Only creates message if the club is the manager's club
- Message type: `success` (green icon)
- Message category: `player_new`
- Includes clickable link to player profile
- Does NOT show strength or talent (secret attributes)
- See `NEW_PLAYER_NOTIFICATIONS.md` for details

#### Modified Function

**`start_new_season()`**
- Added player regeneration logic after retirement
- When a player retires:
  1. Marks player as retired
  2. Removes from all teams
  3. Creates retirement notification message
  4. **NEW**: Generates replacement player for the club
  5. Adds new player to database session
  6. **NEW**: Creates new player notification message (if club is managed)
- Tracks and reports number of new players generated

### 2. `test_player_regeneration.py` (New File)

Test script to verify the player regeneration system:
- Tests player generation for different club configurations
- Verifies ages are appropriate for youngest team's Altersklasse
- Tests with clubs that have youth teams and clubs with only adult teams
- Provides detailed output showing generated player details

## Usage

### Automatic Usage

The player regeneration system runs automatically during season transitions:

1. User clicks "Saisonwechsel" button
2. System ages all players by 1 year
3. For each player that reaches retirement age:
   - Player is marked as retired
   - Player is removed from all teams
   - Retirement notification is created (if player belongs to manager's club)
   - **New player is generated for the club**
4. New players are added to the database
5. Console output shows: "X new players generated to replace retired players"

### Testing

To test the player regeneration system:

```bash
# From the project root directory
python kegelmanager/backend/test_player_regeneration.py kegelmanager/backend/instance/kegelmanager_default.db
```

The test will:
- Analyze the first 5 clubs in the database
- Show each club's teams and their Altersklassen
- Generate a test player for each club
- Verify the generated player's age is appropriate
- Report success/failure for each test

## Configuration

Player generation uses values from `game_config.json`:

```json
{
  "player_generation": {
    "retirement": {
      "mean_age": 37.5,
      "std_dev": 1.95,
      "min_age": 30,
      "max_age": 45
    },
    "attributes": {
      "base_std_dev": 5.0,
      "league_level_factor": 0.5,
      "attr_base_value_offset": 60,
      "attr_strength_factor": 0.6,
      "attr_std_dev_base": 5.0,
      "attr_std_dev_league_factor": 0.3,
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

## Benefits

1. **Stable Player Population**: Clubs maintain their player count over time
2. **Realistic Age Distribution**: New players enter at appropriate ages for the club's youth system
3. **Automatic Management**: No manual intervention required
4. **Balanced Attributes**: New players have attributes appropriate for their club's level
5. **Seamless Integration**: Works with existing retirement and season transition systems

## Future Enhancements

Potential improvements for future versions:

1. **Youth Academy Integration**: Link player generation to club's youth academy quality
2. **Regional Variation**: Generate players with names/nationalities based on club location
3. **Talent Variation**: Higher quality youth academies generate better talents
4. **Contract Negotiation**: Automatically assign contracts based on player quality
5. **Team Assignment**: Automatically assign new players to appropriate teams based on age and strength

## Technical Notes

- New players are generated in the same database transaction as retirements
- Players are added to the club but not automatically assigned to specific teams
- The player redistribution system (which runs after aging) will assign new players to appropriate teams
- All new players start with German nationality ("Deutsch")
- Contract length is set to 3 years by default
- Salary is calculated as: strength × 100

## Compatibility

- Compatible with existing retirement system
- Works with age class validation system
- Integrates with player redistribution system
- Respects club-player relationship model (players belong to clubs, not teams)

