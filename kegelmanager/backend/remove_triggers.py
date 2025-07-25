#!/usr/bin/env python3
"""
Script to remove the validation triggers that are preventing normal operation.
"""

import sqlite3
import os

def get_database_path():
    """Get the current database path from .env file."""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("DATABASE_PATH="):
                    return line.split("=", 1)[1].strip()
    
    # Fallback to default path
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "kegelmanager_default.db")

def main():
    """Remove validation triggers."""
    db_path = get_database_path()
    print(f"Database path: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print('Removing validation triggers...')

    # Drop the validation triggers
    cursor.execute('DROP TRIGGER IF EXISTS validate_performance_insert')
    cursor.execute('DROP TRIGGER IF EXISTS validate_performance_update')

    conn.commit()
    print('✅ Validation triggers removed')

    # Check if triggers are gone
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'validate_performance_%'")
    remaining_triggers = cursor.fetchall()

    if remaining_triggers:
        print(f'❌ Some triggers still exist: {remaining_triggers}')
    else:
        print('✅ All validation triggers successfully removed')

    conn.close()

if __name__ == "__main__":
    main()
