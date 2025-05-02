# Player Assignment Changes

## Overview

This document describes the changes made to the player assignment system in the Kegelmanager application. Previously, players were primarily assigned to teams, but now they are assigned to clubs and the best available players are selected for each team on match day.

## Latest Update: Player Availability System

A new player availability system has been implemented to simulate real-world scenarios where players might be unavailable for a match day due to shift work or other commitments. The system works as follows:

1. At the beginning of each match day, each player has a 16.7% chance of being unavailable
2. The system ensures that each club has enough players available for all of its teams playing on that match day (minimum 6 players per team)
3. The best available players are assigned to teams based on their attributes, with the best players going to the first team, the next best to the second team, and so on
4. Players can only play for one team per match day

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

7. **Player Availability System**:

```python
# New field in Player model
is_available_current_matchday = db.Column(db.Boolean, default=True)

# Reset player availability at the beginning of a match day
def reset_player_availability():
    """Reset the is_available_current_matchday flag for all players."""
    players = Player.query.all()
    for player in players:
        player.is_available_current_matchday = True
        db.session.add(player)
    db.session.commit()

# Determine player availability for a club
def determine_player_availability(club_id, teams_playing):
    """Determine which players are available for a club on the current match day."""
    # Get all players from this club
    club_players = Player.query.filter_by(club_id=club_id).all()

    # Calculate how many players we need at minimum (6 per team)
    min_players_needed = teams_playing * 6

    # Determine unavailable players (16.7% chance of being unavailable)
    for player in club_players:
        # 16.7% chance of being unavailable
        if random.random() < 0.167:
            player.is_available_current_matchday = False

    # Ensure we have enough available players
    available_players = len([p for p in club_players if p.is_available_current_matchday])
    if available_players < min_players_needed:
        # Make some unavailable players available again
        unavailable_players = [p for p in club_players if not p.is_available_current_matchday]
        players_to_make_available = random.sample(unavailable_players, min_players_needed - available_players)
        for player in players_to_make_available:
            player.is_available_current_matchday = True
```

8. **Only Consider Available Players for Team Selection**:

```python
# Get all available players from the home club
home_club_players = Player.query.filter_by(club_id=home_team.club_id, is_available_current_matchday=True).all()
# Get all available players from the away club
away_club_players = Player.query.filter_by(club_id=away_team.club_id, is_available_current_matchday=True).all()
```

These changes create a more realistic simulation of player availability and team selection for match days.

9. **Updated Season Simulation to Work with Player Availability**:

```python
# Simulate match day by match day instead of league by league
for match_day in range(1, max_match_day + 1):
    # Reset player availability flags for all players
    reset_player_availability()

    # Determine which clubs have matches on this match day
    clubs_with_matches = set()
    teams_playing = {}  # Dictionary to track how many teams each club has playing

    # First, identify all clubs that have teams playing on this match day
    for league in leagues:
        unplayed_matches = Match.query.filter_by(
            league_id=league.id,
            season_id=season.id,
            is_played=False,
            match_day=match_day
        ).all()

        # ... determine clubs and teams playing ...

    # Now determine player availability for each club
    for club_id in clubs_with_matches:
        determine_player_availability(club_id, teams_playing.get(club_id, 0))

    # Now simulate matches for this match day across all leagues
    # ... simulate matches ...

    # Reset player flags after the match day is complete
    reset_player_matchday_flags()
```

This change ensures that when simulating an entire season, the player availability is correctly determined for each match day, and the best available players are assigned to teams based on their attributes.

10. **Centralized Player Assignment to Teams**:

```python
# New file: club_player_assignment.py
def assign_players_to_teams_for_match_day(club_id, match_day, season_id):
    """
    Assign players to teams within a club for a specific match day.
    """
    # Get all teams from this club that have matches on this match day
    teams_with_matches = []

    # Find all matches for this club on this match day
    home_matches = Match.query.filter_by(
        season_id=season_id,
        match_day=match_day,
        is_played=False
    ).join(Team, Match.home_team_id == Team.id).filter(
        Team.club_id == club_id
    ).all()

    away_matches = Match.query.filter_by(
        season_id=season_id,
        match_day=match_day,
        is_played=False
    ).join(Team, Match.away_team_id == Team.id).filter(
        Team.club_id == club_id
    ).all()

    # Collect all teams that have matches
    for match in home_matches:
        teams_with_matches.append(match.home_team)

    for match in away_matches:
        teams_with_matches.append(match.away_team)

    # Sort teams by league level (lower level number = higher league)
    teams_with_matches.sort(key=lambda t: t.league.level if t.league else 999)

    # Get all available players from this club
    available_players = Player.query.filter_by(
        club_id=club_id,
        is_available_current_matchday=True,
        has_played_current_matchday=False
    ).all()

    # Sort players by a weighted rating of their attributes
    def player_rating(player):
        return (
            player.strength * 0.5 +  # 50% weight on strength
            player.konstanz * 0.1 +   # 10% weight on consistency
            player.drucksicherheit * 0.1 +  # 10% weight on pressure resistance
            player.volle * 0.15 +     # 15% weight on full pins
            player.raeumer * 0.15     # 15% weight on clearing pins
        )

    available_players.sort(key=player_rating, reverse=True)

    # Assign players to teams
    team_players = {}
    used_players = set()

    # For each team (starting with the highest league), assign 6 players
    for team in teams_with_matches:
        team_players[team.id] = []

        # Get up to 6 best available players who haven't been assigned yet
        needed_players = 6
        assigned_count = 0

        for player in available_players:
            if player.id not in used_players:
                team_players[team.id].append(player)
                used_players.add(player.id)
                assigned_count += 1

                # Mark player as having played on this match day
                player.has_played_current_matchday = True
                player.last_played_matchday = match_day
                db.session.add(player)

                if assigned_count >= needed_players:
                    break

    return team_players
```

This change centralizes the player assignment to teams, ensuring that players are assigned consistently across all matches on a match day. The best available players are assigned to the first team, the next best to the second team, and so on.
