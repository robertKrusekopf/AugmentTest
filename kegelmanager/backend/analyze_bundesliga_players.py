#!/usr/bin/env python3
"""
Erstellt eine Liste aller Spieler der 1. Bundesliga mit Verein, Stärke und Durchschnittsergebnis.
"""

import sqlite3
import sys
import os

def analyze_bundesliga_players():
    """Analysiert alle Spieler der 1. Bundesliga."""
    
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
    
    # Verwende die erste Datenbank
    selected_db = db_files[0]
    print(f"Verwende Datenbank: {selected_db}")
    
    db_path = os.path.join(db_dir, selected_db)
    
    try:
        # Verbindung zur Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n1. BUNDESLIGA SPIELER - ÜBERSICHT")
        print("="*80)
        
        # Hauptabfrage für alle Spieler der 1. Bundesliga
        bundesliga_query = """
        SELECT 
            p.name as spieler_name,
            c.name as verein_name,
            t.name as team_name,
            p.strength,
            p.konstanz,
            p.drucksicherheit,
            p.volle,
            p.raeumer,
            COUNT(perf.id) as spiele,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            ROUND(AVG(perf.volle_score), 1) as avg_volle,
            ROUND(AVG(perf.raeumer_score), 1) as avg_raeumer,
            ROUND(AVG(perf.fehler_count), 1) as avg_fehler,
            ROUND(AVG(perf.set_points), 2) as avg_sp
        FROM player p
        JOIN club c ON p.club_id = c.id
        JOIN team t ON t.club_id = c.id
        JOIN league l ON t.league_id = l.id
        LEFT JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE l.level = 1 AND p.strength IS NOT NULL
        GROUP BY p.id, p.name, c.name, t.name, p.strength, p.konstanz, p.drucksicherheit, p.volle, p.raeumer
        ORDER BY c.name, p.strength DESC, p.name
        """
        
        cursor.execute(bundesliga_query)
        results = cursor.fetchall()
        
        if not results:
            print("Keine Spieler in der 1. Bundesliga gefunden!")
            return
        
        # Ergebnisse nach Verein gruppiert anzeigen
        current_club = None
        club_players = []
        total_players = 0
        
        print(f"{'Spieler':<25} {'Verein':<25} {'Team':<20} {'Stärke':<6} {'Spiele':<6} {'Ø Score':<8} {'Ø SP':<6}")
        print("-" * 100)
        
        for row in results:
            spieler_name, verein_name, team_name, strength, konstanz, drucksicherheit, volle, raeumer, spiele, avg_score, avg_volle, avg_raeumer, avg_fehler, avg_sp = row
            
            # Neue Vereinsgruppe
            if current_club != verein_name:
                if current_club is not None:
                    # Vereinsstatistik anzeigen
                    if club_players:
                        club_avg_strength = sum(p[3] for p in club_players) / len(club_players)
                        club_avg_score = sum(p[9] for p in club_players if p[9] is not None) / len([p for p in club_players if p[9] is not None]) if any(p[9] is not None for p in club_players) else 0
                        print(f"{'>>> VEREINSSCHNITT:':<25} {'':<25} {'':<20} {club_avg_strength:<6.1f} {'':<6} {club_avg_score:<8.1f} {'':<6}")
                        print("-" * 100)
                
                current_club = verein_name
                club_players = []
            
            club_players.append(row)
            total_players += 1
            
            # Spielerdaten anzeigen
            avg_score_str = f"{avg_score:.1f}" if avg_score is not None else "N/A"
            avg_sp_str = f"{avg_sp:.2f}" if avg_sp is not None else "N/A"
            spiele_str = str(spiele) if spiele > 0 else "0"
            
            print(f"{spieler_name:<25} {verein_name:<25} {team_name:<20} {strength:<6} {spiele_str:<6} {avg_score_str:<8} {avg_sp_str:<6}")
        
        # Letzte Vereinsstatistik
        if club_players:
            club_avg_strength = sum(p[3] for p in club_players) / len(club_players)
            club_avg_score = sum(p[9] for p in club_players if p[9] is not None) / len([p for p in club_players if p[9] is not None]) if any(p[9] is not None for p in club_players) else 0
            print(f"{'>>> VEREINSSCHNITT:':<25} {'':<25} {'':<20} {club_avg_strength:<6.1f} {'':<6} {club_avg_score:<8.1f} {'':<6}")
        
        print("="*100)
        print(f"GESAMT: {total_players} Spieler in der 1. Bundesliga")
        
        # Zusätzliche Statistiken
        print("\n2. BUNDESLIGA STATISTIKEN")
        print("="*50)
        
        # Top 10 Spieler nach Stärke
        top_strength_query = """
        SELECT 
            p.name,
            c.name as verein,
            p.strength,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            COUNT(perf.id) as spiele
        FROM player p
        JOIN club c ON p.club_id = c.id
        JOIN team t ON t.club_id = c.id
        JOIN league l ON t.league_id = l.id
        LEFT JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE l.level = 1 AND p.strength IS NOT NULL
        GROUP BY p.id, p.name, c.name, p.strength
        ORDER BY p.strength DESC, avg_score DESC
        LIMIT 10
        """
        
        cursor.execute(top_strength_query)
        top_strength_results = cursor.fetchall()
        
        print("\nTOP 10 SPIELER NACH STÄRKE:")
        print(f"{'Name':<25} {'Verein':<25} {'Stärke':<6} {'Ø Score':<8} {'Spiele':<6}")
        print("-" * 75)
        for name, verein, strength, avg_score, spiele in top_strength_results:
            avg_score_str = f"{avg_score:.1f}" if avg_score is not None else "N/A"
            spiele_str = str(spiele) if spiele > 0 else "0"
            print(f"{name:<25} {verein:<25} {strength:<6} {avg_score_str:<8} {spiele_str:<6}")
        
        # Top 10 Spieler nach Durchschnittsergebnis (mindestens 5 Spiele)
        top_performance_query = """
        SELECT 
            p.name,
            c.name as verein,
            p.strength,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            COUNT(perf.id) as spiele
        FROM player p
        JOIN club c ON p.club_id = c.id
        JOIN team t ON t.club_id = c.id
        JOIN league l ON t.league_id = l.id
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE l.level = 1 AND p.strength IS NOT NULL
        GROUP BY p.id, p.name, c.name, p.strength
        HAVING COUNT(perf.id) >= 5
        ORDER BY avg_score DESC
        LIMIT 10
        """
        
        cursor.execute(top_performance_query)
        top_performance_results = cursor.fetchall()
        
        print("\nTOP 10 SPIELER NACH LEISTUNG (min. 5 Spiele):")
        print(f"{'Name':<25} {'Verein':<25} {'Stärke':<6} {'Ø Score':<8} {'Spiele':<6}")
        print("-" * 75)
        for name, verein, strength, avg_score, spiele in top_performance_results:
            print(f"{name:<25} {verein:<25} {strength:<6} {avg_score:<8.1f} {spiele:<6}")
        
        # Vereinsstatistiken
        club_stats_query = """
        SELECT 
            c.name as verein_name,
            COUNT(DISTINCT p.id) as anzahl_spieler,
            ROUND(AVG(p.strength), 1) as avg_strength,
            MIN(p.strength) as min_strength,
            MAX(p.strength) as max_strength,
            ROUND(AVG(perf_avg.avg_score), 1) as verein_avg_score
        FROM club c
        JOIN team t ON t.club_id = c.id
        JOIN league l ON t.league_id = l.id
        JOIN player p ON p.club_id = c.id
        LEFT JOIN (
            SELECT 
                player_id,
                AVG(total_score) as avg_score
            FROM player_match_performance
            GROUP BY player_id
        ) perf_avg ON p.id = perf_avg.player_id
        WHERE l.level = 1 AND p.strength IS NOT NULL
        GROUP BY c.id, c.name
        ORDER BY avg_strength DESC
        """
        
        cursor.execute(club_stats_query)
        club_stats_results = cursor.fetchall()
        
        print("\nVEREINSSTATISTIKEN:")
        print(f"{'Verein':<30} {'Spieler':<8} {'Ø Stärke':<9} {'Min':<4} {'Max':<4} {'Ø Score':<8}")
        print("-" * 75)
        for verein_name, anzahl_spieler, avg_strength, min_strength, max_strength, verein_avg_score in club_stats_results:
            verein_avg_score_str = f"{verein_avg_score:.1f}" if verein_avg_score is not None else "N/A"
            print(f"{verein_name:<30} {anzahl_spieler:<8} {avg_strength:<9} {min_strength:<4} {max_strength:<4} {verein_avg_score_str:<8}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Datenbankfehler: {e}")
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_bundesliga_players()
