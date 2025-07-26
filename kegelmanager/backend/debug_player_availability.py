#!/usr/bin/env python3
"""
Debug script to analyze player availability issues in cup matches.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Season, CupMatch, Cup, Team, Player, SeasonCalendar
from datetime import date
from simulation import get_cup_matches_for_date

def debug_player_availability():
    """Debug player availability for cup matches."""
    
    with app.app_context():
        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("No current season found")
            return
        
        print(f"Debugging player availability for season: {current_season.name}")
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
        
        print(f"Found calendar day: {target_date} (CUP_DAY)")
        print(f"Match day number: {next_calendar_day.match_day_number}")
        print(f"Found {len(cup_matches_data)} cup matches for date {target_date}")
        print()
        
        # Get clubs with matches
        clubs_with_matches = set()
        for cup_match_data in cup_matches_data:
            home_club_id = cup_match_data['home_club_id']
            away_club_id = cup_match_data['away_club_id']
            clubs_with_matches.add(home_club_id)
            if away_club_id:  # Skip bye matches
                clubs_with_matches.add(away_club_id)
        
        print(f"Clubs with matches: {len(clubs_with_matches)}")
        print()
        
        # Analyze player availability for each club
        for club_id in sorted(list(clubs_with_matches))[:5]:  # Check first 5 clubs
            print(f"=== CLUB {club_id} ===")
            
            # Get all players from this club
            all_players = Player.query.filter_by(club_id=club_id).all()
            available_players = Player.query.filter_by(
                club_id=club_id,
                is_available_current_matchday=True,
                has_played_current_matchday=False
            ).all()
            
            print(f"Total players: {len(all_players)}")
            print(f"Available players: {len(available_players)}")
            
            if len(available_players) < 6:
                print(f"WARNING: Only {len(available_players)} available players (need 6)")
                
                # Show availability details
                unavailable_count = 0
                played_count = 0
                for player in all_players:
                    if not player.is_available_current_matchday:
                        unavailable_count += 1
                    elif player.has_played_current_matchday:
                        played_count += 1
                
                print(f"  - Unavailable: {unavailable_count}")
                print(f"  - Already played: {played_count}")
                print(f"  - Available: {len(available_players)}")
            
            # Get teams from this club that have cup matches
            teams_with_cup_matches = []
            for cup_match_data in cup_matches_data:
                if cup_match_data['home_club_id'] == club_id:
                    team = Team.query.get(cup_match_data['home_team_id'])
                    if team and team not in teams_with_cup_matches:
                        teams_with_cup_matches.append(team)
                if cup_match_data['away_club_id'] == club_id:
                    team = Team.query.get(cup_match_data['away_team_id'])
                    if team and team not in teams_with_cup_matches:
                        teams_with_cup_matches.append(team)
            
            print(f"Teams with cup matches: {len(teams_with_cup_matches)}")
            for team in teams_with_cup_matches:
                print(f"  - {team.name} (ID: {team.id})")
            
            print()

if __name__ == "__main__":
    debug_player_availability()
