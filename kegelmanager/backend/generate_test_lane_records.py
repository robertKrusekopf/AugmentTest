#!/usr/bin/env python3
"""
Test script to generate multiple historical lane records for testing the frontend display.
"""

from app import app
from models import LaneRecord, Player, Team, Club, db
from datetime import datetime, timedelta
import random

def generate_test_lane_records():
    """Generate multiple historical lane records for testing."""
    
    with app.app_context():
        print("Generating test historical lane records...")
        
        # Get a test club
        test_club = Club.query.first()
        if not test_club:
            print("No clubs found!")
            return
        
        print(f"Generating records for club: {test_club.name} (ID: {test_club.id})")
        
        # Get some players and teams from this club
        players = Player.query.filter_by(club_id=test_club.id).limit(5).all()
        teams = Team.query.filter_by(club_id=test_club.id).limit(2).all()
        
        if not players or not teams:
            print("No players or teams found for this club!")
            return
        
        # Generate historical individual records (Herren category)
        print("Generating individual records...")
        base_date = datetime.now() - timedelta(days=365)  # Start a year ago
        
        individual_scores = [650, 680, 700, 720, 740, 760, 780]  # Increasing scores over time
        
        for i, score in enumerate(individual_scores):
            player = random.choice(players)
            record_date = base_date + timedelta(days=i * 50)  # Records every ~50 days
            
            # Create historical record
            record = LaneRecord(
                record_type='individual',
                category='Herren',
                club_id=test_club.id,
                player_id=player.id,
                score=score,
                match_id=None,  # Historical records might not have match_id
                record_date=record_date
            )
            db.session.add(record)
            print(f"  Added individual record: {player.name} - {score} pins ({record_date.strftime('%Y-%m-%d')})")
        
        # Generate historical team records
        print("Generating team records...")
        team_scores = [3400, 3500, 3600, 3700, 3800, 3900, 4000]  # Increasing scores over time
        
        for i, score in enumerate(team_scores):
            team = random.choice(teams)
            record_date = base_date + timedelta(days=i * 45)  # Records every ~45 days
            
            # Create historical record
            record = LaneRecord(
                record_type='team',
                category='Herren',
                club_id=test_club.id,
                team_id=team.id,
                score=score,
                match_id=None,  # Historical records might not have match_id
                record_date=record_date
            )
            db.session.add(record)
            print(f"  Added team record: {team.name} - {score} pins ({record_date.strftime('%Y-%m-%d')})")
        
        # Generate some U19 records
        print("Generating U19 records...")
        u19_scores = [500, 520, 540, 560, 580]  # Lower scores for U19
        
        for i, score in enumerate(u19_scores):
            player = random.choice(players)
            record_date = base_date + timedelta(days=i * 60)  # Records every ~60 days
            
            # Create historical record
            record = LaneRecord(
                record_type='individual',
                category='U19',
                club_id=test_club.id,
                player_id=player.id,
                score=score,
                match_id=None,
                record_date=record_date
            )
            db.session.add(record)
            print(f"  Added U19 record: {player.name} - {score} pins ({record_date.strftime('%Y-%m-%d')})")
        
        # Commit all records
        db.session.commit()
        print(f"\nGenerated {len(individual_scores) + len(team_scores) + len(u19_scores)} historical lane records!")
        
        # Show the final count
        total_records = LaneRecord.query.filter_by(club_id=test_club.id).count()
        print(f"Total lane records for {test_club.name}: {total_records}")
        
        # Show records by type
        individual_count = LaneRecord.query.filter_by(club_id=test_club.id, record_type='individual', category='Herren').count()
        team_count = LaneRecord.query.filter_by(club_id=test_club.id, record_type='team').count()
        u19_count = LaneRecord.query.filter_by(club_id=test_club.id, record_type='individual', category='U19').count()
        
        print(f"  Individual (Herren): {individual_count}")
        print(f"  Team: {team_count}")
        print(f"  U19: {u19_count}")

if __name__ == "__main__":
    generate_test_lane_records()
