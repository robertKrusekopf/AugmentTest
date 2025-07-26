#!/usr/bin/env python3
"""
Test-Skript zur Überprüfung der Lösung für das Spielerverfügbarkeits-Problem.
"""

import app
from models import *
from simulation import simulate_match_day
from season_calendar import get_next_match_date
from performance_optimizations import bulk_reset_player_flags
from sqlalchemy import func

def test_fix_verification():
    """
    Überprüft, ob die Lösung das Problem behebt.
    """
    with app.app.app_context():
        season = Season.query.filter_by(is_current=True).first()
        if not season:
            print("Keine aktuelle Saison gefunden!")
            return
            
        print(f'Testing FIX for season: {season.name}')
        print("=" * 70)
        
        # Hole einen Test-Spieler
        test_player = Player.query.first()
        if not test_player:
            print("Keine Spieler gefunden!")
            return
            
        print(f"Test-Spieler: {test_player.name} (ID: {test_player.id})")
        
        # Test 1: Liga-Spieltag
        print(f"\n1. TEST LIGA-SPIELTAG")
        print("-" * 30)
        
        # Setze Spieler als "gespielt" für Liga-Spieltag 1
        test_player.has_played_current_matchday = True
        test_player.last_played_matchday = 1
        test_player.is_available_current_matchday = True
        db.session.commit()
        
        print(f"Nach Liga-Spieltag 1:")
        print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
        print(f"  - last_played_matchday: {test_player.last_played_matchday}")
        
        # Teste Liga-Spieltag 2 (normale Logik)
        print(f"\nRufe bulk_reset_player_flags(current_match_day=2, day_type='LEAGUE_DAY') auf...")
        bulk_reset_player_flags(current_match_day=2, day_type='LEAGUE_DAY')
        
        db.session.refresh(test_player)
        print(f"Nach Liga-Spieltag 2:")
        print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
        print(f"  - last_played_matchday: {test_player.last_played_matchday}")
        
        if not test_player.has_played_current_matchday:
            print("✅ Liga-Logik funktioniert: Spieler kann an Liga-Spieltag 2 teilnehmen")
        else:
            print("❌ Liga-Logik fehlerhaft")
        
        # Test 2: Pokal-Spieltag mit gleicher match_day_number
        print(f"\n2. TEST POKAL-SPIELTAG (gleiche match_day_number)")
        print("-" * 50)
        
        # Setze Spieler wieder als "gespielt" für Liga-Spieltag 1
        test_player.has_played_current_matchday = True
        test_player.last_played_matchday = 1
        test_player.is_available_current_matchday = True
        db.session.commit()
        
        print(f"Nach Liga-Spieltag 1 (erneut gesetzt):")
        print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
        print(f"  - last_played_matchday: {test_player.last_played_matchday}")
        
        # Teste Pokal-Spieltag 1 (gleiche match_day_number wie Liga!)
        print(f"\nRufe bulk_reset_player_flags(current_match_day=1, day_type='CUP_DAY') auf...")
        bulk_reset_player_flags(current_match_day=1, day_type='CUP_DAY')
        
        db.session.refresh(test_player)
        print(f"Nach Pokal-Spieltag 1:")
        print(f"  - has_played_current_matchday: {test_player.has_played_current_matchday}")
        print(f"  - last_played_matchday: {test_player.last_played_matchday}")
        
        if not test_player.has_played_current_matchday:
            print("✅ LÖSUNG FUNKTIONIERT: Spieler kann am Pokal teilnehmen!")
            print("   Obwohl Liga und Pokal die gleiche match_day_number haben!")
        else:
            print("❌ LÖSUNG FEHLERHAFT: Spieler kann immer noch nicht am Pokal teilnehmen")
        
        # Test 3: Vergleich alte vs neue Logik
        print(f"\n3. VERGLEICH ALTE VS NEUE LOGIK")
        print("-" * 40)
        
        # Simuliere alte Logik
        test_player.has_played_current_matchday = True
        test_player.last_played_matchday = 1
        db.session.commit()
        
        print("Alte Logik (ohne day_type):")
        # Simuliere alte Logik durch Aufruf ohne day_type
        bulk_reset_player_flags(current_match_day=1, day_type=None)
        db.session.refresh(test_player)
        old_logic_result = test_player.has_played_current_matchday
        print(f"  - has_played_current_matchday: {old_logic_result}")
        
        # Setze zurück für neue Logik
        test_player.has_played_current_matchday = True
        test_player.last_played_matchday = 1
        db.session.commit()
        
        print("Neue Logik (mit day_type='CUP_DAY'):")
        bulk_reset_player_flags(current_match_day=1, day_type='CUP_DAY')
        db.session.refresh(test_player)
        new_logic_result = test_player.has_played_current_matchday
        print(f"  - has_played_current_matchday: {new_logic_result}")
        
        if old_logic_result and not new_logic_result:
            print("✅ VERBESSERUNG BESTÄTIGT!")
            print("   Alte Logik: Spieler blockiert")
            print("   Neue Logik: Spieler verfügbar")
        else:
            print("❌ Keine Verbesserung erkannt")

def test_real_scenario():
    """
    Testet ein realistisches Szenario mit echten Kalender-Daten.
    """
    print(f"\n" + "=" * 70)
    print("REAL-SZENARIO TEST")
    print("=" * 70)
    
    with app.app.app_context():
        season = Season.query.filter_by(is_current=True).first()
        
        # Finde einen Liga- und Pokal-Spieltag mit gleicher match_day_number
        league_day = SeasonCalendar.query.filter_by(
            season_id=season.id,
            day_type='LEAGUE_DAY',
            match_day_number=1
        ).first()
        
        cup_day = SeasonCalendar.query.filter_by(
            season_id=season.id,
            day_type='CUP_DAY',
            match_day_number=1
        ).first()
        
        if league_day and cup_day:
            print(f"Liga-Spieltag 1: {league_day.calendar_date}")
            print(f"Pokal-Spieltag 1: {cup_day.calendar_date}")
            print(f"Zeitlicher Abstand: {(cup_day.calendar_date - league_day.calendar_date).days} Tage")
            
            # Teste mit mehreren Spielern
            test_players = Player.query.limit(5).all()
            print(f"\nTeste mit {len(test_players)} Spielern:")
            
            # Setze alle als "gespielt" für Liga-Spieltag
            for player in test_players:
                player.has_played_current_matchday = True
                player.last_played_matchday = 1
                player.is_available_current_matchday = True
            db.session.commit()
            
            print("Nach Liga-Spieltag 1:")
            played_count = sum(1 for p in test_players if p.has_played_current_matchday)
            print(f"  - {played_count}/{len(test_players)} Spieler haben gespielt")
            
            # Wende neue Logik für Pokal an
            bulk_reset_player_flags(current_match_day=1, day_type='CUP_DAY')
            
            # Lade Spieler neu
            for player in test_players:
                db.session.refresh(player)
            
            print("Nach Pokal-Reset (neue Logik):")
            available_count = sum(1 for p in test_players if not p.has_played_current_matchday)
            print(f"  - {available_count}/{len(test_players)} Spieler verfügbar für Pokal")
            
            if available_count == len(test_players):
                print("✅ ALLE SPIELER VERFÜGBAR FÜR POKAL!")
            else:
                print("❌ Nicht alle Spieler verfügbar")
        else:
            print("Keine passenden Liga/Pokal-Spieltage gefunden")

if __name__ == "__main__":
    test_fix_verification()
    test_real_scenario()
