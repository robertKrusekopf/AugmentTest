"""
Performance optimizations for the bowling simulation.

This module contains optimized functions to improve the performance of match day simulations.
"""

from models import db, Player, Match, PlayerMatchPerformance
from sqlalchemy import text
import time


def determine_player_availability(club_id, teams_playing):
    """
    Wrapper function for single club availability determination.
    Uses the optimized batch function for consistency.

    Args:
        club_id: The ID of the club
        teams_playing: Number of teams from this club playing on this match day
    """
    # Use the batch function for consistency
    batch_set_player_availability({club_id}, {club_id: teams_playing})


def create_performance_indexes():
    """Create database indexes to improve query performance."""
    try:
        # Create composite indexes for frequently used query combinations
        indexes = [
            # Player queries for availability and club assignment
            "CREATE INDEX IF NOT EXISTS idx_player_club_availability ON player(club_id, is_available_current_matchday, has_played_current_matchday)",

            # Match queries for simulation
            "CREATE INDEX IF NOT EXISTS idx_match_league_season_played ON match(league_id, season_id, is_played, match_day)",

            # Performance queries
            "CREATE INDEX IF NOT EXISTS idx_performance_player_match ON player_match_performance(player_id, match_id)",
            "CREATE INDEX IF NOT EXISTS idx_performance_match_team ON player_match_performance(match_id, team_id, is_home_team)",
        ]

        for index_sql in indexes:
            db.session.execute(text(index_sql))

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Error creating indexes: {str(e)}")


def bulk_reset_player_flags(current_match_day=None, day_type=None):
    """
    Optimized bulk reset of player flags using raw SQL.

    Args:
        current_match_day: If provided, only reset flags for players who played on a different match day
        day_type: The type of day ('LEAGUE_DAY' or 'CUP_DAY') - affects reset logic
    """
    try:
        start_time = time.time()

        # Reset availability flags
        result1 = db.session.execute(
            text("UPDATE player SET is_available_current_matchday = 1")
        )

        # Reset match day flags - behavior depends on current_match_day parameter and day_type
        if current_match_day is not None:
            if day_type == 'CUP_DAY':
                # For cup days, reset has_played_current_matchday for ALL players
                # since cup and league matches are independent
                result2 = db.session.execute(
                    text("UPDATE player SET has_played_current_matchday = 0 WHERE has_played_current_matchday = 1")
                )
            else:
                # For league days, only reset flags for players who played on a different match day
                # This prevents players from playing for multiple teams in the same season
                result2 = db.session.execute(
                    text("UPDATE player SET has_played_current_matchday = 0 WHERE has_played_current_matchday = 1 AND (last_played_matchday IS NULL OR last_played_matchday != :match_day)"),
                    {"match_day": current_match_day}
                )
        else:
            # Reset all match day flags (used for season simulation)
            result2 = db.session.execute(
                text("UPDATE player SET has_played_current_matchday = 0 WHERE has_played_current_matchday = 1")
            )

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Error in bulk reset: {str(e)}")
        raise


# Removed duplicate function - use determine_player_availability() instead


def batch_create_performances(performances_data):
    """
    Batch create player performances for league matches using bulk insert.

    Args:
        performances_data: List of dictionaries with performance data
    """
    if not performances_data:
        return

    try:
        start_time = time.time()

        # Use bulk insert for better performance
        db.session.bulk_insert_mappings(PlayerMatchPerformance, performances_data)

    except Exception as e:
        print(f"Error in batch create league performances: {str(e)}")
        raise


def batch_create_cup_performances(performances_data):
    """
    Batch create player performances for cup matches using bulk insert.

    Args:
        performances_data: List of dictionaries with cup performance data
    """
    if not performances_data:
        return

    try:
        from models import PlayerCupMatchPerformance
        start_time = time.time()

        # Use bulk insert for better performance
        db.session.bulk_insert_mappings(PlayerCupMatchPerformance, performances_data)

    except Exception as e:
        print(f"Error in batch create cup performances: {str(e)}")
        raise


def optimized_match_queries(season_id, match_day):
    """
    Optimized queries to get matches for simulation.

    Args:
        season_id: The season ID
        match_day: The match day to simulate

    Returns:
        List of match data with preloaded team and club information
    """
    try:
        start_time = time.time()

        # Single query to get all match data with joins
        query = text("""
            SELECT
                m.id as match_id,
                m.league_id,
                m.home_team_id,
                m.away_team_id,
                ht.name as home_team_name,
                at.name as away_team_name,
                ht.club_id as home_club_id,
                at.club_id as away_club_id,
                l.name as league_name
            FROM match m
            JOIN team ht ON m.home_team_id = ht.id
            JOIN team at ON m.away_team_id = at.id
            JOIN league l ON m.league_id = l.id
            WHERE m.season_id = :season_id
                AND m.match_day = :match_day
                AND m.is_played = 0
            ORDER BY m.league_id, m.id
        """)

        result = db.session.execute(query, {
            "season_id": season_id,
            "match_day": match_day
        }).fetchall()

        return result

    except Exception as e:
        print(f"Error in optimized match queries: {str(e)}")
        raise


def get_club_player_stats(club_id):
    """
    Get optimized player statistics for a club.

    Args:
        club_id: The club ID

    Returns:
        Dictionary mapping player_id to player stats
    """
    try:
        start_time = time.time()

        # Single query to get all needed player data
        from simulation import PLAYER_RATING_SQL
        query = text(f"""
            SELECT
                id, strength, konstanz, drucksicherheit, volle, raeumer,
                is_available_current_matchday, has_played_current_matchday
            FROM player
            WHERE club_id = :club_id
            ORDER BY {PLAYER_RATING_SQL} DESC
        """)

        result = db.session.execute(query, {"club_id": club_id}).fetchall()

        # Convert to dictionary for fast lookup
        player_stats = {}
        for row in result:
            player_stats[row[0]] = {
                'id': row[0],
                'strength': row[1],
                'konstanz': row[2],
                'drucksicherheit': row[3],
                'volle': row[4],
                'raeumer': row[5],
                'is_available': row[6],
                'has_played': row[7],
                'rating': row[1] * 0.5 + row[2] * 0.1 + row[3] * 0.1 + row[4] * 0.15 + row[5] * 0.15  # Keep calculation for performance
            }

        return player_stats

    except Exception as e:
        print(f"Error getting club player stats: {str(e)}")
        raise


def performance_monitor(func):
    """Decorator to monitor function performance."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        return result
    return wrapper


class CacheManager:
    """Advanced caching system for simulation data."""

    def __init__(self):
        self.player_cache = {}
        self.team_cache = {}
        self.club_cache = {}
        self.form_cache = {}
        self.lane_quality_cache = {}

    def get_player_data(self, player_id):
        """Get cached player data or load from database."""
        if player_id not in self.player_cache:
            from models import Player
            player = Player.query.get(player_id)
            if player:
                self.player_cache[player_id] = {
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
                    'form_long_remaining_days': player.form_long_remaining_days,
                    'club_id': player.club_id
                }
        return self.player_cache.get(player_id)

    def get_team_data(self, team_id):
        """Get cached team data or load from database."""
        if team_id not in self.team_cache:
            from models import Team
            team = Team.query.get(team_id)
            if team:
                self.team_cache[team_id] = {
                    'id': team.id,
                    'name': team.name,
                    'club_id': team.club_id
                }
        return self.team_cache.get(team_id)

    def get_club_data(self, club_id):
        """Get cached club data or load from database."""
        if club_id not in self.club_cache:
            from models import Club
            club = Club.query.get(club_id)
            if club:
                self.club_cache[club_id] = {
                    'id': club.id,
                    'name': club.name,
                    'bahnqualitaet': getattr(club, 'bahnqualitaet', 100)
                }
        return self.club_cache.get(club_id)

    def get_lane_quality(self, club_id):
        """Get cached lane quality or calculate it."""
        if club_id not in self.lane_quality_cache:
            club_data = self.get_club_data(club_id)
            if club_data:
                # Convert lane quality to factor (100 = 1.0, 110 = 1.1, 90 = 0.9)
                self.lane_quality_cache[club_id] = club_data['bahnqualitaet'] / 100.0
            else:
                self.lane_quality_cache[club_id] = 1.0
        return self.lane_quality_cache[club_id]

    def clear_cache(self):
        """Clear all cached data."""
        self.player_cache.clear()
        self.team_cache.clear()
        self.club_cache.clear()
        self.form_cache.clear()
        self.lane_quality_cache.clear()


def batch_set_player_availability(clubs_with_matches, teams_playing):
    """
    Optimized batch setting of player availability for multiple clubs.
    Uses 0% to 30% unavailability rate per club (randomly determined), then randomly
    selects which players are unavailable. Allows Stroh players to be used when
    not enough players are available.

    Args:
        clubs_with_matches: Set of club IDs that have matches
        teams_playing: Dictionary mapping club_id to number of teams playing
    """
    try:
        start_time = time.time()
        import random



        # Get all player counts for all clubs in one query
        from sqlalchemy import text
        club_player_counts = {}
        if clubs_with_matches:
            # Convert set to list for proper parameter binding
            club_ids_list = list(clubs_with_matches)

            # Create placeholders for IN clause
            placeholders = ','.join([':param' + str(i) for i in range(len(club_ids_list))])

            # Create parameter dictionary
            params = {f'param{i}': club_id for i, club_id in enumerate(club_ids_list)}

            result = db.session.execute(
                text(f"""
                    SELECT club_id, COUNT(*) as player_count
                    FROM player
                    WHERE club_id IN ({placeholders})
                    GROUP BY club_id
                """),
                params
            ).fetchall()

            # Access columns by index or name - use _asdict() for named access
            club_player_counts = {}
            for row in result:
                row_dict = row._asdict() if hasattr(row, '_asdict') else dict(row)
                club_player_counts[row_dict['club_id']] = row_dict['player_count']

        # Process each club with random availability
        all_availability_updates = []

        for club_id in clubs_with_matches:
            total_players = club_player_counts.get(club_id, 0)
            teams_count = teams_playing.get(club_id, 0)
            min_players_needed = teams_count * 6

            if total_players == 0:
                continue

            # Get player IDs for this club
            player_ids = [row[0] for row in db.session.query(Player.id).filter_by(club_id=club_id).all()]

            # Determine unavailable players - new logic: 0% to 30% of players unavailable
            # First determine what percentage of players will be unavailable (0% to 30%)
            unavailability_percentage = random.uniform(0.0, 0.30)  # 0% to 30%

            # Calculate how many players should be unavailable
            num_unavailable = int(total_players * unavailability_percentage)

            # Add debugging information to track availability patterns
            # Randomly select which players will be unavailable
            unavailable_player_ids = []
            if num_unavailable > 0:
                unavailable_player_ids = random.sample(player_ids, min(num_unavailable, len(player_ids)))

            # Log if Stroh players will be needed
            available_players = total_players - len(unavailable_player_ids)
            if available_players < min_players_needed:
                stroh_needed = min_players_needed - available_players
                print(f"Club ID {club_id}: Will need {stroh_needed} Stroh player(s) (have {available_players} available, need {min_players_needed})")

            all_availability_updates.append((club_id, False, unavailable_player_ids))



        # Execute all updates in batch
        for club_id, _, unavailable_ids in all_availability_updates:
            # First set all players as available
            db.session.execute(
                db.update(Player)
                .where(Player.club_id == club_id)
                .values(is_available_current_matchday=True)
            )

            # Then mark some as unavailable if any
            if unavailable_ids:
                db.session.execute(
                    db.update(Player)
                    .where(Player.id.in_(unavailable_ids))
                    .values(is_available_current_matchday=False)
                )

        # Single commit for all changes
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Error in batch player availability: {str(e)}")
        raise
