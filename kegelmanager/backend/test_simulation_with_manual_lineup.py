#!/usr/bin/env python3
"""
Test script to verify that manual lineups work in actual match simulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, UserLineup, LineupPosition, Match, Team, Player, Season
from simulation import simulate_match
from club_player_assignment import batch_assign_players_to_teams
from performance_optimizations import CacheManager
from app import app

def test_simulation_with_manual_lineup():
    """Test that manual lineups are used in actual match simulation."""
    
    with app.app_context():
        print("=== Testing Match Simulation with Manual Lineups ===")
        
        # Find a match with manual lineups
        existing_lineups = UserLineup.query.all()
        if not existing_lineups:
            print("No manual lineups found in database")
            return
        
        test_lineup = existing_lineups[0]
        test_match = Match.query.get(test_lineup.match_id)
        
        if not test_match:
            print("Test match not found")
            return
        
        print(f"Testing match {test_match.id}: {test_match.home_team.name} vs {test_match.away_team.name}")
        
        # Get manual lineups for both teams
        home_lineup = UserLineup.query.filter_by(
            match_id=test_match.id,
            team_id=test_match.home_team_id,
            is_home_team=True
        ).first()
        
        away_lineup = UserLineup.query.filter_by(
            match_id=test_match.id,
            team_id=test_match.away_team_id,
            is_home_team=False
        ).first()
        
        print(f"Home team manual lineup: {'Yes' if home_lineup else 'No'}")
        print(f"Away team manual lineup: {'Yes' if away_lineup else 'No'}")
        
        # Get player assignments using our modified function
        clubs_with_matches = {test_match.home_team.club_id, test_match.away_team.club_id}
        cache_manager = CacheManager()
        
        club_team_players = batch_assign_players_to_teams(
            clubs_with_matches,
            test_match.match_day,
            test_match.season_id,
            cache_manager,
            include_played_matches=True
        )
        
        # Get the assigned players for both teams
        home_club_id = test_match.home_team.club_id
        away_club_id = test_match.away_team.club_id
        
        home_players = club_team_players.get(home_club_id, {}).get(test_match.home_team_id, [])
        away_players = club_team_players.get(away_club_id, {}).get(test_match.away_team_id, [])
        
        print(f"\nAssigned players:")
        print(f"Home team ({test_match.home_team.name}): {len(home_players)} players")
        for i, player in enumerate(home_players, 1):
            print(f"  {i}. {player['name']} (ID: {player['id']})")
        
        print(f"Away team ({test_match.away_team.name}): {len(away_players)} players")
        for i, player in enumerate(away_players, 1):
            print(f"  {i}. {player['name']} (ID: {player['id']})")
        
        # Verify that manual lineups were used
        if home_lineup:
            home_positions = LineupPosition.query.filter_by(lineup_id=home_lineup.id).all()
            manual_home_ids = [pos.player_id for pos in home_positions]
            assigned_home_ids = [p['id'] for p in home_players]
            
            if set(manual_home_ids) == set(assigned_home_ids):
                print(f"✓ Home team manual lineup used correctly!")
            else:
                print(f"✗ Home team manual lineup NOT used correctly!")
                print(f"  Manual: {manual_home_ids}")
                print(f"  Assigned: {assigned_home_ids}")
        
        if away_lineup:
            away_positions = LineupPosition.query.filter_by(lineup_id=away_lineup.id).all()
            manual_away_ids = [pos.player_id for pos in away_positions]
            assigned_away_ids = [p['id'] for p in away_players]
            
            if set(manual_away_ids) == set(assigned_away_ids):
                print(f"✓ Away team manual lineup used correctly!")
            else:
                print(f"✗ Away team manual lineup NOT used correctly!")
                print(f"  Manual: {manual_away_ids}")
                print(f"  Assigned: {assigned_away_ids}")
        
        # Now simulate the actual match to make sure it works end-to-end
        print(f"\n=== Simulating the match ===")
        
        # Convert player data to objects for simulation
        from simulation import SimplePlayer
        
        home_player_objects = []
        for player_data in home_players:
            player_obj = SimplePlayer(player_data)
            home_player_objects.append(player_obj)
        
        away_player_objects = []
        for player_data in away_players:
            player_obj = SimplePlayer(player_data)
            away_player_objects.append(player_obj)
        
        # Simulate the match
        try:
            match_result = simulate_match(
                test_match.home_team,
                test_match.away_team,
                home_player_objects,
                away_player_objects,
                cache_manager,
                match_id=test_match.id
            )
            
            print(f"Match simulation successful!")
            print(f"Result: {match_result['home_team']} {match_result['home_score']} - {match_result['away_score']} {match_result['away_team']}")
            print(f"Match Points: {match_result['home_match_points']} - {match_result['away_match_points']}")
            print(f"Winner: {match_result['winner']}")
            
            # Check that the performances include our manual lineup players
            performances = match_result.get('performances', [])
            print(f"Player performances recorded: {len(performances)}")
            
            if performances:
                print("Sample performances:")
                for perf in performances[:3]:
                    print(f"  {perf['player_name']}: {perf['total_pins']} pins")
            
        except Exception as e:
            print(f"Error during match simulation: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n=== Test completed ===")

if __name__ == "__main__":
    test_simulation_with_manual_lineup()
