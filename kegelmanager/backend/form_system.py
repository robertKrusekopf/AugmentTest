"""
Form System for Player Performance Management

This module handles the dynamic form system for players, which affects their performance
during matches. The form system includes three types of modifiers:
- Short-term form: -20 to +20, lasts 1-3 match days
- Medium-term form: -15 to +15, lasts 4-8 match days  
- Long-term form: -10 to +10, lasts 10-20 match days

Form modifiers are applied to player strength during match simulation.
"""

import random
import numpy as np
from models import Player, db


def generate_form_modifier(form_type):
    """
    Generate a new form modifier based on the type.
    
    Args:
        form_type (str): Type of form modifier ('short', 'medium', 'long')
        
    Returns:
        tuple: (modifier_value, duration_days)
    """
    if form_type == 'short':
        # Short-term form: -10 to +10, duration 1-3 days
        modifier = random.uniform(-10, 10)
        duration = random.randint(1, 3)
    elif form_type == 'medium':
        # Medium-term form: -7 to +7, duration 4-8 days
        modifier = random.uniform(-7, 7)
        duration = random.randint(4, 8)
    elif form_type == 'long':
        # Long-term form: -5 to +5, duration 10-20 days
        modifier = random.uniform(-5, 5)
        duration = random.randint(10, 20)
    else:
        raise ValueError(f"Invalid form type: {form_type}")
    
    return round(modifier, 2), duration


def update_player_form(player):
    """
    Update a single player's form modifiers.
    
    Args:
        player (Player): The player to update
        
    Returns:
        bool: True if any form was updated, False otherwise
    """
    updated = False
    
    # Decrease remaining days for all active forms
    # Handle NULL values by treating them as 0
    if player.form_short_remaining_days is not None and player.form_short_remaining_days > 0:
        player.form_short_remaining_days -= 1
        if player.form_short_remaining_days <= 0:
            player.form_short_term = 0.0
            updated = True
    elif player.form_short_remaining_days is None:
        player.form_short_remaining_days = 0
        updated = True

    if player.form_medium_remaining_days is not None and player.form_medium_remaining_days > 0:
        player.form_medium_remaining_days -= 1
        if player.form_medium_remaining_days <= 0:
            player.form_medium_term = 0.0
            updated = True
    elif player.form_medium_remaining_days is None:
        player.form_medium_remaining_days = 0
        updated = True

    if player.form_long_remaining_days is not None and player.form_long_remaining_days > 0:
        player.form_long_remaining_days -= 1
        if player.form_long_remaining_days <= 0:
            player.form_long_term = 0.0
            updated = True
    elif player.form_long_remaining_days is None:
        player.form_long_remaining_days = 0
        updated = True

    # Chance to generate new form modifiers
    # Short-term form: 15% chance per match day
    if (player.form_short_remaining_days is not None and player.form_short_remaining_days <= 0) and random.random() < 0.15:
        modifier, duration = generate_form_modifier('short')
        player.form_short_term = modifier
        player.form_short_remaining_days = duration
        updated = True
    
    # Medium-term form: 8% chance per match day
    if (player.form_medium_remaining_days is not None and player.form_medium_remaining_days <= 0) and random.random() < 0.08:
        modifier, duration = generate_form_modifier('medium')
        player.form_medium_term = modifier
        player.form_medium_remaining_days = duration
        updated = True

    # Long-term form: 4% chance per match day
    if (player.form_long_remaining_days is not None and player.form_long_remaining_days <= 0) and random.random() < 0.04:
        modifier, duration = generate_form_modifier('long')
        player.form_long_term = modifier
        player.form_long_remaining_days = duration
        updated = True
    
    return updated


def update_all_players_form():
    """
    Update form modifiers for all players in the database.
    This should be called at the beginning of each match day simulation.
    
    Returns:
        int: Number of players whose form was updated
    """
    players = Player.query.all()
    updated_count = 0
    
    for player in players:
        if update_player_form(player):
            updated_count += 1
    
    # Commit all changes at once for better performance
    db.session.commit()
    
    return updated_count


def get_player_total_form_modifier(player):
    """
    Calculate the total form modifier for a player.

    Args:
        player (Player or dict): The player to calculate form for, or a dict for Stroh players

    Returns:
        float: Total form modifier (sum of all active form modifiers)
    """
    # Check if this is a Stroh player (dictionary)
    if isinstance(player, dict):
        # Stroh players don't have form modifiers
        return 0.0

    total_modifier = 0.0

    if player.form_short_remaining_days > 0:
        total_modifier += player.form_short_term

    if player.form_medium_remaining_days > 0:
        total_modifier += player.form_medium_term

    if player.form_long_remaining_days > 0:
        total_modifier += player.form_long_term

    return total_modifier


def apply_form_to_strength(base_strength, player):
    """
    Apply form modifiers to a player's base strength.

    Args:
        base_strength (int): The player's base strength value
        player (Player or dict): The player object with form modifiers, or a dict for Stroh players

    Returns:
        int: Modified strength value (clamped between 1 and 99)
    """
    # Check if this is a Stroh player (dictionary)
    if isinstance(player, dict):
        # Stroh players don't have form modifiers, return base strength
        return max(1, min(99, int(base_strength)))

    # For real players, apply form modifiers
    form_modifier = get_player_total_form_modifier(player)
    modified_strength = base_strength + form_modifier

    # Clamp the result between 1 and 99
    return max(1, min(99, int(round(modified_strength))))


def initialize_random_form_for_player(player):
    """
    Initialize random form modifiers for a new player.
    This can be used when creating new players or resetting form.
    
    Args:
        player (Player): The player to initialize form for
    """
    # 30% chance to start with short-term form
    if random.random() < 0.30:
        modifier, duration = generate_form_modifier('short')
        player.form_short_term = modifier
        player.form_short_remaining_days = duration
    
    # 20% chance to start with medium-term form
    if random.random() < 0.20:
        modifier, duration = generate_form_modifier('medium')
        player.form_medium_term = modifier
        player.form_medium_remaining_days = duration
    
    # 10% chance to start with long-term form
    if random.random() < 0.10:
        modifier, duration = generate_form_modifier('long')
        player.form_long_term = modifier
        player.form_long_remaining_days = duration


def reset_all_player_forms():
    """
    Reset all form modifiers for all players to zero.
    This can be used for testing or at the start of a new season.
    
    Returns:
        int: Number of players whose form was reset
    """
    players = Player.query.all()
    reset_count = 0
    
    for player in players:
        if (player.form_short_term != 0.0 or player.form_medium_term != 0.0 or 
            player.form_long_term != 0.0 or player.form_short_remaining_days > 0 or
            player.form_medium_remaining_days > 0 or player.form_long_remaining_days > 0):
            
            player.form_short_term = 0.0
            player.form_medium_term = 0.0
            player.form_long_term = 0.0
            player.form_short_remaining_days = 0
            player.form_medium_remaining_days = 0
            player.form_long_remaining_days = 0
            reset_count += 1
    
    db.session.commit()
    return reset_count


def get_form_summary_for_player(player):
    """
    Get a human-readable summary of a player's current form.
    
    Args:
        player (Player): The player to get form summary for
        
    Returns:
        dict: Summary of the player's form status
    """
    total_modifier = get_player_total_form_modifier(player)
    
    active_forms = []
    if player.form_short_remaining_days > 0:
        active_forms.append(f"Kurzfristig: {player.form_short_term:+.1f} ({player.form_short_remaining_days} Tage)")
    
    if player.form_medium_remaining_days > 0:
        active_forms.append(f"Mittelfristig: {player.form_medium_term:+.1f} ({player.form_medium_remaining_days} Tage)")
    
    if player.form_long_remaining_days > 0:
        active_forms.append(f"Langfristig: {player.form_long_term:+.1f} ({player.form_long_remaining_days} Tage)")
    
    # Determine form status
    if total_modifier > 10:
        status = "Ausgezeichnet"
    elif total_modifier > 5:
        status = "Sehr gut"
    elif total_modifier > 0:
        status = "Gut"
    elif total_modifier == 0:
        status = "Normal"
    elif total_modifier > -5:
        status = "Schwach"
    elif total_modifier > -10:
        status = "Schlecht"
    else:
        status = "Sehr schlecht"
    
    return {
        'total_modifier': total_modifier,
        'status': status,
        'active_forms': active_forms,
        'has_active_form': len(active_forms) > 0
    }
