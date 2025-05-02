"""
Module for assigning players to teams within a club for a match day.
"""

from models import db, Player, Team, Match

def assign_players_to_teams_for_match_day(club_id, match_day, season_id):
    """
    Assign players to teams within a club for a specific match day.

    Args:
        club_id: The ID of the club
        match_day: The match day number
        season_id: The ID of the season

    Returns:
        dict: A dictionary mapping team IDs to lists of player IDs
    """
    # Get all teams from this club that have matches on this match day
    teams_with_matches = []
    team_to_match = {}

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
        team_to_match[match.home_team.id] = match

    for match in away_matches:
        teams_with_matches.append(match.away_team)
        team_to_match[match.away_team.id] = match

    # If no teams have matches, return empty dictionary
    if not teams_with_matches:
        return {}

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

                # We'll mark players as having played in a bulk operation later

                if assigned_count >= needed_players:
                    break


    # Mark all assigned players as having played on this match day using bulk update
    all_assigned_player_ids = []
    for team_id, players in team_players.items():
        all_assigned_player_ids.extend([p.id for p in players])

    if all_assigned_player_ids:
        db.session.execute(
            db.update(Player)
            .where(Player.id.in_(all_assigned_player_ids))
            .values(
                has_played_current_matchday=True,
                last_played_matchday=match_day
            )
        )

    # Commit changes to database
    db.session.commit()

    return team_players
