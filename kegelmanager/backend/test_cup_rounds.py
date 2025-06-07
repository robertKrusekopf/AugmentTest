#!/usr/bin/env python3
"""Test script to check cup round names after the fix."""

from app import app, db
from models import Cup, CupMatch, Season
import math

def test_cup_rounds():
    with app.app_context():
        # Aktuelle Saison finden
        current_season = Season.query.filter_by(is_current=True).first()
        if not current_season:
            print('Keine aktuelle Saison gefunden')
            return
        
        print(f'Aktuelle Saison: {current_season.name}')
        
        # Alle Pokale der aktuellen Saison anzeigen
        cups = Cup.query.filter_by(season_id=current_season.id).all()
        print(f'\nGefundene Pokale: {len(cups)}')
        
        for cup in cups:
            print(f'\n=== {cup.name} ===')
            print(f'Typ: {cup.cup_type}')
            print(f'Total Runden: {cup.total_rounds}')
            print(f'Aktuelle Runde: {cup.current_round} (Nummer: {cup.current_round_number})')
            print(f'Aktiv: {cup.is_active}')
            
            # Berechtige Teams
            eligible_teams = cup.get_eligible_teams()
            print(f'Berechtigte Teams: {len(eligible_teams)}')
            
            # Teste die neue Rundennamen-Logik
            if cup.total_rounds > 0:
                print('\nRundennamen-Test:')
                for round_num in range(1, cup.total_rounds + 1):
                    round_name = cup.get_round_name(round_num, cup.total_rounds)
                    teams_in_round = 2 ** (cup.total_rounds - round_num + 1)
                    print(f'  Runde {round_num}: {round_name} ({teams_in_round} Teams)')
            
            # Spiele anzeigen
            matches = CupMatch.query.filter_by(cup_id=cup.id).all()
            print(f'\nSpiele: {len(matches)}')
            
            # Gruppiere Spiele nach Runden
            rounds = {}
            for match in matches:
                if match.round_number not in rounds:
                    rounds[match.round_number] = []
                rounds[match.round_number].append(match)
            
            for round_num in sorted(rounds.keys()):
                round_matches = rounds[round_num]
                round_name = round_matches[0].round_name if round_matches else "?"
                print(f'  Runde {round_num} ({round_name}): {len(round_matches)} Spiele')
                for match in round_matches[:3]:  # Nur erste 3 Spiele anzeigen
                    home_name = match.home_team.name if match.home_team else 'Freilos'
                    away_name = match.away_team.name if match.away_team else 'Freilos'
                    status = 'gespielt' if match.is_played else 'offen'
                    print(f'    {home_name} vs {away_name} ({status})')
                if len(round_matches) > 3:
                    print(f'    ... und {len(round_matches) - 3} weitere')

def test_round_name_logic():
    """Test the round name logic with different team counts."""
    print('\n=== Test der Rundennamen-Logik ===')
    
    test_cases = [
        (2, 1),   # 2 Teams -> 1 Runde
        (4, 2),   # 4 Teams -> 2 Runden  
        (8, 3),   # 8 Teams -> 3 Runden
        (16, 4),  # 16 Teams -> 4 Runden
        (32, 5),  # 32 Teams -> 5 Runden
    ]
    
    with app.app_context():
        # Erstelle einen temporären Cup für Tests
        temp_cup = Cup(name="Test Cup", cup_type="Test", season_id=1)
        
        for num_teams, expected_rounds in test_cases:
            print(f'\n--- {num_teams} Teams (erwartet: {expected_rounds} Runden) ---')
            
            # Berechne total_rounds wie im echten Code
            next_power_of_2 = 2 ** math.ceil(math.log2(num_teams))
            total_rounds = int(math.log2(next_power_of_2))
            
            print(f'Berechnet: {total_rounds} Runden')
            
            if total_rounds == expected_rounds:
                print('✅ Rundenzahl korrekt')
            else:
                print(f'❌ Rundenzahl falsch! Erwartet: {expected_rounds}, Berechnet: {total_rounds}')
            
            # Teste Rundennamen
            for round_num in range(1, total_rounds + 1):
                round_name = temp_cup.get_round_name(round_num, total_rounds)
                teams_in_round = 2 ** (total_rounds - round_num + 1)
                print(f'  Runde {round_num}: {round_name} ({teams_in_round} Teams)')

if __name__ == '__main__':
    test_round_name_logic()
    test_cup_rounds()
