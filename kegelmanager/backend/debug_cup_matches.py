#!/usr/bin/env python3
"""
Debug script to analyze cup matches and their dates.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Season, CupMatch, Cup, Team
from datetime import date
from simulation import get_cup_matches_for_date

def debug_cup_matches():
    """Debug cup matches and their dates."""
    
    with app.app_context():
        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("No current season found")
            return
        
        print(f"Debugging cup matches for season: {current_season.name}")
        print()
        
        # Check the target date (13.08.2025)
        target_date = date(2025, 8, 13)
        print(f"Target date: {target_date}")
        print()
        
        # Get all cup matches for this season
        all_cup_matches = db.session.query(
            CupMatch.id,
            CupMatch.match_date,
            CupMatch.cup_match_day,
            CupMatch.is_played,
            CupMatch.round_name,
            Cup.name.label('cup_name'),
            Team.name.label('home_team_name')
        ).join(Cup).join(Team, CupMatch.home_team_id == Team.id).filter(
            Cup.season_id == current_season.id
        ).order_by(CupMatch.match_date, CupMatch.cup_match_day).all()
        
        print(f"Total cup matches in season: {len(all_cup_matches)}")
        print()
        
        # Analyze match dates
        matches_with_date = 0
        matches_without_date = 0
        matches_on_target_date = 0
        played_matches = 0
        unplayed_matches = 0
        
        print("=== ALL CUP MATCHES ===")
        for match in all_cup_matches:
            if match.is_played:
                played_matches += 1
                status = "PLAYED"
            else:
                unplayed_matches += 1
                status = "UNPLAYED"
            
            if match.match_date:
                matches_with_date += 1
                if match.match_date == target_date:
                    matches_on_target_date += 1
                    print(f"🎯 MATCH ON TARGET DATE: {match.id} - {match.cup_name} {match.round_name} - {match.home_team_name} - Date: {match.match_date} - Cup Day: {match.cup_match_day} - {status}")
                else:
                    print(f"   Match {match.id} - {match.cup_name} {match.round_name} - {match.home_team_name} - Date: {match.match_date} - Cup Day: {match.cup_match_day} - {status}")
            else:
                matches_without_date += 1
                print(f"❌ NO DATE: {match.id} - {match.cup_name} {match.round_name} - {match.home_team_name} - Date: None - Cup Day: {match.cup_match_day} - {status}")
        
        print()
        print("=== SUMMARY ===")
        print(f"Total matches: {len(all_cup_matches)}")
        print(f"Played matches: {played_matches}")
        print(f"Unplayed matches: {unplayed_matches}")
        print(f"Matches with date: {matches_with_date}")
        print(f"Matches without date: {matches_without_date}")
        print(f"Matches on target date ({target_date}): {matches_on_target_date}")
        print()
        
        # Test the get_cup_matches_for_date function
        print("=== TESTING get_cup_matches_for_date FUNCTION ===")
        cup_matches_found = get_cup_matches_for_date(current_season.id, target_date)
        print(f"get_cup_matches_for_date found {len(cup_matches_found)} matches for {target_date}")
        
        for i, match_data in enumerate(cup_matches_found):
            print(f"  {i+1}. Match ID: {match_data.get('match_id')} - {match_data.get('cup_name')} - {match_data.get('home_team_name')} vs {match_data.get('away_team_name')} - Cup Day: {match_data.get('cup_match_day')}")
        
        print()
        
        # Check if there are matches without dates that should be on this date
        print("=== CHECKING UNPLAYED MATCHES WITHOUT DATES ===")
        unplayed_no_date = db.session.query(
            CupMatch.id,
            CupMatch.cup_match_day,
            CupMatch.round_name,
            Cup.name.label('cup_name'),
            Team.name.label('home_team_name')
        ).join(Cup).join(Team, CupMatch.home_team_id == Team.id).filter(
            Cup.season_id == current_season.id,
            CupMatch.is_played == False,
            CupMatch.match_date.is_(None)
        ).all()
        
        print(f"Unplayed matches without dates: {len(unplayed_no_date)}")
        for match in unplayed_no_date:
            print(f"  Match {match.id} - {match.cup_name} {match.round_name} - {match.home_team_name} - Cup Day: {match.cup_match_day}")


if __name__ == "__main__":
    debug_cup_matches()
