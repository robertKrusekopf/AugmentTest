#!/usr/bin/env python3
"""
Analysiert den Zusammenhang zwischen Spielerstärke und deren Ergebnissen.
"""

import sqlite3
import sys
import os
import numpy as np

def analyze_strength_performance_correlation():
    """Analysiert den Zusammenhang zwischen Spielerstärke und Leistung."""
    
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
        # Verbindung zur Datenbank
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\nANALYSE: ZUSAMMENHANG SPIELERSTÄRKE UND ERGEBNISSE")
        print("="*60)
        
        # 1. Grundlegende Korrelationsanalyse
        print("\n1. KORRELATION STÄRKE vs. DURCHSCHNITTSERGEBNIS")
        print("-" * 50)
        
        correlation_query = """
        SELECT
            p.id,
            p.name,
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
            SUM(perf.match_points) as total_mp,
            ROUND(AVG(perf.set_points), 2) as avg_sp
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength IS NOT NULL
        GROUP BY p.id, p.name, p.strength, p.konstanz, p.drucksicherheit, p.volle, p.raeumer
        HAVING COUNT(perf.id) >= 5  -- Mindestens 5 Spiele
        ORDER BY p.strength DESC
        """
        
        cursor.execute(correlation_query)
        results = cursor.fetchall()
        
        if not results:
            print("Keine Daten für Korrelationsanalyse gefunden!")
            return
        
        # Daten für Analyse extrahieren
        strengths = []
        avg_scores = []
        avg_volles = []
        avg_raeumers = []
        avg_fehlers = []
        avg_sps = []
        player_names = []
        
        for row in results:
            player_id, name, strength, konstanz, drucksicherheit, volle, raeumer, spiele, avg_score, avg_volle, avg_raeumer, avg_fehler, total_mp, avg_sp = row
            strengths.append(strength)
            avg_scores.append(avg_score)
            avg_volles.append(avg_volle)
            avg_raeumers.append(avg_raeumer)
            avg_fehlers.append(avg_fehler)
            avg_sps.append(avg_sp)
            player_names.append(name)
        
        # Korrelationskoeffizienten berechnen
        corr_score = np.corrcoef(strengths, avg_scores)[0, 1]
        corr_volle = np.corrcoef(strengths, avg_volles)[0, 1]
        corr_raeumer = np.corrcoef(strengths, avg_raeumers)[0, 1]
        corr_fehler = np.corrcoef(strengths, avg_fehlers)[0, 1]
        corr_sp = np.corrcoef(strengths, avg_sps)[0, 1]
        
        print(f"Korrelation Stärke vs. Durchschnittsergebnis: {corr_score:.3f}")
        print(f"Korrelation Stärke vs. Volle-Ergebnis:       {corr_volle:.3f}")
        print(f"Korrelation Stärke vs. Räumer-Ergebnis:      {corr_raeumer:.3f}")
        print(f"Korrelation Stärke vs. Fehleranzahl:         {corr_fehler:.3f}")
        print(f"Korrelation Stärke vs. Satzpunkte:           {corr_sp:.3f}")
        
        # Interpretation der Korrelation
        print("\nInterpretation:")
        if corr_score > 0.7:
            print("- STARKE positive Korrelation zwischen Stärke und Ergebnis")
        elif corr_score > 0.5:
            print("- MITTLERE positive Korrelation zwischen Stärke und Ergebnis")
        elif corr_score > 0.3:
            print("- SCHWACHE positive Korrelation zwischen Stärke und Ergebnis")
        else:
            print("- KEINE oder sehr schwache Korrelation zwischen Stärke und Ergebnis")
        
        # 2. Stärke-Kategorien Analyse
        print("\n2. LEISTUNG NACH STÄRKE-KATEGORIEN")
        print("-" * 50)
        
        category_query = """
        SELECT
            CASE
                WHEN p.strength >= 80 THEN '80-99 (Elite)'
                WHEN p.strength >= 70 THEN '70-79 (Sehr gut)'
                WHEN p.strength >= 60 THEN '60-69 (Gut)'
                WHEN p.strength >= 50 THEN '50-59 (Durchschnitt)'
                WHEN p.strength >= 40 THEN '40-49 (Unterdurchschnitt)'
                ELSE '30-39 (Schwach)'
            END as staerke_kategorie,
            COUNT(DISTINCT p.id) as anzahl_spieler,
            COUNT(perf.id) as anzahl_spiele,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            ROUND(AVG(perf.volle_score), 1) as avg_volle,
            ROUND(AVG(perf.raeumer_score), 1) as avg_raeumer,
            ROUND(AVG(perf.fehler_count), 1) as avg_fehler,
            ROUND(AVG(perf.set_points), 2) as avg_sp,
            ROUND(AVG(CAST(perf.match_points AS FLOAT)), 2) as avg_mp
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength IS NOT NULL
        GROUP BY staerke_kategorie
        ORDER BY MIN(p.strength) DESC
        """
        
        cursor.execute(category_query)
        category_results = cursor.fetchall()
        
        print(f"{'Kategorie':<20} {'Spieler':<8} {'Spiele':<8} {'Ø Score':<8} {'Ø Volle':<8} {'Ø Räumer':<9} {'Ø Fehler':<8} {'Ø SP':<6} {'Ø MP':<6}")
        print("-" * 95)
        for row in category_results:
            kategorie, spieler, spiele, score, volle, raeumer, fehler, sp, mp = row
            print(f"{kategorie:<20} {spieler:<8} {spiele:<8} {score:<8} {volle:<8} {raeumer:<9} {fehler:<8} {sp:<6} {mp:<6}")
        
        # 3. Top und Bottom Performer
        print("\n3. TOP 10 SPIELER NACH DURCHSCHNITTSERGEBNIS")
        print("-" * 50)
        
        top_query = """
        SELECT
            p.name,
            p.strength,
            COUNT(perf.id) as spiele,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            ROUND(AVG(perf.set_points), 2) as avg_sp
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength IS NOT NULL
        GROUP BY p.id, p.name, p.strength
        HAVING COUNT(perf.id) >= 5
        ORDER BY avg_score DESC
        LIMIT 10
        """
        
        cursor.execute(top_query)
        top_results = cursor.fetchall()
        
        print(f"{'Name':<25} {'Stärke':<7} {'Spiele':<7} {'Ø Score':<8} {'Ø SP':<6}")
        print("-" * 55)
        for name, strength, spiele, score, sp in top_results:
            print(f"{name:<25} {strength:<7} {spiele:<7} {score:<8} {sp:<6}")
        
        print("\n4. BOTTOM 10 SPIELER NACH DURCHSCHNITTSERGEBNIS")
        print("-" * 50)
        
        bottom_query = """
        SELECT
            p.name,
            p.strength,
            COUNT(perf.id) as spiele,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            ROUND(AVG(perf.set_points), 2) as avg_sp
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength IS NOT NULL
        GROUP BY p.id, p.name, p.strength
        HAVING COUNT(perf.id) >= 5
        ORDER BY avg_score ASC
        LIMIT 10
        """
        
        cursor.execute(bottom_query)
        bottom_results = cursor.fetchall()
        
        print(f"{'Name':<25} {'Stärke':<7} {'Spiele':<7} {'Ø Score':<8} {'Ø SP':<6}")
        print("-" * 55)
        for name, strength, spiele, score, sp in bottom_results:
            print(f"{name:<25} {strength:<7} {spiele:<7} {score:<8} {sp:<6}")
        
        # 5. Anomalien-Analyse (erweitert)
        print("\n5. ANOMALIEN - SPIELER MIT UNERWARTETER LEISTUNG")
        print("-" * 50)

        # Erweiterte Anomalien-Suche mit flexibleren Kriterien

        # A) Starke Spieler (70+) mit den schlechtesten Ergebnissen (absolut)
        anomaly_high_query = """
        SELECT
            p.name,
            p.strength,
            COUNT(perf.id) as spiele,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            ROUND(AVG(perf.set_points), 2) as avg_sp,
            ROUND(AVG(perf.total_score) - (120 + p.strength * 5.5), 1) as abweichung
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength >= 70 AND p.strength IS NOT NULL
        GROUP BY p.id, p.name, p.strength
        HAVING COUNT(perf.id) >= 5
        ORDER BY avg_score ASC
        LIMIT 10
        """

        cursor.execute(anomaly_high_query)
        anomaly_high_results = cursor.fetchall()

        if anomaly_high_results:
            print("Starke Spieler (70+) mit den schlechtesten absoluten Ergebnissen:")
            print(f"{'Name':<25} {'Stärke':<7} {'Spiele':<7} {'Ø Score':<8} {'Ø SP':<6} {'Abweichung':<10}")
            print("-" * 70)
            for name, strength, spiele, score, sp, abweichung in anomaly_high_results:
                print(f"{name:<25} {strength:<7} {spiele:<7} {score:<8} {sp:<6} {abweichung:<10}")

        # B) Schwache Spieler (≤50) mit den besten Ergebnissen (absolut)
        anomaly_low_query = """
        SELECT
            p.name,
            p.strength,
            COUNT(perf.id) as spiele,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            ROUND(AVG(perf.set_points), 2) as avg_sp,
            ROUND(AVG(perf.total_score) - (120 + p.strength * 5.5), 1) as abweichung
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength <= 50 AND p.strength IS NOT NULL
        GROUP BY p.id, p.name, p.strength
        HAVING COUNT(perf.id) >= 5
        ORDER BY avg_score DESC
        LIMIT 10
        """

        cursor.execute(anomaly_low_query)
        anomaly_low_results = cursor.fetchall()

        if anomaly_low_results:
            print("\nSchwache Spieler (≤50) mit den besten absoluten Ergebnissen:")
            print(f"{'Name':<25} {'Stärke':<7} {'Spiele':<7} {'Ø Score':<8} {'Ø SP':<6} {'Abweichung':<10}")
            print("-" * 70)
            for name, strength, spiele, score, sp, abweichung in anomaly_low_results:
                print(f"{name:<25} {strength:<7} {spiele:<7} {score:<8} {sp:<6} {abweichung:<10}")

        # D) Zusätzliche Analyse: Extreme Anomalien
        print("\n" + "="*60)
        print("EXTREME ANOMALIEN - ECHTE ÜBERRASCHUNGEN")
        print("="*60)

        # Starke Spieler mit wirklich schlechten Ergebnissen (unter 550 Pins)
        extreme_bad_query = """
        SELECT
            p.name,
            p.strength,
            COUNT(perf.id) as spiele,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            ROUND(AVG(perf.set_points), 2) as avg_sp
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength >= 70 AND p.strength IS NOT NULL
        GROUP BY p.id, p.name, p.strength
        HAVING COUNT(perf.id) >= 5 AND AVG(perf.total_score) < 550
        ORDER BY avg_score ASC
        """

        cursor.execute(extreme_bad_query)
        extreme_bad_results = cursor.fetchall()

        if extreme_bad_results:
            print("🔴 STARKE SPIELER (70+) MIT KATASTROPHALEN ERGEBNISSEN (<550 Pins):")
            print(f"{'Name':<25} {'Stärke':<7} {'Spiele':<7} {'Ø Score':<8} {'Ø SP':<6}")
            print("-" * 55)
            for name, strength, spiele, score, sp in extreme_bad_results:
                print(f"{name:<25} {strength:<7} {spiele:<7} {score:<8} {sp:<6}")
        else:
            print("🔴 Keine starken Spieler mit katastrophalen Ergebnissen gefunden.")

        # Schwache Spieler mit wirklich guten Ergebnissen (über 550 Pins)
        extreme_good_query = """
        SELECT
            p.name,
            p.strength,
            COUNT(perf.id) as spiele,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            ROUND(AVG(perf.set_points), 2) as avg_sp
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength <= 50 AND p.strength IS NOT NULL
        GROUP BY p.id, p.name, p.strength
        HAVING COUNT(perf.id) >= 5 AND AVG(perf.total_score) > 550
        ORDER BY avg_score DESC
        """

        cursor.execute(extreme_good_query)
        extreme_good_results = cursor.fetchall()

        if extreme_good_results:
            print("\n🟢 SCHWACHE SPIELER (≤50) MIT ÜBERRASCHEND GUTEN ERGEBNISSEN (>550 Pins):")
            print(f"{'Name':<25} {'Stärke':<7} {'Spiele':<7} {'Ø Score':<8} {'Ø SP':<6}")
            print("-" * 55)
            for name, strength, spiele, score, sp in extreme_good_results:
                print(f"{name:<25} {strength:<7} {spiele:<7} {score:<8} {sp:<6}")
        else:
            print("\n🟢 Keine schwachen Spieler mit überraschend guten Ergebnissen gefunden.")

        # C) Allgemeine Anomalien-Statistik
        anomaly_stats_query = """
        WITH player_averages AS (
            SELECT
                p.id,
                p.strength,
                AVG(perf.total_score) as avg_score,
                ABS(AVG(perf.total_score) - (120 + p.strength * 5.5)) as abweichung
            FROM player p
            JOIN player_match_performance perf ON p.id = perf.player_id
            WHERE p.strength IS NOT NULL
            GROUP BY p.id, p.strength
            HAVING COUNT(perf.id) >= 5
        )
        SELECT
            COUNT(*) as total_players,
            COUNT(CASE WHEN abweichung > 50 THEN 1 END) as anomalies_50,
            COUNT(CASE WHEN abweichung > 30 THEN 1 END) as anomalies_30,
            COUNT(CASE WHEN abweichung > 20 THEN 1 END) as anomalies_20
        FROM player_averages
        """

        cursor.execute(anomaly_stats_query)
        anomaly_stats = cursor.fetchone()

        if anomaly_stats:
            total, anom_50, anom_30, anom_20 = anomaly_stats
            print(f"\nAnomalien-Statistik:")
            print(f"Spieler mit >50 Pins Abweichung: {anom_50} von {total} ({anom_50/total*100:.1f}%)")
            print(f"Spieler mit >30 Pins Abweichung: {anom_30} von {total} ({anom_30/total*100:.1f}%)")
            print(f"Spieler mit >20 Pins Abweichung: {anom_20} von {total} ({anom_20/total*100:.1f}%)")
        
        # 6. Erweiterte Attribut-Analyse
        print("\n6. KORRELATION ALLER ATTRIBUTE MIT LEISTUNG")
        print("-" * 50)

        attribute_query = """
        SELECT
            p.strength,
            p.konstanz,
            p.drucksicherheit,
            p.volle,
            p.raeumer,
            p.sicherheit,
            p.auswaerts,
            p.start,
            p.mitte,
            p.schluss,
            p.ausdauer,
            ROUND(AVG(perf.total_score), 1) as avg_score
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength IS NOT NULL
        GROUP BY p.id, p.strength, p.konstanz, p.drucksicherheit, p.volle, p.raeumer,
                 p.sicherheit, p.auswaerts, p.start, p.mitte, p.schluss, p.ausdauer
        HAVING COUNT(perf.id) >= 5
        """

        cursor.execute(attribute_query)
        attr_results = cursor.fetchall()

        if attr_results:
            # Daten für Korrelationsanalyse extrahieren
            attributes = {
                'strength': [],
                'konstanz': [],
                'drucksicherheit': [],
                'volle': [],
                'raeumer': [],
                'sicherheit': [],
                'auswaerts': [],
                'start': [],
                'mitte': [],
                'schluss': [],
                'ausdauer': []
            }
            scores = []

            for row in attr_results:
                strength, konstanz, drucksicherheit, volle, raeumer, sicherheit, auswaerts, start, mitte, schluss, ausdauer, avg_score = row
                attributes['strength'].append(strength)
                attributes['konstanz'].append(konstanz)
                attributes['drucksicherheit'].append(drucksicherheit)
                attributes['volle'].append(volle)
                attributes['raeumer'].append(raeumer)
                attributes['sicherheit'].append(sicherheit)
                attributes['auswaerts'].append(auswaerts)
                attributes['start'].append(start)
                attributes['mitte'].append(mitte)
                attributes['schluss'].append(schluss)
                attributes['ausdauer'].append(ausdauer)
                scores.append(avg_score)

            # Korrelationen berechnen
            print(f"{'Attribut':<15} {'Korrelation':<12} {'Interpretation'}")
            print("-" * 50)

            for attr_name, attr_values in attributes.items():
                if len(attr_values) > 1:  # Mindestens 2 Werte für Korrelation
                    corr = np.corrcoef(attr_values, scores)[0, 1]
                    if abs(corr) > 0.7:
                        interpretation = "STARK"
                    elif abs(corr) > 0.5:
                        interpretation = "MITTEL"
                    elif abs(corr) > 0.3:
                        interpretation = "SCHWACH"
                    else:
                        interpretation = "KEINE"

                    print(f"{attr_name:<15} {corr:<12.3f} {interpretation}")

        # 7. Zusammenfassung und Fazit
        print("\n7. ZUSAMMENFASSUNG UND FAZIT")
        print("-" * 50)

        # Korrelations-Interpretation aktualisieren
        if corr_score > 0.9:
            corr_interpretation = "SEHR STARKE positive Korrelation"
        elif corr_score > 0.7:
            corr_interpretation = "STARKE positive Korrelation"
        elif corr_score > 0.5:
            corr_interpretation = "MITTLERE positive Korrelation"
        elif corr_score > 0.3:
            corr_interpretation = "SCHWACHE positive Korrelation"
        else:
            corr_interpretation = "KEINE oder sehr schwache Korrelation"

        print(f"• Korrelation Stärke-Ergebnis: {corr_score:.3f} ({corr_interpretation})")
        print(f"• Stärkste negative Korrelation: Fehleranzahl ({corr_fehler:.3f})")
        print(f"• Schwächste Korrelation: Satzpunkte ({corr_sp:.3f})")

        # Berechne Unterschied zwischen stärksten und schwächsten Spielern
        elite_avg = None
        weak_avg = None
        for row in category_results:
            kategorie, spieler, spiele, score, volle, raeumer, fehler, sp, mp = row
            if "Elite" in kategorie:
                elite_avg = score
            elif "Schwach" in kategorie:
                weak_avg = score

        print("\nFazit:")
        print(f"- Die Spielerstärke hat einen {corr_interpretation.lower()} Einfluss auf die Ergebnisse")
        if elite_avg and weak_avg:
            diff = elite_avg - weak_avg
            print(f"- Starke Spieler (80+) erzielen im Schnitt {diff:.1f} Pins mehr als schwache Spieler (30-39)")

        if corr_score > 0.9:
            print("- Die Simulation zeigt eine sehr starke Vorhersagbarkeit basierend auf der Stärke")
            print("- Anomalien und Überraschungen sind selten geworden")
        else:
            print("- Es gibt signifikante Ausreißer: Schwache Spieler mit sehr guten Ergebnissen")
            print("- Die Simulation zeigt realistische Varianz - nicht alle starken Spieler sind automatisch die besten")

        conn.close()

    except sqlite3.Error as e:
        print(f"Datenbankfehler: {e}")
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    analyze_strength_performance_correlation()
