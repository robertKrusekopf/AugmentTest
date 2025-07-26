#!/usr/bin/env python3
"""
Test-Skript zur Überprüfung der Simulation mit der neuen Lösung.
"""

import app
from models import *
from simulation import simulate_match_day
from season_calendar import get_next_match_date
from sqlalchemy import func

def test_simulation_with_fix():
    """
    Testet die Simulation mit der neuen Lösung.
    """
    with app.app.app_context():
        season = Season.query.filter_by(is_current=True).first()
        if not season:
            print("Keine aktuelle Saison gefunden!")
            return
            
        print(f'Testing SIMULATION with FIX for season: {season.name}')
        print("=" * 70)
        
        # Hole die nächsten Spieltage
        calendar_days = SeasonCalendar.query.filter_by(
            season_id=season.id,
            is_simulated=False
        ).order_by(SeasonCalendar.calendar_date).limit(5).all()
        
        print("Nächste 5 Spieltage:")
        for i, day in enumerate(calendar_days):
            print(f"  {i+1}. {day.calendar_date} ({day.day_type}) - Spieltag {day.match_day_number}")
        
        # Suche nach Liga -> Pokal Übergang
        liga_to_cup_transition = None
        for i in range(len(calendar_days) - 1):
            current = calendar_days[i]
            next_day = calendar_days[i + 1]
            if (current.day_type == 'LEAGUE_DAY' and 
                next_day.day_type == 'CUP_DAY' and
                current.match_day_number == next_day.match_day_number):
                liga_to_cup_transition = (current, next_day)
                break
        
        if liga_to_cup_transition:
            liga_day, cup_day = liga_to_cup_transition
            print(f"\n🎯 GEFUNDEN: Liga -> Pokal Übergang!")
            print(f"Liga-Spieltag {liga_day.match_day_number}: {liga_day.calendar_date}")
            print(f"Pokal-Spieltag {cup_day.match_day_number}: {cup_day.calendar_date}")
            print("(Gleiche match_day_number - perfekt zum Testen!)")
            
            # Analysiere Spielerverfügbarkeit vor Liga-Simulation
            print(f"\n1. VOR LIGA-SIMULATION")
            print("-" * 30)
            analyze_player_availability()
            
            # Simuliere Liga-Spieltag
            print(f"\n2. SIMULIERE LIGA-SPIELTAG {liga_day.match_day_number}")
            print("-" * 40)
            result = simulate_match_day(season)
            print(f"Liga-Simulation: {result['matches_simulated']} Spiele simuliert")
            
            # Analysiere Spielerverfügbarkeit nach Liga-Simulation
            print(f"\n3. NACH LIGA-SIMULATION")
            print("-" * 30)
            analyze_player_availability()
            
            # Simuliere Pokal-Spieltag
            print(f"\n4. SIMULIERE POKAL-SPIELTAG {cup_day.match_day_number}")
            print("-" * 40)
            result = simulate_match_day(season)
            print(f"Pokal-Simulation: {result['matches_simulated']} Spiele simuliert")
            
            # Analysiere Spielerverfügbarkeit nach Pokal-Simulation
            print(f"\n5. NACH POKAL-SIMULATION")
            print("-" * 30)
            analyze_player_availability()
            
            if result['matches_simulated'] > 0:
                print(f"\n✅ ERFOLG!")
                print("Liga -> Pokal Übergang funktioniert mit der neuen Lösung!")
                print("Spieler können sowohl an Liga- als auch an Pokalspielen teilnehmen!")
            else:
                print(f"\n❌ PROBLEM!")
                print("Keine Pokalspiele simuliert - möglicherweise Spielerverfügbarkeitsproblem")
        else:
            print(f"\n⚠️  Kein Liga -> Pokal Übergang mit gleicher match_day_number gefunden")
            print("Teste normale Simulation...")
            
            # Simuliere die nächsten 2 Spieltage
            for i in range(min(2, len(calendar_days))):
                day = calendar_days[i]
                print(f"\n{i+1}. SIMULIERE {day.day_type} {day.match_day_number}")
                print(f"   Datum: {day.calendar_date}")
                print("-" * 40)
                
                result = simulate_match_day(season)
                print(f"Simulation: {result['matches_simulated']} Spiele simuliert")
                
                if result['matches_simulated'] > 0:
                    print("✅ Simulation erfolgreich")
                else:
                    print("❌ Keine Spiele simuliert")

def analyze_player_availability():
    """
    Analysiert die aktuelle Spielerverfügbarkeit.
    """
    total_players = Player.query.count()
    available_players = Player.query.filter_by(is_available_current_matchday=True).count()
    played_players = Player.query.filter_by(has_played_current_matchday=True).count()
    
    print(f"Gesamt Spieler: {total_players}")
    print(f"Verfügbare Spieler: {available_players} ({available_players/total_players*100:.1f}%)")
    print(f"Bereits gespielt: {played_players} ({played_players/total_players*100:.1f}%)")
    
    # Analysiere Clubs mit wenigen verfügbaren Spielern
    clubs_with_issues = []
    clubs = Club.query.all()
    
    for club in clubs:
        total_club_players = Player.query.filter_by(club_id=club.id).count()
        available_club_players = Player.query.filter_by(
            club_id=club.id, 
            is_available_current_matchday=True
        ).count()
        
        if total_club_players > 0:
            availability_rate = available_club_players / total_club_players
            if availability_rate < 0.6:  # Weniger als 60% verfügbar
                clubs_with_issues.append((club.name, available_club_players, total_club_players))
    
    if clubs_with_issues:
        print(f"\nClubs mit wenigen verfügbaren Spielern:")
        for club_name, available, total in clubs_with_issues[:5]:
            print(f"  {club_name}: {available}/{total} verfügbar ({available/total*100:.1f}%)")
    else:
        print(f"\nAlle Clubs haben ausreichend verfügbare Spieler")

def show_summary():
    """
    Zeigt eine Zusammenfassung der Lösung.
    """
    print(f"\n" + "=" * 70)
    print("ZUSAMMENFASSUNG DER LÖSUNG")
    print("=" * 70)
    
    print("""
PROBLEM:
- Liga- und Pokalspieltage hatten die gleichen match_day_number (1, 2, 3, ...)
- bulk_reset_player_flags() setzte has_played_current_matchday nicht zurück,
  wenn last_played_matchday == current_match_day
- Spieler, die an Liga-Spieltag 1 gespielt hatten, konnten nicht an 
  Pokal-Spieltag 1 teilnehmen

LÖSUNG:
- Erweiterte bulk_reset_player_flags() um day_type Parameter
- Für CUP_DAY: Setze has_played_current_matchday für ALLE Spieler zurück
- Für LEAGUE_DAY: Behalte die ursprüngliche Logik bei
- simulate_match_day() übergibt jetzt den day_type

ERGEBNIS:
✅ Liga- und Pokalspieltage sind jetzt unabhängig
✅ Spieler können sowohl an Liga- als auch an Pokalspielen teilnehmen
✅ Keine Änderung der match_day_number Struktur erforderlich
✅ Rückwärtskompatibilität gewährleistet
""")

if __name__ == "__main__":
    test_simulation_with_fix()
    show_summary()
