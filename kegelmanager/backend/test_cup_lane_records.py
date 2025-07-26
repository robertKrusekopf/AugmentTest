#!/usr/bin/env python3
"""
Test script to verify that lane records are created during cup matches.
"""

from simulation import simulate_match_day
from models import Season, LaneRecord, SeasonCalendar, CupMatch, db
from app import app

def test_cup_lane_records():
    with app.app_context():
        # Get current season (should be Season 2026)
        season = Season.query.filter_by(is_current=True).first()
        if not season:
            print('No current season found')
            return
            
        print(f'Testing cup match lane records with season: {season.name}')
        
        # Count records before simulation
        records_before = LaneRecord.query.count()
        print(f'Lane records before simulation: {records_before}')
        
        # Simulate until we reach a cup day
        for i in range(10):
            result = simulate_match_day(season)
            matches_simulated = result.get('matches_simulated', 0)
            day_type = result.get('day_type', 'UNKNOWN')
            match_day = result.get('match_day', 0)
            
            print(f'Day {i+1} (match day {match_day}): {matches_simulated} matches, type: {day_type}')
            
            if day_type == 'CUP_DAY' and matches_simulated > 0:
                print('Successfully simulated cup matches!')
                break
            elif matches_simulated == 0:
                print('No more matches to simulate')
                break
        
        # Count records after simulation
        records_after = LaneRecord.query.count()
        print(f'Lane records after simulation: {records_after}')
        print(f'New records created: {records_after - records_before}')
        
        if records_after > records_before:
            # Check if any of the new records are from cup matches
            new_records = LaneRecord.query.order_by(LaneRecord.id.desc()).limit(10).all()
            cup_records_found = 0
            
            for record in new_records:
                if record.match_id:
                    cup_match = CupMatch.query.get(record.match_id)
                    if cup_match:
                        cup_records_found += 1
                        record_type = record.record_type
                        category = record.category
                        score = record.score
                        cup_name = cup_match.cup.name if cup_match.cup else 'Unknown Cup'
                        round_name = cup_match.round_name
                        print(f'  CUP RECORD: {record_type} {category} - {score} pins in {cup_name} {round_name}')
            
            print(f'Found {cup_records_found} cup match records out of {records_after - records_before} new records')
            
            if cup_records_found > 0:
                print('✅ Cup matches DO create lane records!')
                return True
            else:
                print('❌ Cup matches do NOT create lane records')
                return False
        else:
            print('No new records created')
            return False

if __name__ == '__main__':
    test_cup_lane_records()
