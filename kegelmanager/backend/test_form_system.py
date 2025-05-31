"""
Test script for the form system functionality.

This script tests various aspects of the form system:
- Form modifier generation
- Form updates over time
- Integration with player strength
- Form summary generation
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Player
from form_system import (
    generate_form_modifier,
    update_player_form,
    update_all_players_form,
    get_player_total_form_modifier,
    apply_form_to_strength,
    initialize_random_form_for_player,
    reset_all_player_forms,
    get_form_summary_for_player
)


def test_form_modifier_generation():
    """Test the form modifier generation function."""
    print("=== Testing Form Modifier Generation ===")
    
    # Test short-term form
    for i in range(5):
        modifier, duration = generate_form_modifier('short')
        print(f"Short-term form {i+1}: {modifier:+.2f} for {duration} days")
        assert -20 <= modifier <= 20, f"Short-term modifier out of range: {modifier}"
        assert 1 <= duration <= 3, f"Short-term duration out of range: {duration}"
    
    # Test medium-term form
    for i in range(5):
        modifier, duration = generate_form_modifier('medium')
        print(f"Medium-term form {i+1}: {modifier:+.2f} for {duration} days")
        assert -15 <= modifier <= 15, f"Medium-term modifier out of range: {modifier}"
        assert 4 <= duration <= 8, f"Medium-term duration out of range: {duration}"
    
    # Test long-term form
    for i in range(5):
        modifier, duration = generate_form_modifier('long')
        print(f"Long-term form {i+1}: {modifier:+.2f} for {duration} days")
        assert -10 <= modifier <= 10, f"Long-term modifier out of range: {modifier}"
        assert 10 <= duration <= 20, f"Long-term duration out of range: {duration}"
    
    print("✓ Form modifier generation tests passed\n")


def test_player_form_updates():
    """Test form updates for individual players."""
    print("=== Testing Player Form Updates ===")
    
    from app import app
    with app.app_context():
        # Get a test player
        player = Player.query.first()
        if not player:
            print("✗ No players found in database")
            return False
        
        print(f"Testing with player: {player.name}")
        
        # Reset player form
        player.form_short_term = 0.0
        player.form_medium_term = 0.0
        player.form_long_term = 0.0
        player.form_short_remaining_days = 0
        player.form_medium_remaining_days = 0
        player.form_long_remaining_days = 0
        
        # Initialize random form
        initialize_random_form_for_player(player)
        db.session.commit()
        
        print(f"Initial form: Short={player.form_short_term:+.2f} ({player.form_short_remaining_days}d), "
              f"Medium={player.form_medium_term:+.2f} ({player.form_medium_remaining_days}d), "
              f"Long={player.form_long_term:+.2f} ({player.form_long_remaining_days}d)")
        
        # Test form updates over several days
        for day in range(1, 6):
            updated = update_player_form(player)
            print(f"Day {day}: Updated={updated}, "
                  f"Short={player.form_short_term:+.2f} ({player.form_short_remaining_days}d), "
                  f"Medium={player.form_medium_term:+.2f} ({player.form_medium_remaining_days}d), "
                  f"Long={player.form_long_term:+.2f} ({player.form_long_remaining_days}d)")
        
        db.session.commit()
        print("✓ Player form update tests passed\n")
        return True


def test_strength_application():
    """Test applying form modifiers to player strength."""
    print("=== Testing Strength Application ===")
    
    from app import app
    with app.app_context():
        # Get a test player
        player = Player.query.first()
        if not player:
            print("✗ No players found in database")
            return False
        
        print(f"Testing with player: {player.name} (Base strength: {player.strength})")
        
        # Test with different form combinations
        test_cases = [
            (0.0, 0.0, 0.0, "No form"),
            (10.0, 5.0, 3.0, "All positive form"),
            (-8.0, -4.0, -2.0, "All negative form"),
            (15.0, -10.0, 5.0, "Mixed form"),
            (20.0, 15.0, 10.0, "Maximum positive form"),
            (-20.0, -15.0, -10.0, "Maximum negative form")
        ]
        
        for short, medium, long, description in test_cases:
            player.form_short_term = short
            player.form_medium_term = medium
            player.form_long_term = long
            player.form_short_remaining_days = 1 if short != 0 else 0
            player.form_medium_remaining_days = 1 if medium != 0 else 0
            player.form_long_remaining_days = 1 if long != 0 else 0
            
            total_modifier = get_player_total_form_modifier(player)
            effective_strength = apply_form_to_strength(player.strength, player)
            
            print(f"{description}: Total modifier={total_modifier:+.1f}, "
                  f"Effective strength={effective_strength} (was {player.strength})")
            
            # Ensure strength stays within bounds
            assert 1 <= effective_strength <= 99, f"Effective strength out of bounds: {effective_strength}"
        
        print("✓ Strength application tests passed\n")
        return True


def test_form_summary():
    """Test form summary generation."""
    print("=== Testing Form Summary ===")
    
    from app import app
    with app.app_context():
        # Get a test player
        player = Player.query.first()
        if not player:
            print("✗ No players found in database")
            return False
        
        print(f"Testing form summary for player: {player.name}")
        
        # Test different form scenarios
        test_scenarios = [
            (0.0, 0.0, 0.0, 0, 0, 0, "No active form"),
            (12.0, 8.0, 5.0, 2, 5, 15, "Excellent form"),
            (-15.0, -10.0, -8.0, 1, 3, 12, "Very poor form"),
            (5.0, 0.0, 0.0, 2, 0, 0, "Only short-term positive"),
            (0.0, -5.0, 0.0, 0, 4, 0, "Only medium-term negative")
        ]
        
        for short, medium, long, short_days, medium_days, long_days, description in test_scenarios:
            player.form_short_term = short
            player.form_medium_term = medium
            player.form_long_term = long
            player.form_short_remaining_days = short_days
            player.form_medium_remaining_days = medium_days
            player.form_long_remaining_days = long_days
            
            summary = get_form_summary_for_player(player)
            
            print(f"{description}:")
            print(f"  Status: {summary['status']}")
            print(f"  Total modifier: {summary['total_modifier']:+.1f}")
            print(f"  Active forms: {len(summary['active_forms'])}")
            for form in summary['active_forms']:
                print(f"    - {form}")
            print()
        
        print("✓ Form summary tests passed\n")
        return True


def test_bulk_operations():
    """Test bulk form operations."""
    print("=== Testing Bulk Operations ===")
    
    from app import app
    with app.app_context():
        # Test updating all players
        updated_count = update_all_players_form()
        print(f"Updated form for {updated_count} players")
        
        # Test resetting all forms
        reset_count = reset_all_player_forms()
        print(f"Reset form for {reset_count} players")
        
        # Verify all forms are reset
        players_with_form = Player.query.filter(
            (Player.form_short_term != 0.0) |
            (Player.form_medium_term != 0.0) |
            (Player.form_long_term != 0.0) |
            (Player.form_short_remaining_days > 0) |
            (Player.form_medium_remaining_days > 0) |
            (Player.form_long_remaining_days > 0)
        ).count()
        
        print(f"Players with active form after reset: {players_with_form}")
        assert players_with_form == 0, "Some players still have active form after reset"
        
        print("✓ Bulk operations tests passed\n")
        return True


def main():
    """Run all form system tests."""
    print("=== Form System Test Suite ===\n")
    
    try:
        # Test form modifier generation (no database required)
        test_form_modifier_generation()
        
        # Test database-dependent functions
        if not test_player_form_updates():
            return False
        
        if not test_strength_application():
            return False
        
        if not test_form_summary():
            return False
        
        if not test_bulk_operations():
            return False
        
        print("✓ All form system tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
