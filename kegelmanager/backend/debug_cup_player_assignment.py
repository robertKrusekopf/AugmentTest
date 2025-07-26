#!/usr/bin/env python3
"""
Debug script to analyze cup player assignment issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Season, CupMatch, Cup, Team, Player, SeasonCalendar
from datetime import date
from simulation import get_cup_matches_for_date
from club_player_assignment import batch_assign_players_to_teams
from performance_optimizations import CacheManager

def debug_cup_player_assignment():
    """Debug cup player assignment issues."""
    
    with app.app_context():
        # Get current season
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print("No current season found")
            return
        
        print(f"Debugging cup player assignment for season: {current_season.name}")
        print()
        
        # Find a calendar day with cup matches
        calendar_days = SeasonCalendar.query.filter_by(
            season_id=current_season.id,
            day_type='CUP_DAY'
        ).order_by(SeasonCalendar.id).all()

        if not calendar_days:
            print("No cup days found in calendar")
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
            # Show all cup matches regardless of date
            from models import CupMatch, Cup

            # Check if cups exist
            all_cups = Cup.query.filter_by(season_id=current_season.id).all()
            print(f"Total cups in season: {len(all_cups)}")
            for cup in all_cups:
                print(f"  - {cup.name} ({cup.cup_type}): Active={cup.is_active}, Current Round={cup.current_round}")

            all_cup_matches = CupMatch.query.join(Cup).filter(
                Cup.season_id == current_season.id
            ).all()
            print(f"Total cup matches in season: {len(all_cup_matches)}")

            unplayed_cup_matches = CupMatch.query.join(Cup).filter(
                Cup.season_id == current_season.id,
                CupMatch.is_played == False
            ).all()
            print(f"Total unplayed cup matches in season: {len(unplayed_cup_matches)}")

            # Since all matches are played, let's analyze some played matches
            played_cup_matches = CupMatch.query.join(Cup).filter(
                Cup.season_id == current_season.id,
                CupMatch.is_played == True
            ).limit(10).all()

            print(f"\nAnalyzing {len(played_cup_matches)} played cup matches:")

            from models import PlayerCupMatchPerformance

            for match in played_cup_matches:
                print(f"\n=== Cup Match {match.id} ===")
                print(f"  {match.home_team.name} vs {match.away_team.name if match.away_team else 'Freilos'}")
                print(f"  Score: {match.home_score} - {match.away_score}")
                print(f"  Cup: {match.cup.name}, Round: {match.round_name}")
                print(f"  Date: {match.match_date}")

                # Check player performances
                performances = PlayerCupMatchPerformance.query.filter_by(cup_match_id=match.id).all()
                print(f"  Player performances: {len(performances)}")

                if len(performances) == 0:
                    print("  ❌ NO PLAYER PERFORMANCES FOUND!")
                elif len(performances) < 12:  # Should be 12 players (6 home + 6 away)
                    print(f"  ⚠️  Only {len(performances)} player performances (expected 12)")
                    for perf in performances:
                        print(f"    - {perf.player.name}: {perf.total_pins} pins")
                else:
                    print(f"  ✅ {len(performances)} player performances found")
                    # Show a few performances
                    for perf in performances[:4]:
                        print(f"    - {perf.player.name}: {perf.total_pins} pins")

                # Check if scores are unusually low
                if match.home_score < 300 or (match.away_score and match.away_score < 300):
                    print(f"  ⚠️  UNUSUALLY LOW SCORES: {match.home_score} - {match.away_score}")

            return

        print(f"Found calendar day: {next_calendar_day.calendar_date} ({next_calendar_day.day_type})")
        print(f"Match day number: {next_calendar_day.match_day_number}")
        print(f"Found {len(cup_matches_data)} cup matches for date {target_date}")
        print()
        
        # Show cup matches
        print("\n=== CUP MATCHES ===")
        clubs_with_matches = set()
        for i, match_data in enumerate(cup_matches_data):
            print(f"  {i+1}. Match ID: {match_data.get('match_id')} - {match_data.get('cup_name')}")
            print(f"     {match_data.get('home_team_name')} vs {match_data.get('away_team_name')}")
            print(f"     Cup Day: {match_data.get('cup_match_day')}")
            print(f"     Home Club ID: {match_data.get('home_club_id')}")
            print(f"     Away Club ID: {match_data.get('away_club_id')}")
            
            clubs_with_matches.add(match_data.get('home_club_id'))
            if match_data.get('away_club_id'):
                clubs_with_matches.add(match_data.get('away_club_id'))
            print()
        
        print(f"Clubs with matches: {clubs_with_matches}")
        print()
        
        # Test old player assignment (without target_date)
        print("=== TESTING OLD PLAYER ASSIGNMENT (without target_date) ===")
        cache = CacheManager()
        old_club_team_players = batch_assign_players_to_teams(
            clubs_with_matches,
            next_calendar_day.match_day_number,
            current_season.id,
            cache
        )
        
        print(f"Old assignment found players for {len(old_club_team_players)} clubs")
        for club_id, teams in old_club_team_players.items():
            print(f"  Club {club_id}: {len(teams)} teams")
            for team_id, players in teams.items():
                print(f"    Team {team_id}: {len(players)} players")
        print()
        
        # Test new player assignment (with target_date)
        print("=== TESTING NEW PLAYER ASSIGNMENT (with target_date) ===")
        cache = CacheManager()
        new_club_team_players = batch_assign_players_to_teams(
            clubs_with_matches,
            next_calendar_day.match_day_number,
            current_season.id,
            cache,
            target_date=target_date
        )
        
        print(f"New assignment found players for {len(new_club_team_players)} clubs")
        for club_id, teams in new_club_team_players.items():
            print(f"  Club {club_id}: {len(teams)} teams")
            for team_id, players in teams.items():
                print(f"    Team {team_id}: {len(players)} players")
                for player in players[:3]:  # Show first 3 players
                    if isinstance(player, dict):
                        print(f"      - {player.get('name', 'Unknown')} (ID: {player.get('id', 'N/A')}, Stroh: {player.get('is_stroh', False)})")
                    else:
                        print(f"      - {player.name} (ID: {player.id})")
        print()
        
        # Check specific cup match details
        print("=== CUP MATCH DETAILS ===")
        for match_data in cup_matches_data[:2]:  # Check first 2 matches
            cup_match_id = match_data.get('cup_match_id')
            cup_match = CupMatch.query.get(cup_match_id)
            
            if cup_match:
                print(f"Cup Match {cup_match_id}:")
                print(f"  Cup Match Day: {cup_match.cup_match_day}")
                print(f"  Match Date: {cup_match.match_date}")
                print(f"  Round: {cup_match.round_name}")
                print(f"  Home Team: {cup_match.home_team.name} (Club: {cup_match.home_team.club_id})")
                if cup_match.away_team:
                    print(f"  Away Team: {cup_match.away_team.name} (Club: {cup_match.away_team.club_id})")
                else:
                    print(f"  Away Team: Freilos")
                print()

if __name__ == "__main__":
    debug_cup_player_assignment()
