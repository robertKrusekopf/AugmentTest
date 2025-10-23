"""
Test script for age-adjusted player generation.

This demonstrates how young players are now generated with lower strength
that will develop to reach the team's target strength at peak years (age 27).
"""

import sys
import os
import random
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player_development import (
    calculate_expected_development_years_to_peak,
    calculate_age_adjusted_strength
)


def test_expected_development():
    """Test the expected development calculation for different ages and talents."""
    print("\n" + "="*80)
    print("EXPECTED DEVELOPMENT FROM CURRENT AGE TO PEAK (AGE 27)")
    print("="*80)
    print("\nThis shows how much a player is expected to develop from their current age")
    print("to peak years (age 27), based on their talent.\n")
    
    ages = [16, 18, 20, 22, 24, 26, 28, 30]
    talents = [3, 5, 7, 9, 10]
    
    print(f"{'Age':<6}", end="")
    for talent in talents:
        print(f"Talent {talent:<3}", end="  ")
    print()
    print("-" * 80)
    
    for age in ages:
        print(f"{age:<6}", end="")
        for talent in talents:
            expected_dev = calculate_expected_development_years_to_peak(age, talent, club_bonus=1.1)
            print(f"{expected_dev:>8.1f}    ", end="")
        print()
    
    print("\nNote: Negative values mean the player is past peak and will decline.")


def test_age_adjusted_generation():
    """Test how players are generated with age-adjusted strength."""
    print("\n" + "="*80)
    print("AGE-ADJUSTED PLAYER GENERATION")
    print("="*80)
    print("\nThis shows how a young player's strength is adjusted DOWN so they can")
    print("develop to reach the target strength at peak years.\n")
    
    target_strength = 70  # Team needs players with strength 70 at peak
    talents = [5, 7, 9]
    ages = [16, 18, 20, 22, 24, 26, 28, 30]
    
    print(f"Target Strength at Peak (Age 27): {target_strength}")
    print(f"\n{'Age':<6}", end="")
    for talent in talents:
        print(f"Talent {talent} (Max={talent*9})", end="  ")
    print()
    print("-" * 80)
    
    for age in ages:
        print(f"{age:<6}", end="")
        for talent in talents:
            current_strength = calculate_age_adjusted_strength(target_strength, age, talent, club_bonus=1.1)
            expected_dev = calculate_expected_development_years_to_peak(age, talent, club_bonus=1.1)
            print(f"{current_strength:>3} (+{expected_dev:>4.1f})      ", end="")
        print()
    
    print("\nFormat: Current Strength (+Expected Development to Peak)")
    print("Example: '52 (+18.0)' means player starts at 52 and develops +18 to reach 70")


def test_realistic_scenario():
    """Test a realistic scenario with a Bundesliga team."""
    print("\n" + "="*80)
    print("REALISTIC SCENARIO: BUNDESLIGA TEAM (Team Strength = 75)")
    print("="*80)
    print("\nGenerating 10 players of different ages for a Bundesliga team.\n")
    
    team_strength = 75
    league_level = 1
    
    print(f"{'Name':<15} {'Age':<5} {'Talent':<7} {'Current':<9} {'Expected':<10} {'Peak':<6} {'Max Pot.'}")
    print("-" * 80)
    
    ages = [17, 19, 21, 23, 25, 27, 29, 31, 33, 35]
    
    for i, age in enumerate(ages):
        # Generate random talent
        talent = random.randint(6, 10)  # Bundesliga players have higher talent
        
        # Simulate what the generation function would do
        # 1. Generate target strength from team_strength with some variance
        target_strength = max(1, min(99, int(np.random.normal(team_strength, 5))))
        
        # 2. Adjust for age
        current_strength = calculate_age_adjusted_strength(target_strength, age, talent, club_bonus=1.1)
        
        # 3. Calculate expected development
        expected_dev = calculate_expected_development_years_to_peak(age, talent, club_bonus=1.1)
        
        # 4. Calculate what their peak strength would be
        peak_strength = current_strength + expected_dev if age < 27 else current_strength
        
        # 5. Max potential
        max_potential = talent * 9
        
        name = f"Player {i+1}"
        print(f"{name:<15} {age:<5} {talent:<7} {current_strength:<9} {expected_dev:>+6.1f}{'':<4} {int(peak_strength):<6} {max_potential}")
    
    print("\nObservations:")
    print("- Young players (17-23) have LOWER current strength but HIGH expected development")
    print("- Peak players (24-27) have HIGH current strength and minimal development")
    print("- Older players (28+) have declining strength (negative development)")
    print("- All players should reach similar peak strength (~75) if they develop as expected")


def test_talent_impact_on_generation():
    """Test how talent affects the age-adjusted generation."""
    print("\n" + "="*80)
    print("TALENT IMPACT ON AGE-ADJUSTED GENERATION")
    print("="*80)
    print("\nComparing two 18-year-old players with different talents.\n")
    
    age = 18
    target_strength = 70
    
    print(f"Both players should reach strength {target_strength} at peak (age 27)")
    print(f"Both are currently {age} years old\n")
    
    print(f"{'Talent':<8} {'Max Pot.':<10} {'Current':<10} {'Expected Dev.':<15} {'Peak Strength'}")
    print("-" * 70)
    
    for talent in [3, 5, 7, 9, 10]:
        max_potential = talent * 9
        current_strength = calculate_age_adjusted_strength(target_strength, age, talent, club_bonus=1.1)
        expected_dev = calculate_expected_development_years_to_peak(age, talent, club_bonus=1.1)
        peak_strength = current_strength + expected_dev
        
        print(f"{talent:<8} {max_potential:<10} {current_strength:<10} {expected_dev:>+6.1f}{'':<9} {int(peak_strength)}")
    
    print("\nObservations:")
    print("- Low talent players (3-5) start HIGHER because they develop slower")
    print("- High talent players (9-10) start LOWER because they develop faster")
    print("- All should reach similar peak strength (~70) at age 27")
    print("- But high talent players can continue developing beyond 70 (up to their max potential)")


def test_comparison_old_vs_new():
    """Compare old system (no age adjustment) vs new system (age-adjusted)."""
    print("\n" + "="*80)
    print("COMPARISON: OLD SYSTEM vs NEW SYSTEM")
    print("="*80)
    print("\nOLD: All players generated with same strength regardless of age")
    print("NEW: Young players start weaker but develop to reach target strength\n")
    
    team_strength = 70
    talent = 7
    
    print(f"Team Strength: {team_strength}, Talent: {talent} (Max Potential: {talent*9})\n")
    print(f"{'Age':<6} {'OLD System':<12} {'NEW System':<12} {'Difference':<12} {'Expected Dev.'}")
    print("-" * 70)
    
    for age in [16, 18, 20, 22, 24, 26, 28, 30]:
        # OLD system: everyone gets team_strength
        old_strength = team_strength
        
        # NEW system: age-adjusted
        new_strength = calculate_age_adjusted_strength(team_strength, age, talent, club_bonus=1.1)
        
        # Expected development
        expected_dev = calculate_expected_development_years_to_peak(age, talent, club_bonus=1.1)
        
        difference = new_strength - old_strength
        
        print(f"{age:<6} {old_strength:<12} {new_strength:<12} {difference:>+5}{'':<7} {expected_dev:>+6.1f}")
    
    print("\nObservations:")
    print("- OLD system: 18-year-old has same strength (70) as 28-year-old")
    print("- NEW system: 18-year-old starts weaker (~52) but develops to reach 70 at peak")
    print("- This makes young players more realistic: weaker now, but with potential")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("AGE-ADJUSTED PLAYER GENERATION TEST SUITE")
    print("="*80)
    print("\nThis test suite demonstrates the new age-adjusted player generation system.")
    print("Young players are now generated with LOWER strength that develops to reach")
    print("the team's target strength at peak years (age 27).\n")
    
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    try:
        test_expected_development()
        test_age_adjusted_generation()
        test_realistic_scenario()
        test_talent_impact_on_generation()
        test_comparison_old_vs_new()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

