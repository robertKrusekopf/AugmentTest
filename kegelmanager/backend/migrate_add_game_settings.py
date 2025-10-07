"""
Migration script to add GameSettings table to existing databases.

This script adds the game_settings table which stores:
- manager_club_id: The club that the user manages
"""

import os
import sys
import sqlite3

def migrate_database(db_path):
    """Add GameSettings table to a database."""
    print(f"\nMigrating database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"  ❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if game_settings table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='game_settings'
        """)
        
        if cursor.fetchone():
            print("  ℹ️  game_settings table already exists")
            conn.close()
            return True
        
        # Create game_settings table
        print("  Creating game_settings table...")
        cursor.execute("""
            CREATE TABLE game_settings (
                id INTEGER PRIMARY KEY,
                manager_club_id INTEGER,
                FOREIGN KEY (manager_club_id) REFERENCES club (id)
            )
        """)
        
        # Insert default row with no manager club
        cursor.execute("""
            INSERT INTO game_settings (id, manager_club_id)
            VALUES (1, NULL)
        """)
        
        conn.commit()
        conn.close()
        
        print("  ✅ Successfully added game_settings table")
        return True
        
    except Exception as e:
        print(f"  ❌ Error migrating database: {e}")
        return False


def main():
    """Migrate all databases in the instance directory."""
    # Get the instance directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(script_dir, 'instance')
    
    if not os.path.exists(instance_dir):
        print(f"Instance directory not found: {instance_dir}")
        return
    
    # Find all .db files
    db_files = [f for f in os.listdir(instance_dir) if f.endswith('.db')]
    
    if not db_files:
        print("No database files found in instance directory")
        return
    
    print(f"Found {len(db_files)} database(s) to migrate:")
    for db_file in db_files:
        print(f"  - {db_file}")
    
    # Migrate each database
    success_count = 0
    for db_file in db_files:
        db_path = os.path.join(instance_dir, db_file)
        if migrate_database(db_path):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Migration complete: {success_count}/{len(db_files)} databases migrated successfully")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()

