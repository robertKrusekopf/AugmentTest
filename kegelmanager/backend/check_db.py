from flask import Flask
from models import db, Season, League, Team, Match

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Überprüfe, ob es eine aktuelle Saison gibt
    current_season = Season.query.filter_by(is_current=True).first()
    if current_season:
        print(f"Aktuelle Saison gefunden: {current_season.name}")
        
        # Überprüfe, ob es Ligen gibt
        leagues = League.query.filter_by(season_id=current_season.id).all()
        print(f"Anzahl der Ligen: {len(leagues)}")
        
        for league in leagues:
            print(f"Liga: {league.name}, Level: {league.level}")
            
            # Überprüfe, ob es Teams gibt
            teams = Team.query.filter_by(league_id=league.id).all()
            print(f"  Anzahl der Teams: {len(teams)}")
            
            # Überprüfe, ob es Matches gibt
            matches = Match.query.filter_by(league_id=league.id, season_id=current_season.id).all()
            print(f"  Anzahl der Matches: {len(matches)}")
            
            # Überprüfe, ob es ungespielte Matches gibt
            unplayed_matches = Match.query.filter_by(league_id=league.id, season_id=current_season.id, is_played=False).all()
            print(f"  Anzahl der ungespielten Matches: {len(unplayed_matches)}")
    else:
        print("Keine aktuelle Saison gefunden!")
        
        # Überprüfe, ob es überhaupt Saisons gibt
        seasons = Season.query.all()
        print(f"Anzahl der Saisons: {len(seasons)}")
