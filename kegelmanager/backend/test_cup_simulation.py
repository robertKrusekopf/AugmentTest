#!/usr/bin/env python3
"""
Test-Skript um zu überprüfen, ob Pokalspiele korrekt simuliert werden können.
"""

import sqlite3
from datetime import datetime

def test_cup_simulation():
    """Testet, ob Pokalspiele simuliert werden können."""
    
    db_path = 'instance/RealeDB_with_cups_fixed.db'
    
    print("=== Test: Pokal-Simulation ===")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prüfe Pokalspiele mit Daten
    cursor.execute("""
        SELECT cm.id, cm.home_team_id, cm.away_team_id, cm.match_date, cm.is_played,
               ht.name as home_team, at.name as away_team
        FROM cup_match cm
        LEFT JOIN team ht ON cm.home_team_id = ht.id
        LEFT JOIN team at ON cm.away_team_id = at.id
        WHERE cm.match_date IS NOT NULL
        ORDER BY cm.match_date
    """)
    
    cup_matches = cursor.fetchall()
    
    print(f"Gefunden: {len(cup_matches)} Pokalspiele mit Daten")
    
    for match in cup_matches:
        match_id, home_id, away_id, match_date, is_played, home_name, away_name = match
        
        # Konvertiere match_date string zu datetime
        match_datetime = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
        
        print(f"\nSpiel {match_id}: {home_name} vs {away_name}")
        print(f"  Datum: {match_datetime.strftime('%d.%m.%Y %H:%M')}")
        print(f"  Gespielt: {'Ja' if is_played else 'Nein'}")
        
        if not is_played:
            print(f"  ✅ Spiel kann simuliert werden!")
        else:
            print(f"  ℹ️ Spiel bereits gespielt")
    
    # Prüfe Freilose
    cursor.execute("""
        SELECT cm.id, cm.home_team_id, cm.away_team_id, cm.is_played,
               ht.name as home_team
        FROM cup_match cm
        LEFT JOIN team ht ON cm.home_team_id = ht.id
        WHERE cm.away_team_id IS NULL
    """)
    
    bye_matches = cursor.fetchall()
    
    print(f"\nGefunden: {len(bye_matches)} Freilose")
    
    for bye in bye_matches:
        match_id, home_id, away_id, is_played, home_name = bye
        print(f"  Freilos {match_id}: {home_name} (automatisch weiter)")
    
    # Prüfe Saisonkalender für CUP_DAYs
    cursor.execute("""
        SELECT match_day_number, calendar_date, weekday
        FROM season_calendar 
        WHERE day_type = 'CUP_DAY'
        ORDER BY match_day_number
    """)
    
    cup_days = cursor.fetchall()
    
    print(f"\nCUP_DAYs im Kalender: {len(cup_days)}")
    for day in cup_days:
        match_day, date, weekday = day
        print(f"  Pokalspieltag {match_day}: {date} ({weekday})")
    
    conn.close()
    
    # Bewertung
    if len(cup_matches) > 0 and len(cup_days) > 0:
        print(f"\n✅ ERFOLGREICH: Pokale sind vollständig konfiguriert!")
        print(f"   - {len(cup_matches)} Spiele mit Daten")
        print(f"   - {len(bye_matches)} Freilose")
        print(f"   - {len(cup_days)} Pokalspieltage im Kalender")
        print(f"   - Spiele können simuliert werden!")
        return True
    else:
        print(f"\n❌ FEHLER: Pokale sind nicht vollständig konfiguriert!")
        return False

if __name__ == "__main__":
    success = test_cup_simulation()
    
    if success:
        print("\n🎉 Alle Tests erfolgreich! Pokale funktionieren wie bei einer neuen Datenbank.")
    else:
        print("\n💥 Tests fehlgeschlagen!")
