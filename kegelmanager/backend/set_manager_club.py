"""
Script to manually set the manager club in the database.
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import GameSettings, Club


def set_manager_club(club_id):
    """Set the manager club in the database."""
    with app.app_context():
        print("=" * 60)
        print("Setting Manager Club")
        print("=" * 60)
        
        # Verify club exists
        club = Club.query.get(club_id)
        if not club:
            print(f"\n❌ Club with ID {club_id} not found!")
            print("\nAvailable clubs:")
            clubs = Club.query.order_by(Club.name).all()
            for c in clubs[:20]:
                print(f"   ID {c.id}: {c.name}")
            if len(clubs) > 20:
                print(f"   ... and {len(clubs) - 20} more clubs")
            return
        
        # Get or create settings
        settings = GameSettings.query.first()
        if not settings:
            settings = GameSettings()
            db.session.add(settings)
        
        # Update manager club
        settings.manager_club_id = club_id
        db.session.commit()
        
        print(f"\n✅ Manager club set to: {club.name} (ID: {club_id})")
        print("\nYou will now receive retirement notifications for players from this club!")
        print("=" * 60)


def list_clubs():
    """List all clubs."""
    with app.app_context():
        print("=" * 60)
        print("Available Clubs")
        print("=" * 60)
        
        clubs = Club.query.order_by(Club.name).all()
        for club in clubs:
            print(f"   ID {club.id}: {club.name}")
        
        print(f"\nTotal: {len(clubs)} clubs")
        print("=" * 60)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python set_manager_club.py <club_id>    - Set manager club")
        print("  python set_manager_club.py list         - List all clubs")
        print("\nExample:")
        print("  python set_manager_club.py 41")
        sys.exit(1)
    
    if sys.argv[1].lower() == 'list':
        list_clubs()
    else:
        try:
            club_id = int(sys.argv[1])
            set_manager_club(club_id)
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid club ID")
            print("Use 'python set_manager_club.py list' to see all clubs")

