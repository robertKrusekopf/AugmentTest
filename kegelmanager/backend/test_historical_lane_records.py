#!/usr/bin/env python3
"""
Test script to verify that historical lane records are properly preserved.
"""

from app import app
from models import LaneRecord, Player, Team, Club, db
from simulation import simulate_match_day

def test_historical_lane_records():
    """Test that lane records preserve history instead of overwriting."""
    
    with app.app_context():
        print("Testing historical lane records preservation...")
        
        # Get current season
        from models import Season
        season = Season.query.filter_by(is_current=True).first()
        if not season:
            print("No active season found!")
            return
        
        print(f"Testing with season: {season.name}")
        
        # Count lane records before simulation
        records_before = LaneRecord.query.count()
        print(f"Lane records before simulation: {records_before}")
        
        # Get a specific club to monitor
        test_club = Club.query.first()
        if not test_club:
            print("No clubs found!")
            return
        
        print(f"Monitoring club: {test_club.name} (ID: {test_club.id})")
        
        # Get current records for this club
        club_records_before = LaneRecord.query.filter_by(club_id=test_club.id).count()
        print(f"Club {test_club.name} records before: {club_records_before}")
        
        # Show current records for this club
        current_records = LaneRecord.query.filter_by(club_id=test_club.id).order_by(LaneRecord.record_date.desc()).all()
        print(f"\nCurrent records for club {test_club.name}:")
        for record in current_records[:5]:  # Show top 5
            record_holder = record.player.name if record.player else record.team.name
            print(f"  {record.record_type} {record.category}: {record_holder} - {record.score} pins ({record.record_date.strftime('%Y-%m-%d')})")
        
        # Simulate one match day
        print(f"\nSimulating one match day...")
        simulate_match_day(season)
        
        # Count lane records after simulation
        records_after = LaneRecord.query.count()
        print(f"Lane records after simulation: {records_after}")
        print(f"New records created: {records_after - records_before}")
        
        # Get updated records for this club
        club_records_after = LaneRecord.query.filter_by(club_id=test_club.id).count()
        print(f"Club {test_club.name} records after: {club_records_after}")
        print(f"New records for this club: {club_records_after - club_records_before}")
        
        # Show updated records for this club
        updated_records = LaneRecord.query.filter_by(club_id=test_club.id).order_by(LaneRecord.record_date.desc()).all()
        print(f"\nUpdated records for club {test_club.name} (chronological order):")
        for i, record in enumerate(updated_records[:10]):  # Show top 10
            record_holder = record.player.name if record.player else record.team.name
            status = "NEW" if i < (club_records_after - club_records_before) else "OLD"
            print(f"  [{status}] {record.record_type} {record.category}: {record_holder} - {record.score} pins ({record.record_date.strftime('%Y-%m-%d %H:%M')})")
        
        # Test the Club.to_dict() method to see if it returns all records
        print(f"\nTesting Club.to_dict() method for historical records...")
        club_dict = test_club.to_dict()
        
        if 'lane_records' in club_dict:
            team_records = club_dict['lane_records']['team']
            individual_records = club_dict['lane_records']['individual']
            
            print(f"Team records returned: {len(team_records)}")
            for record in team_records[:3]:  # Show top 3
                print(f"  {record['team_name']} - {record['score']} pins ({record['record_date']})")
            
            for category in ['Herren', 'U19', 'U14']:
                if category in individual_records:
                    records = individual_records[category]
                    print(f"{category} individual records returned: {len(records)}")
                    for record in records[:3]:  # Show top 3
                        print(f"  {record['player_name']} - {record['score']} pins ({record['record_date']})")
        
        print("\nHistorical lane records test completed!")

if __name__ == "__main__":
    test_historical_lane_records()
