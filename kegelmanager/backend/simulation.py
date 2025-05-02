import numpy as np
from datetime import datetime, timedelta, timezone
from models import db, Match, Player, Team, League, Season

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
    from models import PlayerMatchPerformance, db, Player, Team
    import random

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
            # Calculate a weighted rating based on key attributes
            # Strength is the most important, but we also consider other attributes
            return (
                player.strength * 0.5 +  # 50% weight on strength
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


    # Add home advantage
    home_advantage = 1.05  # 5% advantage for home team

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
            # Base score depends on player strength and league level
            base_score = (home_player.strength * 1.5) + 450  # 450-600 base for strength 0-100

            # Adjust for player attributes
            ausdauer_factor = max(0.8, home_player.ausdauer / 100 - (lane * 0.05))  # Decreases with each lane

            # Apply home advantage
            base_score *= home_advantage

            # Add randomness using normal distribution
            # Mean of 1.0, standard deviation based on konstanz (higher konstanz = lower std dev)
            konstanz_factor = home_player.konstanz / 100  # 0-1 scale
            std_dev = 0.15 * (2 - konstanz_factor)
            randomness = np.random.normal(1.0, std_dev)

            # Calculate lane score
            lane_score = int(base_score * ausdauer_factor * randomness)

            # Calculate score based solely on player strength and attributes
            # Base score range: 120-180 for strength 0-99
            mean_score = 120 + (home_player.strength * 0.6)

            # Base standard deviation and error values
            std_dev = 12 - (home_player.konstanz / 20)  # 12 to 7 based on konstanz
            fehler_mean = 2.0 - (home_player.sicherheit / 50)  # 2.0 to 0.0 based on sicherheit
            fehler_std = 0.8

            # Adjust for player position in the match (start, middle, end)
            # Depending on which lane we're on, use different attributes
            if lane == 0:  # First lane - use 'start' attribute
                position_factor = 0.8 + (home_player.start / 500)  # 0.8 to 1.0 range
                mean_score *= position_factor
            elif lane == 3:  # Last lane - use 'schluss' attribute and 'drucksicherheit'
                # Base position factor from 'schluss' attribute
                position_factor = 0.8 + (home_player.schluss / 500)  # 0.8 to 1.0 range

                # Add pressure factor for the last lane (only if we have previous lanes to compare)
                if len(home_player_lanes) > 0:
                    # For the last lane, apply drucksicherheit factor
                    # Players with high drucksicherheit perform better on the last lane
                    pressure_factor = 0.9 + (home_player.drucksicherheit / 500)  # 0.9 to 1.1 range
                    position_factor *= pressure_factor

                mean_score *= position_factor
            else:  # Middle lanes - use 'mitte' attribute
                position_factor = 0.8 + (home_player.mitte / 500)  # 0.8 to 1.0 range
                mean_score *= position_factor

            # Konstanz and Sicherheit are already factored into the base values
            # No additional adjustments needed here

            # Generate score from normal distribution and ensure it's within reasonable bounds
            lane_score = int(np.random.normal(mean_score, std_dev))
            # Ensure score is at least 80 and at most 200
            lane_score = max(80, min(200, lane_score))

            # Generate fehler from normal distribution and ensure it's a non-negative integer
            lane_fehler = int(max(0, np.random.normal(fehler_mean, fehler_std)))

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
            home_player_fehler += lane_fehler

        # Simulate 4 lanes for away player
        away_player_lanes = []
        away_player_total = 0
        away_player_volle = 0
        away_player_raeumer = 0
        away_player_fehler = 0

        for lane in range(4):
            # Base score depends on player strength and league level
            base_score = (away_player.strength * 1.5) + 450  # 450-600 base for strength 0-100

            # Adjust for player attributes
            ausdauer_factor = max(0.8, away_player.ausdauer / 100 - (lane * 0.05))  # Decreases with each lane

            # Add randomness using normal distribution
            # Mean of 1.0, standard deviation based on konstanz (higher konstanz = lower std dev)
            konstanz_factor = away_player.konstanz / 100  # 0-1 scale
            std_dev = 0.15 * (2 - konstanz_factor)
            randomness = np.random.normal(1.0, std_dev)

            # Calculate lane score
            lane_score = int(base_score * ausdauer_factor * randomness)

            # Calculate score based solely on player strength and attributes
            # Base score range: 120-180 for strength 0-99
            mean_score = 120 + (away_player.strength * 0.6)

            # Base standard deviation and error values
            std_dev = 12 - (away_player.konstanz / 20)  # 12 to 7 based on konstanz
            fehler_mean = 2.0 - (away_player.sicherheit / 50)  # 2.0 to 0.0 based on sicherheit
            fehler_std = 0.8

            # Apply away factor (players with high 'auswaerts' attribute perform better away)
            # For away games, apply the auswaerts attribute (0-99)
            # A player with auswaerts 50 will have no adjustment
            # A player with auswaerts 99 will get +10% boost
            # A player with auswaerts 0 will get -10% penalty
            away_factor = 0.9 + (away_player.auswaerts / 1000)  # 0.9 to 1.1 range
            mean_score *= away_factor

            # Adjust for player position in the match (start, middle, end)
            # Depending on which lane we're on, use different attributes
            if lane == 0:  # First lane - use 'start' attribute
                position_factor = 0.8 + (away_player.start / 500)  # 0.8 to 1.0 range
                mean_score *= position_factor
            elif lane == 3:  # Last lane - use 'schluss' attribute and 'drucksicherheit'
                # Base position factor from 'schluss' attribute
                position_factor = 0.8 + (away_player.schluss / 500)  # 0.8 to 1.0 range

                # Add pressure factor for the last lane (only if we have previous lanes to compare)
                if len(away_player_lanes) > 0:
                    # For the last lane, apply drucksicherheit factor
                    # Players with high drucksicherheit perform better on the last lane
                    pressure_factor = 0.9 + (away_player.drucksicherheit / 500)  # 0.9 to 1.1 range
                    position_factor *= pressure_factor

                mean_score *= position_factor
            else:  # Middle lanes - use 'mitte' attribute
                position_factor = 0.8 + (away_player.mitte / 500)  # 0.8 to 1.0 range
                mean_score *= position_factor

            # Konstanz and Sicherheit are already factored into the base values
            # No additional adjustments needed here

            # Generate score from normal distribution and ensure it's within reasonable bounds
            lane_score = int(np.random.normal(mean_score, std_dev))

            # Generate fehler from normal distribution and ensure it's a non-negative integer
            lane_fehler = int(max(0, np.random.normal(fehler_mean, fehler_std)))

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
            away_player_fehler += lane_fehler

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
    """Simulate one match day for all leagues in a season."""
    from club_player_assignment import assign_players_to_teams_for_match_day

    results = []

    # Find the global next match day across all leagues
    global_next_match_day = None

    # Get all leagues in the season
    leagues = season.leagues

    # First, ensure all leagues have fixtures generated
    for league in leagues:
        # Check if the league has matches with match_day set
        has_match_days = Match.query.filter(
            Match.league_id == league.id,
            Match.season_id == season.id,
            Match.match_day.isnot(None)
        ).count() > 0

        # If no matches with match_day, regenerate fixtures
        if not has_match_days:
            print(f"League {league.name} has no matches with match_day set. Generating fixtures...")
            # Delete any existing matches without match_day
            existing_matches = Match.query.filter_by(
                league_id=league.id,
                season_id=season.id
            ).all()

            for match in existing_matches:
                db.session.delete(match)

            db.session.commit()

            # Generate new fixtures with proper match_day values
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

    print(f"Simulating global match day {global_next_match_day} across all leagues")

    # Reset player availability flags for all players
    reset_player_availability()

    # Determine which clubs have matches on this match day
    clubs_with_matches = set()
    teams_playing = {}  # Dictionary to track how many teams each club has playing

    # First, identify all clubs that have teams playing on this match day
    for league, league_next_match_day in unplayed_match_days:
        if league_next_match_day == global_next_match_day:
            unplayed_matches = Match.query.filter_by(
                league_id=league.id,
                season_id=season.id,
                is_played=False,
                match_day=global_next_match_day
            ).all()

            for match in unplayed_matches:
                home_club_id = match.home_team.club_id
                away_club_id = match.away_team.club_id

                clubs_with_matches.add(home_club_id)
                clubs_with_matches.add(away_club_id)

                # Count how many teams each club has playing
                teams_playing[home_club_id] = teams_playing.get(home_club_id, 0) + 1
                teams_playing[away_club_id] = teams_playing.get(away_club_id, 0) + 1

    # Now determine player availability for each club
    for club_id in clubs_with_matches:
        determine_player_availability(club_id, teams_playing.get(club_id, 0))

    # Assign players to teams for each club
    club_team_players = {}
    for club_id in clubs_with_matches:
        club_team_players[club_id] = assign_players_to_teams_for_match_day(
            club_id,
            global_next_match_day,
            season.id
        )

    # Now simulate only matches for this global match day
    for league, league_next_match_day in unplayed_match_days:
        # Only simulate matches for leagues that have this match day
        if league_next_match_day == global_next_match_day:
            # Get all unplayed matches for this match day in this league
            unplayed_matches = Match.query.filter_by(
                league_id=league.id,
                season_id=season.id,
                is_played=False,
                match_day=global_next_match_day
            ).all()

            print(f"Simulating match day {global_next_match_day} for league {league.name} with {len(unplayed_matches)} matches")

            # Simulate each match in this match day
            for match in unplayed_matches:
                home_team = match.home_team
                away_team = match.away_team

                # Pass the match instance and pre-assigned players to save player performances
                match_result = simulate_match(
                    home_team,
                    away_team,
                    match=match,
                    home_team_players=club_team_players.get(home_team.club_id, {}).get(home_team.id, []),
                    away_team_players=club_team_players.get(away_team.club_id, {}).get(away_team.id, [])
                )

                # Update match record
                match.home_score = match_result['home_score']
                match.away_score = match_result['away_score']
                match.home_match_points = match_result['home_match_points']
                match.away_match_points = match_result['away_match_points']
                match.is_played = True

                # Keep the original scheduled date
                if not match.match_date:
                    match.match_date = datetime.now(timezone.utc)

                # Add team names to the result for better display
                match_result['home_team_name'] = home_team.name
                match_result['away_team_name'] = away_team.name
                match_result['league_name'] = league.name
                match_result['match_day'] = global_next_match_day

                results.append(match_result)

    # Save all changes to database
    db.session.commit()

    # Reset player flags after the match day is complete
    reset_player_matchday_flags()

    return {
        'season': season.name,
        'matches_simulated': len(results),
        'results': results,
        'match_day': global_next_match_day
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

    # Get all players from this club
    club_players = Player.query.filter_by(club_id=club_id).all()

    if not club_players:
        print(f"No players found for club ID {club_id}")
        return

    # Calculate how many players we need at minimum (6 per team)
    min_players_needed = teams_playing * 6

    # If we don't have enough players, make all available
    if len(club_players) <= min_players_needed:
        # Make sure all players are available using bulk update
        db.session.execute(
            db.update(Player)
            .where(Player.club_id == club_id)
            .values(is_available_current_matchday=True)
        )
        db.session.commit()
        print(f"Club ID {club_id} has only {len(club_players)} players, need {min_players_needed}. All players will be available.")
        return

    # Get all player IDs
    player_ids = [p.id for p in club_players]

    # Determine unavailable players (16.7% chance of being unavailable)
    unavailable_player_ids = []
    for player_id in player_ids:
        # 16.7% chance of being unavailable
        if random.random() < 0.167:
            unavailable_player_ids.append(player_id)

    # Mark selected players as unavailable using bulk update
    if unavailable_player_ids:
        db.session.execute(
            db.update(Player)
            .where(Player.id.in_(unavailable_player_ids))
            .values(is_available_current_matchday=False)
        )
        db.session.commit()

    # Check if we still have enough available players
    available_players = len(player_ids) - len(unavailable_player_ids)

    # If we don't have enough available players, make some unavailable players available again
    if available_players < min_players_needed:
        # Calculate how many more players we need
        players_needed = min_players_needed - available_players

        # Randomly select players to make available again
        if players_needed > 0 and unavailable_player_ids:
            players_to_make_available = random.sample(unavailable_player_ids, min(players_needed, len(unavailable_player_ids)))

            # Mark selected players as available again using bulk update
            if players_to_make_available:
                db.session.execute(
                    db.update(Player)
                    .where(Player.id.in_(players_to_make_available))
                    .values(is_available_current_matchday=True)
                )
                db.session.commit()

    # Recalculate the actual number of available players after all changes using a database query
    available_players_count = db.session.query(db.func.count()).filter(
        Player.club_id == club_id,
        Player.is_available_current_matchday == True
    ).scalar()

    total_players_count = db.session.query(db.func.count()).filter(
        Player.club_id == club_id
    ).scalar()


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

        # Reset player availability flags for all players
        reset_player_availability()

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

        # Now determine player availability for each club
        for club_id in clubs_with_matches:
            determine_player_availability(club_id, teams_playing.get(club_id, 0))

        # Assign players to teams for each club
        club_team_players = {}
        for club_id in clubs_with_matches:
            club_team_players[club_id] = assign_players_to_teams_for_match_day(
                club_id,
                match_day,
                season.id
            )

        # Now simulate matches for this match day across all leagues
        match_day_results = []
        for league in leagues:
            # Get all unplayed matches for this match day in this league
            unplayed_matches = Match.query.filter_by(
                league_id=league.id,
                season_id=season.id,
                is_played=False,
                match_day=match_day
            ).all()

            print(f"Simulating match day {match_day} for league {league.name} with {len(unplayed_matches)} matches")

            # Simulate each match in this match day
            for match in unplayed_matches:
                home_team = match.home_team
                away_team = match.away_team

                # Pass the match instance and pre-assigned players to save player performances
                match_result = simulate_match(
                    home_team,
                    away_team,
                    match=match,
                    home_team_players=club_team_players.get(home_team.club_id, {}).get(home_team.id, []),
                    away_team_players=club_team_players.get(away_team.club_id, {}).get(away_team.id, [])
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
    """Generate fixtures (matches) for a league in a season using a round-robin tournament algorithm."""
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

    # First half of the season (round 1)
    for round_num in range(num_rounds):
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
            match = Match(
                home_team_id=teams[home_idx].id,
                away_team_id=teams[away_idx].id,
                league_id=league.id,
                season_id=season.id,
                match_day=match_day,
                round=1,  # First half of season
                is_played=False
            )
            db.session.add(match)

    # Second half of the season (round 2) - reverse home/away
    for round_num in range(num_rounds):
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
            match = Match(
                home_team_id=teams[home_idx].id,
                away_team_id=teams[away_idx].id,
                league_id=league.id,
                season_id=season.id,
                match_day=match_day,
                round=2,  # Second half of season
                is_played=False
            )
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
