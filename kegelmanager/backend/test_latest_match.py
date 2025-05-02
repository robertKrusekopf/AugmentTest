from flask import Flask
from models import db, Match, PlayerMatchPerformance

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager_default.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Find the latest played match
    match = Match.query.filter_by(is_played=True).order_by(Match.id.desc()).first()
    
    if match:
        print('Latest match data:')
        match_dict = match.to_dict()
        print(f"Match ID: {match_dict['id']}")
        print(f"Home team: {match_dict['home_team_id']}")
        print(f"Away team: {match_dict['away_team_id']}")
        print(f"Home score: {match_dict['home_score']}")
        print(f"Away score: {match_dict['away_score']}")
        print(f"Home match points: {match_dict['home_match_points']}")
        print(f"Away match points: {match_dict['away_match_points']}")
        print(f"Is played: {match_dict['is_played']}")
        
        # Check player performances
        performances = match_dict.get('performances', [])
        print(f"\nNumber of player performances: {len(performances)}")
        
        if performances:
            # Group performances by team
            home_performances = [p for p in performances if p['is_home_team']]
            away_performances = [p for p in performances if not p['is_home_team']]
            
            print(f"\nHome team performances ({len(home_performances)}):")
            for perf in home_performances:
                print(f"  Player: {perf['player_name']} (ID: {perf['player_id']})")
                print(f"  Position: {perf['position_number']}")
                print(f"  Lanes: {perf['lane1_score']}, {perf['lane2_score']}, {perf['lane3_score']}, {perf['lane4_score']}")
                print(f"  Total: {perf['total_score']}")
                print(f"  Set points: {perf.get('set_points', 'N/A')}")
                print(f"  Match points: {perf.get('match_points', 'N/A')}")
                print()
            
            print(f"\nAway team performances ({len(away_performances)}):")
            for perf in away_performances:
                print(f"  Player: {perf['player_name']} (ID: {perf['player_id']})")
                print(f"  Position: {perf['position_number']}")
                print(f"  Lanes: {perf['lane1_score']}, {perf['lane2_score']}, {perf['lane3_score']}, {perf['lane4_score']}")
                print(f"  Total: {perf['total_score']}")
                print(f"  Set points: {perf.get('set_points', 'N/A')}")
                print(f"  Match points: {perf.get('match_points', 'N/A')}")
                print()
    else:
        print('No played matches found')
