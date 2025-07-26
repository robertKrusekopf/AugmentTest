#!/usr/bin/env python3
"""
Debug-Skript zur Untersuchung des Problems mit der Spielerverfügbarkeit
zwischen Liga- und Pokalspieltagen.

Das Problem: Wenn ein Pokalspieltag auf einen Ligaspieltag folgt, sind Spieler
oft als nicht verfügbar markiert, obwohl sie verfügbar sein sollten.
"""

import app
from models import *
from simulation import simulate_match_day
from season_calendar import get_next_match_date
from performance_optimizations import bulk_reset_player_flags
from sqlalchemy import func

def debug_player_availability_issue():
    """
    Untersucht das Problem mit der Spielerverfügbarkeit zwischen Liga- und Pokalspieltagen.
    """
    with app.app.app_context():
        season = Season.query.filter_by(is_current=True).first()
        if not season:
            print("Keine aktuelle Saison gefunden!")
            return
            
        print(f'Debugging player availability for season: {season.name}')
        print("=" * 60)
        
        # Hole die nächsten 5 Spieltage
        calendar_days = SeasonCalendar.query.filter_by(
            season_id=season.id,
            is_simulated=False
        ).order_by(SeasonCalendar.calendar_date).limit(5).all()
        
        if not calendar_days:
            print("Keine ungespielte Spieltage gefunden!")
            return
            
        print("Nächste 5 Spieltage:")
        for i, day in enumerate(calendar_days):
            print(f"  {i+1}. {day.calendar_date} ({day.day_type}) - Spieltag {day.match_day_number}")
        print()
        
        # Simuliere die ersten beiden Spieltage und analysiere die Spielerverfügbarkeit
        for i in range(min(3, len(calendar_days))):
            current_day = calendar_days[i]
            print(f"\n{'='*60}")
            print(f"SIMULIERE SPIELTAG {i+1}: {current_day.calendar_date} ({current_day.day_type})")
            print(f"Match Day Number: {current_day.match_day_number}")
            print(f"{'='*60}")
            
            # Analysiere Spielerverfügbarkeit VOR der Simulation
            print("\n--- SPIELERVERFÜGBARKEIT VOR SIMULATION ---")
            analyze_player_availability_before_simulation(season.id)
            
            # Simuliere den Spieltag
            result = simulate_match_day(season)
            print(f"\nSimulation Result: {result['matches_simulated']} Spiele simuliert")
            
            # Analysiere Spielerverfügbarkeit NACH der Simulation
            print("\n--- SPIELERVERFÜGBARKEIT NACH SIMULATION ---")
            analyze_player_availability_after_simulation(season.id)
            
            # Wenn dies ein Ligaspieltag war und der nächste ein Pokalspieltag ist,
            # analysiere das Problem
            if (i < len(calendar_days) - 1 and 
                current_day.day_type == 'LEAGUE_DAY' and 
                calendar_days[i+1].day_type == 'CUP_DAY'):
                
                print(f"\n🔍 KRITISCHER PUNKT: Liga -> Pokal Übergang erkannt!")
                print(f"Aktueller Tag: {current_day.day_type}")
                print(f"Nächster Tag: {calendar_days[i+1].day_type}")
                
                # Teste, was passiert, wenn wir bulk_reset_player_flags aufrufen
                print("\n--- TESTE BULK_RESET_PLAYER_FLAGS ---")
                next_match_day = calendar_days[i+1].match_day_number
                print(f"Calling bulk_reset_player_flags(current_match_day={next_match_day})")
                
                # Zeige Spieler-Flags vor dem Reset
                show_player_flags_sample("VOR bulk_reset_player_flags")
                
                bulk_reset_player_flags(current_match_day=next_match_day)
                
                # Zeige Spieler-Flags nach dem Reset
                show_player_flags_sample("NACH bulk_reset_player_flags")

def analyze_player_availability_before_simulation(season_id):
    """Analysiert die Spielerverfügbarkeit vor der Simulation."""
    total_players = Player.query.count()
    available_players = Player.query.filter_by(is_available_current_matchday=True).count()
    played_players = Player.query.filter_by(has_played_current_matchday=True).count()
    
    print(f"Gesamt Spieler: {total_players}")
    print(f"Verfügbare Spieler: {available_players} ({available_players/total_players*100:.1f}%)")
    print(f"Bereits gespielt: {played_players} ({played_players/total_players*100:.1f}%)")

def analyze_player_availability_after_simulation(season_id):
    """Analysiert die Spielerverfügbarkeit nach der Simulation."""
    total_players = Player.query.count()
    available_players = Player.query.filter_by(is_available_current_matchday=True).count()
    played_players = Player.query.filter_by(has_played_current_matchday=True).count()
    
    print(f"Gesamt Spieler: {total_players}")
    print(f"Verfügbare Spieler: {available_players} ({available_players/total_players*100:.1f}%)")
    print(f"Bereits gespielt: {played_players} ({played_players/total_players*100:.1f}%)")

def show_player_flags_sample(title, limit=10):
    """Zeigt eine Stichprobe von Spieler-Flags."""
    print(f"\n{title} (erste {limit} Spieler):")
    players = Player.query.limit(limit).all()
    
    for player in players:
        print(f"  {player.name}: available={player.is_available_current_matchday}, "
              f"played={player.has_played_current_matchday}, "
              f"last_played={player.last_played_matchday}")

def analyze_bulk_reset_logic():
    """
    Analysiert die Logik der bulk_reset_player_flags Funktion.
    """
    print("\n" + "="*60)
    print("ANALYSE DER BULK_RESET_PLAYER_FLAGS LOGIK")
    print("="*60)
    
    print("""
PROBLEM IDENTIFIZIERT:

Die bulk_reset_player_flags Funktion hat ein Logikproblem:

1. Sie setzt IMMER is_available_current_matchday = 1 für ALLE Spieler
2. Sie setzt has_played_current_matchday = 0 nur für Spieler, die an einem 
   ANDEREN Spieltag gespielt haben

ABER: Bei Liga -> Pokal Übergängen:
- Liga-Spieltag hat match_day_number = X
- Pokal-Spieltag hat match_day_number = Y (unterschiedlich von X)
- Spieler, die am Liga-Spieltag gespielt haben, haben last_played_matchday = X
- Beim Pokal-Spieltag wird bulk_reset_player_flags(current_match_day=Y) aufgerufen
- Da X != Y, werden die has_played_current_matchday Flags NICHT zurückgesetzt
- Aber is_available_current_matchday wird trotzdem auf 1 gesetzt

RESULTAT: Spieler sind als "verfügbar" markiert, aber haben immer noch 
has_played_current_matchday = True, was zu Konflikten führt.

LÖSUNG: Die Logik muss unterscheiden zwischen Liga- und Pokalspieltagen.
""")

if __name__ == "__main__":
    debug_player_availability_issue()
    analyze_bulk_reset_logic()
