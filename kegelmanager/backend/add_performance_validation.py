#!/usr/bin/env python3
"""
Script to add database validation to prevent invalid PlayerMatchPerformance records.

This script adds a check constraint to ensure that the team_id in PlayerMatchPerformance
records always matches either the home_team_id or away_team_id of the associated match.
"""

import sqlite3
import os
from datetime import datetime

def get_database_path():
    """Get the current database path from .env file."""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("DATABASE_PATH="):
                    db_path = line.split("=", 1)[1].strip()
                    if os.path.exists(db_path):
                        return db_path
                    else:
                        raise FileNotFoundError(f"Datenbank aus .env-Datei existiert nicht: {db_path}")

    raise FileNotFoundError(
        "Keine DATABASE_PATH in .env-Datei gefunden. "
        "Bitte konfigurieren Sie DATABASE_PATH in der .env-Datei."
    )

def backup_database(db_path):
    """Create a backup of the database before making changes."""
    backup_path = db_path.replace('.db', f'_backup_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    print(f"Creating backup: {backup_path}")
    
    # Copy the database file
    import shutil
    shutil.copy2(db_path, backup_path)
    
    print(f"Backup created successfully: {backup_path}")
    return backup_path

def add_validation_constraint(db_path):
    """Add validation triggers to prevent invalid PlayerMatchPerformance records."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Adding validation triggers to PlayerMatchPerformance table...")

    try:
        # Check if triggers already exist
        cursor.execute('''
            SELECT name FROM sqlite_master
            WHERE type='trigger' AND name LIKE 'validate_performance_%'
        ''')
        existing_triggers = cursor.fetchall()

        if existing_triggers:
            print("✅ Validation triggers already exist!")
            for trigger in existing_triggers:
                print(f"   - {trigger[0]}")
            conn.close()
            return

        print("Creating validation triggers...")

        # Trigger for INSERT operations
        cursor.execute('''
            CREATE TRIGGER validate_performance_insert
            BEFORE INSERT ON player_match_performance
            FOR EACH ROW
            BEGIN
                SELECT CASE
                    WHEN NEW.team_id NOT IN (
                        SELECT home_team_id FROM match WHERE id = NEW.match_id
                        UNION
                        SELECT away_team_id FROM match WHERE id = NEW.match_id
                    )
                    THEN RAISE(ABORT, 'Invalid team_id: team must be either home or away team in the match')
                END;
            END
        ''')

        # Trigger for UPDATE operations
        cursor.execute('''
            CREATE TRIGGER validate_performance_update
            BEFORE UPDATE ON player_match_performance
            FOR EACH ROW
            BEGIN
                SELECT CASE
                    WHEN NEW.team_id NOT IN (
                        SELECT home_team_id FROM match WHERE id = NEW.match_id
                        UNION
                        SELECT away_team_id FROM match WHERE id = NEW.match_id
                    )
                    THEN RAISE(ABORT, 'Invalid team_id: team must be either home or away team in the match')
                END;
            END
        ''')

        conn.commit()
        print("✅ Validation triggers added successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error adding validation triggers: {str(e)}")
        raise
    finally:
        conn.close()

def test_validation(db_path):
    """Test that the validation constraint works by trying to insert an invalid record."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nTesting validation constraint...")
    
    try:
        # Try to insert an invalid record (team_id that doesn't match the match)
        cursor.execute('''
            INSERT INTO player_match_performance 
            (player_id, match_id, team_id, is_home_team, position_number, total_score)
            VALUES (1, 1, 999999, 1, 1, 100)
        ''')
        
        conn.commit()
        print("❌ Validation constraint is NOT working - invalid record was inserted!")
        
        # Clean up the test record
        cursor.execute("DELETE FROM player_match_performance WHERE team_id = 999999")
        conn.commit()
        
    except sqlite3.IntegrityError as e:
        print("✅ Validation constraint is working - invalid record was rejected!")
        print(f"   Error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error during validation test: {str(e)}")
    finally:
        conn.close()

def main():
    """Main function to add validation constraint."""
    print("BOWLING SIMULATION - ADD PERFORMANCE VALIDATION")
    print("=" * 60)
    
    db_path = get_database_path()
    print(f"Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found: {db_path}")
        return
    
    # Step 1: Create backup
    backup_path = backup_database(db_path)
    
    # Step 2: Add validation constraint
    try:
        add_validation_constraint(db_path)
        
        # Step 3: Test the validation
        test_validation(db_path)
        
        print(f"\nBackup saved at: {backup_path}")
        print("Validation constraint added successfully!")
        
    except Exception as e:
        print(f"❌ Failed to add validation constraint: {str(e)}")
        print(f"Database backup is available at: {backup_path}")

if __name__ == "__main__":
    main()
