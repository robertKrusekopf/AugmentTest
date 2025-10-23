"""
Test script for the player development system.

This script demonstrates how player development works with different
age, talent, and club quality combinations.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import Player, Club, db
from player_development import (
    calculate_age_development_factor,
    calculate_talent_multiplier,
    calculate_strength_change,
    develop_player
)


def test_age_curve():
    """Test the age-based development curve."""
    print("\n" + "="*60)
    print("AGE-BASED DEVELOPMENT CURVE")
    print("="*60)
    print(f"{'Age':<5} {'Development Factor':<20} {'Expected Change'}")
    print("-"*60)
    
    for age in [17, 19, 21, 23, 25, 27, 29, 31, 33, 35]:
        factor = calculate_age_development_factor(age)
        print(f"{age:<5} {factor:>+6.2f}{'':14} {factor:>+6.2f} strength")
    
    print("="*60)


def test_talent_system():
    """Test the talent multiplier system."""
    print("\n" + "="*60)
    print("TALENT MULTIPLIER SYSTEM")
    print("="*60)
    print(f"{'Talent':<8} {'Multiplier':<15} {'Effect'}")
    print("-"*60)

    for talent in range(1, 11):
        mult = calculate_talent_multiplier(talent)
        effect = (mult - 1.0) * 100
        print(f"{talent:<8} {mult:<15.2f} {effect:+.0f}%")

    print("="*60)





def test_complete_examples():
    """Test complete development examples with realistic scenarios."""
    print("\n" + "="*60)
    print("COMPLETE DEVELOPMENT EXAMPLES")
    print("="*60)
    
    with app.app_context():
        # Example scenarios
        scenarios = [
            {
                'name': 'Young Talent',
                'age': 19,
                'talent': 9,
                'strength': 55,
                'training': 80,
                'coaching': 80
            },
            {
                'name': 'Average Peak Player',
                'age': 26,
                'talent': 5,
                'strength': 44,
                'training': 50,
                'coaching': 50
            },
            {
                'name': 'Declining Veteran',
                'age': 33,
                'talent': 7,
                'strength': 58,
                'training': 60,
                'coaching': 60
            },
            {
                'name': 'Low Talent Youth',
                'age': 18,
                'talent': 3,
                'strength': 25,
                'training': 40,
                'coaching': 40
            },
            {
                'name': 'Elite Peak Player',
                'age': 25,
                'talent': 10,
                'strength': 85,
                'training': 90,
                'coaching': 90
            }
        ]
        
        for scenario in scenarios:
            print(f"\n{scenario['name']}:")
            print(f"  Age: {scenario['age']}, Talent: {scenario['talent']}, Strength: {scenario['strength']}")
            print(f"  Club Quality: Training {scenario['training']}, Coaching {scenario['coaching']}")
            
            # Create temporary club
            club = Club(
                name="Test Club",
                training_facilities=scenario['training'],
                coaching=scenario['coaching']
            )
            db.session.add(club)
            db.session.flush()
            
            # Create temporary player
            player = Player(
                name=scenario['name'],
                age=scenario['age'],
                talent=scenario['talent'],
                strength=scenario['strength'],
                club_id=club.id,
                position='Kegler',
                ausdauer=70,
                konstanz=70,
                drucksicherheit=70,
                volle=70,
                raeumer=70,
                sicherheit=70,
                auswaerts=70,
                start=70,
                mitte=70,
                schluss=70
            )
            
            # Calculate development factors
            age_factor = calculate_age_development_factor(player.age)
            talent_mult = calculate_talent_multiplier(player.talent)

            print(f"  Age Factor: {age_factor:+.2f}")
            print(f"  Talent Multiplier: {talent_mult:.2f}")
            
            # Simulate development 3 times to show variance
            print(f"  Simulated Changes (3 runs):")
            for i in range(3):
                change = calculate_strength_change(player, club)
                new_strength = max(1, min(99, player.strength + change))
                print(f"    Run {i+1}: {player.strength} → {new_strength} ({change:+d})")
            
            # Rollback to avoid saving test data
            db.session.rollback()
    
    print("\n" + "="*60)


def test_real_player_development():
    """Test development on actual players from the database."""
    print("\n" + "="*60)
    print("REAL PLAYER DEVELOPMENT TEST")
    print("="*60)
    
    with app.app_context():
        # Get a sample of players with different ages
        young_player = Player.query.filter(Player.age < 22, Player.is_retired == False).first()
        peak_player = Player.query.filter(Player.age >= 24, Player.age <= 28, Player.is_retired == False).first()
        old_player = Player.query.filter(Player.age > 30, Player.is_retired == False).first()
        
        players_to_test = [p for p in [young_player, peak_player, old_player] if p is not None]
        
        if not players_to_test:
            print("No players found in database. Please run with an existing database.")
            return
        
        for player in players_to_test:
            print(f"\n{player.name}:")
            print(f"  Age: {player.age}, Talent: {player.talent}, Strength: {player.strength}")
            
            if player.club:
                print(f"  Club: {player.club.name}")
                print(f"  Training: {player.club.training_facilities}, Coaching: {player.club.coaching}")
            
            # Store original values
            original_strength = player.strength
            original_attrs = {
                'ausdauer': player.ausdauer,
                'konstanz': player.konstanz,
                'volle': player.volle
            }
            
            # Develop the player
            result = develop_player(player)
            
            print(f"  Strength: {result['old_strength']} → {result['new_strength']} ({result['strength_change']:+d})")
            print(f"  Sample attribute changes:")
            for attr in ['ausdauer', 'konstanz', 'volle']:
                if attr in result['attribute_changes']:
                    change = result['attribute_changes'][attr]
                    old_val = original_attrs[attr]
                    new_val = old_val + change
                    print(f"    {attr.capitalize()}: {old_val} → {new_val} ({change:+d})")
            
            # Rollback changes
            db.session.rollback()
    
    print("\n" + "="*60)


if __name__ == '__main__':
    print("\n" + "="*70)
    print(" "*20 + "PLAYER DEVELOPMENT SYSTEM TEST")
    print("="*70)
    
    # Run all tests
    test_age_curve()
    test_talent_system()
    test_complete_examples()
    
    # Only test real players if database exists
    try:
        test_real_player_development()
    except Exception as e:
        print(f"\nSkipping real player test: {e}")
    
    print("\n" + "="*70)
    print(" "*25 + "TESTS COMPLETE")
    print("="*70 + "\n")

