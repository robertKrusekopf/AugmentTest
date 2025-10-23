"""
Comprehensive check for age class violations and unassigned players across all clubs.
"""

import sys
sys.path.insert(0, '.')

from models import db, Team, Player, Club
from flask import Flask
from age_class_utils import is_player_allowed_in_team, normalize_altersklasse, get_minimum_altersklasse_for_age
from collections import defaultdict
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
    print("COMPREHENSIVE AGE CLASS AND ASSIGNMENT CHECK")
    print("="*80)
    
    all_violations = []
    all_unassigned = []
    clubs_checked = 0
    
    # Check all clubs
    for club in Club.query.all():
        teams = Team.query.filter_by(club_id=club.id).all()
        players = Player.query.filter_by(club_id=club.id, is_retired=False).all()
        
        if not teams or not players:
            continue
        
        clubs_checked += 1
        
        # Check for violations
        for player in players:
            if not player.age:
                continue
            
            # Check if player has no team assignment
            if len(player.teams) == 0:
                all_unassigned.append({
                    'club': club.name,
                    'player': player.name,
                    'age': player.age,
                    'min_class': get_minimum_altersklasse_for_age(player.age)
                })
            
            # Check for age class violations
            for team in player.teams:
                if team.league and team.league.altersklasse:
                    if not is_player_allowed_in_team(player.age, team.league.altersklasse):
                        all_violations.append({
                            'club': club.name,
                            'player': player.name,
                            'age': player.age,
                            'min_class': get_minimum_altersklasse_for_age(player.age),
                            'team': team.name,
                            'team_class': normalize_altersklasse(team.league.altersklasse)
                        })
    
    # Report results
    print(f"\nChecked {clubs_checked} clubs")
    
    print("\n" + "="*80)
    print("AGE CLASS VIOLATIONS")
    print("="*80)
    
    if all_violations:
        print(f"\n⚠️  Found {len(all_violations)} age class violations:\n")

        # Group by club
        violations_by_club = defaultdict(list)
        for v in all_violations:
            violations_by_club[v['club']].append(v)
        
        for club_name, violations in sorted(violations_by_club.items()):
            print(f"{club_name}: {len(violations)} violations")
            for v in violations[:3]:  # Show first 3
                print(f"  - {v['player']} (Age {v['age']}, Min: {v['min_class']}) in {v['team']} ({v['team_class']})")
            if len(violations) > 3:
                print(f"  ... and {len(violations) - 3} more")
    else:
        print("\n✓ No age class violations found!")
    
    print("\n" + "="*80)
    print("UNASSIGNED PLAYERS")
    print("="*80)
    
    if all_unassigned:
        print(f"\n⚠️  Found {len(all_unassigned)} unassigned players:\n")
        
        # Group by club
        unassigned_by_club = defaultdict(list)
        for u in all_unassigned:
            unassigned_by_club[u['club']].append(u)
        
        for club_name, unassigned in sorted(unassigned_by_club.items()):
            print(f"{club_name}: {len(unassigned)} unassigned")
            for u in unassigned[:3]:  # Show first 3
                print(f"  - {u['player']} (Age {u['age']}, Min class: {u['min_class']})")
            if len(unassigned) > 3:
                print(f"  ... and {len(unassigned) - 3} more")
    else:
        print("\n✓ All players are assigned to teams!")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Clubs checked:        {clubs_checked}")
    print(f"Age class violations: {len(all_violations)}")
    print(f"Unassigned players:   {len(all_unassigned)}")
    
    if all_violations or all_unassigned:
        print("\n⚠️  Issues found! Run 'python fix_age_class_violations.py' to fix them.")
    else:
        print("\n✓ All checks passed!")

