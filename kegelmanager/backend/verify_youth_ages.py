"""
Verify that youth league players have correct ages.
"""

import sys
sys.path.insert(0, '.')

from models import db, League, Team, Player
from flask import Flask
from init_db import get_age_range_for_altersklasse
import os

# Find the current database
db_path = None
if os.path.exists('selected_db.txt'):
    with open('selected_db.txt', 'r') as f:
        db_path = f.read().strip()

if not db_path or not os.path.exists(db_path):
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
    print("\n" + "="*80)
    print("YOUTH LEAGUES - PLAYER AGE VERIFICATION")
    print("="*80)
    
    # Get all youth leagues (B, C, D, E, F)
    youth_leagues = League.query.filter(
        League.altersklasse.in_(['B', 'C', 'D', 'E', 'F', 'A'])
    ).all()
    
    for league in youth_leagues:
        print(f"\n{'='*80}")
        print(f"League: {league.name} (Altersklasse: '{league.altersklasse}')")
        
        expected_min, expected_max = get_age_range_for_altersklasse(league.altersklasse)
        print(f"Expected age range: {expected_min}-{expected_max}")
        
        teams = Team.query.filter_by(league_id=league.id).limit(3).all()
        
        for team in teams:
            players = Player.query.join(Player.teams).filter(Team.id == team.id).all()
            
            if players:
                ages = [p.age for p in players]
                min_age = min(ages)
                max_age = max(ages)
                avg_age = sum(ages) / len(ages)
                
                # Check if all ages are within expected range
                all_correct = all(expected_min <= age <= expected_max for age in ages)
                status = "✓" if all_correct else "✗"
                
                print(f"\n  {status} Team: {team.name}")
                print(f"    Players: {len(players)}")
                print(f"    Age range: {min_age}-{max_age} (avg: {avg_age:.1f})")
                print(f"    Ages: {sorted(ages)}")
                
                if not all_correct:
                    wrong_ages = [age for age in ages if age < expected_min or age > expected_max]
                    print(f"    ⚠️  WARNING: {len(wrong_ages)} players with wrong age: {wrong_ages}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_issues = 0
    
    for league in youth_leagues:
        expected_min, expected_max = get_age_range_for_altersklasse(league.altersklasse)
        
        teams = Team.query.filter_by(league_id=league.id).all()
        league_issues = 0
        
        for team in teams:
            players = Player.query.join(Player.teams).filter(Team.id == team.id).all()
            
            for player in players:
                if player.age < expected_min or player.age > expected_max:
                    league_issues += 1
                    total_issues += 1
        
        status = "✓" if league_issues == 0 else "✗"
        print(f"{status} {league.name} ('{league.altersklasse}'): {league_issues} players with wrong age")
    
    print("\n" + "="*80)
    if total_issues == 0:
        print("✓ ALL YOUTH PLAYERS HAVE CORRECT AGES!")
    else:
        print(f"✗ {total_issues} players have incorrect ages")
    print("="*80)

