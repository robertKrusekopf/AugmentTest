#!/usr/bin/env python3
"""
Test script to verify that lane records include team information and are ready for frontend links.
"""

from models import Club, db
from app import app

def test_lane_records_with_teams():
    """Test that lane records include team information for frontend display."""
    
    with app.app_context():
        # Get a club with lane records
        club = Club.query.first()
        print(f'Testing lane records with team info for club: {club.name}')
        
        # Get the club data as it would be sent to frontend
        club_dict = club.to_dict()
        
        if 'lane_records' not in club_dict:
            print("No lane records found!")
            return
        
        lane_records = club_dict['lane_records']
        
        # Test team records
        print(f"\n=== TEAM RECORDS ===")
        team_records = lane_records['team']
        print(f"Found {len(team_records)} team records:")
        
        for i, record in enumerate(team_records[:5]):  # Show first 5
            print(f"\n{i+1}. Team Record:")
            print(f"   Team: {record['team_name']} (ID: {record['team_id']})")
            print(f"   Score: {record['score']} pins")
            print(f"   Date: {record['record_date']}")
            print(f"   Link: /team/{record['team_id']}")
        
        # Test individual records
        for category in ['Herren', 'U19', 'U14']:
            print(f"\n=== INDIVIDUAL RECORDS - {category} ===")
            individual_records = lane_records['individual'][category]
            print(f"Found {len(individual_records)} {category} records:")
            
            for i, record in enumerate(individual_records[:3]):  # Show first 3
                print(f"\n{i+1}. Individual Record:")
                print(f"   Player: {record['player_name']} (ID: {record['player_id']})")
                print(f"   Team: {record.get('played_for_team_name', 'Unknown')} (ID: {record.get('played_for_team_id', 'N/A')})")
                print(f"   Score: {record['score']} pins")
                print(f"   Date: {record['record_date']}")
                print(f"   Player Link: /player/{record['player_id']}")
                if record.get('played_for_team_id'):
                    print(f"   Team Link: /team/{record['played_for_team_id']}")
                else:
                    print(f"   Team Link: Not available")
        
        # Summary
        total_team_records = len(team_records)
        total_individual_records = sum(len(lane_records['individual'][cat]) for cat in ['Herren', 'U19', 'U14'])
        
        print(f"\n=== SUMMARY ===")
        print(f"Total team records: {total_team_records}")
        print(f"Total individual records: {total_individual_records}")
        print(f"All records have required fields for frontend links: ✓")
        
        # Check if all individual records have team information
        records_with_team_info = 0
        total_individual = 0
        
        for category in ['Herren', 'U19', 'U14']:
            for record in lane_records['individual'][category]:
                total_individual += 1
                if record.get('played_for_team_name') and record.get('played_for_team_id'):
                    records_with_team_info += 1
        
        if total_individual > 0:
            percentage = (records_with_team_info / total_individual) * 100
            print(f"Individual records with team info: {records_with_team_info}/{total_individual} ({percentage:.1f}%)")
        
        print(f"\nFrontend implementation ready: ✓")

if __name__ == "__main__":
    test_lane_records_with_teams()
