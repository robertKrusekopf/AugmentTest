"""
Module for assigning players to teams within a club for a match day.

IMPORTANT: Player assignment respects age class (Altersklasse) restrictions.
Players can only be assigned to teams whose league age class is equal to or older
than the player's age class.
"""

from models import db, Player, Team, Match, CupMatch, Cup, UserLineup, LineupPosition, get_cup_match_frontend_id
from sqlalchemy import or_
from age_class_utils import (
    get_minimum_altersklasse_for_age,
    get_age_class_rank,
    is_player_allowed_in_team
)

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

    # Also find cup matches for this club on this match day
    home_cup_matches = CupMatch.query.filter_by(
        cup_match_day=match_day,
        is_played=False
    ).join(Team, CupMatch.home_team_id == Team.id).filter(
        Team.club_id == club_id
    ).join(Cup).filter(Cup.season_id == season_id).all()

    away_cup_matches = CupMatch.query.filter_by(
        cup_match_day=match_day,
        is_played=False
    ).join(Team, CupMatch.away_team_id == Team.id).filter(
        Team.club_id == club_id
    ).join(Cup).filter(Cup.season_id == season_id).all()

    # Collect all teams that have matches (both league and cup)
    for match in home_matches:
        teams_with_matches.append(match.home_team)
        team_to_match[match.home_team.id] = match

    for match in away_matches:
        teams_with_matches.append(match.away_team)
        team_to_match[match.away_team.id] = match

    for cup_match in home_cup_matches:
        if cup_match.home_team not in teams_with_matches:
            teams_with_matches.append(cup_match.home_team)
            team_to_match[cup_match.home_team.id] = cup_match

    for cup_match in away_cup_matches:
        if cup_match.away_team not in teams_with_matches:
            teams_with_matches.append(cup_match.away_team)
            team_to_match[cup_match.away_team.id] = cup_match

    # If no teams have matches, return empty dictionary
    if not teams_with_matches:
        return {}

    # Sort teams by age class rank (oldest first), then by league level (higher league first)
    def team_sort_key(t):
        if t.league and t.league.altersklasse:
            age_rank = get_age_class_rank(t.league.altersklasse)
        else:
            age_rank = 6  # Herren rank for teams without age class
        league_level = t.league.level if t.league else 999
        # Sort by age_rank descending (oldest first), then by league_level ascending (best league first)
        return (-age_rank, league_level)

    teams_with_matches.sort(key=team_sort_key)

    # Get all available players from this club with optimized query
    # IMPORTANT: We need the 'age' field for age class validation
    available_players = Player.query.filter_by(
        club_id=club_id,
        is_available_current_matchday=True,
        has_played_current_matchday=False,
        is_retired=False
    ).all()

    # Group players by their minimum age class
    from collections import defaultdict
    from simulation import calculate_player_rating

    players_by_min_class = defaultdict(list)
    for player in available_players:
        if not player.age:
            min_class = 'Herren'
        else:
            min_class = get_minimum_altersklasse_for_age(player.age)
        players_by_min_class[min_class].append(player)

    # Sort players within each age class by rating (best first)
    for age_class in players_by_min_class:
        players_by_min_class[age_class].sort(key=calculate_player_rating, reverse=True)

    # Assign players to teams with age class validation
    team_players = {}
    used_players = set()

    # For each team (starting with youngest age class, highest league), assign 6 players
    for team in teams_with_matches:
        team_age_class = team.league.altersklasse if team.league and team.league.altersklasse else 'Herren'
        team_age_rank = get_age_class_rank(team_age_class)

        # Find all players eligible for this team (age class equal or younger)
        eligible_players = []
        for age_class, player_list in players_by_min_class.items():
            player_age_rank = get_age_class_rank(age_class)
            # Player can play in this team if their age class rank <= team age class rank
            if player_age_rank <= team_age_rank:
                eligible_players.extend(player_list)

        # Sort eligible players by rating
        eligible_players.sort(key=calculate_player_rating, reverse=True)

        # Select the best 6 eligible available players
        selected_players = []
        assigned_count = 0

        for player in eligible_players:
            if player.id not in used_players and assigned_count < 6:
                selected_players.append(player)
                used_players.add(player.id)
                assigned_count += 1

                if assigned_count >= 6:
                    break

        # Now randomize the positions of these 6 selected players
        if selected_players:
            from auto_lineup import randomize_player_positions
            random_positions = randomize_player_positions(selected_players)

            # Convert to list in random order
            randomized_players = []
            for i in range(1, 7):
                if random_positions[i] is not None:
                    randomized_players.append(random_positions[i])

            team_players[team.id] = randomized_players
        else:
            team_players[team.id] = []


    # Note: Player flags (has_played_current_matchday, last_played_matchday)
    # are now updated in the simulation functions using batch operations
    # for better performance

    return team_players


def get_manual_lineup_for_team(match_id, team_id, is_home_team):
    """
    Retrieve manual lineup for a specific team in a match.

    Args:
        match_id: The ID of the match
        team_id: The ID of the team
        is_home_team: Whether the team is the home team

    Returns:
        list: List of player dictionaries in position order (1-6), or None if no manual lineup exists
    """
    # Check if there's a manual lineup for this team
    lineup = UserLineup.query.filter_by(
        match_id=match_id,
        team_id=team_id,
        is_home_team=is_home_team
    ).first()

    if not lineup:
        return None

    # Get the positions and players
    positions = LineupPosition.query.filter_by(lineup_id=lineup.id).all()

    if not positions:
        return None

    # Create a list of 6 positions, initially filled with None
    positioned_players = [None] * 6

    # Fill in the players at their assigned positions
    for position in positions:
        if 1 <= position.position_number <= 6:
            player = Player.query.get(position.player_id)
            if player:
                # Create player data dictionary compatible with simulation
                player_data = {
                    'id': player.id,
                    'name': player.name,
                    'strength': player.strength,
                    'konstanz': player.konstanz,
                    'drucksicherheit': player.drucksicherheit,
                    'volle': player.volle,
                    'raeumer': player.raeumer,
                    'ausdauer': player.ausdauer,
                    'sicherheit': player.sicherheit,
                    'auswaerts': player.auswaerts,
                    'start': player.start,
                    'mitte': player.mitte,
                    'schluss': player.schluss,
                    'form_short_term': player.form_short_term,
                    'form_medium_term': player.form_medium_term,
                    'form_long_term': player.form_long_term,
                    'form_short_remaining_days': player.form_short_remaining_days,
                    'form_medium_remaining_days': player.form_medium_remaining_days,
                    'form_long_remaining_days': player.form_long_remaining_days
                }
                positioned_players[position.position_number - 1] = player_data

    # Filter out None values to return only real players
    manual_players = [player for player in positioned_players if player is not None]

    return manual_players


def batch_assign_players_to_teams(clubs_with_matches, match_day, season_id, cache_manager, include_played_matches=False, target_date=None):
    """
    Optimized batch assignment of players to teams for multiple clubs.

    Args:
        clubs_with_matches: Set of club IDs that have matches
        match_day: The match day number
        season_id: The ID of the season
        cache_manager: CacheManager instance for caching
        include_played_matches: Whether to include already played matches (default: False)
        target_date: Optional target date for cup matches (if provided, uses date-based filtering for cups)

    Returns:
        dict: A dictionary mapping club_id -> team_id -> list of players
    """
    from sqlalchemy import text, func
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

    # Build the cup match filter based on whether we have a target_date
    if target_date:
        # Use date-based filtering for cup matches
        cup_filter = "AND DATE(cm.match_date) = :target_date"
        params['target_date'] = target_date
        print(f"DEBUG: Using date-based cup filtering for {target_date}")

        # Debug: Check how many cup matches exist for this date
        debug_cup_query = text(f"""
            SELECT COUNT(*) as count
            FROM cup_match cm
            JOIN cup c ON cm.cup_id = c.id
            WHERE c.season_id = :season_id
                AND DATE(cm.match_date) = :target_date
                {'' if include_played_matches else 'AND cm.is_played = 0'}
        """)
        debug_result = db.session.execute(debug_cup_query, {'season_id': season_id, 'target_date': target_date}).fetchone()
        print(f"DEBUG: Found {debug_result[0]} cup matches for date {target_date}")

        # Debug: Also check cup_match_day filtering
        debug_cup_day_query = text(f"""
            SELECT COUNT(*) as count
            FROM cup_match cm
            JOIN cup c ON cm.cup_id = c.id
            WHERE c.season_id = :season_id
                AND cm.cup_match_day = :match_day
                {'' if include_played_matches else 'AND cm.is_played = 0'}
        """)
        debug_day_result = db.session.execute(debug_cup_day_query, {'season_id': season_id, 'match_day': match_day}).fetchone()
        print(f"DEBUG: Found {debug_day_result[0]} cup matches for cup_match_day {match_day}")
    else:
        # Use cup_match_day filtering for cup matches
        cup_filter = "AND cm.cup_match_day = :match_day"
        print(f"DEBUG: Using cup_match_day filtering for match day {match_day}")

    teams_query = text(f"""
        SELECT DISTINCT
            t.id as team_id,
            t.club_id,
            t.name as team_name,
            l.level as league_level,
            l.altersklasse as altersklasse,
            m.id as match_id,
            'league' as match_source,
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
            {'' if include_played_matches else 'AND m.is_played = 0'}

        UNION

        SELECT DISTINCT
            t.id as team_id,
            t.club_id,
            t.name as team_name,
            l.level as league_level,
            l.altersklasse as altersklasse,
            cm.id as match_id,
            'cup' as match_source,
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
            {cup_filter}
            {'' if include_played_matches else 'AND cm.is_played = 0'}
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

        # Convert cup match IDs to frontend IDs for consistency with UserLineup storage
        match_id = row_dict['match_id']
        if row_dict['match_source'] == 'cup':
            match_id = get_cup_match_frontend_id(match_id)

        team_info = {
            'id': row_dict['team_id'],
            'name': row_dict['team_name'],
            'league_level': row_dict['league_level'],
            'altersklasse': row_dict.get('altersklasse'),  # Include age class for validation
            'match_id': match_id,
            'match_type': row_dict['match_type']
        }

        # Avoid duplicates
        if team_info not in club_teams[club_id]:
            club_teams[club_id].append(team_info)

    # Get all available players for all clubs in one query
    # Use the same placeholders as above
    from simulation import PLAYER_RATING_SQL

    # For cup matches, we need to be more lenient with player availability
    # since cup and league matches use the same match_day numbers but are on different dates
    is_cup_day = target_date is not None

    if is_cup_day:
        # For cup matches, only check availability, not if they've played
        # since has_played_current_matchday refers to league matches
        player_filter = "AND is_available_current_matchday = 1"
        print(f"DEBUG: Cup day detected - ignoring has_played_current_matchday flag")
    else:
        # For league matches, use the normal filtering
        player_filter = f"AND is_available_current_matchday = 1 {'' if include_played_matches else 'AND has_played_current_matchday = 0'}"
        print(f"DEBUG: League day detected - using normal player filtering")

    # IMPORTANT: Include 'age' field for age class validation
    players_query = text(f"""
        SELECT
            id, name, club_id, age, strength, konstanz, drucksicherheit, volle, raeumer,
            ausdauer, sicherheit, auswaerts, start, mitte, schluss,
            form_short_term, form_medium_term, form_long_term,
            form_short_remaining_days, form_medium_remaining_days, form_long_remaining_days
        FROM player
        WHERE club_id IN ({placeholders})
            AND is_retired = 0
            {player_filter}
        ORDER BY club_id, {PLAYER_RATING_SQL} DESC
    """)

    # Use only the club parameters for the players query
    players_params = {f'param{i}': club_id for i, club_id in enumerate(club_ids_list)}
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
        # IMPORTANT: Include 'age' for age class validation
        player_data = {
            'id': row_dict['id'],
            'name': row_dict['name'],
            'age': row_dict['age'],
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
            'form_long_term': row_dict['form_long_term'],
            'form_short_remaining_days': row_dict['form_short_remaining_days'],
            'form_medium_remaining_days': row_dict['form_medium_remaining_days'],
            'form_long_remaining_days': row_dict['form_long_remaining_days']
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

        # Sort teams by age class rank (oldest first), then by league level (higher league first)
        def team_sort_key_batch(t):
            if t.get('altersklasse'):
                age_rank = get_age_class_rank(t['altersklasse'])
            else:
                age_rank = 6  # Herren rank for teams without age class
            league_level = t.get('league_level', 999)
            # Sort by age_rank descending (oldest first), then by league_level ascending (best league first)
            return (-age_rank, league_level)

        teams.sort(key=team_sort_key_batch)

        # Group players by their minimum age class for this club
        from collections import defaultdict
        players_by_min_class = defaultdict(list)

        for player_data in available_players:
            player_age = player_data.get('age')
            if not player_age:
                min_class = 'Herren'
            else:
                min_class = get_minimum_altersklasse_for_age(player_age)
            players_by_min_class[min_class].append(player_data)

        used_players = set()

        # First pass: collect all teams and check for manual lineups
        team_manual_lineups = {}  # team_id -> manual_lineup
        teams_to_process = []

        for team in teams:
            team_id = team['id']
            match_id = team['match_id']
            match_type = team['match_type']
            is_home_team = (match_type == 'home')

            # Check if there's a manual lineup for this team/match combination
            manual_lineup = get_manual_lineup_for_team(match_id, team_id, is_home_team)

            if manual_lineup:
                # If this team doesn't have a manual lineup yet, use this lineup
                if team_id not in team_manual_lineups:
                    team_manual_lineups[team_id] = manual_lineup

            teams_to_process.append(team)

        # Second pass: assign players to teams
        for team in teams_to_process:
            team_id = team['id']
            match_id = team['match_id']
            match_type = team['match_type']

            # Skip if we've already processed this team
            if team_id in result[club_id]:
                continue

            result[club_id][team_id] = []

            # Check if this team has a manual lineup
            if team_id in team_manual_lineups:
                manual_lineup = team_manual_lineups[team_id]
                result[club_id][team_id] = manual_lineup

                # Mark these players as used so they can't be assigned to other teams
                for player_data in manual_lineup:
                    used_players.add(player_data['id'])

                continue

            # No manual lineup found, use automatic assignment with age class validation
            team_age_class = team.get('altersklasse', 'Herren')
            team_age_rank = get_age_class_rank(team_age_class)

            # Find all players eligible for this team (age class equal or younger)
            eligible_players = []
            for age_class, player_list in players_by_min_class.items():
                player_age_rank = get_age_class_rank(age_class)
                # Player can play in this team if their age class rank <= team age class rank
                if player_age_rank <= team_age_rank:
                    eligible_players.extend(player_list)

            # Select the best 6 eligible available players
            assigned_count = 0
            selected_players = []
            for player_data in eligible_players:
                if player_data['id'] not in used_players and assigned_count < 6:
                    selected_players.append(player_data)
                    used_players.add(player_data['id'])
                    assigned_count += 1

                if assigned_count >= 6:
                    break

            # Now randomize the positions of these 6 selected players
            if selected_players:
                # Convert to objects for position randomization
                player_objects = []
                for player_data in selected_players:
                    player_obj = type('Player', (), player_data)()
                    player_objects.append(player_obj)

                # Apply position randomization
                from auto_lineup import randomize_player_positions
                random_positions = randomize_player_positions(player_objects)

                # Convert back to list in random order
                randomized_players = []
                for i in range(1, 7):
                    if random_positions[i] is not None:
                        # Convert back to dictionary format
                        player_obj = random_positions[i]
                        player_data = {
                            'id': player_obj.id,
                            'name': player_obj.name,
                            'strength': player_obj.strength,
                            'konstanz': player_obj.konstanz,
                            'drucksicherheit': player_obj.drucksicherheit,
                            'volle': player_obj.volle,
                            'raeumer': player_obj.raeumer,
                            'ausdauer': player_obj.ausdauer,
                            'sicherheit': player_obj.sicherheit,
                            'auswaerts': player_obj.auswaerts,
                            'start': player_obj.start,
                            'mitte': player_obj.mitte,
                            'schluss': player_obj.schluss,
                            'form_short_term': player_obj.form_short_term,
                            'form_medium_term': player_obj.form_medium_term,
                            'form_long_term': player_obj.form_long_term,
                            'form_short_remaining_days': player_obj.form_short_remaining_days,
                            'form_medium_remaining_days': player_obj.form_medium_remaining_days,
                            'form_long_remaining_days': player_obj.form_long_remaining_days
                        }
                        randomized_players.append(player_data)

                result[club_id][team_id] = randomized_players

    end_time = time.time()
    print(f"Batch assigned players for {len(clubs_with_matches)} clubs in {end_time - start_time:.3f}s")

    return result
