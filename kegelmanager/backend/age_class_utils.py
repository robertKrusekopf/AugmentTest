"""
Utility functions for age class management and player-team assignment validation.
"""


def get_age_class_hierarchy():
    """
    Returns the age class hierarchy from youngest to oldest.
    
    Returns:
        list: List of tuples (altersklasse, min_age, max_age) ordered from youngest to oldest
    """
    return [
        ('F', 7, 8),
        ('E', 9, 10),
        ('D', 11, 12),
        ('C', 13, 14),
        ('B', 15, 16),
        ('A', 17, 18),
        ('Herren', 18, 35),
    ]


def get_minimum_altersklasse_for_age(age):
    """
    Determines the minimum (youngest) age class a player of given age can be assigned to.
    
    A player can only be assigned to teams whose age class is equal to or older than
    the player's age class.
    
    Args:
        age: Player's age
        
    Returns:
        str: The minimum age class (e.g., 'D', 'C', 'B', 'A', 'Herren')
             Returns 'Herren' if age is outside all youth ranges
    
    Examples:
        - Age 10 -> 'E' (can play in E, D, C, B, A, or Herren)
        - Age 15 -> 'B' (can play in B, A, or Herren)
        - Age 20 -> 'Herren' (can only play in Herren)
    """
    hierarchy = get_age_class_hierarchy()
    
    # Find the age class that matches the player's age
    for altersklasse, min_age, max_age in hierarchy:
        if min_age <= age <= max_age:
            return altersklasse
    
    # If age is outside all ranges, default to Herren
    return 'Herren'


def get_allowed_altersklassen_for_age(age):
    """
    Returns all age classes a player of given age is allowed to play in.
    
    Args:
        age: Player's age
        
    Returns:
        list: List of allowed age class strings (e.g., ['E', 'D', 'C', 'B', 'A', 'Herren'])
    
    Examples:
        - Age 10 -> ['E', 'D', 'C', 'B', 'A', 'Herren']
        - Age 15 -> ['B', 'A', 'Herren']
        - Age 20 -> ['Herren']
    """
    min_class = get_minimum_altersklasse_for_age(age)
    hierarchy = get_age_class_hierarchy()
    
    # Find the index of the minimum class
    min_index = None
    for i, (altersklasse, _, _) in enumerate(hierarchy):
        if altersklasse == min_class:
            min_index = i
            break
    
    if min_index is None:
        return ['Herren']
    
    # Return all classes from min_class onwards (older classes)
    return [altersklasse for altersklasse, _, _ in hierarchy[min_index:]]


def is_player_allowed_in_team(player_age, team_altersklasse):
    """
    Checks if a player of given age is allowed to be assigned to a team with given age class.
    
    Args:
        player_age: Player's age
        team_altersklasse: Team's league age class (e.g., 'B', 'C', 'Herren')
        
    Returns:
        bool: True if player is allowed, False otherwise
    
    Examples:
        - is_player_allowed_in_team(15, 'B') -> True (15-year-old can play in B-Jugend)
        - is_player_allowed_in_team(15, 'C') -> False (15-year-old is too old for C-Jugend)
        - is_player_allowed_in_team(15, 'A') -> True (15-year-old can play in A-Jugend)
        - is_player_allowed_in_team(15, 'Herren') -> True (15-year-old can play in Herren)
    """
    if not team_altersklasse:
        # If team has no age class, assume Herren (allow all ages)
        return True
    
    # Normalize team_altersklasse to short form
    team_class_normalized = normalize_altersklasse(team_altersklasse)
    
    # Get allowed classes for this player
    allowed_classes = get_allowed_altersklassen_for_age(player_age)
    
    return team_class_normalized in allowed_classes


def normalize_altersklasse(altersklasse):
    """
    Normalizes age class to short form (e.g., 'B-Jugend' -> 'B', 'b jugend' -> 'B').

    Args:
        altersklasse: Age class string in any format

    Returns:
        str: Normalized age class ('F', 'E', 'D', 'C', 'B', 'A', or 'Herren')
    """
    if not altersklasse:
        return 'Herren'

    altersklasse_lower = altersklasse.lower().strip()

    # Check for exact single letter first
    if altersklasse_lower == 'f':
        return 'F'
    elif altersklasse_lower == 'e':
        return 'E'
    elif altersklasse_lower == 'd':
        return 'D'
    elif altersklasse_lower == 'c':
        return 'C'
    elif altersklasse_lower == 'b':
        return 'B'
    elif altersklasse_lower == 'a':
        return 'A'

    # Check for long forms with 'jugend'
    if 'jugend' in altersklasse_lower:
        if 'f-jugend' in altersklasse_lower or 'f jugend' in altersklasse_lower:
            return 'F'
        elif 'e-jugend' in altersklasse_lower or 'e jugend' in altersklasse_lower:
            return 'E'
        elif 'd-jugend' in altersklasse_lower or 'd jugend' in altersklasse_lower:
            return 'D'
        elif 'c-jugend' in altersklasse_lower or 'c jugend' in altersklasse_lower:
            return 'C'
        elif 'b-jugend' in altersklasse_lower or 'b jugend' in altersklasse_lower:
            return 'B'
        elif 'a-jugend' in altersklasse_lower or 'a jugend' in altersklasse_lower:
            return 'A'

    # Default to Herren
    return 'Herren'


def get_age_class_rank(altersklasse):
    """
    Returns the rank of an age class in the hierarchy (0 = youngest, higher = older).
    
    Args:
        altersklasse: Age class string
        
    Returns:
        int: Rank in hierarchy (0-6), or 6 (Herren) if not found
    """
    normalized = normalize_altersklasse(altersklasse)
    hierarchy = get_age_class_hierarchy()
    
    for i, (age_class, _, _) in enumerate(hierarchy):
        if age_class == normalized:
            return i
    
    return 6  # Default to Herren rank


def find_suitable_team_for_player(player_age, available_teams):
    """
    Finds the most suitable team for a player based on age class matching.
    
    Prefers teams that match the player's age class, but will select older teams if needed.
    
    Args:
        player_age: Player's age
        available_teams: List of Team objects with league.altersklasse
        
    Returns:
        Team: The most suitable team, or None if no suitable team found
    """
    if not available_teams:
        return None
    
    # Get player's minimum age class
    min_class = get_minimum_altersklasse_for_age(player_age)
    min_rank = get_age_class_rank(min_class)
    
    # Filter teams by allowed age classes
    suitable_teams = []
    for team in available_teams:
        if team.league and team.league.altersklasse:
            team_rank = get_age_class_rank(team.league.altersklasse)
            # Team must be same age or older (higher rank)
            if team_rank >= min_rank:
                suitable_teams.append((team, team_rank))
        else:
            # Teams without age class (assume Herren) are always suitable
            suitable_teams.append((team, 6))
    
    if not suitable_teams:
        return None
    
    # Sort by rank (prefer teams closest to player's age class)
    suitable_teams.sort(key=lambda x: x[1])
    
    return suitable_teams[0][0]

