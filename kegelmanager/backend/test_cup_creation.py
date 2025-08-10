#!/usr/bin/env python3
"""
Test-Skript um zu überprüfen, ob Pokale korrekt erstellt werden
wenn extend_existing_db verwendet wird.
"""

import os
import sys
import sqlite3
from datetime import datetime

def check_cups_in_database(db_path):
    """
    Überprüft, ob Pokale in einer Datenbank vorhanden sind.
    
    Args:
        db_path (str): Pfad zur Datenbank
        
    Returns:
        dict: Informationen über gefundene Pokale
    """
    if not os.path.exists(db_path):
        print(f"Datenbank '{db_path}' nicht gefunden.")
        return {"success": False, "message": "Datenbank nicht gefunden"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prüfe, ob die cup Tabelle existiert
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cup'")
    if not cursor.fetchone():
        print("Tabelle 'cup' nicht gefunden.")
        conn.close()
        return {"success": False, "message": "Cup-Tabelle nicht gefunden"}
    
    # Hole alle Pokale
    cursor.execute("""
        SELECT id, name, cup_type, season_id, bundesland, landkreis, is_active
        FROM cup
    """)
    
    cups = cursor.fetchall()
    
    # Prüfe auch CupMatch Tabelle
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cup_match'")
    cup_match_table_exists = cursor.fetchone() is not None
    
    cup_matches_count = 0
    if cup_match_table_exists:
        cursor.execute("SELECT COUNT(*) FROM cup_match")
        cup_matches_count = cursor.fetchone()[0]
    
    conn.close()
    
    result = {
        "success": True,
        "cups_count": len(cups),
        "cups": cups,
        "cup_matches_count": cup_matches_count
    }
    
    return result

def test_extend_existing_db_cups():
    """
    Testet, ob extend_existing_db korrekt Pokale erstellt.
    """
    print("=== Test: Pokal-Erstellung in extend_existing_db ===")
    
    # Prüfe, ob eine Test-Datenbank existiert
    test_db_path = "instance/test_base.db"
    
    if not os.path.exists(test_db_path):
        print(f"Test-Datenbank '{test_db_path}' nicht gefunden.")
        print("Erstelle zuerst eine Test-Datenbank mit:")
        print("python create_test_db.py")
        return False
    
    print(f"Analysiere {test_db_path} vor der Erweiterung...")
    before_result = check_cups_in_database(test_db_path)
    
    if not before_result["success"]:
        print(f"Fehler beim Analysieren der Datenbank: {before_result['message']}")
        return False
    
    print(f"Pokale vor Erweiterung: {before_result['cups_count']}")
    print(f"Pokal-Spiele vor Erweiterung: {before_result['cup_matches_count']}")
    
    # Erweitere die Datenbank
    extended_db_name = "test_base_extended"
    extended_db_path = f"instance/{extended_db_name}.db"
    
    # Lösche die erweiterte Datenbank falls sie bereits existiert
    if os.path.exists(extended_db_path):
        os.remove(extended_db_path)
        print(f"Alte erweiterte Datenbank '{extended_db_path}' gelöscht.")
    
    print(f"\nErweitere Datenbank mit extend_existing_db...")
    print(f"Befehl: python extend_existing_db.py {test_db_path} {extended_db_name}")
    
    # Importiere und führe extend_existing_database aus
    try:
        from extend_existing_db import extend_existing_database
        result = extend_existing_database(test_db_path, extended_db_name)
        
        if not result["success"]:
            print(f"Fehler beim Erweitern der Datenbank: {result['message']}")
            return False
        
        print(f"Datenbank erfolgreich erweitert: {result['message']}")
        
    except Exception as e:
        print(f"Fehler beim Erweitern der Datenbank: {str(e)}")
        return False
    
    # Analysiere die erweiterte Datenbank
    print(f"\nAnalysiere {extended_db_path} nach der Erweiterung...")
    after_result = check_cups_in_database(extended_db_path)
    
    if not after_result["success"]:
        print(f"Fehler beim Analysieren der erweiterten Datenbank: {after_result['message']}")
        return False
    
    print(f"Pokale nach Erweiterung: {after_result['cups_count']}")
    print(f"Pokal-Spiele nach Erweiterung: {after_result['cup_matches_count']}")
    
    # Zeige Details der erstellten Pokale
    if after_result["cups_count"] > 0:
        print("\n=== Erstellte Pokale ===")
        for cup in after_result["cups"]:
            cup_id, name, cup_type, season_id, bundesland, landkreis, is_active = cup
            print(f"ID {cup_id}: {name} ({cup_type})")
            if bundesland:
                print(f"  Bundesland: {bundesland}")
            if landkreis:
                print(f"  Landkreis: {landkreis}")
            print(f"  Aktiv: {is_active}")
    
    # Bewertung des Tests
    success = after_result["cups_count"] > before_result["cups_count"]
    
    if success:
        print(f"\n✅ TEST ERFOLGREICH: {after_result['cups_count'] - before_result['cups_count']} neue Pokale erstellt!")
        if after_result["cup_matches_count"] > 0:
            print(f"✅ {after_result['cup_matches_count']} Pokal-Spiele erstellt!")
    else:
        print(f"\n❌ TEST FEHLGESCHLAGEN: Keine neuen Pokale erstellt.")
    
    return success

def main():
    """Hauptfunktion für den Test."""
    success = test_extend_existing_db_cups()
    
    if success:
        print("\n🎉 Alle Tests erfolgreich!")
        sys.exit(0)
    else:
        print("\n💥 Tests fehlgeschlagen!")
        sys.exit(1)

if __name__ == "__main__":
    main()
