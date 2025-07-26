#!/usr/bin/env python3
"""
Test script to check player availability in cup matches.
This script will analyze if the player availability issue in cup matches has been resolved.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Season, Cup, CupMatch, Team, Player, SeasonCalendar
from simulation import simulate_match_day
from season_calendar import validate_no_date_conflicts
from sqlalchemy import func
from datetime import datetime, date

def test_cup_player_availability():
    """Test player availability in cup matches."""
    with app.app_context():
        print("=== TESTING CUP PLAYER AVAILABILITY ===\n")
        
        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("No current season found")
            return
        
        print(f"Testing season: {current_season.name}")
        
        # Check for date conflicts first
        print("\n1. Checking for date conflicts between league and cup matches...")
        no_conflicts = validate_no_date_conflicts(current_season.id)
        if not no_conflicts:
            print("⚠️  Date conflicts detected! This could cause player availability issues.")
        else:
            print("✅ No date conflicts found.")
        
        # Find next cup day
        print("\n2. Finding next cup day...")
        next_cup_day = SeasonCalendar.query.filter_by(
            season_id=current_season.id,
            day_type='CUP_DAY',
            is_simulated=False
        ).order_by(SeasonCalendar.calendar_date).first()
        
        if not next_cup_day:
            print("No unsimulated cup days found")
            return
        
        print(f"Next cup day: {next_cup_day.calendar_date} (Match day {next_cup_day.match_day_number})")
        
        # Check cup matches for this day
        cup_matches = db.session.query(CupMatch).join(Cup).filter(
            Cup.season_id == current_season.id,
            CupMatch.is_played == False,
            func.date(CupMatch.match_date) == next_cup_day.calendar_date
        ).all()
        
        print(f"Found {len(cup_matches)} cup matches for this day")
        
        if not cup_matches:
            print("No cup matches found for the next cup day")
            return
        
        # Analyze player availability before simulation
        print("\n3. Analyzing player availability before simulation...")
        clubs_analyzed = set()
        
        for cup_match in cup_matches[:3]:  # Analyze first 3 matches
            home_team = cup_match.home_team
            away_team = cup_match.away_team
            
            if not away_team:  # Skip bye matches
                continue
                
            print(f"\nMatch: {home_team.name} vs {away_team.name}")
            
            for team in [home_team, away_team]:
                if team.club_id in clubs_analyzed:
                    continue
                clubs_analyzed.add(team.club_id)
                
                # Get all players from this club
                all_players = Player.query.filter_by(club_id=team.club_id).all()
                available_players = [p for p in all_players if p.is_available_current_matchday]
                
                print(f"  {team.name} (Club {team.club_id}): {len(available_players)}/{len(all_players)} players available")
                
                if len(available_players) < 6:
                    stroh_needed = 6 - len(available_players)
                    print(f"    ⚠️  Will need {stroh_needed} Stroh player(s)")
                else:
                    print(f"    ✅ Enough players available")
        
        # Test the simulation
        print("\n4. Testing simulation with fixed logic...")
        try:
            result = simulate_match_day(current_season)
            print(f"✅ Simulation completed successfully!")
            print(f"   Matches simulated: {result.get('matches_simulated', 0)}")
            print(f"   Day type: {result.get('day_type', 'Unknown')}")
            print(f"   Match day: {result.get('match_day', 'Unknown')}")
            
            # Check if any matches were actually simulated
            if result.get('matches_simulated', 0) > 0:
                print("   ✅ Cup matches were successfully simulated")
            else:
                print("   ⚠️  No matches were simulated")
                
        except Exception as e:
            print(f"❌ Simulation failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_cup_player_availability()
