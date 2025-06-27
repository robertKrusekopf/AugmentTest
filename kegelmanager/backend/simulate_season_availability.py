#!/usr/bin/env python3
"""
Simulation der Spielerverfügbarkeit über eine komplette Saison
Analysiert, wie sich die 16.7% Ausfallwahrscheinlichkeit über mehrere Spieltage auswirkt.
"""

import random
import statistics
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import numpy as np

def simulate_player_availability_season(num_players=100, num_match_days=22, num_simulations=1000):
    """
    Simuliert die Spielerverfügbarkeit über eine komplette Saison.
    
    Args:
        num_players: Anzahl Spieler im Verein
        num_match_days: Anzahl Spieltage in der Saison
        num_simulations: Anzahl Simulationen
    
    Returns:
        Dictionary mit Statistiken
    """
    print(f"Simuliere {num_simulations:,} Saisons mit {num_players} Spielern über {num_match_days} Spieltage")
    print(f"Ausfallwahrscheinlichkeit pro Spieler und Spieltag: 16.7%")
    print("=" * 80)
    
    # Statistiken sammeln
    season_stats = []
    match_day_unavailable_counts = defaultdict(list)
    player_unavailable_counts = defaultdict(int)
    
    for simulation in range(num_simulations):
        season_unavailable_total = 0
        season_unavailable_by_match_day = []
        player_unavailable_this_season = [0] * num_players
        
        for match_day in range(1, num_match_days + 1):
            unavailable_this_match_day = 0
            
            for player_id in range(num_players):
                # 16.7% Chance, dass Spieler nicht verfügbar ist
                if random.random() < 0.167:
                    unavailable_this_match_day += 1
                    season_unavailable_total += 1
                    player_unavailable_this_season[player_id] += 1
            
            season_unavailable_by_match_day.append(unavailable_this_match_day)
            match_day_unavailable_counts[match_day].append(unavailable_this_match_day)
        
        # Statistiken für diese Saison
        season_stats.append({
            'total_unavailable_events': season_unavailable_total,
            'avg_per_match_day': season_unavailable_total / num_match_days,
            'max_per_match_day': max(season_unavailable_by_match_day),
            'min_per_match_day': min(season_unavailable_by_match_day),
            'player_unavailable_counts': player_unavailable_this_season
        })
        
        # Zähle, wie oft jeder Spieler in dieser Saison ausgefallen ist
        for player_id, count in enumerate(player_unavailable_this_season):
            player_unavailable_counts[count] += 1
    
    return season_stats, match_day_unavailable_counts, player_unavailable_counts

def analyze_season_statistics(season_stats, num_players, num_match_days):
    """Analysiert die Saisonstatistiken."""
    print("SAISONSTATISTIKEN")
    print("=" * 50)
    
    # Gesamtausfälle pro Saison
    total_unavailable = [s['total_unavailable_events'] for s in season_stats]
    avg_total = statistics.mean(total_unavailable)
    median_total = statistics.median(total_unavailable)
    min_total = min(total_unavailable)
    max_total = max(total_unavailable)
    
    print(f"Ausfälle pro Saison (gesamt):")
    print(f"  Durchschnitt: {avg_total:.1f}")
    print(f"  Median: {median_total:.1f}")
    print(f"  Minimum: {min_total}")
    print(f"  Maximum: {max_total}")
    print(f"  Theoretischer Erwartungswert: {num_players * num_match_days * 0.167:.1f}")
    
    # Durchschnittliche Ausfälle pro Spieltag
    avg_per_match_day = [s['avg_per_match_day'] for s in season_stats]
    avg_avg = statistics.mean(avg_per_match_day)
    
    print(f"\nAusfälle pro Spieltag (Durchschnitt):")
    print(f"  Durchschnitt: {avg_avg:.1f}")
    print(f"  Theoretischer Erwartungswert: {num_players * 0.167:.1f}")
    
    # Maximum pro Spieltag
    max_per_match_day = [s['max_per_match_day'] for s in season_stats]
    avg_max = statistics.mean(max_per_match_day)
    overall_max = max(max_per_match_day)
    
    print(f"\nMaximale Ausfälle an einem Spieltag:")
    print(f"  Durchschnittliches Maximum: {avg_max:.1f}")
    print(f"  Absolutes Maximum: {overall_max}")

def analyze_match_day_patterns(match_day_unavailable_counts, num_match_days):
    """Analysiert Muster über die Spieltage."""
    print("\nSPIELTAG-MUSTER")
    print("=" * 50)
    
    print(f"{'Spieltag':<10} {'Durchschnitt':<12} {'Min':<5} {'Max':<5} {'Std.Abw.':<8}")
    print("-" * 50)
    
    for match_day in range(1, num_match_days + 1):
        counts = match_day_unavailable_counts[match_day]
        avg = statistics.mean(counts)
        min_val = min(counts)
        max_val = max(counts)
        std_dev = statistics.stdev(counts) if len(counts) > 1 else 0
        
        print(f"{match_day:<10} {avg:<12.1f} {min_val:<5} {max_val:<5} {std_dev:<8.1f}")

def analyze_player_patterns(player_unavailable_counts, num_players, num_simulations, num_match_days):
    """Analysiert, wie oft einzelne Spieler über die Saison ausfallen."""
    print("\nSPIELER-AUSFALLMUSTER")
    print("=" * 50)
    
    print("Verteilung: Wie oft fällt ein Spieler in einer Saison aus?")
    print(f"{'Ausfälle':<10} {'Anzahl Spieler':<15} {'Prozent':<10} {'Kumulativ':<10}")
    print("-" * 50)
    
    total_player_seasons = num_players * num_simulations
    cumulative = 0
    
    for unavailable_count in sorted(player_unavailable_counts.keys()):
        count = player_unavailable_counts[unavailable_count]
        percentage = count / total_player_seasons * 100
        cumulative += percentage
        
        print(f"{unavailable_count:<10} {count:<15} {percentage:<10.1f}% {cumulative:<10.1f}%")
    
    # Theoretische Erwartung
    expected_avg = num_match_days * 0.167
    print(f"\nTheoretischer Erwartungswert pro Spieler: {expected_avg:.1f} Ausfälle pro Saison")

def analyze_team_impact(num_players=100, teams_per_club=2, num_match_days=22, num_simulations=1000):
    """Analysiert die Auswirkungen auf Teams (6 Spieler pro Team)."""
    print("\nAUSWIRKUNGEN AUF TEAMS")
    print("=" * 50)
    
    players_per_team = 6
    total_teams = teams_per_club
    
    print(f"Annahmen:")
    print(f"  - {num_players} Spieler im Verein")
    print(f"  - {total_teams} Teams")
    print(f"  - {players_per_team} Spieler pro Team benötigt")
    print(f"  - Spieler werden nach Stärke auf Teams verteilt")
    
    stroh_needed_stats = []
    
    for simulation in range(num_simulations):
        season_stroh_total = 0
        
        for match_day in range(num_match_days):
            # Simuliere Verfügbarkeit
            available_players = 0
            for player in range(num_players):
                if random.random() >= 0.167:  # Spieler ist verfügbar
                    available_players += 1
            
            # Berechne benötigte Stroh-Spieler
            required_players = total_teams * players_per_team
            if available_players < required_players:
                stroh_needed = required_players - available_players
                season_stroh_total += stroh_needed
        
        stroh_needed_stats.append(season_stroh_total)
    
    avg_stroh = statistics.mean(stroh_needed_stats)
    max_stroh = max(stroh_needed_stats)
    seasons_with_stroh = sum(1 for s in stroh_needed_stats if s > 0)
    
    print(f"\nErgebnisse über {num_simulations:,} Saisons:")
    print(f"  Durchschnittlich benötigte Stroh-Spieler pro Saison: {avg_stroh:.1f}")
    print(f"  Maximum Stroh-Spieler in einer Saison: {max_stroh}")
    print(f"  Saisons mit Stroh-Spieler-Bedarf: {seasons_with_stroh}/{num_simulations} ({seasons_with_stroh/num_simulations*100:.1f}%)")

def main():
    """Hauptfunktion für die Simulation."""
    print("SIMULATION DER SPIELERVERFÜGBARKEIT ÜBER EINE SAISON")
    print("=" * 80)
    
    # Parameter
    num_players = 100
    num_match_days = 22  # Typische Anzahl Spieltage in einer Saison
    num_simulations = 1000
    
    # Simulation durchführen
    season_stats, match_day_counts, player_counts = simulate_player_availability_season(
        num_players, num_match_days, num_simulations
    )
    
    # Analysen
    analyze_season_statistics(season_stats, num_players, num_match_days)
    analyze_match_day_patterns(match_day_counts, num_match_days)
    analyze_player_patterns(player_counts, num_players, num_simulations, num_match_days)
    analyze_team_impact(num_players, teams_per_club=2, num_match_days=num_match_days, num_simulations=num_simulations)
    
    print("\n" + "=" * 80)
    print("FAZIT")
    print("=" * 80)
    print("Die 16.7% Ausfallwahrscheinlichkeit pro Spieler und Spieltag führt zu:")
    print(f"- Durchschnittlich ~{num_players * 0.167:.0f} Ausfällen pro Spieltag")
    print(f"- Durchschnittlich ~{num_players * num_match_days * 0.167:.0f} Ausfällen pro Saison")
    print("- Gelegentlichem Bedarf an Stroh-Spielern bei Vereinen mit wenigen Spielern")
    print("- Relativ gleichmäßiger Verteilung über die Saison")

if __name__ == "__main__":
    main()
