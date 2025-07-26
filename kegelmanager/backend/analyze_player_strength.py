#!/usr/bin/env python3
"""
Analyse der durchschnittlichen Spielerstärke je Liga in der aktuellen Datenbank.
"""

import os
import sys
import sqlite3
from collections import defaultdict

def analyze_player_strength_by_league():
    """Analysiert die durchschnittliche Spielerstärke je Liga."""
    
    # Finde die aktuelle Datenbank
    db_dir = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(db_dir):
        print("Fehler: Datenbank-Verzeichnis nicht gefunden.")
        return
    
    # Liste alle .db Dateien auf
    db_files = [f for f in os.listdir(db_dir) if f.endswith('.db')]
    if not db_files:
        print("Fehler: Keine Datenbank-Dateien gefunden.")
        return
    
    print("Verfügbare Datenbanken:")
    for i, db_file in enumerate(db_files, 1):
        print(f"{i}. {db_file}")
    
    # Verwende die erste Datenbank oder lasse den Benutzer wählen
    if len(db_files) == 1:
        selected_db = db_files[0]
        print(f"\nVerwende Datenbank: {selected_db}")
    else:
        try:
            choice = input(f"\nWähle eine Datenbank (1-{len(db_files)}): ")
            selected_db = db_files[int(choice) - 1]
        except (ValueError, IndexError):
            selected_db = db_files[0]
            print(f"Ungültige Eingabe. Verwende: {selected_db}")
    
    db_path = os.path.join(db_dir, selected_db)
    
    try:
        # Verbinde zur Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQL-Abfrage für Spielerstärke je Liga
        query = """
        SELECT 
            l.level as liga_level,
            l.name as liga_name,
            COUNT(p.id) as anzahl_spieler,
            ROUND(AVG(p.strength), 2) as durchschnitt_staerke,
            MIN(p.strength) as min_staerke,
            MAX(p.strength) as max_staerke,
            ROUND(AVG(p.talent), 2) as durchschnitt_talent
        FROM player p
        JOIN club c ON p.club_id = c.id
        JOIN team t ON t.club_id = c.id
        JOIN league l ON t.league_id = l.id
        WHERE p.strength IS NOT NULL
        GROUP BY l.level, l.name
        ORDER BY l.level ASC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if not results:
            print("Keine Daten gefunden.")
            return
        
        print("\n" + "="*80)
        print("ANALYSE DER SPIELERSTÄRKE JE LIGA")
        print("="*80)
        print(f"{'Liga':<25} {'Level':<6} {'Spieler':<8} {'Ø Stärke':<10} {'Min':<5} {'Max':<5} {'Ø Talent':<8}")
        print("-"*80)
        
        total_players = 0
        total_strength_sum = 0
        league_data = []
        
        for row in results:
            liga_level, liga_name, anzahl_spieler, durchschnitt_staerke, min_staerke, max_staerke, durchschnitt_talent = row
            
            print(f"{liga_name:<25} {liga_level:<6} {anzahl_spieler:<8} {durchschnitt_staerke:<10} {min_staerke:<5} {max_staerke:<5} {durchschnitt_talent:<8}")
            
            total_players += anzahl_spieler
            total_strength_sum += durchschnitt_staerke * anzahl_spieler
            league_data.append((liga_level, durchschnitt_staerke, anzahl_spieler))
        
        print("-"*80)
        overall_avg = total_strength_sum / total_players if total_players > 0 else 0
        print(f"{'GESAMT':<25} {'':<6} {total_players:<8} {overall_avg:.2f}")
        
        # Zusätzliche Statistiken
        print("\n" + "="*50)
        print("ZUSÄTZLICHE STATISTIKEN")
        print("="*50)
        
        # Durchschnittliche Stärke je Liga-Level (gruppiert)
        level_stats = defaultdict(list)
        for level, strength, count in league_data:
            level_stats[level].extend([strength] * count)
        
        print(f"{'Liga Level':<12} {'Ø Stärke':<10} {'Anzahl Ligen':<12}")
        print("-"*35)
        for level in sorted(level_stats.keys()):
            strengths = level_stats[level]
            avg_strength = sum(strengths) / len(strengths)
            num_leagues = len([l for l, _, _ in league_data if l == level])
            print(f"{level:<12} {avg_strength:.2f}{'':>4} {num_leagues:<12}")
        
        # Detaillierte Spielerverteilung
        print("\n" + "="*50)
        print("SPIELERVERTEILUNG NACH STÄRKE")
        print("="*50)
        
        strength_query = """
        SELECT 
            CASE 
                WHEN p.strength >= 80 THEN '80-99 (Elite)'
                WHEN p.strength >= 70 THEN '70-79 (Sehr gut)'
                WHEN p.strength >= 60 THEN '60-69 (Gut)'
                WHEN p.strength >= 50 THEN '50-59 (Durchschnitt)'
                WHEN p.strength >= 40 THEN '40-49 (Unterdurchschnitt)'
                WHEN p.strength >= 30 THEN '30-39 (Schwach)'
                ELSE '1-29 (Sehr schwach)'
            END as staerke_kategorie,
            COUNT(*) as anzahl,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM player WHERE strength IS NOT NULL), 1) as prozent
        FROM player p
        WHERE p.strength IS NOT NULL
        GROUP BY staerke_kategorie
        ORDER BY MIN(p.strength) DESC
        """
        
        cursor.execute(strength_query)
        strength_results = cursor.fetchall()
        
        print(f"{'Stärke-Kategorie':<20} {'Anzahl':<8} {'Prozent':<8}")
        print("-"*40)
        for kategorie, anzahl, prozent in strength_results:
            print(f"{kategorie:<20} {anzahl:<8} {prozent}%")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Datenbankfehler: {e}")
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    analyze_player_strength_by_league()
