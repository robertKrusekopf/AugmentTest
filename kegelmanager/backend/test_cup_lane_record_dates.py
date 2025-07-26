#!/usr/bin/env python3
"""
Test script to verify that lane records from cup matches show correct dates.
"""

from models import LaneRecord, CupMatch, db
from app import app

def test_cup_lane_record_dates():
    """Test that lane records from cup matches show the correct match dates."""
    
    with app.app_context():
        print("Testing lane records from cup matches...")
        
        # Find lane records that might be from cup matches
        # (match_id that doesn't exist in Match table but exists in CupMatch table)
        all_records = LaneRecord.query.all()
        
        cup_records = []
        for record in all_records:
            if record.match_id and not record.match:
                # This might be a cup match
                cup_match = CupMatch.query.get(record.match_id)
                if cup_match:
                    cup_records.append((record, cup_match))
        
        print(f"Found {len(cup_records)} lane records from cup matches:")
        
        for record, cup_match in cup_records[:10]:  # Show first 10
            record_dict = record.to_dict()
            print(f"\nCup Record {record.id}:")
            print(f"  Score: {record.score}")
            print(f"  Cup: {cup_match.cup.name} - {cup_match.round_name}")
            print(f"  Match date: {cup_match.match_date}")
            print(f"  Display date: {record_dict['record_date']}")
            
            if record.record_type == 'individual' and record.player:
                print(f"  Player: {record.player.name}")
            elif record.record_type == 'team' and record.team:
                print(f"  Team: {record.team.name}")
        
        if not cup_records:
            print("No cup match lane records found. Let's simulate a cup match to create some...")
            
            # Get the current season and simulate a cup match day
            from models import Season
            from simulation import simulate_match_day
            
            season = Season.query.filter_by(is_current=True).first()
            if season:
                print(f"Simulating cup matches for season {season.name}...")
                
                # Count records before
                records_before = LaneRecord.query.count()
                
                # Simulate one match day (might include cup matches)
                simulate_match_day(season)
                
                # Count records after
                records_after = LaneRecord.query.count()
                new_records = records_after - records_before
                
                print(f"Created {new_records} new lane records")
                
                # Check for new cup records
                all_records = LaneRecord.query.all()
                new_cup_records = []
                for record in all_records:
                    if record.match_id and not record.match:
                        cup_match = CupMatch.query.get(record.match_id)
                        if cup_match:
                            new_cup_records.append((record, cup_match))
                
                print(f"Found {len(new_cup_records)} total cup match lane records after simulation")

if __name__ == "__main__":
    test_cup_lane_record_dates()
