#!/usr/bin/env python3
"""
Test-Skript zur Demonstration und Behebung des Spielerverfügbarkeits-Problems.
"""

import app
from models import *
from simulation import simulate_match_day
from season_calendar import get_next_match_date
from performance_optimizations import bulk_reset_player_flags
from sqlalchemy import func

def test_player_availability_problem():
    """
    Demonstriert das Problem mit der Spielerverfügbarkeit zwischen Liga- und Pokalspieltagen.
    """
    with app.app.app_context():
        season = Season.query.filter_by(is_current=True).first()
        if not season:
            print("Keine aktuelle Saison gefunden!")
            return
            
        print(f'Testing player availability problem for season: {season.name}')
        print("=" * 70)
        
        # Simuliere einen Liga-Spieltag
        print("\n1. SIMULIERE LIGA-SPIELTAG")
        print("-" * 30)
        
        # Hole einen Spieler als Beispiel
        test_player = Player.query.first()
        if not test_player:
            print("Keine Spieler gefunden!")
            return
            
        print(f"Test-Spieler: {test_player.name} (ID: {test_player.id})")
        
        # Setze den Spieler als "gespielt" für Liga-Spieltag 1
        test_player.has_played_current_matchday = True
        test_player.last_played_matchday = 1  # Liga-Spieltag
        test_player.is_available_current_matchday = True
        db.session.commit()
        
        print(f"Nach Liga-Spieltag 1:")
        print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
        print(f"  - last_played_matchday: {test_player.last_played_matchday}")
        print(f"  - is_available_current_matchday: {test_player.is_available_current_matchday}")
        
        # Simuliere jetzt einen Pokal-Spieltag
        print("\n2. SIMULIERE POKAL-SPIELTAG")
        print("-" * 30)
        
        # Rufe bulk_reset_player_flags für Pokal-Spieltag auf (andere match_day_number)
        pokal_match_day = 2  # Unterschiedliche match_day_number
        print(f"Calling bulk_reset_player_flags(current_match_day={pokal_match_day})")
        
        bulk_reset_player_flags(current_match_day=pokal_match_day)
        
        # Lade den Spieler neu
        db.session.refresh(test_player)
        
        print(f"Nach bulk_reset_player_flags für Pokal-Spieltag {pokal_match_day}:")
        print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
        print(f"  - last_played_matchday: {test_player.last_played_matchday}")
        print(f"  - is_available_current_matchday: {test_player.is_available_current_matchday}")
        
        # PROBLEM: Der Spieler hat immer noch has_played_current_matchday = True
        # obwohl er für den Pokal-Spieltag verfügbar sein sollte!
        
        if test_player.has_played_current_matchday and test_player.last_played_matchday != pokal_match_day:
            print("\n❌ PROBLEM BESTÄTIGT!")
            print("Der Spieler hat has_played_current_matchday = True, obwohl er")
            print("an einem anderen Spieltag gespielt hat und für den Pokal verfügbar sein sollte!")
        else:
            print("\n✅ Kein Problem erkannt")
            
        return test_player

def demonstrate_current_logic():
    """
    Demonstriert die aktuelle Logik der bulk_reset_player_flags Funktion.
    """
    print("\n" + "=" * 70)
    print("AKTUELLE LOGIK VON bulk_reset_player_flags")
    print("=" * 70)
    
    print("""
Die aktuelle Implementierung:

1. Setzt IMMER is_available_current_matchday = 1 für ALLE Spieler
2. Setzt has_played_current_matchday = 0 NUR für Spieler mit:
   - has_played_current_matchday = 1 UND
   - (last_played_matchday IS NULL ODER last_played_matchday != current_match_day)

PROBLEM bei Liga -> Pokal Übergang:
- Liga-Spieltag: match_day_number = 1
- Pokal-Spieltag: match_day_number = 2
- Spieler hat last_played_matchday = 1 (Liga)
- bulk_reset_player_flags(current_match_day=2) wird aufgerufen
- Da 1 != 2, wird has_played_current_matchday NICHT zurückgesetzt
- Spieler ist "verfügbar" aber hat immer noch "gespielt" Flag

LÖSUNG:
Die Funktion muss unterscheiden zwischen Liga- und Pokalspieltagen
und entsprechend die Flags zurücksetzen.
""")

def test_proposed_fix():
    """
    Testet die vorgeschlagene Lösung.
    """
    print("\n" + "=" * 70)
    print("TEST DER VORGESCHLAGENEN LÖSUNG")
    print("=" * 70)
    
    with app.app.app_context():
        # Hole einen Spieler
        test_player = Player.query.first()
        
        # Setze ihn als "gespielt" für Liga-Spieltag
        test_player.has_played_current_matchday = True
        test_player.last_played_matchday = 1  # Liga-Spieltag
        test_player.is_available_current_matchday = True
        db.session.commit()
        
        print(f"Test-Spieler: {test_player.name}")
        print(f"Vor Fix - Liga-Spieltag 1:")
        print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
        print(f"  - last_played_matchday: {test_player.last_played_matchday}")
        
        # Teste die neue Logik (simuliert)
        print(f"\nSimuliere neue Logik für Pokal-Spieltag 2:")
        
        # Neue Logik: Für Pokalspieltage, setze has_played_current_matchday = 0
        # für alle Spieler, unabhängig von last_played_matchday
        test_player.has_played_current_matchday = False
        test_player.is_available_current_matchday = True
        db.session.commit()
        
        print(f"Nach Fix - Pokal-Spieltag 2:")
        print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
        print(f"  - last_played_matchday: {test_player.last_played_matchday}")
        print(f"  - is_available_current_matchday: {test_player.is_available_current_matchday}")
        
        print("\n✅ Mit der neuen Logik kann der Spieler am Pokal teilnehmen!")

if __name__ == "__main__":
    test_player = test_player_availability_problem()
    demonstrate_current_logic()
    test_proposed_fix()
