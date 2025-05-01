import os
import sys
import sqlite3
from flask import Flask
from models import db, Match, PlayerMatchPerformance, Season

# Bestimme den Pfad zur Datenbank
db_path = "kegelmanager.db"
instance_db_path = os.path.join("instance", "kegelmanager.db")

if os.path.exists(instance_db_path):
    db_uri = f'sqlite:///{instance_db_path}'
else:
    db_uri = f'sqlite:///{db_path}'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def reset_database():
    """Reset the database to its initial state with no played matches."""
    with app.app_context():
        print("Resetting database...")

        # 1. Lösche alle Spielerleistungen
        print("Deleting all player performances...")
        PlayerMatchPerformance.query.delete()

        # 2. Setze alle Spiele auf nicht gespielt
        print("Resetting all matches to unplayed...")
        matches = Match.query.all()
        for match in matches:
            match.is_played = False
            match.home_score = None
            match.away_score = None
            match.match_date = None

        # 3. Stelle sicher, dass eine aktuelle Saison gesetzt ist
        print("Setting current season...")
        Season.query.update({Season.is_current: False})
        season = Season.query.first()
        if season:
            season.is_current = True

        # 4. Speichere die Änderungen
        db.session.commit()

        print("Database reset complete!")
        print(f"Total matches: {Match.query.count()}")
        print(f"Played matches: {Match.query.filter_by(is_played=True).count()}")
        print(f"Player performances: {PlayerMatchPerformance.query.count()}")

if __name__ == "__main__":
    # Überprüfe, ob die Datenbank existiert
    if not os.path.exists(db_path) and not os.path.exists(instance_db_path):
        print("Database does not exist. Please run init_db.py first.")
        sys.exit(1)

    reset_database()
