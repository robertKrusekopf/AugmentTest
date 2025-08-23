#!/usr/bin/env python3
"""
Test script to verify that manual lineups are properly used during match simulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, UserLineup, LineupPosition, Match, Team, Player, Season
from club_player_assignment import get_manual_lineup_for_team, batch_assign_players_to_teams
from app import app

def test_manual_lineup_functionality():
    """Test that manual lineups are retrieved and used correctly."""
    
    with app.app_context():
        print("=== Testing Manual Lineup Functionality ===")
        
        # Check if there are any existing manual lineups
        existing_lineups = UserLineup.query.all()
        print(f"Found {len(existing_lineups)} existing manual lineups in database")
        
        if existing_lineups:
            for lineup in existing_lineups[:3]:  # Show first 3
                print(f"  - Lineup ID {lineup.id}: Match {lineup.match_id}, Team {lineup.team_id}, Home: {lineup.is_home_team}")
                positions = LineupPosition.query.filter_by(lineup_id=lineup.id).all()
                print(f"    Positions: {len(positions)}")
                for pos in positions:
                    player = Player.query.get(pos.player_id)
                    print(f"      Position {pos.position_number}: {player.name if player else 'Unknown'}")
        
        # Test the get_manual_lineup_for_team function
        if existing_lineups:
            test_lineup = existing_lineups[0]
            print(f"\n=== Testing get_manual_lineup_for_team function ===")
            print(f"Testing with Match {test_lineup.match_id}, Team {test_lineup.team_id}, Home: {test_lineup.is_home_team}")
            
            manual_players = get_manual_lineup_for_team(
                test_lineup.match_id, 
                test_lineup.team_id, 
                test_lineup.is_home_team
            )
            
            if manual_players:
                print(f"Successfully retrieved manual lineup with {len(manual_players)} players:")
                for i, player in enumerate(manual_players, 1):
                    print(f"  Position {i}: {player['name']} (ID: {player['id']})")
            else:
                print("ERROR: Failed to retrieve manual lineup")
        
        # Find an upcoming match to test with
        print(f"\n=== Finding upcoming matches ===")
        upcoming_matches = Match.query.filter_by(is_played=False).limit(5).all()
        print(f"Found {len(upcoming_matches)} upcoming matches")
        
        if upcoming_matches:
            test_match = upcoming_matches[0]
            print(f"Test match: {test_match.id} - {test_match.home_team.name} vs {test_match.away_team.name}")
            
            # Check if this match has manual lineups
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
        
        # Test the batch_assign_players_to_teams function with manual lineups
        print(f"\n=== Testing batch_assign_players_to_teams with manual lineups ===")

        if existing_lineups:
            # Get a match that has manual lineups
            test_lineup = existing_lineups[0]
            test_match = Match.query.get(test_lineup.match_id)

            if test_match:
                print(f"Testing with match {test_match.id}: {test_match.home_team.name} vs {test_match.away_team.name}")

                # Get the clubs involved
                clubs_with_matches = {test_match.home_team.club_id, test_match.away_team.club_id}

                # Call batch_assign_players_to_teams
                from performance_optimizations import CacheManager
                cache_manager = CacheManager()

                result = batch_assign_players_to_teams(
                    clubs_with_matches,
                    test_match.match_day,
                    test_match.season_id,
                    cache_manager,
                    include_played_matches=True  # Include this match even if played
                )

                print(f"batch_assign_players_to_teams returned data for {len(result)} clubs")

                for club_id, teams in result.items():
                    print(f"  Club {club_id}: {len(teams)} teams")
                    for team_id, players in teams.items():
                        team = Team.query.get(team_id)
                        print(f"    Team {team_id} ({team.name if team else 'Unknown'}): {len(players)} players")

                        # Check if this matches our manual lineup
                        if team_id == test_lineup.team_id:
                            print(f"      This team has a manual lineup! Checking if it was used...")
                            manual_players = get_manual_lineup_for_team(
                                test_match.id, team_id, test_lineup.is_home_team
                            )

                            if manual_players and len(players) == len(manual_players):
                                # Check if the players match
                                manual_ids = [p['id'] for p in manual_players]
                                assigned_ids = [p['id'] for p in players]

                                if set(manual_ids) == set(assigned_ids):
                                    print(f"      ✓ SUCCESS: Manual lineup was used correctly!")
                                else:
                                    print(f"      ✗ ERROR: Different players assigned")
                                    print(f"        Manual: {manual_ids}")
                                    print(f"        Assigned: {assigned_ids}")
                            else:
                                print(f"      ✗ ERROR: Player count mismatch or no manual lineup")

                        # Show first few players
                        for i, player in enumerate(players[:3]):
                            print(f"      Player {i+1}: {player['name']} (ID: {player['id']})")
                        if len(players) > 3:
                            print(f"      ... and {len(players) - 3} more players")

        print("\n=== Test completed ===")

if __name__ == "__main__":
    test_manual_lineup_functionality()
