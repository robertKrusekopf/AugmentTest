"""
Migration script to add the is_substitute field to the PlayerMatchPerformance table.
"""
import sqlite3
import os
import sys

def run_migration(db_path):
    """
    Add the is_substitute column to the PlayerMatchPerformance table.
    
    Args:
        db_path: Path to the SQLite database file
    """
    print(f"Running migration on database: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(player_match_performance)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'is_substitute' not in column_names:
            print("Adding 'is_substitute' column to player_match_performance table...")
            cursor.execute("ALTER TABLE player_match_performance ADD COLUMN is_substitute BOOLEAN DEFAULT 0")
            conn.commit()
            print("Migration completed successfully.")
        else:
            print("Column 'is_substitute' already exists. No migration needed.")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    # Get the database path from command line arguments or use default
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kegelmanager.db")
    
    success = run_migration(db_path)
    
    if success:
        print("Migration completed successfully.")
        sys.exit(0)
    else:
        print("Migration failed.")
        sys.exit(1)
