#!/usr/bin/env python3
"""
Check the status of cup matches and calendar days.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Season, Cup, CupMatch, Team, Player, SeasonCalendar
from sqlalchemy import func
from datetime import datetime, date

def check_cup_status():
    """Check the status of cups and matches."""
    with app.app_context():
        print("=== CHECKING CUP STATUS ===\n")
        
        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("No current season found")
            return
        
        print(f"Season: {current_season.name}")
        
        # Check calendar days
        print("\n1. Calendar Days Status:")
        total_days = SeasonCalendar.query.filter_by(season_id=current_season.id).count()
        league_days = SeasonCalendar.query.filter_by(season_id=current_season.id, day_type='LEAGUE_DAY').count()
        cup_days = SeasonCalendar.query.filter_by(season_id=current_season.id, day_type='CUP_DAY').count()
        free_days = SeasonCalendar.query.filter_by(season_id=current_season.id, day_type='FREE_DAY').count()
        
        simulated_league = SeasonCalendar.query.filter_by(season_id=current_season.id, day_type='LEAGUE_DAY', is_simulated=True).count()
        simulated_cup = SeasonCalendar.query.filter_by(season_id=current_season.id, day_type='CUP_DAY', is_simulated=True).count()
        
        print(f"   Total calendar days: {total_days}")
        print(f"   League days: {league_days} (simulated: {simulated_league})")
        print(f"   Cup days: {cup_days} (simulated: {simulated_cup})")
        print(f"   Free days: {free_days}")
        
        # Check cups
        print("\n2. Cups Status:")
        cups = Cup.query.filter_by(season_id=current_season.id).all()
        print(f"   Total cups: {len(cups)}")
        
        for cup in cups:
            total_matches = CupMatch.query.filter_by(cup_id=cup.id).count()
            played_matches = CupMatch.query.filter_by(cup_id=cup.id, is_played=True).count()
            print(f"   {cup.name} ({cup.cup_type}): {played_matches}/{total_matches} matches played, Active: {cup.is_active}")
        
        # Check unplayed cup matches
        print("\n3. Unplayed Cup Matches:")
        unplayed_matches = db.session.query(CupMatch).join(Cup).filter(
            Cup.season_id == current_season.id,
            CupMatch.is_played == False
        ).all()
        
        print(f"   Total unplayed cup matches: {len(unplayed_matches)}")
        
        if unplayed_matches:
            print("   First 5 unplayed matches:")
            for match in unplayed_matches[:5]:
                home_name = match.home_team.name if match.home_team else "BYE"
                away_name = match.away_team.name if match.away_team else "BYE"
                match_date = match.match_date.date() if match.match_date else "No date"
                print(f"     {match.cup.name}: {home_name} vs {away_name} on {match_date}")
        
        # Check next unsimulated day
        print("\n4. Next Unsimulated Day:")
        next_day = SeasonCalendar.query.filter_by(
            season_id=current_season.id,
            is_simulated=False
        ).order_by(SeasonCalendar.calendar_date).first()
        
        if next_day:
            print(f"   Next day: {next_day.calendar_date} ({next_day.day_type})")
            
            # Check matches for this day
            if next_day.day_type == 'CUP_DAY':
                matches_on_day = db.session.query(CupMatch).join(Cup).filter(
                    Cup.season_id == current_season.id,
                    CupMatch.is_played == False,
                    func.date(CupMatch.match_date) == next_day.calendar_date
                ).all()
                print(f"   Cup matches on this day: {len(matches_on_day)}")
                
                for match in matches_on_day[:3]:
                    home_name = match.home_team.name if match.home_team else "BYE"
                    away_name = match.away_team.name if match.away_team else "BYE"
                    print(f"     {match.cup.name}: {home_name} vs {away_name}")
        else:
            print("   No unsimulated days found - season completed!")
        
        print("\n=== STATUS CHECK COMPLETED ===")

if __name__ == "__main__":
    check_cup_status()
