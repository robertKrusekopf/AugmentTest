#!/usr/bin/env python3
"""
Test-Skript für die erweiterte extend_existing_database Funktionalität.
Dieses Skript demonstriert, wie die neue Funktion Spieler mit unvollständigen Attributen ergänzt.
"""

import os
import sys
import sqlite3
from datetime import datetime

def check_player_attributes(db_path):
    """
    Überprüft die Spielerattribute in einer Datenbank und zeigt unvollständige Spieler an.
    
    Args:
        db_path (str): Pfad zur Datenbank
    """
    if not os.path.exists(db_path):
        print(f"Datenbank '{db_path}' nicht gefunden.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prüfe, ob die player Tabelle existiert
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player'")
    if not cursor.fetchone():
        print("Tabelle 'player' nicht gefunden.")
        conn.close()
        return
    
    # Hole alle Spieler
    cursor.execute("""
        SELECT id, name, strength, club_id, age, talent, position, salary, contract_end,
               ausdauer, konstanz, drucksicherheit, volle, raeumer, sicherheit,
               auswaerts, start, mitte, schluss
        FROM player
    """)
    
    players = cursor.fetchall()
    conn.close()
    
    if not players:
        print("Keine Spieler in der Datenbank gefunden.")
        return
    
    print(f"\n=== Analyse der Spielerattribute in {db_path} ===")
    print(f"Anzahl Spieler: {len(players)}")
    
    incomplete_players = []
    complete_players = 0
    
    for player in players:
        player_id, name, strength, club_id, age, talent, position, salary, contract_end, \
        ausdauer, konstanz, drucksicherheit, volle, raeumer, sicherheit, \
        auswaerts, start, mitte, schluss = player
        
        missing_attributes = []
        
        # Prüfe alle wichtigen Attribute
        if age is None or age == 0:
            missing_attributes.append('age')
        if talent is None or talent == 0:
            missing_attributes.append('talent')
        if position is None or position == "":
            missing_attributes.append('position')
        if salary is None or salary == 0:
            missing_attributes.append('salary')
        if contract_end is None:
            missing_attributes.append('contract_end')
        if ausdauer is None or ausdauer == 0:
            missing_attributes.append('ausdauer')
        if konstanz is None or konstanz == 0:
            missing_attributes.append('konstanz')
        if drucksicherheit is None or drucksicherheit == 0:
            missing_attributes.append('drucksicherheit')
        if volle is None or volle == 0:
            missing_attributes.append('volle')
        if raeumer is None or raeumer == 0:
            missing_attributes.append('raeumer')
        if sicherheit is None or sicherheit == 0:
            missing_attributes.append('sicherheit')
        if auswaerts is None or auswaerts == 0:
            missing_attributes.append('auswaerts')
        if start is None or start == 0:
            missing_attributes.append('start')
        if mitte is None or mitte == 0:
            missing_attributes.append('mitte')
        if schluss is None or schluss == 0:
            missing_attributes.append('schluss')
        
        if missing_attributes:
            incomplete_players.append({
                'id': player_id,
                'name': name,
                'strength': strength,
                'club_id': club_id,
                'missing': missing_attributes
            })
        else:
            complete_players += 1
    
    print(f"Vollständige Spieler: {complete_players}")
    print(f"Unvollständige Spieler: {len(incomplete_players)}")
    
    if incomplete_players:
        print("\n=== Unvollständige Spieler ===")
        for player in incomplete_players[:10]:  # Zeige nur die ersten 10
            print(f"ID {player['id']}: {player['name']} (Stärke: {player['strength']}, Verein: {player['club_id']})")
            print(f"  Fehlende Attribute: {', '.join(player['missing'])}")
        
        if len(incomplete_players) > 10:
            print(f"... und {len(incomplete_players) - 10} weitere")
    
    return len(incomplete_players) > 0


def main():
    """Hauptfunktion für den Test."""
    print("=== Test der erweiterten extend_existing_database Funktionalität ===")
    
    # Prüfe, ob RealeDB.db existiert
    reale_db_path = "Datenbanken/RealeDB.db"
    
    if not os.path.exists(reale_db_path):
        print(f"RealeDB.db nicht gefunden unter {reale_db_path}")
        print("Bitte stelle sicher, dass die RealeDB.db im Datenbanken-Ordner vorhanden ist.")
        return
    
    print(f"Analysiere {reale_db_path}...")
    has_incomplete = check_player_attributes(reale_db_path)
    
    if has_incomplete:
        print("\n=== Empfehlung ===")
        print("Die Datenbank enthält Spieler mit unvollständigen Attributen.")
        print("Verwende die extend_existing_database Funktion, um diese zu ergänzen:")
        print(f"python extend_existing_db.py {reale_db_path} RealeDB_Extended")
        print("\nDies wird eine neue Datenbank 'RealeDB_Extended.db' erstellen mit vollständigen Spielerattributen.")
    else:
        print("\nAlle Spieler haben vollständige Attribute!")


if __name__ == "__main__":
    main()
