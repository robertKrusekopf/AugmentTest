#!/usr/bin/env python3
"""
Debug script to see what happens during match day simulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app directly
import app
from models import db, Season, Match, Cup, CupMatch, Team
from sqlalchemy import func
from datetime import datetime, date
from collections import defaultdict


def debug_simulation():
    """Debug what happens during match day simulation."""
    flask_app = app.app
    
    with flask_app.app_context():
        print("=== DEBUGGING SIMULATION ===")
        print()
        
        # Find current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("❌ No current season found")
            return
            
        print(f"Debugging season: {current_season.name} (ID: {current_season.id})")
        print()
        
        # Record current state of some played matches
        print("=== RECORDING CURRENT STATE ===")
        
        played_league_matches = Match.query.filter_by(
            season_id=current_season.id,
            is_played=True
        ).limit(5).all()
        
        print(f"Found {len(played_league_matches)} played league matches (showing first 5)")
        
        # Record original dates
        original_dates = {}
        for match in played_league_matches:
            original_dates[match.id] = match.match_date
            home_team = match.home_team.name if match.home_team else "Unknown"
            away_team = match.away_team.name if match.away_team else "Unknown"
            print(f"Match {match.id}: {home_team} vs {away_team} - {match.match_date} (Day {match.match_day})")
        
        print()
        
        # Check for multiple games per day BEFORE simulation
        print("=== CHECKING FOR CONFLICTS BEFORE SIMULATION ===")
        
        team_games_by_date = defaultdict(lambda: defaultdict(list))
        
        # Check league matches
        league_matches = db.session.query(
            Match.home_team_id,
            Match.away_team_id,
            func.date(Match.match_date).label('match_date'),
            Match.is_played,
            Match.id
        ).filter(
            Match.season_id == current_season.id,
            Match.match_date.isnot(None)
        ).all()
        
        for match in league_matches:
            match_date = match.match_date
            team_games_by_date[match.home_team_id][match_date].append(f'league_{match.id}')
            team_games_by_date[match.away_team_id][match_date].append(f'league_{match.id}')
        
        conflicts_before = 0
        for team_id, dates_dict in team_games_by_date.items():
            for match_date, games in dates_dict.items():
                if len(games) > 1:
                    conflicts_before += 1
        
        print(f"Conflicts before simulation: {conflicts_before}")
        
        # Now simulate one match day
        print("=== SIMULATING ONE MATCH DAY ===")
        
        try:
            from simulation import simulate_match_day
            result = simulate_match_day(current_season)
            print(f"Simulation result: {result.get('matches_simulated', 0)} matches simulated")
        except Exception as e:
            print(f"❌ Error during simulation: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print()
        
        # Check if played matches still have their original dates
        print("=== CHECKING PLAYED MATCHES AFTER SIMULATION ===")
        
        dates_changed = 0
        for match in played_league_matches:
            db.session.refresh(match)  # Reload from database
            original_date = original_dates[match.id]
            current_date = match.match_date
            
            if original_date != current_date:
                print(f"❌ Match {match.id} date CHANGED: {original_date} -> {current_date}")
                dates_changed += 1
            else:
                print(f"✅ Match {match.id} date preserved: {current_date}")
        
        print(f"Dates changed: {dates_changed}")
        print()
        
        # Check for conflicts AFTER simulation
        print("=== CHECKING FOR CONFLICTS AFTER SIMULATION ===")
        
        team_games_by_date_after = defaultdict(lambda: defaultdict(list))
        
        # Re-check league matches
        league_matches_after = db.session.query(
            Match.home_team_id,
            Match.away_team_id,
            func.date(Match.match_date).label('match_date'),
            Match.is_played,
            Match.id
        ).filter(
            Match.season_id == current_season.id,
            Match.match_date.isnot(None)
        ).all()
        
        for match in league_matches_after:
            match_date = match.match_date
            team_games_by_date_after[match.home_team_id][match_date].append(f'league_{match.id}')
            team_games_by_date_after[match.away_team_id][match_date].append(f'league_{match.id}')
        
        conflicts_after = 0
        for team_id, dates_dict in team_games_by_date_after.items():
            for match_date, games in dates_dict.items():
                if len(games) > 1:
                    conflicts_after += 1
                    if conflicts_after <= 3:  # Show first 3 conflicts
                        team = Team.query.get(team_id)
                        team_name = team.name if team else f"Team {team_id}"
                        print(f"❌ CONFLICT: {team_name} has {len(games)} games on {match_date}")
        
        print(f"Conflicts after simulation: {conflicts_after}")
        
        # Summary
        print()
        print("=== SUMMARY ===")
        print(f"Conflicts before: {conflicts_before}")
        print(f"Conflicts after: {conflicts_after}")
        print(f"Dates changed: {dates_changed}")
        
        if conflicts_after > conflicts_before:
            print("❌ NEW CONFLICTS CREATED during simulation!")
        elif dates_changed > 0:
            print("❌ PLAYED MATCH DATES CHANGED during simulation!")
        else:
            print("✅ No new problems created during simulation")


if __name__ == "__main__":
    debug_simulation()
