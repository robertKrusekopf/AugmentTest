"""
Test script to verify the performance improvements in player flag reset operations.
"""

from flask import Flask
from models import db, Player
import time
from simulation import reset_player_availability, reset_player_matchday_flags

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def test_reset_player_availability():
    """Test the performance of reset_player_availability function."""
    with app.app_context():
        # Get the total number of players
        total_players = Player.query.count()
        print(f"Total players in database: {total_players}")
        
        # Test the optimized function
        start_time = time.time()
        reset_player_availability()
        end_time = time.time()
        
        print(f"Time to reset availability flags for all players: {end_time - start_time:.4f} seconds")

def test_reset_player_matchday_flags():
    """Test the performance of reset_player_matchday_flags function."""
    with app.app_context():
        # First, set some players to have played
        player_count = Player.query.count()
        players_to_mark = min(player_count, 100)  # Mark up to 100 players
        
        # Mark some players as having played
        players = Player.query.limit(players_to_mark).all()
        for player in players:
            player.has_played_current_matchday = True
        db.session.commit()
        
        print(f"Marked {players_to_mark} players as having played")
        
        # Test the optimized function
        start_time = time.time()
        reset_player_matchday_flags()
        end_time = time.time()
        
        print(f"Time to reset match day flags: {end_time - start_time:.4f} seconds")
        
        # Verify all players are reset
        players_played = Player.query.filter_by(has_played_current_matchday=True).count()
        print(f"Players still marked as having played: {players_played}")

if __name__ == "__main__":
    print("Testing reset_player_availability function...")
    test_reset_player_availability()
    
    print("\nTesting reset_player_matchday_flags function...")
    test_reset_player_matchday_flags()
