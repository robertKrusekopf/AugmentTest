#!/usr/bin/env python3
"""
Analyse der Spielerverfügbarkeit und Zufallsereignisse
Wertet aus, wie oft Spieler an Spieltagen nicht verfügbar sind.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Player, Club, Team, Season, League, Match
from sqlalchemy import func, text
import random
from collections import defaultdict, Counter

# Import Flask app directly
import app as flask_app

def analyze_current_availability():
    """Analysiert die aktuelle Verfügbarkeit aller Spieler."""
    print("=== AKTUELLE SPIELERVERFÜGBARKEIT ===")
    
    # Gesamtanzahl Spieler
    total_players = Player.query.count()
    
    # Verfügbare vs. nicht verfügbare Spieler
    available_players = Player.query.filter_by(is_available_current_matchday=True).count()
    unavailable_players = Player.query.filter_by(is_available_current_matchday=False).count()
    
    print(f"Gesamtanzahl Spieler: {total_players}")
    print(f"Verfügbare Spieler: {available_players} ({available_players/total_players*100:.1f}%)")
    print(f"Nicht verfügbare Spieler: {unavailable_players} ({unavailable_players/total_players*100:.1f}%)")
    
    return {
        'total': total_players,
        'available': available_players,
        'unavailable': unavailable_players,
        'unavailable_percentage': unavailable_players/total_players*100 if total_players > 0 else 0
    }

def analyze_by_club():
    """Analysiert die Verfügbarkeit nach Vereinen aufgeschlüsselt."""
    print("\n=== VERFÜGBARKEIT NACH VEREINEN ===")
    
    clubs = Club.query.all()
    club_stats = []
    
    for club in clubs:
        total_players = Player.query.filter_by(club_id=club.id).count()
        if total_players == 0:
            continue
            
        available = Player.query.filter_by(
            club_id=club.id, 
            is_available_current_matchday=True
        ).count()
        unavailable = total_players - available
        unavailable_pct = (unavailable / total_players * 100) if total_players > 0 else 0
        
        # Anzahl Teams des Vereins
        teams_count = Team.query.filter_by(club_id=club.id).count()
        
        club_stats.append({
            'club_name': club.name,
            'total_players': total_players,
            'available': available,
            'unavailable': unavailable,
            'unavailable_pct': unavailable_pct,
            'teams_count': teams_count,
            'players_per_team': total_players / teams_count if teams_count > 0 else 0
        })
    
    # Sortiere nach Anzahl nicht verfügbarer Spieler
    club_stats.sort(key=lambda x: x['unavailable'], reverse=True)
    
    print(f"{'Verein':<30} {'Spieler':<8} {'Verfügbar':<10} {'Nicht verf.':<12} {'%':<6} {'Teams':<6}")
    print("-" * 80)
    
    for stats in club_stats:
        print(f"{stats['club_name']:<30} {stats['total_players']:<8} "
              f"{stats['available']:<10} {stats['unavailable']:<12} "
              f"{stats['unavailable_pct']:<6.1f} {stats['teams_count']:<6}")
    
    return club_stats

def simulate_availability_distribution(num_simulations=10000):
    """Simuliert die Verteilung der Spielerausfälle basierend auf 16.7% Wahrscheinlichkeit."""
    print(f"\n=== SIMULATION DER AUSFALLVERTEILUNG ({num_simulations:,} Simulationen) ===")
    
    # Beispiel: 100 Spieler
    num_players = 100
    unavailable_counts = []
    
    for _ in range(num_simulations):
        unavailable = 0
        for player in range(num_players):
            if random.random() < 0.167:  # 16.7% Chance
                unavailable += 1
        unavailable_counts.append(unavailable)
    
    # Statistiken berechnen
    avg_unavailable = sum(unavailable_counts) / len(unavailable_counts)
    min_unavailable = min(unavailable_counts)
    max_unavailable = max(unavailable_counts)
    
    # Verteilung zählen
    distribution = Counter(unavailable_counts)
    
    print(f"Bei {num_players} Spielern mit 16.7% Ausfallwahrscheinlichkeit:")
    print(f"Durchschnittlich nicht verfügbar: {avg_unavailable:.1f} Spieler ({avg_unavailable/num_players*100:.1f}%)")
    print(f"Minimum: {min_unavailable} Spieler")
    print(f"Maximum: {max_unavailable} Spieler")
    
    print(f"\nVerteilung der Ausfälle:")
    print(f"{'Ausfälle':<8} {'Häufigkeit':<10} {'Prozent':<8}")
    print("-" * 30)
    
    for unavailable in sorted(distribution.keys()):
        frequency = distribution[unavailable]
        percentage = frequency / num_simulations * 100
        print(f"{unavailable:<8} {frequency:<10} {percentage:<8.2f}%")
    
    return {
        'average': avg_unavailable,
        'min': min_unavailable,
        'max': max_unavailable,
        'distribution': distribution
    }

def analyze_teams_with_insufficient_players():
    """Analysiert Teams, die nicht genug verfügbare Spieler haben."""
    print("\n=== TEAMS MIT UNZUREICHEND VERFÜGBAREN SPIELERN ===")
    
    clubs = Club.query.all()
    problematic_teams = []
    
    for club in clubs:
        # Verfügbare Spieler des Vereins
        available_players = Player.query.filter_by(
            club_id=club.id,
            is_available_current_matchday=True
        ).count()
        
        # Teams des Vereins
        teams = Team.query.filter_by(club_id=club.id).all()
        teams_count = len(teams)
        
        if teams_count == 0:
            continue
            
        # Benötigte Spieler (6 pro Team)
        required_players = teams_count * 6
        
        if available_players < required_players:
            stroh_players_needed = required_players - available_players
            problematic_teams.append({
                'club_name': club.name,
                'teams_count': teams_count,
                'available_players': available_players,
                'required_players': required_players,
                'stroh_players_needed': stroh_players_needed,
                'teams': [team.name for team in teams]
            })
    
    if problematic_teams:
        print(f"{'Verein':<25} {'Teams':<6} {'Verfügbar':<10} {'Benötigt':<9} {'Stroh':<6}")
        print("-" * 65)
        
        for team_info in problematic_teams:
            print(f"{team_info['club_name']:<25} {team_info['teams_count']:<6} "
                  f"{team_info['available_players']:<10} {team_info['required_players']:<9} "
                  f"{team_info['stroh_players_needed']:<6}")
    else:
        print("Alle Vereine haben genügend verfügbare Spieler für ihre Teams.")
    
    return problematic_teams

def analyze_match_day_impact():
    """Analysiert den Einfluss der Ausfälle auf konkrete Spieltage."""
    print("\n=== AUSWIRKUNGEN AUF SPIELTAGE ===")
    
    # Aktuelle Saison finden
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        print("Keine aktuelle Saison gefunden.")
        return
    
    # Nächster Spieltag
    next_match_day_query = db.session.query(func.min(Match.match_day)).filter(
        Match.season_id == current_season.id,
        Match.is_played == False
    )
    next_match_day = next_match_day_query.scalar()
    
    if not next_match_day:
        print("Alle Spiele der Saison wurden bereits gespielt.")
        return
    
    print(f"Nächster Spieltag: {next_match_day}")
    
    # Matches des nächsten Spieltags
    matches = Match.query.filter(
        Match.season_id == current_season.id,
        Match.match_day == next_match_day,
        Match.is_played == False
    ).all()
    
    print(f"Anzahl Spiele am nächsten Spieltag: {len(matches)}")
    
    # Betroffene Vereine analysieren
    affected_clubs = set()
    for match in matches:
        affected_clubs.add(match.home_team.club_id)
        affected_clubs.add(match.away_team.club_id)
    
    print(f"Betroffene Vereine: {len(affected_clubs)}")
    
    # Für jeden betroffenen Verein prüfen
    clubs_needing_stroh = 0
    total_stroh_needed = 0
    
    for club_id in affected_clubs:
        club = Club.query.get(club_id)
        available_players = Player.query.filter_by(
            club_id=club_id,
            is_available_current_matchday=True
        ).count()
        
        # Teams des Vereins, die am nächsten Spieltag spielen
        teams_playing = 0
        for match in matches:
            if match.home_team.club_id == club_id:
                teams_playing += 1
            if match.away_team.club_id == club_id and match.away_team.club_id != match.home_team.club_id:
                teams_playing += 1
        
        required_players = teams_playing * 6
        
        if available_players < required_players:
            stroh_needed = required_players - available_players
            clubs_needing_stroh += 1
            total_stroh_needed += stroh_needed
            print(f"  {club.name}: {available_players}/{required_players} Spieler, {stroh_needed} Stroh-Spieler benötigt")
    
    print(f"\nZusammenfassung nächster Spieltag:")
    print(f"Vereine mit Stroh-Spieler-Bedarf: {clubs_needing_stroh}/{len(affected_clubs)}")
    print(f"Gesamt benötigte Stroh-Spieler: {total_stroh_needed}")
    
    return {
        'next_match_day': next_match_day,
        'total_matches': len(matches),
        'affected_clubs': len(affected_clubs),
        'clubs_needing_stroh': clubs_needing_stroh,
        'total_stroh_needed': total_stroh_needed
    }

def main():
    """Hauptfunktion für die Analyse."""

    with flask_app.app.app_context():
        print("ANALYSE DER SPIELERVERFÜGBARKEIT UND ZUFALLSEREIGNISSE")
        print("=" * 60)
        
        # 1. Aktuelle Verfügbarkeit
        current_stats = analyze_current_availability()
        
        # 2. Verfügbarkeit nach Vereinen
        club_stats = analyze_by_club()
        
        # 3. Simulation der theoretischen Verteilung
        simulation_stats = simulate_availability_distribution()
        
        # 4. Teams mit unzureichenden Spielern
        problematic_teams = analyze_teams_with_insufficient_players()
        
        # 5. Auswirkungen auf Spieltage
        match_day_impact = analyze_match_day_impact()
        
        # Zusammenfassung
        print("\n" + "=" * 60)
        print("ZUSAMMENFASSUNG")
        print("=" * 60)
        print(f"Theoretische Ausfallrate: 16.7%")
        print(f"Aktuelle Ausfallrate: {current_stats['unavailable_percentage']:.1f}%")
        print(f"Vereine mit Spielermangel: {len(problematic_teams)}")
        if match_day_impact:
            print(f"Stroh-Spieler am nächsten Spieltag: {match_day_impact['total_stroh_needed']}")

if __name__ == "__main__":
    main()
