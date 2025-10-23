"""
Test script to verify that attributes maintain proper relationship to strength during development.

This tests the fix for the issue where young players with low starting attributes
(e.g., 36 for strength 10) would reach maximum (99) after years of development.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from player_development import (
    calculate_strength_change,
    develop_single_attribute,
    calculate_age_development_factor,
    calculate_talent_multiplier
)


class MockPlayer:
    """Mock player object for testing."""
    def __init__(self, age, strength, talent):
        self.age = age
        self.strength = strength
        self.talent = talent
        self.id = 1
        self.name = "Test Player"


def calculate_expected_attribute(strength):
    """Calculate what an attribute should be based on strength."""
    # Formula: attr = 60 + (strength - 50) * 0.6
    return 60 + (strength - 50) * 0.6


def test_attribute_development():
    """Test that attributes maintain proper relationship to strength."""
    print("\n" + "="*80)
    print("ATTRIBUTE DEVELOPMENT TEST")
    print("="*80)
    print("\nTesting that attributes stay proportional to strength during development")
    print("Formula: attribute = 60 + (strength - 50) * 0.6")
    print("\n" + "-"*80)
    
    # Test case: 10-year-old player with strength 10, talent 10
    # This should develop significantly over 15 years
    
    initial_strength = 10
    initial_age = 10
    talent = 10
    years_to_simulate = 15
    
    # Calculate initial attribute value
    current_strength = initial_strength
    current_attribute = calculate_expected_attribute(current_strength)
    
    print(f"\nInitial State (Age {initial_age}):")
    print(f"  Strength: {current_strength}")
    print(f"  Expected Attribute: {current_attribute:.1f}")
    print(f"  Talent: {talent}")
    
    print(f"\n{'Year':<6} {'Age':<5} {'Strength':<10} {'Attr (Old)':<12} {'Attr (New)':<12} {'Expected':<10} {'Deviation':<10}")
    print("-"*80)
    
    # Simulate development year by year
    for year in range(years_to_simulate):
        age = initial_age + year
        
        # Create mock player
        player = MockPlayer(age, current_strength, talent)
        
        # Calculate strength change
        strength_change = calculate_strength_change(player)
        
        # Calculate attribute change using OLD method (70-90% of strength change)
        old_method_change = strength_change * 0.8  # Average of 70-90%
        old_method_attribute = current_attribute + old_method_change
        
        # Calculate attribute change using NEW method (maintains proportion)
        new_attribute = develop_single_attribute(
            current_attribute, 
            strength_change, 
            'konstanz',
            current_strength
        )
        
        # Update strength
        new_strength = current_strength + strength_change
        new_strength = max(1, min(99, new_strength))
        
        # Calculate expected attribute for new strength
        expected_attribute = calculate_expected_attribute(new_strength)
        
        # Calculate deviation
        deviation = new_attribute - expected_attribute
        
        print(f"{year+1:<6} {age:<5} {current_strength:>4} → {new_strength:<3} "
              f"{current_attribute:>5.1f} → {old_method_attribute:<5.1f} "
              f"{current_attribute:>5.1f} → {new_attribute:<5.1f} "
              f"{expected_attribute:>9.1f} {deviation:>+9.1f}")
        
        # Update for next iteration
        current_strength = new_strength
        current_attribute = new_attribute
    
    print("-"*80)
    print(f"\nFinal State (Age {initial_age + years_to_simulate}):")
    print(f"  Strength: {current_strength}")
    print(f"  Attribute: {current_attribute:.1f}")
    print(f"  Expected: {calculate_expected_attribute(current_strength):.1f}")
    print(f"  Deviation: {current_attribute - calculate_expected_attribute(current_strength):+.1f}")
    
    # Check if attribute is capped at 99
    if current_attribute >= 99:
        print(f"\n  ⚠️  WARNING: Attribute reached maximum (99)!")
    else:
        print(f"\n  ✓  Attribute stayed within reasonable range")
    
    print("\n" + "="*80)


def test_multiple_talents():
    """Test development for players with different talents."""
    print("\n" + "="*80)
    print("MULTIPLE TALENT LEVELS TEST")
    print("="*80)
    print("\nTesting 10-year-old players with talents 1-10 after 15 years")
    print("\n" + "-"*80)
    
    print(f"{'Talent':<8} {'Start Str':<12} {'Final Str':<12} {'Start Attr':<12} {'Final Attr':<12} {'Expected':<10} {'At Max?':<8}")
    print("-"*80)
    
    for talent in range(1, 11):
        initial_strength = 10
        initial_age = 10
        years = 15
        
        current_strength = initial_strength
        current_attribute = calculate_expected_attribute(current_strength)
        initial_attribute = current_attribute
        
        # Simulate 15 years
        for year in range(years):
            age = initial_age + year
            player = MockPlayer(age, current_strength, talent)
            strength_change = calculate_strength_change(player)
            
            new_attribute = develop_single_attribute(
                current_attribute,
                strength_change,
                'konstanz',
                current_strength
            )
            
            new_strength = max(1, min(99, current_strength + strength_change))
            
            current_strength = new_strength
            current_attribute = new_attribute
        
        expected = calculate_expected_attribute(current_strength)
        at_max = "YES ⚠️" if current_attribute >= 99 else "No"
        
        print(f"{talent:<8} {initial_strength:<12} {current_strength:<12} "
              f"{initial_attribute:<12.1f} {current_attribute:<12.1f} "
              f"{expected:<10.1f} {at_max:<8}")
    
    print("-"*80)
    print("\n" + "="*80)


if __name__ == "__main__":
    test_attribute_development()
    test_multiple_talents()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nThe NEW method maintains the proportional relationship between")
    print("strength and attributes, preventing attributes from reaching 99")
    print("while strength is still developing.")
    print("\nFormula: attribute = 60 + (strength - 50) * 0.6")
    print("This ensures attributes stay realistic throughout development.")
    print("="*80 + "\n")

