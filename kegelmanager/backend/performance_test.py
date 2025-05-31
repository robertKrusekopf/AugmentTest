"""
Performance test script to compare original vs optimized simulation.

This script can be used to benchmark the performance improvements.
"""

import time
import sys
import os
from flask import Flask

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Season, Match, Player
import simulation
from performance_optimizations import create_performance_indexes


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


def get_database_stats():
    """Get basic database statistics."""
    stats = {
        'players': Player.query.count(),
        'matches_total': Match.query.count(),
        'matches_played': Match.query.filter_by(is_played=True).count(),
        'matches_unplayed': Match.query.filter_by(is_played=False).count(),
    }
    return stats


def benchmark_original_simulation(season):
    """Benchmark the original simulation."""
    print("\n=== Benchmarking Original Simulation ===")
    
    start_time = time.time()
    
    # Reset some matches to unplayed for testing
    reset_matches_for_testing(season)
    
    # Run original simulation
    result = simulation.simulate_match_day(season)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Original simulation completed in {duration:.3f} seconds")
    print(f"Matches simulated: {result.get('matches_simulated', 0)}")
    
    return duration, result


def benchmark_optimized_simulation(season):
    """Benchmark the optimized simulation."""
    print("\n=== Benchmarking Optimized Simulation ===")
    
    try:
        from optimized_simulation import optimized_simulate_match_day
        
        start_time = time.time()
        
        # Reset some matches to unplayed for testing
        reset_matches_for_testing(season)
        
        # Create performance indexes
        create_performance_indexes()
        
        # Run optimized simulation
        result = optimized_simulate_match_day(season)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Optimized simulation completed in {duration:.3f} seconds")
        print(f"Matches simulated: {result.get('matches_simulated', 0)}")
        
        return duration, result
        
    except ImportError as e:
        print(f"Could not import optimized simulation: {e}")
        return None, None


def reset_matches_for_testing(season, num_matches=10):
    """Reset some matches to unplayed for testing purposes."""
    # Find some played matches to reset
    played_matches = Match.query.filter_by(
        season_id=season.id,
        is_played=True
    ).limit(num_matches).all()
    
    for match in played_matches:
        match.is_played = False
        match.home_score = None
        match.away_score = None
        match.home_match_points = 0
        match.away_match_points = 0
        match.match_date = None
    
    db.session.commit()
    print(f"Reset {len(played_matches)} matches for testing")


def benchmark_player_operations():
    """Benchmark player-related operations."""
    print("\n=== Benchmarking Player Operations ===")
    
    # Test bulk vs individual updates
    all_players = Player.query.all()
    player_count = len(all_players)
    
    print(f"Testing with {player_count} players")
    
    # Test individual updates (old method)
    start_time = time.time()
    for player in all_players[:100]:  # Test with first 100 players
        player.is_available_current_matchday = True
        db.session.add(player)
    db.session.commit()
    individual_time = time.time() - start_time
    
    # Test bulk update (new method)
    start_time = time.time()
    db.session.execute(
        db.update(Player)
        .where(Player.id.in_([p.id for p in all_players[:100]]))
        .values(is_available_current_matchday=False)
    )
    db.session.commit()
    bulk_time = time.time() - start_time
    
    print(f"Individual updates (100 players): {individual_time:.3f}s")
    print(f"Bulk update (100 players): {bulk_time:.3f}s")
    print(f"Speedup: {individual_time / bulk_time:.1f}x faster")


def run_performance_tests():
    """Run all performance tests."""
    app = setup_test_app()
    
    with app.app_context():
        print("=== Performance Test Suite ===")
        
        # Get database stats
        stats = get_database_stats()
        print(f"\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("No current season found!")
            return
        
        print(f"\nTesting with season: {current_season.name}")
        
        # Benchmark player operations
        benchmark_player_operations()
        
        # Benchmark simulations
        original_time, original_result = benchmark_original_simulation(current_season)
        optimized_time, optimized_result = benchmark_optimized_simulation(current_season)
        
        # Compare results
        if original_time and optimized_time:
            print(f"\n=== Performance Comparison ===")
            print(f"Original simulation: {original_time:.3f}s")
            print(f"Optimized simulation: {optimized_time:.3f}s")
            speedup = original_time / optimized_time
            print(f"Speedup: {speedup:.1f}x faster ({((speedup - 1) * 100):.1f}% improvement)")
            
            # Verify results are similar
            if (original_result and optimized_result and 
                original_result.get('matches_simulated') == optimized_result.get('matches_simulated')):
                print("✓ Results are consistent between implementations")
            else:
                print("⚠ Results differ between implementations")
        
        print("\n=== Test Complete ===")


if __name__ == "__main__":
    run_performance_tests()
