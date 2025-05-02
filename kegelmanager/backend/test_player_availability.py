"""
Test script for the player availability system.
"""

import os
import sys
import random
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from the parent directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Player, Team, Club, Match, Season, League
from simulation import determine_player_availability, reset_player_availability, simulate_match

def test_player_availability():
    """Test the player availability system."""
    # Create a Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    db.init_app(app)
    
    with app.app_context():
        # Reset player availability flags
        reset_player_availability()
        
        # Get all clubs
        clubs = Club.query.all()
        
        if not clubs:
            print("No clubs found in the database.")
            return
        
        # Select a random club for testing
        club = random.choice(clubs)
        
        # Get all players from this club
        players = Player.query.filter_by(club_id=club.id).all()
        
        if not players:
            print(f"No players found for club {club.name} (ID: {club.id}).")
            return
        
        # Get all teams from this club
        teams = Team.query.filter_by(club_id=club.id).all()
        
        if not teams:
            print(f"No teams found for club {club.name} (ID: {club.id}).")
            return
        
        print(f"Testing player availability for club {club.name} (ID: {club.id})")
        print(f"Club has {len(players)} players and {len(teams)} teams")
        
        # Print player information before determining availability
        print("\nPlayers before determining availability:")
        for i, player in enumerate(players):
            print(f"{i+1}. {player.name} (ID: {player.id}, Strength: {player.strength}, Available: {player.is_available_current_matchday})")
        
        # Determine player availability
        determine_player_availability(club.id, len(teams))
        
        # Get updated player information
        players = Player.query.filter_by(club_id=club.id).all()
        
        # Print player information after determining availability
        print("\nPlayers after determining availability:")
        for i, player in enumerate(players):
            print(f"{i+1}. {player.name} (ID: {player.id}, Strength: {player.strength}, Available: {player.is_available_current_matchday})")
        
        # Count available and unavailable players
        available_players = [p for p in players if p.is_available_current_matchday]
        unavailable_players = [p for p in players if not p.is_available_current_matchday]
        
        print(f"\nAvailable players: {len(available_players)}")
        print(f"Unavailable players: {len(unavailable_players)}")
        print(f"Unavailability rate: {len(unavailable_players) / len(players) * 100:.1f}%")
        
        # Check if we have enough available players for all teams
        min_players_needed = len(teams) * 6
        print(f"\nMinimum players needed for {len(teams)} teams: {min_players_needed}")
        print(f"Available players: {len(available_players)}")
        
        if len(available_players) >= min_players_needed:
            print("✅ We have enough available players for all teams")
        else:
            print("❌ We don't have enough available players for all teams")
        
        # Test player assignment to teams
        if len(teams) >= 2 and len(available_players) >= 12:
            # Get two teams from the club
            team1 = teams[0]
            team2 = teams[1]
            
            print(f"\nTesting player assignment for teams {team1.name} and {team2.name}")
            
            # Create a dummy match for each team
            dummy_opponent1 = Team.query.filter(Team.club_id != club.id).first()
            dummy_opponent2 = Team.query.filter(Team.club_id != club.id, Team.id != dummy_opponent1.id).first()
            
            if dummy_opponent1 and dummy_opponent2:
                # Simulate matches to see which players are assigned to which team
                print(f"\nSimulating match for {team1.name} vs {dummy_opponent1.name}")
                match_result1 = simulate_match(team1, dummy_opponent1)
                
                # Get the players who played in the first match
                players_team1 = Player.query.filter_by(club_id=club.id, has_played_current_matchday=True).all()
                
                print(f"Players assigned to {team1.name}:")
                for i, player in enumerate(players_team1):
                    print(f"{i+1}. {player.name} (ID: {player.id}, Strength: {player.strength})")
                
                # Reset player flags
                for player in players_team1:
                    player.has_played_current_matchday = False
                db.session.commit()
                
                print(f"\nSimulating match for {team2.name} vs {dummy_opponent2.name}")
                match_result2 = simulate_match(team2, dummy_opponent2)
                
                # Get the players who played in the second match
                players_team2 = Player.query.filter_by(club_id=club.id, has_played_current_matchday=True).all()
                
                print(f"Players assigned to {team2.name}:")
                for i, player in enumerate(players_team2):
                    print(f"{i+1}. {player.name} (ID: {player.id}, Strength: {player.strength})")
                
                # Check if the best players were assigned to the first team
                avg_strength_team1 = sum(p.strength for p in players_team1) / len(players_team1)
                avg_strength_team2 = sum(p.strength for p in players_team2) / len(players_team2)
                
                print(f"\nAverage strength of {team1.name}: {avg_strength_team1:.1f}")
                print(f"Average strength of {team2.name}: {avg_strength_team2:.1f}")
                
                if avg_strength_team1 > avg_strength_team2:
                    print("✅ The best players were assigned to the first team")
                else:
                    print("❌ The best players were not assigned to the first team")
            else:
                print("Not enough opponent teams found for testing.")
        else:
            print("Not enough teams or available players for testing player assignment.")

if __name__ == '__main__':
    test_player_availability()
