from flask import Flask
from models import db, Season, Match
import simulation

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager_default.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Find the current season
    current_season = Season.query.filter_by(is_current=True).first()
    
    if current_season:
        print(f'Simulating match day for season {current_season.name}')
        
        # Count matches before simulation
        played_matches_before = Match.query.filter_by(is_played=True).count()
        print(f'Played matches before simulation: {played_matches_before}')
        
        # Simulate a match day
        result = simulation.simulate_match_day(current_season)
        
        # Count matches after simulation
        played_matches_after = Match.query.filter_by(is_played=True).count()
        print(f'Played matches after simulation: {played_matches_after}')
        print(f'Newly simulated matches: {played_matches_after - played_matches_before}')
        
        print('Simulation result:')
        print(result)
    else:
        print('No current season found')
