"""
Performance optimizations for the bowling simulation.

This module contains optimized functions to improve the performance of match day simulations.
"""

from models import db, Player, Match, PlayerMatchPerformance
from sqlalchemy import text
import time


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
        print("Performance indexes created successfully")

    except Exception as e:
        db.session.rollback()
        print(f"Error creating indexes: {str(e)}")


def bulk_reset_player_flags():
    """Optimized bulk reset of player flags using raw SQL."""
    try:
        start_time = time.time()

        # Reset availability flags
        result1 = db.session.execute(
            text("UPDATE player SET is_available_current_matchday = 1")
        )

        # Reset match day flags only for players who have played
        result2 = db.session.execute(
            text("UPDATE player SET has_played_current_matchday = 0 WHERE has_played_current_matchday = 1")
        )

        db.session.commit()

        end_time = time.time()
        print(f"Bulk reset completed in {end_time - start_time:.3f}s - Availability: {result1.rowcount}, Match day: {result2.rowcount}")

    except Exception as e:
        db.session.rollback()
        print(f"Error in bulk reset: {str(e)}")
        raise


def optimized_player_availability(club_id, teams_playing):
    """
    Optimized player availability determination using raw SQL.

    Args:
        club_id: The ID of the club
        teams_playing: Number of teams from this club playing on this match day
    """
    import random

    try:
        start_time = time.time()

        # Get player count and IDs in one query
        result = db.session.execute(
            text("SELECT COUNT(*), GROUP_CONCAT(id) FROM player WHERE club_id = :club_id"),
            {"club_id": club_id}
        ).fetchone()

        total_players = result[0]
        player_ids_str = result[1]

        if total_players == 0:
            print(f"No players found for club ID {club_id}")
            return

        min_players_needed = teams_playing * 6

        # If not enough players, make all available
        if total_players <= min_players_needed:
            db.session.execute(
                text("UPDATE player SET is_available_current_matchday = 1 WHERE club_id = :club_id"),
                {"club_id": club_id}
            )
            print(f"Club ID {club_id}: All {total_players} players available (need {min_players_needed})")
            return

        # Parse player IDs
        player_ids = [int(pid) for pid in player_ids_str.split(',')]

        # Determine unavailable players (16.7% chance)
        unavailable_count = max(0, min(
            int(total_players * 0.167),
            total_players - min_players_needed
        ))

        if unavailable_count > 0:
            unavailable_ids = random.sample(player_ids, unavailable_count)

            # Set all as available first, then mark some as unavailable
            db.session.execute(
                text("UPDATE player SET is_available_current_matchday = 1 WHERE club_id = :club_id"),
                {"club_id": club_id}
            )

            if unavailable_ids:
                placeholders = ','.join(['?' for _ in unavailable_ids])
                db.session.execute(
                    text(f"UPDATE player SET is_available_current_matchday = 0 WHERE id IN ({placeholders})"),
                    unavailable_ids
                )
        else:
            # All players available
            db.session.execute(
                text("UPDATE player SET is_available_current_matchday = 1 WHERE club_id = :club_id"),
                {"club_id": club_id}
            )

        end_time = time.time()
        print(f"Player availability for club {club_id} set in {end_time - start_time:.3f}s")

    except Exception as e:
        print(f"Error in optimized player availability: {str(e)}")
        raise


def batch_create_performances(performances_data):
    """
    Batch create player performances using bulk insert.

    Args:
        performances_data: List of dictionaries with performance data
    """
    if not performances_data:
        return

    try:
        start_time = time.time()

        # Use bulk insert for better performance
        db.session.bulk_insert_mappings(PlayerMatchPerformance, performances_data)

        end_time = time.time()
        print(f"Batch created {len(performances_data)} performances in {end_time - start_time:.3f}s")

    except Exception as e:
        print(f"Error in batch create performances: {str(e)}")
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

        end_time = time.time()
        print(f"Loaded {len(result)} matches in {end_time - start_time:.3f}s")

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
        query = text("""
            SELECT
                id, strength, konstanz, drucksicherheit, volle, raeumer,
                is_available_current_matchday, has_played_current_matchday
            FROM player
            WHERE club_id = :club_id
            ORDER BY (strength * 0.5 + konstanz * 0.1 + drucksicherheit * 0.1 + volle * 0.15 + raeumer * 0.15) DESC
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
                'rating': row[1] * 0.5 + row[2] * 0.1 + row[3] * 0.1 + row[4] * 0.15 + row[5] * 0.15
            }

        end_time = time.time()
        print(f"Loaded stats for {len(player_stats)} players in {end_time - start_time:.3f}s")

        return player_stats

    except Exception as e:
        print(f"Error getting club player stats: {str(e)}")
        raise


def performance_monitor(func):
    """Decorator to monitor function performance."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} completed in {end_time - start_time:.3f}s")
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

    Args:
        clubs_with_matches: Set of club IDs that have matches
        teams_playing: Dictionary mapping club_id to number of teams playing
    """
    try:
        start_time = time.time()

        # Get all player counts for all clubs in one query
        from sqlalchemy import text
        club_player_counts = {}
        if clubs_with_matches:
            result = db.session.execute(
                text("""
                    SELECT club_id, COUNT(*) as player_count
                    FROM player
                    WHERE club_id IN :club_ids
                    GROUP BY club_id
                """),
                {"club_ids": tuple(clubs_with_matches)}
            ).fetchall()

            club_player_counts = {row.club_id: row.player_count for row in result}

        # Process each club
        import random
        all_availability_updates = []

        for club_id in clubs_with_matches:
            total_players = club_player_counts.get(club_id, 0)
            teams_count = teams_playing.get(club_id, 0)
            min_players_needed = teams_count * 6

            if total_players == 0:
                continue

            if total_players <= min_players_needed:
                # All players available
                all_availability_updates.append((club_id, True, []))
                continue

            # Get player IDs for this club
            player_ids = [row[0] for row in db.session.query(Player.id).filter_by(club_id=club_id).all()]

            # Determine unavailable players (16.7% chance)
            unavailable_player_ids = []
            for player_id in player_ids:
                if random.random() < 0.167:
                    unavailable_player_ids.append(player_id)

            # Ensure we have enough available players
            available_players = len(player_ids) - len(unavailable_player_ids)
            if available_players < min_players_needed:
                players_needed = min_players_needed - available_players
                if players_needed > 0 and unavailable_player_ids:
                    unavailable_player_ids = unavailable_player_ids[:-players_needed]

            all_availability_updates.append((club_id, False, unavailable_player_ids))

        # Execute all updates in batch
        for club_id, all_available, unavailable_ids in all_availability_updates:
            if all_available or not unavailable_ids:
                # Set all players as available
                db.session.execute(
                    db.update(Player)
                    .where(Player.club_id == club_id)
                    .values(is_available_current_matchday=True)
                )
            else:
                # First set all as available, then mark some as unavailable
                db.session.execute(
                    db.update(Player)
                    .where(Player.club_id == club_id)
                    .values(is_available_current_matchday=True)
                )

                db.session.execute(
                    db.update(Player)
                    .where(Player.id.in_(unavailable_ids))
                    .values(is_available_current_matchday=False)
                )

        # Single commit for all changes
        db.session.commit()

        end_time = time.time()
        print(f"Batch set player availability for {len(clubs_with_matches)} clubs in {end_time - start_time:.3f}s")

    except Exception as e:
        db.session.rollback()
        print(f"Error in batch player availability: {str(e)}")
        raise
