#!/usr/bin/env python3
"""
Erstellt visuelle Darstellungen des Zusammenhangs zwischen Spielerstärke und Ergebnissen.
"""

import sqlite3
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def create_visualizations():
    """Erstellt verschiedene Visualisierungen der Stärke-Leistung-Korrelation."""
    
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
        
        print("Erstelle Visualisierungen...")
        
        # Daten für Scatter Plot laden
        scatter_query = """
        SELECT 
            p.strength,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            COUNT(perf.id) as spiele,
            p.name
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength IS NOT NULL
        GROUP BY p.id, p.name, p.strength
        HAVING COUNT(perf.id) >= 5
        """
        
        cursor.execute(scatter_query)
        scatter_data = cursor.fetchall()
        
        if not scatter_data:
            print("Keine Daten für Visualisierung gefunden!")
            return
        
        # Daten extrahieren
        strengths = [row[0] for row in scatter_data]
        avg_scores = [row[1] for row in scatter_data]
        game_counts = [row[2] for row in scatter_data]
        names = [row[3] for row in scatter_data]
        
        # Matplotlib Style setzen
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Figure mit Subplots erstellen
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Bowling Simulation: Zusammenhang Spielerstärke und Leistung', fontsize=16, fontweight='bold')
        
        # 1. Scatter Plot: Stärke vs. Durchschnittsergebnis
        ax1.scatter(strengths, avg_scores, alpha=0.6, s=50)
        
        # Trendlinie hinzufügen
        z = np.polyfit(strengths, avg_scores, 1)
        p = np.poly1d(z)
        ax1.plot(strengths, p(strengths), "r--", alpha=0.8, linewidth=2)
        
        # Korrelationskoeffizient berechnen und anzeigen
        corr = np.corrcoef(strengths, avg_scores)[0, 1]
        ax1.text(0.05, 0.95, f'Korrelation: {corr:.3f}', transform=ax1.transAxes, 
                bbox=dict(boxstyle="round", facecolor='wheat', alpha=0.8))
        
        ax1.set_xlabel('Spielerstärke')
        ax1.set_ylabel('Durchschnittsergebnis (Pins)')
        ax1.set_title('Stärke vs. Durchschnittsergebnis')
        ax1.grid(True, alpha=0.3)
        
        # 2. Box Plot: Ergebnisse nach Stärke-Kategorien
        category_query = """
        SELECT 
            CASE 
                WHEN p.strength >= 80 THEN '80-99\n(Elite)'
                WHEN p.strength >= 70 THEN '70-79\n(Sehr gut)'
                WHEN p.strength >= 60 THEN '60-69\n(Gut)'
                WHEN p.strength >= 50 THEN '50-59\n(Durchschnitt)'
                WHEN p.strength >= 40 THEN '40-49\n(Unterdurchschnitt)'
                ELSE '30-39\n(Schwach)'
            END as kategorie,
            perf.total_score
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength IS NOT NULL
        """
        
        cursor.execute(category_query)
        category_data = cursor.fetchall()
        
        # Daten für Box Plot gruppieren
        categories = ['30-39\n(Schwach)', '40-49\n(Unterdurchschnitt)', '50-59\n(Durchschnitt)', 
                     '60-69\n(Gut)', '70-79\n(Sehr gut)', '80-99\n(Elite)']
        category_scores = {cat: [] for cat in categories}
        
        for cat, score in category_data:
            if cat in category_scores:
                category_scores[cat].append(score)
        
        # Box Plot erstellen
        box_data = [category_scores[cat] for cat in categories if category_scores[cat]]
        box_labels = [cat for cat in categories if category_scores[cat]]
        
        bp = ax2.boxplot(box_data, labels=box_labels, patch_artist=True)
        
        # Farben für Box Plot
        colors = ['lightcoral', 'lightblue', 'lightgreen', 'lightyellow', 'lightpink', 'lightgray']
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
        
        ax2.set_ylabel('Ergebnis (Pins)')
        ax2.set_title('Ergebnisverteilung nach Stärke-Kategorien')
        ax2.grid(True, alpha=0.3)
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        # 3. Histogram: Verteilung der Spielerstärken
        ax3.hist(strengths, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.axvline(np.mean(strengths), color='red', linestyle='--', linewidth=2, 
                   label=f'Durchschnitt: {np.mean(strengths):.1f}')
        ax3.set_xlabel('Spielerstärke')
        ax3.set_ylabel('Anzahl Spieler')
        ax3.set_title('Verteilung der Spielerstärken')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Korrelations-Heatmap für alle Attribute
        attr_query = """
        SELECT 
            p.strength,
            p.konstanz,
            p.drucksicherheit,
            p.volle,
            p.raeumer,
            p.ausdauer,
            ROUND(AVG(perf.total_score), 1) as avg_score,
            ROUND(AVG(perf.fehler_count), 1) as avg_fehler
        FROM player p
        JOIN player_match_performance perf ON p.id = perf.player_id
        WHERE p.strength IS NOT NULL
        GROUP BY p.id, p.strength, p.konstanz, p.drucksicherheit, p.volle, p.raeumer, p.ausdauer
        HAVING COUNT(perf.id) >= 5
        """
        
        cursor.execute(attr_query)
        attr_data = cursor.fetchall()
        
        if attr_data:
            # Daten in Arrays umwandeln
            attr_array = np.array(attr_data)
            
            # Korrelationsmatrix berechnen
            corr_matrix = np.corrcoef(attr_array.T)
            
            # Labels für die Heatmap
            labels = ['Stärke', 'Konstanz', 'Drucksicherheit', 'Volle', 'Räumer', 
                     'Ausdauer', 'Ø Score', 'Ø Fehler']
            
            # Heatmap erstellen
            im = ax4.imshow(corr_matrix, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
            
            # Ticks und Labels setzen
            ax4.set_xticks(range(len(labels)))
            ax4.set_yticks(range(len(labels)))
            ax4.set_xticklabels(labels, rotation=45, ha='right')
            ax4.set_yticklabels(labels)
            
            # Korrelationswerte in die Zellen schreiben
            for i in range(len(labels)):
                for j in range(len(labels)):
                    text = ax4.text(j, i, f'{corr_matrix[i, j]:.2f}',
                                   ha="center", va="center", color="black", fontsize=8)
            
            ax4.set_title('Korrelationsmatrix aller Attribute')
            
            # Colorbar hinzufügen
            cbar = plt.colorbar(im, ax=ax4, shrink=0.8)
            cbar.set_label('Korrelationskoeffizient')
        
        # Layout anpassen
        plt.tight_layout()
        
        # Grafik speichern
        output_path = os.path.join(os.path.dirname(__file__), 'strength_correlation_analysis.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Visualisierung gespeichert: {output_path}")
        
        # Grafik anzeigen
        plt.show()
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Datenbankfehler: {e}")
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        create_visualizations()
    except ImportError as e:
        print(f"Fehler beim Importieren der Bibliotheken: {e}")
        print("Bitte installieren Sie die erforderlichen Bibliotheken:")
        print("pip install matplotlib seaborn scipy")
