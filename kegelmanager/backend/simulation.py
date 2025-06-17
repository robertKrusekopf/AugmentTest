import numpy as np
from datetime import datetime, timedelta, timezone
from models import db, Match, Player, Team, League, Season
from form_system import apply_form_to_strength, get_player_total_form_modifier

def calculate_realistic_fehler(total_score, sicherheit_attribute):
    """
    Calculate realistic error count (Fehlwürfe) based on total score and safety attribute.

    Args:
        total_score: Player's total score across all 4 lanes
        sicherheit_attribute: Player's safety/security attribute (0-99)

    Returns:
        int: Number of errors (Fehlwürfe)

    Logic:
        - Continuous formula based on score: high scores = fewer errors
        - Sicherheit attribute provides smooth adjustment
        - No hard intervals, smooth transitions
    """
    # Continuous formula for base error calculation
    # Uses exponential decay: high scores have exponentially fewer errors
    # Formula: base_fehler = 15 * exp(-0.004 * (score - 300))
    # This gives approximately:
    # - 300 points: ~15 errors
    # - 400 points: ~10 errors
    # - 500 points: ~5.4 errors
    # - 600 points: ~1.8 errors
    # - 700 points: ~0.6 errors

    # Ensure score is at least 300 to avoid negative exponents getting too large
    adjusted_score = max(300, total_score)

    # Base error mean using exponential decay
    base_fehler_mean = 15.0 * np.exp(-0.004 * (adjusted_score - 300))

    # Standard deviation scales with the mean (higher errors = more variation)
    # But with a minimum to ensure some variation even for very good players
    base_fehler_std = max(0.3, base_fehler_mean * 0.4)

    # Smooth sicherheit adjustment using continuous function
    # Sicherheit 0-99 maps to factor 0.5-1.5 smoothly
    # Formula: factor = 1.5 - (sicherheit / 99)
    # This gives:
    # - Sicherheit 0: factor = 1.5 (+50% errors)
    # - Sicherheit 50: factor = ~1.0 (no change)
    # - Sicherheit 99: factor = 0.5 (-50% errors)
    sicherheit_factor = 1.5 - (sicherheit_attribute / 99.0)

    # Apply sicherheit factor smoothly
    adjusted_fehler_mean = base_fehler_mean * sicherheit_factor
    adjusted_fehler_std = base_fehler_std * sicherheit_factor

    # Generate fehler from normal distribution
    fehler = int(max(0, np.random.normal(adjusted_fehler_mean, adjusted_fehler_std)))

    return fehler

def calculate_team_strength(team):
    """Calculate the overall strength of a team based on its players."""
    if not team.players:
        return 50  # Default value if no players

    total_strength = sum(player.strength for player in team.players)
    return total_strength / len(team.players)

def simulate_match(home_team, away_team, match=None, home_team_players=None, away_team_players=None):
    """Simulate a bowling match between two teams and return the result.

    In bowling, 6 players from each team play 4 lanes with 30 throws each.
    Players compete directly against each other (1st vs 1st, 2nd vs 2nd, etc.).
    For each lane, the player with more pins gets 1 set point (SP).
    If both players score the same on a lane, each gets 0.5 SP.
    The player with more SP gets 1 match point (MP).
    If both players have 2 SP each, the player with more total pins gets the MP.
    The team with more total pins gets 2 additional MP.
    The team with more MP wins the match.

    Args:
        home_team: The home team
        away_team: The away team
        match: The match object (optional)
        home_team_players: Pre-assigned players for the home team (optional)
        away_team_players: Pre-assigned players for the away team (optional)
    """
    from models import PlayerMatchPerformance, db, Player, Team, UserLineup
    import random

    # Check for user-selected lineups if a match is provided
    if match:
        # Check for home team lineup
        home_lineup = UserLineup.query.filter_by(
            match_id=match.id,
            team_id=home_team.id,
            is_home_team=True
        ).first()

        # Check for away team lineup
        away_lineup = UserLineup.query.filter_by(
            match_id=match.id,
            team_id=away_team.id,
            is_home_team=False
        ).first()

        # If user lineups exist, use them
        if home_lineup and len(home_lineup.positions) == 6:
            # Sort positions by position number
            sorted_positions = sorted(home_lineup.positions, key=lambda p: p.position_number)
            # Get the players in the correct order
            home_team_players = [Player.query.get(pos.player_id) for pos in sorted_positions]
            print(f"Using user-selected lineup for home team {home_team.name}")

        if away_lineup and len(away_lineup.positions) == 6:
            # Sort positions by position number
            sorted_positions = sorted(away_lineup.positions, key=lambda p: p.position_number)
            # Get the players in the correct order
            away_team_players = [Player.query.get(pos.player_id) for pos in sorted_positions]
            print(f"Using user-selected lineup for away team {away_team.name}")

    # If pre-assigned players are provided, use them
    if home_team_players is not None and away_team_players is not None:
        home_players = home_team_players
        away_players = away_team_players

    else:
        # If no pre-assigned players, use the old method to assign players
        print(f"No pre-assigned players for match {home_team.name} vs {away_team.name}, using old method")

        # Get all teams from the same club as the home team
        home_club_teams = Team.query.filter_by(club_id=home_team.club_id).all()
        # Sort teams by league level (lower level number = higher league)
        home_club_teams.sort(key=lambda t: t.league.level if t.league else 999)

        # Get all teams from the same club as the away team
        away_club_teams = Team.query.filter_by(club_id=away_team.club_id).all()
        # Sort teams by league level (lower level number = higher league)
        away_club_teams.sort(key=lambda t: t.league.level if t.league else 999)

        # Get all available players from the home club
        home_club_players = Player.query.filter_by(club_id=home_team.club_id, is_available_current_matchday=True).all()
        # Get all available players from the away club
        away_club_players = Player.query.filter_by(club_id=away_team.club_id, is_available_current_matchday=True).all()

        # Sort available players by a combination of attributes (best players first)
        # We'll use a weighted average of strength and other key attributes
        def player_rating(player):
            # Calculate a weighted rating based on key attributes including form
            # Apply form modifiers to strength for more accurate rating
            effective_strength = apply_form_to_strength(player.strength, player)
            return (
                effective_strength * 0.5 +  # 50% weight on effective strength (including form)
                player.konstanz * 0.1 +   # 10% weight on consistency
                player.drucksicherheit * 0.1 +  # 10% weight on pressure resistance
                player.volle * 0.15 +     # 15% weight on full pins
                player.raeumer * 0.15     # 15% weight on clearing pins
            )

        # Sort players by their calculated rating
        home_club_players.sort(key=player_rating, reverse=True)
        away_club_players.sort(key=player_rating, reverse=True)

        # Assign players to teams based on team level (best players to first team, etc.)
        home_team_players = {}
        away_team_players = {}

        # Initialize player lists for each team
        for team in home_club_teams:
            home_team_players[team.id] = []

        for team in away_club_teams:
            away_team_players[team.id] = []

        # Get the current match day if a match is provided
        # Handle both regular matches and cup matches
        if match:
            if hasattr(match, 'match_day'):
                current_match_day = match.match_day
            elif hasattr(match, 'cup_match_day'):
                current_match_day = match.cup_match_day
            else:
                current_match_day = None
        else:
            current_match_day = None

        # Filter out players who have already played on this match day
        # We use the has_played_current_matchday flag and last_played_matchday to check
        if current_match_day:
            # Reset flags for players who played on a different match day using bulk update
            # First for home club players
            home_player_ids = [p.id for p in home_club_players if p.has_played_current_matchday and p.last_played_matchday != current_match_day]
            if home_player_ids:
                db.session.execute(
                    db.update(Player)
                    .where(Player.id.in_(home_player_ids))
                    .values(has_played_current_matchday=False)
                )

            # Then for away club players
            away_player_ids = [p.id for p in away_club_players if p.has_played_current_matchday and p.last_played_matchday != current_match_day]
            if away_player_ids:
                db.session.execute(
                    db.update(Player)
                    .where(Player.id.in_(away_player_ids))
                    .values(has_played_current_matchday=False)
                )

            # Commit changes to reset flags
            db.session.commit()

        # Filter out players who have already played on this match day
        home_club_players = [p for p in home_club_players if not p.has_played_current_matchday]
        away_club_players = [p for p in away_club_players if not p.has_played_current_matchday]

        # Make sure teams are sorted by league level (lower level number = higher league)
        home_club_teams.sort(key=lambda t: t.league.level if t.league else 999)
        away_club_teams.sort(key=lambda t: t.league.level if t.league else 999)

        # Assign players to home teams (best teams first)
        used_home_players = set()  # Track which players have been assigned
        for team in home_club_teams:
            home_team_players[team.id] = []
            # For each team, assign up to 6 players who haven't been used yet
            needed_players = 6 - len(home_team_players[team.id])
            available_players = [p for p in home_club_players if p.id not in used_home_players]

            # Take the top N available players for this team
            for player in available_players[:needed_players]:
                home_team_players[team.id].append(player)
                used_home_players.add(player.id)

        # Assign players to away teams (best teams first)
        used_away_players = set()  # Track which players have been assigned
        for team in away_club_teams:
            away_team_players[team.id] = []
            # For each team, assign up to 6 players who haven't been used yet
            needed_players = 6 - len(away_team_players[team.id])
            available_players = [p for p in away_club_players if p.id not in used_away_players]

            # Take the top N available players for this team
            for player in available_players[:needed_players]:
                away_team_players[team.id].append(player)
                used_away_players.add(player.id)

        # Get the players for the current match
        home_players = home_team_players.get(home_team.id, [])
        away_players = away_team_players.get(away_team.id, [])

    # Determine which players are substitutes (not originally in the team)
    home_substitutes = [p for p in home_players if home_team not in p.teams]
    away_substitutes = [p for p in away_players if away_team not in p.teams]

    # Make sure we have enough players (at least 1)
    if not home_players or not away_players:
        # Default scores if not enough players
        home_score = 3000 if home_players else 0
        away_score = 3000 if away_players else 0
        home_match_points = 8 if home_score > away_score else (4 if home_score == away_score else 0)
        away_match_points = 8 if away_score > home_score else (4 if home_score == away_score else 0)

        return {
            'home_team': home_team.name,
            'away_team': away_team.name,
            'home_score': home_score,
            'away_score': away_score,
            'home_match_points': home_match_points,
            'away_match_points': away_match_points,
            'winner': home_team.name if home_match_points > away_match_points else (away_team.name if away_match_points > home_match_points else 'Draw')
        }


    # Add home advantage (fixed 5%)
    home_advantage = 1.05  # 5% advantage for home team

    # Get the home club's lane quality (affects both teams)
    home_club = home_team.club
    lane_quality = home_club.lane_quality if home_club else 1.0  # Default to neutral if no club found

    # Initialize scores and match points
    home_score = 0
    away_score = 0
    home_match_points = 0
    away_match_points = 0

    # Player performances to save
    performances = []

    # Simulate each player's performance
    for i, (home_player, away_player) in enumerate(zip(home_players, away_players)):
        # Simulate 4 lanes for home player
        home_player_lanes = []
        home_player_total = 0
        home_player_volle = 0
        home_player_raeumer = 0
        home_player_fehler = 0

        for lane in range(4):
            # Apply form modifiers to player strength
            effective_strength = apply_form_to_strength(home_player.strength, home_player)

            # Base score depends on effective player strength (including form)
            base_score = (effective_strength * 1.5) + 450  # 450-600 base for strength 0-100

            # Adjust for player attributes
            ausdauer_factor = max(0.8, home_player.ausdauer / 100 - (lane * 0.05))  # Decreases with each lane

            # Apply home advantage
            base_score *= home_advantage

            # Apply lane quality (affects all players on this lane)
            base_score *= lane_quality

            # Add randomness using normal distribution
            # Mean of 1.0, standard deviation based on konstanz (higher konstanz = lower std dev)
            konstanz_factor = home_player.konstanz / 100  # 0-1 scale
            std_dev = 0.15 * (2 - konstanz_factor)
            randomness = np.random.normal(1.0, std_dev)

            # Calculate lane score
            lane_score = int(base_score * ausdauer_factor * randomness)

            # Calculate score based solely on effective player strength (including form) and attributes
            # Base score range: 120-180 for strength 0-99
            mean_score = 120 + (effective_strength * 0.6)

            # Apply lane quality (affects all players on this lane)
            mean_score *= lane_quality

            # Base standard deviation
            std_dev = 12 - (home_player.konstanz / 20)  # 12 to 7 based on konstanz

            # Apply position-based attribute factor based on player's position in lineup
            # Position i: 0-1 = Start, 2-3 = Mitte, 4-5 = Schluss
            if i in [0, 1]:  # Start pair (positions 1-2)
                position_factor = 0.8 + (home_player.start / 500)  # 0.8 to 1.0 range
            elif i in [2, 3]:  # Middle pair (positions 3-4)
                position_factor = 0.8 + (home_player.mitte / 500)  # 0.8 to 1.0 range
            else:  # Schluss pair (positions 5-6)
                position_factor = 0.8 + (home_player.schluss / 500)  # 0.8 to 1.0 range

            # Apply position factor to all lanes
            mean_score *= position_factor

            # Apply drucksicherheit only on the last lane (lane 3)
            if lane == 3:  # Last lane - apply drucksicherheit factor
                # Players with high drucksicherheit perform better on the last lane
                pressure_factor = 0.9 + (home_player.drucksicherheit / 500)  # 0.9 to 1.1 range
                mean_score *= pressure_factor

            # Konstanz and Sicherheit are already factored into the base values
            # No additional adjustments needed here

            # Generate score from normal distribution and ensure it's within reasonable bounds
            lane_score = int(np.random.normal(mean_score, std_dev))
            # Ensure score is at least 80 and at most 200
            lane_score = max(80, min(200, lane_score))

            # Berechne Volle und Räumer direkt basierend auf den Spielerattributen
            # Spieler mit höherem 'volle' Attribut erzielen mehr Punkte auf die vollen Kegel

            # Berechne den Anteil der Volle-Punkte basierend auf den Attributen
            # Spieler mit höherem volle-Attribut erzielen mehr Punkte auf die vollen Kegel
            # Spieler mit höherem raeumer-Attribut erzielen mehr Punkte auf die Räumer

            # Berechne den Volle-Prozentsatz direkt aus den Attributen
            # Formel: 0.5 + (volle / (volle + raeumer)) * 0.3
            # Dies ergibt einen Bereich von ca. 0.5 bis 0.8 je nach Attributverhältnis
            volle_percentage = 0.5 + (home_player.volle / max(1, home_player.volle + home_player.raeumer)) * 0.3

            # Füge etwas Zufälligkeit hinzu (±2%)
            volle_percentage += np.random.normal(0, 0.02)

            # Begrenze den Prozentsatz auf sinnvolle Werte (0.55-0.75)
            volle_percentage = max(0.55, min(0.75, volle_percentage))

            lane_volle = int(lane_score * volle_percentage)
            lane_raeumer = lane_score - lane_volle  # Rest auf Räumer

            home_player_lanes.append(lane_score)
            home_player_total += lane_score
            home_player_volle += lane_volle
            home_player_raeumer += lane_raeumer
            # Note: fehler will be calculated after all lanes are completed

        # Calculate realistic fehler based on total score and sicherheit attribute
        home_player_fehler = calculate_realistic_fehler(home_player_total, home_player.sicherheit)

        # Simulate 4 lanes for away player
        away_player_lanes = []
        away_player_total = 0
        away_player_volle = 0
        away_player_raeumer = 0
        away_player_fehler = 0

        for lane in range(4):
            # Apply form modifiers to player strength
            effective_strength = apply_form_to_strength(away_player.strength, away_player)

            # Base score depends on effective player strength (including form)
            base_score = (effective_strength * 1.5) + 450  # 450-600 base for strength 0-100

            # Adjust for player attributes
            ausdauer_factor = max(0.8, away_player.ausdauer / 100 - (lane * 0.05))  # Decreases with each lane

            # Apply lane quality (affects all players on this lane)
            base_score *= lane_quality

            # Add randomness using normal distribution
            # Mean of 1.0, standard deviation based on konstanz (higher konstanz = lower std dev)
            konstanz_factor = away_player.konstanz / 100  # 0-1 scale
            std_dev = 0.15 * (2 - konstanz_factor)
            randomness = np.random.normal(1.0, std_dev)

            # Calculate lane score
            lane_score = int(base_score * ausdauer_factor * randomness)

            # Calculate score based solely on effective player strength (including form) and attributes
            # Base score range: 120-180 for strength 0-99
            mean_score = 120 + (effective_strength * 0.6)

            # Apply lane quality (affects all players on this lane)
            mean_score *= lane_quality

            # Base standard deviation
            std_dev = 12 - (away_player.konstanz / 20)  # 12 to 7 based on konstanz

            # Apply away factor (players with high 'auswaerts' attribute perform better away)
            # For away games, apply the auswaerts attribute (0-99)
            # A player with auswaerts 50 will have no adjustment
            # A player with auswaerts 99 will get +10% boost
            # A player with auswaerts 0 will get -10% penalty
            away_factor = 0.9 + (away_player.auswaerts / 1000)  # 0.9 to 1.1 range
            mean_score *= away_factor

            # Apply position-based attribute factor based on player's position in lineup
            # Position i: 0-1 = Start, 2-3 = Mitte, 4-5 = Schluss
            if i in [0, 1]:  # Start pair (positions 1-2)
                position_factor = 0.8 + (away_player.start / 500)  # 0.8 to 1.0 range
            elif i in [2, 3]:  # Middle pair (positions 3-4)
                position_factor = 0.8 + (away_player.mitte / 500)  # 0.8 to 1.0 range
            else:  # Schluss pair (positions 5-6)
                position_factor = 0.8 + (away_player.schluss / 500)  # 0.8 to 1.0 range

            # Apply position factor to all lanes
            mean_score *= position_factor

            # Apply drucksicherheit only on the last lane (lane 3)
            if lane == 3:  # Last lane - apply drucksicherheit factor
                # Players with high drucksicherheit perform better on the last lane
                pressure_factor = 0.9 + (away_player.drucksicherheit / 500)  # 0.9 to 1.1 range
                mean_score *= pressure_factor

            # Konstanz and Sicherheit are already factored into the base values
            # No additional adjustments needed here

            # Generate score from normal distribution and ensure it's within reasonable bounds
            lane_score = int(np.random.normal(mean_score, std_dev))

            # Berechne Volle und Räumer direkt basierend auf den Spielerattributen
            # Spieler mit höherem 'volle' Attribut erzielen mehr Punkte auf die vollen Kegel

            # Berechne den Anteil der Volle-Punkte basierend auf den Attributen
            # Spieler mit höherem volle-Attribut erzielen mehr Punkte auf die vollen Kegel
            # Spieler mit höherem raeumer-Attribut erzielen mehr Punkte auf die Räumer

            # Berechne den Volle-Prozentsatz direkt aus den Attributen
            # Formel: 0.5 + (volle / (volle + raeumer)) * 0.3
            # Dies ergibt einen Bereich von ca. 0.5 bis 0.8 je nach Attributverhältnis
            volle_percentage = 0.5 + (away_player.volle / max(1, away_player.volle + away_player.raeumer)) * 0.3

            # Füge etwas Zufälligkeit hinzu (±2%)
            volle_percentage += np.random.normal(0, 0.02)

            # Begrenze den Prozentsatz auf sinnvolle Werte (0.55-0.75)
            volle_percentage = max(0.55, min(0.75, volle_percentage))

            lane_volle = int(lane_score * volle_percentage)
            lane_raeumer = lane_score - lane_volle  # Rest auf Räumer

            away_player_lanes.append(lane_score)
            away_player_total += lane_score
            away_player_volle += lane_volle
            away_player_raeumer += lane_raeumer
            # Note: fehler will be calculated after all lanes are completed

        # Calculate realistic fehler based on total score and sicherheit attribute
        away_player_fehler = calculate_realistic_fehler(away_player_total, away_player.sicherheit)

        # Add to team scores
        home_score += home_player_total
        away_score += away_player_total

        # Calculate set points (SP) for each lane
        home_player_set_points = 0
        away_player_set_points = 0

        for lane in range(4):
            if home_player_lanes[lane] > away_player_lanes[lane]:
                home_player_set_points += 1
            elif home_player_lanes[lane] < away_player_lanes[lane]:
                away_player_set_points += 1
            else:
                # Tie on this lane, both get 0.5 SP
                home_player_set_points += 0.5
                away_player_set_points += 0.5

        # Calculate match points (MP) for this player duel
        home_player_match_points = 0
        away_player_match_points = 0

        if home_player_set_points > away_player_set_points:
            home_player_match_points = 1
        elif home_player_set_points < away_player_set_points:
            away_player_match_points = 1
        else:
            # Tie on set points, player with more total pins gets the MP
            if home_player_total > away_player_total:
                home_player_match_points = 1
            elif home_player_total < away_player_total:
                away_player_match_points = 1
            else:
                # Complete tie, both get 0.5 MP (unlikely but possible)
                home_player_match_points = 0.5
                away_player_match_points = 0.5

        # Add to team match points
        home_match_points += home_player_match_points
        away_match_points += away_player_match_points

        # Create performance records if match is provided
        if match:
            # Check if home player is a substitute
            is_home_substitute = home_player in home_substitutes if 'home_substitutes' in locals() else False

            # Determine if this is a cup match or regular match
            from models import CupMatch
            is_cup_match = isinstance(match, CupMatch)

            if is_cup_match:
                # Create cup match performance
                from models import PlayerCupMatchPerformance
                home_perf = PlayerCupMatchPerformance(
                    player_id=home_player.id,
                    cup_match_id=match.id,
                    team_id=home_team.id,
                    is_home_team=True,
                    position_number=i+1,
                    is_substitute=is_home_substitute,
                    lane1_score=home_player_lanes[0],
                    lane2_score=home_player_lanes[1],
                    lane3_score=home_player_lanes[2],
                    lane4_score=home_player_lanes[3],
                    total_score=home_player_total,
                    volle_score=home_player_volle,
                    raeumer_score=home_player_raeumer,
                    fehler_count=home_player_fehler,
                    set_points=home_player_set_points,
                    match_points=home_player_match_points
                )
            else:
                # Create regular match performance
                home_perf = PlayerMatchPerformance(
                    player_id=home_player.id,
                    match_id=match.id,
                    team_id=home_team.id,
                    is_home_team=True,
                    position_number=i+1,
                    is_substitute=is_home_substitute,
                    lane1_score=home_player_lanes[0],
                    lane2_score=home_player_lanes[1],
                    lane3_score=home_player_lanes[2],
                    lane4_score=home_player_lanes[3],
                    total_score=home_player_total,
                    volle_score=home_player_volle,
                    raeumer_score=home_player_raeumer,
                    fehler_count=home_player_fehler,
                    set_points=home_player_set_points,
                    match_points=home_player_match_points
                )
            performances.append(home_perf)

            # Check if away player is a substitute
            is_away_substitute = away_player in away_substitutes if 'away_substitutes' in locals() else False

            if is_cup_match:
                # Create cup match performance
                from models import PlayerCupMatchPerformance
                away_perf = PlayerCupMatchPerformance(
                    player_id=away_player.id,
                    cup_match_id=match.id,
                    team_id=away_team.id,
                    is_home_team=False,
                    position_number=i+1,
                    is_substitute=is_away_substitute,
                    lane1_score=away_player_lanes[0],
                    lane2_score=away_player_lanes[1],
                    lane3_score=away_player_lanes[2],
                    lane4_score=away_player_lanes[3],
                    total_score=away_player_total,
                    volle_score=away_player_volle,
                    raeumer_score=away_player_raeumer,
                    fehler_count=away_player_fehler,
                    set_points=away_player_set_points,
                    match_points=away_player_match_points
                )
            else:
                # Create regular match performance
                away_perf = PlayerMatchPerformance(
                    player_id=away_player.id,
                    match_id=match.id,
                    team_id=away_team.id,
                    is_home_team=False,
                    position_number=i+1,
                    is_substitute=is_away_substitute,
                    lane1_score=away_player_lanes[0],
                    lane2_score=away_player_lanes[1],
                    lane3_score=away_player_lanes[2],
                    lane4_score=away_player_lanes[3],
                    total_score=away_player_total,
                    volle_score=away_player_volle,
                    raeumer_score=away_player_raeumer,
                    fehler_count=away_player_fehler,
                    set_points=away_player_set_points,
                    match_points=away_player_match_points
                )
            performances.append(away_perf)


    # Add 2 additional MP for the team with more total pins
    if home_score > away_score:
        home_match_points += 2
    elif away_score > home_score:
        away_match_points += 2
    else:
        # Tie on total pins, both get 1 MP
        home_match_points += 1
        away_match_points += 1

    # Save performances to database if match is provided
    if match and performances:
        db.session.add_all(performances)

        # Update match with match points
        match.home_match_points = home_match_points
        match.away_match_points = away_match_points

        # Mark all players as having played on this match day using bulk update
        player_ids = [p.id for p in home_players + away_players]
        if player_ids:
            # Get the match day value (handle both regular matches and cup matches)
            match_day_value = current_match_day if 'current_match_day' in locals() else None
            if match_day_value is not None:
                db.session.execute(
                    db.update(Player)
                    .where(Player.id.in_(player_ids))
                    .values(
                        has_played_current_matchday=True,
                        last_played_matchday=match_day_value
                    )
                )

        # Check for lane records
        from models import LaneRecord

        # Get the home club ID (where the lanes are located)
        home_club_id = home_team.club_id

        # Check for team records - using total team scores across all lanes
        home_team_total_score = sum(perf.total_score for perf in performances if perf.is_home_team)
        away_team_total_score = sum(perf.total_score for perf in performances if not perf.is_home_team)

        # Check for home team record
        LaneRecord.check_and_update_record(
            club_id=home_club_id,
            score=home_team_total_score,
            team=home_team,
            match_id=match.id
        )

        # Check for away team record
        LaneRecord.check_and_update_record(
            club_id=home_club_id,
            score=away_team_total_score,
            team=away_team,
            match_id=match.id
        )

        # Check for individual player records - using total player scores across all lanes
        for perf in performances:
            player = Player.query.get(perf.player_id)

            # Use the total score across all 4 lanes
            LaneRecord.check_and_update_record(
                club_id=home_club_id,
                score=perf.total_score,
                player=player,
                match_id=match.id
            )

    return {
        'home_team': home_team.name,
        'away_team': away_team.name,
        'home_score': home_score,
        'away_score': away_score,
        'home_match_points': home_match_points,
        'away_match_points': away_match_points,
        'winner': home_team.name if home_match_points > away_match_points else (away_team.name if away_match_points > home_match_points else 'Draw')
    }

def simulate_match_day(season):
    """
    Optimized simulation of one match day for all leagues in a season.

    This function uses performance optimizations including:
    - Bulk database operations
    - Reduced query count
    - Optimized player assignment
    - Better transaction management
    """
    from performance_optimizations import (
        create_performance_indexes,
        optimized_match_queries,
        bulk_reset_player_flags,
        CacheManager
    )
    import time

    print(f"Starting optimized simulation for season {season.name}")
    start_time = time.time()

    # Update player form modifiers at the beginning of each match day
    from form_system import update_all_players_form
    updated_players = update_all_players_form()
    print(f"Updated form for {updated_players} players")

    # Create performance indexes if they don't exist
    create_performance_indexes()

    # Check if leagues have fixtures, generate if missing
    leagues = season.leagues
    print(f"Checking {len(leagues)} leagues for fixtures...")

    for league in leagues:
        teams_in_league = Team.query.filter_by(league_id=league.id).all()
        matches_in_league = Match.query.filter_by(league_id=league.id, season_id=season.id).count()

        print(f"League {league.name}: {len(teams_in_league)} teams, {matches_in_league} matches")

        if len(teams_in_league) >= 2 and matches_in_league == 0:
            print(f"Generating missing fixtures for league {league.name}")
            generate_fixtures(league, season)

    # Step 1: Find the next match day to simulate
    next_match_day = find_next_match_day(season.id)
    if not next_match_day:
        return {
            'season': season.name,
            'matches_simulated': 0,
            'results': [],
            'message': 'Keine ungespielte Spiele gefunden. Die Saison ist abgeschlossen.'
        }

    print(f"Simulating match day {next_match_day}")

    # Step 2: Reset player flags efficiently
    bulk_reset_player_flags()

    # Step 3: Get all matches for this match day with optimized query
    try:
        matches_data = optimized_match_queries(season.id, next_match_day)
        cup_matches_data = get_cup_matches_for_match_day(season.id, next_match_day)

        if not matches_data and not cup_matches_data:
            return {
                'season': season.name,
                'matches_simulated': 0,
                'results': [],
                'message': f'Keine Spiele für Spieltag {next_match_day} gefunden.'
            }
    except Exception as e:
        print(f"Error getting match data: {str(e)}")
        # Fallback to original method
        return simulate_match_day_fallback(season)

    # Step 4: Determine clubs and teams playing (from both league and cup matches)
    clubs_with_matches = set()
    teams_playing = {}

    # Process league matches
    if matches_data:
        for match_data in matches_data:
            home_club_id = match_data.home_club_id
            away_club_id = match_data.away_club_id

            clubs_with_matches.add(home_club_id)
            clubs_with_matches.add(away_club_id)

            teams_playing[home_club_id] = teams_playing.get(home_club_id, 0) + 1
            teams_playing[away_club_id] = teams_playing.get(away_club_id, 0) + 1

    # Process cup matches
    if cup_matches_data:
        for cup_match_data in cup_matches_data:
            home_club_id = cup_match_data['home_club_id']
            away_club_id = cup_match_data['away_club_id']

            clubs_with_matches.add(home_club_id)
            clubs_with_matches.add(away_club_id)

            teams_playing[home_club_id] = teams_playing.get(home_club_id, 0) + 1
            teams_playing[away_club_id] = teams_playing.get(away_club_id, 0) + 1

    # Step 5: Batch set player availability for all clubs
    try:
        availability_start = time.time()
        from performance_optimizations import batch_set_player_availability
        batch_set_player_availability(clubs_with_matches, teams_playing)
        print(f"Set player availability for {len(clubs_with_matches)} clubs in {time.time() - availability_start:.3f}s")

    except Exception as e:
        db.session.rollback()
        print(f"Error setting player availability: {str(e)}")
        raise

    # Step 6: Batch assign players to teams for all clubs
    assignment_start = time.time()
    from club_player_assignment import batch_assign_players_to_teams
    cache = CacheManager()
    club_team_players = batch_assign_players_to_teams(
        clubs_with_matches,
        next_match_day,
        season.id,
        cache
    )
    print(f"Assigned players to teams in {time.time() - assignment_start:.3f}s")

    # Step 7: Simulate all matches in parallel (league and cup matches)
    simulation_start = time.time()

    # Combine league and cup matches for simulation
    all_matches_data = []
    if matches_data:
        all_matches_data.extend(matches_data)
    if cup_matches_data:
        all_matches_data.extend(cup_matches_data)

    results, all_performances, all_player_updates, all_lane_records = simulate_matches_parallel(
        all_matches_data,
        club_team_players,
        next_match_day,
        cache
    )
    print(f"Simulated {len(results)} matches ({len(matches_data or [])} league, {len(cup_matches_data or [])} cup) in parallel in {time.time() - simulation_start:.3f}s")

    # Step 8: Batch commit all database changes
    commit_start = time.time()
    batch_commit_simulation_results(
        matches_data,
        results,
        all_performances,
        all_player_updates,
        all_lane_records,
        next_match_day
    )
    print(f"Committed all changes in {time.time() - commit_start:.3f}s")

    end_time = time.time()
    print(f"Optimized simulation completed in {end_time - start_time:.3f}s: {len(results)} matches")

    # Step 9: Check for completed cup rounds and advance if necessary
    if cup_matches_data:
        try:
            advance_completed_cup_rounds(season.id, next_match_day)
        except Exception as e:
            print(f"Error advancing cup rounds: {str(e)}")

    return {
        'season': season.name,
        'matches_simulated': len(results),
        'results': results,
        'match_day': next_match_day
    }


def find_next_match_day(season_id):
    """Find the next match day to simulate (including cup matches)."""
    from sqlalchemy import text, union

    # Find next league match day
    league_result = db.session.execute(
        text("""
            SELECT MIN(match_day)
            FROM match
            WHERE season_id = :season_id
                AND is_played = 0
                AND match_day IS NOT NULL
        """),
        {"season_id": season_id}
    ).scalar()

    # Find next cup match day
    cup_result = db.session.execute(
        text("""
            SELECT MIN(cm.cup_match_day)
            FROM cup_match cm
            JOIN cup c ON cm.cup_id = c.id
            WHERE c.season_id = :season_id
                AND cm.is_played = 0
                AND cm.cup_match_day IS NOT NULL
        """),
        {"season_id": season_id}
    ).scalar()

    # Return the earliest match day
    match_days = [day for day in [league_result, cup_result] if day is not None]
    if match_days:
        next_day = min(match_days)
        # Determine what type of matches are on this day
        has_league = league_result == next_day if league_result else False
        has_cup = cup_result == next_day if cup_result else False

        if has_league and has_cup:
            print(f"Next match day {next_day}: Both league and cup matches")
        elif has_league:
            print(f"Next match day {next_day}: League matches only")
        elif has_cup:
            print(f"Next match day {next_day}: Cup matches only")

        return next_day
    return None


def get_cup_matches_for_match_day(season_id, match_day):
    """Get all cup matches for a specific match day."""
    from models import CupMatch, Cup, Team, Club
    from sqlalchemy import text

    # Query cup matches for the specific match day
    cup_matches = db.session.execute(
        text("""
            SELECT
                cm.id as match_id,
                cm.cup_id,
                cm.home_team_id,
                cm.away_team_id,
                cm.round_name,
                cm.round_number,
                ht.name as home_team_name,
                at.name as away_team_name,
                hc.id as home_club_id,
                ac.id as away_club_id,
                c.name as cup_name,
                c.cup_type
            FROM cup_match cm
            JOIN cup c ON cm.cup_id = c.id
            JOIN team ht ON cm.home_team_id = ht.id
            JOIN team at ON cm.away_team_id = at.id
            LEFT JOIN club hc ON ht.club_id = hc.id
            LEFT JOIN club ac ON at.club_id = ac.id
            WHERE c.season_id = :season_id
                AND cm.cup_match_day = :match_day
                AND cm.is_played = 0
        """),
        {"season_id": season_id, "match_day": match_day}
    ).fetchall()

    # Convert to list of dictionaries for easier handling
    cup_matches_data = []
    for match in cup_matches:
        # Access columns by index or name - use _asdict() for named access
        match_dict = match._asdict() if hasattr(match, '_asdict') else dict(match)
        cup_matches_data.append({
            'match_id': match_dict['match_id'],
            'cup_id': match_dict['cup_id'],
            'home_team_id': match_dict['home_team_id'],
            'away_team_id': match_dict['away_team_id'],
            'home_team_name': match_dict['home_team_name'],
            'away_team_name': match_dict['away_team_name'],
            'home_club_id': match_dict['home_club_id'],
            'away_club_id': match_dict['away_club_id'],
            'cup_name': match_dict['cup_name'],
            'cup_type': match_dict['cup_type'],
            'round_name': match_dict['round_name'],
            'round_number': match_dict['round_number'],
            'match_day': match_day,
            'is_cup_match': True
        })

    return cup_matches_data


def advance_completed_cup_rounds(season_id, match_day):
    """Check for completed cup rounds and advance to next round if all matches are played."""
    from models import Cup, CupMatch
    from sqlalchemy import text

    # Get all cups for this season
    cups = Cup.query.filter_by(season_id=season_id, is_active=True).all()

    for cup in cups:
        try:
            # Check if any matches were played on this match day for this cup
            played_matches_today = db.session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM cup_match cm
                    WHERE cm.cup_id = :cup_id
                        AND cm.cup_match_day = :match_day
                        AND cm.is_played = 1
                """),
                {"cup_id": cup.id, "match_day": match_day}
            ).scalar()

            # Only try to advance if matches were played today for this cup
            if played_matches_today > 0:
                print(f"POKAL: Cup {cup.name}: {played_matches_today} matches played on match day {match_day}")

                # Check if this cup can advance to the next round
                # This will check ALL matches in the current round, not just today's
                success = cup.advance_to_next_round()
                if success:
                    if cup.is_active:
                        print(f"POKAL: Cup {cup.name} advanced to {cup.current_round}")
                    else:
                        print(f"POKAL: Cup {cup.name} completed!")
                else:
                    print(f"POKAL: Cup {cup.name}: Not all matches in round {cup.current_round_number} completed yet")

        except Exception as e:
            print(f"Error advancing cup {cup.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    # Commit any changes made during cup advancement
    db.session.commit()


def simulate_matches_parallel(matches_data, club_team_players, next_match_day, cache_manager):
    """
    Simulate matches in parallel for better performance.

    Args:
        matches_data: List of match data from optimized_match_queries
        club_team_players: Dictionary mapping club_id -> team_id -> players
        next_match_day: The match day being simulated
        cache_manager: CacheManager instance for caching

    Returns:
        tuple: (results, all_performances, all_player_updates, all_lane_records)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    from flask import current_app

    # For now, use sequential simulation to avoid context issues
    # TODO: Fix parallel simulation context issues in future version
    print("Using sequential simulation to avoid context issues")
    return _simulate_matches_sequential(matches_data, club_team_players, next_match_day, cache_manager)


def _simulate_matches_parallel_with_context(matches_data, club_team_players, next_match_day, cache_manager):
    """
    Simulate matches in parallel with proper Flask application context.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    from flask import current_app

    results = []
    all_performances = []
    all_player_updates = []
    all_lane_records = []

    # Thread-safe locks for shared data structures
    results_lock = threading.Lock()
    performances_lock = threading.Lock()
    updates_lock = threading.Lock()
    records_lock = threading.Lock()

    def simulate_single_match(match_data):
        """Simulate a single match in a thread with proper Flask context."""
        # Create application context for this thread
        with current_app.app_context():
            try:
                # Get match object (we'll need to load this in each thread)
                match = Match.query.get(match_data.match_id)
                if not match:
                    return None

                # Get assigned players
                home_players = club_team_players.get(match_data.home_club_id, {}).get(match_data.home_team_id, [])
                away_players = club_team_players.get(match_data.away_club_id, {}).get(match_data.away_team_id, [])

                # Convert player data dictionaries to objects for compatibility
                home_player_objects = []
                away_player_objects = []

                for player_data in home_players:
                    if isinstance(player_data, dict):
                        # Create a simple object from dictionary
                        player_obj = type('Player', (), player_data)()
                        home_player_objects.append(player_obj)
                    else:
                        home_player_objects.append(player_data)

                for player_data in away_players:
                    if isinstance(player_data, dict):
                        # Create a simple object from dictionary
                        player_obj = type('Player', (), player_data)()
                        away_player_objects.append(player_obj)
                    else:
                        away_player_objects.append(player_data)

                # Simulate the match without database operations
                match_result = simulate_match_optimized(
                    match.home_team,
                    match.away_team,
                    home_player_objects,
                    away_player_objects,
                    cache_manager
                )

                # Prepare match result data
                match_result.update({
                    'match_id': match_data.match_id,
                    'home_team_name': match_data.home_team_name,
                    'away_team_name': match_data.away_team_name,
                    'league_name': match_data.league_name,
                    'match_day': next_match_day
                })

                # Collect player updates
                player_updates = []
                for player in home_player_objects + away_player_objects:
                    player_id = player.id if hasattr(player, 'id') else player['id']
                    player_updates.append((player_id, True, next_match_day))

                return {
                    'result': match_result,
                    'player_updates': player_updates,
                    'performances': match_result.get('performances', []),
                    'lane_records': match_result.get('lane_records', [])
                }

            except Exception as e:
                print(f"Error simulating match {match_data.match_id}: {str(e)}")
                return None

    # Determine optimal number of threads (max 4 to avoid overwhelming the database)
    max_workers = min(4, len(matches_data))

    # Execute matches in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all matches
        future_to_match = {
            executor.submit(simulate_single_match, match_data): match_data
            for match_data in matches_data
        }

        # Collect results as they complete
        for future in as_completed(future_to_match):
            match_data = future_to_match[future]
            try:
                result = future.result()
                if result:
                    with results_lock:
                        results.append(result['result'])

                    with updates_lock:
                        all_player_updates.extend(result['player_updates'])

                    with performances_lock:
                        all_performances.extend(result['performances'])

                    with records_lock:
                        all_lane_records.extend(result['lane_records'])

            except Exception as e:
                print(f"Error processing match result for {match_data.match_id}: {str(e)}")

    return results, all_performances, all_player_updates, all_lane_records


def _simulate_matches_sequential(matches_data, club_team_players, next_match_day, cache_manager):
    """
    Sequential simulation fallback when parallel simulation fails.
    """
    results = []
    all_performances = []
    all_player_updates = []
    all_lane_records = []

    for match_data in matches_data:
        try:
            # Convert match_data to dictionary if it's a SQLAlchemy row
            if hasattr(match_data, '_asdict'):
                match_dict = match_data._asdict()
            elif hasattr(match_data, 'keys'):
                match_dict = dict(match_data)
            elif isinstance(match_data, dict):
                match_dict = match_data
            else:
                # Fallback: assume it's a tuple from the SQL query
                # Based on the query in optimized_match_queries: (id, league_id, home_team_id, away_team_id, home_team_name, away_team_name, home_club_id, away_club_id, league_name)
                match_dict = {
                    'match_id': match_data[0],
                    'league_id': match_data[1],
                    'home_team_id': match_data[2],
                    'away_team_id': match_data[3],
                    'home_team_name': match_data[4],
                    'away_team_name': match_data[5],
                    'home_club_id': match_data[6],
                    'away_club_id': match_data[7],
                    'league_name': match_data[8],
                    'is_cup_match': False  # League matches don't have this field
                }

            # Determine if this is a cup match or league match
            is_cup_match = match_dict.get('is_cup_match', False)

            if is_cup_match:
                # Get cup match object
                from models import CupMatch
                match = CupMatch.query.get(match_dict['match_id'])
                if not match:
                    continue
                # Get teams from the cup match
                home_team = match.home_team
                away_team = match.away_team
            else:
                # Get league match object
                match = Match.query.get(match_dict['match_id'])
                if not match:
                    continue
                home_team = match.home_team
                away_team = match.away_team

            # Get assigned players
            home_team_id = match_dict.get('home_team_id') or home_team.id
            away_team_id = match_dict.get('away_team_id') or away_team.id
            home_club_id = match_dict.get('home_club_id') or home_team.club_id
            away_club_id = match_dict.get('away_club_id') or away_team.club_id

            home_players = club_team_players.get(home_club_id, {}).get(home_team_id, [])
            away_players = club_team_players.get(away_club_id, {}).get(away_team_id, [])

            # Convert player data dictionaries to objects for compatibility
            home_player_objects = []
            away_player_objects = []

            for player_data in home_players:
                if isinstance(player_data, dict):
                    # Create a simple object from dictionary
                    player_obj = type('Player', (), player_data)()
                    home_player_objects.append(player_obj)
                else:
                    home_player_objects.append(player_data)

            for player_data in away_players:
                if isinstance(player_data, dict):
                    # Create a simple object from dictionary
                    player_obj = type('Player', (), player_data)()
                    away_player_objects.append(player_obj)
                else:
                    away_player_objects.append(player_data)

            # Simulate the match without database operations
            match_result = simulate_match_optimized(
                home_team,
                away_team,
                home_player_objects,
                away_player_objects,
                cache_manager
            )

            # Prepare match result data
            match_result.update({
                'match_id': match_dict.get('match_id'),
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'home_team_name': match_dict.get('home_team_name') or home_team.name,
                'away_team_name': match_dict.get('away_team_name') or away_team.name,
                'league_name': match_dict.get('league_name') or (match_dict.get('cup_name') if is_cup_match else ''),
                'match_day': next_match_day,
                'is_cup_match': is_cup_match
            })

            # Print cup match results
            if is_cup_match:
                home_team_name = match_dict.get('home_team_name') or home_team.name
                away_team_name = match_dict.get('away_team_name') or away_team.name
                cup_name = match_dict.get('cup_name', 'Unknown Cup')
                round_name = match_dict.get('round_name', 'Unknown Round')
                home_score = match_result['home_score']
                away_score = match_result['away_score']
                home_match_points = match_result['home_match_points']
                away_match_points = match_result['away_match_points']

                # Determine winner
                if home_match_points > away_match_points:
                    winner_name = home_team_name
                elif away_match_points > home_match_points:
                    winner_name = away_team_name
                else:
                    # In case of a tie on match points, the team with more total pins wins
                    if home_score > away_score:
                        winner_name = home_team_name
                    else:
                        winner_name = away_team_name

                print(f"POKAL: {cup_name} {round_name} - {home_team_name} {home_score}:{away_score} {away_team_name} ({home_match_points}:{away_match_points} SP) - Winner: {winner_name}")

            # Collect data
            results.append(match_result)
            all_performances.extend(match_result.get('performances', []))
            all_lane_records.extend(match_result.get('lane_records', []))

            # Collect player updates
            for player in home_player_objects + away_player_objects:
                try:
                    if hasattr(player, 'id'):
                        player_id = player.id
                    elif isinstance(player, dict) and 'id' in player:
                        player_id = player['id']
                    else:
                        print(f"Warning: Player object has no 'id' attribute. Type: {type(player)}")
                        if isinstance(player, dict):
                            print(f"Available keys: {list(player.keys())}")
                        continue
                    all_player_updates.append((player_id, True, next_match_day))
                except Exception as e:
                    print(f"Error getting player ID: {str(e)}")
                    print(f"Player object: {player}")
                    continue

        except Exception as e:
            match_id = getattr(match_data, 'match_id', match_data[0] if hasattr(match_data, '__getitem__') else 'unknown')
            print(f"Error simulating match {match_id} in sequential mode: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"Match data: {match_data}")
            # Only print player data if variables exist
            try:
                print(f"Home players: {home_players}")
                print(f"Away players: {away_players}")
            except NameError:
                print("Player data not available (error occurred before assignment)")

    return results, all_performances, all_player_updates, all_lane_records


def simulate_match_optimized(home_team, away_team, home_players, away_players, cache_manager):
    """
    Optimized match simulation without immediate database operations.

    This version collects all data and returns it for batch processing.
    """
    # Use cached lane quality
    home_club_id = home_team.club_id
    lane_quality = cache_manager.get_lane_quality(home_club_id)

    # Home advantage (5%)
    home_advantage = 1.05

    # Initialize scores and match points
    home_score = 0
    away_score = 0
    home_match_points = 0
    away_match_points = 0

    performances = []
    lane_records = []

    # Simulate each player pair (6 pairs total)
    for i, (home_player, away_player) in enumerate(zip(home_players, away_players)):
        # Simulate home player
        home_result = simulate_player_performance(
            home_player, i, lane_quality, home_advantage, True, cache_manager
        )

        # Simulate away player
        away_result = simulate_player_performance(
            away_player, i, lane_quality, 1.0, False, cache_manager
        )

        # Calculate set points for each lane
        home_set_points = 0
        away_set_points = 0

        for lane in range(4):
            home_lane_score = home_result['lane_scores'][lane]
            away_lane_score = away_result['lane_scores'][lane]

            if home_lane_score > away_lane_score:
                home_set_points += 1
            elif away_lane_score > home_lane_score:
                away_set_points += 1
            else:
                # Tie on this lane, both get 0.5 SP
                home_set_points += 0.5
                away_set_points += 0.5

        # Update performance data with calculated set points
        home_result['performance']['set_points'] = home_set_points
        away_result['performance']['set_points'] = away_set_points

        # Add to team scores
        home_score += home_result['total_score']
        away_score += away_result['total_score']

        # Calculate match points for this player duel
        if home_set_points > away_set_points:
            home_match_points += 1
            home_result['performance']['match_points'] = 1
            away_result['performance']['match_points'] = 0
        elif away_set_points > home_set_points:
            away_match_points += 1
            home_result['performance']['match_points'] = 0
            away_result['performance']['match_points'] = 1
        else:
            # Tie on set points, player with more total pins gets the MP
            if home_result['total_score'] > away_result['total_score']:
                home_match_points += 1
                home_result['performance']['match_points'] = 1
                away_result['performance']['match_points'] = 0
            elif away_result['total_score'] > home_result['total_score']:
                away_match_points += 1
                home_result['performance']['match_points'] = 0
                away_result['performance']['match_points'] = 1
            else:
                # Complete tie, both get 0.5 MP
                home_match_points += 0.5
                away_match_points += 0.5
                home_result['performance']['match_points'] = 0.5
                away_result['performance']['match_points'] = 0.5

        # Store performance data for batch creation
        performances.extend([home_result['performance'], away_result['performance']])

        # Check for potential lane records
        player_id_home = home_player.id if hasattr(home_player, 'id') else home_player['id']
        player_id_away = away_player.id if hasattr(away_player, 'id') else away_player['id']

        lane_records.extend([
            {'club_id': home_club_id, 'score': home_result['total_score'], 'player_id': player_id_home},
            {'club_id': home_club_id, 'score': away_result['total_score'], 'player_id': player_id_away}
        ])

    # Add 2 additional MP for the team with more total pins
    if home_score > away_score:
        home_match_points += 2
    elif away_score > home_score:
        away_match_points += 2
    else:
        # Tie on total pins, both get 1 MP
        home_match_points += 1
        away_match_points += 1

    # Check for team lane records
    lane_records.extend([
        {'club_id': home_club_id, 'score': home_score, 'team_id': home_team.id},
        {'club_id': home_club_id, 'score': away_score, 'team_id': away_team.id}
    ])

    return {
        'home_team': home_team.name,
        'away_team': away_team.name,
        'home_score': home_score,
        'away_score': away_score,
        'home_match_points': home_match_points,
        'away_match_points': away_match_points,
        'winner': home_team.name if home_match_points > away_match_points else (away_team.name if away_match_points > home_match_points else 'Draw'),
        'performances': performances,
        'lane_records': lane_records
    }


def simulate_player_performance(player, position, lane_quality, team_advantage, is_home, cache_manager):
    """
    Simulate performance for a single player across 4 lanes.

    Args:
        player: Player object or dictionary with player data
        position: Position in lineup (0-5)
        lane_quality: Lane quality factor
        team_advantage: Team advantage factor (home advantage for home team)
        is_home: Whether this is the home team
        cache_manager: CacheManager instance

    Returns:
        dict: Player performance data
    """
    # Get player attributes (handle both objects and dictionaries)
    def get_attr(obj, attr, default=50):
        try:
            if hasattr(obj, attr):
                return getattr(obj, attr)
            elif isinstance(obj, dict):
                return obj.get(attr, default)
            else:
                print(f"Warning: Player object is neither dict nor has attributes. Type: {type(obj)}, Attr: {attr}")
                return default
        except Exception as e:
            print(f"Error accessing attribute '{attr}' from player object: {str(e)}")
            print(f"Player object type: {type(obj)}")
            if isinstance(obj, dict):
                print(f"Available keys: {list(obj.keys())}")
            return default

    player_id = get_attr(player, 'id')
    strength = get_attr(player, 'strength', 50)
    konstanz = get_attr(player, 'konstanz', 50)
    drucksicherheit = get_attr(player, 'drucksicherheit', 50)
    volle = get_attr(player, 'volle', 50)
    raeumer = get_attr(player, 'raeumer', 50)
    ausdauer = get_attr(player, 'ausdauer', 50)
    sicherheit = get_attr(player, 'sicherheit', 50)
    auswaerts = get_attr(player, 'auswaerts', 50)
    start = get_attr(player, 'start', 50)
    mitte = get_attr(player, 'mitte', 50)
    schluss = get_attr(player, 'schluss', 50)

    # Apply form modifiers
    form_short = get_attr(player, 'form_short_term', 0.0)
    form_medium = get_attr(player, 'form_medium_term', 0.0)
    form_long = get_attr(player, 'form_long_term', 0.0)

    effective_strength = strength + (strength * (form_short + form_medium + form_long))
    effective_strength = max(1, min(99, effective_strength))  # Clamp to valid range

    # Simulate 4 lanes
    lane_scores = []
    total_score = 0
    total_volle = 0
    total_raeumer = 0

    for lane in range(4):
        # Base score calculation
        mean_score = 120 + (effective_strength * 0.6)

        # Apply lane quality
        mean_score *= lane_quality

        # Apply team advantage (home advantage for home team)
        mean_score *= team_advantage

        # Apply away factor for away players
        if not is_home:
            away_factor = 0.9 + (auswaerts / 1000)  # 0.9 to 1.1 range
            mean_score *= away_factor

        # Apply position-based attributes
        if position in [0, 1]:  # Start pair
            position_factor = 0.8 + (start / 500)
        elif position in [2, 3]:  # Middle pair
            position_factor = 0.8 + (mitte / 500)
        else:  # End pair
            position_factor = 0.8 + (schluss / 500)

        mean_score *= position_factor

        # Apply pressure on last lane
        if lane == 3:
            pressure_factor = 0.9 + (drucksicherheit / 500)
            mean_score *= pressure_factor

        # Apply stamina factor (decreases with each lane)
        ausdauer_factor = max(0.8, ausdauer / 100 - (lane * 0.05))
        mean_score *= ausdauer_factor

        # Add randomness based on consistency
        std_dev = 12 - (konstanz / 20)  # 12 to 7 based on konstanz
        lane_score = int(np.random.normal(mean_score, std_dev))
        lane_score = max(80, min(200, lane_score))  # Clamp to reasonable range

        # Calculate Volle and Räumer
        volle_percentage = 0.5 + (volle / max(1, volle + raeumer)) * 0.3
        volle_percentage += np.random.normal(0, 0.02)
        volle_percentage = max(0.55, min(0.75, volle_percentage))

        lane_volle = int(lane_score * volle_percentage)
        lane_raeumer = lane_score - lane_volle

        lane_scores.append(lane_score)
        total_score += lane_score
        total_volle += lane_volle
        total_raeumer += lane_raeumer

    # Calculate realistic errors
    fehler_count = calculate_realistic_fehler(total_score, sicherheit)

    # Calculate set points (will be calculated against opponent later)
    set_points = 0  # This will be calculated in the match simulation

    # Create performance data structure
    performance_data = {
        'player_id': player_id,
        'team_id': None,  # Will be set later in batch_commit_simulation_results
        'position_number': position + 1,
        'is_substitute': False,  # We'll handle substitutes separately
        'lane1_score': lane_scores[0],
        'lane2_score': lane_scores[1],
        'lane3_score': lane_scores[2],
        'lane4_score': lane_scores[3],
        'total_score': total_score,
        'volle_score': total_volle,
        'raeumer_score': total_raeumer,
        'fehler_count': fehler_count,
        'set_points': set_points,  # Will be updated later
        'match_points': 0  # Will be updated later
    }

    return {
        'lane_scores': lane_scores,
        'total_score': total_score,
        'volle_score': total_volle,
        'raeumer_score': total_raeumer,
        'fehler_count': fehler_count,
        'set_points': set_points,
        'performance': performance_data
    }


def batch_commit_simulation_results(matches_data, results, all_performances, all_player_updates, all_lane_records, next_match_day):
    """
    Batch commit all simulation results to the database.

    Args:
        matches_data: Original match data
        results: Match results
        all_performances: All player performances
        all_player_updates: All player flag updates
        all_lane_records: All lane record checks
        next_match_day: The match day being simulated
    """
    from performance_optimizations import batch_create_performances
    import time

    start_time = time.time()

    try:
        # Update match records (both league and cup matches)
        league_match_updates = {}
        cup_match_updates = {}

        for i, result in enumerate(results):
            match_id = result.get('match_id')
            is_cup_match = result.get('is_cup_match', False)

            if match_id:
                update_data = {
                    'home_score': result['home_score'],
                    'away_score': result['away_score'],
                    'is_played': True
                }

                if is_cup_match:
                    # For cup matches, we also need to determine the winner
                    from models import CupMatch
                    if result['home_match_points'] > result['away_match_points']:
                        update_data['winner_team_id'] = result.get('home_team_id')
                    elif result['away_match_points'] > result['home_match_points']:
                        update_data['winner_team_id'] = result.get('away_team_id')
                    else:
                        # In case of a tie in cup matches, home team wins (or we could use total pins)
                        if result['home_score'] >= result['away_score']:
                            update_data['winner_team_id'] = result.get('home_team_id')
                        else:
                            update_data['winner_team_id'] = result.get('away_team_id')

                    # Add set points for cup matches
                    update_data['home_set_points'] = result['home_match_points']
                    update_data['away_set_points'] = result['away_match_points']

                    cup_match_updates[match_id] = update_data
                else:
                    # For league matches, add match points and date
                    update_data['home_match_points'] = result['home_match_points']
                    update_data['away_match_points'] = result['away_match_points']
                    update_data['match_date'] = datetime.now(timezone.utc)

                    league_match_updates[match_id] = update_data

        # Batch update league matches
        for match_id, updates in league_match_updates.items():
            db.session.execute(
                db.update(Match)
                .where(Match.id == match_id)
                .values(**updates)
            )

        # Batch update cup matches
        if cup_match_updates:
            from models import CupMatch
            print(f"POKAL: Updating {len(cup_match_updates)} cup matches in database")
            for match_id, updates in cup_match_updates.items():
                db.session.execute(
                    db.update(CupMatch)
                    .where(CupMatch.id == match_id)
                    .values(**updates)
                )
                print(f"POKAL: Updated cup match {match_id} with winner_team_id={updates.get('winner_team_id')}")

        # Batch create performances
        if all_performances:
            # Convert performance data to proper format and add missing fields
            performance_dicts = []

            # Create a mapping from match_id to team_ids for quick lookup
            match_team_mapping = {}
            for result in results:
                match_id = result.get('match_id')
                if match_id:
                    # Get the match to find team IDs
                    match = Match.query.get(match_id)
                    if match:
                        match_team_mapping[match_id] = {
                            'home_team_id': match.home_team_id,
                            'away_team_id': match.away_team_id
                        }

            for i, perf in enumerate(all_performances):
                if isinstance(perf, dict):
                    # Add missing required fields
                    perf_dict = perf.copy()

                    # Find the corresponding match_id from results
                    result_index = i // 12  # 12 performances per match (6 home + 6 away)
                    if result_index < len(results):
                        match_id = results[result_index].get('match_id')
                        perf_dict['match_id'] = match_id

                        # Determine team_id and is_home_team based on position in list
                        player_index_in_match = i % 12
                        perf_dict['is_home_team'] = player_index_in_match < 6

                        # Set the correct team_id
                        if match_id in match_team_mapping:
                            if perf_dict['is_home_team']:
                                perf_dict['team_id'] = match_team_mapping[match_id]['home_team_id']
                            else:
                                perf_dict['team_id'] = match_team_mapping[match_id]['away_team_id']

                    performance_dicts.append(perf_dict)
                else:
                    # Convert object to dict if needed
                    performance_dicts.append(perf.__dict__)

            # Filter out performances without required fields
            valid_performances = [p for p in performance_dicts if p.get('match_id') and p.get('player_id') and p.get('team_id')]

            if valid_performances:
                batch_create_performances(valid_performances)

        # Batch update player flags
        if all_player_updates:
            batch_update_player_flags(all_player_updates)

        # Process lane records (this might need to be done individually due to complex logic)
        if all_lane_records:
            process_lane_records_batch(all_lane_records)

        # Single commit for all changes
        db.session.commit()

        end_time = time.time()
        print(f"Batch committed all simulation results in {end_time - start_time:.3f}s")

    except Exception as e:
        db.session.rollback()
        print(f"Error in batch commit: {str(e)}")
        raise


def process_lane_records_batch(all_lane_records):
    """
    Process lane records in batch for better performance.

    Args:
        all_lane_records: List of lane record data
    """
    # Group records by club for efficient processing
    club_records = {}
    for record in all_lane_records:
        club_id = record['club_id']
        if club_id not in club_records:
            club_records[club_id] = []
        club_records[club_id].append(record)

    # Process each club's records
    for club_id, records in club_records.items():
        # Find the highest scores for this club
        team_records = [r for r in records if 'team_id' in r]
        player_records = [r for r in records if 'player_id' in r]

        if team_records:
            max_team_score = max(team_records, key=lambda x: x['score'])
            # Check if this is a new team record (simplified check)
            # In a full implementation, you'd check against existing records

        if player_records:
            max_player_score = max(player_records, key=lambda x: x['score'])
            # Check if this is a new player record (simplified check)
            # In a full implementation, you'd check against existing records


def batch_update_player_flags(all_player_updates):
    """
    Batch update player flags for better performance.

    Args:
        all_player_updates: List of tuples (player_id, has_played, match_day)
    """
    if not all_player_updates:
        return

    try:
        # Group updates by player_id to avoid duplicates
        player_updates_dict = {}
        for player_id, has_played, match_day in all_player_updates:
            player_updates_dict[player_id] = (has_played, match_day)

        # Batch update all players
        for player_id, (has_played, match_day) in player_updates_dict.items():
            db.session.execute(
                db.update(Player)
                .where(Player.id == player_id)
                .values(
                    has_played_current_matchday=has_played,
                    last_played_matchday=match_day
                )
            )
    except Exception as e:
        print(f"Error in batch update player flags: {str(e)}")
        raise


def simulate_match_day_fallback(season):
    """Fallback to original simulation method if optimized version fails."""
    print("Using fallback simulation method")

    results = []

    # Get all leagues in the season
    leagues = season.leagues
    print(f"Fallback: Found {len(leagues)} leagues in season {season.name}")

    # Check if leagues have fixtures, generate if missing
    for league in leagues:
        teams_in_league = Team.query.filter_by(league_id=league.id).all()
        matches_in_league = Match.query.filter_by(league_id=league.id, season_id=season.id).count()

        print(f"Fallback: League {league.name}: {len(teams_in_league)} teams, {matches_in_league} matches")

        if len(teams_in_league) >= 2 and matches_in_league == 0:
            print(f"Fallback: Generating missing fixtures for league {league.name}")
            generate_fixtures(league, season)

    # Find the earliest unplayed match day across all leagues
    unplayed_match_days = []

    for league in leagues:
        # Get all unplayed matches ordered by match day
        unplayed_matches = Match.query.filter(
            Match.league_id == league.id,
            Match.season_id == season.id,
            Match.is_played == False,
            Match.match_day.isnot(None)
        ).order_by(Match.match_day).all()

        if unplayed_matches:
            # Get the earliest match day that has unplayed matches for this league
            league_next_match_day = unplayed_matches[0].match_day
            unplayed_match_days.append((league, league_next_match_day))

    # If no unplayed matches, return empty results
    if not unplayed_match_days:
        return {
            'season': season.name,
            'matches_simulated': 0,
            'results': [],
            'message': 'Keine ungespielte Spiele gefunden. Die Saison ist abgeschlossen.'
        }

    # Find the earliest match day across all leagues
    global_next_match_day = min(unplayed_match_days, key=lambda x: x[1])[1]

    print(f"Fallback: Simulating global match day {global_next_match_day}")

    # Reset player availability flags for all players
    reset_player_availability()

    # Get matches for this match day
    matches_to_simulate = []
    for league in leagues:
        league_matches = Match.query.filter(
            Match.league_id == league.id,
            Match.season_id == season.id,
            Match.is_played == False,
            Match.match_day == global_next_match_day
        ).all()
        matches_to_simulate.extend(league_matches)

    print(f"Fallback: Found {len(matches_to_simulate)} matches to simulate")

    if not matches_to_simulate:
        return {
            'season': season.name,
            'matches_simulated': 0,
            'results': [],
            'message': f'Keine Spiele für Spieltag {global_next_match_day} gefunden.'
        }

    # Simulate each match
    for match in matches_to_simulate:
        try:
            result = simulate_match(match.home_team, match.away_team, match=match)
            results.append(result)

            # Update match in database
            match.home_score = result['home_score']
            match.away_score = result['away_score']
            match.home_match_points = result['home_match_points']
            match.away_match_points = result['away_match_points']
            match.is_played = True
            match.date_played = datetime.now()

        except Exception as e:
            print(f"Fallback: Error simulating match {match.id}: {str(e)}")

    # Commit all changes
    db.session.commit()

    return {
        'season': season.name,
        'matches_simulated': len(results),
        'results': results,
        'message': f'Fallback simulation completed: {len(results)} matches simulated'
    }

def reset_player_availability():
    """Reset the is_available_current_matchday flag for all players."""
    # Use a bulk update operation instead of loading all players into memory
    result = db.session.execute(
        db.update(Player)
        .values(is_available_current_matchday=True)
    )
    db.session.commit()
    print(f"Reset availability flags for all players (affected rows: {result.rowcount})")

def determine_player_availability(club_id, teams_playing):
    """Determine which players are available for a club on the current match day.

    Args:
        club_id: The ID of the club
        teams_playing: Number of teams from this club playing on this match day
    """
    import random

    # Get count of players from this club using a single query
    total_players_count = db.session.query(db.func.count()).filter(
        Player.club_id == club_id
    ).scalar()

    if total_players_count == 0:
        print(f"No players found for club ID {club_id}")
        return

    # Calculate how many players we need at minimum (6 per team)
    min_players_needed = teams_playing * 6

    # If we don't have enough players, make all available
    if total_players_count <= min_players_needed:
        # Make sure all players are available using bulk update
        db.session.execute(
            db.update(Player)
            .where(Player.club_id == club_id)
            .values(is_available_current_matchday=True)
        )
        print(f"Club ID {club_id} has only {total_players_count} players, need {min_players_needed}. All players will be available.")
        return

    # Get all player IDs in a single query
    player_ids = [row[0] for row in db.session.query(Player.id).filter_by(club_id=club_id).all()]

    # Determine unavailable players (16.7% chance of being unavailable)
    unavailable_player_ids = []
    for player_id in player_ids:
        # 16.7% chance of being unavailable
        if random.random() < 0.167:
            unavailable_player_ids.append(player_id)

    # Check if we still have enough available players
    available_players = len(player_ids) - len(unavailable_player_ids)

    # If we don't have enough available players, reduce the unavailable list
    if available_players < min_players_needed:
        # Calculate how many more players we need
        players_needed = min_players_needed - available_players

        # Remove some players from the unavailable list
        if players_needed > 0 and unavailable_player_ids:
            # Remove the last N players from unavailable list to make them available
            unavailable_player_ids = unavailable_player_ids[:-players_needed]

    # Perform all updates in a single transaction
    if unavailable_player_ids:
        # First, set all players as available
        db.session.execute(
            db.update(Player)
            .where(Player.club_id == club_id)
            .values(is_available_current_matchday=True)
        )

        # Then mark selected players as unavailable
        db.session.execute(
            db.update(Player)
            .where(Player.id.in_(unavailable_player_ids))
            .values(is_available_current_matchday=False)
        )
    else:
        # All players available
        db.session.execute(
            db.update(Player)
            .where(Player.club_id == club_id)
            .values(is_available_current_matchday=True)
        )


def reset_player_matchday_flags():
    """Reset the has_played_current_matchday flag for all players."""
    # Only update players that have the flag set to True
    result = db.session.execute(
        db.update(Player)
        .where(Player.has_played_current_matchday == True)
        .values(has_played_current_matchday=False)
    )
    db.session.commit()
    print(f"Reset match day flags for players (affected rows: {result.rowcount})")

def batch_update_player_flags(player_updates):
    """
    Batch update player flags to reduce database operations.

    Args:
        player_updates: List of tuples (player_id, has_played, last_played_matchday)
    """
    if not player_updates:
        return

    try:
        # Validate input data
        for i, update in enumerate(player_updates):
            if len(update) != 3:
                raise ValueError(f"Invalid update tuple at index {i}: {update}. Expected (player_id, has_played, last_matchday)")

            player_id, has_played, last_matchday = update

            # Ensure player_id is an integer
            if not isinstance(player_id, int):
                raise ValueError(f"Invalid player_id at index {i}: {player_id} (type: {type(player_id)}). Expected integer.")

        # Group updates by values to minimize database operations
        played_players = []
        matchday_updates = {}

        for player_id, has_played, last_matchday in player_updates:
            if has_played:
                played_players.append(player_id)
            if last_matchday is not None:
                if last_matchday not in matchday_updates:
                    matchday_updates[last_matchday] = []
                matchday_updates[last_matchday].append(player_id)

        # Update has_played_current_matchday for all players who played
        if played_players:
            db.session.execute(
                db.update(Player)
                .where(Player.id.in_(played_players))
                .values(has_played_current_matchday=True)
            )

        # Update last_played_matchday for each group
        for matchday, player_ids in matchday_updates.items():
            db.session.execute(
                db.update(Player)
                .where(Player.id.in_(player_ids))
                .values(last_played_matchday=matchday)
            )

        db.session.commit()
        print(f"Batch updated flags for {len(player_updates)} players")

    except Exception as e:
        db.session.rollback()
        print(f"Error in batch update: {str(e)}")
        print(f"Player updates data: {player_updates[:5]}...")  # Show first 5 for debugging
        raise

def simulate_season(season, create_new_season=True):
    """Simulate all matches for a season.

    Args:
        season: The season to simulate
        create_new_season: Whether to create a new season after simulation (default: True)
    """
    from club_player_assignment import assign_players_to_teams_for_match_day

    results = []
    new_season_created = False
    new_season_id = None

    # Get all leagues in the season
    leagues = season.leagues

    print(f"Simulating entire season: {season.name} (ID: {season.id})")
    print(f"Number of leagues: {len(leagues)}")
    print(f"Create new season after simulation: {create_new_season}")

    # Check if cups exist for this season
    from models import Cup, CupMatch
    cups = Cup.query.filter_by(season_id=season.id).all()
    total_cup_matches = 0
    unplayed_cup_matches = 0
    all_cup_match_days = set()

    for cup in cups:
        cup_match_count = CupMatch.query.filter_by(cup_id=cup.id).count()
        unplayed_count = CupMatch.query.filter_by(cup_id=cup.id, is_played=False).count()
        total_cup_matches += cup_match_count
        unplayed_cup_matches += unplayed_count
        print(f"POKAL: Cup {cup.name} has {cup_match_count} matches ({unplayed_count} unplayed)")

        # Show cup match days for this cup
        cup_match_days = db.session.query(CupMatch.cup_match_day).filter_by(cup_id=cup.id, is_played=False).distinct().all()
        if cup_match_days:
            match_days_list = [str(day[0]) for day in cup_match_days if day[0] is not None]
            print(f"POKAL: Cup {cup.name} has unplayed matches on match days: {', '.join(match_days_list)}")
            # Add to overall set
            for day in cup_match_days:
                if day[0] is not None:
                    all_cup_match_days.add(day[0])

        # Also show ALL cup match days (including played ones) for debugging
        all_cup_days = db.session.query(CupMatch.cup_match_day).filter_by(cup_id=cup.id).distinct().all()
        if all_cup_days:
            all_days_list = [str(day[0]) for day in all_cup_days if day[0] is not None]
            print(f"POKAL: Cup {cup.name} ALL match days (played and unplayed): {', '.join(all_days_list)}")

    print(f"POKAL: Total {len(cups)} cups with {total_cup_matches} matches ({unplayed_cup_matches} unplayed) in season")

    if all_cup_match_days:
        sorted_cup_days = sorted(all_cup_match_days)
        print(f"POKAL: All unplayed cup match days in season: {', '.join(map(str, sorted_cup_days))}")
    else:
        print("POKAL: No unplayed cup match days found in season")

    # First, ensure all leagues have fixtures generated
    for league in leagues:
        # Generate matches if they don't exist
        if not league.matches:
            print(f"No matches found for league {league.name}, generating fixtures...")
            generate_fixtures(league, season)

    # Simulate match day by match day using the same logic as simulate_match_day
    # This ensures that both league and cup matches are properly simulated in the correct order
    while True:
        # Find the next match day to simulate (same logic as simulate_match_day)
        next_match_day = find_next_match_day(season.id)
        if not next_match_day:
            print("No more unplayed matches found. Season simulation complete.")
            break

        print(f"Simulating match day {next_match_day} across all leagues and cups")

        # Reset player availability flags efficiently
        from performance_optimizations import bulk_reset_player_flags
        bulk_reset_player_flags()

        # Determine which clubs have matches on this match day
        clubs_with_matches = set()
        teams_playing = {}  # Dictionary to track how many teams each club has playing

        # First, identify all clubs that have teams playing on this match day
        for league in leagues:
            unplayed_matches = Match.query.filter_by(
                league_id=league.id,
                season_id=season.id,
                is_played=False,
                match_day=next_match_day
            ).all()

            for match in unplayed_matches:
                home_club_id = match.home_team.club_id
                away_club_id = match.away_team.club_id

                clubs_with_matches.add(home_club_id)
                clubs_with_matches.add(away_club_id)

                # Count how many teams each club has playing
                teams_playing[home_club_id] = teams_playing.get(home_club_id, 0) + 1
                teams_playing[away_club_id] = teams_playing.get(away_club_id, 0) + 1

        # Also check for cup matches on this match day using the same function as simulate_match_day
        cup_matches_data = get_cup_matches_for_match_day(season.id, next_match_day)
        print(f"POKAL: Found {len(cup_matches_data)} cup matches for match day {next_match_day}")

        # Get actual CupMatch objects for simulation
        from models import CupMatch, Cup
        cup_matches = []
        for cup_match_data in cup_matches_data:
            cup_match = CupMatch.query.get(cup_match_data['match_id'])
            if cup_match:
                cup_matches.append(cup_match)

        for cup_match in cup_matches:
            home_club_id = cup_match.home_team.club_id
            away_club_id = cup_match.away_team.club_id

            clubs_with_matches.add(home_club_id)
            clubs_with_matches.add(away_club_id)

            # Count how many teams each club has playing
            teams_playing[home_club_id] = teams_playing.get(home_club_id, 0) + 1
            teams_playing[away_club_id] = teams_playing.get(away_club_id, 0) + 1

        # Batch process player availability for all clubs
        try:
            for club_id in clubs_with_matches:
                determine_player_availability(club_id, teams_playing.get(club_id, 0))

            # Commit all availability changes at once
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"Error setting player availability for match day {next_match_day}: {str(e)}")
            raise

        # Assign players to teams for each club
        club_team_players = {}
        for club_id in clubs_with_matches:
            club_team_players[club_id] = assign_players_to_teams_for_match_day(
                club_id,
                next_match_day,
                season.id
            )

        # Simulate matches for this match day across all leagues
        match_day_results = []
        all_player_updates = []

        # Simulate league matches
        for league in leagues:
            # Get all unplayed matches for this match day in this league
            unplayed_matches = Match.query.filter_by(
                league_id=league.id,
                season_id=season.id,
                is_played=False,
                match_day=next_match_day
            ).all()

            if unplayed_matches:
                print(f"Simulating match day {next_match_day} for league {league.name} with {len(unplayed_matches)} matches")

            # Simulate each match in this match day
            for match in unplayed_matches:
                home_team = match.home_team
                away_team = match.away_team

                # Get assigned players
                home_players = club_team_players.get(home_team.club_id, {}).get(home_team.id, [])
                away_players = club_team_players.get(away_team.club_id, {}).get(away_team.id, [])

                # Simulate the match
                match_result = simulate_match(
                    home_team,
                    away_team,
                    match=match,
                    home_team_players=home_players,
                    away_team_players=away_players
                )

                # Update match record
                match.home_score = match_result['home_score']
                match.away_score = match_result['away_score']
                match.home_match_points = match_result['home_match_points']
                match.away_match_points = match_result['away_match_points']
                match.is_played = True
                match.match_date = datetime.now(timezone.utc)

                # Add team names to the result for better display
                match_result['home_team_name'] = home_team.name
                match_result['away_team_name'] = away_team.name
                match_result['league_name'] = league.name
                match_result['match_day'] = next_match_day

                match_day_results.append(match_result)

                # Collect player updates for batch processing
                # Convert player objects to IDs if necessary
                home_player_ids = [p.id if hasattr(p, 'id') else p for p in home_players]
                away_player_ids = [p.id if hasattr(p, 'id') else p for p in away_players]

                for player_id in home_player_ids + away_player_ids:
                    all_player_updates.append((player_id, True, next_match_day))

        # Simulate cup matches for this match day
        if cup_matches:
            print(f"POKAL: Simulating {len(cup_matches)} cup matches for match day {next_match_day}")

            for cup_match in cup_matches:
                home_team = cup_match.home_team
                away_team = cup_match.away_team

                # Get assigned players
                home_players = club_team_players.get(home_team.club_id, {}).get(home_team.id, [])
                away_players = club_team_players.get(away_team.club_id, {}).get(away_team.id, [])

                # Simulate the match
                match_result = simulate_match(
                    home_team,
                    away_team,
                    match=cup_match,
                    home_team_players=home_players,
                    away_team_players=away_players
                )

                # Update cup match record
                cup_match.home_score = match_result['home_score']
                cup_match.away_score = match_result['away_score']
                cup_match.home_set_points = match_result['home_match_points']
                cup_match.away_set_points = match_result['away_match_points']
                cup_match.is_played = True
                cup_match.match_date = datetime.now(timezone.utc).date()

                # Determine and set the winner (essential for cup advancement)
                if match_result['home_match_points'] > match_result['away_match_points']:
                    cup_match.winner_team_id = home_team.id
                    winner_name = home_team.name
                elif match_result['away_match_points'] > match_result['home_match_points']:
                    cup_match.winner_team_id = away_team.id
                    winner_name = away_team.name
                else:
                    # In case of a tie on match points, the team with more total pins wins
                    if match_result['home_score'] > match_result['away_score']:
                        cup_match.winner_team_id = home_team.id
                        winner_name = home_team.name
                    else:
                        cup_match.winner_team_id = away_team.id
                        winner_name = away_team.name

                # Print cup match result
                print(f"POKAL: {cup_match.cup.name} {cup_match.round_name} - {home_team.name} {match_result['home_score']}:{match_result['away_score']} {away_team.name} ({match_result['home_match_points']}:{match_result['away_match_points']} SP) - Winner: {winner_name}")

                # Add team names to the result for better display
                match_result['home_team_name'] = home_team.name
                match_result['away_team_name'] = away_team.name
                match_result['cup_name'] = cup_match.cup.name
                match_result['round_name'] = cup_match.round_name
                match_result['match_day'] = next_match_day
                match_result['is_cup_match'] = True

                match_day_results.append(match_result)

                # Collect player updates for batch processing
                # Convert player objects to IDs if necessary
                home_player_ids = [p.id if hasattr(p, 'id') else p for p in home_players]
                away_player_ids = [p.id if hasattr(p, 'id') else p for p in away_players]

                for player_id in home_player_ids + away_player_ids:
                    all_player_updates.append((player_id, True, next_match_day))

        # Batch update player flags
        if all_player_updates:
            batch_update_player_flags(all_player_updates)

        # Save all changes to database after each match day
        db.session.commit()
        print(f"Simulated {len(match_day_results)} matches for match day {next_match_day}")

        # Check for completed cup rounds and advance if necessary
        # This must be called after every match day, not just when cup matches exist on this day
        try:
            advance_completed_cup_rounds(season.id, next_match_day)
        except Exception as e:
            print(f"Error advancing cup rounds: {str(e)}")

        # Reset player flags after the match day is complete
        reset_player_matchday_flags()

        # Add results from this match day to overall results
        results.extend(match_day_results)

    print(f"Simulated {len(results)} matches in total")

    # Explicitly recalculate standings for each league
    for league in leagues:
        print(f"Recalculating standings for league: {league.name}")
        standings = calculate_standings(league)
        print(f"League {league.name} has {len(standings)} teams in standings")

    # Process end of season (promotions/relegations) only if create_new_season is True
    if create_new_season:
        # Check if all league matches are played
        all_league_matches_played = all(match.is_played for league in leagues for match in league.matches)

        # Check if all cup matches are played
        from models import Cup, CupMatch
        all_cup_matches_played = True
        cups = Cup.query.filter_by(season_id=season.id).all()
        for cup in cups:
            cup_matches = CupMatch.query.filter_by(cup_id=cup.id).all()
            if not all(match.is_played for match in cup_matches):
                all_cup_matches_played = False
                break

        # Only process end of season if ALL matches (league and cup) are played
        if all_league_matches_played and all_cup_matches_played:
            print("All league and cup matches played, processing end of season...")
            process_end_of_season(season)

            # Get the new current season
            new_season = Season.query.filter_by(is_current=True).first()
            if new_season and new_season.id != season.id:
                new_season_created = True
                new_season_id = new_season.id
                print(f"New season created: {new_season.name} (ID: {new_season.id})")
        else:
            unplayed_league_matches = sum(1 for league in leagues for match in league.matches if not match.is_played)
            unplayed_cup_matches = sum(1 for cup in cups for match in CupMatch.query.filter_by(cup_id=cup.id).all() if not match.is_played)
            print(f"Season not complete: {unplayed_league_matches} league matches and {unplayed_cup_matches} cup matches still unplayed")

    return {
        'season': season.name,
        'matches_simulated': len(results),
        'results': results,
        'new_season_created': new_season_created,
        'new_season_id': new_season_id
    }

def generate_fixtures(league, season):
    """Generate fixtures (matches) for a league in a season using a round-robin tournament algorithm.
    Ensures teams alternate between home and away matches as much as possible."""
    # Use direct query instead of relationship to ensure we get updated team assignments
    teams = list(Team.query.filter_by(league_id=league.id).all())

    # Need at least 2 teams to create fixtures
    if len(teams) < 2:
        return

    # If odd number of teams, add a dummy team (bye)
    if len(teams) % 2 != 0:
        teams.append(None)

    num_teams = len(teams)
    num_rounds = num_teams - 1
    matches_per_round = num_teams // 2

    # Dictionary to track the last match type for each team (True for home, False for away)
    # Initialize with None (no matches played yet)
    last_match_type = {team.id: None for team in teams if team is not None}

    # Dictionary to track consecutive home/away matches for each team
    consecutive_matches = {team.id: 0 for team in teams if team is not None}

    # List to store all matches before committing to database
    all_matches = []

    # First half of the season (round 1)
    for round_num in range(num_rounds):
        round_matches = []

        # Generate matches for this round
        for match_num in range(matches_per_round):
            home_idx = (round_num + match_num) % (num_teams - 1)
            away_idx = (num_teams - 1 - match_num + round_num) % (num_teams - 1)

            # Last team stays fixed, others rotate
            if match_num == 0:
                away_idx = num_teams - 1

            # Skip matches with dummy team (bye)
            if teams[home_idx] is None or teams[away_idx] is None:
                continue

            # Create match with proper match day
            match_day = round_num + 1

            # Check if we should swap home/away to ensure alternation
            should_swap = False

            if teams[home_idx] and teams[away_idx]:
                home_team_id = teams[home_idx].id
                away_team_id = teams[away_idx].id

                # If home team had a home match last time and away team had an away match last time,
                # consider swapping to maintain alternation
                if (last_match_type[home_team_id] == True and
                    last_match_type[away_team_id] == False):
                    # Only swap if both teams have had consecutive matches of the same type
                    if consecutive_matches[home_team_id] > 0 and consecutive_matches[away_team_id] > 0:
                        should_swap = True

            if should_swap:
                # Swap home and away teams
                match = Match(
                    home_team_id=teams[away_idx].id,
                    away_team_id=teams[home_idx].id,
                    league_id=league.id,
                    season_id=season.id,
                    match_day=match_day,
                    round=1,  # First half of season
                    is_played=False
                )

                # Update tracking dictionaries
                last_match_type[teams[away_idx].id] = True
                last_match_type[teams[home_idx].id] = False

                if last_match_type[teams[away_idx].id] == True:
                    consecutive_matches[teams[away_idx].id] += 1
                else:
                    consecutive_matches[teams[away_idx].id] = 1

                if last_match_type[teams[home_idx].id] == False:
                    consecutive_matches[teams[home_idx].id] += 1
                else:
                    consecutive_matches[teams[home_idx].id] = 1
            else:
                # Create match normally
                match = Match(
                    home_team_id=teams[home_idx].id,
                    away_team_id=teams[away_idx].id,
                    league_id=league.id,
                    season_id=season.id,
                    match_day=match_day,
                    round=1,  # First half of season
                    is_played=False
                )

                # Update tracking dictionaries
                if teams[home_idx] and teams[away_idx]:
                    last_match_type[teams[home_idx].id] = True
                    last_match_type[teams[away_idx].id] = False

                    if last_match_type[teams[home_idx].id] == True:
                        consecutive_matches[teams[home_idx].id] += 1
                    else:
                        consecutive_matches[teams[home_idx].id] = 1

                    if last_match_type[teams[away_idx].id] == False:
                        consecutive_matches[teams[away_idx].id] += 1
                    else:
                        consecutive_matches[teams[away_idx].id] = 1

            round_matches.append(match)

        # Add all matches for this round
        all_matches.extend(round_matches)

    # Reset tracking dictionaries for second half
    last_match_type = {team.id: None for team in teams if team is not None}
    consecutive_matches = {team.id: 0 for team in teams if team is not None}

    # Second half of the season (round 2) - reverse home/away
    for round_num in range(num_rounds):
        round_matches = []

        # Generate matches for this round
        for match_num in range(matches_per_round):
            # Same as first half but home/away reversed
            away_idx = (round_num + match_num) % (num_teams - 1)
            home_idx = (num_teams - 1 - match_num + round_num) % (num_teams - 1)

            # Last team stays fixed, others rotate
            if match_num == 0:
                home_idx = num_teams - 1

            # Skip matches with dummy team (bye)
            if teams[home_idx] is None or teams[away_idx] is None:
                continue

            # Create match with proper match day (continue from first half)
            match_day = num_rounds + round_num + 1

            # Check if we should swap home/away to ensure alternation
            should_swap = False

            if teams[home_idx] and teams[away_idx]:
                home_team_id = teams[home_idx].id
                away_team_id = teams[away_idx].id

                # If home team had a home match last time and away team had an away match last time,
                # consider swapping to maintain alternation
                if (last_match_type[home_team_id] == True and
                    last_match_type[away_team_id] == False):
                    # Only swap if both teams have had consecutive matches of the same type
                    if consecutive_matches[home_team_id] > 0 and consecutive_matches[away_team_id] > 0:
                        should_swap = True

            if should_swap:
                # Swap home and away teams
                match = Match(
                    home_team_id=teams[away_idx].id,
                    away_team_id=teams[home_idx].id,
                    league_id=league.id,
                    season_id=season.id,
                    match_day=match_day,
                    round=2,  # Second half of season
                    is_played=False
                )

                # Update tracking dictionaries
                last_match_type[teams[away_idx].id] = True
                last_match_type[teams[home_idx].id] = False

                if last_match_type[teams[away_idx].id] == True:
                    consecutive_matches[teams[away_idx].id] += 1
                else:
                    consecutive_matches[teams[away_idx].id] = 1

                if last_match_type[teams[home_idx].id] == False:
                    consecutive_matches[teams[home_idx].id] += 1
                else:
                    consecutive_matches[teams[home_idx].id] = 1
            else:
                # Create match normally
                match = Match(
                    home_team_id=teams[home_idx].id,
                    away_team_id=teams[away_idx].id,
                    league_id=league.id,
                    season_id=season.id,
                    match_day=match_day,
                    round=2,  # Second half of season
                    is_played=False
                )

                # Update tracking dictionaries
                if teams[home_idx] and teams[away_idx]:
                    last_match_type[teams[home_idx].id] = True
                    last_match_type[teams[away_idx].id] = False

                    if last_match_type[teams[home_idx].id] == True:
                        consecutive_matches[teams[home_idx].id] += 1
                    else:
                        consecutive_matches[teams[home_idx].id] = 1

                    if last_match_type[teams[away_idx].id] == False:
                        consecutive_matches[teams[away_idx].id] += 1
                    else:
                        consecutive_matches[teams[away_idx].id] = 1

            round_matches.append(match)

        # Add all matches for this round
        all_matches.extend(round_matches)

    # Add all matches to the database
    for match in all_matches:
        db.session.add(match)

    db.session.commit()

    # Set match dates (one match day per week starting from season start date)
    matches = Match.query.filter_by(league_id=league.id, season_id=season.id).all()
    match_days = {}

    # Group matches by match day
    for match in matches:
        if match.match_day not in match_days:
            match_days[match.match_day] = []
        match_days[match.match_day].append(match)

    # Set dates for each match day (one week apart)
    for match_day, day_matches in match_days.items():
        # Calculate date for this match day (season start + (match_day-1) weeks)
        match_date = season.start_date + timedelta(days=(match_day-1) * 7)

        # Set the same date for all matches on this match day
        for match in day_matches:
            # Convert date to datetime at 15:00 (3 PM)
            match.match_date = datetime.combine(
                match_date,
                datetime.min.time().replace(hour=15),
                tzinfo=timezone.utc
            )

    # Verify home/away alternation for each team
    team_matches = {}

    # Group matches by team
    for match in matches:
        if match.home_team_id not in team_matches:
            team_matches[match.home_team_id] = []
        if match.away_team_id not in team_matches:
            team_matches[match.away_team_id] = []

        # Add match to both teams' lists with a flag indicating home/away
        team_matches[match.home_team_id].append((match, True))  # True for home
        team_matches[match.away_team_id].append((match, False))  # False for away

    # Sort each team's matches by match day
    for team_id, team_match_list in team_matches.items():
        team_match_list.sort(key=lambda x: x[0].match_day)

        # Count consecutive home/away matches
        consecutive_home = 0
        consecutive_away = 0
        total_consecutive = 0

        for i in range(len(team_match_list)):
            is_home = team_match_list[i][1]

            if is_home:
                consecutive_home += 1
                consecutive_away = 0
            else:
                consecutive_away += 1
                consecutive_home = 0

            # Count matches with more than 2 consecutive home/away games
            if consecutive_home > 2 or consecutive_away > 2:
                total_consecutive += 1

        # Log teams with many consecutive matches of the same type
        if total_consecutive > 0:
            team = Team.query.get(team_id)
            print(f"Team {team.name} has {total_consecutive} instances of more than 2 consecutive home/away matches")

    db.session.commit()

def process_end_of_season(season):
    """Process end of season events like promotions and relegations."""
    print("Processing end of season...")

    # Save final standings to league history before creating new season
    save_league_history(season)

    # Save cup winners and finalists to cup history before creating new season
    save_cup_history(season)

    # Save team cup participation history before creating new season
    save_team_cup_history(season)

    # Save team achievements (league champions and cup winners) before creating new season
    save_team_achievements(season)

    # Create new season (this will handle promotions/relegations internally)
    create_new_season(season)

def save_league_history(season):
    """Save the final standings of all leagues to the league history table."""
    try:
        from models import LeagueHistory, League, db

        print("Saving league history for season:", season.name)

        # Check if LeagueHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'league_history' not in existing_tables:
            print("LeagueHistory table does not exist yet. Creating it...")
            # Create the table
            db.create_all()
            print("LeagueHistory table created successfully.")

        # Get all leagues for this season
        leagues = League.query.filter_by(season_id=season.id).all()
        print(f"Found {len(leagues)} leagues for season {season.name}")

        for league in leagues:
            print(f"Saving history for league: {league.name} (ID: {league.id})")

            # Calculate final standings
            standings = calculate_standings(league)
            print(f"Calculated {len(standings)} standings for league {league.name}")

            # Save each team's final position and statistics
            for i, standing in enumerate(standings):
                team = standing['team']
                position = i + 1  # Position is index + 1
                print(f"  Processing team {i+1}: {team.name} (Position: {position})")

                # Get club information
                club_name = team.club.name if team.club else None
                club_id = team.club.id if team.club else None
                verein_id = team.club.verein_id if team.club else None

                # Calculate games played
                games_played = standing['wins'] + standing['draws'] + standing['losses']

                # Calculate average scores (home and away)
                home_matches = Match.query.filter_by(home_team_id=team.id, league_id=league.id, is_played=True).all()
                away_matches = Match.query.filter_by(away_team_id=team.id, league_id=league.id, is_played=True).all()

                avg_home_score = 0.0
                avg_away_score = 0.0

                if home_matches:
                    total_home_score = sum(match.home_score for match in home_matches)
                    avg_home_score = total_home_score / len(home_matches)

                if away_matches:
                    total_away_score = sum(match.away_score for match in away_matches)
                    avg_away_score = total_away_score / len(away_matches)

                # Create league history entry
                history_entry = LeagueHistory(
                    league_name=league.name,
                    league_level=league.level,
                    season_id=season.id,
                    season_name=season.name,
                    team_id=team.id,
                    team_name=team.name,
                    club_name=club_name,
                    club_id=club_id,
                    verein_id=verein_id,
                    position=position,
                    games_played=games_played,
                    wins=standing['wins'],
                    draws=standing['draws'],
                    losses=standing['losses'],
                    table_points=standing['points'],
                    match_points_for=standing['match_points_for'],
                    match_points_against=standing['match_points_against'],
                    pins_for=standing['goals_for'],  # goals_for is actually pins_for
                    pins_against=standing['goals_against'],  # goals_against is actually pins_against
                    avg_home_score=avg_home_score,
                    avg_away_score=avg_away_score
                )

                print(f"    Created history entry: {team.name} -> Position {position}")
                db.session.add(history_entry)

            print(f"Added {len(standings)} teams for league {league.name} to session")

        # Commit all history entries
        print("Committing all history entries to database...")
        db.session.commit()
        print(f"League history saved successfully for {len(leagues)} leagues")

        # Verify the data was saved
        total_entries = LeagueHistory.query.filter_by(season_id=season.id).count()
        print(f"Verification: {total_entries} history entries saved for season {season.name}")

    except Exception as e:
        print(f"Error saving league history: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with season transition without saving history...")
        # Don't let history saving errors break the season transition
        try:
            db.session.rollback()
        except:
            pass


def save_cup_history(season):
    """Save the winners and finalists of all completed cups to the cup history table."""
    try:
        from models import CupHistory, Cup, CupMatch, Team, Club, db

        print("Saving cup history for season:", season.name)

        # Check if CupHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'cup_history' not in existing_tables:
            print("CupHistory table does not exist yet. Creating it...")
            # Create the table
            db.create_all()
            print("CupHistory table created successfully.")

        # Get all cups for this season
        cups = Cup.query.filter_by(season_id=season.id).all()
        print(f"Found {len(cups)} cups for season {season.name}")

        for cup in cups:
            print(f"Processing cup: {cup.name}")

            # Check if this cup is completed (not active)
            if cup.is_active:
                print(f"  Cup {cup.name} is still active, skipping...")
                continue

            # Find the final match (should be the last round)
            final_matches = CupMatch.query.filter_by(
                cup_id=cup.id,
                round_number=cup.total_rounds,
                is_played=True
            ).all()

            if not final_matches:
                print(f"  No final match found for cup {cup.name}, skipping...")
                continue

            # There should be exactly one final match
            if len(final_matches) != 1:
                print(f"  Expected 1 final match for cup {cup.name}, found {len(final_matches)}, skipping...")
                continue

            final_match = final_matches[0]

            # Get winner and finalist teams
            if not final_match.winner_team_id:
                print(f"  Final match for cup {cup.name} has no winner, skipping...")
                continue

            winner_team = Team.query.get(final_match.winner_team_id)
            if not winner_team:
                print(f"  Winner team not found for cup {cup.name}, skipping...")
                continue

            # Determine finalist (the team that lost the final)
            if final_match.home_team_id == final_match.winner_team_id:
                finalist_team = Team.query.get(final_match.away_team_id)
            else:
                finalist_team = Team.query.get(final_match.home_team_id)

            if not finalist_team:
                print(f"  Finalist team not found for cup {cup.name}, skipping...")
                continue

            # Get club information for winner
            winner_club = winner_team.club if winner_team.club else None
            winner_club_name = winner_club.name if winner_club else None
            winner_club_id = winner_club.id if winner_club else None
            winner_verein_id = winner_club.verein_id if winner_club else None

            # Get club information for finalist
            finalist_club = finalist_team.club if finalist_team.club else None
            finalist_club_name = finalist_club.name if finalist_club else None
            finalist_club_id = finalist_club.id if finalist_club else None
            finalist_verein_id = finalist_club.verein_id if finalist_club else None

            # Check if history entry already exists for this cup and season
            existing_entry = CupHistory.query.filter_by(
                cup_name=cup.name,
                season_id=season.id
            ).first()

            if existing_entry:
                print(f"  History entry already exists for cup {cup.name} in season {season.name}, skipping...")
                continue

            # Create cup history entry
            history_entry = CupHistory(
                cup_name=cup.name,
                cup_type=cup.cup_type,
                season_id=season.id,
                season_name=season.name,
                bundesland=cup.bundesland,
                landkreis=cup.landkreis,
                winner_team_id=winner_team.id,
                winner_team_name=winner_team.name,
                winner_club_name=winner_club_name,
                winner_club_id=winner_club_id,
                winner_verein_id=winner_verein_id,
                finalist_team_id=finalist_team.id,
                finalist_team_name=finalist_team.name,
                finalist_club_name=finalist_club_name,
                finalist_club_id=finalist_club_id,
                finalist_verein_id=finalist_verein_id,
                final_winner_score=final_match.home_score if final_match.home_team_id == final_match.winner_team_id else final_match.away_score,
                final_finalist_score=final_match.away_score if final_match.home_team_id == final_match.winner_team_id else final_match.home_score,
                final_winner_set_points=final_match.home_set_points if final_match.home_team_id == final_match.winner_team_id else final_match.away_set_points,
                final_finalist_set_points=final_match.away_set_points if final_match.home_team_id == final_match.winner_team_id else final_match.home_set_points
            )

            print(f"    Created history entry: {cup.name} -> Winner: {winner_team.name}, Finalist: {finalist_team.name}")
            db.session.add(history_entry)

        # Commit all history entries
        print("Committing all cup history entries to database...")
        db.session.commit()
        print(f"Cup history saved successfully for {len(cups)} cups")

        # Verify the data was saved
        total_entries = CupHistory.query.filter_by(season_id=season.id).count()
        print(f"Verification: {total_entries} cup history entries saved for season {season.name}")

    except Exception as e:
        print(f"Error saving cup history: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with season transition without saving cup history...")
        # Don't let history saving errors break the season transition
        try:
            db.session.rollback()
        except:
            pass


def save_team_cup_history(season):
    """Save the cup participation history for all teams in all cups for this season."""
    try:
        from models import TeamCupHistory, Cup, CupMatch, Team, Club, db

        print("Saving team cup history for season:", season.name)

        # Check if TeamCupHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'team_cup_history' not in existing_tables:
            print("TeamCupHistory table does not exist yet. Creating it...")
            # Create the table
            db.create_all()
            print("TeamCupHistory table created successfully.")

        # Get all cups for this season
        cups = Cup.query.filter_by(season_id=season.id).all()
        print(f"Found {len(cups)} cups for season {season.name}")

        for cup in cups:
            print(f"Processing cup: {cup.name}")

            # Get all teams that participated in this cup
            # Find all teams that played at least one match in this cup
            participating_teams_query = db.session.query(CupMatch.home_team_id, CupMatch.away_team_id).filter_by(
                cup_id=cup.id,
                is_played=True
            ).distinct()

            participating_team_ids = set()
            for home_id, away_id in participating_teams_query:
                participating_team_ids.add(home_id)
                participating_team_ids.add(away_id)

            print(f"  Found {len(participating_team_ids)} participating teams")

            for team_id in participating_team_ids:
                team = Team.query.get(team_id)
                if not team:
                    print(f"    Team {team_id} not found, skipping...")
                    continue

                # Check if history entry already exists for this team and cup
                existing_entry = TeamCupHistory.query.filter_by(
                    team_id=team_id,
                    cup_name=cup.name,
                    season_id=season.id
                ).first()

                if existing_entry:
                    print(f"    History entry already exists for team {team.name} in cup {cup.name}, skipping...")
                    continue

                # Determine how far this team reached
                team_matches = CupMatch.query.filter(
                    CupMatch.cup_id == cup.id,
                    CupMatch.is_played == True,
                    db.or_(CupMatch.home_team_id == team_id, CupMatch.away_team_id == team_id)
                ).order_by(CupMatch.round_number.desc()).all()

                if not team_matches:
                    print(f"    No matches found for team {team.name} in cup {cup.name}, skipping...")
                    continue

                # Find the last round this team played in
                last_round = max(match.round_number for match in team_matches)
                last_match = next(match for match in team_matches if match.round_number == last_round)

                # Determine if team won or lost their last match
                team_won_last_match = last_match.winner_team_id == team_id

                # Determine reached round and status
                is_winner = False
                is_finalist = False
                reached_round_number = last_round

                if team_won_last_match and last_round == cup.total_rounds:
                    # Team won the final
                    is_winner = True
                    is_finalist = True
                    reached_round = "Sieger"
                elif not team_won_last_match and last_round == cup.total_rounds:
                    # Team lost the final
                    is_finalist = True
                    reached_round = "Finale"
                elif team_won_last_match:
                    # Team won their last match but didn't reach the final
                    # This means they reached the next round but didn't play it (cup ended)
                    reached_round_number = min(last_round + 1, cup.total_rounds)
                    reached_round = get_round_name(reached_round_number, cup.total_rounds)
                else:
                    # Team lost their last match
                    reached_round = get_round_name(last_round, cup.total_rounds)

                # Get elimination details (if not winner)
                eliminated_by_team_id = None
                eliminated_by_team_name = None
                eliminated_by_club_name = None
                eliminated_by_verein_id = None
                elimination_match_score_for = None
                elimination_match_score_against = None
                elimination_match_set_points_for = None
                elimination_match_set_points_against = None

                if not is_winner:
                    # Find the match where this team was eliminated
                    elimination_match = None
                    if not team_won_last_match:
                        elimination_match = last_match
                    else:
                        # Team won their last match but was eliminated in a later round they didn't play
                        # This shouldn't happen in normal circumstances, but handle it gracefully
                        pass

                    if elimination_match:
                        # Determine the opponent
                        if elimination_match.home_team_id == team_id:
                            eliminated_by_team_id = elimination_match.away_team_id
                            elimination_match_score_for = elimination_match.home_score
                            elimination_match_score_against = elimination_match.away_score
                            elimination_match_set_points_for = elimination_match.home_set_points
                            elimination_match_set_points_against = elimination_match.away_set_points
                        else:
                            eliminated_by_team_id = elimination_match.home_team_id
                            elimination_match_score_for = elimination_match.away_score
                            elimination_match_score_against = elimination_match.home_score
                            elimination_match_set_points_for = elimination_match.away_set_points
                            elimination_match_set_points_against = elimination_match.home_set_points

                        # Get opponent team details
                        eliminated_by_team = Team.query.get(eliminated_by_team_id)
                        if eliminated_by_team:
                            eliminated_by_team_name = eliminated_by_team.name
                            if eliminated_by_team.club:
                                eliminated_by_club_name = eliminated_by_team.club.name
                                eliminated_by_verein_id = eliminated_by_team.club.verein_id

                # Get team club information
                club_name = team.club.name if team.club else None
                club_id = team.club.id if team.club else None
                verein_id = team.club.verein_id if team.club else None

                # Create team cup history entry
                history_entry = TeamCupHistory(
                    team_id=team.id,
                    team_name=team.name,
                    club_name=club_name,
                    club_id=club_id,
                    verein_id=verein_id,
                    cup_name=cup.name,
                    cup_type=cup.cup_type,
                    season_id=season.id,
                    season_name=season.name,
                    bundesland=cup.bundesland,
                    landkreis=cup.landkreis,
                    reached_round=reached_round,
                    reached_round_number=reached_round_number,
                    total_rounds=cup.total_rounds,
                    eliminated_by_team_id=eliminated_by_team_id,
                    eliminated_by_team_name=eliminated_by_team_name,
                    eliminated_by_club_name=eliminated_by_club_name,
                    eliminated_by_verein_id=eliminated_by_verein_id,
                    elimination_match_score_for=elimination_match_score_for,
                    elimination_match_score_against=elimination_match_score_against,
                    elimination_match_set_points_for=elimination_match_set_points_for,
                    elimination_match_set_points_against=elimination_match_set_points_against,
                    is_winner=is_winner,
                    is_finalist=is_finalist
                )

                print(f"    Created history entry: {team.name} -> {reached_round} in {cup.name}")
                db.session.add(history_entry)

        # Commit all history entries
        print("Committing all team cup history entries to database...")
        db.session.commit()
        print(f"Team cup history saved successfully for season {season.name}")

        # Verify the data was saved
        total_entries = TeamCupHistory.query.filter_by(season_id=season.id).count()
        print(f"Verification: {total_entries} team cup history entries saved for season {season.name}")

    except Exception as e:
        print(f"Error saving team cup history: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with season transition without saving team cup history...")
        # Don't let history saving errors break the season transition
        try:
            db.session.rollback()
        except:
            pass


def save_team_achievements(season):
    """Save team achievements (league championships and cup wins) for this season."""
    try:
        from models import TeamAchievement, League, Cup, CupMatch, Team, Club, db

        print("Saving team achievements for season:", season.name)

        # Check if TeamAchievement table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'team_achievement' not in existing_tables:
            print("TeamAchievement table does not exist yet. Creating it...")
            # Create the table
            db.create_all()
            print("TeamAchievement table created successfully.")

        achievements_saved = 0

        # Save league champions
        leagues = League.query.filter_by(season_id=season.id).all()
        print(f"Found {len(leagues)} leagues for season {season.name}")

        for league in leagues:
            print(f"Processing league: {league.name} (Level {league.level})")

            # Get league standings using the correct function
            standings = calculate_standings(league)
            if not standings:
                print(f"    No standings found for league {league.name}")
                continue

            # Get the champion (first place)
            champion_standing = standings[0]
            champion_team = champion_standing['team']

            if not champion_team:
                print(f"    Champion team not found for league {league.name}")
                continue

            # Check if achievement already exists
            existing_achievement = TeamAchievement.query.filter_by(
                team_id=champion_team.id,
                season_id=season.id,
                achievement_type='LEAGUE_CHAMPION',
                achievement_name=league.name
            ).first()

            if existing_achievement:
                print(f"    Achievement already exists for {champion_team.name} in {league.name}")
                continue

            # Get club information
            club_name = champion_team.club.name if champion_team.club else 'Unbekannt'
            club_id = champion_team.club.id if champion_team.club else None
            verein_id = champion_team.club.id if champion_team.club else None

            # Create league championship achievement
            achievement = TeamAchievement(
                team_id=champion_team.id,
                team_name=champion_team.name,
                club_name=club_name,
                club_id=club_id,
                verein_id=verein_id,
                season_id=season.id,
                season_name=season.name,
                achievement_type='LEAGUE_CHAMPION',
                achievement_name=league.name,
                achievement_level=league.level
            )

            print(f"    Created league championship: {champion_team.name} -> {league.name}")
            db.session.add(achievement)
            achievements_saved += 1

        # Save cup winners
        cups = Cup.query.filter_by(season_id=season.id).all()
        print(f"Found {len(cups)} cups for season {season.name}")

        for cup in cups:
            print(f"Processing cup: {cup.name} ({cup.cup_type})")

            # Find the final match
            final_matches = CupMatch.query.filter(
                CupMatch.cup_id == cup.id,
                CupMatch.round_number == cup.total_rounds,
                CupMatch.is_played == True,
                CupMatch.winner_team_id.isnot(None)
            ).all()

            if not final_matches:
                print(f"    No completed final found for cup {cup.name}")
                continue

            final_match = final_matches[0]
            winner_team = Team.query.get(final_match.winner_team_id)

            if not winner_team:
                print(f"    Winner team not found for cup {cup.name}")
                continue

            # Get finalist team
            finalist_team_id = final_match.home_team_id if final_match.away_team_id == final_match.winner_team_id else final_match.away_team_id
            finalist_team = Team.query.get(finalist_team_id)

            # Check if achievement already exists
            existing_achievement = TeamAchievement.query.filter_by(
                team_id=winner_team.id,
                season_id=season.id,
                achievement_type='CUP_WINNER',
                achievement_name=cup.name
            ).first()

            if existing_achievement:
                print(f"    Achievement already exists for {winner_team.name} in {cup.name}")
                continue

            # Get club information
            club_name = winner_team.club.name if winner_team.club else 'Unbekannt'
            club_id = winner_team.club.id if winner_team.club else None
            verein_id = winner_team.club.id if winner_team.club else None

            # Get final opponent information
            final_opponent_team_name = finalist_team.name if finalist_team else 'Unbekannt'
            final_opponent_club_name = finalist_team.club.name if finalist_team and finalist_team.club else 'Unbekannt'

            # Get final scores
            final_score_for = final_match.home_score if final_match.home_team_id == final_match.winner_team_id else final_match.away_score
            final_score_against = final_match.away_score if final_match.home_team_id == final_match.winner_team_id else final_match.home_score

            # Create cup winner achievement
            achievement = TeamAchievement(
                team_id=winner_team.id,
                team_name=winner_team.name,
                club_name=club_name,
                club_id=club_id,
                verein_id=verein_id,
                season_id=season.id,
                season_name=season.name,
                achievement_type='CUP_WINNER',
                achievement_name=cup.name,
                bundesland=cup.bundesland,
                landkreis=cup.landkreis,
                cup_type=cup.cup_type,
                final_opponent_team_name=final_opponent_team_name,
                final_opponent_club_name=final_opponent_club_name,
                final_score_for=final_score_for,
                final_score_against=final_score_against
            )

            print(f"    Created cup winner achievement: {winner_team.name} -> {cup.name}")
            db.session.add(achievement)
            achievements_saved += 1

        # Commit all achievements
        print("Committing all team achievements to database...")
        db.session.commit()
        print(f"Team achievements saved successfully: {achievements_saved} achievements for season {season.name}")

        # Verify the data was saved
        total_entries = TeamAchievement.query.filter_by(season_id=season.id).count()
        print(f"Verification: {total_entries} team achievement entries saved for season {season.name}")

    except Exception as e:
        print(f"Error saving team achievements: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with season transition without saving team achievements...")
        # Don't let achievement saving errors break the season transition
        try:
            db.session.rollback()
        except:
            pass


def get_round_name(round_number, total_rounds):
    """Convert round number to human-readable round name."""
    if round_number == total_rounds:
        return "Finale"
    elif round_number == total_rounds - 1:
        return "Halbfinale"
    elif round_number == total_rounds - 2:
        return "Viertelfinale"
    elif round_number == total_rounds - 3:
        return "Achtelfinale"
    elif round_number == total_rounds - 4:
        return "1/16-Finale"
    elif round_number == total_rounds - 5:
        return "1/32-Finale"
    else:
        return f"{round_number}. Runde"


def calculate_standings(league):
    """Calculate the standings for a league."""
    # Use direct query instead of relationship to ensure we get updated team assignments
    teams = Team.query.filter_by(league_id=league.id).all()
    standings = []

    # Check if any matches have been played in this league
    played_matches_count = Match.query.filter_by(league_id=league.id, is_played=True).count()

    for team in teams:
        # Get all matches for this team
        home_matches = Match.query.filter_by(home_team_id=team.id, league_id=league.id).all()
        away_matches = Match.query.filter_by(away_team_id=team.id, league_id=league.id).all()

        table_points = 0
        wins = 0
        draws = 0
        losses = 0
        match_points_for = 0
        match_points_against = 0
        pins_for = 0
        pins_against = 0

        # Calculate points from home matches
        for match in home_matches:
            if match.is_played:
                pins_for += match.home_score
                pins_against += match.away_score
                match_points_for += match.home_match_points
                match_points_against += match.away_match_points

                if match.home_match_points > match.away_match_points:
                    table_points += 2  # Win = 2 points in table
                    wins += 1
                elif match.home_match_points == match.away_match_points:
                    table_points += 1  # Draw = 1 point in table
                    draws += 1
                else:
                    losses += 1

        # Calculate points from away matches
        for match in away_matches:
            if match.is_played:
                pins_for += match.away_score
                pins_against += match.home_score
                match_points_for += match.away_match_points
                match_points_against += match.home_match_points

                if match.away_match_points > match.home_match_points:
                    table_points += 2  # Win = 2 points in table
                    wins += 1
                elif match.away_match_points == match.home_match_points:
                    table_points += 1  # Draw = 1 point in table
                    draws += 1
                else:
                    losses += 1

        # Create the standings entry for this team
        standings.append({
            'team': team,
            'points': table_points,  # Renamed from table_points to match what's used in the frontend
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'match_points_for': match_points_for,
            'match_points_against': match_points_against,
            'match_point_difference': match_points_for - match_points_against,
            'goals_for': pins_for,  # Renamed from pins_for to match what's used in the frontend
            'goals_against': pins_against,  # Renamed from pins_against to match what's used in the frontend
            'goal_difference': pins_for - pins_against  # Renamed from pin_difference to match what's used in the frontend
        })

    # Sort standings by table points, then match point difference, then total pins
    # Only sort if matches have been played, otherwise keep the original team order
    if played_matches_count > 0:
        standings.sort(key=lambda x: (x['points'], x['match_point_difference'], x['goal_difference']), reverse=True)

    return standings

def select_target_league_id(available_league_ids, old_to_new_mapping, new_leagues):
    """
    Select the best target league ID from available options.
    For now, uses the first available league, but could be enhanced with more logic.
    """
    for old_league_id in available_league_ids:
        new_league_id = old_to_new_mapping.get(old_league_id)
        if new_league_id:
            # Verify the league exists in new_leagues
            if any(nl.id == new_league_id for nl in new_leagues):
                return new_league_id
    return None

def _update_league_references(leagues, leagues_by_level):
    """
    Update league references in aufstieg_liga_id and abstieg_liga_id fields
    to use current season league IDs based on league attributes.
    """
    print("Updating league references to current season IDs...")

    # Create a mapping from league name to current league ID for each level
    league_lookup_by_name_level = {}
    for league in leagues:
        key = (league.name, league.level)
        league_lookup_by_name_level[key] = league.id

    updates_made = 0

    for league in leagues:
        # Update promotion league IDs
        if league.aufstieg_liga_id:
            old_ids = league.get_aufstieg_liga_ids()
            new_ids = []

            for old_id in old_ids:
                # Try to find the corresponding league in current season by ID first
                found_league = None
                for candidate in leagues:
                    if candidate.id == old_id:
                        found_league = candidate
                        break

                if found_league:
                    new_ids.append(found_league.id)
                else:
                    # League not found by ID, try to find by level relationship
                    target_level = league.level - 1
                    if target_level in leagues_by_level:
                        # Try to match by position in the original structure
                        # This is a heuristic - take leagues at target level in order
                        target_leagues = leagues_by_level[target_level]
                        if target_leagues:
                            # For simplicity, map to the first available league at target level
                            new_ids.append(target_leagues[0].id)

            if new_ids and new_ids != old_ids:
                league.aufstieg_liga_id = ';'.join(map(str, new_ids))
                updates_made += 1

        # Update relegation league IDs
        if league.abstieg_liga_id:
            old_ids = league.get_abstieg_liga_ids()
            new_ids = []

            for old_id in old_ids:
                # Try to find the corresponding league in current season by ID first
                found_league = None
                for candidate in leagues:
                    if candidate.id == old_id:
                        found_league = candidate
                        break

                if found_league:
                    new_ids.append(found_league.id)
                else:
                    # League not found by ID, try to find by level relationship
                    target_level = league.level + 1
                    if target_level in leagues_by_level:
                        # Try to match by position in the original structure
                        target_leagues = leagues_by_level[target_level]
                        if target_leagues:
                            # For simplicity, map to the first available league at target level
                            new_ids.append(target_leagues[0].id)

            if new_ids and new_ids != old_ids:
                league.abstieg_liga_id = ';'.join(map(str, new_ids))
                updates_made += 1

    if updates_made > 0:
        db.session.commit()
        print(f"Updated {updates_made} league references")
    else:
        print("No league reference updates needed")


def balance_promotion_relegation_spots(season_id, old_to_new_league_mapping=None):
    """
    Balance promotion and relegation spots between league levels.

    For each league level, check how many leagues from the next lower level
    feed into it, and adjust relegation spots accordingly.

    Args:
        season_id: The season ID to balance leagues for
        old_to_new_league_mapping: Optional mapping from old league IDs to new league IDs
                                  (used during season transitions)
    """
    print("Balancing promotion and relegation spots...")

    leagues = League.query.filter_by(season_id=season_id).order_by(League.level).all()
    leagues_by_level = {}

    # Group leagues by level
    for league in leagues:
        if league.level not in leagues_by_level:
            leagues_by_level[league.level] = []
        leagues_by_level[league.level].append(league)

    # First, update league IDs in promotion/relegation fields to current season IDs
    _update_league_references(leagues, leagues_by_level)

    changes_made = 0

    # Process each league level
    for level in sorted(leagues_by_level.keys()):
        current_level_leagues = leagues_by_level[level]

        # For each league in this level, check how many lower-level leagues feed into it
        for league in current_level_leagues:
            # Get leagues that can be promoted to this league
            feeding_leagues = []

            # Check all leagues in lower levels (higher level numbers)
            for lower_level in range(level + 1, max(leagues_by_level.keys()) + 1):
                if lower_level in leagues_by_level:
                    for lower_league in leagues_by_level[lower_level]:
                        # Check if this lower league can promote to our current league
                        promotion_league_ids = lower_league.get_aufstieg_liga_ids()

                        if league.id in promotion_league_ids:
                            feeding_leagues.append(lower_league)

            # Calculate required relegation spots
            required_relegation_spots = len(feeding_leagues)

            # Only adjust if there are feeding leagues and the current spots don't match
            if required_relegation_spots > 0:
                if league.anzahl_absteiger != required_relegation_spots:
                    old_spots = league.anzahl_absteiger
                    league.anzahl_absteiger = required_relegation_spots
                    changes_made += 1
                    print(f"  {league.name} (Level {league.level}): Changed relegation spots from {old_spots} to {required_relegation_spots}")

                # Also update promotion spots for the feeding leagues
                for feeding_league in feeding_leagues:
                    # Each feeding league should have at least 1 promotion spot to this level
                    if feeding_league.anzahl_aufsteiger < 1:
                        feeding_league.anzahl_aufsteiger = 1
                        print(f"    {feeding_league.name} (Level {feeding_league.level}): Set promotion spots to 1")
            elif required_relegation_spots == 0 and level < max(leagues_by_level.keys()):
                # This league has no feeding leagues but is not the bottom level
                # Keep at least 1 relegation spot unless it's the bottom level
                if league.anzahl_absteiger == 0:
                    league.anzahl_absteiger = 1
                    changes_made += 1
                    print(f"  {league.name} (Level {league.level}): Set minimum 1 relegation spot (no feeding leagues)")

    # Special case: Check if top-level leagues have promotion spots when they shouldn't
    top_level = min(leagues_by_level.keys()) if leagues_by_level else 1
    if top_level in leagues_by_level:
        for league in leagues_by_level[top_level]:
            # Top level leagues should not have promotion spots
            if league.anzahl_aufsteiger > 0:
                league.anzahl_aufsteiger = 0
                changes_made += 1
                print(f"  {league.name} (Level {league.level}): Removed promotion spots (top level)")

    # Special case: Check if bottom-level leagues have relegation spots when they shouldn't
    bottom_level = max(leagues_by_level.keys()) if leagues_by_level else 10
    if bottom_level in leagues_by_level:
        for league in leagues_by_level[bottom_level]:
            # Bottom level leagues should not have relegation spots
            if league.anzahl_absteiger > 0:
                league.anzahl_absteiger = 0
                changes_made += 1
                print(f"  {league.name} (Level {league.level}): Removed relegation spots (bottom level)")

    if changes_made > 0:
        db.session.commit()
        print(f"Balanced promotion/relegation spots: {changes_made} changes made")
    else:
        print("No changes needed for promotion/relegation spots")


def create_new_season(old_season):
    """Create a new season based on the old one."""
    print("Creating new season...")

    # Keep the old season as current for now
    # We'll only change it after everything is set up
    new_season = Season(
        name=f"Season {int(old_season.name.split()[-1]) + 1}",
        start_date=old_season.end_date + timedelta(days=30),  # Start 30 days after previous season
        end_date=old_season.end_date + timedelta(days=30 + 365),  # End roughly a year later
        is_current=False  # Start as not current, will set to current at the end
    )

    db.session.add(new_season)
    db.session.commit()
    print(f"Created new season: {new_season.name} (ID: {new_season.id})")

    # Create leagues for the new season
    old_leagues = League.query.filter_by(season_id=old_season.id).order_by(League.level).all()
    new_leagues = []
    old_to_new_league_mapping = {}  # Maps old league ID to new league ID

    print(f"Creating {len(old_leagues)} leagues for the new season...")
    for old_league in old_leagues:
        new_league = League(
            name=old_league.name,
            level=old_league.level,
            season_id=new_season.id,
            bundesland=old_league.bundesland,
            landkreis=old_league.landkreis,
            altersklasse=old_league.altersklasse,
            anzahl_aufsteiger=old_league.anzahl_aufsteiger,
            anzahl_absteiger=old_league.anzahl_absteiger,
            aufstieg_liga_id=old_league.aufstieg_liga_id,
            abstieg_liga_id=old_league.abstieg_liga_id
        )
        new_leagues.append(new_league)
        db.session.add(new_league)

    db.session.commit()

    # Create mapping from old league IDs to new league IDs
    for i, old_league in enumerate(old_leagues):
        old_to_new_league_mapping[old_league.id] = new_leagues[i].id

    # Balance promotion and relegation spots for the new season
    balance_promotion_relegation_spots(new_season.id, old_to_new_league_mapping)

    print(f"Created {len(new_leagues)} leagues for the new season")
    print(f"League ID mapping: {old_to_new_league_mapping}")

    # Create a mapping of teams to their new leagues
    team_to_new_league = {}

    # First, get the final standings for each old league
    for i, old_league in enumerate(old_leagues):
        standings = calculate_standings(old_league)
        print(f"Old league {old_league.name} (Level {old_league.level}) has {len(standings)} teams")

        # Map each team to its corresponding new league and set status flags
        for j, standing in enumerate(standings):
            team = standing['team']
            target_new_league_id = None

            # Store previous season information
            team.previous_season_position = j + 1
            team.previous_season_league_level = old_league.level
            team.previous_season_status = None  # Reset status first

            # Apply promotions/relegations based on standings and set status
            if j < old_league.anzahl_aufsteiger and i > 0:  # Promotion (except for top league)
                team.previous_season_status = 'promoted'
                # Get promotion league IDs from the old league
                promotion_league_ids = old_league.get_aufstieg_liga_ids()
                if promotion_league_ids:
                    target_new_league_id = select_target_league_id(promotion_league_ids, old_to_new_league_mapping, new_leagues)
                    if target_new_league_id:
                        target_league_name = next((nl.name for nl in new_leagues if nl.id == target_new_league_id), "Unknown")
                        print(f"Team {team.name} promoted from {old_league.name} to {target_league_name}")
                    else:
                        print(f"WARNING: Could not find valid promotion league for {team.name} from {old_league.name}")
                else:
                    print(f"WARNING: No promotion leagues defined for {old_league.name}")
            elif j >= len(standings) - old_league.anzahl_absteiger and i < len(old_leagues) - 1:  # Relegation (except for bottom league)
                team.previous_season_status = 'relegated'
                # Get relegation league IDs from the old league
                relegation_league_ids = old_league.get_abstieg_liga_ids()
                if relegation_league_ids:
                    target_new_league_id = select_target_league_id(relegation_league_ids, old_to_new_league_mapping, new_leagues)
                    if target_new_league_id:
                        target_league_name = next((nl.name for nl in new_leagues if nl.id == target_new_league_id), "Unknown")
                        print(f"Team {team.name} relegated from {old_league.name} to {target_league_name}")
                    else:
                        print(f"WARNING: Could not find valid relegation league for {team.name} from {old_league.name}")
                else:
                    print(f"WARNING: No relegation leagues defined for {old_league.name}")
            elif j == 0 and old_league.level == 1:  # Champion of top league
                team.previous_season_status = 'champion'
                print(f"Team {team.name} is champion of level {old_league.level}")
                # Champions stay in the same league
                target_new_league_id = old_to_new_league_mapping.get(old_league.id)
            else:
                # Team stays in the same league
                target_new_league_id = old_to_new_league_mapping.get(old_league.id)

            # Map team to the target league
            if target_new_league_id:
                team_to_new_league[team.id] = target_new_league_id
                target_league_name = next((nl.name for nl in new_leagues if nl.id == target_new_league_id), "Unknown")
                print(f"Team {team.name} (ID: {team.id}) mapped to new league {target_league_name} (ID: {target_new_league_id})")
            else:
                print(f"WARNING: Could not determine target league for team {team.name}")

    # Now update all teams to point to their new leagues
    teams = Team.query.all()
    updated_teams = 0
    unmapped_teams = []

    for team in teams:
        if team.id in team_to_new_league:
            old_league_id = team.league_id
            team.league_id = team_to_new_league[team.id]
            updated_teams += 1
            print(f"Team {team.name} moved from league {old_league_id} to league {team.league_id}")
        elif team.target_league_level is not None:
            # This is a new team added via cheat function - assign to target league
            target_league = None
            for new_league in new_leagues:
                if (new_league.level == team.target_league_level and
                    new_league.bundesland == team.target_league_bundesland and
                    new_league.landkreis == team.target_league_landkreis and
                    new_league.altersklasse == team.target_league_altersklasse):
                    target_league = new_league
                    break

            if target_league:
                team.league_id = target_league.id
                # Clear the temporary fields
                team.target_league_level = None
                team.target_league_bundesland = None
                team.target_league_landkreis = None
                team.target_league_altersklasse = None
                updated_teams += 1
                print(f"New team {team.name} assigned to target league {target_league.name}")
            else:
                unmapped_teams.append(team)
                print(f"WARNING: Could not find target league for new team {team.name}")
        else:
            # If for some reason we don't have a mapping, try to map to the same league
            old_league = League.query.get(team.league_id)
            if old_league:
                # Try to find the corresponding new league using the mapping
                new_league_id = old_to_new_league_mapping.get(old_league.id)
                if new_league_id:
                    team.league_id = new_league_id
                    updated_teams += 1
                    new_league_name = next((nl.name for nl in new_leagues if nl.id == new_league_id), "Unknown")
                    print(f"Team {team.name} mapped to corresponding league {new_league_name} using ID mapping")
                else:
                    # Fallback: find a league with the same level
                    for new_league in new_leagues:
                        if new_league.level == old_league.level:
                            team.league_id = new_league.id
                            updated_teams += 1
                            print(f"Team {team.name} mapped to same level league {new_league.name} (fallback)")
                            break
                    else:
                        unmapped_teams.append(team)
                        print(f"WARNING: Could not find new league for team {team.name} (old level: {old_league.level})")
            else:
                unmapped_teams.append(team)
                print(f"WARNING: Team {team.name} has invalid old league reference")

    db.session.commit()
    print(f"Updated {updated_teams} teams to point to their new leagues")

    if unmapped_teams:
        print(f"WARNING: {len(unmapped_teams)} teams could not be mapped to new leagues")

    # Refresh the session to ensure relationships are updated
    db.session.expire_all()

    # Generate fixtures for the new season
    total_fixtures_generated = 0
    for new_league in new_leagues:
        # Verify that the league has teams before generating fixtures
        league_teams = Team.query.filter_by(league_id=new_league.id).all()
        print(f"League {new_league.name} (Level {new_league.level}) has {len(league_teams)} teams")

        if len(league_teams) >= 2:
            generate_fixtures(new_league, new_season)
            fixtures_count = Match.query.filter_by(league_id=new_league.id, season_id=new_season.id).count()
            total_fixtures_generated += fixtures_count
            print(f"Generated {fixtures_count} fixtures for league {new_league.name}")
        else:
            print(f"WARNING: League {new_league.name} has only {len(league_teams)} teams, skipping fixture generation")

    print(f"Total fixtures generated: {total_fixtures_generated}")

    print("Generated fixtures for all leagues in the new season")

    # Create cups for the new season
    from app import auto_initialize_cups
    try:
        auto_initialize_cups(new_season.id)
        print("Auto-initialized cups for the new season")
    except Exception as e:
        print(f"Error initializing cups: {str(e)}")

    # Age all players by 1 year
    players = Player.query.all()
    for player in players:
        player.age += 1

    db.session.commit()
    print(f"Aged {len(players)} players by 1 year")

    # Note: Player redistribution is disabled during season transitions to avoid conflicts
    # with the game's dynamic player assignment system. The current system assigns players
    # to teams dynamically based on availability and strength for each match day.
    #
    # TODO: Future improvement - integrate permanent team assignments with match assignments
    # so that players can only play for teams they are permanently assigned to.

    # Now that everything is set up, make the new season current
    old_season.is_current = False
    new_season.is_current = True
    db.session.commit()
    print(f"Set {new_season.name} as the current season")
