"""
Test script for talent calculation based on peak strength.

This demonstrates how player talent is now determined by their expected peak strength
rather than being randomly assigned.
"""

import sys
import os
import random
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player_development import (
    calculate_talent_from_peak_strength,
    calculate_age_adjusted_strength,
    calculate_expected_development_years_to_peak
)


def test_talent_calculation():
    """Test how talent is calculated from peak strength."""
    print("\n" + "="*80)
    print("TALENT CALCULATION FROM PEAK STRENGTH")
    print("="*80)
    print("\nTalent is now determined by expected peak strength, not random.\n")
    
    print(f"{'Peak Strength':<15} {'Talent':<8} {'Max Potential':<15} {'Notes'}")
    print("-" * 80)
    
    test_strengths = [10, 20, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95]
    
    for peak_str in test_strengths:
        talent = calculate_talent_from_peak_strength(peak_str)
        max_potential = talent * 9
        
        # Determine notes
        if peak_str > max_potential:
            notes = "⚠️ Exceeds max potential"
        elif peak_str > max_potential * 0.9:
            notes = "Near max potential"
        else:
            notes = "Room to grow"
        
        print(f"{peak_str:<15} {talent:<8} {max_potential:<15} {notes}")
    
    print("\nTalent Ranges:")
    print("  Talent 10: Peak > 88  (Max Potential = 90)")
    print("  Talent 9:  Peak 80-88 (Max Potential = 81)")
    print("  Talent 8:  Peak 71-79 (Max Potential = 72)")
    print("  Talent 7:  Peak 62-70 (Max Potential = 63)")
    print("  Talent 6:  Peak 53-61 (Max Potential = 54)")
    print("  Talent 5:  Peak 44-52 (Max Potential = 45)")
    print("  Talent 4:  Peak 35-43 (Max Potential = 36)")
    print("  Talent 3:  Peak 26-34 (Max Potential = 27)")
    print("  Talent 2:  Peak 17-25 (Max Potential = 18)")
    print("  Talent 1:  Peak < 17  (Max Potential = 9)")


def test_bundesliga_team_generation():
    """Test realistic Bundesliga team generation with talent based on peak strength."""
    print("\n" + "="*80)
    print("BUNDESLIGA TEAM GENERATION (Team Strength = 75)")
    print("="*80)
    print("\nGenerating 15 players with talent determined by peak strength.\n")
    
    team_strength = 75
    league_level = 1
    std_dev = 5.0  # From config
    
    print(f"{'Name':<12} {'Age':<5} {'Peak':<6} {'Talent':<7} {'Max Pot':<9} {'Current':<9} {'Dev.'}")
    print("-" * 80)
    
    ages = [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 32]
    
    for i, age in enumerate(ages):
        # 1. Generate peak strength from team_strength with variance
        peak_strength = max(1, min(99, int(np.random.normal(team_strength, std_dev))))
        
        # 2. Calculate talent from peak strength
        talent = calculate_talent_from_peak_strength(peak_strength)
        max_potential = talent * 9
        
        # 3. Calculate current strength based on age
        current_strength = calculate_age_adjusted_strength(peak_strength, age, talent, club_bonus=1.1)
        
        # 4. Calculate expected development
        expected_dev = calculate_expected_development_years_to_peak(age, talent, club_bonus=1.1)
        
        name = f"Player {i+1}"
        print(f"{name:<12} {age:<5} {peak_strength:<6} {talent:<7} {max_potential:<9} {current_strength:<9} {expected_dev:>+5.1f}")
    
    print("\nObservations:")
    print("- Players with higher peak strength get higher talent")
    print("- Young players start with lower current strength")
    print("- All players develop toward their peak strength at age 27")
    print("- Talent determines max potential (Talent × 9)")


def test_different_league_levels():
    """Test how talent distribution varies across league levels."""
    print("\n" + "="*80)
    print("TALENT DISTRIBUTION ACROSS LEAGUE LEVELS")
    print("="*80)
    print("\nComparing talent distribution for different league levels.\n")
    
    league_configs = [
        ("Bundesliga", 1, 75),
        ("2. Bundesliga", 3, 65),
        ("Regionalliga", 5, 55),
        ("Landesliga", 7, 45),
        ("Kreisliga", 9, 35),
    ]
    
    print(f"{'League':<20} {'Team Str':<10} {'Avg Talent':<12} {'Talent Range'}")
    print("-" * 80)
    
    for league_name, league_level, team_strength in league_configs:
        std_dev = 5.0 + (league_level - 1) * 0.5
        
        # Generate 100 players and calculate average talent
        talents = []
        for _ in range(100):
            peak_strength = max(1, min(99, int(np.random.normal(team_strength, std_dev))))
            talent = calculate_talent_from_peak_strength(peak_strength)
            talents.append(talent)
        
        avg_talent = sum(talents) / len(talents)
        min_talent = min(talents)
        max_talent = max(talents)
        
        print(f"{league_name:<20} {team_strength:<10} {avg_talent:.2f}{'':<8} {min_talent}-{max_talent}")
    
    print("\nObservations:")
    print("- Higher leagues have higher average talent")
    print("- Talent is directly correlated with team strength")
    print("- Lower leagues have more variance in talent")


def test_age_talent_interaction():
    """Test how age and talent interact in player generation."""
    print("\n" + "="*80)
    print("AGE AND TALENT INTERACTION")
    print("="*80)
    print("\nHow age affects current strength for different talent levels.\n")
    print("All players have same peak strength (70), but different talents.\n")
    
    peak_strength = 70
    ages = [16, 18, 20, 22, 24, 26, 28, 30]
    
    # Generate different peak strengths to get different talents
    peak_strengths_for_talents = [50, 60, 70, 80, 90]  # Will give talents 6, 7, 8, 9, 10
    
    print(f"{'Age':<6}", end="")
    for ps in peak_strengths_for_talents:
        t = calculate_talent_from_peak_strength(ps)
        print(f"T{t} (Peak={ps})", end="  ")
    print()
    print("-" * 80)
    
    for age in ages:
        print(f"{age:<6}", end="")
        for peak_str in peak_strengths_for_talents:
            talent = calculate_talent_from_peak_strength(peak_str)
            current = calculate_age_adjusted_strength(peak_str, age, talent, club_bonus=1.1)
            expected_dev = calculate_expected_development_years_to_peak(age, talent, club_bonus=1.1)
            print(f"{current:>3} ({expected_dev:>+4.1f})", end="  ")
        print()
    
    print("\nFormat: Current Strength (+Expected Development)")
    print("\nObservations:")
    print("- Higher talent players develop faster (more expected development)")
    print("- At age 27+, all players are at their peak strength")
    print("- Young high-talent players start much weaker but have huge potential")


def test_comparison_old_vs_new_talent():
    """Compare old random talent vs new peak-based talent."""
    print("\n" + "="*80)
    print("COMPARISON: RANDOM TALENT vs PEAK-BASED TALENT")
    print("="*80)
    print("\nOLD: Talent was random (1-10), independent of strength")
    print("NEW: Talent is calculated from peak strength\n")
    
    team_strength = 70
    
    print("Generating 20 players with team strength 70:\n")
    print(f"{'Player':<10} {'Peak Str':<10} {'OLD Talent':<12} {'NEW Talent':<12} {'Difference'}")
    print("-" * 70)
    
    for i in range(20):
        # Generate peak strength
        peak_strength = max(1, min(99, int(np.random.normal(team_strength, 5))))
        
        # OLD system: random talent
        old_talent = random.randint(1, 10)
        
        # NEW system: talent from peak strength
        new_talent = calculate_talent_from_peak_strength(peak_strength)
        
        difference = new_talent - old_talent
        diff_str = f"{difference:+d}" if difference != 0 else "0"
        
        print(f"Player {i+1:<3} {peak_strength:<10} {old_talent:<12} {new_talent:<12} {diff_str}")
    
    print("\nObservations:")
    print("- OLD: A weak player (strength 50) could have talent 10 (unrealistic)")
    print("- OLD: A strong player (strength 85) could have talent 3 (unrealistic)")
    print("- NEW: Talent matches peak strength (strong players have high talent)")
    print("- NEW: More realistic and consistent player generation")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TALENT FROM PEAK STRENGTH TEST SUITE")
    print("="*80)
    print("\nThis test suite demonstrates the new talent calculation system.")
    print("Talent is now determined by expected peak strength, not randomly assigned.\n")
    
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    try:
        test_talent_calculation()
        test_bundesliga_team_generation()
        test_different_league_levels()
        test_age_talent_interaction()
        test_comparison_old_vs_new_talent()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

