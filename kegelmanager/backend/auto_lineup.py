"""
Module for automatically creating lineups for AI-controlled teams.
"""
from models import db, Player, Team, UserLineup, LineupPosition, Match
import random

def randomize_player_positions(available_players):
    """
    Randomly assign positions to the 6 selected players.

    Args:
        available_players: List of available players

    Returns:
        dict: Dictionary mapping position numbers (1-6) to players
    """
    # If we have 6 or fewer players, use all of them
    if len(available_players) <= 6:
        players_to_position = available_players[:]
    else:
        # If we have more than 6 players, select the best 6 based on overall rating
        from simulation import calculate_player_rating
        available_players.sort(key=calculate_player_rating, reverse=True)
        players_to_position = available_players[:6]

    # Filter out None values (real players only)
    real_players = [p for p in players_to_position if p is not None]

    if len(real_players) == 0:
        # No real players available
        return {i: None for i in range(1, 7)}

    # Randomly shuffle the real players
    random.shuffle(real_players)

    # Create position mapping
    positions = {}
    for i in range(6):
        if i < len(real_players):
            positions[i + 1] = real_players[i]
        else:
            positions[i + 1] = None

    return positions

def optimize_player_positions(available_players):
    """
    Optimize player positions based on their Start/Mitte/Schluss attributes.

    Args:
        available_players: List of available players

    Returns:
        dict: Dictionary mapping position numbers (1-6) to players
    """
    # If we have 6 or fewer players, use all of them
    if len(available_players) <= 6:
        players_to_position = available_players
    else:
        # If we have more than 6 players, select the best 6 based on overall rating
        from simulation import calculate_player_rating
        available_players.sort(key=calculate_player_rating, reverse=True)
        players_to_position = available_players[:6]

    # If we have fewer than 6 players, fill remaining positions with None
    # (Stroh players will be handled during simulation)
    while len(players_to_position) < 6:
        players_to_position.append(None)

    # Use the centralized position scoring function
    from simulation import calculate_position_score as central_position_score

    def calculate_position_score(player, position):
        """Calculate how well a player fits a specific position (1-6)."""
        if player is None:
            return 0

        # Use the centralized function for consistency
        return central_position_score(player, position)

    # Find the optimal assignment using a greedy approach
    # For small teams (6 players), we can afford to check all permutations
    # For efficiency, we'll use a greedy approach that should work well

    real_players = [p for p in players_to_position if p is not None]

    if len(real_players) == 0:
        # No real players available
        return {i: None for i in range(1, 7)}

    # Calculate scores for all player-position combinations
    position_scores = {}
    for player in real_players:
        for position in range(1, 7):
            position_scores[(player.id, position)] = calculate_position_score(player, position)

    # Use greedy assignment: assign each position to the best available player
    assigned_players = set()
    optimal_positions = {}

    # Sort positions by importance: Start (1,2), Mitte (3,4), Schluss (5,6)
    position_order = [1, 2, 3, 4, 5, 6]

    for position in position_order:
        best_player = None
        best_score = -1

        for player in real_players:
            if player.id not in assigned_players:
                score = position_scores[(player.id, position)]
                if score > best_score:
                    best_score = score
                    best_player = player

        if best_player:
            optimal_positions[position] = best_player
            assigned_players.add(best_player.id)
        else:
            optimal_positions[position] = None

    return optimal_positions

def create_auto_lineup_for_team(match_id, team_id, is_home_team):
    """
    Create an automatic lineup for a team.
    
    Args:
        match_id: The ID of the match
        team_id: The ID of the team
        is_home_team: Whether the team is the home team
        
    Returns:
        UserLineup: The created lineup object, or None if creation failed
    """
    # Check if a lineup already exists
    existing_lineup = UserLineup.query.filter_by(
        match_id=match_id,
        team_id=team_id,
        is_home_team=is_home_team
    ).first()
    
    if existing_lineup:
        return existing_lineup
    
    # Get the team
    team = Team.query.get(team_id)
    if not team:
        return None
    
    # Get all active (non-retired) players from the club
    club_players = Player.query.filter_by(club_id=team.club_id, is_retired=False).all()
    if not club_players or len(club_players) < 6:
        return None

    # Build detailed team information for proper availability calculation
    # This ensures consistency with automatic simulation logic
    clubs_with_matches = {team.club_id}
    teams_playing = {team.club_id: 1}
    playing_teams_info = {
        team.club_id: [{
            'id': team.id,
            'name': team.name,
            'league_level': team.league.level if team.league else 999
        }]
    }

    # Use centralized player availability determination with proper context
    from performance_optimizations import batch_set_player_availability
    batch_set_player_availability(clubs_with_matches, teams_playing, playing_teams_info)

    # Get available players after availability determination
    available_players = [p for p in club_players if p.is_available_current_matchday]
    if len(available_players) < 6:
        # Note that Stroh players will be needed
        stroh_players_needed = 6 - len(available_players)
        print(f"Auto lineup: Only {len(available_players)} players available for team {team_id}, will need {stroh_players_needed} Stroh player(s) during simulation")

        # If we have no players at all, we can't create a lineup
        if len(available_players) == 0:
            return None

    # Randomly assign positions to the selected players
    random_positions = randomize_player_positions(available_players)

    # Create a new lineup
    lineup = UserLineup(
        match_id=match_id,
        team_id=team_id,
        is_home_team=is_home_team
    )
    db.session.add(lineup)
    db.session.flush()  # Get the ID for the new lineup

    # Add the positions based on random positioning
    for position_number, player in random_positions.items():
        if player is not None:  # Only add positions for real players
            position = LineupPosition(
                lineup_id=lineup.id,
                player_id=player.id,
                position_number=position_number
            )
            db.session.add(position)
    
    # Save changes to database
    db.session.commit()

    return lineup

def ensure_home_team_lineup_exists(match_id):
    """
    Ensure that the home team has a lineup for the given match.
    If no lineup exists, create one automatically.
    
    Args:
        match_id: The ID of the match
        
    Returns:
        bool: True if a lineup exists or was created, False otherwise
    """
    # Get the match
    match = Match.query.get(match_id)
    if not match:
        return False
    
    # Check if the home team already has a lineup
    home_lineup = UserLineup.query.filter_by(
        match_id=match_id,
        team_id=match.home_team_id,
        is_home_team=True
    ).first()
    
    if home_lineup:
        return True
    
    # Create an automatic lineup for the home team
    home_lineup = create_auto_lineup_for_team(match_id, match.home_team_id, True)
    
    return home_lineup is not None
