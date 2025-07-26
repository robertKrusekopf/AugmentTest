#!/usr/bin/env python3
"""
Test script to verify that lane records show the correct match dates.
"""

from models import LaneRecord, Club, CupMatch, db
from app import app

def test_lane_record_dates():
    """Test that lane records show match dates instead of record dates."""
    
    with app.app_context():
        # Get a club with lane records
        club = Club.query.first()
        print(f'Testing lane records for club: {club.name}')
        
        # Get some lane records
        records = LaneRecord.query.filter_by(club_id=club.id).limit(10).all()
        
        print(f'Found {len(records)} lane records for this club:')
        
        for record in records:
            record_dict = record.to_dict()
            print(f'\nRecord {record.id}:')
            print(f'  Score: {record.score}')
            print(f'  Record date (when saved): {record.record_date}')
            print(f'  Display date (from to_dict): {record_dict["record_date"]}')
            print(f'  Match ID: {record.match_id}')
            
            # Check if match exists
            if record.match:
                print(f'  -> League match found: {record.match.match_date}')
            elif record.match_id:
                cup_match = CupMatch.query.get(record.match_id)
                if cup_match:
                    print(f'  -> Cup match found: {cup_match.match_date}')
                else:
                    print(f'  -> No match found for match_id {record.match_id}')
            else:
                print(f'  -> No match_id set (historical record)')
        
        # Test the Club.to_dict() method
        print(f'\n\nTesting Club.to_dict() method...')
        club_dict = club.to_dict()
        
        if 'lane_records' in club_dict:
            team_records = club_dict['lane_records']['team']
            print(f'Team records: {len(team_records)}')
            for record in team_records[:3]:  # Show first 3
                print(f'  {record["team_name"]} - {record["score"]} pins - {record["record_date"]}')
            
            individual_records = club_dict['lane_records']['individual']['Herren']
            print(f'Individual (Herren) records: {len(individual_records)}')
            for record in individual_records[:3]:  # Show first 3
                team_info = record.get('played_for_team_name', 'Unknown')
                print(f'  {record["player_name"]} ({team_info}) - {record["score"]} pins - {record["record_date"]}')

if __name__ == "__main__":
    test_lane_record_dates()
