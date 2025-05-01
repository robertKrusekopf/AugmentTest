from flask import Flask
from models import db, PlayerMatchPerformance, Match

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Überprüfe, ob es Spielerleistungen gibt
    performances = PlayerMatchPerformance.query.all()
    print(f"Anzahl der Spielerleistungen: {len(performances)}")

    # Überprüfe, ob es gespielte Spiele gibt
    played_matches = Match.query.filter_by(is_played=True).all()
    print(f"Anzahl der gespielten Spiele: {len(played_matches)}")

    # Zeige Details zu den gespielten Spielen
    for match in played_matches[:5]:  # Zeige nur die ersten 5 an
        print(f"Spiel {match.id}: {match.home_team.name} vs {match.away_team.name}, Ergebnis: {match.home_score}:{match.away_score}")
