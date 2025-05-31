"""
Module for automatically creating lineups for AI-controlled teams.
"""
from models import db, Player, Team, UserLineup, LineupPosition, Match
import random

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
        print(f"Lineup already exists for team {team_id} in match {match_id}")
        return existing_lineup
    
    # Get the team
    team = Team.query.get(team_id)
    if not team:
        print(f"Team with ID {team_id} not found")
        return None
    
    # Get all players from the club
    club_players = Player.query.filter_by(club_id=team.club_id).all()
    if not club_players or len(club_players) < 6:
        print(f"Not enough players found for club ID {team.club_id}")
        return None
    
    # Reset player availability flags for this club
    for player in club_players:
        player.is_available_current_matchday = True
    
    # Determine player availability (16.7% chance of being unavailable)
    unavailable_players = []
    for player in club_players:
        # 16.7% chance of being unavailable
        if random.random() < 0.167:
            player.is_available_current_matchday = False
            unavailable_players.append(player.id)
    
    # Make sure we have at least 6 available players
    available_players = [p for p in club_players if p.is_available_current_matchday]
    if len(available_players) < 6:
        # Make some unavailable players available again
        players_needed = 6 - len(available_players)
        players_to_make_available = random.sample(unavailable_players, min(players_needed, len(unavailable_players)))
        for player_id in players_to_make_available:
            for player in club_players:
                if player.id == player_id:
                    player.is_available_current_matchday = True
                    break
    
    # Get available players again after making some available
    available_players = [p for p in club_players if p.is_available_current_matchday]
    
    # Sort players by a weighted rating of their attributes
    def player_rating(player):
        return (
            player.strength * 0.5 +  # 50% weight on strength
            player.konstanz * 0.1 +   # 10% weight on consistency
            player.drucksicherheit * 0.1 +  # 10% weight on pressure resistance
            player.volle * 0.15 +     # 15% weight on full pins
            player.raeumer * 0.15     # 15% weight on clearing pins
        )
    
    available_players.sort(key=player_rating, reverse=True)
    
    # Take the top 6 players
    selected_players = available_players[:6]
    
    # Create a new lineup
    lineup = UserLineup(
        match_id=match_id,
        team_id=team_id,
        is_home_team=is_home_team
    )
    db.session.add(lineup)
    db.session.flush()  # Get the ID for the new lineup
    
    # Add the positions
    for i, player in enumerate(selected_players):
        position = LineupPosition(
            lineup_id=lineup.id,
            player_id=player.id,
            position_number=i + 1
        )
        db.session.add(position)
    
    # Save changes to database
    db.session.commit()
    
    print(f"Auto lineup created for team {team.name} (ID: {team_id}) in match {match_id}")
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
        print(f"Match with ID {match_id} not found")
        return False
    
    # Check if the home team already has a lineup
    home_lineup = UserLineup.query.filter_by(
        match_id=match_id,
        team_id=match.home_team_id,
        is_home_team=True
    ).first()
    
    if home_lineup:
        print(f"Home team already has a lineup for match {match_id}")
        return True
    
    # Create an automatic lineup for the home team
    home_lineup = create_auto_lineup_for_team(match_id, match.home_team_id, True)
    
    return home_lineup is not None
