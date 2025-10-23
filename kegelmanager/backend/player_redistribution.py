"""
Module for redistributing players within clubs based on their strength and age class.

This module ensures that the strongest players are assigned to the highest teams
while respecting age class (Altersklasse) restrictions.

MAIN FUNCTIONS:
- redistribute_players_by_strength_and_age(): Redistribute all players in all clubs
- redistribute_club_players_by_strength_and_age(club_id): Redistribute players in one club

AGE CLASS RULES:
Players can only be assigned to teams whose league age class is equal to or older
than the player's age class.

Example: A 15-year-old (B-Jugend) can play in B, A, or Herren teams,
         but NOT in C, D, E, or F teams (too young for those classes).

LEGACY FUNCTIONS (deprecated, kept for backward compatibility):
- initial_player_distribution(): Now calls redistribute_players_by_strength_and_age()
- redistribute_players_by_strength(): Now calls redistribute_players_by_strength_and_age()
- redistribute_club_players_by_strength(club_id): Now calls redistribute_club_players_by_strength_and_age()
"""

from models import db, Player, Team, Club
from sqlalchemy import func
from age_class_utils import (
    is_player_allowed_in_team,
    get_minimum_altersklasse_for_age,
    get_age_class_rank,
    normalize_altersklasse
)


def calculate_player_rating(player):
    """
    Calculate a weighted rating for a player based on their attributes.
    Uses the centralized function with youth bonus for redistribution.

    Args:
        player: Player object

    Returns:
        float: Weighted rating of the player including youth bonus
    """
    from simulation import calculate_player_rating as base_rating_func
    return base_rating_func(player, include_youth_bonus=True)


def redistribute_players_by_strength_and_age():
    """
    Redistribute all players within clubs based on their strength AND age class.

    This is the main function for player-team assignment that respects age class restrictions.

    Use cases:
    - Initial player distribution after database generation
    - Manual redistribution between seasons
    - Fixing incorrect player assignments

    IMPORTANT: This function changes permanent team assignments. Safe to use during:
    - Initial database setup
    - Between seasons
    NOT safe during an active season (would disrupt ongoing matches).

    For clubs with multiple teams:
    - Teams are sorted by age class (oldest first), then by league level (best first)
    - Players are first filtered by age class eligibility
    - Within eligible teams, players are sorted by strength (using weighted rating)
    - Best eligible players go to highest eligible team (oldest age class, lowest league level number)
    - Players are distributed fairly: if uneven, highest team gets one extra

    Age class rules:
    - Players can only be assigned to teams whose age class is equal to or older
    - Example: A 15-year-old (B-Jugend) can play in B, A, or Herren teams, but NOT in C, D, E, or F teams

    Team sorting example (Herren Level 1, Herren Level 2, A-Jugend Level 1, B-Jugend Level 1):
    1. Herren Level 1 (oldest age class, best league)
    2. Herren Level 2 (oldest age class, second best league)
    3. A-Jugend Level 1 (second oldest age class, best league)
    4. B-Jugend Level 1 (third oldest age class, best league)
    """
    print("Starting player redistribution by strength and age class...")
    print("Note: This sets team assignments for UI display. Dynamic assignment is used for actual matches.")

    # Find all clubs that have teams
    clubs_with_teams = db.session.query(Club).join(Team).group_by(Club.id).having(func.count(Team.id) >= 1).all()

    if not clubs_with_teams:
        print("No clubs with teams found. Redistribution not needed.")
        return

    print(f"Found {len(clubs_with_teams)} clubs with teams")

    redistributed_clubs = 0
    total_players_moved = 0

    for club in clubs_with_teams:
        print(f"\nProcessing club: {club.name}")

        # Get all teams for this club, sorted by age class rank (oldest first), then by league level
        teams = Team.query.filter_by(club_id=club.id).all()

        # Sort teams: first by age class rank (oldest to youngest), then by league level (higher to lower)
        def team_sort_key(t):
            if t.league and t.league.altersklasse:
                age_rank = get_age_class_rank(t.league.altersklasse)
            else:
                age_rank = 6  # Herren rank for teams without age class
            league_level = t.league.level if t.league else 999
            # Sort by age_rank descending (oldest first), then by league_level ascending (best league first)
            return (-age_rank, league_level)

        teams.sort(key=team_sort_key)

        if len(teams) == 0:
            continue

        team_info = []
        for team in teams:
            level = team.league.level if team.league else 'N/A'
            age_class = team.league.altersklasse if team.league and team.league.altersklasse else 'Herren'
            team_info.append(f"{team.name} ({age_class}, Level {level})")
        print(f"  Teams: {team_info}")

        # Get all players for this club (exclude retired players)
        players = Player.query.filter_by(club_id=club.id, is_retired=False).all()

        if len(players) == 0:
            print(f"  No players found for {club.name}. Skipping.")
            continue

        print(f"  Total players: {len(players)}")

        # Special case: If club has only one team, assign all eligible players to it
        if len(teams) == 1:
            team = teams[0]
            team_age_class = team.league.altersklasse if team.league and team.league.altersklasse else 'Herren'
            team_age_rank = get_age_class_rank(team_age_class)

            print(f"  Club has only one team. Assigning all eligible players to {team.name}...")

            # Clear current team associations
            for player in players:
                player.teams.clear()

            assigned_count = 0
            for player in players:
                # Check if player is eligible for this team based on age
                if player.age:
                    player_min_class = get_minimum_altersklasse_for_age(player.age)
                    player_age_rank = get_age_class_rank(player_min_class)

                    if player_age_rank <= team_age_rank:
                        player.teams.append(team)
                        assigned_count += 1
                    else:
                        print(f"    WARNING: {player.name} (Age: {player.age}, {player_min_class}) is too young for {team_age_class} team")
                else:
                    # Players without age default to being eligible
                    player.teams.append(team)
                    assigned_count += 1

            print(f"  Assigned {assigned_count} players to {team.name}")
            total_players_moved += assigned_count
            redistributed_clubs += 1
            continue

        # Clear current team associations
        for player in players:
            player.teams.clear()

        # Group players by their minimum age class
        from collections import defaultdict
        players_by_min_class = defaultdict(list)

        for player in players:
            if not player.age:
                # Players without age default to Herren
                min_class = 'Herren'
            else:
                min_class = get_minimum_altersklasse_for_age(player.age)
            players_by_min_class[min_class].append(player)

        # Sort players within each age class by rating (best first)
        for age_class in players_by_min_class:
            players_by_min_class[age_class].sort(key=calculate_player_rating, reverse=True)

        # Assign players to teams using age-class-aware distribution
        players_moved_this_club = 0
        unassigned_players = []

        for team in teams:
            team_age_class = team.league.altersklasse if team.league and team.league.altersklasse else 'Herren'
            team_age_rank = get_age_class_rank(team_age_class)

            print(f"    Assigning players to {team.name} ({team_age_class})...")

            # Find all players eligible for this team (age class equal or younger)
            eligible_players = []
            for age_class, player_list in players_by_min_class.items():
                player_age_rank = get_age_class_rank(age_class)
                # Player can play in this team if their age class rank <= team age class rank
                if player_age_rank <= team_age_rank:
                    eligible_players.extend(player_list)

            # Sort eligible players by rating
            eligible_players.sort(key=calculate_player_rating, reverse=True)

            # Assign best eligible players to this team
            # Target: roughly equal distribution, but respect age constraints
            target_count = max(6, len(players) // len(teams))  # At least 6 players per team
            assigned_count = 0

            for player in eligible_players:
                if assigned_count >= target_count:
                    break
                if len(player.teams) == 0:  # Player not yet assigned
                    player.teams.append(team)
                    print(f"      {player.name} (Age: {player.age}, Rating: {calculate_player_rating(player):.1f})")
                    assigned_count += 1
                    players_moved_this_club += 1

        # Check for unassigned players
        for player in players:
            if len(player.teams) == 0:
                unassigned_players.append(player)

        if unassigned_players:
            print(f"  WARNING: {len(unassigned_players)} players could not be assigned:")
            for player in unassigned_players:
                min_class = get_minimum_altersklasse_for_age(player.age) if player.age else 'Herren'
                print(f"    {player.name} (Age: {player.age}, Min class: {min_class})")

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


def redistribute_players_by_strength():
    """
    Legacy function for backward compatibility.
    Now calls the age-class-aware redistribution function.

    DEPRECATED: Use redistribute_players_by_strength_and_age() instead.
    """
    print("NOTE: redistribute_players_by_strength() is deprecated.")
    print("      Using redistribute_players_by_strength_and_age() instead.")
    return redistribute_players_by_strength_and_age()


def redistribute_club_players_by_strength_and_age(club_id):
    """
    Redistribute players within a specific club based on their strength AND age class.

    Respects age class restrictions: players can only be assigned to teams whose
    league age class is equal to or older than the player's age class.

    Args:
        club_id: ID of the club to redistribute players for
    """
    print(f"Redistributing players for club ID: {club_id} (age-class-aware)")

    club = Club.query.get(club_id)
    if not club:
        print(f"Club with ID {club_id} not found")
        return

    # Get all teams for this club, sorted by age class rank (oldest first), then league level
    teams = Team.query.filter_by(club_id=club_id).all()

    def team_sort_key(t):
        if t.league and t.league.altersklasse:
            age_rank = get_age_class_rank(t.league.altersklasse)
        else:
            age_rank = 6  # Herren rank
        league_level = t.league.level if t.league else 999
        # Sort by age_rank descending (oldest first), then by league_level ascending (best league first)
        return (-age_rank, league_level)

    teams.sort(key=team_sort_key)

    if len(teams) == 0:
        print(f"Club {club.name} has no teams. No redistribution possible.")
        return

    # Get all players for this club (exclude retired)
    players = Player.query.filter_by(club_id=club_id, is_retired=False).all()

    if len(players) == 0:
        print(f"Club {club.name} has no players. No redistribution needed.")
        return

    print(f"Redistributing {len(players)} players across {len(teams)} teams in {club.name}")

    # Special case: If club has only one team, assign all eligible players to it
    if len(teams) == 1:
        team = teams[0]
        team_age_class = team.league.altersklasse if team.league and team.league.altersklasse else 'Herren'
        team_age_rank = get_age_class_rank(team_age_class)

        print(f"  Club has only one team. Assigning all eligible players to {team.name}...")

        # Clear current team associations
        for player in players:
            player.teams.clear()

        assigned_count = 0
        for player in players:
            # Check if player is eligible for this team based on age
            if player.age:
                player_min_class = get_minimum_altersklasse_for_age(player.age)
                player_age_rank = get_age_class_rank(player_min_class)

                if player_age_rank <= team_age_rank:
                    player.teams.append(team)
                    assigned_count += 1
                    print(f"    {player.name} (Age: {player.age})")
                else:
                    print(f"    WARNING: {player.name} (Age: {player.age}, {player_min_class}) is too young for {team_age_class} team")
            else:
                # Players without age default to being eligible
                player.teams.append(team)
                assigned_count += 1
                print(f"    {player.name} (No age)")

        print(f"  Assigned {assigned_count} players to {team.name}")

        # Commit changes
        try:
            db.session.commit()
            print(f"Player redistribution for {club.name} completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error during player redistribution: {str(e)}")
            raise

        return

    # Clear current team associations
    for player in players:
        player.teams.clear()

    # Assign players using age-class-aware logic (same as global redistribution)
    from collections import defaultdict
    players_by_min_class = defaultdict(list)

    for player in players:
        if not player.age:
            min_class = 'Herren'
        else:
            min_class = get_minimum_altersklasse_for_age(player.age)
        players_by_min_class[min_class].append(player)

    # Sort players within each age class by rating
    for age_class in players_by_min_class:
        players_by_min_class[age_class].sort(key=calculate_player_rating, reverse=True)

    # Assign players to teams
    for team in teams:
        team_age_class = team.league.altersklasse if team.league and team.league.altersklasse else 'Herren'
        team_age_rank = get_age_class_rank(team_age_class)

        print(f"  Assigning players to {team.name} ({team_age_class})...")

        # Find eligible players
        eligible_players = []
        for age_class, player_list in players_by_min_class.items():
            player_age_rank = get_age_class_rank(age_class)
            if player_age_rank <= team_age_rank:
                eligible_players.extend(player_list)

        eligible_players.sort(key=calculate_player_rating, reverse=True)

        # Assign best eligible players
        target_count = max(6, len(players) // len(teams))
        assigned_count = 0

        for player in eligible_players:
            if assigned_count >= target_count:
                break
            if len(player.teams) == 0:
                player.teams.append(team)
                print(f"    {player.name} (Age: {player.age}, Rating: {calculate_player_rating(player):.1f})")
                assigned_count += 1


def redistribute_club_players_by_strength(club_id):
    """
    Legacy function for backward compatibility.
    Now calls the age-class-aware redistribution function.

    DEPRECATED: Use redistribute_club_players_by_strength_and_age() instead.

    Args:
        club_id: ID of the club to redistribute players for
    """
    print("NOTE: redistribute_club_players_by_strength() is deprecated.")
    print("      Using redistribute_club_players_by_strength_and_age() instead.")
    return redistribute_club_players_by_strength_and_age(club_id)


def initial_player_distribution():
    """
    DEPRECATED: This function is now an alias for redistribute_players_by_strength_and_age().

    Kept for backward compatibility. Use redistribute_players_by_strength_and_age() directly.
    """
    print("NOTE: initial_player_distribution() is deprecated and now calls redistribute_players_by_strength_and_age()")
    return redistribute_players_by_strength_and_age()
