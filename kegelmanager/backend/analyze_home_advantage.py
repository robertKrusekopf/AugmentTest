#!/usr/bin/env python3
"""
Home Advantage Analysis Script for Bowling Simulation

This script analyzes the home advantage effect in the bowling simulation by:
1. Examining the current implementation
2. Running controlled simulations
3. Calculating statistical impact
4. Providing quantitative analysis
"""

import sys
import os
import numpy as np
from statistics import mean, stdev
import json

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_home_advantage_implementation():
    """Analyze how home advantage is implemented in the code."""
    print("=== HOME ADVANTAGE IMPLEMENTATION ANALYSIS ===\n")
    
    print("1. HOME ADVANTAGE MODIFIER:")
    print("   - Home teams receive a 2% bonus (factor = 1.02)")
    print("   - Applied to mean_score in simulate_player_performance()")
    print("   - Location: simulation.py line 822 and 1043")
    
    print("\n2. AWAY TEAM PENALTY:")
    print("   - Away teams have an additional 'auswaerts' attribute modifier")
    print("   - Formula: away_factor = 0.98 + (auswaerts / 2500)")
    print("   - Range: 0.98 to 1.02 (based on auswaerts attribute 1-99)")
    print("   - Default auswaerts = 70, so typical away_factor = 1.008")
    print("   - Location: simulation.py lines 1046-1048")
    
    print("\n3. COMBINED EFFECT:")
    print("   - Home team: 1.02 multiplier (no away penalty)")
    print("   - Away team: 1.0 multiplier + away_factor (0.98-1.02)")
    print("   - Typical away team: 1.0 * 1.008 = 1.008")
    print("   - Net home advantage: 1.02 / 1.008 ≈ 1.012 (1.2% advantage)")

def simulate_controlled_matches(num_simulations=1000):
    """Run controlled simulations to measure home advantage effect."""
    print(f"\n=== CONTROLLED SIMULATION ANALYSIS ({num_simulations} matches) ===\n")
    
    # Import required modules
    try:
        from simulation import simulate_player_performance
        from performance_optimizations import CacheManager
    except ImportError as e:
        print(f"Error importing simulation modules: {e}")
        return None
    
    # Create a mock cache manager
    cache_manager = CacheManager()
    
    # Create identical mock players for fair comparison
    mock_player = {
        'id': 'test_player',
        'name': 'Test Player',
        'strength': 70,
        'konstanz': 70,
        'drucksicherheit': 70,
        'volle': 70,
        'raeumer': 70,
        'ausdauer': 70,
        'sicherheit': 70,
        'auswaerts': 70,  # Default value
        'start': 70,
        'mitte': 70,
        'schluss': 70,
        'form_short_term': 0.0,
        'form_medium_term': 0.0,
        'form_long_term': 0.0
    }
    
    home_scores = []
    away_scores = []
    
    lane_quality = 1.0  # Neutral lane quality
    position = 2  # Middle position
    
    print("Running simulations...")
    
    for i in range(num_simulations):
        if i % 100 == 0:
            print(f"  Progress: {i}/{num_simulations}")
        
        # Simulate home player performance
        home_result = simulate_player_performance(
            mock_player, position, lane_quality, 1.02, True, cache_manager
        )
        home_scores.append(home_result['total_score'])
        
        # Simulate away player performance  
        away_result = simulate_player_performance(
            mock_player, position, lane_quality, 1.0, False, cache_manager
        )
        away_scores.append(away_result['total_score'])
    
    # Calculate statistics
    home_mean = mean(home_scores)
    away_mean = mean(away_scores)
    home_std = stdev(home_scores)
    away_std = stdev(away_scores)
    
    score_difference = home_mean - away_mean
    percentage_advantage = (score_difference / away_mean) * 100
    
    print(f"\nRESULTS:")
    print(f"  Home team average score: {home_mean:.1f} ± {home_std:.1f}")
    print(f"  Away team average score: {away_mean:.1f} ± {away_std:.1f}")
    print(f"  Score difference: {score_difference:.1f} pins")
    print(f"  Percentage advantage: {percentage_advantage:.2f}%")
    
    # Calculate win probability
    home_wins = sum(1 for h, a in zip(home_scores, away_scores) if h > a)
    away_wins = sum(1 for h, a in zip(home_scores, away_scores) if h < a)
    draws = num_simulations - home_wins - away_wins
    
    home_win_rate = (home_wins / num_simulations) * 100
    away_win_rate = (away_wins / num_simulations) * 100
    draw_rate = (draws / num_simulations) * 100
    
    print(f"\nWIN RATES:")
    print(f"  Home wins: {home_wins} ({home_win_rate:.1f}%)")
    print(f"  Away wins: {away_wins} ({away_win_rate:.1f}%)")
    print(f"  Draws: {draws} ({draw_rate:.1f}%)")
    
    return {
        'home_mean': home_mean,
        'away_mean': away_mean,
        'score_difference': score_difference,
        'percentage_advantage': percentage_advantage,
        'home_win_rate': home_win_rate,
        'away_win_rate': away_win_rate,
        'draw_rate': draw_rate
    }

def analyze_auswaerts_attribute_impact():
    """Analyze how different auswaerts values affect away performance."""
    print("\n=== AUSWAERTS ATTRIBUTE IMPACT ANALYSIS ===\n")
    
    print("Away factor formula: 0.98 + (auswaerts / 2500)")
    print("Auswaerts range: 1-99")
    print()
    
    auswaerts_values = [1, 25, 50, 70, 75, 90, 99]
    
    print("Auswaerts | Away Factor | Performance vs Neutral")
    print("----------|-------------|----------------------")
    
    for auswaerts in auswaerts_values:
        away_factor = 0.98 + (auswaerts / 2500)
        performance_vs_neutral = (away_factor - 1.0) * 100
        print(f"    {auswaerts:2d}    |    {away_factor:.4f}   |      {performance_vs_neutral:+.2f}%")
    
    print(f"\nTypical player (auswaerts=70): {0.98 + (70/2500):.4f} = +0.8% vs neutral")
    print(f"Best away player (auswaerts=99): {0.98 + (99/2500):.4f} = +1.96% vs neutral")
    print(f"Worst away player (auswaerts=1): {0.98 + (1/2500):.4f} = -1.96% vs neutral")

def calculate_theoretical_advantage():
    """Calculate theoretical home advantage based on formulas."""
    print("\n=== THEORETICAL HOME ADVANTAGE CALCULATION ===\n")
    
    # Typical values
    home_multiplier = 1.02
    typical_auswaerts = 70
    away_factor = 0.98 + (typical_auswaerts / 2500)

    print(f"Home team multiplier: {home_multiplier}")
    print(f"Away team multiplier: {away_factor:.4f} (auswaerts={typical_auswaerts})")
    print(f"Net home advantage: {home_multiplier / away_factor:.4f}")
    print(f"Percentage advantage: {((home_multiplier / away_factor) - 1) * 100:.2f}%")
    
    # Range analysis
    print(f"\nHome advantage range:")
    min_auswaerts = 1
    max_auswaerts = 99
    min_away_factor = 0.98 + (min_auswaerts / 2500)
    max_away_factor = 0.98 + (max_auswaerts / 2500)
    
    max_advantage = home_multiplier / min_away_factor
    min_advantage = home_multiplier / max_away_factor
    
    print(f"  vs worst away players (auswaerts=1): {((max_advantage - 1) * 100):.2f}%")
    print(f"  vs best away players (auswaerts=99): {((min_advantage - 1) * 100):.2f}%")

def main():
    """Main analysis function."""
    print("BOWLING SIMULATION HOME ADVANTAGE ANALYSIS")
    print("=" * 50)
    
    # 1. Implementation analysis
    analyze_home_advantage_implementation()
    
    # 2. Theoretical calculations
    calculate_theoretical_advantage()
    
    # 3. Auswaerts attribute impact
    analyze_auswaerts_attribute_impact()
    
    # 4. Controlled simulations
    try:
        simulation_results = simulate_controlled_matches(1000)
        
        if simulation_results:
            print(f"\n=== SUMMARY ===")
            print(f"Theoretical home advantage: ~1.2%")
            print(f"Measured home advantage: {simulation_results['percentage_advantage']:.2f}%")
            print(f"Home win rate: {simulation_results['home_win_rate']:.1f}%")
            print(f"Expected win rate (no advantage): 50.0%")
            print(f"Home advantage effect: +{simulation_results['home_win_rate'] - 50:.1f} percentage points")
            
    except Exception as e:
        print(f"\nSimulation failed: {e}")
        print("This is expected if running outside the Flask application context.")

if __name__ == "__main__":
    main()
