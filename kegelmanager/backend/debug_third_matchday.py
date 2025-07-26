#!/usr/bin/env python3

import app
from models import *
from simulation import *
from season_calendar import get_next_match_date
from sqlalchemy import func

def debug_third_matchday():
    with app.app.app_context():
        season = Season.query.filter_by(is_current=True).first()
        print(f'Current season: {season.name}')
        
        # Simuliere die ersten beiden Spieltage
        print('\n=== Simulating first two match days ===')
        for i in range(2):
            next_date = get_next_match_date(season.id)
            if next_date:
                print(f'Match day {i+1}: {next_date.calendar_date} ({next_date.day_type})')
                result = simulate_match_day(season)
                print(f'Simulated {result["matches_simulated"]} matches')
            else:
                print('No more match days')
                break
        
        # Schaue was als nächstes kommt (sollte der dritte Spieltag sein)
        print('\n=== Next match day (should be 3rd) ===')
        next_date = get_next_match_date(season.id)
        if next_date:
            print(f'Next date: {next_date.calendar_date} ({next_date.day_type})')
            print(f'Match day number: {next_date.match_day_number}')
            
            # Schaue welche Spiele für dieses Datum geplant sind
            league_matches = get_league_matches_for_date(season.id, next_date.calendar_date)
            cup_matches = get_cup_matches_for_date(season.id, next_date.calendar_date)
            
            print(f'League matches on this date: {len(league_matches)}')
            print(f'Cup matches on this date: {len(cup_matches)}')
            
            if league_matches:
                print('\nLeague matches:')
                for match in league_matches[:3]:  # Zeige nur die ersten 3
                    print(f'  Match {match.match_id}: {match.home_team_name} vs {match.away_team_name} (Match Day {match.match_day})')
            
            if cup_matches:
                print('\nCup matches:')
                for match in cup_matches[:3]:  # Zeige nur die ersten 3
                    print(f'  Cup Match {match["match_id"]}: {match["home_team_name"]} vs {match["away_team_name"]} (Cup Day {match["cup_match_day"]})')
        
        else:
            print('No next match day found')

        # Zusätzliche Analyse: Schaue was am 30.08.2025 laut Kalender passieren sollte
        from datetime import date
        target_date = date(2025, 8, 30)

        calendar_entry = SeasonCalendar.query.filter(
            SeasonCalendar.season_id == season.id,
            SeasonCalendar.calendar_date == target_date
        ).first()

        print(f'\n=== Analysis of 2025-08-30 ===')
        if calendar_entry:
            print(f'Calendar entry for {target_date}:')
            print(f'  Day type: {calendar_entry.day_type}')
            print(f'  Match day number: {calendar_entry.match_day_number}')
            print(f'  Week number: {calendar_entry.week_number}')
        else:
            print(f'No calendar entry found for {target_date}')

        # Schaue welche Liga-Spiele für dieses Datum geplant sind
        league_matches = db.session.query(Match).filter(
            Match.season_id == season.id,
            Match.is_played == False,
            func.date(Match.match_date) == target_date
        ).all()

        print(f'\nLeague matches scheduled for {target_date}: {len(league_matches)}')
        if league_matches:
            for match in league_matches[:5]:
                print(f'  Match {match.id}: {match.home_team.name} vs {match.away_team.name} (Match Day {match.match_day}, Date: {match.match_date})')

        # Schaue welche Cup-Spiele für dieses Datum geplant sind
        cup_matches = db.session.query(CupMatch).join(Cup).filter(
            Cup.season_id == season.id,
            CupMatch.is_played == False,
            func.date(CupMatch.match_date) == target_date
        ).all()

        print(f'\nCup matches scheduled for {target_date}: {len(cup_matches)}')
        if cup_matches:
            for match in cup_matches[:5]:
                print(f'  Cup Match {match.id}: {match.home_team.name} vs {match.away_team.name if match.away_team else "Freilos"} (Cup Day {match.cup_match_day}, Date: {match.match_date})')

if __name__ == '__main__':
    debug_third_matchday()
