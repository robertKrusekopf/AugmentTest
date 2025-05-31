from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from models import db, Player, Team, Club, League, Match, Season, Finance, UserLineup, LineupPosition, TransferOffer, TransferHistory
import os
import sys
import subprocess
from dotenv import load_dotenv
import simulation
import db_manager
import auto_lineup

# Load environment variables
load_dotenv()

# Ensure database directory exists
db_manager.ensure_db_dir_exists()

# Überprüfe, ob eine Datenbank in der .env-Datei oder in selected_db.txt angegeben ist
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
db_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "selected_db.txt")
selected_db_path = None

print("=== DEBUG: Starte Datenbankauswahl ===")

# Versuche zuerst, die Datenbank aus der separaten Konfigurationsdatei zu laden
if os.path.exists(db_config_file):
    print(f"DEBUG: Konfigurationsdatei gefunden: {db_config_file}")
    try:
        with open(db_config_file, "r") as f:
            db_path = f.read().strip()
            print(f"DEBUG: Datenbankpfad aus Konfigurationsdatei: {db_path}")
            if os.path.exists(db_path):
                selected_db_path = db_path
                print(f"DEBUG: Verwende Datenbank aus Konfigurationsdatei: {selected_db_path}")
            else:
                print(f"DEBUG: Datenbank aus Konfigurationsdatei existiert nicht: {db_path}")
    except Exception as e:
        print(f"DEBUG: Fehler beim Lesen der Konfigurationsdatei: {str(e)}")

# Wenn keine Datenbank aus der Konfigurationsdatei geladen wurde, versuche es mit der .env-Datei
if not selected_db_path and os.path.exists(env_file):
    print(f"DEBUG: .env-Datei gefunden: {env_file}")
    try:
        with open(env_file, "r") as f:
            env_content = f.read()
            print(f"DEBUG: Inhalt der .env-Datei: {env_content}")
            for line in env_content.splitlines():
                if line.startswith("DATABASE_PATH="):
                    db_path = line.strip().split("=", 1)[1]
                    if os.path.exists(db_path):
                        selected_db_path = db_path
                        print(f"DEBUG: Verwende ausgewählte Datenbank aus .env-Datei: {selected_db_path}")
                        break
                    else:
                        print(f"DEBUG: Ausgewählte Datenbank aus .env-Datei existiert nicht: {db_path}")
    except Exception as e:
        print(f"DEBUG: Fehler beim Lesen der .env-Datei: {str(e)}")
else:
    print("DEBUG: Keine .env-Datei gefunden oder bereits Datenbank aus Konfigurationsdatei geladen")

# Default database path
default_db_path = os.path.join(db_manager.get_database_dir(), "kegelmanager_default.db")
print(f"DEBUG: Standard-Datenbank-Pfad: {default_db_path}")

# Falls keine Datenbank ausgewählt wurde, verwende die Standard-Datenbank
if not selected_db_path:
    selected_db_path = default_db_path
    print(f"DEBUG: Verwende Standard-Datenbank: {selected_db_path}")
else:
    print(f"DEBUG: Verwende ausgewählte Datenbank: {selected_db_path}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{selected_db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

# Initialize the database
db.init_app(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

# Global search endpoint
@app.route('/api/search', methods=['GET'])
def global_search():
    """Global search across all entities."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({
            "players": [],
            "teams": [],
            "clubs": [],
            "leagues": []
        })

    # Search players
    players = Player.query.filter(
        Player.name.ilike(f'%{query}%')
    ).limit(10).all()

    # Search teams
    teams = Team.query.filter(
        Team.name.ilike(f'%{query}%')
    ).limit(10).all()

    # Search clubs
    clubs = Club.query.filter(
        Club.name.ilike(f'%{query}%')
    ).limit(10).all()

    # Search leagues
    leagues = League.query.filter(
        League.name.ilike(f'%{query}%')
    ).limit(10).all()

    return jsonify({
        "players": [{"id": p.id, "name": p.name, "team": p.teams[0].name if p.teams else "Kein Team", "club": p.club.name if p.club else "Kein Verein"} for p in players],
        "teams": [{"id": t.id, "name": t.name, "league": t.league.name if t.league else "Keine Liga", "club": t.club.name if t.club else "Kein Verein"} for t in teams],
        "clubs": [{"id": c.id, "name": c.name} for c in clubs],
        "leagues": [{"id": l.id, "name": l.name, "level": l.level} for l in leagues]
    })

# Club endpoints
@app.route('/api/clubs', methods=['GET'])
def get_clubs():
    clubs = Club.query.all()
    return jsonify([club.to_dict() for club in clubs])

@app.route('/api/clubs/<int:club_id>', methods=['GET'])
def get_club(club_id):
    club = Club.query.get_or_404(club_id)
    return jsonify(club.to_dict())

@app.route('/api/clubs/<int:club_id>/lane-records', methods=['GET'])
def get_club_lane_records(club_id):
    """Get lane records for a specific club."""
    club = Club.query.get_or_404(club_id)

    # Get lane records from the club's to_dict method
    club_data = club.to_dict()
    lane_records = club_data.get('lane_records', {})

    return jsonify(lane_records)

@app.route('/api/clubs/<int:club_id>', methods=['PATCH'])
def update_club(club_id):
    """Update club attributes (Cheat mode)."""
    club = Club.query.get_or_404(club_id)
    data = request.json

    # Update club attributes
    if 'name' in data:
        club.name = data['name']
    if 'founded' in data:
        club.founded = data['founded']
    if 'reputation' in data:
        club.reputation = data['reputation']
    if 'fans' in data:
        club.fans = data['fans']
    if 'training_facilities' in data:
        club.training_facilities = data['training_facilities']
    if 'coaching' in data:
        club.coaching = data['coaching']
    if 'lane_quality' in data:
        club.lane_quality = data['lane_quality']

    # Save changes to database
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Verein erfolgreich aktualisiert",
        "club": club.to_dict()
    })

# Team endpoints
@app.route('/api/teams', methods=['GET'])
def get_teams():
    teams = Team.query.all()
    return jsonify([team.to_dict() for team in teams])

@app.route('/api/teams/<int:team_id>', methods=['GET'])
def get_team(team_id):
    team = Team.query.get_or_404(team_id)
    return jsonify(team.to_dict())

@app.route('/api/teams/<int:team_id>', methods=['PATCH'])
def update_team(team_id):
    """Update team attributes."""
    team = Team.query.get_or_404(team_id)
    data = request.json

    # Update team attributes
    if 'staerke' in data:
        team.staerke = data['staerke']
    if 'name' in data:
        team.name = data['name']
    if 'is_youth_team' in data:
        team.is_youth_team = data['is_youth_team']

    # Save changes to database
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Team erfolgreich aktualisiert",
        "team": team.to_dict()
    })

# Player endpoints
@app.route('/api/players', methods=['GET'])
def get_players():
    players = Player.query.all()
    return jsonify([player.to_dict() for player in players])

@app.route('/api/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    player = Player.query.get_or_404(player_id)
    return jsonify(player.to_dict())

@app.route('/api/players/<int:player_id>', methods=['PATCH'])
def update_player(player_id):
    """Update player attributes (Cheat mode)."""
    player = Player.query.get_or_404(player_id)
    data = request.json

    # Update basic attributes
    if 'name' in data:
        player.name = data['name']
    if 'age' in data:
        player.age = data['age']
    if 'position' in data:
        player.position = data['position']
    if 'strength' in data:
        player.strength = data['strength']
    if 'talent' in data:
        player.talent = data['talent']
    if 'salary' in data:
        player.salary = data['salary']
    if 'contract_end' in data and data['contract_end']:
        from datetime import datetime
        player.contract_end = datetime.fromisoformat(data['contract_end'].replace('Z', '+00:00')).date()

    # Update bowling-specific attributes
    if 'konstanz' in data:
        player.konstanz = data['konstanz']
    if 'drucksicherheit' in data:
        player.drucksicherheit = data['drucksicherheit']
    if 'volle' in data:
        player.volle = data['volle']
    if 'raeumer' in data:
        player.raeumer = data['raeumer']
    if 'sicherheit' in data:
        player.sicherheit = data['sicherheit']
    if 'consistency' in data:
        player.consistency = data['consistency']
    if 'precision' in data:
        player.precision = data['precision']
    if 'stamina' in data:
        player.stamina = data['stamina']

    # Update the new attributes
    if 'auswaerts' in data:
        player.auswaerts = data['auswaerts']
    if 'start' in data:
        player.start = data['start']
    if 'mitte' in data:
        player.mitte = data['mitte']
    if 'schluss' in data:
        player.schluss = data['schluss']

    # Update form system attributes (only in cheat mode)
    if 'form_short_term' in data:
        player.form_short_term = data['form_short_term']
    if 'form_medium_term' in data:
        player.form_medium_term = data['form_medium_term']
    if 'form_long_term' in data:
        player.form_long_term = data['form_long_term']
    if 'form_short_remaining_days' in data:
        player.form_short_remaining_days = data['form_short_remaining_days']
    if 'form_medium_remaining_days' in data:
        player.form_medium_remaining_days = data['form_medium_remaining_days']
    if 'form_long_remaining_days' in data:
        player.form_long_remaining_days = data['form_long_remaining_days']

    # Save changes to database
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Spieler erfolgreich aktualisiert",
        "player": player.to_dict()
    })

# League endpoints
@app.route('/api/leagues', methods=['GET'])
def get_leagues():
    leagues = League.query.all()
    return jsonify([league.to_dict() for league in leagues])

@app.route('/api/leagues/<int:league_id>', methods=['GET'])
def get_league(league_id):
    league = League.query.get_or_404(league_id)
    return jsonify(league.to_dict())

# Match endpoints
@app.route('/api/matches', methods=['GET'])
def get_matches():
    matches = Match.query.all()
    return jsonify([match.to_dict() for match in matches])

@app.route('/api/matches/<int:match_id>', methods=['GET'])
def get_match(match_id):
    match = Match.query.get_or_404(match_id)
    return jsonify(match.to_dict())

# Season endpoints
@app.route('/api/seasons', methods=['GET'])
def get_seasons():
    seasons = Season.query.all()
    return jsonify([season.to_dict() for season in seasons])

@app.route('/api/seasons/<int:season_id>', methods=['GET'])
def get_season(season_id):
    season = Season.query.get_or_404(season_id)
    return jsonify(season.to_dict())

# Simulation endpoints
@app.route('/api/simulate/match', methods=['POST'])
def simulate_match():
    data = request.json
    home_team_id = data.get('home_team_id')
    away_team_id = data.get('away_team_id')

    home_team = Team.query.get_or_404(home_team_id)
    away_team = Team.query.get_or_404(away_team_id)

    result = simulation.simulate_match(home_team, away_team)
    return jsonify(result)

@app.route('/api/simulate/season', methods=['POST'])
def simulate_season():
    data = request.json
    season_id = data.get('season_id')
    create_new_season = data.get('create_new_season', True)  # Default to True for backward compatibility

    print(f"DEBUG: Simulating season with ID: {season_id}")
    print(f"DEBUG: Create new season: {create_new_season}")

    if not season_id:
        return jsonify({"error": "season_id is required"}), 400

    try:
        season = Season.query.get_or_404(season_id)
        print(f"DEBUG: Found season: {season.name} (ID: {season.id})")

        # Count matches before simulation
        played_matches_before = Match.query.filter_by(is_played=True).count()
        print(f"DEBUG: Played matches before simulation: {played_matches_before}")

        # Simulate the season
        result = simulation.simulate_season(season, create_new_season=create_new_season)

        # Count matches after simulation
        played_matches_after = Match.query.filter_by(is_played=True).count()
        print(f"DEBUG: Played matches after simulation: {played_matches_after}")
        print(f"DEBUG: Newly simulated matches: {played_matches_after - played_matches_before}")

        # Explicitly recalculate standings for each league
        for league in season.leagues:
            print(f"DEBUG: Recalculating standings for league: {league.name}")
            standings = simulation.calculate_standings(league)
            print(f"DEBUG: League {league.name} has {len(standings)} teams in standings")

        return jsonify(result)
    except Exception as e:
        print(f"DEBUG: Error simulating season: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/season/status', methods=['GET'])
def get_season_status():
    """Get the status of the current season (completed or not)."""
    try:
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

        # Check if all matches in the season are played
        total_matches = Match.query.filter_by(season_id=current_season.id).count()
        played_matches = Match.query.filter_by(season_id=current_season.id, is_played=True).count()

        is_completed = total_matches > 0 and total_matches == played_matches

        return jsonify({
            "season_id": current_season.id,
            "season_name": current_season.name,
            "is_completed": is_completed,
            "total_matches": total_matches,
            "played_matches": played_matches,
            "remaining_matches": total_matches - played_matches
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/season/transition', methods=['POST'])
def transition_to_new_season():
    """Start a new season after the current one is completed."""
    try:
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

        # Check if all matches are played
        total_matches = Match.query.filter_by(season_id=current_season.id).count()
        played_matches = Match.query.filter_by(season_id=current_season.id, is_played=True).count()

        if total_matches == 0 or total_matches != played_matches:
            return jsonify({"error": "Die Saison ist noch nicht abgeschlossen"}), 400

        # Process end of season and create new season
        print("Processing season transition...")
        simulation.process_end_of_season(current_season)

        # Get the new current season
        new_season = Season.query.filter_by(is_current=True).first()
        if new_season and new_season.id != current_season.id:
            return jsonify({
                "success": True,
                "message": "Saisonwechsel erfolgreich durchgeführt",
                "old_season": current_season.name,
                "new_season": new_season.name,
                "new_season_id": new_season.id
            })
        else:
            return jsonify({"error": "Fehler beim Erstellen der neuen Saison"}), 500

    except Exception as e:
        print(f"Error during season transition: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulate/match_day', methods=['POST'])
def simulate_match_day():
    """Simulate one match day for all leagues in a season using optimized methods."""
    try:
        # Finde die aktuelle Saison
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

        # Zähle die gespielten Spiele vor der Simulation
        played_matches_before = Match.query.filter_by(is_played=True).count()
        print(f"DEBUG: Anzahl gespielter Spiele VOR der Simulation: {played_matches_before}")

        # Simuliere einen Spieltag mit optimierter Version
        result = simulation.simulate_match_day(current_season)

        # Zähle die gespielten Spiele nach der Simulation
        played_matches_after = Match.query.filter_by(is_played=True).count()
        print(f"DEBUG: Anzahl gespielter Spiele NACH der Simulation: {played_matches_after}")
        print(f"DEBUG: Neu simulierte Spiele: {played_matches_after - played_matches_before}")

        return jsonify(result)

    except Exception as e:
        print(f"ERROR in simulation: {str(e)}")
        return jsonify({"error": f"Fehler bei der Simulation: {str(e)}"}), 500

# Initialize database
@app.route('/api/init_db', methods=['POST'])
def initialize_database():
    with app.app_context():
        db.create_all()
        # Add initial data if needed
    return jsonify({"message": "Database initialized successfully"})

# Migrate database to add new tables
@app.route('/api/migrate_db', methods=['POST'])
def migrate_database():
    """Add new tables to the database without affecting existing data."""
    with app.app_context():
        # Check if tables exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        new_tables_created = []

        # Create UserLineup table if it doesn't exist
        if 'user_lineup' not in existing_tables:
            UserLineup.__table__.create(db.engine)
            new_tables_created.append('user_lineup')

        # Create LineupPosition table if it doesn't exist
        if 'lineup_position' not in existing_tables:
            LineupPosition.__table__.create(db.engine)
            new_tables_created.append('lineup_position')

        # Create TransferOffer table if it doesn't exist
        if 'transfer_offer' not in existing_tables:
            TransferOffer.__table__.create(db.engine)
            new_tables_created.append('transfer_offer')

        # Create TransferHistory table if it doesn't exist
        if 'transfer_history' not in existing_tables:
            TransferHistory.__table__.create(db.engine)
            new_tables_created.append('transfer_history')

        return jsonify({
            "message": "Database migration completed successfully",
            "new_tables_created": new_tables_created
        })

# Route to serve club emblems
@app.route('/api/club-emblem/<verein_id>', methods=['GET'])
def get_club_emblem(verein_id):
    """Serve the club emblem image."""
    print(f"DEBUG: Requested emblem for verein_id: {verein_id}")
    # Convert verein_id to string if it's not already
    verein_id_str = str(verein_id)

    # Get the wappen directory
    wappen_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wappen")
    print(f"DEBUG: Wappen directory: {wappen_dir}")

    # Check if the directory exists
    if not os.path.exists(wappen_dir):
        print(f"DEBUG: Wappen directory does not exist: {wappen_dir}")
        return jsonify({"error": "Wappen directory not found"}), 404

    # List all files in the wappen directory
    all_files = os.listdir(wappen_dir)
    print(f"DEBUG: Number of files in wappen directory: {len(all_files)}")

    # First try exact match
    exact_file = f"{verein_id_str}.png"
    exact_path = os.path.join(wappen_dir, exact_file)

    if os.path.exists(exact_path):
        print(f"DEBUG: Found exact match: {exact_path}")
        return send_file(exact_path, mimetype='image/png')

    # If no exact match, try to find a file that contains the verein_id
    matching_files = [f for f in all_files if verein_id_str in f]
    print(f"DEBUG: Matching files for verein_id {verein_id}: {matching_files}")

    if matching_files:
        # Use the first matching file
        emblem_path = os.path.join(wappen_dir, matching_files[0])
        print(f"DEBUG: Serving emblem from: {emblem_path}")
        return send_file(emblem_path, mimetype='image/png')
    else:
        print(f"DEBUG: No emblem found for verein_id: {verein_id}")
        return jsonify({"error": "Emblem not found"}), 404

# Debug endpoint to check match data
@app.route('/api/debug/matches', methods=['GET'])
def debug_matches():
    """Debug endpoint to check match data."""
    played_matches = Match.query.filter_by(is_played=True).all()
    unplayed_matches = Match.query.filter_by(is_played=False).all()
    all_matches = Match.query.all()

    # Check match_day distribution
    matches_with_match_day = Match.query.filter(Match.match_day.isnot(None)).all()
    matches_without_match_day = Match.query.filter(Match.match_day.is_(None)).all()

    return jsonify({
        'total_matches': len(all_matches),
        'played_matches_count': len(played_matches),
        'unplayed_matches_count': len(unplayed_matches),
        'matches_with_match_day': len(matches_with_match_day),
        'matches_without_match_day': len(matches_without_match_day),
        'sample_matches': [
            {
                'id': match.id,
                'home_team': match.home_team.name,
                'away_team': match.away_team.name,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'league': match.league.name,
                'match_day': match.match_day,
                'is_played': match.is_played,
                'date': match.match_date.isoformat() if match.match_date else None
            }
            for match in all_matches[:10]  # Limit to 10 matches
        ]
    })

# Debug endpoint to check league standings
@app.route('/api/debug/standings/<int:league_id>', methods=['GET'])
def debug_standings(league_id):
    """Debug endpoint to check league standings."""
    league = League.query.get_or_404(league_id)
    import simulation
    standings = simulation.calculate_standings(league)

    return jsonify({
        'league': league.name,
        'standings': [
            {
                'position': i + 1,
                'team': standing['team'].name,
                'points': standing['points'],
                'wins': standing['wins'],
                'draws': standing['draws'],
                'losses': standing['losses'],
                'goals_for': standing['goals_for'],
                'goals_against': standing['goals_against'],
                'goal_difference': standing['goal_difference']
            }
            for i, standing in enumerate(standings)
        ]
    })

# Lineup management endpoints
@app.route('/api/matches/<int:match_id>/available-players', methods=['GET'])
def get_available_players_for_match(match_id):
    """Get available players for a match."""
    match = Match.query.get_or_404(match_id)

    # Get the managed club ID from the request
    managed_club_id = request.args.get('managed_club_id', type=int)
    if not managed_club_id:
        return jsonify({"error": "managed_club_id parameter is required"}), 400

    # Check if the managed club is playing in this match
    is_home_team = match.home_team.club_id == managed_club_id
    is_away_team = match.away_team.club_id == managed_club_id

    if not (is_home_team or is_away_team):
        return jsonify({"error": "The managed club is not playing in this match"}), 400

    # Get the team that belongs to the managed club
    team = match.home_team if is_home_team else match.away_team

    # If this is an away team, ensure the home team has a lineup
    if is_away_team:
        home_lineup_exists = auto_lineup.ensure_home_team_lineup_exists(match_id)
        if not home_lineup_exists:
            return jsonify({"error": "Failed to create home team lineup"}), 500

    # Get all players from the club
    club_players = Player.query.filter_by(club_id=managed_club_id).all()

    # Reset player availability flags for this club
    for player in club_players:
        player.is_available_current_matchday = True

    # Determine player availability (16.7% chance of being unavailable)
    import random
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

    # Check if there's an existing lineup for this match and team
    existing_lineup = UserLineup.query.filter_by(
        match_id=match_id,
        team_id=team.id,
        is_home_team=is_home_team
    ).first()

    # Check if there's an existing lineup for the opponent
    opponent_team = match.away_team if is_home_team else match.home_team
    opponent_lineup = UserLineup.query.filter_by(
        match_id=match_id,
        team_id=opponent_team.id,
        is_home_team=not is_home_team
    ).first()

    # Prepare the response
    result = {
        'match_id': match_id,
        'team_id': team.id,
        'team_name': team.name,
        'is_home_team': is_home_team,
        'players': [
            {
                'id': player.id,
                'name': player.name,
                'strength': player.strength,
                'is_available': player.is_available_current_matchday,
                'position': None  # Will be filled if player is in the lineup
            }
            for player in club_players
        ],
        'has_lineup': existing_lineup is not None,
        'opponent_has_lineup': opponent_lineup is not None
    }

    # If there's an existing lineup, include the positions
    if existing_lineup:
        for position in existing_lineup.positions:
            for player in result['players']:
                if player['id'] == position.player_id:
                    player['position'] = position.position_number
                    break

    # If this is the away team and the home team has already set their lineup,
    # include the home team's lineup in the response
    if is_away_team and opponent_lineup:
        # Get the home team's lineup positions
        home_positions = sorted(opponent_lineup.positions, key=lambda p: p.position_number)

        # Add the home team's lineup to the response
        result['opponent_lineup'] = [
            {
                'position': pos.position_number,
                'player_id': pos.player_id,
                'player_name': pos.player.name,
                'player_strength': pos.player.strength
            }
            for pos in home_positions
        ]

    return jsonify(result)

@app.route('/api/matches/<int:match_id>/lineup', methods=['POST'])
def save_lineup(match_id):
    """Save a user-selected lineup for a match."""
    match = Match.query.get_or_404(match_id)
    data = request.json

    team_id = data.get('team_id')
    is_home_team = data.get('is_home_team')
    positions = data.get('positions', [])

    if not team_id:
        return jsonify({"error": "team_id is required"}), 400

    if is_home_team is None:
        return jsonify({"error": "is_home_team is required"}), 400

    if len(positions) != 6:
        return jsonify({"error": "Exactly 6 positions are required"}), 400

    # Check if the team is actually playing in this match
    if (is_home_team and match.home_team_id != team_id) or (not is_home_team and match.away_team_id != team_id):
        return jsonify({"error": "The specified team is not playing in this match"}), 400

    # If this is the away team, ensure the home team has a lineup
    if not is_home_team:
        home_lineup_exists = auto_lineup.ensure_home_team_lineup_exists(match_id)
        if not home_lineup_exists:
            return jsonify({
                "error": "Fehler beim Erstellen der Heimmannschaftsaufstellung",
                "code": "HOME_TEAM_LINEUP_CREATION_FAILED"
            }), 500

    # Check if there's an existing lineup
    existing_lineup = UserLineup.query.filter_by(
        match_id=match_id,
        team_id=team_id,
        is_home_team=is_home_team
    ).first()

    if existing_lineup:
        # Delete existing positions
        for position in existing_lineup.positions:
            db.session.delete(position)

        # Update the lineup
        lineup = existing_lineup
    else:
        # Create a new lineup
        lineup = UserLineup(
            match_id=match_id,
            team_id=team_id,
            is_home_team=is_home_team
        )
        db.session.add(lineup)
        db.session.flush()  # Get the ID for the new lineup

    # Add the positions
    for position_data in positions:
        player_id = position_data.get('player_id')
        position_number = position_data.get('position')

        if not player_id or not position_number:
            return jsonify({"error": "player_id and position are required for each position"}), 400

        # Check if the player exists
        player = Player.query.get(player_id)
        if not player:
            return jsonify({"error": f"Player with ID {player_id} not found"}), 404

        # Check if the player is available
        if not player.is_available_current_matchday:
            return jsonify({"error": f"Player {player.name} is not available for this match"}), 400

        # Create the position
        position = LineupPosition(
            lineup_id=lineup.id,
            player_id=player_id,
            position_number=position_number
        )
        db.session.add(position)

    # Save changes to database
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Aufstellung erfolgreich gespeichert",
        "lineup": lineup.to_dict()
    })

@app.route('/api/matches/<int:match_id>/lineup', methods=['GET'])
def get_lineup(match_id):
    """Get the user-selected lineup for a match."""
    # Verify the match exists
    Match.query.get_or_404(match_id)

    # Get the team ID from the request
    team_id = request.args.get('team_id', type=int)
    is_home_team = request.args.get('is_home_team', type=bool)

    if not team_id:
        return jsonify({"error": "team_id parameter is required"}), 400

    if is_home_team is None:
        return jsonify({"error": "is_home_team parameter is required"}), 400

    # Check if there's an existing lineup
    lineup = UserLineup.query.filter_by(
        match_id=match_id,
        team_id=team_id,
        is_home_team=is_home_team
    ).first()

    if not lineup:
        return jsonify({"error": "No lineup found for this match and team"}), 404

    return jsonify(lineup.to_dict())

@app.route('/api/matches/<int:match_id>/lineup', methods=['DELETE'])
def delete_lineup(match_id):
    """Delete a user-selected lineup for a match."""
    # Verify the match exists
    Match.query.get_or_404(match_id)

    # Get the team ID from the request
    team_id = request.args.get('team_id', type=int)
    is_home_team = request.args.get('is_home_team', type=bool)

    if not team_id:
        return jsonify({"error": "team_id parameter is required"}), 400

    if is_home_team is None:
        return jsonify({"error": "is_home_team parameter is required"}), 400

    # Check if there's an existing lineup
    lineup = UserLineup.query.filter_by(
        match_id=match_id,
        team_id=team_id,
        is_home_team=is_home_team
    ).first()

    if not lineup:
        return jsonify({"error": "No lineup found for this match and team"}), 404

    # Delete the lineup and its positions
    db.session.delete(lineup)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Aufstellung erfolgreich gelöscht"
    })

# Database management endpoints
@app.route('/api/databases', methods=['GET'])
def list_databases():
    """List all available databases."""
    databases = db_manager.list_databases()
    return jsonify(databases)

@app.route('/api/databases/create', methods=['POST'])
def create_database():
    """Create a new database by running neue_DB.py."""
    data = request.json
    db_name = data.get('name')
    with_sample_data = data.get('with_sample_data', True)

    if not db_name:
        return jsonify({"success": False, "message": "Datenbankname ist erforderlich."}), 400

    try:
        # Führe neue_DB.py als separaten Prozess aus
        cmd = [sys.executable, "neue_DB.py", db_name]
        if not with_sample_data:
            cmd.append("--no-sample-data")

        # Führe den Befehl aus und erfasse die Ausgabe
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Wenn der Prozess erfolgreich war, gib eine Erfolgsmeldung zurück
        return jsonify({
            "success": True,
            "message": f"Datenbank '{db_name}' wurde erstellt. Sie können die Datei jetzt bearbeiten.",
            "output": result.stdout
        })
    except subprocess.CalledProcessError as e:
        # Wenn der Prozess fehlgeschlagen ist, gib eine Fehlermeldung zurück
        return jsonify({
            "success": False,
            "message": f"Fehler beim Erstellen der Datenbank: {e}",
            "output": e.stderr
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Unerwarteter Fehler: {str(e)}"
        }), 500

@app.route('/api/databases/select', methods=['POST'])
def select_database():
    """Select a database to use."""
    data = request.json
    db_name = data.get('name')

    if not db_name:
        return jsonify({"success": False, "message": "Datenbankname ist erforderlich."}), 400

    result = db_manager.select_database(db_name)
    return jsonify(result)

@app.route('/api/databases/delete', methods=['POST'])
def delete_database():
    """Delete a database."""
    data = request.json
    db_name = data.get('name')

    if not db_name:
        return jsonify({"success": False, "message": "Datenbankname ist erforderlich."}), 400

    result = db_manager.delete_database(db_name)
    return jsonify(result)

# Transfer endpoints
@app.route('/api/transfers', methods=['GET'])
def get_transfers():
    """Get transfer data for the managed club."""
    managed_club_id = request.args.get('managed_club_id', type=int)

    if not managed_club_id:
        return jsonify({"error": "managed_club_id parameter is required"}), 400

    # Get current season
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        return jsonify({"error": "No current season found"}), 404

    # Get transfer budget (from club finances or default)
    managed_club = Club.query.get_or_404(managed_club_id)
    latest_finance = Finance.query.filter_by(club_id=managed_club_id).order_by(Finance.date.desc()).first()
    transfer_budget = int(latest_finance.balance) if latest_finance else 500000

    # Get players available for transfer (not from managed club)
    market_players = Player.query.filter(
        Player.club_id != managed_club_id,
        Player.contract_end.isnot(None)  # Only players with contracts
    ).limit(20).all()

    # Get offers made by the managed club
    my_offers = TransferOffer.query.filter_by(
        offering_club_id=managed_club_id
    ).order_by(TransferOffer.created_at.desc()).all()

    # Get offers received by the managed club
    received_offers = TransferOffer.query.filter_by(
        receiving_club_id=managed_club_id
    ).order_by(TransferOffer.created_at.desc()).all()

    # Get transfer history for current season
    transfer_history = TransferHistory.query.filter_by(
        season_id=current_season.id
    ).order_by(TransferHistory.transfer_date.desc()).limit(20).all()

    return jsonify({
        'transfer_budget': transfer_budget,
        'market_players': [
            {
                'id': player.id,
                'name': player.name,
                'age': player.age,
                'position': player.position,
                'strength': player.strength,
                'team': player.teams[0].name if player.teams else 'Vereinslos',
                'club': player.club.name if player.club else 'Kein Verein',
                'value': player.strength * 5000,  # Simple value calculation
                'salary': player.salary
            }
            for player in market_players
        ],
        'my_offers': [offer.to_dict() for offer in my_offers],
        'received_offers': [offer.to_dict() for offer in received_offers],
        'transfer_history': [transfer.to_dict() for transfer in transfer_history]
    })

@app.route('/api/transfers/offer', methods=['POST'])
def create_transfer_offer():
    """Create a new transfer offer."""
    data = request.json
    player_id = data.get('player_id')
    offering_club_id = data.get('offering_club_id')
    offer_amount = data.get('offer_amount')

    if not all([player_id, offering_club_id, offer_amount]):
        return jsonify({"error": "Missing required fields"}), 400

    # Get player and validate
    player = Player.query.get_or_404(player_id)
    if not player.club_id:
        return jsonify({"error": "Player is not assigned to a club"}), 400

    # Check if offer already exists
    existing_offer = TransferOffer.query.filter_by(
        player_id=player_id,
        offering_club_id=offering_club_id,
        status='pending'
    ).first()

    if existing_offer:
        return jsonify({"error": "You already have a pending offer for this player"}), 400

    # Create new offer
    new_offer = TransferOffer(
        player_id=player_id,
        offering_club_id=offering_club_id,
        receiving_club_id=player.club_id,
        offer_amount=offer_amount
    )

    db.session.add(new_offer)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Transferangebot erfolgreich erstellt",
        "offer": new_offer.to_dict()
    })

@app.route('/api/transfers/offer/<int:offer_id>', methods=['PATCH'])
def update_transfer_offer(offer_id):
    """Accept, reject, or withdraw a transfer offer."""
    data = request.json
    action = data.get('action')  # 'accept', 'reject', 'withdraw'

    if action not in ['accept', 'reject', 'withdraw']:
        return jsonify({"error": "Invalid action"}), 400

    offer = TransferOffer.query.get_or_404(offer_id)

    if offer.status != 'pending':
        return jsonify({"error": "Offer is no longer pending"}), 400

    if action == 'accept':
        # Complete the transfer
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            return jsonify({"error": "No current season found"}), 404

        # Create transfer history record
        transfer_record = TransferHistory(
            player_id=offer.player_id,
            from_club_id=offer.receiving_club_id,
            to_club_id=offer.offering_club_id,
            transfer_amount=offer.offer_amount,
            season_id=current_season.id
        )

        # Update player's club
        player = Player.query.get(offer.player_id)
        player.club_id = offer.offering_club_id

        # Update offer status
        offer.status = 'accepted'

        # Add records to database
        db.session.add(transfer_record)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Transfer erfolgreich abgeschlossen",
            "transfer": transfer_record.to_dict()
        })

    elif action == 'reject':
        offer.status = 'rejected'
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Transferangebot abgelehnt"
        })

    elif action == 'withdraw':
        offer.status = 'withdrawn'
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Transferangebot zurückgezogen"
        })

@app.route('/api/transfers/offer/<int:offer_id>', methods=['DELETE'])
def delete_transfer_offer(offer_id):
    """Delete a transfer offer (withdraw)."""
    offer = TransferOffer.query.get_or_404(offer_id)

    if offer.status != 'pending':
        return jsonify({"error": "Can only withdraw pending offers"}), 400

    offer.status = 'withdrawn'
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Transferangebot zurückgezogen"
    })

if __name__ == '__main__':
    print("=== DEBUG: Starte Anwendung ===")
    print(f"DEBUG: Verwende Datenbank: {selected_db_path}")
    print(f"DEBUG: SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Überprüfe, ob die Datenbank existiert
    if not os.path.exists(selected_db_path):
        print(f"DEBUG: Datenbank existiert nicht: {selected_db_path}")
        print(f"DEBUG: Erstelle neue Datenbank: {selected_db_path}")

        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(selected_db_path), exist_ok=True)

    with app.app_context():
        # Stelle sicher, dass die Tabellen in der ausgewählten Datenbank existieren
        db.create_all()
        print("DEBUG: Tabellen wurden erstellt oder existieren bereits")

        # Überprüfe, ob die Datenbank leer ist (keine Clubs vorhanden)
        club_count = Club.query.count()
        print(f"DEBUG: Anzahl der Clubs in der Datenbank: {club_count}")

        # Nur wenn die Datenbank leer ist, füge Beispieldaten hinzu
        if club_count == 0:
            print(f"DEBUG: Datenbank '{selected_db_path}' ist leer. Füge Beispieldaten hinzu...")
            try:
                from init_db import create_sample_data
                create_sample_data(custom_app=app)
                print("DEBUG: Beispieldaten erfolgreich hinzugefügt.")

                # Überprüfe die hinzugefügten Clubs
                clubs = Club.query.all()
                print(f"DEBUG: Hinzugefügte Clubs: {[club.name for club in clubs]}")

                # Speichere die Datenbank
                db.session.commit()
                print("DEBUG: Datenbank gespeichert")
            except Exception as e:
                print(f"DEBUG: Fehler beim Hinzufügen von Beispieldaten: {str(e)}")
        else:
            # Zeige die vorhandenen Clubs an
            clubs = Club.query.all()
            print(f"DEBUG: Vorhandene Clubs: {[club.name for club in clubs]}")

    print("DEBUG: Starte Flask-Server...")
    app.run(debug=True)
