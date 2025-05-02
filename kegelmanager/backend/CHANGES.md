# Player Assignment Changes

## Overview

This document describes the changes made to the player assignment system in the Kegelmanager application. Previously, players were primarily assigned to teams, but now they are assigned to clubs and the best available players are selected for each team on match day.

## Changes Made

### 1. Player Selection Logic in `simulation.py`

The `simulate_match` function has been modified to:

- Get all teams from the same club as the home and away teams
- Get all players from each club
- Determine which players are unavailable for the match (random selection)
- Check which players are already playing in other matches on the same match day
- Sort available players by a weighted rating based on multiple attributes:
  - Strength (50% weight)
  - Consistency (10% weight)
  - Pressure resistance (10% weight)
  - Full pins performance (15% weight)
  - Clearing pins performance (15% weight)
- Sort teams by league level (higher leagues first)
- Assign the best available players to the first team, next best to the second team, etc.
- Ensure each player only plays in one match per match day
- Identify which players are substitutes (not originally in the team)

### 2. Player Generation in `init_db.py`

No changes were needed to the player generation code in `init_db.py` as it was already:
- Generating players for teams
- Assigning players to clubs via the `club_id` field
- Associating players with teams for backward compatibility

### 3. Testing

The `test_simulation.py` file was updated to test the new player selection logic:
- Shows information about clubs and their teams
- Demonstrates that players are selected from the club based on their attributes
- Verifies that the match simulation works correctly with the new player selection logic

## Benefits

1. **More Realistic Team Selection**: The best players in a club will play for the first team, the next best for the second team, etc.

2. **Comprehensive Player Evaluation**: Players are now evaluated based on multiple attributes, not just strength, providing a more nuanced selection process.

3. **Substitutes from Other Teams**: If a team doesn't have enough players, substitutes can come from other teams in the same club.

4. **One Match Per Player Per Day**: Players can only participate in one match per match day, which is more realistic and prevents the same player from appearing in multiple teams on the same day.

5. **League-Based Team Priority**: Teams in higher leagues get priority when selecting players, ensuring that the best teams get the best players.

## Technical Implementation

The key technical changes include:

1. **Player Rating Algorithm**:

```python
def player_rating(player):
    # Calculate a weighted rating based on key attributes
    return (
        player.strength * 0.5 +  # 50% weight on strength
        player.konstanz * 0.1 +   # 10% weight on consistency
        player.drucksicherheit * 0.1 +  # 10% weight on pressure resistance
        player.volle * 0.15 +     # 15% weight on full pins
        player.raeumer * 0.15     # 15% weight on clearing pins
    )
```

2. **Player Model Extension with Match Day Flags**:

```python
# Flag, ob der Spieler am aktuellen Spieltag bereits gespielt hat
has_played_current_matchday = db.Column(db.Boolean, default=False)
last_played_matchday = db.Column(db.Integer, nullable=True)  # Speichert den letzten Spieltag, an dem der Spieler gespielt hat
```

3. **Preventing Players from Playing Multiple Matches on the Same Day**:

```python
# Filter out players who have already played on this match day
if current_match_day:
    # Reset flags for players who played on a different match day
    for player in home_club_players:
        if player.has_played_current_matchday and player.last_played_matchday != current_match_day:
            player.has_played_current_matchday = False
            db.session.add(player)

# Filter out players who have already played on this match day
home_club_players = [p for p in home_club_players if not p.has_played_current_matchday]
```

4. **Setting Player Flags After a Match**:

```python
# Mark all players as having played on this match day
for player in home_players + away_players:
    player.has_played_current_matchday = True
    player.last_played_matchday = match.match_day
    db.session.add(player)
```

5. **Resetting Player Flags After a Match Day**:

```python
def reset_player_matchday_flags():
    """Reset the has_played_current_matchday flag for all players."""
    players = Player.query.all()
    for player in players:
        if player.has_played_current_matchday:
            player.has_played_current_matchday = False
            db.session.add(player)
    db.session.commit()
```

6. **Assigning Players to Teams by League Level**:

```python
# Make sure teams are sorted by league level (lower level number = higher league)
home_club_teams.sort(key=lambda t: t.league.level if t.league else 999)

# Assign players to home teams (best teams first)
used_home_players = set()  # Track which players have been assigned
for team in home_club_teams:
    needed_players = 6 - len(home_team_players[team.id])
    available_players = [p for p in home_club_players if p.id not in used_home_players]

    # Take the top N available players for this team
    for player in available_players[:needed_players]:
        home_team_players[team.id].append(player)
        used_home_players.add(player.id)
```

These changes ensure that the best players are selected for the first team, and that no player plays in multiple matches on the same match day.
