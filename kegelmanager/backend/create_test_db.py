import os
import sys
import random
from datetime import datetime
from flask import Flask
from models import db, Club, League, Team, Season

def create_test_database(db_name="test_base"):
    """
    Erstellt eine Test-Datenbank mit nur Vereinen und Teams, aber ohne Spieler.
    Diese kann dann mit extend_existing_db.py erweitert werden.
    """
    
    # Stelle sicher, dass der Name keine .db Endung hat
    if db_name.endswith('.db'):
        db_name = db_name[:-3]

    # Stelle sicher, dass der Instance-Ordner existiert
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

    # Vollständiger Pfad zur Datenbank
    db_path = os.path.join(instance_dir, f"{db_name}.db")

    # Überprüfe, ob die Datenbank bereits existiert
    if os.path.exists(db_path):
        print(f"Fehler: Datenbank '{db_name}.db' existiert bereits.")
        return {"success": False, "message": f"Datenbank '{db_name}.db' existiert bereits."}

    # Erstelle eine neue Flask-App und konfiguriere die Datenbank
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # Erstelle alle Tabellen
        db.create_all()
        print(f"Datenbank '{db_name}.db' wurde erstellt.")

        # Erstelle eine Saison
        season = Season(
            name="Test Season 2025",
            start_date=datetime(2025, 8, 1).date(),
            end_date=datetime(2026, 5, 31).date(),
            is_current=True
        )
        db.session.add(season)
        db.session.flush()

        # Erstelle einige Test-Ligen
        leagues = []
        league_names = [
            "Bundesliga",
            "2. Bundesliga",
            "Regionalliga Nord",
            "Oberliga Hamburg",
            "Landesliga Hamburg"
        ]
        
        for i, league_name in enumerate(league_names, 1):
            league = League(
                name=league_name,
                level=i,
                season_id=season.id,
                state="Hamburg",
                district="Hamburg",
                age_group="Herren"
            )
            leagues.append(league)
            db.session.add(league)
        
        db.session.flush()

        # Erstelle einige Test-Vereine
        club_names = [
            "FC St. Pauli",
            "Hamburger SV", 
            "FC Eintracht Norderstedt",
            "TSV Buchholz 08",
            "SC Victoria Hamburg",
            "Altona 93",
            "TuS Dassendorf",
            "Barmbek-Uhlenhorst"
        ]

        clubs = []
        for i, club_name in enumerate(club_names):
            club = Club(
                name=club_name,
                founded=random.randint(1900, 1980),
                reputation=random.randint(50, 90),
                fans=random.randint(500, 10000),
                training_facilities=random.randint(30, 90),
                coaching=random.randint(30, 90),
                verein_id=i+1000,
                lane_quality=random.uniform(0.95, 1.05)
            )
            clubs.append(club)
            db.session.add(club)
        
        db.session.flush()

        # Erstelle Teams für die Vereine (aber keine Spieler)
        for i, club in enumerate(clubs):
            # Jeder Verein bekommt 1-2 Teams in verschiedenen Ligen
            num_teams = random.randint(1, 2)
            
            for team_num in range(num_teams):
                # Wähle eine Liga basierend auf der Vereinsstärke
                league_index = min(i // 2, len(leagues) - 1)
                league = leagues[league_index]
                
                # Team-Name
                if team_num == 0:
                    team_name = club.name
                else:
                    team_name = f"{club.name} II"
                
                # Team-Stärke basierend auf Liga
                league_base = max(25, 75 - (league.level - 1) * 5.56)
                team_strength = random.randint(max(30, int(league_base - 10)), min(99, int(league_base + 10)))
                
                team = Team(
                    name=team_name,
                    club_id=club.id,
                    league_id=league.id,
                    staerke=team_strength,
                    is_youth_team=False
                )
                db.session.add(team)

        # Speichere alle Änderungen
        db.session.commit()
        print(f"Test-Datenbank '{db_name}.db' mit {len(clubs)} Vereinen und Teams erstellt (ohne Spieler).")
        
        return {"success": True, "message": f"Test-Datenbank '{db_name}.db' erstellt."}

if __name__ == "__main__":
    # Überprüfe, ob ein Datenbankname als Argument übergeben wurde
    db_name = "test_base"
    if len(sys.argv) > 1:
        db_name = sys.argv[1]

    result = create_test_database(db_name)

    if result["success"]:
        print(result["message"])
        print(f"Sie können diese Datenbank jetzt mit extend_existing_db.py erweitern:")
        print(f"python extend_existing_db.py instance/{db_name}.db {db_name}_extended")
        sys.exit(0)
    else:
        print(f"Fehler: {result['message']}")
        sys.exit(1)
