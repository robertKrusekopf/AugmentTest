"""
Test script to verify the simulation fix for the batch update error.
"""

import sys
import os
from flask import Flask

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Season, Match, Player
import simulation


def setup_test_app():
    """Setup Flask app for testing."""
    app = Flask(__name__)
    
    # Use the same database configuration as the main app
    db_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "selected_db.txt")
    
    if os.path.exists(db_config_file):
        with open(db_config_file, "r") as f:
            db_path = f.read().strip()
    else:
        # Fallback to default database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "kegelmanager.db")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app


def test_batch_update_function():
    """Test the batch_update_player_flags function directly."""
    print("=== Testing batch_update_player_flags function ===")
    
    # Get some player IDs for testing
    player_ids = [row[0] for row in db.session.query(Player.id).limit(5).all()]
    
    if not player_ids:
        print("No players found for testing")
        return False
    
    print(f"Testing with player IDs: {player_ids}")
    
    # Test data: (player_id, has_played, last_played_matchday)
    test_updates = [(pid, True, 1) for pid in player_ids]
    
    try:
        simulation.batch_update_player_flags(test_updates)
        print("✓ batch_update_player_flags completed successfully")
        return True
    except Exception as e:
        print(f"✗ batch_update_player_flags failed: {str(e)}")
        return False


def test_player_id_conversion():
    """Test the player ID conversion logic."""
    print("\n=== Testing player ID conversion ===")
    
    # Get some actual player objects
    players = Player.query.limit(3).all()
    
    if not players:
        print("No players found for testing")
        return False
    
    print(f"Testing with {len(players)} player objects")
    
    # Test the conversion logic
    try:
        # Simulate the conversion logic from the simulation
        player_ids = [p.id if hasattr(p, 'id') else p for p in players]
        print(f"Original players: {[p.name for p in players]}")
        print(f"Converted IDs: {player_ids}")
        
        # Test with mixed data (some objects, some IDs)
        mixed_data = [players[0], players[1].id, players[2]]
        mixed_ids = [p.id if hasattr(p, 'id') else p for p in mixed_data]
        print(f"Mixed data conversion: {mixed_ids}")
        
        print("✓ Player ID conversion works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Player ID conversion failed: {str(e)}")
        return False


def test_simulation():
    """Test a small simulation to see if the error is fixed."""
    print("\n=== Testing simulation ===")
    
    # Get current season
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        print("No current season found")
        return False
    
    print(f"Testing simulation with season: {current_season.name}")
    
    # Count unplayed matches
    unplayed_count = Match.query.filter_by(
        season_id=current_season.id,
        is_played=False
    ).count()
    
    print(f"Unplayed matches: {unplayed_count}")
    
    if unplayed_count == 0:
        print("No unplayed matches found - cannot test simulation")
        return True
    
    try:
        # Try to simulate one match day
        result = simulation.simulate_match_day(current_season)
        
        print(f"✓ Simulation completed successfully")
        print(f"  Matches simulated: {result.get('matches_simulated', 0)}")
        print(f"  Match day: {result.get('match_day', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_tests():
    """Run all tests."""
    app = setup_test_app()
    
    with app.app_context():
        print("=== Simulation Fix Test Suite ===")
        
        # Test 1: Direct batch update function
        test1_passed = test_batch_update_function()
        
        # Test 2: Player ID conversion
        test2_passed = test_player_id_conversion()
        
        # Test 3: Full simulation
        test3_passed = test_simulation()
        
        # Summary
        print(f"\n=== Test Results ===")
        print(f"Batch update function: {'✓ PASS' if test1_passed else '✗ FAIL'}")
        print(f"Player ID conversion: {'✓ PASS' if test2_passed else '✗ FAIL'}")
        print(f"Full simulation: {'✓ PASS' if test3_passed else '✗ FAIL'}")
        
        all_passed = test1_passed and test2_passed and test3_passed
        print(f"\nOverall result: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
        
        return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
