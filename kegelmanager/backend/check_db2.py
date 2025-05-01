from flask import Flask
from models import db, Player, Team, League, Match, Season, PlayerMatchPerformance

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        # Überprüfe, ob die Tabelle PlayerMatchPerformance existiert
        from sqlalchemy import text
        db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='player_match_performance'"))
        print("Die Tabelle PlayerMatchPerformance existiert.")
    except Exception as e:
        print(f"Fehler beim Überprüfen der Tabelle PlayerMatchPerformance: {e}")
        print("Die Tabelle PlayerMatchPerformance existiert möglicherweise nicht.")

    # Überprüfe, ob es Spieler mit den neuen Attributen gibt
    try:
        players = Player.query.limit(5).all()
        if players:
            print(f"Gefundene Spieler: {len(players)}")
            for player in players:
                print(f"Spieler: {player.name}, Stärke: {player.strength}, Konsistenz: {player.consistency}, Präzision: {player.precision}, Ausdauer: {player.stamina}")
        else:
            print("Keine Spieler gefunden.")
    except Exception as e:
        print(f"Fehler beim Überprüfen der Spieler: {e}")

    # Überprüfe, ob es Matches gibt
    try:
        matches = Match.query.limit(5).all()
        if matches:
            print(f"Gefundene Matches: {len(matches)}")
            for match in matches:
                print(f"Match: {match.id}, Heimteam: {match.home_team.name}, Auswärtsteam: {match.away_team.name}, Gespielt: {match.is_played}")
        else:
            print("Keine Matches gefunden.")
    except Exception as e:
        print(f"Fehler beim Überprüfen der Matches: {e}")
