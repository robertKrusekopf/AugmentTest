#!/usr/bin/env python3
"""
Debug script to check for conflicts between league and cup matches on the same day.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Season, CupMatch, Cup, Team, Player, SeasonCalendar, Match
from datetime import date
from simulation import get_cup_matches_for_date, get_league_matches_for_date

def debug_match_conflicts():
    """Debug conflicts between league and cup matches."""
    
    with app.app_context():
        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("No current season found")
            return
        
        print(f"Debugging match conflicts for season: {current_season.name}")
        print()
        
        # Find a cup day with matches
        calendar_days = SeasonCalendar.query.filter_by(
            season_id=current_season.id,
            day_type='CUP_DAY'
        ).order_by(SeasonCalendar.id).all()
        
        if not calendar_days:
            print("No CUP_DAY entries found in calendar")
            return
        
        # Try to find a cup day with actual matches
        next_calendar_day = None
        target_date = None
        cup_matches_data = []

        for calendar_day in calendar_days:
            target_date = calendar_day.calendar_date
            cup_matches_data = get_cup_matches_for_date(current_season.id, target_date)
            if cup_matches_data:
                next_calendar_day = calendar_day
                break

        if not next_calendar_day or not cup_matches_data:
            print("No calendar days with cup matches found")
            return
        
        print(f"Found cup day: {target_date} (CUP_DAY)")
        print(f"Match day number: {next_calendar_day.match_day_number}")
        print(f"Found {len(cup_matches_data)} cup matches for date {target_date}")
        print()
        
        # Check for league matches on the same date
        league_matches_data = get_league_matches_for_date(current_season.id, target_date)
        print(f"Found {len(league_matches_data)} league matches for the same date {target_date}")
        
        if league_matches_data:
            print("WARNING: League and cup matches on the same date!")
            print("League matches:")
            for match_data in league_matches_data[:5]:  # Show first 5
                print(f"  - Match {match_data['match_id']}: {match_data['home_team_name']} vs {match_data['away_team_name']}")
        print()
        
        # Check for league matches on the same match_day_number
        league_matches_same_day = db.session.query(
            Match.id,
            Match.match_day,
            Team.name.label('home_team_name')
        ).join(
            Team, Match.home_team_id == Team.id
        ).filter(
            Match.season_id == current_season.id,
            Match.match_day == next_calendar_day.match_day_number,
            Match.is_played == False
        ).all()
        
        print(f"Found {len(league_matches_same_day)} league matches with match_day = {next_calendar_day.match_day_number}")
        if league_matches_same_day:
            print("WARNING: League and cup matches with same match_day number!")
            print("League matches with same match_day:")
            for match_data in league_matches_same_day[:5]:  # Show first 5
                print(f"  - Match {match_data.id}: {match_data.home_team_name} (match_day: {match_data.match_day})")
        print()
        
        # Check player flags for a specific club
        print("=== PLAYER FLAG ANALYSIS ===")
        # Get a club that has cup matches
        sample_club_id = cup_matches_data[0]['home_club_id']
        print(f"Analyzing club {sample_club_id}")
        
        all_players = Player.query.filter_by(club_id=sample_club_id).all()
        print(f"Total players in club: {len(all_players)}")
        
        available_count = 0
        unavailable_count = 0
        played_count = 0
        
        for player in all_players:
            if player.has_played_current_matchday:
                played_count += 1
                print(f"  - {player.name}: has_played=True, last_played_matchday={player.last_played_matchday}")
            elif not player.is_available_current_matchday:
                unavailable_count += 1
            else:
                available_count += 1
        
        print(f"Available: {available_count}")
        print(f"Unavailable: {unavailable_count}")
        print(f"Already played: {played_count}")
        print()
        
        # Check what the current match day is set to
        print("=== CURRENT MATCH DAY ANALYSIS ===")
        print(f"Calendar match_day_number: {next_calendar_day.match_day_number}")
        
        # Check if there are any recent league matches that were played
        recent_league_matches = db.session.query(
            Match.id,
            Match.match_day,
            Match.match_date,
            Match.is_played,
            Team.name.label('home_team_name')
        ).join(
            Team, Match.home_team_id == Team.id
        ).filter(
            Match.season_id == current_season.id,
            Match.is_played == True
        ).order_by(Match.match_day.desc()).limit(10).all()
        
        print("Recent played league matches:")
        for match in recent_league_matches:
            print(f"  - Match {match.id}: {match.home_team_name} (match_day: {match.match_day}, date: {match.match_date}, played: {match.is_played})")

if __name__ == "__main__":
    debug_match_conflicts()
