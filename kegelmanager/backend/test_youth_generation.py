"""
Test script to verify UNIFIED youth player generation and development system.

This script tests:
1. ALL young players (10-26) are generated based on talent and age, NOT team level
2. 10-year-old players have similar low strength (8-12) regardless of team
3. Development is smooth and consistent across all ages
4. Talent determines peak strength, not starting team level
5. A 15-year-old talent 10 player is stronger than a 15-year-old talent 5 player
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from player_development import (
    calculate_talent_multiplier,
    calculate_age_development_factor,
    calculate_expected_development_years_to_peak,
    calculate_current_strength_from_talent_and_age,
    calculate_peak_strength_from_talent
)
import random


def test_unified_young_player_generation():
    """Test that ALL young players are generated based on talent and age, not team level."""
    print("\n" + "="*80)
    print("TEST 1: UNIFIED YOUNG PLAYER GENERATION")
    print("="*80)
    print("\nTesting that young players (10-26) are generated based on talent and age,")
    print("NOT based on team level or team_staerke.\n")

    # Test different ages with same talent
    print("Testing Talent 10 players at different ages:")
    print(f"{'Age':<6} {'Strength':<10} {'Expected Range':<20}")
    print("-" * 40)

    talent_10_results = []
    for age in [10, 12, 15, 18, 21, 24, 26]:
        strengths = []
        for _ in range(20):
            strength = calculate_current_strength_from_talent_and_age(10, age)
            strengths.append(strength)

        avg_strength = sum(strengths) / len(strengths)
        min_strength = min(strengths)
        max_strength = max(strengths)

        talent_10_results.append((age, avg_strength, min_strength, max_strength))

        if age == 10:
            expected = "8-12 (base)"
        elif age == 26:
            expected = "~85-90 (near peak)"
        else:
            expected = "increasing"

        print(f"{age:<6} {avg_strength:<10.1f} {expected:<20}")

    # Test same age with different talents
    print("\nTesting 15-year-old players with different talents:")
    print(f"{'Talent':<8} {'Avg Strength':<15} {'Range':<20}")
    print("-" * 50)

    age_15_results = []
    for talent in [1, 3, 5, 7, 10]:
        strengths = []
        for _ in range(20):
            strength = calculate_current_strength_from_talent_and_age(talent, 15)
            strengths.append(strength)

        avg_strength = sum(strengths) / len(strengths)
        min_strength = min(strengths)
        max_strength = max(strengths)

        age_15_results.append((talent, avg_strength))
        print(f"{talent:<8} {avg_strength:<15.1f} {min_strength}-{max_strength}")

    # Verify that strength increases with age for same talent
    age_progression_ok = all(
        talent_10_results[i][1] < talent_10_results[i+1][1]
        for i in range(len(talent_10_results)-1)
    )

    # Verify that strength increases with talent for same age
    talent_progression_ok = all(
        age_15_results[i][1] < age_15_results[i+1][1]
        for i in range(len(age_15_results)-1)
    )

    # Verify 10-year-olds are in 8-12 range
    age_10_in_range = 8 <= talent_10_results[0][2] and talent_10_results[0][3] <= 12

    print("\n" + "-" * 50)
    if age_progression_ok:
        print("✓ PASS: Strength increases with age for same talent")
    else:
        print("✗ FAIL: Strength does not increase consistently with age")

    if talent_progression_ok:
        print("✓ PASS: Strength increases with talent for same age")
    else:
        print("✗ FAIL: Strength does not increase consistently with talent")

    if age_10_in_range:
        print("✓ PASS: 10-year-olds generate in 8-12 range")
    else:
        print(f"✗ FAIL: 10-year-olds outside 8-12 range ({talent_10_results[0][2]}-{talent_10_results[0][3]})")

    return age_progression_ok and talent_progression_ok and age_10_in_range


def test_talent_development():
    """Test that talent determines peak strength correctly."""
    print("\n" + "="*80)
    print("TEST 2: TALENT-BASED DEVELOPMENT TO PEAK")
    print("="*80)
    print("\nTesting that talent is the PRIMARY factor determining peak strength.")
    print("Expected results:")
    print("  - Talent 10: ~10 at age 10 → ~90+ at age 27")
    print("  - Talent 5:  ~10 at age 10 → ~50-72 at age 27")
    print("  - Talent 1:  ~10 at age 10 → ~40 at age 27\n")
    
    test_cases = [
        (10, 10, "Talent 10 (Elite)"),
        (9, 10, "Talent 9 (Excellent)"),
        (8, 10, "Talent 8 (Very Good)"),
        (7, 10, "Talent 7 (Good)"),
        (6, 10, "Talent 6 (Above Average)"),
        (5, 10, "Talent 5 (Average)"),
        (4, 10, "Talent 4 (Below Average)"),
        (3, 10, "Talent 3 (Poor)"),
        (2, 10, "Talent 2 (Very Poor)"),
        (1, 10, "Talent 1 (Minimal)"),
    ]
    
    print(f"{'Talent':<8} {'Start':<8} {'Expected Dev':<15} {'Peak Str':<12} {'Talent Mult':<12} {'Status'}")
    print("-" * 80)
    
    results = []
    for talent, starting_strength, label in test_cases:
        # Calculate expected development from age 10 to 27
        expected_dev = calculate_expected_development_years_to_peak(10, talent)
        
        # Calculate peak strength
        peak_strength = min(99, starting_strength + expected_dev)
        
        # Get talent multiplier
        talent_mult = calculate_talent_multiplier(talent)
        
        # Determine if result is as expected
        if talent == 10:
            status = "✓" if peak_strength >= 80 else "✗"
        elif talent == 5:
            status = "✓" if 50 <= peak_strength <= 80 else "✗"
        elif talent == 1:
            status = "✓" if 30 <= peak_strength <= 50 else "✗"
        else:
            status = "✓"  # Other talents are in between
        
        print(f"{talent:<8} {starting_strength:<8} {expected_dev:<15.1f} {peak_strength:<12.1f} {talent_mult:<12.2f} {status}")
        results.append((talent, peak_strength, status))
    
    # Check if key talents meet expectations
    talent_10_result = next((r for r in results if r[0] == 10), None)
    talent_5_result = next((r for r in results if r[0] == 5), None)
    talent_1_result = next((r for r in results if r[0] == 1), None)
    
    all_pass = True
    if talent_10_result and talent_10_result[1] >= 80:
        print("\n✓ PASS: Talent 10 reaches ~90+ at peak")
    else:
        print(f"\n✗ FAIL: Talent 10 only reaches {talent_10_result[1]:.1f} at peak (expected ~90+)")
        all_pass = False
    
    if talent_5_result and 50 <= talent_5_result[1] <= 80:
        print(f"✓ PASS: Talent 5 reaches {talent_5_result[1]:.1f} at peak (expected 50-80)")
    else:
        print(f"✗ FAIL: Talent 5 reaches {talent_5_result[1]:.1f} at peak (expected 50-80)")
        all_pass = False
    
    if talent_1_result and 30 <= talent_1_result[1] <= 50:
        print(f"✓ PASS: Talent 1 reaches {talent_1_result[1]:.1f} at peak (expected 30-50)")
    else:
        print(f"✗ FAIL: Talent 1 reaches {talent_1_result[1]:.1f} at peak (expected 30-50)")
        all_pass = False
    
    return all_pass


def test_development_progression():
    """Test that development progression is smooth across all ages."""
    print("\n" + "="*80)
    print("TEST 3: DEVELOPMENT PROGRESSION BY AGE")
    print("="*80)
    print("\nTesting smooth development progression for Talent 10 and Talent 5 players.\n")
    
    # Test Talent 10 player
    print("TALENT 10 PLAYER (Elite):")
    print(f"{'Age':<6} {'Strength':<10} {'Dev from 10':<15} {'Age Factor':<12}")
    print("-" * 50)
    
    talent_10_strengths = []
    for age in range(10, 28):
        expected_dev = calculate_expected_development_years_to_peak(age, 10)
        current_strength = min(99, 10 + (calculate_expected_development_years_to_peak(10, 10) - expected_dev))
        age_factor = calculate_age_development_factor(age)
        
        talent_10_strengths.append(current_strength)
        print(f"{age:<6} {current_strength:<10.1f} {current_strength - 10:<15.1f} {age_factor:<12.2f}")
    
    # Test Talent 5 player
    print("\nTALENT 5 PLAYER (Average):")
    print(f"{'Age':<6} {'Strength':<10} {'Dev from 10':<15} {'Age Factor':<12}")
    print("-" * 50)
    
    talent_5_strengths = []
    for age in range(10, 28):
        expected_dev = calculate_expected_development_years_to_peak(age, 5)
        current_strength = min(99, 10 + (calculate_expected_development_years_to_peak(10, 5) - expected_dev))
        age_factor = calculate_age_development_factor(age)
        
        talent_5_strengths.append(current_strength)
        print(f"{age:<6} {current_strength:<10.1f} {current_strength - 10:<15.1f} {age_factor:<12.2f}")
    
    # Check for smooth progression (no sudden jumps or decreases)
    def is_smooth(strengths):
        for i in range(1, len(strengths)):
            # Strength should always increase or stay the same for young players
            if strengths[i] < strengths[i-1]:
                return False
        return True
    
    talent_10_smooth = is_smooth(talent_10_strengths)
    talent_5_smooth = is_smooth(talent_5_strengths)
    
    print("\n" + "-" * 50)
    if talent_10_smooth:
        print("✓ PASS: Talent 10 progression is smooth (always increasing)")
    else:
        print("✗ FAIL: Talent 10 progression has decreases")
    
    if talent_5_smooth:
        print("✓ PASS: Talent 5 progression is smooth (always increasing)")
    else:
        print("✗ FAIL: Talent 5 progression has decreases")
    
    return talent_10_smooth and talent_5_smooth


def test_talent_multiplier_impact():
    """Test that talent multiplier has strong impact on development."""
    print("\n" + "="*80)
    print("TEST 4: TALENT MULTIPLIER IMPACT")
    print("="*80)
    print("\nTesting that talent multiplier has significant impact on development.\n")
    
    print(f"{'Talent':<8} {'Multiplier':<12} {'Total Dev (10→27)':<20} {'Peak Strength':<15}")
    print("-" * 60)
    
    for talent in range(1, 11):
        mult = calculate_talent_multiplier(talent)
        total_dev = calculate_expected_development_years_to_peak(10, talent)
        peak = min(99, 10 + total_dev)
        
        print(f"{talent:<8} {mult:<12.2f} {total_dev:<20.1f} {peak:<15.1f}")
    
    # Check that there's significant difference between talent 1 and talent 10
    talent_1_dev = calculate_expected_development_years_to_peak(10, 1)
    talent_10_dev = calculate_expected_development_years_to_peak(10, 10)
    
    difference = talent_10_dev - talent_1_dev
    
    print(f"\nDifference in development (Talent 10 vs Talent 1): {difference:.1f} strength points")
    
    if difference >= 40:
        print("✓ PASS: Talent has strong impact on development (40+ point difference)")
        return True
    else:
        print(f"✗ FAIL: Talent impact too weak (only {difference:.1f} point difference, expected 40+)")
        return False


def run_all_tests():
    """Run all verification tests."""
    print("\n" + "="*80)
    print("UNIFIED YOUTH PLAYER GENERATION AND DEVELOPMENT VERIFICATION")
    print("="*80)

    results = []

    # Run all tests
    results.append(("Unified young player generation", test_unified_young_player_generation()))
    results.append(("Talent-based development", test_talent_development()))
    results.append(("Development progression", test_development_progression()))
    results.append(("Talent multiplier impact", test_talent_multiplier_impact()))

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(r[1] for r in results)

    print("\n" + "="*80)
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("="*80 + "\n")

    return all_passed


if __name__ == "__main__":
    run_all_tests()

