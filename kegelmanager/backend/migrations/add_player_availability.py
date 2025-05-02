"""
Migration script to add the is_available_current_matchday column to the Player table.
"""

import os
import sys
import sqlite3

def run_migration(db_path):
    """
    Add the is_available_current_matchday column to the Player table.

    Args:
        db_path: Path to the database file

    Returns:
        bool: True if the migration was successful, False otherwise
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the column already exists
        cursor.execute("PRAGMA table_info(player)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'is_available_current_matchday' not in columns:
            # Add the column
            cursor.execute("ALTER TABLE player ADD COLUMN is_available_current_matchday BOOLEAN DEFAULT 1")

            # Set all existing players to be available
            cursor.execute("UPDATE player SET is_available_current_matchday = 1")
            conn.commit()

            print("Added is_available_current_matchday column to Player table")
        else:
            print("Column is_available_current_matchday already exists in Player table")

        conn.close()
        return True
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

def downgrade(db_path):
    """
    Remove the is_available_current_matchday column from the Player table.

    Args:
        db_path: Path to the database file

    Returns:
        bool: True if the downgrade was successful, False otherwise
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the column exists
        cursor.execute("PRAGMA table_info(player)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'is_available_current_matchday' in columns:
            # SQLite doesn't support dropping columns directly
            # We need to create a new table without the column and copy the data

            # Get all columns except the one we want to drop
            columns_to_keep = [col for col in columns if col != 'is_available_current_matchday']
            columns_str = ', '.join(columns_to_keep)

            # Create a new table without the column
            cursor.execute(f"CREATE TABLE player_new AS SELECT {columns_str} FROM player")

            # Drop the old table
            cursor.execute("DROP TABLE player")

            # Rename the new table
            cursor.execute("ALTER TABLE player_new RENAME TO player")

            conn.commit()
            print("Removed is_available_current_matchday column from Player table")
        else:
            print("Column is_available_current_matchday does not exist in Player table")

        conn.close()
        return True
    except Exception as e:
        print(f"Error during downgrade: {e}")
        return False

if __name__ == '__main__':
    # If the script is run directly, perform the upgrade
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default database path
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kegelmanager.db")

    run_migration(db_path)
