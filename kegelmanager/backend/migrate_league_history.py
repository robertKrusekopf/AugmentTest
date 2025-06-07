#!/usr/bin/env python3
"""
Migration script to create the LeagueHistory table.
This script should be run once to add the new table to existing databases.
"""

from flask import Flask
from models import db, LeagueHistory
import os

def create_app():
    """Create Flask app for migration."""
    app = Flask(__name__)
    
    # Database configuration
    database_path = os.path.join(os.path.dirname(__file__), 'kegelmanager.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def migrate_database():
    """Create the LeagueHistory table if it doesn't exist."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the table already exists
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'league_history' in existing_tables:
                print("LeagueHistory table already exists. No migration needed.")
                return
            
            print("Creating LeagueHistory table...")
            
            # Create the table
            db.create_all()
            
            print("LeagueHistory table created successfully!")
            print("\nTable structure:")
            print("- id: Primary key")
            print("- league_name: Name of the league")
            print("- league_level: Level of the league")
            print("- season_id: Foreign key to Season")
            print("- season_name: Name of the season")
            print("- team_id: Original team ID")
            print("- team_name: Name of the team")
            print("- club_name: Name of the club")
            print("- club_id: Club ID")
            print("- verein_id: Verein ID for emblems")
            print("- position: Final position in the table")
            print("- games_played: Number of games played")
            print("- wins: Number of wins")
            print("- draws: Number of draws")
            print("- losses: Number of losses")
            print("- table_points: Table points")
            print("- match_points_for: Match points for")
            print("- match_points_against: Match points against")
            print("- pins_for: Pins for")
            print("- pins_against: Pins against")
            print("- avg_home_score: Average home score")
            print("- avg_away_score: Average away score")
            print("- created_at: Creation timestamp")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            raise

if __name__ == '__main__':
    migrate_database()
