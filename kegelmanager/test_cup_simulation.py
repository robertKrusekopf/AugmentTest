#!/usr/bin/env python3
"""
Test script to verify cup match simulation with proper player assignment.
"""

import sys
import os
sys.path.append('backend')

# Import Flask app to get application context
from app import app
from models import db, Season, CupMatch, PlayerMatchPerformance
from simulation import simulate_match_day
from club_player_assignment import batch_assign_players_to_teams
import sqlite3

def test_cup_simulation():
    """Test cup simulation to check if players are properly assigned."""
    
    # Connect to database directly
    db_path = 'backend/instance/kegelmanager_default.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== Testing Cup Simulation ===")
    
    # Check current season
    cursor.execute("SELECT id, name, is_current FROM season WHERE is_current = 1")
    season_data = cursor.fetchone()
    if not season_data:
        print("No current season found")
        return
    
    season_id, season_name, is_current = season_data
    print(f"Current season: {season_name} (ID: {season_id})")
    
    # Find next match day with cup matches
    cursor.execute("""
        SELECT cup_match_day, COUNT(*) as match_count
        FROM cup_match 
        WHERE is_played = 0 
        GROUP BY cup_match_day 
        ORDER BY cup_match_day 
        LIMIT 1
    """)
    
    cup_match_day_data = cursor.fetchone()
    if not cup_match_day_data:
        print("No unplayed cup matches found")
        return
    
    match_day, match_count = cup_match_day_data
    print(f"Next cup match day: {match_day} with {match_count} matches")
    
    # Get cup matches for this match day
    cursor.execute("""
        SELECT cm.id, ht.name as home_team, at.name as away_team, 
               ht.club_id as home_club_id, at.club_id as away_club_id,
               c.name as cup_name
        FROM cup_match cm
        JOIN team ht ON cm.home_team_id = ht.id
        JOIN team at ON cm.away_team_id = at.id
        JOIN cup c ON cm.cup_id = c.id
        WHERE cm.cup_match_day = ? AND cm.is_played = 0
        LIMIT 3
    """, (match_day,))
    
    cup_matches = cursor.fetchall()
    print(f"\nSample cup matches for match day {match_day}:")
    for match in cup_matches:
        match_id, home_team, away_team, home_club_id, away_club_id, cup_name = match
        print(f"  {cup_name}: {home_team} vs {away_team} (Clubs: {home_club_id} vs {away_club_id})")
    
    # Test player assignment for these clubs
    clubs_with_matches = set()
    for match in cup_matches:
        clubs_with_matches.add(match[3])  # home_club_id
        clubs_with_matches.add(match[4])  # away_club_id
    
    print(f"\nClubs with cup matches: {clubs_with_matches}")
    
    # Test the batch_assign_players_to_teams function
    print("\n=== Testing Player Assignment ===")
    try:
        # Use Flask application context
        with app.app_context():
            # Mock cache manager
            class MockCacheManager:
                pass

            cache_manager = MockCacheManager()

            # Test player assignment
            club_team_players = batch_assign_players_to_teams(
                clubs_with_matches,
                match_day,
                season_id,
                cache_manager
            )

            print(f"Player assignment result: {len(club_team_players)} clubs processed")

            for club_id, teams in club_team_players.items():
                print(f"\nClub {club_id}:")
                for team_id, players in teams.items():
                    print(f"  Team {team_id}: {len(players)} players assigned")
                    if len(players) < 6:
                        print(f"    WARNING: Only {len(players)} players assigned (should be 6)")
                        # Show player IDs for debugging
                        player_ids = [p['id'] if isinstance(p, dict) else p.id for p in players]
                        print(f"    Player IDs: {player_ids}")

    except Exception as e:
        print(f"Error testing player assignment: {e}")
        import traceback
        traceback.print_exc()
    
    # Check available players for these clubs
    print("\n=== Checking Available Players ===")
    for club_id in clubs_with_matches:
        cursor.execute("""
            SELECT COUNT(*) as total_players,
                   SUM(CASE WHEN is_available_current_matchday = 1 THEN 1 ELSE 0 END) as available_players,
                   SUM(CASE WHEN has_played_current_matchday = 1 THEN 1 ELSE 0 END) as played_players
            FROM player 
            WHERE club_id = ?
        """, (club_id,))
        
        player_stats = cursor.fetchone()
        total, available, played = player_stats
        print(f"Club {club_id}: {total} total, {available} available, {played} already played")
    
    conn.close()

def test_actual_simulation():
    """Test actual cup simulation."""
    with app.app_context():
        season = Season.query.filter_by(is_current=True).first()
        if season:
            print(f"\n=== Running Actual Cup Simulation ===")
            print(f"Season: {season.name}")

            # Simulate multiple match days to reach cup matches
            for i in range(5):  # Simulate up to 5 match days
                result = simulate_match_day(season)
                print(f"Match day simulation {i+1}: {result['matches_simulated']} matches")

                # Check cup matches
                cup_matches = [r for r in result.get('results', []) if r.get('is_cup_match', False)]
                if cup_matches:
                    print(f"Cup matches simulated: {len(cup_matches)}")

                    # Show first few cup match results
                    for j, match in enumerate(cup_matches[:3]):
                        print(f"  {match['cup_name']}: {match['home_team_name']} {match['home_score']}:{match['away_score']} {match['away_team_name']}")

                        # Check if players were assigned by looking at performances
                        from models import PlayerMatchPerformance, CupMatch
                        cup_match = CupMatch.query.filter_by(
                            home_team_id=match.get('home_team_id'),
                            away_team_id=match.get('away_team_id'),
                            is_played=True
                        ).first()

                        if cup_match:
                            performances = PlayerMatchPerformance.query.filter_by(match_id=cup_match.id).all()
                            home_performances = [p for p in performances if p.is_home_team]
                            away_performances = [p for p in performances if not p.is_home_team]
                            print(f"    Players: {len(home_performances)} home, {len(away_performances)} away")
                    break  # Stop after finding cup matches

                if result['matches_simulated'] == 0:
                    print("No more matches to simulate")
                    break
        else:
            print("No current season found")

if __name__ == "__main__":
    test_cup_simulation()
    test_actual_simulation()
