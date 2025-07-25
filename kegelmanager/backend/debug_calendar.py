#!/usr/bin/env python3
"""
Debug script to analyze season calendar and cup match day assignments.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Season, SeasonCalendar, CupMatch, Cup
from datetime import date

def debug_calendar():
    """Debug season calendar and cup match day assignments."""
    
    with app.app_context():
        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("No current season found")
            return
        
        print(f"Debugging calendar for season: {current_season.name}")
        print()
        
        # Get all calendar entries for this season
        calendar_entries = SeasonCalendar.query.filter_by(
            season_id=current_season.id
        ).order_by(SeasonCalendar.calendar_date).all()
        
        print(f"Total calendar entries: {len(calendar_entries)}")
        print()
        
        # Analyze calendar entries
        league_days = []
        cup_days = []
        free_days = []
        
        for entry in calendar_entries:
            if entry.day_type == 'LEAGUE_DAY':
                league_days.append(entry)
            elif entry.day_type == 'CUP_DAY':
                cup_days.append(entry)
            else:
                free_days.append(entry)
        
        print(f"League days: {len(league_days)}")
        print(f"Cup days: {len(cup_days)}")
        print(f"Free days: {len(free_days)}")
        print()
        
        # Show cup days in detail
        print("=== CUP DAYS IN CALENDAR ===")
        for entry in cup_days:
            print(f"Cup Day {entry.match_day_number}: {entry.calendar_date} ({entry.weekday})")
        
        print()
        
        # Check which cup matches are assigned to which cup days
        print("=== CUP MATCHES BY CUP DAY ===")
        cup_matches = db.session.query(
            CupMatch.cup_match_day,
            CupMatch.match_date,
            Cup.name.label('cup_name'),
            db.func.count(CupMatch.id).label('match_count')
        ).join(Cup).filter(
            Cup.season_id == current_season.id
        ).group_by(
            CupMatch.cup_match_day,
            CupMatch.match_date,
            Cup.name
        ).order_by(CupMatch.cup_match_day).all()
        
        for match_group in cup_matches:
            print(f"Cup Day {match_group.cup_match_day}: {match_group.match_count} matches from {match_group.cup_name} - Date: {match_group.match_date}")
        
        print()
        
        # Check the specific problem: matches on 2025-08-13
        target_date = date(2025, 8, 13)
        print(f"=== MATCHES ON {target_date} ===")
        
        # Find which calendar entry corresponds to this date
        calendar_entry = SeasonCalendar.query.filter_by(
            season_id=current_season.id,
            calendar_date=target_date
        ).first()
        
        if calendar_entry:
            print(f"Calendar entry for {target_date}:")
            print(f"  Day type: {calendar_entry.day_type}")
            print(f"  Match day number: {calendar_entry.match_day_number}")
            print(f"  Week number: {calendar_entry.week_number}")
            print(f"  Weekday: {calendar_entry.weekday}")
        else:
            print(f"No calendar entry found for {target_date}")
        
        print()
        
        # Check cup matches on this date
        matches_on_date = db.session.query(
            CupMatch.id,
            CupMatch.cup_match_day,
            CupMatch.match_date,
            Cup.name.label('cup_name'),
            Cup.cup_type
        ).join(Cup).filter(
            Cup.season_id == current_season.id,
            CupMatch.match_date == target_date
        ).order_by(CupMatch.cup_match_day).all()
        
        print(f"Cup matches on {target_date}:")
        cup_day_counts = {}
        for match in matches_on_date:
            cup_day = match.cup_match_day
            if cup_day not in cup_day_counts:
                cup_day_counts[cup_day] = []
            cup_day_counts[cup_day].append(match)
        
        for cup_day, matches in cup_day_counts.items():
            print(f"  Cup Day {cup_day}: {len(matches)} matches")
            for match in matches[:3]:  # Show first 3 matches
                print(f"    - {match.cup_name} (Match {match.id})")
            if len(matches) > 3:
                print(f"    ... and {len(matches) - 3} more")
        
        print()
        
        # Check if there's a mismatch between calendar and cup matches
        print("=== CHECKING FOR MISMATCHES ===")
        if calendar_entry and calendar_entry.day_type == 'CUP_DAY':
            expected_cup_day = calendar_entry.match_day_number
            print(f"Calendar says {target_date} should be Cup Day {expected_cup_day}")
            
            actual_cup_days = list(cup_day_counts.keys())
            print(f"But we found matches for Cup Days: {actual_cup_days}")
            
            if expected_cup_day not in actual_cup_days:
                print(f"❌ MISMATCH: Expected Cup Day {expected_cup_day} but found {actual_cup_days}")
            elif len(actual_cup_days) > 1:
                print(f"❌ PROBLEM: Multiple cup days on same date: {actual_cup_days}")
            else:
                print(f"✅ Match: Cup Day {expected_cup_day} matches calendar")
        else:
            print(f"❌ PROBLEM: {target_date} is not a CUP_DAY in calendar but has cup matches")


if __name__ == "__main__":
    debug_calendar()
