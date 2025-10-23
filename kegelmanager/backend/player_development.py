"""
Player Development System

This module handles player attribute development over time based on:
- Age-based development curves
- Talent (development speed multiplier)
- Controlled randomness for realism

Development occurs during season transitions (Saisonwechsel).
"""

import random
import math
from models import Player, Club, PlayerHistory, Season, db
from config.config import get_config


def calculate_age_development_factor(age):
    """
    Calculate the base development factor based on player age.

    Returns a multiplier that determines how much a player develops:
    - Young players (10-23): Positive development (3.0 to 5.0)
    - Peak years (24-27): Minimal change (-0.2 to 0.5)
    - Decline years (28+): Negative development (-0.5 to -2.0)

    NEW: Increased development rates to allow talent to be the primary factor
    determining peak strength. A talent 10 player starting at ~10 should reach ~90,
    while a talent 5 player should reach ~50.

    Args:
        age: Player's current age

    Returns:
        float: Development factor (positive = improvement, negative = decline)
    """
    if age < 18:
        # Very young players develop rapidly (increased from 2.5 to 5.0)
        return 5.0
    elif age < 20:
        # Young players develop quickly (increased from 2.0 to 4.0)
        return 4.0
    elif age < 22:
        # Development continues but slows (increased from 1.5 to 3.0)
        return 3.0
    elif age < 24:
        # Late development phase (increased from 1.0 to 2.0)
        return 2.0
    elif age < 25:
        # Transition to peak (increased from 0.5 to 1.0)
        return 1.0
    elif age < 28:
        # Peak years - minimal change
        return random.uniform(-0.2, 0.3)
    elif age < 30:
        # Early decline
        return random.uniform(-0.5, -0.2)
    elif age < 32:
        # Moderate decline
        return random.uniform(-1.0, -0.5)
    elif age < 35:
        # Significant decline
        return random.uniform(-1.5, -1.0)
    else:
        # Steep decline
        return random.uniform(-2.0, -1.5)


def calculate_talent_multiplier(talent):
    """
    Calculate how talent affects development speed.

    NEW: Talent is now the PRIMARY factor determining peak strength.
    With increased development rates, talent multiplier determines how much
    a player develops from their starting strength (~10) to their peak.

    Talent determines development speed:
    - Talent 1 → 0.5× development speed (reaches ~40 from ~10)
    - Talent 2 → 0.6× development speed (reaches ~48 from ~10)
    - Talent 3 → 0.7× development speed (reaches ~56 from ~10)
    - Talent 4 → 0.8× development speed (reaches ~64 from ~10)
    - Talent 5 → 0.9× development speed (reaches ~72 from ~10)
    - Talent 6 → 1.0× development speed (reaches ~80 from ~10)
    - Talent 7 → 1.1× development speed (reaches ~88 from ~10)
    - Talent 8 → 1.2× development speed (reaches ~96 from ~10)
    - Talent 9 → 1.3× development speed (reaches ~104 → capped at 99)
    - Talent 10 → 1.4× development speed (reaches ~112 → capped at 99)

    Args:
        talent: Player's talent rating (1-10)

    Returns:
        float: Talent multiplier for development
    """
    # Linear formula: Talent 6 = 1.0, each talent level adds/subtracts 0.1
    return 0.5 + (talent - 1) * 0.1





def calculate_expected_development_years_to_peak(current_age, talent, club_bonus=1.0):
    """
    Calculate the expected total strength gain from current age to peak years (age 27).

    This simulates how much a player would develop if they continue developing normally.
    Uses average/expected values (not random) for predictable calculation.

    Args:
        current_age: Player's current age
        talent: Player's talent rating (1-10)
        club_bonus: Not used anymore, kept for compatibility (default 1.0)

    Returns:
        float: Expected total strength gain from current age to peak
    """
    if current_age >= 27:
        # Already at or past peak
        return 0.0

    # We'll simulate year by year with AVERAGE values (no randomness)
    total_expected_gain = 0.0
    simulated_age = current_age

    # Get talent multiplier (constant for all years)
    talent_mult = calculate_talent_multiplier(talent)

    # Simulate development year by year until age 27 (peak)
    while simulated_age < 27:
        # Get age factor (use deterministic values for peak years)
        # NEW: Updated to match the increased development rates
        if simulated_age < 18:
            age_factor = 5.0  # Increased from 2.5
        elif simulated_age < 20:
            age_factor = 4.0  # Increased from 2.0
        elif simulated_age < 22:
            age_factor = 3.0  # Increased from 1.5
        elif simulated_age < 24:
            age_factor = 2.0  # Increased from 1.0
        elif simulated_age < 25:
            age_factor = 1.0  # Increased from 0.5
        else:  # 25-26
            age_factor = 0.05  # Average of peak years (-0.2 to 0.3)

        # Calculate expected change for this year (no randomness)
        year_change = age_factor * talent_mult

        # Add to total
        total_expected_gain += year_change
        simulated_age += 1

    return total_expected_gain


def calculate_expected_decline_from_peak(current_age, talent=5):
    """
    Calculate the expected total strength loss from peak (age 27) to current age.

    This simulates how much a player would decline due to aging.
    Uses average/expected values (not random) for predictable calculation.

    Args:
        current_age: Player's current age
        talent: Player's talent rating (1-10), affects decline speed

    Returns:
        float: Expected total strength loss from peak to current age (positive number)
    """
    if current_age <= 27:
        # Not past peak yet
        return 0.0

    # We'll simulate year by year with AVERAGE values (no randomness)
    total_expected_decline = 0.0
    simulated_age = 27

    # Get talent multiplier
    talent_mult = calculate_talent_multiplier(talent)

    # Simulate decline year by year from peak (27) to current age
    while simulated_age < current_age:
        # Get age factor (use average of the random ranges)
        if simulated_age < 28:
            age_factor = 0.05  # Average of peak years (-0.2 to 0.3)
        elif simulated_age < 30:
            age_factor = -0.35  # Average of (-0.5 to -0.2)
        elif simulated_age < 32:
            age_factor = -0.75  # Average of (-1.0 to -0.5)
        elif simulated_age < 35:
            age_factor = -1.25  # Average of (-1.5 to -1.0)
        else:
            age_factor = -1.75  # Average of (-2.0 to -1.5)

        # Decline is affected by talent (high talent = slower decline)
        year_decline = age_factor * talent_mult

        total_expected_decline += abs(year_decline)  # Make it positive
        simulated_age += 1

    return total_expected_decline


def calculate_peak_strength_from_talent(talent, base_strength=10):
    """
    Calculate expected peak strength based on talent.

    NEW UNIFIED SYSTEM: Talent determines peak strength, not team level.
    All young players start with similar low strength (around 10) and develop
    based on their talent.

    Args:
        talent: Player's talent rating (1-10)
        base_strength: Starting strength for young players (default 10)

    Returns:
        int: Expected peak strength at age 27
    """
    # Calculate expected development from base to peak
    expected_dev = calculate_expected_development_years_to_peak(10, talent)

    # Peak = base + development
    peak_strength = int(base_strength + expected_dev)

    # Cap at 99
    return min(99, max(1, peak_strength))


def calculate_talent_from_peak_strength(peak_strength):
    """
    Calculate a player's talent based on their expected peak strength.

    NEW: With the new system, talent is the PRIMARY factor determining peak strength.
    This function reverse-engineers talent from a desired peak strength.

    Talent Distribution (based on peak strength):
    - Talent 10: Peak 90-99  (Elite) - develops ~80 points from base ~10
    - Talent 9:  Peak 82-89  (Excellent) - develops ~72-79 points
    - Talent 8:  Peak 74-81  (Very Good) - develops ~64-71 points
    - Talent 7:  Peak 66-73  (Good) - develops ~56-63 points
    - Talent 6:  Peak 58-65  (Above Average) - develops ~48-55 points
    - Talent 5:  Peak 50-57  (Average) - develops ~40-47 points
    - Talent 4:  Peak 42-49  (Below Average) - develops ~32-39 points
    - Talent 3:  Peak 34-41  (Poor) - develops ~24-31 points
    - Talent 2:  Peak 26-33  (Very Poor) - develops ~16-23 points
    - Talent 1:  Peak 1-25   (Minimal) - develops ~0-15 points

    Args:
        peak_strength: Expected strength at peak years (age 27)

    Returns:
        int: Talent rating (1-10)
    """
    # Distribution based on new development system
    if peak_strength >= 90:
        return 10
    elif peak_strength >= 82:
        return 9
    elif peak_strength >= 74:
        return 8
    elif peak_strength >= 66:
        return 7
    elif peak_strength >= 58:
        return 6
    elif peak_strength >= 50:
        return 5
    elif peak_strength >= 42:
        return 4
    elif peak_strength >= 34:
        return 3
    elif peak_strength >= 26:
        return 2
    else:
        return 1


def calculate_current_strength_from_talent_and_age(talent, age, club_bonus=1.0, base_strength_range=(8, 12)):
    """
    UNIFIED SYSTEM: Calculate a player's current strength based on talent and age.

    This is the NEW way to generate young players:
    - Talent determines peak strength (independent of team level)
    - Age determines how far along the development curve they are
    - Young players (10-17) start with similar low strength (8-12)
    - Development is smooth and consistent across all ages

    Args:
        talent: Player's talent rating (1-10)
        age: Player's current age
        club_bonus: Club quality bonus (default 1.0 = no bonus)
        base_strength_range: Range for very young players' starting strength (default 8-12)

    Returns:
        int: Current strength based on talent and age
    """
    import random

    # For very young players (10-13), use a base strength with small variation
    if age <= 13:
        base_strength = random.randint(base_strength_range[0], base_strength_range[1])
        # Calculate how much they've already developed from age 10
        if age > 10:
            development_so_far = 0
            for sim_age in range(10, age):
                age_factor = calculate_age_development_factor(sim_age)
                talent_mult = calculate_talent_multiplier(talent)
                development_so_far += age_factor * talent_mult * club_bonus
            return max(1, int(base_strength + development_so_far))
        return base_strength

    # For older players, calculate from peak strength
    peak_strength = calculate_peak_strength_from_talent(talent, base_strength=10)

    if age >= 27:
        # At or past peak
        if age == 27:
            return peak_strength

        # Calculate decline from peak
        expected_decline = calculate_expected_decline_from_peak(age, talent)
        current_strength = peak_strength - expected_decline
        return max(1, int(current_strength))

    else:
        # Young player (14-26) - calculate remaining development to peak
        expected_development = calculate_expected_development_years_to_peak(age, talent, club_bonus)
        current_strength = peak_strength - expected_development
        return max(1, int(current_strength))


def calculate_age_adjusted_strength(target_strength, age, talent, club_bonus=1.0):
    """
    Calculate what a player's current strength should be, given their target peak strength.

    LEGACY FUNCTION: This is used when generating players based on team_staerke.
    For the new unified system, use calculate_current_strength_from_talent_and_age() instead.

    This "reverse engineers" player generation:
    - target_strength: What the team needs at peak (based on team_staerke)
    - age: Player's current age
    - Returns: What their strength should be NOW based on age

    For young players (< 27): Reduces strength based on expected development to peak
    For peak players (27): Uses target strength directly
    For older players (> 27): Reduces strength based on expected decline from peak

    Args:
        target_strength: The desired strength at peak years (age 27)
        age: Player's current age
        talent: Player's talent rating (1-10)
        club_bonus: Not used anymore, kept for compatibility (default 1.0)

    Returns:
        int: Adjusted strength for current age
    """
    config = get_config()
    min_attr = config.get('player_generation.attributes.min_attribute_value', 1)
    max_attr = config.get('player_generation.attributes.max_attribute_value', 99)

    if age < 27:
        # Young player - calculate how much they would develop from now to peak
        expected_development = calculate_expected_development_years_to_peak(age, talent)

        # Subtract expected development from target to get current strength
        current_strength = target_strength - expected_development

    elif age == 27:
        # At peak - use target strength directly
        current_strength = target_strength

    else:
        # Older player - calculate how much they declined from peak
        expected_decline = calculate_expected_decline_from_peak(age, talent)

        # Subtract expected decline from target to get current strength
        current_strength = target_strength - expected_decline

    # Make sure it's within valid range
    return max(min_attr, min(max_attr, int(round(current_strength))))


def calculate_strength_change(player, club=None):
    """
    Calculate how much a player's strength should change this season.

    Combines age, talent, and randomness to determine development.

    Formula: Strength Change = Age Factor × Talent Multiplier × Randomness

    Args:
        player: Player object
        club: Club object (optional, not used but kept for compatibility)

    Returns:
        int: Change in strength (can be positive or negative)
    """
    # Get base development from age
    age_factor = calculate_age_development_factor(player.age)

    # Get talent multiplier (development speed)
    talent_mult = calculate_talent_multiplier(player.talent)

    # Calculate base change
    base_change = age_factor * talent_mult

    # Get config for randomness
    config = get_config()
    randomness_min = config.get('player_generation.development.randomness_min', 0.85)
    randomness_max = config.get('player_generation.development.randomness_max', 1.15)

    # Add randomness (default ±15% variance)
    randomness = random.uniform(randomness_min, randomness_max)
    final_change = base_change * randomness

    # Round to integer
    return round(final_change)


def develop_single_attribute(current_value, strength_change, attribute_name, current_strength):
    """
    Develop a single player attribute based on strength change.

    NEW: Attributes now maintain their relationship to strength during development.
    Instead of developing at a fixed rate, they stay proportional to current strength.

    This prevents the problem where young players with low starting attributes
    (e.g., 36 for strength 10) reach the maximum (99) after years of development.

    Args:
        current_value: Current attribute value
        strength_change: How much strength changed
        attribute_name: Name of the attribute (for specific adjustments)
        current_strength: Player's current strength (before change)

    Returns:
        int: New attribute value (clamped to 1-99)
    """
    # Get config
    config = get_config()
    min_attr = config.get('player_generation.attributes.min_attribute_value', 1)
    max_attr = config.get('player_generation.attributes.max_attribute_value', 99)
    attr_base_offset = config.get('player_generation.attributes.attr_base_value_offset', 60)
    attr_strength_factor = config.get('player_generation.attributes.attr_strength_factor', 0.6)

    # Calculate what the attribute SHOULD be based on the NEW strength
    # This maintains the relationship: attr = 60 + (strength - 50) * 0.6
    new_strength = current_strength + strength_change
    target_attr_value = attr_base_offset + (new_strength - 50) * attr_strength_factor

    # Add some randomness to create natural variation (±10% of the change)
    # This prevents all attributes from being identical
    change_amount = target_attr_value - current_value
    randomness = random.uniform(0.9, 1.1)
    adjusted_change = change_amount * randomness

    # Apply change
    new_value = current_value + adjusted_change

    # Clamp to valid range (from config)
    return max(min_attr, min(max_attr, int(round(new_value))))


def develop_player(player):
    """
    Develop all attributes for a single player.

    This is the main function called during season transitions.
    Updates player's strength and all other attributes.

    Args:
        player: Player object to develop

    Returns:
        dict: Summary of changes made
    """
    # Get config
    config = get_config()
    min_attr = config.get('player_generation.attributes.min_attribute_value', 1)
    max_attr = config.get('player_generation.attributes.max_attribute_value', 99)

    # Store original values for reporting
    original_strength = player.strength

    # Calculate strength change
    strength_change = calculate_strength_change(player)

    # Apply strength change
    new_strength = player.strength + strength_change
    new_strength = max(min_attr, min(max_attr, new_strength))  # Clamp to valid range
    player.strength = new_strength

    # Develop all other attributes proportionally
    attributes_to_develop = [
        'ausdauer', 'konstanz', 'drucksicherheit',
        'volle', 'raeumer', 'sicherheit',
        'auswaerts', 'start', 'mitte', 'schluss'
    ]

    attribute_changes = {}
    for attr_name in attributes_to_develop:
        current_value = getattr(player, attr_name, 70)
        # Pass current_strength (before change) to maintain proportional relationship
        new_value = develop_single_attribute(current_value, strength_change, attr_name, original_strength)
        setattr(player, attr_name, new_value)
        attribute_changes[attr_name] = new_value - current_value

    # Return summary
    return {
        'player_id': player.id,
        'player_name': player.name,
        'age': player.age,
        'talent': player.talent,
        'strength_change': new_strength - original_strength,
        'old_strength': original_strength,
        'new_strength': new_strength,
        'attribute_changes': attribute_changes
    }


def develop_all_players():
    """
    Develop all active (non-retired) players in the database.

    This function should be called during season transitions.

    Returns:
        dict: Summary statistics of player development
    """
    # Check if development is enabled
    config = get_config()
    if not config.get('player_generation.development.enabled', True):
        print("Player development is disabled in config")
        return {
            'total_players': 0,
            'improved': 0,
            'declined': 0,
            'unchanged': 0,
            'total_strength_gained': 0,
            'total_strength_lost': 0,
            'biggest_improvement': None,
            'biggest_decline': None
        }

    print("\n" + "="*60)
    print("PLAYER DEVELOPMENT SYSTEM")
    print("="*60)

    # Get all active players
    players = Player.query.filter_by(is_retired=False).all()

    # Track statistics
    stats = {
        'total_players': len(players),
        'improved': 0,
        'declined': 0,
        'unchanged': 0,
        'total_strength_gained': 0,
        'total_strength_lost': 0,
        'biggest_improvement': None,
        'biggest_decline': None
    }

    # Develop each player
    development_results = []
    for player in players:
        result = develop_player(player)
        development_results.append(result)

        # Update statistics
        strength_change = result['strength_change']
        if strength_change > 0:
            stats['improved'] += 1
            stats['total_strength_gained'] += strength_change
            if stats['biggest_improvement'] is None or strength_change > stats['biggest_improvement']['change']:
                stats['biggest_improvement'] = {
                    'player': result['player_name'],
                    'age': result['age'],
                    'talent': result['talent'],
                    'change': strength_change,
                    'old': result['old_strength'],
                    'new': result['new_strength']
                }
        elif strength_change < 0:
            stats['declined'] += 1
            stats['total_strength_lost'] += abs(strength_change)
            if stats['biggest_decline'] is None or strength_change < stats['biggest_decline']['change']:
                stats['biggest_decline'] = {
                    'player': result['player_name'],
                    'age': result['age'],
                    'talent': result['talent'],
                    'change': strength_change,
                    'old': result['old_strength'],
                    'new': result['new_strength']
                }
        else:
            stats['unchanged'] += 1

    # Commit all changes
    db.session.commit()

    # Print summary
    print(f"\nDevelopment Summary:")
    print(f"  Total players: {stats['total_players']}")
    print(f"  Improved: {stats['improved']} players (+{stats['total_strength_gained']} total strength)")
    print(f"  Declined: {stats['declined']} players (-{stats['total_strength_lost']} total strength)")
    print(f"  Unchanged: {stats['unchanged']} players")

    if stats['biggest_improvement']:
        imp = stats['biggest_improvement']
        print(f"\n  Biggest improvement: {imp['player']} (Age {imp['age']}, Talent {imp['talent']})")
        print(f"    {imp['old']} → {imp['new']} ({imp['change']:+d})")

    if stats['biggest_decline']:
        dec = stats['biggest_decline']
        print(f"\n  Biggest decline: {dec['player']} (Age {dec['age']}, Talent {dec['talent']})")
        print(f"    {dec['old']} → {dec['new']} ({dec['change']:+d})")

    print("="*60 + "\n")

    return stats



def save_player_history_snapshot():
    """
    Save a snapshot of all active players' attributes at the end of the current season.

    This function should be called AFTER player development during season transitions.
    It creates a historical record of each player's attributes for tracking development over time.

    Returns:
        int: Number of player history records created
    """
    # Get current season
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        print("Warning: No current season found, cannot save player history")
        return 0

    # Get all active players
    players = Player.query.filter_by(is_retired=False).all()

    records_created = 0
    for player in players:
        # Check if a history record already exists for this player and season
        existing = PlayerHistory.query.filter_by(
            player_id=player.id,
            season_id=current_season.id
        ).first()

        if existing:
            # Update existing record instead of creating duplicate
            existing.player_name = player.name
            existing.age = player.age
            existing.club_id = player.club_id
            existing.club_name = player.club.name if player.club else None
            existing.strength = player.strength
            existing.talent = player.talent
            existing.ausdauer = player.ausdauer
            existing.konstanz = player.konstanz
            existing.drucksicherheit = player.drucksicherheit
            existing.volle = player.volle
            existing.raeumer = player.raeumer
            existing.sicherheit = player.sicherheit
            existing.auswaerts = player.auswaerts
            existing.start = player.start
            existing.mitte = player.mitte
            existing.schluss = player.schluss
        else:
            # Create new history record
            history_record = PlayerHistory(
                player_id=player.id,
                season_id=current_season.id,
                season_name=current_season.name,
                player_name=player.name,
                age=player.age,
                club_id=player.club_id,
                club_name=player.club.name if player.club else None,
                strength=player.strength,
                talent=player.talent,
                ausdauer=player.ausdauer,
                konstanz=player.konstanz,
                drucksicherheit=player.drucksicherheit,
                volle=player.volle,
                raeumer=player.raeumer,
                sicherheit=player.sicherheit,
                auswaerts=player.auswaerts,
                start=player.start,
                mitte=player.mitte,
                schluss=player.schluss
            )
            db.session.add(history_record)
            records_created += 1

    # Commit all history records
    db.session.commit()

    print(f"✓ Saved player history snapshot: {records_created} new records for season '{current_season.name}'")

    return records_created
