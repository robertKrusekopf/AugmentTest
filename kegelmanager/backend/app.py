from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from models import db, Player, Team, Club, League, Match, Season, Finance
import os
import sys
import subprocess
from dotenv import load_dotenv
import simulation
import db_manager

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

# Club endpoints
@app.route('/api/clubs', methods=['GET'])
def get_clubs():
    clubs = Club.query.all()
    return jsonify([club.to_dict() for club in clubs])

@app.route('/api/clubs/<int:club_id>', methods=['GET'])
def get_club(club_id):
    club = Club.query.get_or_404(club_id)
    return jsonify(club.to_dict())

# Team endpoints
@app.route('/api/teams', methods=['GET'])
def get_teams():
    teams = Team.query.all()
    return jsonify([team.to_dict() for team in teams])

@app.route('/api/teams/<int:team_id>', methods=['GET'])
def get_team(team_id):
    team = Team.query.get_or_404(team_id)
    return jsonify(team.to_dict())

# Player endpoints
@app.route('/api/players', methods=['GET'])
def get_players():
    players = Player.query.all()
    return jsonify([player.to_dict() for player in players])

@app.route('/api/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    player = Player.query.get_or_404(player_id)
    return jsonify(player.to_dict())

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

    season = Season.query.get_or_404(season_id)
    result = simulation.simulate_season(season)
    return jsonify(result)

@app.route('/api/simulate/match_day', methods=['POST'])
def simulate_match_day():
    # Finde die aktuelle Saison
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

    # Zähle die gespielten Spiele vor der Simulation
    played_matches_before = Match.query.filter_by(is_played=True).count()
    print(f"DEBUG: Anzahl gespielter Spiele VOR der Simulation: {played_matches_before}")

    # Simuliere einen Spieltag für alle Ligen
    result = simulation.simulate_match_day(current_season)

    # Zähle die gespielten Spiele nach der Simulation
    played_matches_after = Match.query.filter_by(is_played=True).count()
    print(f"DEBUG: Anzahl gespielter Spiele NACH der Simulation: {played_matches_after}")
    print(f"DEBUG: Neu simulierte Spiele: {played_matches_after - played_matches_before}")

    return jsonify(result)

# Initialize database
@app.route('/api/init_db', methods=['POST'])
def initialize_database():
    with app.app_context():
        db.create_all()
        # Add initial data if needed
    return jsonify({"message": "Database initialized successfully"})

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

    return jsonify({
        'played_matches_count': len(played_matches),
        'unplayed_matches_count': len(unplayed_matches),
        'played_matches': [
            {
                'id': match.id,
                'home_team': match.home_team.name,
                'away_team': match.away_team.name,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'league': match.league.name,
                'date': match.match_date.isoformat() if match.match_date else None
            }
            for match in played_matches[:10]  # Limit to 10 matches
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
