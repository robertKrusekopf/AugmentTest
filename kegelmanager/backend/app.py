from flask import Flask, jsonify, request, send_file, abort
from flask_cors import CORS
from models import db, Player, Team, Club, League, Match, Season, Finance, UserLineup, LineupPosition, TransferOffer, TransferHistory, Cup, CupMatch, PlayerCupMatchPerformance
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

@app.route('/api/clubs/<int:club_id>/teams', methods=['POST'])
def add_team_to_club(club_id):
    """Add a new team to a club for the next season (Cheat function)."""
    try:
        # Check if season is completed
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

        # Check season status
        season_status = get_season_status_data(current_season)
        if not season_status.get('is_completed', False):
            return jsonify({"error": "Diese Funktion ist nur nach dem letzten Spieltag verfügbar"}), 400

        # Get club
        club = Club.query.get_or_404(club_id)

        # Get request data
        data = request.json
        league_id = data.get('league_id')
        team_name = data.get('team_name')

        if not league_id:
            return jsonify({"error": "Liga-ID ist erforderlich"}), 400

        if not team_name:
            # Generate default team name
            existing_teams = Team.query.filter_by(club_id=club_id).count()
            team_name = f"{club.name} {existing_teams + 1}"

        # Validate league exists and is in current season
        league = League.query.filter_by(id=league_id, season_id=current_season.id).first()
        if not league:
            return jsonify({"error": "Liga nicht gefunden oder nicht in aktueller Saison"}), 404

        # Create new team (will be added to next season during season transition)
        new_team = Team(
            name=team_name,
            club_id=club_id,
            league_id=None,  # Will be set during season transition
            is_youth_team=False,
            staerke=0
        )

        # Store the target league for next season in a temporary field
        # We'll use a simple approach: store it in the database and handle it during season transition
        new_team.target_league_level = league.level
        new_team.target_league_bundesland = league.bundesland
        new_team.target_league_landkreis = league.landkreis
        new_team.target_league_altersklasse = league.altersklasse

        db.session.add(new_team)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Mannschaft '{team_name}' wurde erstellt und wird zur nächsten Saison zu '{league.name}' hinzugefügt",
            "team": new_team.to_dict(),
            "target_league": league.name
        })

    except Exception as e:
        print(f"Error adding team to club: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/teams/<int:team_id>/history', methods=['GET'])
def get_team_history(team_id):
    """Get historical league positions for a team across all seasons."""
    try:
        from models import LeagueHistory, Season

        # Verify team exists
        team = Team.query.get_or_404(team_id)

        # Check if LeagueHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'league_history' not in existing_tables:
            return jsonify({
                'team_name': team.name,
                'club_name': team.club.name if team.club else 'Unbekannt',
                'history': []
            })

        # Get historical data for this team
        history_entries = LeagueHistory.query.filter_by(
            team_id=team_id
        ).order_by(LeagueHistory.season_id.desc()).all()

        # Group by season and format data
        history_data = []
        for entry in history_entries:
            history_data.append({
                'season_name': entry.season_name,
                'season_id': entry.season_id,
                'league_name': entry.league_name,
                'league_level': entry.league_level,
                'position': entry.position,
                'games_played': entry.games_played,
                'wins': entry.wins,
                'draws': entry.draws,
                'losses': entry.losses,
                'table_points': entry.table_points,
                'match_points_for': entry.match_points_for,
                'match_points_against': entry.match_points_against,
                'pins_for': entry.pins_for,
                'pins_against': entry.pins_against,
                'avg_home_score': entry.avg_home_score,
                'avg_away_score': entry.avg_away_score,
                'emblem_url': f"/api/club-emblem/{entry.verein_id}" if entry.verein_id else None
            })

        return jsonify({
            'team_name': team.name,
            'club_name': team.club.name if team.club else 'Unbekannt',
            'history': history_data
        })

    except Exception as e:
        print(f"Error getting team history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Fehler beim Laden der Team-Historie"}), 500


@app.route('/api/teams/<int:team_id>/cup-history', methods=['GET'])
def get_team_cup_history(team_id):
    """Get historical cup participations for a team across all seasons."""
    try:
        from models import TeamCupHistory, Season

        # Verify team exists
        team = Team.query.get_or_404(team_id)

        # Check if TeamCupHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'team_cup_history' not in existing_tables:
            return jsonify({
                'team_name': team.name,
                'club_name': team.club.name if team.club else 'Unbekannt',
                'cup_history': []
            })

        # Get historical cup data for this team
        history_entries = TeamCupHistory.query.filter_by(
            team_id=team_id
        ).order_by(TeamCupHistory.season_id.desc()).all()

        # Format data
        cup_history_data = []
        for entry in history_entries:
            cup_history_data.append(entry.to_dict())

        return jsonify({
            'team_name': team.name,
            'club_name': team.club.name if team.club else 'Unbekannt',
            'cup_history': cup_history_data
        })

    except Exception as e:
        print(f"Error getting team cup history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Fehler beim Laden der Team-Pokal-Historie"}), 500


@app.route('/api/teams/<int:team_id>/achievements', methods=['GET'])
def get_team_achievements(team_id):
    """Get all achievements (league championships and cup wins) for a team across all seasons."""
    try:
        from models import TeamAchievement, Season

        # Verify team exists
        team = Team.query.get_or_404(team_id)

        # Check if TeamAchievement table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'team_achievement' not in existing_tables:
            return jsonify({
                'team_name': team.name,
                'club_name': team.club.name if team.club else 'Unbekannt',
                'achievements': []
            })

        # Get all achievements for this team
        achievements = TeamAchievement.query.filter_by(
            team_id=team_id
        ).order_by(TeamAchievement.season_id.desc(), TeamAchievement.achievement_type).all()

        # Format data
        achievements_data = []
        for achievement in achievements:
            achievements_data.append(achievement.to_dict())

        return jsonify({
            'team_name': team.name,
            'club_name': team.club.name if team.club else 'Unbekannt',
            'achievements': achievements_data
        })

    except Exception as e:
        print(f"Error getting team achievements: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Fehler beim Laden der Team-Erfolge"}), 500


# Player endpoints
@app.route('/api/players', methods=['GET'])
def get_players():
    players = Player.query.all()
    return jsonify([player.to_dict() for player in players])

@app.route('/api/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    player = Player.query.get_or_404(player_id)
    return jsonify(player.to_dict())

@app.route('/api/players/<int:player_id>/matches', methods=['GET'])
def get_player_matches(player_id):
    """Get all matches for a player (both league and cup matches)."""
    try:
        from models import PlayerMatchPerformance, PlayerCupMatchPerformance, Match, CupMatch
        from sqlalchemy import or_, and_

        # Verify player exists
        player = Player.query.get_or_404(player_id)

        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

        # Get all teams the player belongs to
        player_team_ids = [team.id for team in player.teams]

        if not player_team_ids:
            return jsonify({
                'player_name': player.name,
                'upcoming_matches': [],
                'recent_matches': []
            })

        # Get league matches for player's teams
        league_matches = Match.query.filter(
            and_(
                Match.season_id == current_season.id,
                or_(
                    Match.home_team_id.in_(player_team_ids),
                    Match.away_team_id.in_(player_team_ids)
                )
            )
        ).order_by(Match.match_date.desc()).all()

        # Get cup matches for player's teams
        cup_matches = CupMatch.query.join(Cup).filter(
            and_(
                Cup.season_id == current_season.id,
                or_(
                    CupMatch.home_team_id.in_(player_team_ids),
                    CupMatch.away_team_id.in_(player_team_ids)
                )
            )
        ).order_by(CupMatch.match_date.desc()).all()

        # Get player performances for league matches
        league_performances = {}
        if league_matches:
            match_ids = [m.id for m in league_matches]
            perfs = PlayerMatchPerformance.query.filter(
                and_(
                    PlayerMatchPerformance.player_id == player_id,
                    PlayerMatchPerformance.match_id.in_(match_ids)
                )
            ).all()
            league_performances = {p.match_id: p for p in perfs}

        # Get player performances for cup matches
        cup_performances = {}
        if cup_matches:
            cup_match_ids = [m.id for m in cup_matches]
            cup_perfs = PlayerCupMatchPerformance.query.filter(
                and_(
                    PlayerCupMatchPerformance.player_id == player_id,
                    PlayerCupMatchPerformance.cup_match_id.in_(cup_match_ids)
                )
            ).all()
            cup_performances = {p.cup_match_id: p for p in cup_perfs}

        # Combine and process matches
        all_matches = []

        # Process league matches
        for match in league_matches:
            player_participated = match.id in league_performances
            match_data = {
                'id': match.id,
                'type': 'league',
                'date': match.match_date.isoformat() if match.match_date else None,
                'homeTeam': match.home_team.name,
                'awayTeam': match.away_team.name,
                'homeScore': match.home_score,
                'awayScore': match.away_score,
                'league': match.league.name,
                'match_day': match.match_day,
                'is_played': match.is_played,
                'player_participated': player_participated,
                'player_performance': league_performances[match.id].to_dict() if player_participated else None
            }
            all_matches.append(match_data)

        # Process cup matches
        for cup_match in cup_matches:
            player_participated = cup_match.id in cup_performances
            # Convert cup match ID to frontend format (add 1,000,000)
            frontend_id = cup_match.id + 1000000
            match_data = {
                'id': frontend_id,
                'type': 'cup',
                'date': cup_match.match_date.isoformat() if cup_match.match_date else None,
                'homeTeam': cup_match.home_team.name,
                'awayTeam': cup_match.away_team.name if cup_match.away_team else 'Freilos',
                'homeScore': cup_match.home_score,
                'awayScore': cup_match.away_score,
                'league': f"{cup_match.cup.name} - {cup_match.round_name}",
                'match_day': cup_match.cup_match_day,
                'is_played': cup_match.is_played,
                'player_participated': player_participated,
                'player_performance': cup_performances[cup_match.id].to_dict() if player_participated else None
            }
            all_matches.append(match_data)

        # Sort all matches by date
        all_matches.sort(key=lambda x: x['date'] if x['date'] else '', reverse=True)

        # Split into upcoming and recent matches
        from datetime import datetime
        now = datetime.now()

        upcoming_matches = []
        recent_matches = []

        for match in all_matches:
            if match['date']:
                match_date = datetime.fromisoformat(match['date'].replace('Z', '+00:00'))
                if match_date > now:
                    upcoming_matches.append(match)
                else:
                    recent_matches.append(match)
            elif not match['is_played']:
                upcoming_matches.append(match)
            else:
                recent_matches.append(match)

        # Sort upcoming matches by date (earliest first)
        upcoming_matches.sort(key=lambda x: x['date'] if x['date'] else '', reverse=False)

        # Add visibility flag for expand/collapse functionality
        for i, match in enumerate(upcoming_matches):
            match['visible'] = i < 5

        for i, match in enumerate(recent_matches):
            match['visible'] = i < 5

        return jsonify({
            'player_name': player.name,
            'upcoming_matches': upcoming_matches,
            'recent_matches': recent_matches
        })

    except Exception as e:
        print(f"Error getting player matches: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Fehler beim Laden der Spieler-Spiele"}), 500

@app.route('/api/players/<int:player_id>/history', methods=['GET'])
def get_player_history(player_id):
    """Get historical team assignments and league positions for a player across all seasons."""
    try:
        from models import PlayerMatchPerformance, LeagueHistory, Season
        from sqlalchemy import func, distinct

        # Verify player exists
        player = Player.query.get_or_404(player_id)

        # Check if LeagueHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'league_history' not in existing_tables:
            return jsonify({
                'player_name': player.name,
                'history': []
            })

        # Get all seasons where the player played
        seasons_with_performances = db.session.query(
            PlayerMatchPerformance.team_id,
            Match.season_id,
            func.count(PlayerMatchPerformance.id).label('appearances')
        ).join(
            Match, PlayerMatchPerformance.match_id == Match.id
        ).filter(
            PlayerMatchPerformance.player_id == player_id
        ).group_by(
            PlayerMatchPerformance.team_id,
            Match.season_id
        ).all()

        history_data = []

        for team_id, season_id, appearances in seasons_with_performances:
            # Get team information
            team = Team.query.get(team_id)
            if not team:
                continue

            # Get season information
            season = Season.query.get(season_id)
            if not season:
                continue

            # Calculate player statistics for this team/season combination
            player_performances = PlayerMatchPerformance.query.join(
                Match, PlayerMatchPerformance.match_id == Match.id
            ).filter(
                PlayerMatchPerformance.player_id == player_id,
                PlayerMatchPerformance.team_id == team_id,
                Match.season_id == season_id
            ).all()

            # Calculate statistics
            home_performances = [p for p in player_performances if p.is_home_team]
            away_performances = [p for p in player_performances if not p.is_home_team]

            # Calculate averages
            avg_home_score = round(sum(p.total_score for p in home_performances) / len(home_performances), 1) if home_performances else 0
            avg_away_score = round(sum(p.total_score for p in away_performances) / len(away_performances), 1) if away_performances else 0
            avg_total_score = round(sum(p.total_score for p in player_performances) / len(player_performances), 1) if player_performances else 0

            # Calculate error averages
            avg_home_errors = round(sum(p.fehler_count for p in home_performances) / len(home_performances), 1) if home_performances else 0
            avg_away_errors = round(sum(p.fehler_count for p in away_performances) / len(away_performances), 1) if away_performances else 0
            avg_total_errors = round(sum(p.fehler_count for p in player_performances) / len(player_performances), 1) if player_performances else 0

            # Calculate Volle and Räumer averages
            avg_home_volle = round(sum(p.volle_score for p in home_performances) / len(home_performances), 1) if home_performances else 0
            avg_away_volle = round(sum(p.volle_score for p in away_performances) / len(away_performances), 1) if away_performances else 0
            avg_total_volle = round(sum(p.volle_score for p in player_performances) / len(player_performances), 1) if player_performances else 0

            avg_home_raeumer = round(sum(p.raeumer_score for p in home_performances) / len(home_performances), 1) if home_performances else 0
            avg_away_raeumer = round(sum(p.raeumer_score for p in away_performances) / len(away_performances), 1) if away_performances else 0
            avg_total_raeumer = round(sum(p.raeumer_score for p in player_performances) / len(player_performances), 1) if player_performances else 0

            # Get league history for this team and season
            league_history = LeagueHistory.query.filter_by(
                team_id=team_id,
                season_id=season_id
            ).first()

            if league_history:
                history_entry = {
                    'season_id': season_id,
                    'season_name': season.name,
                    'team_id': team_id,
                    'team_name': team.name,
                    'club_name': team.club.name if team.club else 'Unbekannt',
                    'league_name': league_history.league_name,
                    'league_level': league_history.league_level,
                    'final_position': league_history.position,
                    'appearances': appearances,
                    'games_played': league_history.games_played,
                    'wins': league_history.wins,
                    'draws': league_history.draws,
                    'losses': league_history.losses,
                    'table_points': league_history.table_points,
                    # Player statistics
                    'avg_home_score': avg_home_score,
                    'avg_away_score': avg_away_score,
                    'avg_total_score': avg_total_score,
                    'avg_home_errors': avg_home_errors,
                    'avg_away_errors': avg_away_errors,
                    'avg_total_errors': avg_total_errors,
                    'avg_home_volle': avg_home_volle,
                    'avg_away_volle': avg_away_volle,
                    'avg_total_volle': avg_total_volle,
                    'avg_home_raeumer': avg_home_raeumer,
                    'avg_away_raeumer': avg_away_raeumer,
                    'avg_total_raeumer': avg_total_raeumer,
                    'home_matches': len(home_performances),
                    'away_matches': len(away_performances)
                }
            else:
                # Fallback if no league history exists yet (current season)
                history_entry = {
                    'season_id': season_id,
                    'season_name': season.name,
                    'team_id': team_id,
                    'team_name': team.name,
                    'club_name': team.club.name if team.club else 'Unbekannt',
                    'league_name': team.league.name if team.league else 'Unbekannt',
                    'league_level': team.league.level if team.league else 0,
                    'final_position': None,  # Current season, no final position yet
                    'appearances': appearances,
                    'games_played': None,
                    'wins': None,
                    'draws': None,
                    'losses': None,
                    'table_points': None,
                    # Player statistics
                    'avg_home_score': avg_home_score,
                    'avg_away_score': avg_away_score,
                    'avg_total_score': avg_total_score,
                    'avg_home_errors': avg_home_errors,
                    'avg_away_errors': avg_away_errors,
                    'avg_total_errors': avg_total_errors,
                    'avg_home_volle': avg_home_volle,
                    'avg_away_volle': avg_away_volle,
                    'avg_total_volle': avg_total_volle,
                    'avg_home_raeumer': avg_home_raeumer,
                    'avg_away_raeumer': avg_away_raeumer,
                    'avg_total_raeumer': avg_total_raeumer,
                    'home_matches': len(home_performances),
                    'away_matches': len(away_performances)
                }

            history_data.append(history_entry)

        # Sort by season (newest first), then by team name
        history_data.sort(key=lambda x: (x['season_id'], x['team_name']), reverse=True)

        # If no history data exists, create sample data for demonstration
        if not history_data:
            # Check if this is a demo request
            demo_mode = request.args.get('demo', 'false').lower() == 'true'
            if demo_mode:
                history_data = [
                    {
                        'season_id': 1,
                        'season_name': 'Season 2024',
                        'team_id': 1,
                        'team_name': 'FC Bayern München I',
                        'club_name': 'FC Bayern München',
                        'league_name': 'Bundesliga',
                        'league_level': 1,
                        'final_position': 2,
                        'appearances': 18,
                        'avg_home_score': 645.2,
                        'avg_away_score': 612.8,
                        'avg_total_score': 629.0,
                        'avg_home_errors': 2.1,
                        'avg_away_errors': 3.4,
                        'avg_total_errors': 2.8,
                        'home_matches': 9,
                        'away_matches': 9
                    },
                    {
                        'season_id': 1,
                        'season_name': 'Season 2024',
                        'team_id': 2,
                        'team_name': 'FC Bayern München II',
                        'club_name': 'FC Bayern München',
                        'league_name': 'Regionalliga',
                        'league_level': 4,
                        'final_position': 1,
                        'appearances': 4,
                        'avg_home_score': 598.5,
                        'avg_away_score': 587.2,
                        'avg_total_score': 592.9,
                        'avg_home_errors': 3.5,
                        'avg_away_errors': 4.1,
                        'avg_total_errors': 3.8,
                        'home_matches': 2,
                        'away_matches': 2
                    }
                ]

        return jsonify({
            'player_name': player.name,
            'history': history_data
        })

    except Exception as e:
        print(f"Error getting player history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Fehler beim Laden der Spieler-Historie"}), 500

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
    # Get current season
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

    # Filter leagues by current season
    leagues = League.query.filter_by(season_id=current_season.id).all()
    return jsonify([league.to_dict() for league in leagues])

@app.route('/api/leagues/<int:league_id>', methods=['GET'])
def get_league(league_id):
    league = League.query.get_or_404(league_id)
    return jsonify(league.to_dict())

@app.route('/api/leagues/<int:league_id>/history', methods=['GET'])
def get_league_history(league_id):
    """Get historical standings for a league across all seasons."""
    try:
        from models import LeagueHistory, Season

        print(f"Getting history for league ID: {league_id}")

        # Get the current league to get its name and level
        current_league = League.query.get_or_404(league_id)
        print(f"League found: {current_league.name} (Level {current_league.level})")

        # Check if LeagueHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'league_history' not in existing_tables:
            print("LeagueHistory table does not exist")
            # Return empty history if table doesn't exist yet
            return jsonify({
                'league_name': current_league.name,
                'league_level': current_league.level,
                'seasons': []
            })

        print("LeagueHistory table exists, querying for data...")

        # Find all historical data for leagues with the same name and level
        # This handles the case where league IDs change between seasons
        history_entries = LeagueHistory.query.filter_by(
            league_name=current_league.name,
            league_level=current_league.level
        ).order_by(LeagueHistory.season_id.desc()).all()

        print(f"Found {len(history_entries)} history entries")

        # Group by season
        seasons_data = {}
        for entry in history_entries:
            season_id = entry.season_id
            if season_id not in seasons_data:
                seasons_data[season_id] = {
                    'season_id': season_id,
                    'season_name': entry.season_name,
                    'standings': []
                }
            seasons_data[season_id]['standings'].append(entry.to_dict())

        print(f"Grouped into {len(seasons_data)} seasons")

        # Sort standings within each season by position
        for season_data in seasons_data.values():
            season_data['standings'].sort(key=lambda x: x['position'])

        # Convert to list and sort by season (newest first)
        seasons_list = list(seasons_data.values())
        seasons_list.sort(key=lambda x: x['season_id'], reverse=True)

        result = {
            'league_name': current_league.name,
            'league_level': current_league.level,
            'seasons': seasons_list
        }

        print(f"Returning result with {len(seasons_list)} seasons")
        return jsonify(result)

    except Exception as e:
        print(f"Error getting league history: {e}")
        import traceback
        traceback.print_exc()
        # Return empty history on error
        try:
            current_league = League.query.get_or_404(league_id)
            return jsonify({
                'league_name': current_league.name,
                'league_level': current_league.level,
                'seasons': []
            })
        except:
            return jsonify({"error": "League not found"}), 404

@app.route('/api/leagues/<int:league_id>/history/<int:season_id>', methods=['GET'])
def get_league_history_season(league_id, season_id):
    """Get historical standings for a specific league and season."""
    try:
        from models import LeagueHistory

        # Get the current league to get its name and level
        current_league = League.query.get_or_404(league_id)

        # Check if LeagueHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'league_history' not in existing_tables:
            return jsonify({"error": "Keine historischen Daten verfügbar"}), 404

        # Get historical data for this specific season
        history_entries = LeagueHistory.query.filter_by(
            league_name=current_league.name,
            league_level=current_league.level,
            season_id=season_id
        ).order_by(LeagueHistory.position).all()

        if not history_entries:
            return jsonify({"error": "Keine historischen Daten für diese Liga und Saison gefunden"}), 404

        return jsonify({
            'league_name': current_league.name,
            'league_level': current_league.level,
            'season_id': season_id,
            'season_name': history_entries[0].season_name,
            'standings': [entry.to_dict() for entry in history_entries]
        })

    except Exception as e:
        print(f"Error getting league history for season: {e}")
        return jsonify({"error": "Fehler beim Laden der historischen Daten"}), 500

# Match endpoints
@app.route('/api/matches', methods=['GET'])
def get_matches():
    matches = Match.query.all()
    return jsonify([match.to_dict() for match in matches])

# Constants for ID ranges
CUP_MATCH_ID_OFFSET = 1000000  # Cup match IDs start at 1,000,000

def is_cup_match_id(match_id):
    """Check if a match ID belongs to a cup match."""
    return match_id >= CUP_MATCH_ID_OFFSET

def get_cup_match_db_id(frontend_id):
    """Convert frontend cup match ID to database ID."""
    return frontend_id - CUP_MATCH_ID_OFFSET

def get_cup_match_frontend_id(db_id):
    """Convert database cup match ID to frontend ID."""
    return db_id + CUP_MATCH_ID_OFFSET

@app.route('/api/matches/<int:match_id>', methods=['GET'])
def get_match(match_id):
    # Check if this is a cup match ID (>= 1,000,000)
    if is_cup_match_id(match_id):
        # Convert to database ID and look for cup match
        db_id = get_cup_match_db_id(match_id)
        cup_match = CupMatch.query.get(db_id)
        if cup_match:
            # Convert CupMatch to Match-like format for compatibility
            cup_match_data = cup_match.to_dict()

            # Load cup match performances
            cup_performances = PlayerCupMatchPerformance.query.filter_by(cup_match_id=db_id).all()
            performances_data = [perf.to_dict() for perf in cup_performances]

            # Add additional fields that MatchDetail expects
            cup_match_data.update({
                'id': match_id,  # Use the frontend ID
                'league_id': None,  # Cup matches don't have a league
                'league_name': f"{cup_match.cup.name} - {cup_match.round_name}",
                'match_day': cup_match.cup_match_day,
                'date': cup_match.match_date.isoformat() if cup_match.match_date else None,
                'venue': cup_match.home_team.club.name if cup_match.home_team and cup_match.home_team.club else 'Unbekannt',
                'attendance': 0,  # Cup matches don't track attendance yet
                'referee': 'Unbekannt',  # Cup matches don't track referee yet
                'round': cup_match.cup_match_day or 0,
                'performances': performances_data,  # Load actual cup match performances
                'is_cup_match': True,  # Flag to identify this as a cup match
                # Add fields for team club IDs (needed for emblems)
                'home_team_verein_id': cup_match.home_team.club.verein_id if cup_match.home_team and cup_match.home_team.club else None,
                'away_team_verein_id': cup_match.away_team.club.verein_id if cup_match.away_team and cup_match.away_team.club else None,
                'home_team_club_id': cup_match.home_team.club.id if cup_match.home_team and cup_match.home_team.club else None,
                'away_team_club_id': cup_match.away_team.club.id if cup_match.away_team and cup_match.away_team.club else None,
                # Add score fields with proper names
                'homeScore': cup_match.home_score,
                'awayScore': cup_match.away_score,
                'homeMatchPoints': int(cup_match.home_set_points * 2) if cup_match.home_set_points else 0,  # Convert set points to match points
                'awayMatchPoints': int(cup_match.away_set_points * 2) if cup_match.away_set_points else 0,
                'status': 'played' if cup_match.is_played else 'upcoming'
            })

            return jsonify(cup_match_data)
    else:
        # Look for regular league match
        match = Match.query.get(match_id)
        if match:
            match_data = match.to_dict()
            match_data['is_cup_match'] = False
            return jsonify(match_data)

    # If neither found, return 404
    abort(404)



# Helper function for auto-initialization
def auto_initialize_cups(season_id):
    """Automatically initialize cups and generate fixtures for a season."""
    from models import Cup, League

    created_cups = []

    # Create DKBC-Pokal (for leagues without bundesland and landkreis)
    dkbc_cup = Cup(
        name="DKBC-Pokal",
        cup_type="DKBC",
        season_id=season_id
    )
    db.session.add(dkbc_cup)
    created_cups.append(dkbc_cup)

    # Get all unique bundesland values (excluding None and empty strings)
    bundeslaender = db.session.query(League.bundesland).filter(
        League.season_id == season_id,
        League.bundesland.isnot(None),
        League.bundesland != ''
    ).distinct().all()

    # Create Landespokal for each Bundesland
    for (bundesland,) in bundeslaender:
        landespokal = Cup(
            name=f"{bundesland}-Pokal",
            cup_type="Landespokal",
            season_id=season_id,
            bundesland=bundesland
        )
        db.session.add(landespokal)
        created_cups.append(landespokal)

    # Get all unique landkreis values (excluding None and empty strings)
    landkreise = db.session.query(League.landkreis).filter(
        League.season_id == season_id,
        League.landkreis.isnot(None),
        League.landkreis != ''
    ).distinct().all()

    # Create Kreispokal for each Landkreis
    for (landkreis,) in landkreise:
        # Get the bundesland for this landkreis
        league_with_landkreis = League.query.filter_by(
            season_id=season_id,
            landkreis=landkreis
        ).first()

        if league_with_landkreis:
            kreispokal = Cup(
                name=f"Landkreis {landkreis}-Pokal",
                cup_type="Kreispokal",
                season_id=season_id,
                bundesland=league_with_landkreis.bundesland,
                landkreis=landkreis
            )
            db.session.add(kreispokal)
            created_cups.append(kreispokal)

    db.session.commit()

    # Auto-generate fixtures for all created cups
    for cup in created_cups:
        eligible_teams = cup.get_eligible_teams()
        if len(eligible_teams) >= 2:
            try:
                cup.generate_cup_fixtures()
                print(f"Generated fixtures for {cup.name} with {len(eligible_teams)} teams")
            except Exception as e:
                print(f"Error generating fixtures for {cup.name}: {e}")

    print(f"Auto-initialized {len(created_cups)} cups for season {season_id}")

# Cup endpoints
@app.route('/api/cups', methods=['GET'])
def get_cups():
    """Get all cups for the current season."""
    # Get current season
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

    # Filter cups by current season
    cups = Cup.query.filter_by(season_id=current_season.id).all()
    return jsonify([cup.to_dict() for cup in cups])

@app.route('/api/cups/<int:cup_id>', methods=['GET'])
def get_cup(cup_id):
    """Get detailed information about a specific cup."""
    cup = Cup.query.get_or_404(cup_id)
    cup_data = cup.to_dict()

    # Add eligible teams
    eligible_teams = cup.get_eligible_teams()
    cup_data['eligible_teams'] = [
        {
            'id': team.id,
            'name': team.name,
            'club_name': team.club.name if team.club else None,
            'league_name': team.league.name if team.league else None,
            'emblem_url': f"/api/club-emblem/{team.club.verein_id}" if team.club and team.club.verein_id else None
        }
        for team in eligible_teams
    ]

    # Add cup matches with frontend IDs
    cup_matches = CupMatch.query.filter_by(cup_id=cup_id).order_by(CupMatch.round_number, CupMatch.id).all()
    matches_data = []
    for match in cup_matches:
        match_data = match.to_dict()
        # Convert database ID to frontend ID for cup matches
        match_data['id'] = get_cup_match_frontend_id(match.id)
        matches_data.append(match_data)

    cup_data['matches'] = matches_data

    return jsonify(cup_data)

@app.route('/api/cups/by-type/<cup_type>', methods=['GET'])
def get_cups_by_type(cup_type):
    """Get all cups of a specific type (DKBC, Landespokal, Kreispokal)."""
    # Get current season
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

    # Validate cup type
    valid_types = ['DKBC', 'Landespokal', 'Kreispokal']
    if cup_type not in valid_types:
        return jsonify({"error": f"Ungültiger Pokaltyp. Erlaubt: {', '.join(valid_types)}"}), 400

    # Filter cups by type and current season
    cups = Cup.query.filter_by(season_id=current_season.id, cup_type=cup_type).all()
    return jsonify([cup.to_dict() for cup in cups])



@app.route('/api/cups/<int:cup_id>/advance-round', methods=['POST'])
def advance_cup_round(cup_id):
    """Advance cup to next round based on match results."""
    cup = Cup.query.get_or_404(cup_id)

    try:
        success = cup.advance_to_next_round()
        if success:
            if cup.is_active:
                return jsonify({
                    "success": True,
                    "message": f"Erfolgreich zur nächsten Runde aufgestiegen: {cup.current_round}",
                    "current_round": cup.current_round,
                    "current_round_number": cup.current_round_number,
                    "is_active": cup.is_active
                })
            else:
                return jsonify({
                    "success": True,
                    "message": f"Pokal {cup.name} ist beendet!",
                    "current_round": cup.current_round,
                    "current_round_number": cup.current_round_number,
                    "is_active": cup.is_active
                })
        else:
            return jsonify({
                "success": False,
                "message": "Nicht alle Spiele der aktuellen Runde wurden gespielt"
            })
    except Exception as e:
        return jsonify({"error": f"Fehler beim Aufstieg zur nächsten Runde: {str(e)}"}), 500

@app.route('/api/cups/match-days', methods=['GET'])
def get_cup_match_days():
    """Get all cup match days for the current season."""
    # Get current season
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404



    # Get all cup matches with their match days
    cup_matches = db.session.query(
        CupMatch.cup_match_day,
        Cup.name.label('cup_name'),
        Cup.cup_type,
        CupMatch.round_name,
        db.func.count(CupMatch.id).label('matches_count'),
        db.func.sum(db.case([(CupMatch.is_played == True, 1)], else_=0)).label('played_count')
    ).join(Cup).filter(
        Cup.season_id == current_season.id,
        CupMatch.cup_match_day.isnot(None)
    ).group_by(
        CupMatch.cup_match_day,
        Cup.name,
        Cup.cup_type,
        CupMatch.round_name
    ).order_by(CupMatch.cup_match_day).all()

    # Group by match day
    match_days = {}
    for match in cup_matches:
        match_day = match.cup_match_day
        if match_day not in match_days:
            match_days[match_day] = {
                'match_day': match_day,
                'cups': [],
                'total_matches': 0,
                'total_played': 0
            }

        match_days[match_day]['cups'].append({
            'name': match.cup_name,
            'type': match.cup_type,
            'round': match.round_name,
            'matches': match.matches_count,
            'played': match.played_count
        })
        match_days[match_day]['total_matches'] += match.matches_count
        match_days[match_day]['total_played'] += match.played_count

    return jsonify(list(match_days.values()))


@app.route('/api/cups/history', methods=['GET'])
def get_all_cups_history():
    """Get historical winners and finalists for all cups across all seasons."""
    try:
        from models import CupHistory

        # Check if CupHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'cup_history' not in existing_tables:
            return jsonify([])

        # Get all cup history entries, ordered by season (newest first)
        history_entries = CupHistory.query.order_by(CupHistory.season_id.desc()).all()

        return jsonify([entry.to_dict() for entry in history_entries])

    except Exception as e:
        print(f"Error getting all cups history: {e}")
        return jsonify({"error": "Fehler beim Laden der Pokal-Historie"}), 500


@app.route('/api/cups/history/<cup_type>', methods=['GET'])
def get_cups_history_by_type(cup_type):
    """Get historical winners and finalists for cups of a specific type."""
    try:
        from models import CupHistory

        # Validate cup type
        valid_types = ['DKBC', 'Landespokal', 'Kreispokal']
        if cup_type not in valid_types:
            return jsonify({"error": f"Ungültiger Pokaltyp. Erlaubt: {', '.join(valid_types)}"}), 400

        # Check if CupHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'cup_history' not in existing_tables:
            return jsonify([])

        # Get cup history entries for this type, ordered by season (newest first)
        history_entries = CupHistory.query.filter_by(
            cup_type=cup_type
        ).order_by(CupHistory.season_id.desc()).all()

        return jsonify([entry.to_dict() for entry in history_entries])

    except Exception as e:
        print(f"Error getting cups history by type: {e}")
        return jsonify({"error": "Fehler beim Laden der Pokal-Historie"}), 500


@app.route('/api/cups/history/cup/<cup_name>', methods=['GET'])
def get_cup_history_by_name(cup_name):
    """Get historical winners and finalists for a specific cup across all seasons."""
    try:
        from models import CupHistory

        # Check if CupHistory table exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'cup_history' not in existing_tables:
            return jsonify([])

        # Get cup history entries for this specific cup, ordered by season (newest first)
        history_entries = CupHistory.query.filter_by(
            cup_name=cup_name
        ).order_by(CupHistory.season_id.desc()).all()

        return jsonify([entry.to_dict() for entry in history_entries])

    except Exception as e:
        print(f"Error getting cup history by name: {e}")
        return jsonify({"error": "Fehler beim Laden der Pokal-Historie"}), 500


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

def get_season_status_data(season):
    """Helper function to get season status data."""
    # Check if all matches in the season are played (both league and cup matches)
    total_league_matches = Match.query.filter_by(season_id=season.id).count()
    played_league_matches = Match.query.filter_by(season_id=season.id, is_played=True).count()

    # Check cup matches
    from models import CupMatch, Cup
    total_cup_matches = db.session.query(CupMatch).join(Cup).filter(
        Cup.season_id == season.id
    ).count()
    played_cup_matches = db.session.query(CupMatch).join(Cup).filter(
        Cup.season_id == season.id,
        CupMatch.is_played == True
    ).count()

    # Total matches = league matches + cup matches
    total_matches = total_league_matches + total_cup_matches
    played_matches = played_league_matches + played_cup_matches

    is_completed = total_matches > 0 and total_matches == played_matches

    return {
        "season_id": season.id,
        "season_name": season.name,
        "is_completed": is_completed,
        "total_matches": total_matches,
        "played_matches": played_matches,
        "unplayed_matches": total_matches - played_matches
    }

@app.route('/api/season/status', methods=['GET'])
def get_season_status():
    """Get the status of the current season (completed or not)."""
    try:
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            return jsonify({"error": "Keine aktuelle Saison gefunden"}), 404

        # Check if all matches in the season are played (both league and cup matches)
        total_league_matches = Match.query.filter_by(season_id=current_season.id).count()
        played_league_matches = Match.query.filter_by(season_id=current_season.id, is_played=True).count()

        # Check cup matches
        from models import CupMatch, Cup
        total_cup_matches = db.session.query(CupMatch).join(Cup).filter(
            Cup.season_id == current_season.id
        ).count()
        played_cup_matches = db.session.query(CupMatch).join(Cup).filter(
            Cup.season_id == current_season.id,
            CupMatch.is_played == True
        ).count()

        # Total matches = league matches + cup matches
        total_matches = total_league_matches + total_cup_matches
        played_matches = played_league_matches + played_cup_matches

        # Additional debug: Check matches without match_day
        matches_without_match_day = Match.query.filter_by(season_id=current_season.id).filter(Match.match_day.is_(None)).count()
        unplayed_league_matches = Match.query.filter_by(season_id=current_season.id, is_played=False).count()
        unplayed_cup_matches = db.session.query(CupMatch).join(Cup).filter(
            Cup.season_id == current_season.id,
            CupMatch.is_played == False
        ).count()
        unplayed_matches = unplayed_league_matches + unplayed_cup_matches

        is_completed = total_matches > 0 and total_matches == played_matches

        # Debug logging
        print(f"DEBUG: Season status check for {current_season.name} (ID: {current_season.id})")
        print(f"DEBUG: League matches: {played_league_matches}/{total_league_matches} played")
        print(f"DEBUG: Cup matches: {played_cup_matches}/{total_cup_matches} played")
        print(f"DEBUG: Total matches: {played_matches}/{total_matches} played")
        print(f"DEBUG: Unplayed league matches: {unplayed_league_matches}")
        print(f"DEBUG: Unplayed cup matches: {unplayed_cup_matches}")
        print(f"DEBUG: Matches without match_day: {matches_without_match_day}")
        print(f"DEBUG: Season completed: {is_completed}")

        # Get some sample unplayed matches for debugging
        sample_unplayed_league = Match.query.filter_by(season_id=current_season.id, is_played=False).limit(3).all()
        sample_unplayed_cup = db.session.query(CupMatch).join(Cup).filter(
            Cup.season_id == current_season.id,
            CupMatch.is_played == False
        ).limit(3).all()

        print(f"DEBUG: Sample unplayed league matches:")
        for match in sample_unplayed_league:
            print(f"  Match {match.id}: {match.home_team.name} vs {match.away_team.name}, match_day: {match.match_day}, league: {match.league.name}")

        print(f"DEBUG: Sample unplayed cup matches:")
        for match in sample_unplayed_cup:
            print(f"  Cup Match {match.id}: {match.home_team.name} vs {match.away_team.name}, cup_match_day: {match.cup_match_day}, round: {match.round_name}")

        return jsonify({
            "season_id": current_season.id,
            "season_name": current_season.name,
            "is_completed": is_completed,
            "total_matches": total_matches,
            "played_matches": played_matches,
            "unplayed_matches": unplayed_matches,
            "league_matches": {
                "total": total_league_matches,
                "played": played_league_matches,
                "unplayed": unplayed_league_matches
            },
            "cup_matches": {
                "total": total_cup_matches,
                "played": played_cup_matches,
                "unplayed": unplayed_cup_matches
            },
            "matches_without_match_day": matches_without_match_day,
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

        # Check if all matches are played (both league and cup matches)
        total_league_matches = Match.query.filter_by(season_id=current_season.id).count()
        played_league_matches = Match.query.filter_by(season_id=current_season.id, is_played=True).count()

        # Check cup matches
        from models import CupMatch, Cup
        total_cup_matches = db.session.query(CupMatch).join(Cup).filter(
            Cup.season_id == current_season.id
        ).count()
        played_cup_matches = db.session.query(CupMatch).join(Cup).filter(
            Cup.season_id == current_season.id,
            CupMatch.is_played == True
        ).count()

        total_matches = total_league_matches + total_cup_matches
        played_matches = played_league_matches + played_cup_matches

        if total_matches == 0 or total_matches != played_matches:
            unplayed_league = total_league_matches - played_league_matches
            unplayed_cup = total_cup_matches - played_cup_matches
            return jsonify({
                "error": f"Die Saison ist noch nicht abgeschlossen. Noch {unplayed_league} Liga-Spiele und {unplayed_cup} Pokal-Spiele ausstehend."
            }), 400

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

        # Check if leagues exist and have teams
        leagues = League.query.filter_by(season_id=current_season.id).all()
        if not leagues:
            return jsonify({"error": "Keine Ligen in der aktuellen Saison gefunden"}), 404

        # Check for empty leagues and generate fixtures if needed
        empty_leagues = []
        leagues_fixed = 0

        for league in leagues:
            teams = Team.query.filter_by(league_id=league.id).all()
            matches = Match.query.filter_by(league_id=league.id, season_id=current_season.id).count()

            if len(teams) == 0:
                empty_leagues.append(league.name)
            elif len(teams) >= 2 and matches == 0:
                print(f"Generating missing fixtures for league {league.name}")
                simulation.generate_fixtures(league, current_season)
                leagues_fixed += 1

        if empty_leagues:
            return jsonify({
                "error": f"Folgende Ligen haben keine Teams: {', '.join(empty_leagues)}. Bitte überprüfen Sie die Saisonwechsel-Logik."
            }), 400

        if leagues_fixed > 0:
            print(f"Fixed {leagues_fixed} leagues by generating missing fixtures")

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
        import traceback
        traceback.print_exc()
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

        # Add new columns to Team table for cheat function
        try:
            # Check if the new columns exist
            inspector = db.inspect(db.engine)
            team_columns = [col['name'] for col in inspector.get_columns('team')]

            columns_to_add = []
            if 'target_league_level' not in team_columns:
                columns_to_add.append('target_league_level INTEGER')
            if 'target_league_bundesland' not in team_columns:
                columns_to_add.append('target_league_bundesland VARCHAR(50)')
            if 'target_league_landkreis' not in team_columns:
                columns_to_add.append('target_league_landkreis VARCHAR(100)')
            if 'target_league_altersklasse' not in team_columns:
                columns_to_add.append('target_league_altersklasse VARCHAR(50)')

            # Add the columns if they don't exist
            for column_def in columns_to_add:
                try:
                    db.session.execute(f'ALTER TABLE team ADD COLUMN {column_def}')
                    db.session.commit()
                    print(f"Added column to team table: {column_def}")
                except Exception as e:
                    print(f"Error adding column {column_def}: {e}")
                    db.session.rollback()

        except Exception as e:
            print(f"Error checking/adding team table columns: {e}")

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
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        return jsonify({"error": "No current season found"}), 404

    played_matches = Match.query.filter_by(season_id=current_season.id, is_played=True).all()
    unplayed_matches = Match.query.filter_by(season_id=current_season.id, is_played=False).all()
    all_matches = Match.query.filter_by(season_id=current_season.id).all()

    # Check match_day distribution
    matches_with_match_day = Match.query.filter_by(season_id=current_season.id).filter(Match.match_day.isnot(None)).all()
    matches_without_match_day = Match.query.filter_by(season_id=current_season.id).filter(Match.match_day.is_(None)).all()

    return jsonify({
        'season_id': current_season.id,
        'season_name': current_season.name,
        'total_matches': len(all_matches),
        'played_matches_count': len(played_matches),
        'unplayed_matches_count': len(unplayed_matches),
        'matches_with_match_day': len(matches_with_match_day),
        'matches_without_match_day': len(matches_without_match_day),
        'is_season_completed': len(all_matches) > 0 and len(all_matches) == len(played_matches),
        'sample_unplayed_matches': [
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
            for match in unplayed_matches[:10]  # Limit to 10 unplayed matches
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
