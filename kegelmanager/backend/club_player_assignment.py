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
    # Convert set to list for proper parameter binding
    club_ids_list = list(clubs_with_matches)

    # Create placeholders for IN clause
    placeholders = ','.join([':param' + str(i) for i in range(len(club_ids_list))])

    # Create parameter dictionary
    params = {f'param{i}': club_id for i, club_id in enumerate(club_ids_list)}
    params['season_id'] = season_id
    params['match_day'] = match_day

    teams_query = text(f"""
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
        WHERE t.club_id IN ({placeholders})
            AND m.season_id = :season_id
            AND m.match_day = :match_day
            AND m.is_played = 0

        UNION

        SELECT DISTINCT
            t.id as team_id,
            t.club_id,
            t.name as team_name,
            l.level as league_level,
            CASE
                WHEN cm.home_team_id = t.id THEN 'home'
                WHEN cm.away_team_id = t.id THEN 'away'
            END as match_type
        FROM team t
        JOIN cup_match cm ON (cm.home_team_id = t.id OR cm.away_team_id = t.id)
        JOIN league l ON t.league_id = l.id
        JOIN cup c ON cm.cup_id = c.id
        WHERE t.club_id IN ({placeholders})
            AND c.season_id = :season_id
            AND cm.cup_match_day = :match_day
            AND cm.is_played = 0
        ORDER BY club_id, league_level, team_id
    """)

    teams_data = db.session.execute(teams_query, params).fetchall()

    # Group teams by club
    club_teams = {}
    for row in teams_data:
        # Access columns by index or name - use _asdict() for named access
        row_dict = row._asdict() if hasattr(row, '_asdict') else dict(row)
        club_id = row_dict['club_id']

        if club_id not in club_teams:
            club_teams[club_id] = []

        team_info = {
            'id': row_dict['team_id'],
            'name': row_dict['team_name'],
            'league_level': row_dict['league_level'],
            'match_type': row_dict['match_type']
        }

        # Avoid duplicates
        if team_info not in club_teams[club_id]:
            club_teams[club_id].append(team_info)

    # Get all available players for all clubs in one query
    # Use the same placeholders as above
    players_query = text(f"""
        SELECT
            id, club_id, strength, konstanz, drucksicherheit, volle, raeumer,
            ausdauer, sicherheit, auswaerts, start, mitte, schluss,
            form_short_term, form_medium_term, form_long_term
        FROM player
        WHERE club_id IN ({placeholders})
            AND is_available_current_matchday = 1
            AND (last_played_matchday IS NULL OR last_played_matchday != :match_day)
        ORDER BY club_id, (strength * 0.5 + konstanz * 0.1 + drucksicherheit * 0.1 + volle * 0.15 + raeumer * 0.15) DESC
    """)

    # Use only the club parameters for the players query, plus match_day
    players_params = {f'param{i}': club_id for i, club_id in enumerate(club_ids_list)}
    players_params['match_day'] = match_day
    players_data = db.session.execute(players_query, players_params).fetchall()

    # Group players by club
    club_players = {}
    for row in players_data:
        # Access columns by index or name - use _asdict() for named access
        row_dict = row._asdict() if hasattr(row, '_asdict') else dict(row)
        club_id = row_dict['club_id']

        if club_id not in club_players:
            club_players[club_id] = []

        # Create player object-like structure for compatibility
        player_data = {
            'id': row_dict['id'],
            'strength': row_dict['strength'],
            'konstanz': row_dict['konstanz'],
            'drucksicherheit': row_dict['drucksicherheit'],
            'volle': row_dict['volle'],
            'raeumer': row_dict['raeumer'],
            'ausdauer': row_dict['ausdauer'],
            'sicherheit': row_dict['sicherheit'],
            'auswaerts': row_dict['auswaerts'],
            'start': row_dict['start'],
            'mitte': row_dict['mitte'],
            'schluss': row_dict['schluss'],
            'form_short_term': row_dict['form_short_term'],
            'form_medium_term': row_dict['form_medium_term'],
            'form_long_term': row_dict['form_long_term']
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
