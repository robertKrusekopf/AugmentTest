import numpy as np
from datetime import datetime, timedelta, timezone
from models import db, Match, Player, Team, League, Season
from form_system import apply_form_to_strength, get_player_total_form_modifier

# Central player rating formula for SQL queries
PLAYER_RATING_SQL = "(strength * 0.5 + konstanz * 0.1 + drucksicherheit * 0.1 + volle * 0.15 + raeumer * 0.15)"


class SimplePlayer:
    """Simple player object created from dictionary data for simulation compatibility."""
    def __init__(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                setattr(self, key, value)
        else:
            # If data is not a dictionary, it might already be a player object
            # Copy all attributes from the source object
            if hasattr(data, '__dict__'):
                for key, value in data.__dict__.items():
                    setattr(self, key, value)
            else:
                # Fallback: create a minimal player object
                self.id = getattr(data, 'id', 'unknown')
                self.name = getattr(data, 'name', 'Unknown Player')
                self.strength = getattr(data, 'strength', 50)
                # Set default values for all expected attributes
                self.konstanz = getattr(data, 'konstanz', 50)
                self.drucksicherheit = getattr(data, 'drucksicherheit', 50)
                self.volle = getattr(data, 'volle', 50)
                self.raeumer = getattr(data, 'raeumer', 50)
                self.ausdauer = getattr(data, 'ausdauer', 50)
                self.sicherheit = getattr(data, 'sicherheit', 50)
                self.auswaerts = getattr(data, 'auswaerts', 50)
                self.start = getattr(data, 'start', 50)
                self.mitte = getattr(data, 'mitte', 50)
                self.schluss = getattr(data, 'schluss', 50)
                self.form_short_term = getattr(data, 'form_short_term', 0.0)
                self.form_medium_term = getattr(data, 'form_medium_term', 0.0)
                self.form_long_term = getattr(data, 'form_long_term', 0.0)
                self.form_short_remaining_days = getattr(data, 'form_short_remaining_days', 0)
                self.form_medium_remaining_days = getattr(data, 'form_medium_remaining_days', 0)
                self.form_long_remaining_days = getattr(data, 'form_long_remaining_days', 0)

def calculate_realistic_fehler(total_score, sicherheit_attribute):
    """
    Calculate realistic error count (Fehlwürfe) based on total score and safety attribute.

    Args:
        total_score: Player's total score across all 4 lanes
        sicherheit_attribute: Player's safety/security attribute (0-99)

    Returns:
        int: Number of errors (Fehlwürfe)

    Logic:
        - Continuous formula based on score: high scores = fewer errors
        - Sicherheit attribute provides smooth adjustment
        - No hard intervals, smooth transitions
    """
    # Continuous formula for base error calculation
    # Uses exponential decay: high scores have exponentially fewer errors
    # Formula: base_fehler = 15 * exp(-0.004 * (score - 300))
    # This gives approximately:
    # - 300 points: ~15 errors
    # - 400 points: ~10 errors
    # - 500 points: ~5.4 errors
    # - 600 points: ~1.8 errors
    # - 700 points: ~0.6 errors

    # Ensure score is at least 300 to avoid negative exponents getting too large
    adjusted_score = max(300, total_score)

    # Base error mean using exponential decay
    base_fehler_mean = 15.0 * np.exp(-0.004 * (adjusted_score - 300))

    # Standard deviation scales with the mean (higher errors = more variation)
    # But with a minimum to ensure some variation even for very good players
    base_fehler_std = max(0.3, base_fehler_mean * 0.4)

    # Smooth sicherheit adjustment using continuous function
    # Sicherheit 0-99 maps to factor 0.5-1.5 smoothly
    # Formula: factor = 1.5 - (sicherheit / 99)
    # This gives:
    # - Sicherheit 0: factor = 1.5 (+50% errors)
    # - Sicherheit 50: factor = ~1.0 (no change)
    # - Sicherheit 99: factor = 0.5 (-50% errors)
    sicherheit_factor = 1.5 - (sicherheit_attribute / 99.0)

    # Apply sicherheit factor smoothly
    adjusted_fehler_mean = base_fehler_mean * sicherheit_factor
    adjusted_fehler_std = base_fehler_std * sicherheit_factor

    # Generate fehler from normal distribution
    fehler = int(max(0, np.random.normal(adjusted_fehler_mean, adjusted_fehler_std)))

    return fehler

def calculate_team_strength(team):
    """Calculate the overall strength of a team based on its players."""
    if not team.players:
        return 50  # Default value if no players

    total_strength = sum(player.strength for player in team.players)
    return total_strength / len(team.players)

def create_stroh_player(weakest_player_strength):
    """Create a virtual 'Stroh' player with strength 10% lower than the weakest real player.

    Args:
        weakest_player_strength: The strength of the weakest real player in the team

    Returns:
        dict: A dictionary representing the Stroh player with all necessary attributes
    """
    stroh_strength = max(1, int(weakest_player_strength * 0.9))  # 10% weaker, minimum strength of 1

    # Create a virtual player object as a dictionary
    # All attributes are 10% weaker than the base strength
    stroh_player = {
        'id': 'stroh',  # Special ID to identify this as a Stroh player
        'name': 'Stroh',
        'strength': stroh_strength,
        'konstanz': max(1, int(stroh_strength * 0.95)),  # 5% lower consistency
        'drucksicherheit': max(1, int(stroh_strength * 0.95)),  # 5% lower pressure resistance
        'volle': max(1, int(stroh_strength * 0.97)),  # 3% lower full pins
        'raeumer': max(1, int(stroh_strength * 0.97)),  # 3% lower clearing pins
        'sicherheit': max(1, int(stroh_strength * 0.95)),  # 5% lower safety
        'auswaerts': max(1, int(stroh_strength * 0.95)),  # 5% lower away performance
        'start': max(1, int(stroh_strength * 0.97)),  # 3% lower start performance
        'mitte': max(1, int(stroh_strength * 0.97)),  # 3% lower middle performance
        'schluss': max(1, int(stroh_strength * 0.97)),  # 3% lower end performance
        'ausdauer': max(1, int(stroh_strength * 0.95)),  # 5% lower stamina
        'form_short_term': 0,  # Neutral form
        'form_medium_term': 0,  # Neutral form
        'form_long_term': 0,  # Neutral form
        'form_short_remaining_days': 0,  # No active form
        'form_medium_remaining_days': 0,  # No active form
        'form_long_remaining_days': 0,  # No active form
        'is_stroh': True  # Flag to identify this as a Stroh player
    }

    return stroh_player


def fill_with_stroh_players(players, team_name):
    """Fill a team with Stroh players if there are fewer than 6 players.

    Args:
        players: List of players (can be Player objects or dicts)
        team_name: Name of the team for logging purposes

    Returns:
        List of exactly 6 players (mix of real players and Stroh players)
    """
    if len(players) >= 6:
        return players[:6]  # Take only the first 6 players

    if len(players) == 0:
        # If no players at all, create 6 Stroh players with default strength
        print(f"No players available for {team_name}, using 6 Stroh players")
        return [create_stroh_player(30) for _ in range(6)]

    # Find the weakest real player to base Stroh strength on
    real_players = [p for p in players if not (isinstance(p, dict) and p.get('is_stroh', False))]
    if real_players:
        # Get strength values, handling None values
        strength_values = []
        for p in real_players:
            if hasattr(p, 'strength'):
                strength = p.strength if p.strength is not None else 30
            else:
                strength = p.get('strength', 30)
            strength_values.append(strength)
        weakest_strength = min(strength_values)
    else:
        weakest_strength = 30  # Default if no real players

    # Add Stroh players to fill the team
    filled_players = players[:]
    stroh_needed = 6 - len(players)
    print(f"Adding {stroh_needed} Stroh player(s) to {team_name} (weakest real player: {weakest_strength})")

    for _ in range(stroh_needed):
        filled_players.append(create_stroh_player(weakest_strength))

    return filled_players


def calculate_player_rating(player, include_youth_bonus=False):
    """Calculate a weighted rating for a player based on their attributes.

    This is the standard formula used throughout the application for player ranking.

    Args:
        player: Player object or dict with attributes
        include_youth_bonus: Whether to include youth bonus for players under 25

    Returns:
        float: Weighted rating of the player (never None or NaN)
    """
    try:
        # Get attributes (works for both Player objects and dicts)
        strength = get_player_attribute(player, 'strength')
        konstanz = get_player_attribute(player, 'konstanz')
        drucksicherheit = get_player_attribute(player, 'drucksicherheit')
        volle = get_player_attribute(player, 'volle')
        raeumer = get_player_attribute(player, 'raeumer')

        # Standard rating formula
        base_rating = (
            strength * 0.5 +           # 50% weight on strength
            konstanz * 0.1 +           # 10% weight on consistency
            drucksicherheit * 0.1 +    # 10% weight on pressure resistance
            volle * 0.15 +             # 15% weight on full pins
            raeumer * 0.15             # 15% weight on clearing pins
        )

        # Optional youth bonus for redistribution
        if include_youth_bonus and hasattr(player, 'age') and player.age and player.age < 25:
            youth_bonus = 25 - player.age
            base_rating += youth_bonus

        # Ensure we never return None or NaN
        if base_rating is None or np.isnan(base_rating):
            return 50.0  # Default rating

        return float(base_rating)

    except Exception as e:
        print(f"Error calculating player rating for player {getattr(player, 'name', 'unknown')}: {e}")
        return 50.0  # Default rating on error


def calculate_position_score(player, position):
    """Calculate player score for a specific position including position bonus.

    Args:
        player: Player object or dict with attributes
        position: Position number (1-6, where 1-2=Start, 3-4=Mitte, 5-6=Schluss)

    Returns:
        float: Player score including position-specific bonus
    """
    # Use standard rating as base
    base_score = calculate_player_rating(player)

    # Add position-specific bonus based on Start/Mitte/Schluss attributes
    if position in [1, 2]:  # Start positions
        position_bonus = get_player_attribute(player, 'start') * 0.3
    elif position in [3, 4]:  # Mitte positions
        position_bonus = get_player_attribute(player, 'mitte') * 0.3
    else:  # Schluss positions (5, 6)
        position_bonus = get_player_attribute(player, 'schluss') * 0.3

    return base_score + position_bonus


def get_player_attribute(player, attribute_name):
    """Get an attribute from a player object or dictionary (for Stroh players).

    Args:
        player: Either a Player model object or a dictionary (for Stroh players)
        attribute_name: The name of the attribute to retrieve

    Returns:
        The attribute value (never None, defaults to 0)
    """
    if isinstance(player, dict):
        return player.get(attribute_name, 0)
    else:
        value = getattr(player, attribute_name, 0)
        # Handle NULL values from database
        return value if value is not None else 0






def simulate_match_day(season):
    """
    Optimized simulation of one match day for all leagues in a season.

    This function uses performance optimizations including:
    - Bulk database operations
    - Reduced query count
    - Optimized player assignment
    - Better transaction management
    """
    from performance_optimizations import (
        create_performance_indexes,
        optimized_match_queries,
        bulk_reset_player_flags,
        CacheManager
    )
    import time

    start_time = time.time()

    # Update player form modifiers at the beginning of each match day
    from form_system import update_all_players_form
    updated_players = update_all_players_form()

    # Create performance indexes if they don't exist
    create_performance_indexes()

    # Check if leagues have fixtures, generate if missing
    leagues = season.leagues

    for league in leagues:
        teams_in_league = Team.query.filter_by(league_id=league.id).all()
        matches_in_league = Match.query.filter_by(league_id=league.id, season_id=season.id).count()

        if len(teams_in_league) >= 2 and matches_in_league == 0:
            generate_fixtures(league, season)

    # Step 1: Find the next match date to simulate using date-based logic
    from season_calendar import get_next_match_date, mark_calendar_day_simulated

    next_calendar_day = get_next_match_date(season.id)

    if not next_calendar_day:
        return {
            'season': season.name,
            'matches_simulated': 0,
            'results': [],
            'message': 'Keine ungespielte Spiele gefunden. Die Saison ist abgeschlossen.'
        }

    # Step 2: Reset player flags efficiently
    # Pass the current match day and day type to handle Liga vs Pokal correctly
    bulk_reset_player_flags(
        current_match_day=next_calendar_day.match_day_number,
        day_type=next_calendar_day.day_type
    )

    # Step 3: Get matches for this calendar day using date-based logic
    matches_data = []
    cup_matches_data = []

    # Get matches by date - but only for the correct day type
    match_date = next_calendar_day.calendar_date
    day_type = next_calendar_day.day_type

    # Get matches based on the day type to prevent conflicts
    matches_data = []
    cup_matches_data = []

    if day_type == 'LEAGUE_DAY':
        # Only get league matches on league days
        matches_data = get_league_matches_for_date(season.id, match_date)
    elif day_type == 'CUP_DAY':
        # Only get cup matches on cup days
        cup_matches_data = get_cup_matches_for_date(season.id, match_date)
    else:
        # FREE_DAY - no matches should be scheduled
        pass

    if not matches_data and not cup_matches_data:
        return {
            'season': season.name,
            'matches_simulated': 0,
            'results': [],
            'message': f'Keine Spiele für {day_type} am Datum {match_date} gefunden.'
        }

    # Step 4: Determine clubs and teams playing (from both league and cup matches)
    clubs_with_matches = set()
    teams_playing = {}
    playing_teams_info = {}  # New: track which specific teams are playing

    # Process league matches
    if matches_data:
        for match_data in matches_data:
            home_club_id = match_data.home_club_id
            away_club_id = match_data.away_club_id
            home_team_id = match_data.home_team_id
            away_team_id = match_data.away_team_id

            clubs_with_matches.add(home_club_id)
            clubs_with_matches.add(away_club_id)

            teams_playing[home_club_id] = teams_playing.get(home_club_id, 0) + 1
            teams_playing[away_club_id] = teams_playing.get(away_club_id, 0) + 1

            # Collect team info for realistic availability
            if home_club_id not in playing_teams_info:
                playing_teams_info[home_club_id] = []
            if away_club_id not in playing_teams_info:
                playing_teams_info[away_club_id] = []

            # Get team details for home team
            home_team = Team.query.get(home_team_id)
            if home_team and home_team.id not in [t['id'] for t in playing_teams_info[home_club_id]]:
                playing_teams_info[home_club_id].append({
                    'id': home_team.id,
                    'name': home_team.name,
                    'league_level': home_team.league.level if home_team.league else 999
                })

            # Get team details for away team
            away_team = Team.query.get(away_team_id)
            if away_team and away_team.id not in [t['id'] for t in playing_teams_info[away_club_id]]:
                playing_teams_info[away_club_id].append({
                    'id': away_team.id,
                    'name': away_team.name,
                    'league_level': away_team.league.level if away_team.league else 999
                })

    # Process cup matches
    if cup_matches_data:
        for cup_match_data in cup_matches_data:
            home_club_id = cup_match_data['home_club_id']
            away_club_id = cup_match_data['away_club_id']
            home_team_id = cup_match_data['home_team_id']
            away_team_id = cup_match_data['away_team_id']

            clubs_with_matches.add(home_club_id)
            clubs_with_matches.add(away_club_id)

            teams_playing[home_club_id] = teams_playing.get(home_club_id, 0) + 1
            teams_playing[away_club_id] = teams_playing.get(away_club_id, 0) + 1

            # Collect team info for cup matches too
            if home_club_id not in playing_teams_info:
                playing_teams_info[home_club_id] = []
            if away_club_id not in playing_teams_info:
                playing_teams_info[away_club_id] = []

            # Get team details for cup matches
            home_team = Team.query.get(home_team_id)
            if home_team and home_team.id not in [t['id'] for t in playing_teams_info[home_club_id]]:
                playing_teams_info[home_club_id].append({
                    'id': home_team.id,
                    'name': home_team.name,
                    'league_level': home_team.league.level if home_team.league else 999
                })

            away_team = Team.query.get(away_team_id)
            if away_team and away_team.id not in [t['id'] for t in playing_teams_info[away_club_id]]:
                playing_teams_info[away_club_id].append({
                    'id': away_team.id,
                    'name': away_team.name,
                    'league_level': away_team.league.level if away_team.league else 999
                })

    # Step 5: Batch set player availability for all clubs
    try:
        availability_start = time.time()
        from performance_optimizations import batch_set_player_availability
        batch_set_player_availability(clubs_with_matches, teams_playing, playing_teams_info)

    except Exception as e:
        db.session.rollback()
        print(f"Error setting player availability: {str(e)}")
        raise

    # Step 6: Batch assign players to teams for all clubs
    assignment_start = time.time()
    from club_player_assignment import batch_assign_players_to_teams
    cache = CacheManager()

    # Convert match_date to date if it's a datetime
    target_date = match_date.date() if hasattr(match_date, 'date') else match_date

    club_team_players = batch_assign_players_to_teams(
        clubs_with_matches,
        next_calendar_day.match_day_number,
        season.id,
        cache,
        target_date=target_date
    )

    # Step 6.5: Immediately update player flags to prevent multiple assignments
    immediate_player_updates = []
    for club_id, teams in club_team_players.items():
        for team_id, players in teams.items():
            for player in players:
                # Skip Stroh players - they don't get saved to database
                if isinstance(player, dict) and player.get('is_stroh', False):
                    continue
                player_id = player['id'] if isinstance(player, dict) else player.id
                immediate_player_updates.append((player_id, True, next_calendar_day.match_day_number))

    if immediate_player_updates:
        batch_update_player_flags(immediate_player_updates)

    # Step 7: Simulate all matches in parallel (league and cup matches)
    simulation_start = time.time()

    # Combine league and cup matches for simulation
    all_matches_data = []
    if matches_data:
        all_matches_data.extend(matches_data)
    if cup_matches_data:
        all_matches_data.extend(cup_matches_data)

    results, all_performances, all_player_updates, all_lane_records = simulate_matches_parallel(
        all_matches_data,
        club_team_players,
        next_calendar_day.match_day_number,
        cache
    )

    # Step 8: Batch commit all database changes
    commit_start = time.time()
    batch_commit_simulation_results(
        matches_data,
        cup_matches_data,
        results,
        all_performances,
        all_player_updates,
        all_lane_records,
        next_calendar_day.match_day_number,
        next_calendar_day.calendar_date  # Pass the correct calendar date
    )

    # Step 9: Check for completed cup rounds and advance if necessary
    if cup_matches_data:
        try:
            advance_completed_cup_rounds(season.id, next_calendar_day.match_day_number)
        except Exception as e:
            print(f"Error advancing cup rounds: {str(e)}")

    # Step 10: Mark calendar day as simulated
    mark_calendar_day_simulated(next_calendar_day.id)

    return {
        'season': season.name,
        'matches_simulated': len(results),
        'results': results,
        'match_day': next_calendar_day.match_day_number,
        'calendar_week': getattr(next_calendar_day, 'week_number', 1),
        'day_type': next_calendar_day.day_type,
        'match_date': next_calendar_day.calendar_date.isoformat() if next_calendar_day.calendar_date else None
    }








def advance_completed_cup_rounds(season_id, match_day):
    """Check for completed cup rounds and advance to next round if all matches are played."""
    from models import Cup, CupMatch
    from sqlalchemy import text

    # Get all cups for this season
    cups = Cup.query.filter_by(season_id=season_id, is_active=True).all()

    for cup in cups:
        try:
            # Check if any matches were played on this match day for this cup
            played_matches_today = db.session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM cup_match cm
                    WHERE cm.cup_id = :cup_id
                        AND cm.cup_match_day = :match_day
                        AND cm.is_played = 1
                """),
                {"cup_id": cup.id, "match_day": match_day}
            ).scalar()

            # Try to advance if matches were played today OR if all matches in current round are completed
            # This handles cases where matches were played on previous days but advancement was missed
            should_check_advancement = played_matches_today > 0

            if not should_check_advancement:
                # Check if all matches in current round are completed (fallback for missed advancements)
                current_round_matches = CupMatch.query.filter_by(
                    cup_id=cup.id,
                    round_number=cup.current_round_number
                ).all()

                if current_round_matches:
                    all_played = all(match.is_played for match in current_round_matches)
                    if all_played:
                        should_check_advancement = True

            if should_check_advancement:
                # Check if this cup can advance to the next round
                # This will check ALL matches in the current round, not just today's
                success = cup.advance_to_next_round()

        except Exception as e:
            print(f"Error advancing cup {cup.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    # Commit any changes made during cup advancement
    db.session.commit()


def simulate_matches_parallel(matches_data, club_team_players, next_match_day, cache_manager):
    """
    Simulate matches in parallel for better performance.

    Args:
        matches_data: List of match data from optimized_match_queries
        club_team_players: Dictionary mapping club_id -> team_id -> players
        next_match_day: The match day being simulated
        cache_manager: CacheManager instance for caching

    Returns:
        tuple: (results, all_performances, all_player_updates, all_lane_records)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    from flask import current_app

    # For now, use sequential simulation to avoid context issues
    # TODO: Fix parallel simulation context issues in future version
    return _simulate_matches_sequential(matches_data, club_team_players, next_match_day, cache_manager)



def _simulate_matches_sequential(matches_data, club_team_players, next_match_day, cache_manager):
    """
    Sequential simulation fallback when parallel simulation fails.
    """
    results = []
    all_performances = []
    all_player_updates = []
    all_lane_records = []

    for match_data in matches_data:
        try:
            # Convert match_data to dictionary if it's a SQLAlchemy row
            if hasattr(match_data, '_asdict'):
                match_dict = match_data._asdict()
            elif hasattr(match_data, 'keys'):
                match_dict = dict(match_data)
            elif isinstance(match_data, dict):
                match_dict = match_data
            else:
                # Fallback: assume it's a tuple from the SQL query
                # Based on the query in optimized_match_queries: (id, league_id, home_team_id, away_team_id, home_team_name, away_team_name, home_club_id, away_club_id, league_name)
                match_dict = {
                    'match_id': match_data[0],
                    'league_id': match_data[1],
                    'home_team_id': match_data[2],
                    'away_team_id': match_data[3],
                    'home_team_name': match_data[4],
                    'away_team_name': match_data[5],
                    'home_club_id': match_data[6],
                    'away_club_id': match_data[7],
                    'league_name': match_data[8],
                    'is_cup_match': False  # League matches don't have this field
                }

            # Determine if this is a cup match or league match
            is_cup_match = match_dict.get('is_cup_match', False)

            if is_cup_match:
                # Get cup match object
                from models import CupMatch
                match = CupMatch.query.get(match_dict['match_id'])
                if not match:
                    continue
                # Get teams from the cup match
                home_team = match.home_team
                away_team = match.away_team
            else:
                # Get league match object
                match = Match.query.get(match_dict['match_id'])
                if not match:
                    continue
                home_team = match.home_team
                away_team = match.away_team

            # Get assigned players
            home_team_id = match_dict.get('home_team_id') or home_team.id
            away_team_id = match_dict.get('away_team_id') or away_team.id
            home_club_id = match_dict.get('home_club_id') or home_team.club_id
            away_club_id = match_dict.get('away_club_id') or away_team.club_id

            home_players = club_team_players.get(home_club_id, {}).get(home_team_id, [])
            away_players = club_team_players.get(away_club_id, {}).get(away_team_id, [])

            # Convert player data dictionaries to objects for compatibility
            home_player_objects = []
            away_player_objects = []

            for player_data in home_players:
                if isinstance(player_data, dict):
                    # Create a simple object from dictionary with proper attribute assignment
                    player_obj = SimplePlayer(player_data)
                    home_player_objects.append(player_obj)
                else:
                    home_player_objects.append(player_data)

            for player_data in away_players:
                if isinstance(player_data, dict):
                    # Create a simple object from dictionary with proper attribute assignment
                    player_obj = SimplePlayer(player_data)
                    away_player_objects.append(player_obj)
                else:
                    away_player_objects.append(player_data)

            # Note: Position optimization is already handled in club_player_assignment.py

            # Simulate the match without database operations
            match_result = simulate_match(
                home_team,
                away_team,
                home_player_objects,
                away_player_objects,
                cache_manager,
                match_id=match_dict.get('match_id')
            )

            # Prepare match result data
            match_result.update({
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'home_team_name': match_dict.get('home_team_name') or home_team.name,
                'away_team_name': match_dict.get('away_team_name') or away_team.name,
                'league_name': match_dict.get('league_name') or (match_dict.get('cup_name') if is_cup_match else ''),
                'match_day': next_match_day,
                'is_cup_match': is_cup_match
            })

            # Add match_id to all performance data
            for performance in match_result.get('performances', []):
                performance['match_id'] = match_dict.get('match_id')

            # Print cup match results
            if is_cup_match:
                home_team_name = match_dict.get('home_team_name') or home_team.name
                away_team_name = match_dict.get('away_team_name') or away_team.name
                cup_name = match_dict.get('cup_name', 'Unknown Cup')
                round_name = match_dict.get('round_name', 'Unknown Round')
                home_score = match_result['home_score']
                away_score = match_result['away_score']
                home_match_points = match_result['home_match_points']
                away_match_points = match_result['away_match_points']

                # Determine winner
                if home_match_points > away_match_points:
                    winner_name = home_team_name
                elif away_match_points > home_match_points:
                    winner_name = away_team_name
                else:
                    # In case of a tie on match points, the team with more total pins wins
                    if home_score > away_score:
                        winner_name = home_team_name
                    else:
                        winner_name = away_team_name

            # Collect data
            results.append(match_result)
            all_performances.extend(match_result.get('performances', []))
            all_lane_records.extend(match_result.get('lane_records', []))

            # Collect player updates (skip Stroh players)
            for player in home_player_objects + away_player_objects:
                try:
                    # Skip Stroh players - they don't get saved to database
                    if isinstance(player, dict) and player.get('is_stroh', False):
                        continue

                    if hasattr(player, 'id'):
                        player_id = player.id
                    elif isinstance(player, dict) and 'id' in player:
                        player_id = player['id']
                    else:
                        continue
                    all_player_updates.append((player_id, True, next_match_day))
                except Exception as e:
                    continue

        except Exception as e:
            match_id = getattr(match_data, 'match_id', match_data[0] if hasattr(match_data, '__getitem__') else 'unknown')
            print(f"Error simulating match {match_id} in sequential mode: {str(e)}")
            import traceback
            traceback.print_exc()

    return results, all_performances, all_player_updates, all_lane_records


def simulate_match(home_team, away_team, home_players, away_players, cache_manager, match_id=None):
    """
    Simulate a bowling match between two teams and return the result.

    In bowling, 6 players from each team play 4 lanes with 30 throws each.
    Players compete directly against each other (1st vs 1st, 2nd vs 2nd, etc.).
    For each lane, the player with more pins gets 1 set point (SP).
    If both players score the same on a lane, each gets 0.5 SP.
    The player with more SP gets 1 match point (MP).
    If both players have 2 SP each, the player with more total pins gets the MP.
    The team with more total pins gets 2 additional MP.
    The team with more MP wins the match.

    This version collects all data and returns it for batch processing.

    Args:
        home_team: The home team
        away_team: The away team
        home_players: Pre-assigned players for the home team
        away_players: Pre-assigned players for the away team
        cache_manager: CacheManager instance for performance optimization
        match_id: Optional match ID to include in the result

    Returns:
        dict: Match result with scores, match points, performances, and lane records
    """

    # Fill both teams with Stroh players if needed
    home_players = fill_with_stroh_players(home_players, home_team.name)
    away_players = fill_with_stroh_players(away_players, away_team.name)

    # Use cached lane quality
    home_club_id = home_team.club_id
    lane_quality = cache_manager.get_lane_quality(home_club_id)

    # Home advantage (2%)
    home_advantage = 1.02

    # Initialize scores and match points
    home_score = 0
    away_score = 0
    home_match_points = 0
    away_match_points = 0

    performances = []
    lane_records = []
    stroh_performances = []  # Store Stroh player performances separately

    # Simulate each player pair (6 pairs total)
    for i, (home_player, away_player) in enumerate(zip(home_players, away_players)):
        # Simulate home player
        home_result = simulate_player_performance(
            home_player, i, lane_quality, home_advantage, True, cache_manager
        )

        # Simulate away player
        away_result = simulate_player_performance(
            away_player, i, lane_quality, 1.0, False, cache_manager
        )

        # Calculate set points for each lane
        home_set_points = 0
        away_set_points = 0

        for lane in range(4):
            home_lane_score = home_result['lane_scores'][lane]
            away_lane_score = away_result['lane_scores'][lane]

            if home_lane_score > away_lane_score:
                home_set_points += 1
            elif away_lane_score > home_lane_score:
                away_set_points += 1
            else:
                # Tie on this lane, both get 0.5 SP
                home_set_points += 0.5
                away_set_points += 0.5

        # Update performance data with calculated set points
        home_result['performance']['set_points'] = home_set_points
        away_result['performance']['set_points'] = away_set_points

        # Add to team scores
        home_score += home_result['total_score']
        away_score += away_result['total_score']

        # Calculate match points for this player duel
        if home_set_points > away_set_points:
            home_match_points += 1
            home_result['performance']['match_points'] = 1
            away_result['performance']['match_points'] = 0
        elif away_set_points > home_set_points:
            away_match_points += 1
            home_result['performance']['match_points'] = 0
            away_result['performance']['match_points'] = 1
        else:
            # Tie on set points, player with more total pins gets the MP
            if home_result['total_score'] > away_result['total_score']:
                home_match_points += 1
                home_result['performance']['match_points'] = 1
                away_result['performance']['match_points'] = 0
            elif away_result['total_score'] > home_result['total_score']:
                away_match_points += 1
                home_result['performance']['match_points'] = 0
                away_result['performance']['match_points'] = 1
            else:
                # Complete tie, both get 0.5 MP
                home_match_points += 0.5
                away_match_points += 0.5
                home_result['performance']['match_points'] = 0.5
                away_result['performance']['match_points'] = 0.5

        # Store performance data for batch creation with correct team information
        # Only store performances for real players, not Stroh players
        if not (isinstance(home_player, dict) and home_player.get('is_stroh', False)):
            # Ensure team_id and is_home_team are properly set to prevent data corruption
            home_result['performance']['team_id'] = home_team.id
            home_result['performance']['is_home_team'] = True

            # Validate that the team_id is correct (home team should match home_team.id)
            if home_result['performance']['team_id'] != home_team.id:
                continue

            performances.append(home_result['performance'])

        if not (isinstance(away_player, dict) and away_player.get('is_stroh', False)):
            # Ensure team_id and is_home_team are properly set to prevent data corruption
            away_result['performance']['team_id'] = away_team.id
            away_result['performance']['is_home_team'] = False

            # Validate that the team_id is correct (away team should match away_team.id)
            if away_result['performance']['team_id'] != away_team.id:
                continue

            performances.append(away_result['performance'])

        # Check for potential lane records (only for real players, not Stroh players)
        if not (isinstance(home_player, dict) and home_player.get('is_stroh', False)):
            player_id_home = home_player.id if hasattr(home_player, 'id') else home_player['id']
            lane_records.append({'club_id': home_club_id, 'score': home_result['total_score'], 'player_id': player_id_home})

        if not (isinstance(away_player, dict) and away_player.get('is_stroh', False)):
            player_id_away = away_player.id if hasattr(away_player, 'id') else away_player['id']
            lane_records.append({'club_id': home_club_id, 'score': away_result['total_score'], 'player_id': player_id_away})

    # Add 2 additional MP for the team with more total pins
    if home_score > away_score:
        home_match_points += 2
    elif away_score > home_score:
        away_match_points += 2
    else:
        # Tie on total pins, both get 1 MP
        home_match_points += 1
        away_match_points += 1

    # Check for team lane records
    lane_records.extend([
        {'club_id': home_club_id, 'score': home_score, 'team_id': home_team.id},
        {'club_id': home_club_id, 'score': away_score, 'team_id': away_team.id}
    ])

    result = {
        'home_team': home_team.name,
        'away_team': away_team.name,
        'home_score': home_score,
        'away_score': away_score,
        'home_match_points': home_match_points,
        'away_match_points': away_match_points,
        'winner': home_team.name if home_match_points > away_match_points else (away_team.name if away_match_points > home_match_points else 'Draw'),
        'performances': performances,
        'lane_records': lane_records
    }

    # Add match_id if provided
    if match_id is not None:
        result['match_id'] = match_id

    return result


def simulate_player_performance(player, position, lane_quality, team_advantage, is_home, cache_manager):
    """
    Simulate performance for a single player across 4 lanes.

    Args:
        player: Player object or dictionary with player data
        position: Position in lineup (0-5)
        lane_quality: Lane quality factor
        team_advantage: Team advantage factor (home advantage for home team)
        is_home: Whether this is the home team
        cache_manager: CacheManager instance

    Returns:
        dict: Player performance data
    """
    # Get player attributes (handle both objects and dictionaries)
    def get_attr(obj, attr, default=50):
        try:
            if hasattr(obj, attr):
                return getattr(obj, attr)
            elif isinstance(obj, dict):
                return obj.get(attr, default)
            else:
                return default
        except Exception as e:
            return default

    player_id = get_attr(player, 'id')
    strength = get_attr(player, 'strength', 50)
    konstanz = get_attr(player, 'konstanz', 50)
    drucksicherheit = get_attr(player, 'drucksicherheit', 50)
    volle = get_attr(player, 'volle', 50)
    raeumer = get_attr(player, 'raeumer', 50)
    ausdauer = get_attr(player, 'ausdauer', 50)
    sicherheit = get_attr(player, 'sicherheit', 50)
    auswaerts = get_attr(player, 'auswaerts', 50)
    start = get_attr(player, 'start', 50)
    mitte = get_attr(player, 'mitte', 50)
    schluss = get_attr(player, 'schluss', 50)

    # Apply form modifiers using the percentage-based approach from form_system.py
    form_short = get_attr(player, 'form_short_term', 0.0)
    form_medium = get_attr(player, 'form_medium_term', 0.0)
    form_long = get_attr(player, 'form_long_term', 0.0)

    # Check if form is active (remaining days > 0)
    form_short_active = get_attr(player, 'form_short_remaining_days', 0) > 0
    form_medium_active = get_attr(player, 'form_medium_remaining_days', 0) > 0
    form_long_active = get_attr(player, 'form_long_remaining_days', 0) > 0

    # Only apply form modifiers if they are active
    # modify with 0.5 so effects are not too strong
    total_form_modifier = 0.0
    if form_short_active:
        total_form_modifier += form_short*0.5
    if form_medium_active:
        total_form_modifier += form_medium*0.5
    if form_long_active:
        total_form_modifier += form_long*0.5

    # Apply form as percentage modifier: strength * (1 + form_modifier)
    effective_strength = strength #* (1 + total_form_modifier)
    effective_strength = max(1, min(99, effective_strength))  # Clamp to valid range

    # Simulate 4 lanes
    lane_scores = []
    total_score = 0
    total_volle = 0
    total_raeumer = 0

    for lane in range(4):
        # Base score calculation
        mean_score = 120 + (effective_strength * 0.6)

        # Apply lane quality
        mean_score *= lane_quality

        # Apply team advantage (home advantage for home team)
        mean_score *= team_advantage

        # Apply away factor for away players
        if not is_home:
            away_factor = 0.98 + (auswaerts / 2500)  # 0.98 to 1.02 range
            mean_score *= away_factor

        # Apply position-based attributes
        if position in [0, 1]:  # Start pair
            position_factor = 0.8 + (start / 500)
        elif position in [2, 3]:  # Middle pair
            position_factor = 0.8 + (mitte / 500)
        else:  # End pair
            position_factor = 0.8 + (schluss / 500)

        mean_score *= position_factor

        # Apply pressure on last lane
        if lane == 3:
            pressure_factor = 0.9 + (drucksicherheit / 500)
            mean_score *= pressure_factor

        # Apply stamina factor (decreases with each lane)
        ausdauer_factor = max(0.95, ausdauer / 100 - (lane * 0.01))
        mean_score *= ausdauer_factor

        # Add randomness based on consistency
        std_dev = 12 - (konstanz / 20)  # 12 to 7 based on konstanz
        lane_score = int(np.random.normal(mean_score, std_dev))
        lane_score = max(80, min(200, lane_score))  # Clamp to reasonable range

        # Calculate Volle and Räumer
        volle_percentage = 0.5 + (volle / max(1, volle + raeumer)) * 0.3
        volle_percentage += np.random.normal(0, 0.02)
        volle_percentage = max(0.55, min(0.75, volle_percentage))

        lane_volle = int(lane_score * volle_percentage)
        lane_raeumer = lane_score - lane_volle

        lane_scores.append(lane_score)
        total_score += lane_score
        total_volle += lane_volle
        total_raeumer += lane_raeumer

    # Calculate realistic errors
    fehler_count = calculate_realistic_fehler(total_score, sicherheit)

    # Calculate set points (will be calculated against opponent later)
    set_points = 0  # This will be calculated in the match simulation

    # Create performance data structure
    # Note: team_id and is_home_team should be set by the calling function
    performance_data = {
        'player_id': player_id,
        'team_id': None,  # MUST be set by calling function to prevent data corruption
        'is_home_team': None,  # MUST be set by calling function to prevent data corruption
        'position_number': position + 1,
        'is_substitute': False,  # We'll handle substitutes separately
        'lane1_score': lane_scores[0],
        'lane2_score': lane_scores[1],
        'lane3_score': lane_scores[2],
        'lane4_score': lane_scores[3],
        'total_score': total_score,
        'volle_score': total_volle,
        'raeumer_score': total_raeumer,
        'fehler_count': fehler_count,
        'set_points': set_points,  # Will be updated later
        'match_points': 0  # Will be updated later
    }

    return {
        'lane_scores': lane_scores,
        'total_score': total_score,
        'volle_score': total_volle,
        'raeumer_score': total_raeumer,
        'fehler_count': fehler_count,
        'set_points': set_points,
        'performance': performance_data
    }


def batch_commit_simulation_results(matches_data, cup_matches_data, results, all_performances, all_player_updates, all_lane_records, next_match_day, calendar_date=None):
    """
    Batch commit all simulation results to the database.

    Args:
        matches_data: Original league match data for today
        cup_matches_data: Original cup match data for today
        results: Match results (both league and cup matches)
        all_performances: All player performances
        all_player_updates: All player flag updates
        all_lane_records: All lane record checks
        next_match_day: The match day being simulated
        calendar_date: The correct calendar date for this match day
    """
    from performance_optimizations import batch_create_performances, batch_create_cup_performances
    import time

    start_time = time.time()

    try:
        # Create sets of match IDs that were actually played today
        # This prevents updating dates for matches that weren't played today
        league_matches_today = set()
        cup_matches_today = set()

        # Get league match IDs from matches_data (these were played today)
        if matches_data:
            for match_data in matches_data:
                match_id = getattr(match_data, 'match_id', None)
                if match_id:
                    league_matches_today.add(match_id)

        # Get cup match IDs from cup_matches_data (these were played today)
        if cup_matches_data:
            for cup_match_data in cup_matches_data:
                # cup_matches_data contains dictionaries with 'match_id' or 'cup_match_id'
                if isinstance(cup_match_data, dict):
                    match_id = cup_match_data.get('match_id') or cup_match_data.get('cup_match_id')
                else:
                    match_id = getattr(cup_match_data, 'cup_match_id', None) or getattr(cup_match_data, 'match_id', None)
                if match_id:
                    cup_matches_today.add(match_id)

        # Update match records (both league and cup matches)
        league_match_updates = {}
        cup_match_updates = {}

        for i, result in enumerate(results):
            match_id = result.get('match_id')
            is_cup_match = result.get('is_cup_match', False)

            if match_id:
                update_data = {
                    'home_score': result['home_score'],
                    'away_score': result['away_score'],
                    'is_played': True
                }

                if is_cup_match:
                    # For cup matches, we also need to determine the winner
                    from models import CupMatch
                    if result['home_match_points'] > result['away_match_points']:
                        update_data['winner_team_id'] = result.get('home_team_id')
                    elif result['away_match_points'] > result['home_match_points']:
                        update_data['winner_team_id'] = result.get('away_team_id')
                    else:
                        # In case of a tie in cup matches, home team wins (or we could use total pins)
                        if result['home_score'] >= result['away_score']:
                            update_data['winner_team_id'] = result.get('home_team_id')
                        else:
                            update_data['winner_team_id'] = result.get('away_team_id')

                    # Add set points for cup matches
                    update_data['home_set_points'] = result['home_match_points']
                    update_data['away_set_points'] = result['away_match_points']

                    # Only update match_date if this cup match was scheduled for today
                    if calendar_date and match_id in cup_matches_today:
                        # For cup matches, store as date only (not datetime)
                        if hasattr(calendar_date, 'date'):
                            update_data['match_date'] = calendar_date.date()
                        else:
                            update_data['match_date'] = calendar_date

                    cup_match_updates[match_id] = update_data
                else:
                    # For league matches, add match points and preserve correct date
                    update_data['home_match_points'] = result['home_match_points']
                    update_data['away_match_points'] = result['away_match_points']

                    # Only update match_date if this league match was scheduled for today
                    if calendar_date and match_id in league_matches_today:
                        # Convert date to datetime at 15:00 (3 PM) with timezone
                        if hasattr(calendar_date, 'date'):
                            # calendar_date is already a datetime
                            update_data['match_date'] = calendar_date
                        else:
                            # calendar_date is a date, convert to datetime
                            update_data['match_date'] = datetime.combine(
                                calendar_date,
                                datetime.min.time().replace(hour=15),
                                tzinfo=timezone.utc
                            )
                    # If no calendar_date provided or match not scheduled today, don't update match_date

                    league_match_updates[match_id] = update_data

        # Batch update league matches
        for match_id, updates in league_match_updates.items():
            db.session.execute(
                db.update(Match)
                .where(Match.id == match_id)
                .values(**updates)
            )

        # Batch update cup matches
        if cup_match_updates:
            from models import CupMatch
            for match_id, updates in cup_match_updates.items():
                db.session.execute(
                    db.update(CupMatch)
                    .where(CupMatch.id == match_id)
                    .values(**updates)
                )

        # Batch create performances - separate league and cup performances
        if all_performances:
            # Separate performances by type
            league_performances = []
            cup_performances = []

            # Create mappings for both league and cup matches
            league_match_mapping = {}
            cup_match_mapping = {}

            for result in results:
                match_id = result.get('match_id')
                is_cup_match = result.get('is_cup_match', False)

                if match_id:
                    if is_cup_match:
                        # Get cup match to find team IDs
                        from models import CupMatch
                        cup_match = CupMatch.query.get(match_id)
                        if cup_match:
                            cup_match_mapping[match_id] = {
                                'home_team_id': cup_match.home_team_id,
                                'away_team_id': cup_match.away_team_id
                            }
                    else:
                        # Get league match to find team IDs
                        match = Match.query.get(match_id)
                        if match:
                            league_match_mapping[match_id] = {
                                'home_team_id': match.home_team_id,
                                'away_team_id': match.away_team_id
                            }

            # Process each performance and categorize by type
            for i, perf in enumerate(all_performances):
                if isinstance(perf, dict):
                    perf_dict = perf.copy()

                    # Check if this performance has a match_id
                    match_id = perf_dict.get('match_id')
                    if not match_id:
                        continue

                    # Determine if this is a cup match or league match
                    # Check if match_id exists in cup_match_mapping or league_match_mapping
                    is_cup_performance = match_id in cup_match_mapping
                    is_league_performance = match_id in league_match_mapping

                    if not is_cup_performance and not is_league_performance:
                        continue

                    # Validate required fields
                    if not (perf_dict.get('player_id') and perf_dict.get('team_id')):
                        continue

                    if is_cup_performance:
                        # Convert match_id to cup_match_id for cup performances
                        perf_dict['cup_match_id'] = perf_dict.pop('match_id')
                        cup_performances.append(perf_dict)
                    else:
                        # Keep as league performance
                        league_performances.append(perf_dict)
                else:
                    # Convert object to dict if needed
                    perf_dict = perf.__dict__.copy()
                    match_id = perf_dict.get('match_id')

                    if match_id in cup_match_mapping:
                        perf_dict['cup_match_id'] = perf_dict.pop('match_id')
                        cup_performances.append(perf_dict)
                    elif match_id in league_match_mapping:
                        league_performances.append(perf_dict)
                    else:
                        continue

            # Create performances in their respective tables
            if league_performances:
                batch_create_performances(league_performances)

            if cup_performances:
                batch_create_cup_performances(cup_performances)

        # Batch update player flags
        if all_player_updates:
            batch_update_player_flags(all_player_updates)

        # Process lane records (this might need to be done individually due to complex logic)
        if all_lane_records:
            # Add match_id information to lane records from results
            enhanced_lane_records = []
            for i, result in enumerate(results):
                match_id = result.get('match_id')
                if match_id and 'lane_records' in result:
                    for record in result['lane_records']:
                        record['match_id'] = match_id
                        enhanced_lane_records.append(record)

            if enhanced_lane_records:
                process_lane_records_batch(enhanced_lane_records)

        # Single commit for all changes
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Error in batch commit: {str(e)}")
        raise


def process_lane_records_batch(all_lane_records):
    """
    Process lane records in batch for better performance.

    Args:
        all_lane_records: List of lane record data
    """
    from models import LaneRecord, Player, Team

    if not all_lane_records:
        return

    # Process each record individually to check for new records
    records_processed = 0
    new_records_set = 0

    for record_data in all_lane_records:
        try:
            club_id = record_data['club_id']
            score = record_data['score']

            # Handle player records
            if 'player_id' in record_data:
                player_id = record_data['player_id']
                player = Player.query.get(player_id)

                if player:
                    # Get match_id if available (might not be set yet during batch processing)
                    match_id = record_data.get('match_id', None)

                    # Check and update individual record (don't commit, will be committed in batch)
                    if LaneRecord.check_and_update_record(
                        club_id=club_id,
                        score=score,
                        player=player,
                        match_id=match_id,
                        commit=False
                    ):
                        new_records_set += 1

            # Handle team records
            elif 'team_id' in record_data:
                team_id = record_data['team_id']
                team = Team.query.get(team_id)

                if team:
                    # Get match_id if available
                    match_id = record_data.get('match_id', None)

                    # Check and update team record (don't commit, will be committed in batch)
                    if LaneRecord.check_and_update_record(
                        club_id=club_id,
                        score=score,
                        team=team,
                        match_id=match_id,
                        commit=False
                    ):
                        new_records_set += 1

            records_processed += 1

        except Exception as e:
            print(f"Error processing lane record {record_data}: {str(e)}")
            continue


# Removed duplicate function - using the one below






# Function removed - use determine_player_availability from performance_optimizations.py directly




def batch_update_player_flags(player_updates):
    """
    Batch update player flags to reduce database operations.

    Args:
        player_updates: List of tuples (player_id, has_played, last_played_matchday)
    """
    if not player_updates:
        return

    try:
        # Validate input data
        for i, update in enumerate(player_updates):
            if len(update) != 3:
                raise ValueError(f"Invalid update tuple at index {i}: {update}. Expected (player_id, has_played, last_matchday)")

            player_id, has_played, last_matchday = update

            # Ensure player_id is an integer
            if not isinstance(player_id, int):
                raise ValueError(f"Invalid player_id at index {i}: {player_id} (type: {type(player_id)}). Expected integer.")

        # Group updates by values to minimize database operations
        played_players = []
        matchday_updates = {}

        for player_id, has_played, last_matchday in player_updates:
            if has_played:
                played_players.append(player_id)
            if last_matchday is not None:
                if last_matchday not in matchday_updates:
                    matchday_updates[last_matchday] = []
                matchday_updates[last_matchday].append(player_id)

        # Update has_played_current_matchday for all players who played
        if played_players:
            db.session.execute(
                db.update(Player)
                .where(Player.id.in_(played_players))
                .values(has_played_current_matchday=True)
            )

        # Update last_played_matchday for each group
        for matchday, player_ids in matchday_updates.items():
            db.session.execute(
                db.update(Player)
                .where(Player.id.in_(player_ids))
                .values(last_played_matchday=matchday)
            )

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Error in batch update: {str(e)}")
        raise

def simulate_season(season, create_new_season=True):
    """Simulate all matches for a season by repeatedly calling simulate_match_day.

    Args:
        season: The season to simulate
        create_new_season: Whether to create a new season after simulation (default: True)
    """
    # Get all leagues in the season
    leagues = season.leagues

    # Check if any leagues are empty
    empty_leagues = []
    for league in leagues:
        teams = Team.query.filter_by(league_id=league.id).all()
        if len(teams) == 0:
            empty_leagues.append(league.name)

    if empty_leagues:
        error_msg = f"Cannot simulate season: The following leagues have no teams: {', '.join(empty_leagues)}. Please check the season transition logic."

        return {
            'season': season.name,
            'matches_simulated': 0,
            'results': [],
            'error': error_msg,
            'new_season_created': False,
            'new_season_id': None
        }

    # Initialize cups for the season if they don't exist
    try:
        from app import auto_initialize_cups
        auto_initialize_cups(season.id)
    except Exception as e:
        pass

    # Ensure all leagues have fixtures generated
    for league in leagues:
        teams_in_league = Team.query.filter_by(league_id=league.id).all()
        matches_in_league = Match.query.filter_by(league_id=league.id, season_id=season.id).count()

        if len(teams_in_league) >= 2 and matches_in_league == 0:
            generate_fixtures(league, season)

    # Track total results and matches simulated
    all_results = []
    total_matches_simulated = 0
    new_season_created = False
    new_season_id = None

    # Simulate the season by repeatedly calling simulate_match_day until complete
    match_day_count = 0
    while True:
        match_day_count += 1

        # Use the same logic as the single match day simulation
        match_day_result = simulate_match_day(season)

        # Check if simulation is complete
        if match_day_result['matches_simulated'] == 0:
            break

        # Add results to our total
        all_results.extend(match_day_result.get('results', []))
        total_matches_simulated += match_day_result['matches_simulated']

    # Check if season is complete and handle end-of-season processing
    from models import Cup, CupMatch

    # Check if all league matches are played
    total_league_matches = Match.query.filter_by(season_id=season.id).count()
    played_league_matches = Match.query.filter_by(season_id=season.id, is_played=True).count()

    # Check if all cup matches are played
    cups = Cup.query.filter_by(season_id=season.id).all()
    total_cup_matches = 0
    played_cup_matches = 0

    for cup in cups:
        cup_matches = CupMatch.query.filter_by(cup_id=cup.id).all()
        total_cup_matches += len(cup_matches)
        played_cup_matches += len([m for m in cup_matches if m.is_played])

    season_complete = (played_league_matches == total_league_matches and
                      played_cup_matches == total_cup_matches)

    if season_complete and create_new_season:
        try:
            new_season = process_end_of_season(season)
            if new_season:
                new_season_created = True
                new_season_id = new_season.id
        except Exception as e:
            print(f"Error creating new season: {str(e)}")

    return {
        'season': season.name,
        'matches_simulated': total_matches_simulated,
        'results': all_results,
        'new_season_created': new_season_created,
        'new_season_id': new_season_id
    }

def generate_fixtures(league, season):
    """Generate fixtures (matches) for a league in a season using a round-robin tournament algorithm.
    Ensures teams alternate between home and away matches as much as possible."""
    # Use direct query instead of relationship to ensure we get updated team assignments
    teams = list(Team.query.filter_by(league_id=league.id).all())

    # Need at least 2 teams to create fixtures
    if len(teams) < 2:
        return

    # If odd number of teams, add a dummy team (bye)
    if len(teams) % 2 != 0:
        teams.append(None)

    num_teams = len(teams)
    num_rounds = num_teams - 1
    matches_per_round = num_teams // 2

    # Dictionary to track the last match type for each team (True for home, False for away)
    # Initialize with None (no matches played yet)
    last_match_type = {team.id: None for team in teams if team is not None}

    # Dictionary to track consecutive home/away matches for each team
    consecutive_matches = {team.id: 0 for team in teams if team is not None}

    # List to store all matches before committing to database
    all_matches = []

    # First half of the season (round 1)
    for round_num in range(num_rounds):
        round_matches = []

        # Generate matches for this round
        for match_num in range(matches_per_round):
            home_idx = (round_num + match_num) % (num_teams - 1)
            away_idx = (num_teams - 1 - match_num + round_num) % (num_teams - 1)

            # Last team stays fixed, others rotate
            if match_num == 0:
                away_idx = num_teams - 1

            # Skip matches with dummy team (bye)
            if teams[home_idx] is None or teams[away_idx] is None:
                continue

            # Create match with proper match day
            match_day = round_num + 1

            # Check if we should swap home/away to ensure alternation
            should_swap = False

            if teams[home_idx] and teams[away_idx]:
                home_team_id = teams[home_idx].id
                away_team_id = teams[away_idx].id

                # If home team had a home match last time and away team had an away match last time,
                # consider swapping to maintain alternation
                if (last_match_type[home_team_id] == True and
                    last_match_type[away_team_id] == False):
                    # Only swap if both teams have had consecutive matches of the same type
                    if consecutive_matches[home_team_id] > 0 and consecutive_matches[away_team_id] > 0:
                        should_swap = True

            if should_swap:
                # Swap home and away teams
                match = Match(
                    home_team_id=teams[away_idx].id,
                    away_team_id=teams[home_idx].id,
                    league_id=league.id,
                    season_id=season.id,
                    match_day=match_day,
                    round=1,  # First half of season
                    is_played=False
                )

                # Update tracking dictionaries
                last_match_type[teams[away_idx].id] = True
                last_match_type[teams[home_idx].id] = False

                if last_match_type[teams[away_idx].id] == True:
                    consecutive_matches[teams[away_idx].id] += 1
                else:
                    consecutive_matches[teams[away_idx].id] = 1

                if last_match_type[teams[home_idx].id] == False:
                    consecutive_matches[teams[home_idx].id] += 1
                else:
                    consecutive_matches[teams[home_idx].id] = 1
            else:
                # Create match normally
                match = Match(
                    home_team_id=teams[home_idx].id,
                    away_team_id=teams[away_idx].id,
                    league_id=league.id,
                    season_id=season.id,
                    match_day=match_day,
                    round=1,  # First half of season
                    is_played=False
                )

                # Update tracking dictionaries
                if teams[home_idx] and teams[away_idx]:
                    last_match_type[teams[home_idx].id] = True
                    last_match_type[teams[away_idx].id] = False

                    if last_match_type[teams[home_idx].id] == True:
                        consecutive_matches[teams[home_idx].id] += 1
                    else:
                        consecutive_matches[teams[home_idx].id] = 1

                    if last_match_type[teams[away_idx].id] == False:
                        consecutive_matches[teams[away_idx].id] += 1
                    else:
                        consecutive_matches[teams[away_idx].id] = 1

            round_matches.append(match)

        # Add all matches for this round
        all_matches.extend(round_matches)

    # Reset tracking dictionaries for second half
    last_match_type = {team.id: None for team in teams if team is not None}
    consecutive_matches = {team.id: 0 for team in teams if team is not None}

    # Second half of the season (round 2) - reverse home/away
    for round_num in range(num_rounds):
        round_matches = []

        # Generate matches for this round
        for match_num in range(matches_per_round):
            # Same as first half but home/away reversed
            away_idx = (round_num + match_num) % (num_teams - 1)
            home_idx = (num_teams - 1 - match_num + round_num) % (num_teams - 1)

            # Last team stays fixed, others rotate
            if match_num == 0:
                home_idx = num_teams - 1

            # Skip matches with dummy team (bye)
            if teams[home_idx] is None or teams[away_idx] is None:
                continue

            # Create match with proper match day (continue from first half)
            match_day = num_rounds + round_num + 1

            # Check if we should swap home/away to ensure alternation
            should_swap = False

            if teams[home_idx] and teams[away_idx]:
                home_team_id = teams[home_idx].id
                away_team_id = teams[away_idx].id

                # If home team had a home match last time and away team had an away match last time,
                # consider swapping to maintain alternation
                if (last_match_type[home_team_id] == True and
                    last_match_type[away_team_id] == False):
                    # Only swap if both teams have had consecutive matches of the same type
                    if consecutive_matches[home_team_id] > 0 and consecutive_matches[away_team_id] > 0:
                        should_swap = True

            if should_swap:
                # Swap home and away teams
                match = Match(
                    home_team_id=teams[away_idx].id,
                    away_team_id=teams[home_idx].id,
                    league_id=league.id,
                    season_id=season.id,
                    match_day=match_day,
                    round=2,  # Second half of season
                    is_played=False
                )

                # Update tracking dictionaries
                last_match_type[teams[away_idx].id] = True
                last_match_type[teams[home_idx].id] = False

                if last_match_type[teams[away_idx].id] == True:
                    consecutive_matches[teams[away_idx].id] += 1
                else:
                    consecutive_matches[teams[away_idx].id] = 1

                if last_match_type[teams[home_idx].id] == False:
                    consecutive_matches[teams[home_idx].id] += 1
                else:
                    consecutive_matches[teams[home_idx].id] = 1
            else:
                # Create match normally
                match = Match(
                    home_team_id=teams[home_idx].id,
                    away_team_id=teams[away_idx].id,
                    league_id=league.id,
                    season_id=season.id,
                    match_day=match_day,
                    round=2,  # Second half of season
                    is_played=False
                )

                # Update tracking dictionaries
                if teams[home_idx] and teams[away_idx]:
                    last_match_type[teams[home_idx].id] = True
                    last_match_type[teams[away_idx].id] = False

                    if last_match_type[teams[home_idx].id] == True:
                        consecutive_matches[teams[home_idx].id] += 1
                    else:
                        consecutive_matches[teams[home_idx].id] = 1

                    if last_match_type[teams[away_idx].id] == False:
                        consecutive_matches[teams[away_idx].id] += 1
                    else:
                        consecutive_matches[teams[away_idx].id] = 1

            round_matches.append(match)

        # Add all matches for this round
        all_matches.extend(round_matches)

    # Add all matches to the database
    for match in all_matches:
        db.session.add(match)

    db.session.commit()

    # Note: Match dates will be set later in init_db.py using unified calendar-based logic
    # This avoids calling set_all_match_dates_unified multiple times (once per league)

    # Get all matches for verification (needed regardless of which method was used above)
    matches = Match.query.filter_by(league_id=league.id, season_id=season.id).all()

    # Verify home/away alternation for each team
    team_matches = {}

    # Group matches by team
    for match in matches:
        if match.home_team_id not in team_matches:
            team_matches[match.home_team_id] = []
        if match.away_team_id not in team_matches:
            team_matches[match.away_team_id] = []

        # Add match to both teams' lists with a flag indicating home/away
        team_matches[match.home_team_id].append((match, True))  # True for home
        team_matches[match.away_team_id].append((match, False))  # False for away

    # Sort each team's matches by match day
    for team_id, team_match_list in team_matches.items():
        team_match_list.sort(key=lambda x: x[0].match_day)

        # Count consecutive home/away matches
        consecutive_home = 0
        consecutive_away = 0
        total_consecutive = 0

        for i in range(len(team_match_list)):
            is_home = team_match_list[i][1]

            if is_home:
                consecutive_home += 1
                consecutive_away = 0
            else:
                consecutive_away += 1
                consecutive_home = 0

            # Count matches with more than 2 consecutive home/away games
            if consecutive_home > 2 or consecutive_away > 2:
                total_consecutive += 1

        # Log teams with many consecutive matches of the same type
        if total_consecutive > 0:
            team = Team.query.get(team_id)

    db.session.commit()

def process_end_of_season(season):
    """Process end of season events like promotions and relegations."""

    # Save final standings to league history before creating new season
    save_league_history(season)

    # Save cup winners and finalists to cup history before creating new season
    save_cup_history(season)

    # Save team cup participation history before creating new season
    save_team_cup_history(season)

    # Save team achievements (league champions and cup winners) before creating new season
    save_team_achievements(season)

    # Create new season (this will handle promotions/relegations internally)
    create_new_season(season)

def save_league_history(season):
    """Save the final standings of all leagues to the league history table."""
    try:
        from models import LeagueHistory, League, db

        print("Saving league history for season:", season.name)

        # Check if LeagueHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'league_history' not in existing_tables:
            print("LeagueHistory table does not exist yet. Creating it...")
            # Create the table
            db.create_all()
            print("LeagueHistory table created successfully.")

        # Get all leagues for this season
        leagues = League.query.filter_by(season_id=season.id).all()
        print(f"Found {len(leagues)} leagues for season {season.name}")

        for league in leagues:
            print(f"Saving history for league: {league.name} (ID: {league.id})")

            # Calculate final standings
            standings = calculate_standings(league)
            print(f"Calculated {len(standings)} standings for league {league.name}")

            # Save each team's final position and statistics
            for i, standing in enumerate(standings):
                team = standing['team']
                position = i + 1  # Position is index + 1
                print(f"  Processing team {i+1}: {team.name} (Position: {position})")

                # Get club information
                club_name = team.club.name if team.club else None
                club_id = team.club.id if team.club else None
                verein_id = team.club.verein_id if team.club else None

                # Calculate games played
                games_played = standing['wins'] + standing['draws'] + standing['losses']

                # Calculate average scores (home and away)
                home_matches = Match.query.filter_by(home_team_id=team.id, league_id=league.id, is_played=True).all()
                away_matches = Match.query.filter_by(away_team_id=team.id, league_id=league.id, is_played=True).all()

                avg_home_score = 0.0
                avg_away_score = 0.0

                if home_matches:
                    total_home_score = sum(match.home_score for match in home_matches)
                    avg_home_score = total_home_score / len(home_matches)

                if away_matches:
                    total_away_score = sum(match.away_score for match in away_matches)
                    avg_away_score = total_away_score / len(away_matches)

                # Create league history entry
                history_entry = LeagueHistory(
                    league_name=league.name,
                    league_level=league.level,
                    season_id=season.id,
                    season_name=season.name,
                    team_id=team.id,
                    team_name=team.name,
                    club_name=club_name,
                    club_id=club_id,
                    verein_id=verein_id,
                    position=position,
                    games_played=games_played,
                    wins=standing['wins'],
                    draws=standing['draws'],
                    losses=standing['losses'],
                    table_points=standing['points'],
                    match_points_for=standing['match_points_for'],
                    match_points_against=standing['match_points_against'],
                    pins_for=standing['goals_for'],  # goals_for is actually pins_for
                    pins_against=standing['goals_against'],  # goals_against is actually pins_against
                    avg_home_score=avg_home_score,
                    avg_away_score=avg_away_score
                )

                print(f"    Created history entry: {team.name} -> Position {position}")
                db.session.add(history_entry)

            print(f"Added {len(standings)} teams for league {league.name} to session")

        # Commit all history entries
        print("Committing all history entries to database...")
        db.session.commit()
        print(f"League history saved successfully for {len(leagues)} leagues")

        # Verify the data was saved
        total_entries = LeagueHistory.query.filter_by(season_id=season.id).count()
        print(f"Verification: {total_entries} history entries saved for season {season.name}")

    except Exception as e:
        print(f"Error saving league history: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with season transition without saving history...")
        # Don't let history saving errors break the season transition
        try:
            db.session.rollback()
        except:
            pass


def save_cup_history(season):
    """Save the winners and finalists of all completed cups to the cup history table."""
    try:
        from models import CupHistory, Cup, CupMatch, Team, Club, db

        print("Saving cup history for season:", season.name)

        # Check if CupHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'cup_history' not in existing_tables:
            print("CupHistory table does not exist yet. Creating it...")
            # Create the table
            db.create_all()
            print("CupHistory table created successfully.")

        # Get all cups for this season
        cups = Cup.query.filter_by(season_id=season.id).all()
        print(f"Found {len(cups)} cups for season {season.name}")

        for cup in cups:
            print(f"Processing cup: {cup.name}")

            # Check if this cup is completed (not active)
            if cup.is_active:
                print(f"  Cup {cup.name} is still active, skipping...")
                continue

            # Find the final match (should be the last round)
            final_matches = CupMatch.query.filter_by(
                cup_id=cup.id,
                round_number=cup.total_rounds,
                is_played=True
            ).all()

            if not final_matches:
                print(f"  No final match found for cup {cup.name}, skipping...")
                continue

            # There should be exactly one final match
            if len(final_matches) != 1:
                print(f"  Expected 1 final match for cup {cup.name}, found {len(final_matches)}, skipping...")
                continue

            final_match = final_matches[0]

            # Get winner and finalist teams
            if not final_match.winner_team_id:
                print(f"  Final match for cup {cup.name} has no winner, skipping...")
                continue

            winner_team = Team.query.get(final_match.winner_team_id)
            if not winner_team:
                print(f"  Winner team not found for cup {cup.name}, skipping...")
                continue

            # Determine finalist (the team that lost the final)
            if final_match.home_team_id == final_match.winner_team_id:
                finalist_team = Team.query.get(final_match.away_team_id)
            else:
                finalist_team = Team.query.get(final_match.home_team_id)

            if not finalist_team:
                print(f"  Finalist team not found for cup {cup.name}, skipping...")
                continue

            # Get club information for winner
            winner_club = winner_team.club if winner_team.club else None
            winner_club_name = winner_club.name if winner_club else None
            winner_club_id = winner_club.id if winner_club else None
            winner_verein_id = winner_club.verein_id if winner_club else None

            # Get club information for finalist
            finalist_club = finalist_team.club if finalist_team.club else None
            finalist_club_name = finalist_club.name if finalist_club else None
            finalist_club_id = finalist_club.id if finalist_club else None
            finalist_verein_id = finalist_club.verein_id if finalist_club else None

            # Check if history entry already exists for this cup and season
            existing_entry = CupHistory.query.filter_by(
                cup_name=cup.name,
                season_id=season.id
            ).first()

            if existing_entry:
                print(f"  History entry already exists for cup {cup.name} in season {season.name}, skipping...")
                continue

            # Create cup history entry
            history_entry = CupHistory(
                cup_name=cup.name,
                cup_type=cup.cup_type,
                season_id=season.id,
                season_name=season.name,
                bundesland=cup.bundesland,
                landkreis=cup.landkreis,
                winner_team_id=winner_team.id,
                winner_team_name=winner_team.name,
                winner_club_name=winner_club_name,
                winner_club_id=winner_club_id,
                winner_verein_id=winner_verein_id,
                finalist_team_id=finalist_team.id,
                finalist_team_name=finalist_team.name,
                finalist_club_name=finalist_club_name,
                finalist_club_id=finalist_club_id,
                finalist_verein_id=finalist_verein_id,
                final_winner_score=final_match.home_score if final_match.home_team_id == final_match.winner_team_id else final_match.away_score,
                final_finalist_score=final_match.away_score if final_match.home_team_id == final_match.winner_team_id else final_match.home_score,
                final_winner_set_points=final_match.home_set_points if final_match.home_team_id == final_match.winner_team_id else final_match.away_set_points,
                final_finalist_set_points=final_match.away_set_points if final_match.home_team_id == final_match.winner_team_id else final_match.home_set_points
            )

            print(f"    Created history entry: {cup.name} -> Winner: {winner_team.name}, Finalist: {finalist_team.name}")
            db.session.add(history_entry)

        # Commit all history entries
        print("Committing all cup history entries to database...")
        db.session.commit()
        print(f"Cup history saved successfully for {len(cups)} cups")

        # Verify the data was saved
        total_entries = CupHistory.query.filter_by(season_id=season.id).count()
        print(f"Verification: {total_entries} cup history entries saved for season {season.name}")

    except Exception as e:
        print(f"Error saving cup history: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with season transition without saving cup history...")
        # Don't let history saving errors break the season transition
        try:
            db.session.rollback()
        except:
            pass


def save_team_cup_history(season):
    """Save the cup participation history for all teams in all cups for this season."""
    try:
        from models import TeamCupHistory, Cup, CupMatch, Team, Club, db

        print("Saving team cup history for season:", season.name)

        # Check if TeamCupHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'team_cup_history' not in existing_tables:
            print("TeamCupHistory table does not exist yet. Creating it...")
            # Create the table
            db.create_all()
            print("TeamCupHistory table created successfully.")

        # Get all cups for this season
        cups = Cup.query.filter_by(season_id=season.id).all()
        print(f"Found {len(cups)} cups for season {season.name}")

        for cup in cups:
            print(f"Processing cup: {cup.name}")

            # Get all teams that participated in this cup
            # Find all teams that played at least one match in this cup
            participating_teams_query = db.session.query(CupMatch.home_team_id, CupMatch.away_team_id).filter_by(
                cup_id=cup.id,
                is_played=True
            ).distinct()

            participating_team_ids = set()
            for home_id, away_id in participating_teams_query:
                participating_team_ids.add(home_id)
                participating_team_ids.add(away_id)

            print(f"  Found {len(participating_team_ids)} participating teams")

            for team_id in participating_team_ids:
                team = Team.query.get(team_id)
                if not team:
                    print(f"    Team {team_id} not found, skipping...")
                    continue

                # Check if history entry already exists for this team and cup
                existing_entry = TeamCupHistory.query.filter_by(
                    team_id=team_id,
                    cup_name=cup.name,
                    season_id=season.id
                ).first()

                if existing_entry:
                    print(f"    History entry already exists for team {team.name} in cup {cup.name}, skipping...")
                    continue

                # Determine how far this team reached
                team_matches = CupMatch.query.filter(
                    CupMatch.cup_id == cup.id,
                    CupMatch.is_played == True,
                    db.or_(CupMatch.home_team_id == team_id, CupMatch.away_team_id == team_id)
                ).order_by(CupMatch.round_number.desc()).all()

                if not team_matches:
                    print(f"    No matches found for team {team.name} in cup {cup.name}, skipping...")
                    continue

                # Find the last round this team played in
                # Filter out None values to prevent comparison errors
                valid_round_numbers = [match.round_number for match in team_matches if match.round_number is not None]
                if not valid_round_numbers:
                    print(f"    No valid round numbers found for team {team.name} in cup {cup.name}, skipping...")
                    continue

                last_round = max(valid_round_numbers)
                last_match = next(match for match in team_matches if match.round_number == last_round)

                # Determine if team won or lost their last match
                team_won_last_match = last_match.winner_team_id == team_id

                # Determine reached round and status
                is_winner = False
                is_finalist = False
                reached_round_number = last_round

                if team_won_last_match and last_round == cup.total_rounds:
                    # Team won the final
                    is_winner = True
                    is_finalist = True
                    reached_round = "Sieger"
                elif not team_won_last_match and last_round == cup.total_rounds:
                    # Team lost the final
                    is_finalist = True
                    reached_round = "Finale"
                elif team_won_last_match:
                    # Team won their last match but didn't reach the final
                    # This means they reached the next round but didn't play it (cup ended)
                    reached_round_number = min(last_round + 1, cup.total_rounds)
                    reached_round = get_round_name(reached_round_number, cup.total_rounds)
                else:
                    # Team lost their last match
                    reached_round = get_round_name(last_round, cup.total_rounds)

                # Get elimination details (if not winner)
                eliminated_by_team_id = None
                eliminated_by_team_name = None
                eliminated_by_club_name = None
                eliminated_by_verein_id = None
                elimination_match_score_for = None
                elimination_match_score_against = None
                elimination_match_set_points_for = None
                elimination_match_set_points_against = None

                if not is_winner:
                    # Find the match where this team was eliminated
                    elimination_match = None
                    if not team_won_last_match:
                        elimination_match = last_match
                    else:
                        # Team won their last match but was eliminated in a later round they didn't play
                        # This shouldn't happen in normal circumstances, but handle it gracefully
                        pass

                    if elimination_match:
                        # Determine the opponent
                        if elimination_match.home_team_id == team_id:
                            eliminated_by_team_id = elimination_match.away_team_id
                            elimination_match_score_for = elimination_match.home_score
                            elimination_match_score_against = elimination_match.away_score
                            elimination_match_set_points_for = elimination_match.home_set_points
                            elimination_match_set_points_against = elimination_match.away_set_points
                        else:
                            eliminated_by_team_id = elimination_match.home_team_id
                            elimination_match_score_for = elimination_match.away_score
                            elimination_match_score_against = elimination_match.home_score
                            elimination_match_set_points_for = elimination_match.away_set_points
                            elimination_match_set_points_against = elimination_match.home_set_points

                        # Get opponent team details
                        eliminated_by_team = Team.query.get(eliminated_by_team_id)
                        if eliminated_by_team:
                            eliminated_by_team_name = eliminated_by_team.name
                            if eliminated_by_team.club:
                                eliminated_by_club_name = eliminated_by_team.club.name
                                eliminated_by_verein_id = eliminated_by_team.club.verein_id

                # Get team club information
                club_name = team.club.name if team.club else None
                club_id = team.club.id if team.club else None
                verein_id = team.club.verein_id if team.club else None

                # Create team cup history entry
                history_entry = TeamCupHistory(
                    team_id=team.id,
                    team_name=team.name,
                    club_name=club_name,
                    club_id=club_id,
                    verein_id=verein_id,
                    cup_name=cup.name,
                    cup_type=cup.cup_type,
                    season_id=season.id,
                    season_name=season.name,
                    bundesland=cup.bundesland,
                    landkreis=cup.landkreis,
                    reached_round=reached_round,
                    reached_round_number=reached_round_number,
                    total_rounds=cup.total_rounds,
                    eliminated_by_team_id=eliminated_by_team_id,
                    eliminated_by_team_name=eliminated_by_team_name,
                    eliminated_by_club_name=eliminated_by_club_name,
                    eliminated_by_verein_id=eliminated_by_verein_id,
                    elimination_match_score_for=elimination_match_score_for,
                    elimination_match_score_against=elimination_match_score_against,
                    elimination_match_set_points_for=elimination_match_set_points_for,
                    elimination_match_set_points_against=elimination_match_set_points_against,
                    is_winner=is_winner,
                    is_finalist=is_finalist
                )

                print(f"    Created history entry: {team.name} -> {reached_round} in {cup.name}")
                db.session.add(history_entry)

        # Commit all history entries
        print("Committing all team cup history entries to database...")
        db.session.commit()
        print(f"Team cup history saved successfully for season {season.name}")

        # Verify the data was saved
        total_entries = TeamCupHistory.query.filter_by(season_id=season.id).count()
        print(f"Verification: {total_entries} team cup history entries saved for season {season.name}")

    except Exception as e:
        print(f"Error saving team cup history: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with season transition without saving team cup history...")
        # Don't let history saving errors break the season transition
        try:
            db.session.rollback()
        except:
            pass


def save_team_achievements(season):
    """Save team achievements (league championships and cup wins) for this season."""
    try:
        from models import TeamAchievement, League, Cup, CupMatch, Team, Club, db

        print("Saving team achievements for season:", season.name)

        # Check if TeamAchievement table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'team_achievement' not in existing_tables:
            print("TeamAchievement table does not exist yet. Creating it...")
            # Create the table
            db.create_all()
            print("TeamAchievement table created successfully.")

        achievements_saved = 0

        # Save league champions
        leagues = League.query.filter_by(season_id=season.id).all()
        print(f"Found {len(leagues)} leagues for season {season.name}")

        for league in leagues:
            print(f"Processing league: {league.name} (Level {league.level})")

            # Get league standings using the correct function
            standings = calculate_standings(league)
            if not standings:
                print(f"    No standings found for league {league.name}")
                continue

            # Get the champion (first place)
            champion_standing = standings[0]
            champion_team = champion_standing['team']

            if not champion_team:
                print(f"    Champion team not found for league {league.name}")
                continue

            # Check if achievement already exists
            existing_achievement = TeamAchievement.query.filter_by(
                team_id=champion_team.id,
                season_id=season.id,
                achievement_type='LEAGUE_CHAMPION',
                achievement_name=league.name
            ).first()

            if existing_achievement:
                print(f"    Achievement already exists for {champion_team.name} in {league.name}")
                continue

            # Get club information
            club_name = champion_team.club.name if champion_team.club else 'Unbekannt'
            club_id = champion_team.club.id if champion_team.club else None
            verein_id = champion_team.club.id if champion_team.club else None

            # Create league championship achievement
            achievement = TeamAchievement(
                team_id=champion_team.id,
                team_name=champion_team.name,
                club_name=club_name,
                club_id=club_id,
                verein_id=verein_id,
                season_id=season.id,
                season_name=season.name,
                achievement_type='LEAGUE_CHAMPION',
                achievement_name=league.name,
                achievement_level=league.level
            )

            print(f"    Created league championship: {champion_team.name} -> {league.name}")
            db.session.add(achievement)
            achievements_saved += 1

        # Save cup winners
        cups = Cup.query.filter_by(season_id=season.id).all()
        print(f"Found {len(cups)} cups for season {season.name}")

        for cup in cups:
            print(f"Processing cup: {cup.name} ({cup.cup_type})")

            # Find the final match
            final_matches = CupMatch.query.filter(
                CupMatch.cup_id == cup.id,
                CupMatch.round_number == cup.total_rounds,
                CupMatch.is_played == True,
                CupMatch.winner_team_id.isnot(None)
            ).all()

            if not final_matches:
                print(f"    No completed final found for cup {cup.name}")
                continue

            final_match = final_matches[0]
            winner_team = Team.query.get(final_match.winner_team_id)

            if not winner_team:
                print(f"    Winner team not found for cup {cup.name}")
                continue

            # Get finalist team
            finalist_team_id = final_match.home_team_id if final_match.away_team_id == final_match.winner_team_id else final_match.away_team_id
            finalist_team = Team.query.get(finalist_team_id)

            # Check if achievement already exists
            existing_achievement = TeamAchievement.query.filter_by(
                team_id=winner_team.id,
                season_id=season.id,
                achievement_type='CUP_WINNER',
                achievement_name=cup.name
            ).first()

            if existing_achievement:
                print(f"    Achievement already exists for {winner_team.name} in {cup.name}")
                continue

            # Get club information
            club_name = winner_team.club.name if winner_team.club else 'Unbekannt'
            club_id = winner_team.club.id if winner_team.club else None
            verein_id = winner_team.club.id if winner_team.club else None

            # Get final opponent information
            final_opponent_team_name = finalist_team.name if finalist_team else 'Unbekannt'
            final_opponent_club_name = finalist_team.club.name if finalist_team and finalist_team.club else 'Unbekannt'

            # Get final scores
            final_score_for = final_match.home_score if final_match.home_team_id == final_match.winner_team_id else final_match.away_score
            final_score_against = final_match.away_score if final_match.home_team_id == final_match.winner_team_id else final_match.home_score

            # Create cup winner achievement
            achievement = TeamAchievement(
                team_id=winner_team.id,
                team_name=winner_team.name,
                club_name=club_name,
                club_id=club_id,
                verein_id=verein_id,
                season_id=season.id,
                season_name=season.name,
                achievement_type='CUP_WINNER',
                achievement_name=cup.name,
                bundesland=cup.bundesland,
                landkreis=cup.landkreis,
                cup_type=cup.cup_type,
                final_opponent_team_name=final_opponent_team_name,
                final_opponent_club_name=final_opponent_club_name,
                final_score_for=final_score_for,
                final_score_against=final_score_against
            )

            print(f"    Created cup winner achievement: {winner_team.name} -> {cup.name}")
            db.session.add(achievement)
            achievements_saved += 1

        # Commit all achievements
        print("Committing all team achievements to database...")
        db.session.commit()
        print(f"Team achievements saved successfully: {achievements_saved} achievements for season {season.name}")

        # Verify the data was saved
        total_entries = TeamAchievement.query.filter_by(season_id=season.id).count()
        print(f"Verification: {total_entries} team achievement entries saved for season {season.name}")

    except Exception as e:
        print(f"Error saving team achievements: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with season transition without saving team achievements...")
        # Don't let achievement saving errors break the season transition
        try:
            db.session.rollback()
        except:
            pass


def get_round_name(round_number, total_rounds):
    """Convert round number to human-readable round name."""
    if round_number == total_rounds:
        return "Finale"
    elif round_number == total_rounds - 1:
        return "Halbfinale"
    elif round_number == total_rounds - 2:
        return "Viertelfinale"
    elif round_number == total_rounds - 3:
        return "Achtelfinale"
    elif round_number == total_rounds - 4:
        return "1/16-Finale"
    elif round_number == total_rounds - 5:
        return "1/32-Finale"
    else:
        return f"{round_number}. Runde"


def calculate_standings(league):
    """Calculate the standings for a league."""
    # Use direct query instead of relationship to ensure we get updated team assignments
    teams = Team.query.filter_by(league_id=league.id).all()
    standings = []

    # Check if any matches have been played in this league
    played_matches_count = Match.query.filter_by(league_id=league.id, is_played=True).count()

    for team in teams:
        # Get all matches for this team
        home_matches = Match.query.filter_by(home_team_id=team.id, league_id=league.id).all()
        away_matches = Match.query.filter_by(away_team_id=team.id, league_id=league.id).all()

        table_points = 0
        wins = 0
        draws = 0
        losses = 0
        match_points_for = 0
        match_points_against = 0
        pins_for = 0
        pins_against = 0

        # Calculate points from home matches
        for match in home_matches:
            if match.is_played:
                pins_for += match.home_score
                pins_against += match.away_score
                match_points_for += match.home_match_points
                match_points_against += match.away_match_points

                if match.home_match_points > match.away_match_points:
                    table_points += 3  # Win = 3 points in table
                    wins += 1
                elif match.home_match_points == match.away_match_points:
                    table_points += 1  # Draw = 1 point in table
                    draws += 1
                else:
                    losses += 1

        # Calculate points from away matches
        for match in away_matches:
            if match.is_played:
                pins_for += match.away_score
                pins_against += match.home_score
                match_points_for += match.away_match_points
                match_points_against += match.home_match_points

                if match.away_match_points > match.home_match_points:
                    table_points += 3  # Win = 3 points in table
                    wins += 1
                elif match.away_match_points == match.home_match_points:
                    table_points += 1  # Draw = 1 point in table
                    draws += 1
                else:
                    losses += 1

        # Create the standings entry for this team
        standings.append({
            'team': team,
            'points': table_points,  # Renamed from table_points to match what's used in the frontend
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'match_points_for': match_points_for,
            'match_points_against': match_points_against,
            'match_point_difference': match_points_for - match_points_against,
            'goals_for': pins_for,  # Renamed from pins_for to match what's used in the frontend
            'goals_against': pins_against,  # Renamed from pins_against to match what's used in the frontend
            'goal_difference': pins_for - pins_against  # Renamed from pin_difference to match what's used in the frontend
        })

    # Sort standings by table points, then match point difference, then total pins
    # Only sort if matches have been played, otherwise keep the original team order
    if played_matches_count > 0:
        standings.sort(key=lambda x: (x['points'], x['match_point_difference'], x['goal_difference']), reverse=True)

    return standings

def select_target_league_id(available_league_ids, old_to_new_mapping, new_leagues, distribution_tracker=None):
    """
    Select the best target league ID from available options with load balancing.
    Distributes teams evenly across available leagues to prevent overcrowding.

    Args:
        available_league_ids: List of possible target league IDs
        old_to_new_mapping: Mapping from old to new league IDs
        new_leagues: List of new league objects
        distribution_tracker: Dict tracking team counts per league for load balancing
    """
    # Get valid target league IDs
    valid_target_ids = []
    for old_league_id in available_league_ids:
        new_league_id = old_to_new_mapping.get(old_league_id)
        if new_league_id and any(nl.id == new_league_id for nl in new_leagues):
            valid_target_ids.append(new_league_id)

    if not valid_target_ids:
        return None

    # If no distribution tracker provided, distribute evenly by sorting IDs
    if distribution_tracker is None:
        # Sort by ID to ensure consistent distribution instead of always picking first
        valid_target_ids.sort()
        # Use a simple round-robin approach based on the number of calls
        if not hasattr(select_target_league_id, '_call_counter'):
            select_target_league_id._call_counter = 0
        select_target_league_id._call_counter += 1
        return valid_target_ids[select_target_league_id._call_counter % len(valid_target_ids)]

    # Find the league with the fewest teams assigned so far
    min_teams = float('inf')
    best_league_id = None

    for league_id in valid_target_ids:
        current_count = distribution_tracker.get(league_id, 0)
        if current_count < min_teams:
            min_teams = current_count
            best_league_id = league_id
        elif current_count == min_teams and best_league_id is None:
            # If counts are equal, prefer the league with lower ID for consistency
            best_league_id = league_id

    # Update the tracker
    if best_league_id:
        distribution_tracker[best_league_id] = distribution_tracker.get(best_league_id, 0) + 1

    return best_league_id




def balance_promotion_relegation_spots(season_id, old_to_new_league_mapping=None):
    """
    Balance promotion and relegation spots between league levels.

    For each league level, check how many leagues from the next lower level
    feed into it, and adjust relegation spots accordingly.

    Args:
        season_id: The season ID to balance leagues for
        old_to_new_league_mapping: Optional mapping from old league IDs to new league IDs
                                  (used during season transitions)
    """
    print("Balancing promotion and relegation spots...")

    leagues = League.query.filter_by(season_id=season_id).order_by(League.level).all()
    leagues_by_level = {}

    # Group leagues by level
    for league in leagues:
        if league.level not in leagues_by_level:
            leagues_by_level[league.level] = []
        leagues_by_level[league.level].append(league)

    # Note: League references are now updated in create_new_season before this function is called
    # For first season (old_to_new_league_mapping is None), league references are already correct

    changes_made = 0

    # Process each league level
    for level in sorted(leagues_by_level.keys()):
        current_level_leagues = leagues_by_level[level]

        # For each league in this level, check how many lower-level leagues feed into it
        for league in current_level_leagues:
            # Get leagues that can be promoted to this league
            feeding_leagues = []

            # Check all leagues in lower levels (higher level numbers)
            for lower_level in range(level + 1, max(leagues_by_level.keys()) + 1):
                if lower_level in leagues_by_level:
                    for lower_league in leagues_by_level[lower_level]:
                        # Check if this lower league can promote to our current league
                        promotion_league_ids = lower_league.get_aufstieg_liga_ids()

                        if league.id in promotion_league_ids:
                            feeding_leagues.append(lower_league)

            # Calculate required relegation spots
            required_relegation_spots = len(feeding_leagues)

            # Only adjust if there are feeding leagues and the current spots don't match
            # Also check if the league has valid relegation targets before setting relegation spots
            if required_relegation_spots > 0:
                # Only set relegation spots if the league has valid relegation targets
                valid_relegation_targets = league.get_abstieg_liga_ids()
                if valid_relegation_targets and league.anzahl_absteiger != required_relegation_spots:
                    old_spots = league.anzahl_absteiger
                    league.anzahl_absteiger = required_relegation_spots
                    changes_made += 1
                    print(f"  {league.name} (Level {league.level}): Changed relegation spots from {old_spots} to {required_relegation_spots}")
                elif not valid_relegation_targets and league.anzahl_absteiger > 0:
                    # League has relegation spots but no valid targets - remove spots
                    old_spots = league.anzahl_absteiger
                    league.anzahl_absteiger = 0
                    changes_made += 1
                    print(f"  {league.name} (Level {league.level}): Removed relegation spots (no valid relegation targets) - was {old_spots}")

                # Also update promotion spots for the feeding leagues
                for feeding_league in feeding_leagues:
                    # Each feeding league should have at least 1 promotion spot to this level
                    if feeding_league.anzahl_aufsteiger < 1:
                        feeding_league.anzahl_aufsteiger = 1
                        print(f"    {feeding_league.name} (Level {feeding_league.level}): Set promotion spots to 1")
            elif required_relegation_spots == 0 and level < max(leagues_by_level.keys()):
                # This league has no feeding leagues but is not the bottom level
                # Only set relegation spots if the league has valid relegation targets
                if league.anzahl_absteiger == 0 and league.get_abstieg_liga_ids():
                    league.anzahl_absteiger = 1
                    changes_made += 1
                    print(f"  {league.name} (Level {league.level}): Set minimum 1 relegation spot (no feeding leagues, but has relegation targets)")
                elif league.anzahl_absteiger > 0 and not league.get_abstieg_liga_ids():
                    # League has relegation spots but no valid targets - remove spots
                    league.anzahl_absteiger = 0
                    changes_made += 1
                    print(f"  {league.name} (Level {league.level}): Removed relegation spots (no valid relegation targets)")

    # Special case: Check if top-level leagues have promotion spots when they shouldn't
    top_level = min(leagues_by_level.keys()) if leagues_by_level else 1
    if top_level in leagues_by_level:
        for league in leagues_by_level[top_level]:
            # Top level leagues should not have promotion spots
            if league.anzahl_aufsteiger > 0:
                league.anzahl_aufsteiger = 0
                changes_made += 1
                print(f"  {league.name} (Level {league.level}): Removed promotion spots (top level)")

    # Special case: Check if bottom-level leagues have relegation spots when they shouldn't
    bottom_level = max(leagues_by_level.keys()) if leagues_by_level else 10
    if bottom_level in leagues_by_level:
        for league in leagues_by_level[bottom_level]:
            # Bottom level leagues should not have relegation spots
            if league.anzahl_absteiger > 0:
                league.anzahl_absteiger = 0
                changes_made += 1
                print(f"  {league.name} (Level {league.level}): Removed relegation spots (bottom level)")

    if changes_made > 0:
        db.session.commit()
        print(f"Balanced promotion/relegation spots: {changes_made} changes made")
    else:
        print("No changes needed for promotion/relegation spots")


def create_new_season(old_season):
    """Create a new season based on the old one."""
    print("Creating new season...")

    # Reset the call counter for league selection to ensure fair distribution
    if hasattr(select_target_league_id, '_call_counter'):
        select_target_league_id._call_counter = 0

    # Keep the old season as current for now
    # We'll only change it after everything is set up
    new_season = Season(
        name=f"Season {int(old_season.name.split()[-1]) + 1}",
        start_date=old_season.end_date + timedelta(days=30),  # Start 30 days after previous season
        end_date=old_season.end_date + timedelta(days=30 + 365),  # End roughly a year later
        is_current=False  # Start as not current, will set to current at the end
    )

    db.session.add(new_season)
    db.session.commit()
    print(f"Created new season: {new_season.name} (ID: {new_season.id})")

    # Create leagues for the new season
    old_leagues = League.query.filter_by(season_id=old_season.id).order_by(League.level).all()
    new_leagues = []
    old_to_new_league_mapping = {}  # Maps old league ID to new league ID

    print(f"Creating {len(old_leagues)} leagues for the new season...")
    for old_league in old_leagues:
        new_league = League(
            name=old_league.name,
            level=old_league.level,
            season_id=new_season.id,
            bundesland=old_league.bundesland,
            landkreis=old_league.landkreis,
            altersklasse=old_league.altersklasse,
            anzahl_aufsteiger=old_league.anzahl_aufsteiger,
            anzahl_absteiger=old_league.anzahl_absteiger,
            aufstieg_liga_id=old_league.aufstieg_liga_id,
            abstieg_liga_id=old_league.abstieg_liga_id
        )
        new_leagues.append(new_league)
        db.session.add(new_league)

    db.session.commit()

    # Create mapping from old league IDs to new league IDs
    for i, old_league in enumerate(old_leagues):
        old_to_new_league_mapping[old_league.id] = new_leagues[i].id

    # CRITICAL: Update all aufstieg_liga_id and abstieg_liga_id references to use new league IDs
    # This must happen BEFORE team assignments to ensure correct promotion/relegation targets
    print("Updating league references to new season IDs...")
    for new_league in new_leagues:
        # Update promotion league IDs
        if new_league.aufstieg_liga_id:
            old_ids = new_league.get_aufstieg_liga_ids()
            new_ids = []
            for old_id in old_ids:
                if old_id in old_to_new_league_mapping:
                    new_ids.append(old_to_new_league_mapping[old_id])
                else:
                    print(f"WARNING: Could not map promotion league ID {old_id} for league {new_league.name}")
            if new_ids:
                new_league.aufstieg_liga_id = ';'.join(map(str, new_ids))
                print(f"Updated promotion targets for {new_league.name}: {new_ids}")
            else:
                # If no valid new IDs found, clear the field
                new_league.aufstieg_liga_id = None
                print(f"WARNING: No valid promotion targets found for {new_league.name}, cleared aufstieg_liga_id")

        # Update relegation league IDs
        if new_league.abstieg_liga_id:
            old_ids = new_league.get_abstieg_liga_ids()
            new_ids = []
            for old_id in old_ids:
                if old_id in old_to_new_league_mapping:
                    new_ids.append(old_to_new_league_mapping[old_id])
                else:
                    print(f"WARNING: Could not map relegation league ID {old_id} for league {new_league.name}")
            if new_ids:
                new_league.abstieg_liga_id = ';'.join(map(str, new_ids))
                print(f"Updated relegation targets for {new_league.name}: {new_ids}")
            else:
                # If no valid new IDs found, clear the field
                new_league.abstieg_liga_id = None
                print(f"WARNING: No valid relegation targets found for {new_league.name}, cleared abstieg_liga_id")

    db.session.commit()
    print("Successfully updated all league references to new season IDs")

    # Balance promotion and relegation spots for the new season
    balance_promotion_relegation_spots(new_season.id, old_to_new_league_mapping)

    print(f"Created {len(new_leagues)} leagues for the new season")
    print(f"League ID mapping: {old_to_new_league_mapping}")

    # Create a mapping of teams to their new leagues
    team_to_new_league = {}

    # Initialize distribution tracker for load balancing
    # Pre-populate with current team counts to ensure proper load balancing
    league_distribution_tracker = {}
    for new_league in new_leagues:
        # Count teams that will stay in this league (mapped from old leagues)
        corresponding_old_league_id = None
        for old_id, new_id in old_to_new_league_mapping.items():
            if new_id == new_league.id:
                corresponding_old_league_id = old_id
                break

        if corresponding_old_league_id:
            # Count teams in the old league that will stay (not promoted/relegated)
            old_league = next((ol for ol in old_leagues if ol.id == corresponding_old_league_id), None)
            if old_league:
                standings = calculate_standings(old_league)
                staying_teams = 0
                for j, standing in enumerate(standings):
                    # Count teams that are not promoted or relegated
                    is_promoted = j < old_league.anzahl_aufsteiger and old_league.level > 1
                    is_relegated = j >= len(standings) - old_league.anzahl_absteiger and old_league.level < max(ol.level for ol in old_leagues)
                    if not is_promoted and not is_relegated:
                        staying_teams += 1
                league_distribution_tracker[new_league.id] = staying_teams
            else:
                league_distribution_tracker[new_league.id] = 0
        else:
            league_distribution_tracker[new_league.id] = 0

    # First, get the final standings for each old league
    for i, old_league in enumerate(old_leagues):
        standings = calculate_standings(old_league)
        print(f"Old league {old_league.name} (Level {old_league.level}) has {len(standings)} teams")

        # Map each team to its corresponding new league and set status flags
        for j, standing in enumerate(standings):
            team = standing['team']
            target_new_league_id = None

            # Store previous season information
            team.previous_season_position = j + 1
            team.previous_season_league_level = old_league.level
            team.previous_season_status = None  # Reset status first

            # Apply promotions/relegations based on standings and set status
            if j < old_league.anzahl_aufsteiger and i > 0:  # Promotion (except for top league)
                # Get promotion league IDs from the old league
                promotion_league_ids = old_league.get_aufstieg_liga_ids()
                if promotion_league_ids:
                    target_new_league_id = select_target_league_id(
                        promotion_league_ids,
                        old_to_new_league_mapping,
                        new_leagues,
                        league_distribution_tracker
                    )
                    if target_new_league_id:
                        # Only mark as promoted if we actually found a target league
                        team.previous_season_status = 'promoted'
                        target_league_name = next((nl.name for nl in new_leagues if nl.id == target_new_league_id), "Unknown")
                        print(f"Team {team.name} promoted from {old_league.name} to {target_league_name}")
                    else:
                        # If no valid promotion league found, team stays in same league
                        target_new_league_id = old_to_new_league_mapping.get(old_league.id)
                        print(f"WARNING: Could not find valid promotion league for {team.name} from {old_league.name} - team stays in same league")
                else:
                    # If no promotion leagues defined, team stays in same league
                    target_new_league_id = old_to_new_league_mapping.get(old_league.id)
                    print(f"WARNING: No promotion leagues defined for {old_league.name} - team {team.name} stays in same league")
            elif j >= len(standings) - old_league.anzahl_absteiger and i < len(old_leagues) - 1:  # Relegation (except for bottom league)
                # Get relegation league IDs from the old league
                relegation_league_ids = old_league.get_abstieg_liga_ids()
                if relegation_league_ids:
                    target_new_league_id = select_target_league_id(
                        relegation_league_ids,
                        old_to_new_league_mapping,
                        new_leagues,
                        league_distribution_tracker
                    )
                    if target_new_league_id:
                        # Only mark as relegated if we actually found a target league
                        team.previous_season_status = 'relegated'
                        target_league_name = next((nl.name for nl in new_leagues if nl.id == target_new_league_id), "Unknown")
                        print(f"Team {team.name} relegated from {old_league.name} to {target_league_name}")
                    else:
                        # If no valid relegation league found, team stays in same league
                        target_new_league_id = old_to_new_league_mapping.get(old_league.id)
                        print(f"WARNING: Could not find valid relegation league for {team.name} from {old_league.name} - team stays in same league")
                else:
                    # If no relegation leagues defined, team stays in same league
                    target_new_league_id = old_to_new_league_mapping.get(old_league.id)
                    print(f"WARNING: No relegation leagues defined for {old_league.name} - team {team.name} stays in same league")
            elif j == 0 and old_league.level == 1:  # Champion of top league
                team.previous_season_status = 'champion'
                print(f"Team {team.name} is champion of level {old_league.level}")
                # Champions stay in the same league
                target_new_league_id = old_to_new_league_mapping.get(old_league.id)
                # Note: Distribution tracker already accounts for staying teams in initialization
            else:
                # Team stays in the same league
                target_new_league_id = old_to_new_league_mapping.get(old_league.id)
                # Note: Distribution tracker already accounts for staying teams in initialization

            # Map team to the target league
            if target_new_league_id:
                team_to_new_league[team.id] = target_new_league_id
                target_league_name = next((nl.name for nl in new_leagues if nl.id == target_new_league_id), "Unknown")
                print(f"Team {team.name} (ID: {team.id}) mapped to new league {target_league_name} (ID: {target_new_league_id})")
            else:
                print(f"WARNING: Could not determine target league for team {team.name}")

    # Print distribution summary
    print("\n=== LEAGUE DISTRIBUTION SUMMARY ===")
    for league_id, team_count in league_distribution_tracker.items():
        league_name = next((nl.name for nl in new_leagues if nl.id == league_id), f"League {league_id}")
        print(f"{league_name}: {team_count} teams")

    # Now update all teams to point to their new leagues
    teams = Team.query.all()
    updated_teams = 0
    unmapped_teams = []

    for team in teams:
        if team.id in team_to_new_league:
            old_league_id = team.league_id
            team.league_id = team_to_new_league[team.id]
            updated_teams += 1
            print(f"Team {team.name} moved from league {old_league_id} to league {team.league_id}")
        elif team.target_league_level is not None:
            # This is a new team added via cheat function - assign to target league
            target_league = None
            for new_league in new_leagues:
                if (new_league.level == team.target_league_level and
                    new_league.bundesland == team.target_league_bundesland and
                    new_league.landkreis == team.target_league_landkreis and
                    new_league.altersklasse == team.target_league_altersklasse):
                    target_league = new_league
                    break

            if target_league:
                team.league_id = target_league.id
                # Clear the temporary fields
                team.target_league_level = None
                team.target_league_bundesland = None
                team.target_league_landkreis = None
                team.target_league_altersklasse = None
                updated_teams += 1
                print(f"New team {team.name} assigned to target league {target_league.name}")
            else:
                unmapped_teams.append(team)
                print(f"WARNING: Could not find target league for new team {team.name}")
        else:
            # If for some reason we don't have a mapping, try to map to the same league
            old_league = League.query.get(team.league_id)
            if old_league:
                # Try to find the corresponding new league using the mapping
                new_league_id = old_to_new_league_mapping.get(old_league.id)
                if new_league_id:
                    team.league_id = new_league_id
                    updated_teams += 1
                    new_league_name = next((nl.name for nl in new_leagues if nl.id == new_league_id), "Unknown")
                    print(f"Team {team.name} mapped to corresponding league {new_league_name} using ID mapping")
                else:
                    # Fallback: find a league with the same level
                    for new_league in new_leagues:
                        if new_league.level == old_league.level:
                            team.league_id = new_league.id
                            updated_teams += 1
                            print(f"Team {team.name} mapped to same level league {new_league.name} (fallback)")
                            break
                    else:
                        unmapped_teams.append(team)
                        print(f"WARNING: Could not find new league for team {team.name} (old level: {old_league.level})")
            else:
                unmapped_teams.append(team)
                print(f"WARNING: Team {team.name} has invalid old league reference")

    db.session.commit()
    print(f"Updated {updated_teams} teams to point to their new leagues")

    if unmapped_teams:
        print(f"WARNING: {len(unmapped_teams)} teams could not be mapped to new leagues")

    # Refresh the session to ensure relationships are updated
    db.session.expire_all()

    # Generate fixtures for the new season
    total_fixtures_generated = 0
    for new_league in new_leagues:
        # Verify that the league has teams before generating fixtures
        league_teams = Team.query.filter_by(league_id=new_league.id).all()
        print(f"League {new_league.name} (Level {new_league.level}) has {len(league_teams)} teams")

        if len(league_teams) >= 2:
            generate_fixtures(new_league, new_season)
            fixtures_count = Match.query.filter_by(league_id=new_league.id, season_id=new_season.id).count()
            total_fixtures_generated += fixtures_count
            print(f"Generated {fixtures_count} fixtures for league {new_league.name}")
        else:
            print(f"WARNING: League {new_league.name} has only {len(league_teams)} teams, skipping fixture generation")

    # Create cups for the new season (before calendar creation)
    from app import auto_initialize_cups
    try:
        auto_initialize_cups(new_season.id)
        print("Auto-initialized cups for the new season")
    except Exception as e:
        print(f"Error initializing cups: {str(e)}")

    # Create season calendar after fixtures and cups are generated
    from season_calendar import create_season_calendar
    try:
        create_season_calendar(new_season.id)
        print(f"Created season calendar for {new_season.name}")
    except Exception as e:
        print(f"Error creating season calendar: {str(e)}")

    # Recalculate cup match days now that season calendar exists
    print("Recalculating cup match days...")
    try:
        from models import Cup, CupMatch
        cups = Cup.query.filter_by(season_id=new_season.id).all()

        for cup in cups:
            print(f"Recalculating match days for {cup.name}...")
            cup_matches = CupMatch.query.filter_by(cup_id=cup.id).all()

            for match in cup_matches:
                # Recalculate cup match day using the new logic
                new_cup_match_day = cup.calculate_cup_match_day(match.round_number, cup.total_rounds)
                if new_cup_match_day != match.cup_match_day:
                    print(f"  Updated match {match.id}: {match.cup_match_day} -> {new_cup_match_day}")
                    match.cup_match_day = new_cup_match_day

            db.session.commit()
            print(f"Recalculated match days for {cup.name}")

    except Exception as e:
        print(f"Error recalculating cup match days: {e}")

    # Ensure all matches have correct dates using unified logic (after calendar is created)
    try:
        from season_calendar import set_all_match_dates_unified
        set_all_match_dates_unified(new_season.id)
        print(f"Set unified match dates for all matches in new season {new_season.id}")
    except Exception as e:
        print(f"Error setting unified match dates for new season: {e}")

    print(f"Total fixtures generated: {total_fixtures_generated}")

    print("Generated fixtures for all leagues and cups in the new season")

    # Age all players by 1 year
    players = Player.query.all()
    for player in players:
        player.age += 1

    db.session.commit()
    print(f"Aged {len(players)} players by 1 year")

    # Note: Player redistribution is disabled during season transitions to avoid conflicts
    # with the game's dynamic player assignment system. The current system assigns players
    # to teams dynamically based on availability and strength for each match day.
    #
    # TODO: Future improvement - integrate permanent team assignments with match assignments
    # so that players can only play for teams they are permanently assigned to.

    # Now that everything is set up, make the new season current
    old_season.is_current = False
    new_season.is_current = True
    db.session.commit()
    print(f"Set {new_season.name} as the current season")

    print(f"Created new season: {new_season.name} (ID: {new_season.id})")
    return new_season


def get_league_matches_for_date(season_id, match_date):
    """
    Holt alle Ligaspiele für ein bestimmtes Datum.
    Verwendet die gleiche Logik wie optimized_match_queries, aber filtert nach Datum.
    """
    from sqlalchemy import func
    from sqlalchemy.orm import aliased

    # Konvertiere match_date zu einem Datum falls es ein datetime ist
    if hasattr(match_date, 'date'):
        target_date = match_date.date()
    else:
        target_date = match_date

    # Erstelle Alias für away_team
    away_team = aliased(Team)

    # Query für Ligaspiele an diesem Datum
    matches_query = db.session.query(
        Match.id.label('match_id'),
        Match.home_team_id,
        Match.away_team_id,
        Match.match_day,
        Match.league_id,
        Team.name.label('home_team_name'),
        Team.club_id.label('home_club_id'),
        away_team.name.label('away_team_name'),
        away_team.club_id.label('away_club_id'),
        League.name.label('league_name')
    ).join(
        Team, Match.home_team_id == Team.id
    ).join(
        away_team, Match.away_team_id == away_team.id
    ).join(
        League, Match.league_id == League.id
    ).filter(
        Match.season_id == season_id,
        Match.is_played == False,
        func.date(Match.match_date) == target_date
    )

    matches_data = matches_query.all()

    return matches_data


def get_cup_matches_for_date(season_id, match_date):
    """
    Holt alle Pokalspiele für ein bestimmtes Datum.
    Verwendet die gleiche Logik wie get_cup_matches_for_match_day, aber filtert nach Datum.
    """
    from sqlalchemy.orm import aliased
    from sqlalchemy import func
    from models import CupMatch, Cup

    # Konvertiere match_date zu einem Datum falls es ein datetime ist
    if hasattr(match_date, 'date'):
        target_date = match_date.date()
    else:
        target_date = match_date

    # Erstelle Alias für away_team
    away_team = aliased(Team)

    # Query für Pokalspiele an diesem Datum
    cup_matches_query = db.session.query(
        CupMatch.id.label('cup_match_id'),
        CupMatch.home_team_id,
        CupMatch.away_team_id,
        CupMatch.cup_match_day,
        CupMatch.round_name,
        CupMatch.round_number,
        Team.name.label('home_team_name'),
        Team.club_id.label('home_club_id'),
        away_team.name.label('away_team_name'),
        away_team.club_id.label('away_club_id'),
        Cup.name.label('cup_name')
    ).join(
        Team, CupMatch.home_team_id == Team.id
    ).outerjoin(
        away_team, CupMatch.away_team_id == away_team.id
    ).join(
        Cup, CupMatch.cup_id == Cup.id
    ).filter(
        Cup.season_id == season_id,
        CupMatch.is_played == False,
        func.date(CupMatch.match_date) == target_date
    )

    cup_matches_data = []
    for cup_match_row in cup_matches_query.all():
        # Erstelle ein Dictionary das kompatibel mit der bestehenden Simulation ist
        cup_match_data = {
            'match_id': cup_match_row.cup_match_id,  # Verwende match_id für Kompatibilität
            'cup_match_id': cup_match_row.cup_match_id,
            'home_team_id': cup_match_row.home_team_id,
            'away_team_id': cup_match_row.away_team_id,
            'cup_match_day': cup_match_row.cup_match_day,
            'round_name': cup_match_row.round_name,
            'round_number': cup_match_row.round_number,
            'home_team_name': cup_match_row.home_team_name,
            'home_club_id': cup_match_row.home_club_id,
            'away_team_name': cup_match_row.away_team_name if cup_match_row.away_team_name else 'Freilos',
            'away_club_id': cup_match_row.away_club_id,
            'cup_name': cup_match_row.cup_name,
            'is_cup_match': True  # Wichtig: Markiere als Cup-Match für korrekte Verarbeitung
        }
        cup_matches_data.append(cup_match_data)

    return cup_matches_data
