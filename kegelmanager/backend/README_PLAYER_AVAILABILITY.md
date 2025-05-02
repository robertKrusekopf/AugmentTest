# Player Availability System

This document explains the new player availability system implemented in the Kegelmanager application.

## Overview

The player availability system simulates real-world scenarios where players might be unavailable for a match day due to shift work or other commitments. The system works as follows:

1. At the beginning of each match day, each player has a 16.7% chance of being unavailable
2. The system ensures that each club has enough players available for all of its teams playing on that match day (minimum 6 players per team)
3. The best available players are assigned to teams based on their attributes, with the best players going to the first team, the next best to the second team, and so on
4. Players can only play for one team per match day

## Implementation Details

### Database Changes

A new column has been added to the Player table:

- `is_available_current_matchday` (Boolean, default: True): Indicates whether a player is available for the current match day

### New Files

A new file has been added to handle player assignment to teams:

- `club_player_assignment.py`: Contains the function `assign_players_to_teams_for_match_day()` which assigns players to teams within a club for a specific match day

### New Functions

The following new functions have been added to the `simulation.py` file:

- `reset_player_availability()`: Resets the availability flag for all players at the beginning of a match day
- `determine_player_availability(club_id, teams_playing)`: Determines which players are available for a club on the current match day

The following new function has been added to the `club_player_assignment.py` file:

- `assign_players_to_teams_for_match_day(club_id, match_day, season_id)`: Assigns players to teams within a club for a specific match day, ensuring that the best available players are assigned to the first team, the next best to the second team, and so on

### Modified Functions

The following functions have been modified:

- `simulate_match_day(season)`: Now calls `reset_player_availability()` and `determine_player_availability()` for each club with teams playing on the current match day, and then calls `assign_players_to_teams_for_match_day()` to assign players to teams before simulating matches
- `simulate_match(home_team, away_team, match=None, home_team_players=None, away_team_players=None)`: Now accepts pre-assigned players for the home and away teams, and only falls back to the old method if no pre-assigned players are provided
- `simulate_season(season, create_new_season=True)`: Now simulates match day by match day instead of league by league, ensuring that player availability is correctly determined for each match day, and uses the new player assignment system

## How to Use

### Running the Migration

To add the new column to your database, run the following command:

```bash
python run_migration.py migrations/add_player_availability.py
```

### Testing the Player Availability System

To test the player availability system, run the following command:

```bash
python test_player_availability.py
```

This will:
1. Reset player availability flags
2. Select a random club and determine player availability
3. Show which players are available and which are not
4. Test player assignment to teams based on availability and strength

## Expected Behavior

- Approximately 16.7% of players should be unavailable for each match day
- Each club should have at least 6 available players for each team playing on the match day
- The best available players should be assigned to the first team, the next best to the second team, and so on
- Players should only play for one team per match day

## Troubleshooting

If you encounter any issues with the player availability system, check the following:

1. Make sure the `is_available_current_matchday` column exists in the Player table
2. Make sure the `reset_player_availability()` function is called at the beginning of each match day
3. Make sure the `determine_player_availability()` function is called for each club with teams playing on the current match day
4. Make sure the `simulate_match()` function only considers available players when selecting players for teams
5. When using the "Simulate Season" button, make sure the `simulate_season()` function is simulating match day by match day, not league by league

### Known Issues

- If you use the "Simulate Season" button with an older version of the code, player availability will not be correctly determined for each match day. Make sure you're using the latest version of the code that simulates match day by match day.

### Bug Fixes

- Fixed an issue where the player availability system would incorrectly report the number of available players after making some unavailable players available again.
- Fixed an issue where player availability changes wouldn't be saved to the database when a club has fewer players than the minimum required.

If you still have issues, please contact the development team.
