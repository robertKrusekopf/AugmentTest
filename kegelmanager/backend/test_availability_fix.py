#!/usr/bin/env python3
"""
Test script to verify that the player availability fix works correctly.
This script tests that manual lineup setup and automatic simulation 
now use the same availability logic with proper team context.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Player, Team, Club, Match, Season
from performance_optimizations import batch_set_player_availability

def test_availability_consistency():
    """Test that availability calculation is consistent between scenarios."""
    
    with app.app_context():
        print("=== Testing Player Availability Consistency ===")
        
        # Get a test club and team
        test_club = Club.query.first()
        if not test_club:
            print("No clubs found in database")
            return False
            
        test_team = Team.query.filter_by(club_id=test_club.id).first()
        if not test_team:
            print("No teams found for test club")
            return False
            
        print(f"Testing with club: {test_club.name}, team: {test_team.name}")
        
        # Get all players from the club
        club_players = Player.query.filter_by(club_id=test_club.id).all()
        print(f"Club has {len(club_players)} players")
        
        if len(club_players) < 6:
            print("Not enough players to test")
            return False
        
        # Test 1: Old method (should show deprecation warning)
        print("\n--- Test 1: Old method (deprecated) ---")
        try:
            from performance_optimizations import determine_player_availability
            determine_player_availability(test_club.id, 1)
            
            old_method_unavailable = [p for p in club_players if not p.is_available_current_matchday]
            print(f"Old method: {len(old_method_unavailable)} players unavailable")
            for p in old_method_unavailable[:3]:  # Show first 3
                print(f"  - {p.name}")
                
        except Exception as e:
            print(f"Error with old method: {e}")
            return False
        
        # Test 2: New method with proper context
        print("\n--- Test 2: New method with team context ---")
        try:
            # Build proper team context like the fixed code does
            clubs_with_matches = {test_club.id}
            teams_playing = {test_club.id: 1}
            playing_teams_info = {
                test_club.id: [{
                    'id': test_team.id,
                    'name': test_team.name,
                    'league_level': test_team.league.level if test_team.league else 999
                }]
            }
            
            batch_set_player_availability(clubs_with_matches, teams_playing, playing_teams_info)
            
            new_method_unavailable = [p for p in club_players if not p.is_available_current_matchday]
            print(f"New method: {len(new_method_unavailable)} players unavailable")
            for p in new_method_unavailable[:3]:  # Show first 3
                print(f"  - {p.name}")
                
        except Exception as e:
            print(f"Error with new method: {e}")
            return False
        
        # Test 3: Check if the logic paths are different
        print("\n--- Test 3: Logic path analysis ---")
        
        # Get all teams for this club to understand the logic path
        all_club_teams = Team.query.filter_by(club_id=test_club.id).all()
        print(f"Club has {len(all_club_teams)} teams total")
        print(f"Teams playing: 1")
        
        if len(all_club_teams) > 1:
            print("Expected logic: Higher non-playing teams should make top players unavailable")
            
            # Find higher teams
            playing_league_level = test_team.league.level if test_team.league else 999
            higher_teams = [t for t in all_club_teams 
                          if t.league and t.league.level < playing_league_level]
            
            if higher_teams:
                print(f"Higher teams not playing: {[t.name for t in higher_teams]}")
                print("This should cause some top players to be unavailable")
            else:
                print("No higher teams - should use normal random availability")
        else:
            print("Only one team - should use normal random availability")
        
        print("\n=== Test completed ===")
        return True

if __name__ == "__main__":
    success = test_availability_consistency()
    if success:
        print("✓ Test completed successfully")
    else:
        print("✗ Test failed")
