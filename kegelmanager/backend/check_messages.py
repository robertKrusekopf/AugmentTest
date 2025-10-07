"""
Script to check messages in the database.
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Message, GameSettings, Club, Player


def check_messages():
    """Check all messages in the database."""
    with app.app_context():
        print("=" * 60)
        print("Checking Messages in Database")
        print("=" * 60)
        
        # Check game settings
        settings = GameSettings.query.first()
        if settings and settings.manager_club_id:
            club = Club.query.get(settings.manager_club_id)
            print(f"\nManager Club: {club.name if club else 'Unknown'} (ID: {settings.manager_club_id})")
        else:
            print("\n⚠️  No manager club set!")
        
        # Get all messages
        messages = Message.query.order_by(Message.created_at.desc()).all()
        
        print(f"\nTotal messages in database: {len(messages)}")
        
        if not messages:
            print("\n❌ No messages found in database!")
            return
        
        print("\n" + "=" * 60)
        print("Messages:")
        print("=" * 60)
        
        for msg in messages:
            print(f"\nMessage ID: {msg.id}")
            print(f"  Subject: {msg.subject}")
            print(f"  Type: {msg.message_type}")
            print(f"  Read: {msg.is_read}")
            print(f"  Created: {msg.created_at}")
            print(f"  Related Club ID: {msg.related_club_id}")
            if msg.related_club_id:
                club = Club.query.get(msg.related_club_id)
                print(f"  Related Club Name: {club.name if club else 'Unknown'}")
            print(f"  Related Player ID: {msg.related_player_id}")
            if msg.related_player_id:
                player = Player.query.get(msg.related_player_id)
                print(f"  Related Player Name: {player.name if player else 'Unknown'}")
            print(f"  Content preview: {msg.content[:100]}...")
        
        print("\n" + "=" * 60)


if __name__ == '__main__':
    check_messages()

