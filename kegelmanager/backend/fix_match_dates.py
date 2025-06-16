#!/usr/bin/env python3
"""
Script to fix match dates by creating season calendar and updating match dates.
This script should be run when match dates show incorrect values like "07.06." or "Invalid Date".
"""

from app import app
from models import db, Match, CupMatch, SeasonCalendar, Season
from season_calendar import create_season_calendar
from datetime import datetime


def fix_match_dates():
    """Fix match dates by creating season calendar and updating all matches."""
    with app.app_context():
        print("=== FIXING MATCH DATES ===")
        
        # 1. Check if season calendar exists
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("ERROR: No current season found!")
            return False
        
        print(f"Current season: {current_season.id} - {current_season.name}")
        
        # 2. Check if calendar exists
        calendar_count = SeasonCalendar.query.filter_by(season_id=current_season.id).count()
        print(f"Calendar entries for current season: {calendar_count}")
        
        if calendar_count == 0:
            print("Creating season calendar...")
            try:
                create_season_calendar(current_season.id)
                print("✅ Season calendar created successfully!")
            except Exception as e:
                print(f"❌ Error creating season calendar: {e}")
                return False
        else:
            print("✅ Season calendar already exists")
        
        # 3. Update league match dates
        print("\nUpdating league match dates...")
        matches = Match.query.filter_by(season_id=current_season.id).all()
        updated_league_matches = 0
        
        for match in matches:
            if match.match_day:
                # Find corresponding calendar entry
                calendar_day = SeasonCalendar.query.filter_by(
                    season_id=match.season_id,
                    match_day_number=match.match_day,
                    day_type='LEAGUE_DAY'
                ).first()
                
                if calendar_day:
                    # Set correct date
                    new_date = datetime.combine(
                        calendar_day.calendar_date, 
                        datetime.min.time().replace(hour=15)
                    )
                    match.match_date = new_date
                    updated_league_matches += 1
        
        # 4. Update cup match dates
        print("Updating cup match dates...")
        cup_matches = CupMatch.query.join(CupMatch.cup).filter_by(season_id=current_season.id).all()
        updated_cup_matches = 0
        
        for cup_match in cup_matches:
            if cup_match.cup_match_day:
                # Find corresponding calendar entry
                calendar_day = SeasonCalendar.query.filter_by(
                    season_id=cup_match.cup.season_id,
                    match_day_number=cup_match.cup_match_day,
                    day_type='CUP_DAY'
                ).first()
                
                if calendar_day:
                    cup_match.match_date = calendar_day.calendar_date
                    updated_cup_matches += 1
        
        # 5. Save changes
        try:
            db.session.commit()
            print(f"✅ Updated {updated_league_matches} league matches")
            print(f"✅ Updated {updated_cup_matches} cup matches")
            print("✅ All changes saved successfully!")
            
            # 6. Verify results
            print("\nVerification:")
            sample_matches = Match.query.filter_by(season_id=current_season.id).limit(3).all()
            for match in sample_matches:
                print(f"  Match {match.id}: match_day={match.match_day}, date={match.match_date}")
            
            sample_cup_matches = CupMatch.query.join(CupMatch.cup).filter_by(season_id=current_season.id).limit(3).all()
            for cup_match in sample_cup_matches:
                print(f"  CupMatch {cup_match.id}: cup_match_day={cup_match.cup_match_day}, date={cup_match.match_date}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving changes: {e}")
            db.session.rollback()
            return False


if __name__ == "__main__":
    success = fix_match_dates()
    if success:
        print("\n🎉 Match dates fixed successfully!")
    else:
        print("\n💥 Failed to fix match dates!")
