#!/usr/bin/env python3
"""
Test-Skript zur Demonstration des echten Problems mit der Spielerverfügbarkeit.
"""

import app
from models import *
from simulation import simulate_match_day
from season_calendar import get_next_match_date
from performance_optimizations import bulk_reset_player_flags
from sqlalchemy import func

def test_real_problem():
    """
    Demonstriert das echte Problem: Liga- und Pokalspieltage haben die gleichen match_day_number!
    """
    with app.app.app_context():
        season = Season.query.filter_by(is_current=True).first()
        if not season:
            print("Keine aktuelle Saison gefunden!")
            return
            
        print(f'Testing REAL problem for season: {season.name}')
        print("=" * 70)
        
        # Schaue dir die Kalendereinträge an
        print("\n1. KALENDER-ANALYSE")
        print("-" * 30)
        
        calendar_days = SeasonCalendar.query.filter_by(
            season_id=season.id
        ).order_by(SeasonCalendar.calendar_date).limit(10).all()
        
        print("Erste 10 Kalendereinträge:")
        for day in calendar_days:
            print(f"  {day.calendar_date} | {day.day_type:10} | match_day_number: {day.match_day_number}")
        
        # Finde Liga- und Pokalspieltage mit gleichen match_day_number
        print("\n2. MATCH_DAY_NUMBER ANALYSE")
        print("-" * 30)
        
        league_days = SeasonCalendar.query.filter_by(
            season_id=season.id,
            day_type='LEAGUE_DAY'
        ).filter(SeasonCalendar.match_day_number.isnot(None)).all()
        
        cup_days = SeasonCalendar.query.filter_by(
            season_id=season.id,
            day_type='CUP_DAY'
        ).filter(SeasonCalendar.match_day_number.isnot(None)).all()
        
        print(f"Liga-Spieltage: {len(league_days)}")
        for day in league_days[:5]:
            print(f"  Liga-Spieltag {day.match_day_number}: {day.calendar_date}")
            
        print(f"\nPokal-Spieltage: {len(cup_days)}")
        for day in cup_days[:5]:
            print(f"  Pokal-Spieltag {day.match_day_number}: {day.calendar_date}")
        
        # Finde Überschneidungen
        league_numbers = {day.match_day_number for day in league_days}
        cup_numbers = {day.match_day_number for day in cup_days}
        overlaps = league_numbers.intersection(cup_numbers)
        
        print(f"\n3. ÜBERSCHNEIDUNGEN")
        print("-" * 30)
        print(f"Liga match_day_numbers: {sorted(list(league_numbers))[:10]}...")
        print(f"Pokal match_day_numbers: {sorted(list(cup_numbers))[:10]}...")
        print(f"Überschneidungen: {sorted(list(overlaps))[:10]}...")
        
        if overlaps:
            print(f"\n❌ PROBLEM BESTÄTIGT!")
            print(f"Liga- und Pokalspieltage haben {len(overlaps)} gleiche match_day_number!")
            print("Das führt zu Problemen bei bulk_reset_player_flags!")
        else:
            print(f"\n✅ Keine Überschneidungen gefunden")
            
        # Demonstriere das Problem
        if overlaps:
            test_overlap_number = min(overlaps)
            print(f"\n4. PROBLEM-DEMONSTRATION mit match_day_number {test_overlap_number}")
            print("-" * 50)
            
            # Finde Liga- und Pokalspieltag mit gleicher Nummer
            league_day = next((day for day in league_days if day.match_day_number == test_overlap_number), None)
            cup_day = next((day for day in cup_days if day.match_day_number == test_overlap_number), None)
            
            if league_day and cup_day:
                print(f"Liga-Spieltag {test_overlap_number}: {league_day.calendar_date}")
                print(f"Pokal-Spieltag {test_overlap_number}: {cup_day.calendar_date}")
                
                # Simuliere das Problem
                test_player = Player.query.first()
                if test_player:
                    print(f"\nTest-Spieler: {test_player.name}")
                    
                    # Setze Spieler als "gespielt" für Liga-Spieltag
                    test_player.has_played_current_matchday = True
                    test_player.last_played_matchday = test_overlap_number
                    test_player.is_available_current_matchday = True
                    db.session.commit()
                    
                    print(f"Nach Liga-Spieltag {test_overlap_number}:")
                    print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
                    print(f"  - last_played_matchday: {test_player.last_played_matchday}")
                    
                    # Jetzt kommt der Pokal-Spieltag mit GLEICHER match_day_number
                    print(f"\nRufe bulk_reset_player_flags(current_match_day={test_overlap_number}) für Pokal auf...")
                    bulk_reset_player_flags(current_match_day=test_overlap_number)
                    
                    db.session.refresh(test_player)
                    print(f"Nach bulk_reset_player_flags für Pokal-Spieltag {test_overlap_number}:")
                    print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
                    print(f"  - last_played_matchday: {test_player.last_played_matchday}")
                    
                    # PROBLEM: Da last_played_matchday == current_match_day,
                    # wird has_played_current_matchday NICHT zurückgesetzt!
                    if test_player.has_played_current_matchday:
                        print(f"\n❌ PROBLEM BESTÄTIGT!")
                        print("Der Spieler kann nicht am Pokal teilnehmen, obwohl er sollte!")
                        print("Grund: Liga und Pokal haben die gleiche match_day_number!")
                    else:
                        print(f"\n✅ Kein Problem")

def show_solution():
    """
    Zeigt die Lösung für das Problem.
    """
    print("\n" + "=" * 70)
    print("LÖSUNG")
    print("=" * 70)
    
    print("""
Das Problem liegt in der bulk_reset_player_flags Funktion:

AKTUELL:
```sql
UPDATE player SET has_played_current_matchday = 0 
WHERE has_played_current_matchday = 1 
AND (last_played_matchday IS NULL OR last_played_matchday != :match_day)
```

PROBLEM:
- Liga-Spieltag 1 und Pokal-Spieltag 1 haben beide match_day_number = 1
- Spieler spielt Liga-Spieltag 1 → last_played_matchday = 1
- Pokal-Spieltag 1 ruft bulk_reset_player_flags(current_match_day=1) auf
- Da last_played_matchday (1) == current_match_day (1), wird has_played_current_matchday NICHT zurückgesetzt

LÖSUNG:
Die Funktion muss den day_type (LEAGUE_DAY vs CUP_DAY) berücksichtigen:

1. Für LEAGUE_DAY: Normale Logik beibehalten
2. Für CUP_DAY: has_played_current_matchday für ALLE Spieler zurücksetzen,
   da Pokal- und Liga-Spiele unabhängig sind

ODER:

Verwende separate match_day_number Bereiche:
- Liga: 1-100
- Pokal: 101-200
""")

if __name__ == "__main__":
    test_real_problem()
    show_solution()
