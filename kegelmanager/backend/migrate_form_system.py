"""
Migration script to add form system fields to the Player table.

This script adds the following fields to the Player table:
- form_short_term (Float): Short-term form modifier (-20 to +20)
- form_medium_term (Float): Medium-term form modifier (-15 to +15)
- form_long_term (Float): Long-term form modifier (-10 to +10)
- form_short_remaining_days (Integer): Remaining days for short-term form
- form_medium_remaining_days (Integer): Remaining days for medium-term form
- form_long_remaining_days (Integer): Remaining days for long-term form

Run this script after updating the models.py file to add the form system.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Player
from sqlalchemy import text
import random


def check_columns_exist():
    """Check if the form system columns already exist in the database."""
    try:
        # Try to query one of the new columns
        result = db.session.execute(text("SELECT form_short_term FROM player LIMIT 1"))
        return True
    except Exception:
        return False


def add_form_columns():
    """Add the form system columns to the Player table."""
    print("Adding form system columns to Player table...")
    
    try:
        # Add the new columns with default values
        db.session.execute(text("""
            ALTER TABLE player 
            ADD COLUMN form_short_term REAL DEFAULT 0.0
        """))
        
        db.session.execute(text("""
            ALTER TABLE player 
            ADD COLUMN form_medium_term REAL DEFAULT 0.0
        """))
        
        db.session.execute(text("""
            ALTER TABLE player 
            ADD COLUMN form_long_term REAL DEFAULT 0.0
        """))
        
        db.session.execute(text("""
            ALTER TABLE player 
            ADD COLUMN form_short_remaining_days INTEGER DEFAULT 0
        """))
        
        db.session.execute(text("""
            ALTER TABLE player 
            ADD COLUMN form_medium_remaining_days INTEGER DEFAULT 0
        """))
        
        db.session.execute(text("""
            ALTER TABLE player 
            ADD COLUMN form_long_remaining_days INTEGER DEFAULT 0
        """))
        
        db.session.commit()
        print("✓ Form system columns added successfully")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error adding form system columns: {str(e)}")
        return False


def initialize_random_form():
    """Initialize random form values for existing players."""
    print("Initializing random form values for existing players...")
    
    try:
        players = Player.query.all()
        updated_count = 0
        
        for player in players:
            # 30% chance to start with short-term form
            if random.random() < 0.30:
                player.form_short_term = round(random.uniform(-20, 20), 2)
                player.form_short_remaining_days = random.randint(1, 3)
            
            # 20% chance to start with medium-term form
            if random.random() < 0.20:
                player.form_medium_term = round(random.uniform(-15, 15), 2)
                player.form_medium_remaining_days = random.randint(4, 8)
            
            # 10% chance to start with long-term form
            if random.random() < 0.10:
                player.form_long_term = round(random.uniform(-10, 10), 2)
                player.form_long_remaining_days = random.randint(10, 20)
            
            # Only count players who got some form
            if (player.form_short_term != 0 or player.form_medium_term != 0 or 
                player.form_long_term != 0):
                updated_count += 1
        
        db.session.commit()
        print(f"✓ Initialized random form for {updated_count} out of {len(players)} players")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error initializing random form: {str(e)}")
        return False


def verify_migration():
    """Verify that the migration was successful."""
    print("Verifying migration...")
    
    try:
        # Check if we can query the new columns
        result = db.session.execute(text("""
            SELECT COUNT(*) as total_players,
                   COUNT(CASE WHEN form_short_term != 0 THEN 1 END) as short_form_players,
                   COUNT(CASE WHEN form_medium_term != 0 THEN 1 END) as medium_form_players,
                   COUNT(CASE WHEN form_long_term != 0 THEN 1 END) as long_form_players
            FROM player
        """)).fetchone()
        
        print(f"✓ Migration verification successful:")
        print(f"  - Total players: {result.total_players}")
        print(f"  - Players with short-term form: {result.short_form_players}")
        print(f"  - Players with medium-term form: {result.medium_form_players}")
        print(f"  - Players with long-term form: {result.long_form_players}")
        
        return True
        
    except Exception as e:
        print(f"✗ Migration verification failed: {str(e)}")
        return False


def main():
    """Main migration function."""
    print("=== Form System Migration ===")
    print("This script will add form system fields to the Player table.")
    
    # Initialize the database connection
    from app import app
    with app.app_context():
        # Check if columns already exist
        if check_columns_exist():
            print("✓ Form system columns already exist in the database")
            
            # Ask if user wants to reinitialize form values
            response = input("Do you want to reinitialize random form values? (y/N): ")
            if response.lower() == 'y':
                if initialize_random_form():
                    verify_migration()
            else:
                print("Migration skipped - columns already exist")
            return
        
        # Add the new columns
        if not add_form_columns():
            print("Migration failed - could not add columns")
            return
        
        # Initialize random form values
        if not initialize_random_form():
            print("Migration partially failed - columns added but form initialization failed")
            return
        
        # Verify the migration
        if verify_migration():
            print("✓ Form system migration completed successfully!")
        else:
            print("✗ Migration completed but verification failed")


if __name__ == "__main__":
    main()
