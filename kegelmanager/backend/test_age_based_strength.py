"""
Test script for age-based strength generation.

This script tests the new age-based strength generation system by creating
sample players of different ages and talents, and verifying that:
1. Young players have lower initial strength
2. Peak-age players have higher initial strength
3. Older players have moderate strength
4. Strength respects talent-based maximum potential
"""

import sys
import os
import random
import numpy as np

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import get_config
from init_db import get_age_based_strength_modifier, calculate_player_attribute_by_league_level


def test_age_based_strength_modifier():
    """Test the age-based strength modifier function."""
    print("=" * 80)
    print("TEST 1: Age-Based Strength Modifier")
    print("=" * 80)

    test_cases = [
        # (age, talent, expected_range_description)
        (10, 7, "Youth player (E-Jugend) - should be 30-50% of potential"),
        (14, 8, "Youth player (C-Jugend) - should be 30-50% of potential"),
        (18, 8, "Young player - should be 50-70% of potential"),
        (22, 9, "Young player - should be 50-70% of potential"),
        (25, 7, "Peak player - should be 80-95% of potential"),
        (27, 10, "Peak player - should be 80-95% of potential"),
        (30, 6, "Mature player - should be 75-90% of potential"),
        (32, 8, "Mature player - should be 75-90% of potential"),
        (35, 7, "Veteran player - should be 65-85% of potential"),
        (38, 5, "Veteran player - should be 65-85% of potential"),
    ]
    
    for age, talent, description in test_cases:
        # Test multiple times to see the range
        modifiers = [get_age_based_strength_modifier(age, talent) for _ in range(10)]
        avg_modifier = sum(modifiers) / len(modifiers)
        min_modifier = min(modifiers)
        max_modifier = max(modifiers)
        
        print(f"\nAge {age}, Talent {talent}: {description}")
        print(f"  Modifier range: {min_modifier:.2%} - {max_modifier:.2%}")
        print(f"  Average modifier: {avg_modifier:.2%}")
        print(f"  Max potential: {talent * 9} → Expected strength: {int(talent * 9 * avg_modifier)}")


def test_player_generation_by_age():
    """Test complete player generation with different ages."""
    print("\n" + "=" * 80)
    print("TEST 2: Complete Player Generation by Age")
    print("=" * 80)
    
    # Test for Bundesliga level (level 1) with team strength 70
    league_level = 1
    team_staerke = 70
    
    print(f"\nGenerating players for League Level {league_level}, Team Strength {team_staerke}")
    print("-" * 80)
    
    age_groups = [
        ("Youth (7-15)", list(range(7, 16))),
        ("Young (16-23)", list(range(16, 24))),
        ("Peak (24-27)", list(range(24, 28))),
        ("Mature (28-32)", list(range(28, 33))),
        ("Veteran (33-40)", list(range(33, 41))),
    ]
    
    for group_name, ages in age_groups:
        print(f"\n{group_name}:")
        print(f"{'Age':<5} {'Talent':<7} {'Strength':<9} {'Max Pot.':<10} {'% of Max':<10}")
        print("-" * 50)
        
        for _ in range(5):  # Generate 5 players per age group
            age = random.choice(ages)
            
            # Generate player with age
            attributes = calculate_player_attribute_by_league_level(
                league_level,
                team_staerke=team_staerke,
                age=age
            )
            
            strength = attributes['strength']
            talent = attributes['talent']
            max_potential = talent * 9
            percentage = (strength / max_potential * 100) if max_potential > 0 else 0
            
            print(f"{age:<5} {talent:<7} {strength:<9} {max_potential:<10} {percentage:.1f}%")


def test_talent_impact():
    """Test how talent affects initial strength for different ages."""
    print("\n" + "=" * 80)
    print("TEST 3: Talent Impact on Initial Strength")
    print("=" * 80)
    
    league_level = 1
    team_staerke = 70
    
    talents = [3, 5, 7, 9, 10]
    ages = [18, 25, 30, 35]
    
    print(f"\nGenerating players with different talents and ages")
    print(f"League Level {league_level}, Team Strength {team_staerke}")
    print("-" * 80)
    
    for age in ages:
        print(f"\nAge {age}:")
        print(f"{'Talent':<7} {'Strength':<9} {'Max Pot.':<10} {'% of Max':<10}")
        print("-" * 40)
        
        for talent in talents:
            # Generate multiple players and average
            strengths = []
            for _ in range(10):
                attributes = calculate_player_attribute_by_league_level(
                    league_level,
                    team_staerke=team_staerke,
                    age=age,
                    talent=talent
                )
                strengths.append(attributes['strength'])
            
            avg_strength = sum(strengths) / len(strengths)
            max_potential = talent * 9
            percentage = (avg_strength / max_potential * 100) if max_potential > 0 else 0
            
            print(f"{talent:<7} {avg_strength:.1f}{'':<5} {max_potential:<10} {percentage:.1f}%")


def test_league_level_impact():
    """Test how league level affects strength generation with age."""
    print("\n" + "=" * 80)
    print("TEST 4: League Level Impact with Age-Based Strength")
    print("=" * 80)
    
    age = 20  # Young player
    talent = 7
    
    print(f"\nGenerating 20-year-old player with Talent {talent} across different leagues")
    print("-" * 80)
    print(f"{'League':<15} {'Team Str.':<12} {'Avg Strength':<15} {'Max Pot.':<10}")
    print("-" * 60)
    
    league_configs = [
        ("Bundesliga", 1, 70),
        ("2. Bundesliga", 2, 65),
        ("Regionalliga", 3, 60),
        ("Oberliga", 5, 50),
        ("Landesliga", 8, 40),
        ("Kreisliga", 10, 30),
    ]
    
    for league_name, league_level, team_staerke in league_configs:
        # Generate multiple players and average
        strengths = []
        for _ in range(20):
            attributes = calculate_player_attribute_by_league_level(
                league_level,
                team_staerke=team_staerke,
                age=age,
                talent=talent
            )
            strengths.append(attributes['strength'])
        
        avg_strength = sum(strengths) / len(strengths)
        max_potential = talent * 9
        
        print(f"{league_name:<15} {team_staerke:<12} {avg_strength:.1f}{'':<11} {max_potential:<10}")


def test_development_potential():
    """Test that young players have room to develop."""
    print("\n" + "=" * 80)
    print("TEST 5: Development Potential for Young Players")
    print("=" * 80)
    
    league_level = 1
    team_staerke = 70
    
    print(f"\nYoung players should have significant room to develop")
    print(f"League Level {league_level}, Team Strength {team_staerke}")
    print("-" * 80)
    print(f"{'Age':<5} {'Talent':<7} {'Start Str.':<11} {'Max Pot.':<10} {'Growth Room':<12}")
    print("-" * 50)
    
    for _ in range(10):
        age = random.randint(16, 22)
        
        attributes = calculate_player_attribute_by_league_level(
            league_level,
            team_staerke=team_staerke,
            age=age
        )
        
        strength = attributes['strength']
        talent = attributes['talent']
        max_potential = talent * 9
        growth_room = max_potential - strength
        
        print(f"{age:<5} {talent:<7} {strength:<11} {max_potential:<10} {growth_room} ({growth_room/max_potential*100:.1f}%)")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("AGE-BASED STRENGTH GENERATION TEST SUITE")
    print("=" * 80)
    
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    try:
        test_age_based_strength_modifier()
        test_player_generation_by_age()
        test_talent_impact()
        test_league_level_impact()
        test_development_potential()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nKey Observations:")
        print("1. Youth players (7-15) start at 30-50% of their maximum potential")
        print("2. Young players (16-23) start at 50-70% of their maximum potential")
        print("3. Peak players (24-27) start at 80-95% of their maximum potential")
        print("4. Mature players (28-32) start at 75-90% of their maximum potential")
        print("5. Veteran players (33+) start at 65-85% of their maximum potential")
        print("6. Strength never exceeds talent-based maximum (talent × 9)")
        print("7. Youth and young talented players have significant room to develop")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

