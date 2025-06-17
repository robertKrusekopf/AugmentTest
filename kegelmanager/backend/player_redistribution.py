"""
Module for redistributing players within clubs based on their strength.
This ensures that the strongest players are assigned to the highest teams.
"""

from models import db, Player, Team, Club
from sqlalchemy import func


def calculate_player_rating(player):
    """
    Calculate a weighted rating for a player based on their attributes.
    Uses the same formula as in club_player_assignment.py for consistency,
    but adds a youth bonus for players under 25 years old.

    Args:
        player: Player object

    Returns:
        float: Weighted rating of the player including youth bonus
    """
    base_rating = (
        player.strength * 0.5 +      # 50% weight on strength
        player.konstanz * 0.1 +      # 10% weight on consistency
        player.drucksicherheit * 0.1 + # 10% weight on pressure resistance
        player.volle * 0.15 +        # 15% weight on full pins
        player.raeumer * 0.15        # 15% weight on clearing pins
    )

    # Youth bonus: +1 point for each year under 25
    youth_bonus = 0
    if player.age < 25:
        youth_bonus = 25 - player.age

    return base_rating + youth_bonus


def redistribute_players_by_strength():
    """
    Redistribute all players within clubs based on their strength.

    IMPORTANT: This function should only be called between seasons or during initial setup,
    never during an active season, as it changes permanent team assignments.

    For clubs with multiple teams:
    - All players are sorted by strength (using weighted rating)
    - Players are redistributed to teams based on team league level
    - Best players go to highest team (lowest league level number)
    - Players are distributed fairly: if uneven, highest team gets one extra

    Example with 22 players and 3 teams:
    - Team 1 (highest): 8 best players
    - Team 2 (middle): 7 next best players
    - Team 3 (lowest): 7 remaining players
    """
    print("Starting player redistribution by strength...")
    print("WARNING: This changes permanent team assignments and should only be used between seasons!")

    # Find all clubs that have multiple teams
    clubs_with_multiple_teams = db.session.query(Club).join(Team).group_by(Club.id).having(func.count(Team.id) > 1).all()

    if not clubs_with_multiple_teams:
        print("No clubs with multiple teams found. Redistribution not needed.")
        return

    print(f"Found {len(clubs_with_multiple_teams)} clubs with multiple teams")

    redistributed_clubs = 0
    total_players_moved = 0
    
    for club in clubs_with_multiple_teams:
        print(f"\nProcessing club: {club.name}")
        
        # Get all teams for this club, sorted by league level (lower = higher league)
        # Teams without league go to the end
        teams = Team.query.filter_by(club_id=club.id).all()
        teams.sort(key=lambda t: (t.league.level if t.league else 999))
        
        if len(teams) < 2:
            continue
            
        team_info = [f"{team.name} (Level {team.league.level if team.league else 'N/A'})" for team in teams]
        print(f"  Teams: {team_info}")
        
        # Get all players for this club
        players = Player.query.filter_by(club_id=club.id).all()
        
        if len(players) < len(teams):
            print(f"  Warning: Only {len(players)} players for {len(teams)} teams. Skipping redistribution.")
            continue
            
        print(f"  Total players: {len(players)}")
        
        # Sort players by rating (best first)
        players.sort(key=calculate_player_rating, reverse=True)
        
        # Calculate how many players each team should get
        players_per_team = len(players) // len(teams)
        extra_players = len(players) % len(teams)
        
        print(f"  Base players per team: {players_per_team}, Extra players for top teams: {extra_players}")
        
        # Clear current team associations
        for player in players:
            player.teams.clear()
        
        # Redistribute players to teams
        player_index = 0
        players_moved_this_club = 0
        
        for i, team in enumerate(teams):
            # Calculate how many players this team should get
            team_player_count = players_per_team
            if i < extra_players:  # Give extra players to highest teams first
                team_player_count += 1
            
            print(f"    Assigning {team_player_count} players to {team.name}")
            
            # Assign players to this team
            for j in range(team_player_count):
                if player_index < len(players):
                    player = players[player_index]
                    player.teams.append(team)
                    print(f"      {player.name} (Rating: {calculate_player_rating(player):.1f})")
                    player_index += 1
                    players_moved_this_club += 1
        
        total_players_moved += players_moved_this_club
        redistributed_clubs += 1
        print(f"  Redistributed {players_moved_this_club} players in {club.name}")
    
    # Commit all changes
    try:
        db.session.commit()
        print(f"\nPlayer redistribution completed successfully!")
        print(f"Redistributed {total_players_moved} players across {redistributed_clubs} clubs")
    except Exception as e:
        db.session.rollback()
        print(f"Error during player redistribution: {str(e)}")
        raise


def redistribute_club_players_by_strength(club_id):
    """
    Redistribute players within a specific club based on their strength.
    
    Args:
        club_id: ID of the club to redistribute players for
    """
    print(f"Redistributing players for club ID: {club_id}")
    
    club = Club.query.get(club_id)
    if not club:
        print(f"Club with ID {club_id} not found")
        return
    
    # Get all teams for this club, sorted by league level (lower = higher league)
    # Teams without league go to the end
    teams = Team.query.filter_by(club_id=club_id).all()
    teams.sort(key=lambda t: (t.league.level if t.league else 999))
    
    if len(teams) < 2:
        print(f"Club {club.name} has only {len(teams)} team(s). No redistribution needed.")
        return
    
    # Get all players for this club
    players = Player.query.filter_by(club_id=club_id).all()
    
    if len(players) < len(teams):
        print(f"Warning: Only {len(players)} players for {len(teams)} teams in {club.name}. Skipping redistribution.")
        return
    
    print(f"Redistributing {len(players)} players across {len(teams)} teams in {club.name}")
    
    # Sort players by rating (best first)
    players.sort(key=calculate_player_rating, reverse=True)
    
    # Calculate how many players each team should get
    players_per_team = len(players) // len(teams)
    extra_players = len(players) % len(teams)
    
    # Clear current team associations
    for player in players:
        player.teams.clear()
    
    # Redistribute players to teams
    player_index = 0
    
    for i, team in enumerate(teams):
        # Calculate how many players this team should get
        team_player_count = players_per_team
        if i < extra_players:  # Give extra players to highest teams first
            team_player_count += 1
        
        print(f"  Assigning {team_player_count} players to {team.name}")
        
        # Assign players to this team
        for j in range(team_player_count):
            if player_index < len(players):
                player = players[player_index]
                player.teams.append(team)
                player_index += 1
    
    try:
        db.session.commit()
        print(f"Successfully redistributed players in {club.name}")
    except Exception as e:
        db.session.rollback()
        print(f"Error redistributing players in {club.name}: {str(e)}")
        raise


def initial_player_distribution():
    """
    Perform initial player distribution after player generation.

    This function should only be called once after initial player generation
    to ensure that the strongest players are assigned to the highest teams.

    Unlike redistribute_players_by_strength(), this function is designed to work
    with the current game system that uses dynamic player assignments for matches.
    """
    print("Performing initial player distribution after generation...")
    print("Note: This sets initial team assignments for UI display purposes.")
    print("The game will still use dynamic assignment for actual matches.")

    # Find all clubs that have multiple teams
    clubs_with_multiple_teams = db.session.query(Club).join(Team).group_by(Club.id).having(func.count(Team.id) > 1).all()

    if not clubs_with_multiple_teams:
        print("No clubs with multiple teams found. Initial distribution not needed.")
        return

    print(f"Found {len(clubs_with_multiple_teams)} clubs with multiple teams")

    redistributed_clubs = 0
    total_players_assigned = 0

    for club in clubs_with_multiple_teams:
        print(f"\nProcessing club: {club.name}")

        # Get all teams for this club, sorted by league level (lower = higher league)
        teams = Team.query.filter_by(club_id=club.id).all()
        teams.sort(key=lambda t: (t.league.level if t.league else 999))

        if len(teams) < 2:
            continue

        team_info = [f"{team.name} (Level {team.league.level if team.league else 'N/A'})" for team in teams]
        print(f"  Teams: {team_info}")

        # Get all players for this club
        players = Player.query.filter_by(club_id=club.id).all()

        if len(players) < len(teams):
            print(f"  Warning: Only {len(players)} players for {len(teams)} teams. Skipping distribution.")
            continue

        print(f"  Total players: {len(players)}")

        # Sort players by rating (best first)
        players.sort(key=calculate_player_rating, reverse=True)

        # Calculate how many players each team should get
        players_per_team = len(players) // len(teams)
        extra_players = len(players) % len(teams)

        print(f"  Base players per team: {players_per_team}, Extra players for top teams: {extra_players}")

        # Clear current team associations (in case there are any)
        for player in players:
            player.teams.clear()

        # Assign players to teams for UI display
        player_index = 0
        players_assigned_this_club = 0

        for i, team in enumerate(teams):
            # Calculate how many players this team should get
            team_player_count = players_per_team
            if i < extra_players:  # Give extra players to highest teams first
                team_player_count += 1

            print(f"    Assigning {team_player_count} players to {team.name}")

            # Assign players to this team
            for j in range(team_player_count):
                if player_index < len(players):
                    player = players[player_index]
                    player.teams.append(team)
                    print(f"      {player.name} (Rating: {calculate_player_rating(player):.1f})")
                    player_index += 1
                    players_assigned_this_club += 1

        total_players_assigned += players_assigned_this_club
        redistributed_clubs += 1
        print(f"  Assigned {players_assigned_this_club} players in {club.name}")

    # Commit all changes
    try:
        db.session.commit()
        print(f"\nInitial player distribution completed successfully!")
        print(f"Assigned {total_players_assigned} players across {redistributed_clubs} clubs")
        print("\nIMPORTANT: These assignments are for UI display only.")
        print("The game uses dynamic player assignment for actual matches based on availability and strength.")
    except Exception as e:
        db.session.rollback()
        print(f"Error during initial player distribution: {str(e)}")
        raise
