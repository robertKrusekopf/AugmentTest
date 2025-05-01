import random
from datetime import datetime, timedelta, timezone
from models import db, Match, Player, Team, League, Season

def calculate_team_strength(team):
    """Calculate the overall strength of a team based on its players."""
    if not team.players:
        return 50  # Default value if no players

    total_strength = sum(player.strength for player in team.players)
    return total_strength / len(team.players)

def simulate_match(home_team, away_team, match=None):
    """Simulate a bowling match between two teams and return the result.

    In bowling, 6 players from each team play 4 lanes with 30 throws each.
    The total score of all players determines the winner.
    """
    from models import PlayerMatchPerformance, db

    # Get 6 players from each team
    home_players = home_team.players[:6] if len(home_team.players) >= 6 else home_team.players
    away_players = away_team.players[:6] if len(away_team.players) >= 6 else away_team.players

    # Make sure we have enough players (at least 1)
    if not home_players or not away_players:
        # Default scores if not enough players
        home_score = 3000 if home_players else 0
        away_score = 3000 if away_players else 0

        return {
            'home_team': home_team.name,
            'away_team': away_team.name,
            'home_score': home_score,
            'away_score': away_score,
            'winner': home_team.name if home_score > away_score else (away_team.name if away_score > home_score else 'Draw')
        }

    # Calculate team strengths
    home_strength = calculate_team_strength(home_team)
    away_strength = calculate_team_strength(away_team)

    # Add home advantage
    home_advantage = 1.05  # 5% advantage for home team

    # Initialize scores
    home_score = 0
    away_score = 0

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
            consistency_factor = home_player.consistency / 100  # 0-1 scale
            precision_factor = home_player.precision / 100  # 0-1 scale
            stamina_factor = max(0.8, home_player.stamina / 100 - (lane * 0.05))  # Decreases with each lane

            # Apply home advantage
            base_score *= home_advantage

            # Add randomness (more consistent players have less randomness)
            randomness = random.uniform(0.85, 1.15) * (2 - consistency_factor)

            # Calculate lane score
            lane_score = int(base_score * precision_factor * stamina_factor * randomness)

            # Ensure score is within realistic bounds for league level
            if home_team.league.level == 1:  # Bundesliga
                lane_score = max(140, min(190, lane_score))
                # Fehlwürfe für Bundesliga (0-3 pro Spiel)
                lane_fehler = random.randint(0, 1)
            elif home_team.league.level == 2:  # 2. Liga
                lane_score = max(130, min(180, lane_score))
                # Fehlwürfe für 2. Liga (3-6 pro Spiel)
                lane_fehler = random.randint(0, 2)
            else:  # Lower leagues
                lane_score = max(100, min(160, lane_score))
                # Fehlwürfe für untere Ligen (5-10 pro Spiel)
                lane_fehler = random.randint(1, 3)

            # Berechne Volle und Räumer (Verhältnis etwa 2:1)
            lane_volle = int(lane_score * 0.67)  # ca. 2/3 der Punkte auf Volle
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
            consistency_factor = away_player.consistency / 100  # 0-1 scale
            precision_factor = away_player.precision / 100  # 0-1 scale
            stamina_factor = max(0.8, away_player.stamina / 100 - (lane * 0.05))  # Decreases with each lane

            # Apply randomness (more consistent players have less randomness)
            randomness = random.uniform(0.85, 1.15) * (2 - consistency_factor)

            # Calculate lane score
            lane_score = int(base_score * precision_factor * stamina_factor * randomness)

            # Ensure score is within realistic bounds for league level
            if away_team.league.level == 1:  # Bundesliga
                lane_score = max(140, min(190, lane_score))
                # Fehlwürfe für Bundesliga (0-3 pro Spiel)
                lane_fehler = random.randint(0, 1)
            elif away_team.league.level == 2:  # 2. Liga
                lane_score = max(130, min(180, lane_score))
                # Fehlwürfe für 2. Liga (3-6 pro Spiel)
                lane_fehler = random.randint(0, 2)
            else:  # Lower leagues
                lane_score = max(100, min(160, lane_score))
                # Fehlwürfe für untere Ligen (5-10 pro Spiel)
                lane_fehler = random.randint(1, 3)

            # Berechne Volle und Räumer (Verhältnis etwa 2:1)
            lane_volle = int(lane_score * 0.67)  # ca. 2/3 der Punkte auf Volle
            lane_raeumer = lane_score - lane_volle  # Rest auf Räumer

            away_player_lanes.append(lane_score)
            away_player_total += lane_score
            away_player_volle += lane_volle
            away_player_raeumer += lane_raeumer
            away_player_fehler += lane_fehler

        # Add to team scores
        home_score += home_player_total
        away_score += away_player_total

        # Create performance records if match is provided
        if match:
            # Home player performance
            home_perf = PlayerMatchPerformance(
                player_id=home_player.id,
                match_id=match.id,
                team_id=home_team.id,
                is_home_team=True,
                position_number=i+1,
                lane1_score=home_player_lanes[0],
                lane2_score=home_player_lanes[1],
                lane3_score=home_player_lanes[2],
                lane4_score=home_player_lanes[3],
                total_score=home_player_total,
                volle_score=home_player_volle,
                raeumer_score=home_player_raeumer,
                fehler_count=home_player_fehler
            )
            performances.append(home_perf)

            # Away player performance
            away_perf = PlayerMatchPerformance(
                player_id=away_player.id,
                match_id=match.id,
                team_id=away_team.id,
                is_home_team=False,
                position_number=i+1,
                lane1_score=away_player_lanes[0],
                lane2_score=away_player_lanes[1],
                lane3_score=away_player_lanes[2],
                lane4_score=away_player_lanes[3],
                total_score=away_player_total,
                volle_score=away_player_volle,
                raeumer_score=away_player_raeumer,
                fehler_count=away_player_fehler
            )
            performances.append(away_perf)

        # Update player development
        develop_player(home_player, played_minutes=120)  # 120 minutes for a full bowling match
        develop_player(away_player, played_minutes=120)

    # Save performances to database if match is provided
    if match and performances:
        db.session.add_all(performances)

    return {
        'home_team': home_team.name,
        'away_team': away_team.name,
        'home_score': home_score,
        'away_score': away_score,
        'winner': home_team.name if home_score > away_score else (away_team.name if away_score > home_score else 'Draw')
    }

def simulate_match_day(season):
    """Simulate one match day for all leagues in a season."""
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

                # Pass the match instance to save player performances
                match_result = simulate_match(home_team, away_team, match=match)

                # Update match record
                match.home_score = match_result['home_score']
                match.away_score = match_result['away_score']
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

    return {
        'season': season.name,
        'matches_simulated': len(results),
        'results': results,
        'match_day': global_next_match_day
    }

def simulate_season(season):
    """Simulate all matches for a season."""
    results = []

    # Get all leagues in the season
    leagues = season.leagues

    for league in leagues:
        # Generate matches if they don't exist
        if not league.matches:
            generate_fixtures(league, season)

        # Simulate all unplayed matches
        matches = Match.query.filter_by(league_id=league.id, season_id=season.id, is_played=False).all()

        for match in matches:
            home_team = match.home_team
            away_team = match.away_team

            # Pass the match instance to save player performances
            match_result = simulate_match(home_team, away_team, match=match)

            # Update match record
            match.home_score = match_result['home_score']
            match.away_score = match_result['away_score']
            match.is_played = True
            match.match_date = datetime.now(timezone.utc)

            results.append(match_result)

    # Save all changes to database
    db.session.commit()

    # Process end of season (promotions/relegations)
    if all(match.is_played for league in leagues for match in league.matches):
        process_end_of_season(season)

    return {
        'season': season.name,
        'matches_simulated': len(results),
        'results': results
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

    for team in teams:
        # Get all matches for this team
        home_matches = Match.query.filter_by(home_team_id=team.id, league_id=league.id).all()
        away_matches = Match.query.filter_by(away_team_id=team.id, league_id=league.id).all()

        points = 0
        wins = 0
        draws = 0
        losses = 0
        goals_for = 0
        goals_against = 0

        # Calculate points from home matches
        for match in home_matches:
            if match.is_played:
                goals_for += match.home_score
                goals_against += match.away_score

                if match.home_score > match.away_score:
                    points += 3
                    wins += 1
                elif match.home_score == match.away_score:
                    points += 1
                    draws += 1
                else:
                    losses += 1

        # Calculate points from away matches
        for match in away_matches:
            if match.is_played:
                goals_for += match.away_score
                goals_against += match.home_score

                if match.away_score > match.home_score:
                    points += 3
                    wins += 1
                elif match.away_score == match.home_score:
                    points += 1
                    draws += 1
                else:
                    losses += 1

        standings.append({
            'team': team,
            'points': points,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'goal_difference': goals_for - goals_against
        })

    # Sort standings by points, then goal difference, then goals scored
    standings.sort(key=lambda x: (x['points'], x['goal_difference'], x['goals_for']), reverse=True)

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
    new_season = Season(
        name=f"Season {int(old_season.name.split()[-1]) + 1}",
        start_date=old_season.end_date + timedelta(days=30),  # Start 30 days after previous season
        end_date=old_season.end_date + timedelta(days=30 + 365),  # End roughly a year later
        is_current=True
    )

    # Set old season as not current
    old_season.is_current = False

    db.session.add(new_season)
    db.session.commit()

    # Create leagues for the new season
    old_leagues = League.query.filter_by(season_id=old_season.id).all()

    for old_league in old_leagues:
        new_league = League(
            name=old_league.name,
            level=old_league.level,
            season_id=new_season.id
        )
        db.session.add(new_league)

    db.session.commit()

    # Update teams to point to the new leagues
    new_leagues = League.query.filter_by(season_id=new_season.id).order_by(League.level).all()
    old_leagues = League.query.filter_by(season_id=old_season.id).order_by(League.level).all()

    for i, old_league in enumerate(old_leagues):
        for team in old_league.teams:
            team.league_id = new_leagues[i].id

    db.session.commit()

    # Age all players by 1 year
    players = Player.query.all()
    for player in players:
        player.age += 1

    db.session.commit()

def develop_player(player, played_minutes=0, training_intensity=1.0):
    """Develop a player based on playing time, training, and talent."""
    # Base development factor
    base_factor = 0.01

    # Talent factor (higher talent = faster development)
    talent_factor = player.talent / 5.0  # Scale from 1-10 to 0.2-2.0

    # Age factor (younger players develop faster)
    if player.age < 23:
        age_factor = 2.0 - (player.age / 23.0)
    else:
        # Players over 30 start to decline
        if player.age > 30:
            age_factor = -0.1 * (player.age - 30)
        else:
            age_factor = 0.5

    # Playing time factor
    play_factor = played_minutes / 90.0

    # Calculate overall development
    development = base_factor * talent_factor * age_factor * play_factor * training_intensity

    # Apply development to player strength
    player.strength = max(1, min(99, player.strength + development))

    # Save changes
    db.session.add(player)

    return development
