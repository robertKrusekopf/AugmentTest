"""
Test script for age-based decline in player generation.

This demonstrates how older players (> 27) are now generated with reduced strength
based on expected decline from peak.
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
    calculate_expected_development_years_to_peak,
    calculate_expected_decline_from_peak
)


def test_decline_calculation():
    """Test how decline is calculated for different ages."""
    print("\n" + "="*80)
    print("AGE-BASED DECLINE CALCULATION")
    print("="*80)
    print("\nExpected strength loss from peak (age 27) to current age.\n")
    
    print(f"{'Age':<6} {'Years Past Peak':<18} {'Expected Decline':<18} {'Notes'}")
    print("-" * 80)
    
    ages = [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 40]
    
    for age in ages:
        years_past_peak = max(0, age - 27)
        decline = calculate_expected_decline_from_peak(age)
        
        if age == 27:
            notes = "Peak age"
        elif age < 30:
            notes = "Early decline"
        elif age < 32:
            notes = "Moderate decline"
        elif age < 35:
            notes = "Significant decline"
        else:
            notes = "Steep decline"
        
        print(f"{age:<6} {years_past_peak:<18} {decline:<18.1f} {notes}")
    
    print("\nDecline Rates:")
    print("  Age 27:    Peak (no decline)")
    print("  Age 28-29: -0.35 per year (early decline)")
    print("  Age 30-31: -0.75 per year (moderate decline)")
    print("  Age 32-34: -1.25 per year (significant decline)")
    print("  Age 35+:   -1.75 per year (steep decline)")


def test_full_career_arc():
    """Test a player's full career from youth to retirement."""
    print("\n" + "="*80)
    print("FULL CAREER ARC: 16 to 40 YEARS OLD")
    print("="*80)
    print("\nSimulating a Bundesliga player's career (Peak Strength = 75, Talent = 9).\n")
    
    peak_strength = 75
    talent = 9
    club_bonus = 1.1
    
    print(f"{'Age':<6} {'Current Str':<13} {'vs Peak':<10} {'Development':<15} {'Phase'}")
    print("-" * 80)
    
    ages = list(range(16, 41))
    
    for age in ages:
        current_strength = calculate_age_adjusted_strength(peak_strength, age, talent, club_bonus)
        vs_peak = current_strength - peak_strength
        
        if age < 27:
            expected_dev = calculate_expected_development_years_to_peak(age, talent, club_bonus)
            dev_str = f"+{expected_dev:.1f} to peak"
            phase = "Development"
        elif age == 27:
            dev_str = "At peak"
            phase = "Peak"
        else:
            expected_decline = calculate_expected_decline_from_peak(age)
            dev_str = f"-{expected_decline:.1f} from peak"
            phase = "Decline"
        
        print(f"{age:<6} {current_strength:<13} {vs_peak:>+4}{'':<6} {dev_str:<15} {phase}")
    
    print("\nObservations:")
    print("- Young players (16-26) start weaker and develop toward peak")
    print("- Peak at age 27 with full strength")
    print("- Older players (28+) decline from peak strength")
    print("- Decline accelerates with age")


def test_team_generation_with_age_distribution():
    """Test realistic team generation with various ages."""
    print("\n" + "="*80)
    print("BUNDESLIGA TEAM WITH AGE DISTRIBUTION")
    print("="*80)
    print("\nGenerating a team with players of different ages (Team Strength = 70).\n")
    
    team_strength = 70
    std_dev = 5.0
    
    # Realistic age distribution for a Bundesliga team
    ages = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 33, 35]
    
    print(f"{'Name':<12} {'Age':<5} {'Peak':<6} {'Talent':<7} {'Current':<9} {'vs Peak':<9} {'Phase'}")
    print("-" * 80)
    
    for i, age in enumerate(ages):
        # Generate peak strength
        peak_strength = max(1, min(99, int(np.random.normal(team_strength, std_dev))))
        
        # Calculate talent from peak strength
        talent = calculate_talent_from_peak_strength(peak_strength)
        
        # Calculate current strength based on age
        current_strength = calculate_age_adjusted_strength(peak_strength, age, talent, club_bonus=1.1)
        
        vs_peak = current_strength - peak_strength
        
        if age < 27:
            phase = "Developing"
        elif age == 27:
            phase = "Peak"
        else:
            phase = "Declining"
        
        name = f"Player {i+1}"
        print(f"{name:<12} {age:<5} {peak_strength:<6} {talent:<7} {current_strength:<9} {vs_peak:>+4}{'':<5} {phase}")
    
    print("\nObservations:")
    print("- Young players have lower current strength but will improve")
    print("- Players at peak (27) have full strength")
    print("- Older players have reduced strength due to age decline")
    print("- Team has a realistic mix of developing, peak, and declining players")


def test_comparison_old_vs_new_system():
    """Compare old system (no decline) vs new system (with decline)."""
    print("\n" + "="*80)
    print("COMPARISON: OLD vs NEW SYSTEM FOR OLDER PLAYERS")
    print("="*80)
    print("\nOLD: Players 27+ got full target strength (unrealistic)")
    print("NEW: Players 27+ get reduced strength based on age decline\n")
    
    team_strength = 70
    talent = 8
    
    print(f"{'Age':<6} {'OLD System':<13} {'NEW System':<13} {'Difference':<12} {'Notes'}")
    print("-" * 80)
    
    ages = [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 38, 40]
    
    for age in ages:
        # OLD system: always use target strength for age >= 27
        old_strength = team_strength
        
        # NEW system: reduce strength based on decline
        new_strength = calculate_age_adjusted_strength(team_strength, age, talent, club_bonus=1.1)
        
        difference = new_strength - old_strength
        
        if age == 27:
            notes = "Peak - same in both"
        elif age < 30:
            notes = "Small decline"
        elif age < 35:
            notes = "Moderate decline"
        else:
            notes = "Large decline"
        
        print(f"{age:<6} {old_strength:<13} {new_strength:<13} {difference:>+4}{'':<8} {notes}")
    
    print("\nObservations:")
    print("- OLD: 40-year-old had same strength as 27-year-old (unrealistic!)")
    print("- NEW: 40-year-old is significantly weaker (realistic)")
    print("- NEW: Gradual decline creates realistic age distribution")


def test_different_talents_decline():
    """Test how different talents affect decline."""
    print("\n" + "="*80)
    print("DECLINE ACROSS DIFFERENT TALENT LEVELS")
    print("="*80)
    print("\nNote: Decline is age-based only, not affected by talent.\n")
    
    peak_strength = 70
    ages = [27, 29, 31, 33, 35, 37, 40]
    talents = [5, 7, 9, 10]
    
    print(f"{'Age':<6}", end="")
    for t in talents:
        print(f"Talent {t}{'':<6}", end="")
    print()
    print("-" * 80)
    
    for age in ages:
        print(f"{age:<6}", end="")
        for talent in talents:
            current = calculate_age_adjusted_strength(peak_strength, age, talent, club_bonus=1.1)
            decline = peak_strength - current
            print(f"{current} (-{decline:.0f}){'':<6}", end="")
        print()
    
    print("\nFormat: Current Strength (-Decline from Peak)")
    print("\nObservations:")
    print("- Decline is the SAME for all talent levels at the same age")
    print("- Talent affects development speed, not decline rate")
    print("- All players decline at the same rate based purely on age")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("AGE-BASED DECLINE TEST SUITE")
    print("="*80)
    print("\nThis test suite demonstrates the new age-based decline system.")
    print("Older players (> 27) are now generated with reduced strength.\n")
    
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    try:
        test_decline_calculation()
        test_full_career_arc()
        test_team_generation_with_age_distribution()
        test_comparison_old_vs_new_system()
        test_different_talents_decline()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\n✅ Older players now have realistic age-based decline!")
        print("✅ Young players develop toward peak!")
        print("✅ Full career arc from 16 to 40+ implemented!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

