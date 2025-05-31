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

    # Get all available players from this club with optimized query
    # Load only the attributes we need for sorting to reduce memory usage
    available_players = Player.query.filter_by(
        club_id=club_id,
        is_available_current_matchday=True,
        has_played_current_matchday=False
    ).options(
        db.load_only(Player.id, Player.strength, Player.konstanz, Player.drucksicherheit, Player.volle, Player.raeumer)
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


    # Note: Player flags (has_played_current_matchday, last_played_matchday)
    # are now updated in the simulation functions using batch operations
    # for better performance

    return team_players


def batch_assign_players_to_teams(clubs_with_matches, match_day, season_id, cache_manager):
    """
    Optimized batch assignment of players to teams for multiple clubs.

    Args:
        clubs_with_matches: Set of club IDs that have matches
        match_day: The match day number
        season_id: The ID of the season
        cache_manager: CacheManager instance for caching

    Returns:
        dict: A dictionary mapping club_id -> team_id -> list of players
    """
    from sqlalchemy import text
    import time

    start_time = time.time()

    # Get all teams with matches for all clubs in one query
    if not clubs_with_matches:
        return {}

    # Single query to get all teams and their matches
    teams_query = text("""
        SELECT DISTINCT
            t.id as team_id,
            t.club_id,
            t.name as team_name,
            l.level as league_level,
            CASE
                WHEN m.home_team_id = t.id THEN 'home'
                WHEN m.away_team_id = t.id THEN 'away'
            END as match_type
        FROM team t
        JOIN match m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
        JOIN league l ON t.league_id = l.id
        WHERE t.club_id IN :club_ids
            AND m.season_id = :season_id
            AND m.match_day = :match_day
            AND m.is_played = 0
        ORDER BY t.club_id, l.level, t.id
    """)

    teams_data = db.session.execute(teams_query, {
        "club_ids": tuple(clubs_with_matches),
        "season_id": season_id,
        "match_day": match_day
    }).fetchall()

    # Group teams by club
    club_teams = {}
    for row in teams_data:
        club_id = row.club_id
        if club_id not in club_teams:
            club_teams[club_id] = []

        team_info = {
            'id': row.team_id,
            'name': row.team_name,
            'league_level': row.league_level,
            'match_type': row.match_type
        }

        # Avoid duplicates
        if team_info not in club_teams[club_id]:
            club_teams[club_id].append(team_info)

    # Get all available players for all clubs in one query
    players_query = text("""
        SELECT
            id, club_id, strength, konstanz, drucksicherheit, volle, raeumer
        FROM player
        WHERE club_id IN :club_ids
            AND is_available_current_matchday = 1
            AND has_played_current_matchday = 0
        ORDER BY club_id, (strength * 0.5 + konstanz * 0.1 + drucksicherheit * 0.1 + volle * 0.15 + raeumer * 0.15) DESC
    """)

    players_data = db.session.execute(players_query, {
        "club_ids": tuple(clubs_with_matches)
    }).fetchall()

    # Group players by club
    club_players = {}
    for row in players_data:
        club_id = row.club_id
        if club_id not in club_players:
            club_players[club_id] = []

        # Create player object-like structure for compatibility
        player_data = {
            'id': row.id,
            'strength': row.strength,
            'konstanz': row.konstanz,
            'drucksicherheit': row.drucksicherheit,
            'volle': row.volle,
            'raeumer': row.raeumer
        }
        club_players[club_id].append(player_data)

    # Assign players to teams for each club
    result = {}

    for club_id in clubs_with_matches:
        result[club_id] = {}

        teams = club_teams.get(club_id, [])
        available_players = club_players.get(club_id, [])

        if not teams or not available_players:
            continue

        # Sort teams by league level (lower level = higher priority)
        teams.sort(key=lambda t: t['league_level'])

        used_players = set()

        # Assign 6 players to each team
        for team in teams:
            team_id = team['id']
            result[club_id][team_id] = []

            assigned_count = 0
            for player_data in available_players:
                if player_data['id'] not in used_players and assigned_count < 6:
                    result[club_id][team_id].append(player_data)
                    used_players.add(player_data['id'])
                    assigned_count += 1

                if assigned_count >= 6:
                    break

    end_time = time.time()
    print(f"Batch assigned players for {len(clubs_with_matches)} clubs in {end_time - start_time:.3f}s")

    return result
