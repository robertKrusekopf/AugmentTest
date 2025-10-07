"""
Script to fix player ages based on their league's altersklasse.
This updates existing players in the database to have the correct age range.
"""

import sys
sys.path.insert(0, '.')

from models import db, League, Team, Player
from flask import Flask
from init_db import get_age_range_for_altersklasse
import os
import random

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
    print("\n" + "="*80)
    print("FIXING PLAYER AGES BASED ON LEAGUE ALTERSKLASSE")
    print("="*80)
    
    # Get all teams with their leagues
    teams = Team.query.join(League).all()
    
    total_players_updated = 0
    teams_processed = 0
    
    for team in teams:
        if not team.league:
            continue
        
        # Get the age range for this league's altersklasse
        min_age, max_age = get_age_range_for_altersklasse(team.league.altersklasse)
        
        # Get all players for this team
        players = Player.query.join(Player.teams).filter(Team.id == team.id).all()
        
        if not players:
            continue
        
        players_updated = 0
        
        for player in players:
            # Check if player's age is outside the expected range
            if player.age < min_age or player.age > max_age:
                old_age = player.age
                # Generate new age within the correct range
                player.age = random.randint(min_age, max_age)
                players_updated += 1
                total_players_updated += 1
                
                if players_updated <= 3:  # Show first 3 examples per team
                    print(f"  {player.name}: {old_age} -> {player.age}")
        
        if players_updated > 0:
            teams_processed += 1
            print(f"\nTeam: {team.name}")
            print(f"  League: {team.league.name} (Altersklasse: '{team.league.altersklasse}')")
            print(f"  Expected age range: {min_age}-{max_age}")
            print(f"  Players updated: {players_updated}/{len(players)}")
    
    # Commit all changes
    if total_players_updated > 0:
        db.session.commit()
        print("\n" + "="*80)
        print(f"✓ Successfully updated {total_players_updated} players across {teams_processed} teams")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("✓ No players needed updating - all ages are already correct!")
        print("="*80)
    
    # Show statistics after fix
    print("\n" + "="*80)
    print("VERIFICATION - SAMPLE TEAMS AFTER FIX:")
    print("="*80)
    
    for league in League.query.all()[:5]:
        teams = Team.query.filter_by(league_id=league.id).limit(1).all()
        
        for team in teams:
            players = Player.query.join(Player.teams).filter(Team.id == team.id).all()
            
            if players:
                ages = [p.age for p in players]
                min_age_actual = min(ages)
                max_age_actual = max(ages)
                avg_age = sum(ages) / len(ages)
                
                expected_min, expected_max = get_age_range_for_altersklasse(league.altersklasse)
                
                status = "✓" if min_age_actual >= expected_min and max_age_actual <= expected_max else "✗"
                
                print(f"\n{status} Team: {team.name}")
                print(f"  League: {league.name} (Altersklasse: '{league.altersklasse}')")
                print(f"  Expected: {expected_min}-{expected_max}, Actual: {min_age_actual}-{max_age_actual} (avg: {avg_age:.1f})")
                print(f"  Ages: {sorted(ages)}")

