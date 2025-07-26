#!/usr/bin/env python3
"""
Test script to simulate a new cup match and verify player performances are saved.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Season, Cup, CupMatch, Team, Player, PlayerCupMatchPerformance
from datetime import date, datetime
import simulation

def test_cup_simulation():
    """Test cup simulation with player performance tracking."""
    
    with app.app_context():
        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("No current season found")
            return
        
        print(f"Testing cup simulation for season: {current_season.name}")
        
        # Create a test cup match
        print("\n=== CREATING TEST CUP MATCH ===")
        
        # Get two teams for testing
        teams = Team.query.limit(2).all()
        if len(teams) < 2:
            print("Not enough teams found for testing")
            return
        
        home_team = teams[0]
        away_team = teams[1]
        
        print(f"Home team: {home_team.name} (Club: {home_team.club_id})")
        print(f"Away team: {away_team.name} (Club: {away_team.club_id})")
        
        # Get or create a test cup
        test_cup = Cup.query.filter_by(season_id=current_season.id, cup_type='DKBC').first()
        if not test_cup:
            print("No DKBC cup found")
            return
        
        # Create a test cup match
        test_match = CupMatch(
            cup_id=test_cup.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            round_name="Test Runde",
            round_number=1,
            cup_match_day=1,
            match_date=datetime.now().date(),
            is_played=False
        )
        
        db.session.add(test_match)
        db.session.commit()
        
        print(f"Created test cup match with ID: {test_match.id}")
        
        # Test the cup match simulation directly
        print("\n=== TESTING CUP MATCH SIMULATION ===")
        
        # Get players for both teams
        home_players = Player.query.filter_by(club_id=home_team.club_id, is_available_current_matchday=True).limit(6).all()
        away_players = Player.query.filter_by(club_id=away_team.club_id, is_available_current_matchday=True).limit(6).all()
        
        print(f"Home players available: {len(home_players)}")
        print(f"Away players available: {len(away_players)}")
        
        if len(home_players) < 6 or len(away_players) < 6:
            print("Not enough players available for simulation")
            # Clean up
            db.session.delete(test_match)
            db.session.commit()
            return
        
        # Create a cache manager
        from performance_optimizations import CacheManager
        cache = CacheManager()
        
        # Simulate the match
        match_result = simulation.simulate_match(
            home_team,
            away_team,
            home_players,
            away_players,
            cache
        )
        
        print(f"Match result: {match_result['home_score']} - {match_result['away_score']}")
        print(f"Match points: {match_result['home_match_points']} - {match_result['away_match_points']}")
        print(f"Performances generated: {len(match_result.get('performances', []))}")
        
        # Test the cup match data structure
        cup_match_data = {
            'match_id': test_match.id,
            'cup_match_id': test_match.id,
            'home_team_id': home_team.id,
            'away_team_id': away_team.id,
            'cup_match_day': 1,
            'round_name': "Test Runde",
            'round_number': 1,
            'home_team_name': home_team.name,
            'home_club_id': home_team.club_id,
            'away_team_name': away_team.name,
            'away_club_id': away_team.club_id,
            'cup_name': test_cup.name,
            'is_cup_match': True
        }
        
        # Update match result with cup match info
        match_result.update({
            'match_id': test_match.id,
            'home_team_id': home_team.id,
            'away_team_id': away_team.id,
            'home_team_name': home_team.name,
            'away_team_name': away_team.name,
            'league_name': f"{test_cup.name} - Test Runde",
            'match_day': 1,
            'is_cup_match': True
        })
        
        # Add match_id to all performance data
        for performance in match_result.get('performances', []):
            performance['match_id'] = test_match.id
        
        print("\n=== TESTING PERFORMANCE SAVING ===")
        
        # Test the batch commit function
        try:
            simulation.batch_commit_simulation_results(
                [],  # No league matches
                [cup_match_data],  # Our test cup match
                [match_result],  # Match results
                match_result.get('performances', []),  # Performances
                [],  # No player updates
                [],  # No lane records
                1,  # Match day
                datetime.now().date()  # Calendar date
            )
            
            print("✅ batch_commit_simulation_results completed successfully")
            
            # Check if performances were saved
            saved_performances = PlayerCupMatchPerformance.query.filter_by(cup_match_id=test_match.id).all()
            print(f"✅ Saved {len(saved_performances)} cup match performances")
            
            if saved_performances:
                for perf in saved_performances[:3]:  # Show first 3
                    print(f"  - {perf.player.name}: {perf.total_pins} pins (Team: {perf.team.name})")
            
            # Check if match was updated
            updated_match = CupMatch.query.get(test_match.id)
            print(f"✅ Match updated: is_played={updated_match.is_played}, score={updated_match.home_score}-{updated_match.away_score}")
            
        except Exception as e:
            print(f"❌ Error in batch_commit_simulation_results: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Clean up
        print("\n=== CLEANING UP ===")
        # Delete performances first (foreign key constraint)
        PlayerCupMatchPerformance.query.filter_by(cup_match_id=test_match.id).delete()
        db.session.delete(test_match)
        db.session.commit()
        print("✅ Test data cleaned up")

if __name__ == "__main__":
    test_cup_simulation()
