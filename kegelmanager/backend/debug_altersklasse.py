"""
Debug script to check if altersklasse is being read and used correctly.
"""

import sys
sys.path.insert(0, '.')

from models import db, League, Team, Player
from flask import Flask
import os

# Find the current database
db_path = None
if os.path.exists('selected_db.txt'):
    with open('selected_db.txt', 'r') as f:
        db_path = f.read().strip()

if not db_path or not os.path.exists(db_path):
    # Try default database
    if os.path.exists('instance/kegelmanager_default.db'):
        db_path = 'instance/kegelmanager_default.db'
    elif os.path.exists('kegelmanager.db'):
        db_path = 'kegelmanager.db'
    else:
        print("No database found!")
        sys.exit(1)

print(f"Using database: {db_path}")

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Check leagues and their altersklasse
    print("\n" + "="*80)
    print("LEAGUES AND THEIR ALTERSKLASSE:")
    print("="*80)
    
    leagues = League.query.all()
    for league in leagues:
        team_count = Team.query.filter_by(league_id=league.id).count()
        print(f"\nLeague: {league.name}")
        print(f"  Level: {league.level}")
        print(f"  Altersklasse: '{league.altersklasse}' (type: {type(league.altersklasse).__name__})")
        print(f"  Teams: {team_count}")
        
        # Check if altersklasse is empty or None
        if not league.altersklasse:
            print(f"  ⚠️  WARNING: Altersklasse is empty or None!")
    
    # Check some teams and their players' ages
    print("\n" + "="*80)
    print("SAMPLE TEAMS AND PLAYER AGES:")
    print("="*80)
    
    # Get a few teams from different leagues
    for league in leagues[:5]:  # First 5 leagues
        teams = Team.query.filter_by(league_id=league.id).limit(2).all()
        
        for team in teams:
            players = Player.query.join(Player.teams).filter(Team.id == team.id).all()
            
            if players:
                ages = [p.age for p in players]
                avg_age = sum(ages) / len(ages)
                min_age = min(ages)
                max_age = max(ages)
                
                print(f"\nTeam: {team.name}")
                print(f"  League: {league.name} (Altersklasse: '{league.altersklasse}')")
                print(f"  Players: {len(players)}")
                print(f"  Age range: {min_age}-{max_age} (avg: {avg_age:.1f})")
                print(f"  Individual ages: {sorted(ages)}")
                
                # Check if ages match expected range for altersklasse
                from init_db import get_age_range_for_altersklasse
                expected_min, expected_max = get_age_range_for_altersklasse(league.altersklasse)
                
                if min_age < expected_min or max_age > expected_max:
                    print(f"  ⚠️  WARNING: Ages don't match expected range ({expected_min}-{expected_max})!")
    
    # Statistics
    print("\n" + "="*80)
    print("STATISTICS:")
    print("="*80)
    
    total_leagues = League.query.count()
    leagues_with_altersklasse = League.query.filter(League.altersklasse.isnot(None), League.altersklasse != '').count()
    leagues_without_altersklasse = total_leagues - leagues_with_altersklasse
    
    print(f"Total leagues: {total_leagues}")
    print(f"Leagues with altersklasse: {leagues_with_altersklasse}")
    print(f"Leagues without altersklasse: {leagues_without_altersklasse}")
    
    # Count leagues by altersklasse
    print("\nLeagues by altersklasse:")
    from sqlalchemy import func
    altersklasse_counts = db.session.query(
        League.altersklasse, 
        func.count(League.id)
    ).group_by(League.altersklasse).all()
    
    for altersklasse, count in altersklasse_counts:
        display_name = altersklasse if altersklasse else "(None/Empty)"
        print(f"  {display_name}: {count}")

