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
        current_match_day = match.match_day if match else None

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

            # Home player performance
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

            # Away player performance
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
            db.session.execute(
                db.update(Player)
                .where(Player.id.in_(player_ids))
                .values(
                    has_played_current_matchday=True,
                    last_played_matchday=match.match_day
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
        if not matches_data:
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

    # Step 4: Determine clubs and teams playing
    clubs_with_matches = set()
    teams_playing = {}

    for match_data in matches_data:
        home_club_id = match_data.home_club_id
        away_club_id = match_data.away_club_id

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

    # Step 7: Simulate all matches in parallel
    simulation_start = time.time()
    results, all_performances, all_player_updates, all_lane_records = simulate_matches_parallel(
        matches_data,
        club_team_players,
        next_match_day,
        cache
    )
    print(f"Simulated {len(results)} matches in parallel in {time.time() - simulation_start:.3f}s")

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

    return {
        'season': season.name,
        'matches_simulated': len(results),
        'results': results,
        'match_day': next_match_day
    }


def find_next_match_day(season_id):
    """Find the next match day to simulate."""
    from sqlalchemy import text

    result = db.session.execute(
        text("""
            SELECT MIN(match_day)
            FROM match
            WHERE season_id = :season_id
                AND is_played = 0
                AND match_day IS NOT NULL
        """),
        {"season_id": season_id}
    ).scalar()

    return result


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
        """Simulate a single match in a thread."""
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
        if hasattr(obj, attr):
            return getattr(obj, attr)
        elif isinstance(obj, dict):
            return obj.get(attr, default)
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
        # Update match records
        match_updates = {}
        for i, result in enumerate(results):
            match_id = result.get('match_id')
            if match_id:
                match_updates[match_id] = {
                    'home_score': result['home_score'],
                    'away_score': result['away_score'],
                    'home_match_points': result['home_match_points'],
                    'away_match_points': result['away_match_points'],
                    'is_played': True,
                    'match_date': datetime.now(timezone.utc)
                }

        # Batch update matches
        for match_id, updates in match_updates.items():
            db.session.execute(
                db.update(Match)
                .where(Match.id == match_id)
                .values(**updates)
            )

        # Batch create performances
        if all_performances:
            # Convert performance data to proper format and add missing fields
            performance_dicts = []
            for i, perf in enumerate(all_performances):
                if isinstance(perf, dict):
                    # Add missing required fields
                    perf_dict = perf.copy()

                    # Find the corresponding match_id from results
                    result_index = i // 12  # 12 performances per match (6 home + 6 away)
                    if result_index < len(results):
                        perf_dict['match_id'] = results[result_index].get('match_id')

                    # Determine team_id and is_home_team based on position in list
                    player_index_in_match = i % 12
                    perf_dict['is_home_team'] = player_index_in_match < 6

                    # We'll need to get team_id from the match data
                    # For now, set a placeholder - this should be improved
                    perf_dict['team_id'] = None

                    performance_dicts.append(perf_dict)
                else:
                    # Convert object to dict if needed
                    performance_dicts.append(perf.__dict__)

            # Filter out performances without required fields
            valid_performances = [p for p in performance_dicts if p.get('match_id') and p.get('player_id')]

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


def simulate_match_day_fallback(season):
    """Fallback to original simulation method if optimized version fails."""
    print("Using fallback simulation method")

    results = []

    # Get all leagues in the season
    leagues = season.leagues

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

    # Continue with original logic...
    # (Rest of original implementation would go here if needed)

    return {
        'season': season.name,
        'matches_simulated': 0,
        'results': [],
        'message': 'Fallback simulation not fully implemented'
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

    # First, ensure all leagues have fixtures generated
    for league in leagues:
        # Generate matches if they don't exist
        if not league.matches:
            print(f"No matches found for league {league.name}, generating fixtures...")
            generate_fixtures(league, season)

    # Find the maximum match day across all leagues
    max_match_day = 0
    for league in leagues:
        # Get the highest match day for this league
        highest_match_day = db.session.query(db.func.max(Match.match_day)).filter(
            Match.league_id == league.id,
            Match.season_id == season.id
        ).scalar() or 0
        max_match_day = max(max_match_day, highest_match_day)

    print(f"Maximum match day across all leagues: {max_match_day}")

    # Simulate match day by match day
    for match_day in range(1, max_match_day + 1):
        print(f"Simulating match day {match_day} across all leagues")

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
                match_day=match_day
            ).all()

            for match in unplayed_matches:
                home_club_id = match.home_team.club_id
                away_club_id = match.away_team.club_id

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
            print(f"Error setting player availability for match day {match_day}: {str(e)}")
            raise

        # Assign players to teams for each club
        club_team_players = {}
        for club_id in clubs_with_matches:
            club_team_players[club_id] = assign_players_to_teams_for_match_day(
                club_id,
                match_day,
                season.id
            )

        # Simulate matches for this match day across all leagues
        match_day_results = []
        all_player_updates = []

        for league in leagues:
            # Get all unplayed matches for this match day in this league
            unplayed_matches = Match.query.filter_by(
                league_id=league.id,
                season_id=season.id,
                is_played=False,
                match_day=match_day
            ).all()

            if unplayed_matches:
                print(f"Simulating match day {match_day} for league {league.name} with {len(unplayed_matches)} matches")

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
                match_result['match_day'] = match_day

                match_day_results.append(match_result)

                # Collect player updates for batch processing
                # Convert player objects to IDs if necessary
                home_player_ids = [p.id if hasattr(p, 'id') else p for p in home_players]
                away_player_ids = [p.id if hasattr(p, 'id') else p for p in away_players]

                for player_id in home_player_ids + away_player_ids:
                    all_player_updates.append((player_id, True, match_day))

        # Batch update player flags
        if all_player_updates:
            batch_update_player_flags(all_player_updates)

        # Save all changes to database after each match day
        db.session.commit()
        print(f"Simulated {len(match_day_results)} matches for match day {match_day}")

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
    if create_new_season and all(match.is_played for league in leagues for match in league.matches):
        print("All matches played, processing end of season...")
        process_end_of_season(season)

        # Get the new current season
        new_season = Season.query.filter_by(is_current=True).first()
        if new_season and new_season.id != season.id:
            new_season_created = True
            new_season_id = new_season.id
            print(f"New season created: {new_season.name} (ID: {new_season.id})")

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
    teams = list(league.teams)

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
    leagues = League.query.filter_by(season_id=season.id).order_by(League.level).all()

    # Process each league level
    for i, league in enumerate(leagues):
        # Calculate league standings
        standings = calculate_standings(league)

        # Process promotions (except for the top league)
        if i > 0:
            promote_teams(standings, leagues[i-1])

        # Process relegations (except for the bottom league)
        if i < len(leagues) - 1:
            relegate_teams(standings, leagues[i+1])

    # Create new season
    create_new_season(season)

def calculate_standings(league):
    """Calculate the standings for a league."""
    teams = league.teams
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

def promote_teams(standings, higher_league):
    """Promote top teams to a higher league."""
    # Promote top 2 teams
    for i in range(min(2, len(standings))):
        team = standings[i]['team']
        team.league_id = higher_league.id

    db.session.commit()

def relegate_teams(standings, lower_league):
    """Relegate bottom teams to a lower league."""
    # Relegate bottom 2 teams
    for i in range(max(0, len(standings) - 2), len(standings)):
        team = standings[i]['team']
        team.league_id = lower_league.id

    db.session.commit()

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
            anzahl_absteiger=old_league.anzahl_absteiger
        )
        new_leagues.append(new_league)
        db.session.add(new_league)

    db.session.commit()
    print(f"Created {len(new_leagues)} leagues for the new season")

    # Create a mapping of teams to their new leagues
    team_to_new_league = {}

    # First, get the final standings for each old league
    for i, old_league in enumerate(old_leagues):
        standings = calculate_standings(old_league)

        # Map each team to its corresponding new league
        for j, standing in enumerate(standings):
            team = standing['team']
            # By default, teams stay in the same level
            target_level = old_league.level

            # Apply promotions/relegations based on standings
            if j < old_league.anzahl_aufsteiger and i > 0:  # Promotion (except for top league)
                target_level = old_league.level - 1
            elif j >= len(standings) - old_league.anzahl_absteiger and i < len(old_leagues) - 1:  # Relegation (except for bottom league)
                target_level = old_league.level + 1

            # Find the new league with the matching level
            for new_league in new_leagues:
                if new_league.level == target_level:
                    team_to_new_league[team.id] = new_league.id
                    break

    # Now update all teams to point to their new leagues
    teams = Team.query.all()
    for team in teams:
        if team.id in team_to_new_league:
            team.league_id = team_to_new_league[team.id]
        else:
            # If for some reason we don't have a mapping, find a league with the same level
            old_league = League.query.get(team.league_id)
            if old_league:
                for new_league in new_leagues:
                    if new_league.level == old_league.level:
                        team.league_id = new_league.id
                        break

    db.session.commit()
    print(f"Updated {len(teams)} teams to point to their new leagues")

    # Generate fixtures for the new season
    for new_league in new_leagues:
        generate_fixtures(new_league, new_season)

    print("Generated fixtures for all leagues in the new season")

    # Age all players by 1 year
    players = Player.query.all()
    for player in players:
        player.age += 1

    db.session.commit()
    print(f"Aged {len(players)} players by 1 year")

    # Now that everything is set up, make the new season current
    old_season.is_current = False
    new_season.is_current = True
    db.session.commit()
    print(f"Set {new_season.name} as the current season")
