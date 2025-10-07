"""
Script to check the current game settings in the database.
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import GameSettings, Club


def check_game_settings():
    """Check the current game settings."""
    with app.app_context():
        print("=" * 60)
        print("Checking Game Settings")
        print("=" * 60)
        
        # Check if GameSettings table exists and has data
        settings = GameSettings.query.first()
        
        if not settings:
            print("\n❌ No game settings found in database!")
            print("Creating default settings...")
            settings = GameSettings(manager_club_id=None)
            db.session.add(settings)
            db.session.commit()
            print("✅ Default settings created")
        else:
            print(f"\n✅ Game settings found:")
            print(f"   ID: {settings.id}")
            print(f"   Manager Club ID: {settings.manager_club_id}")
            
            if settings.manager_club_id:
                club = Club.query.get(settings.manager_club_id)
                if club:
                    print(f"   Manager Club Name: {club.name}")
                else:
                    print(f"   ⚠️  Manager Club ID {settings.manager_club_id} not found!")
            else:
                print("   ℹ️  No manager club set (vereinslos)")
        
        # List all clubs
        print("\n" + "=" * 60)
        print("Available Clubs:")
        print("=" * 60)
        clubs = Club.query.order_by(Club.name).all()
        for club in clubs[:10]:  # Show first 10
            print(f"   ID {club.id}: {club.name}")
        
        if len(clubs) > 10:
            print(f"   ... and {len(clubs) - 10} more clubs")
        
        print("\n" + "=" * 60)


if __name__ == '__main__':
    check_game_settings()

