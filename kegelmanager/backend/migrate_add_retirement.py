"""
Migration script to add retirement system to existing databases.

This script adds the following fields to the Player table:
- retirement_age: Integer - Age at which the player will retire
- is_retired: Boolean - Whether the player is currently retired
- retirement_season_id: Integer - Foreign key to the season in which the player retired

For existing players, it generates a retirement age using the same
normal distribution as new players (80% between 35-40 years).
"""

import os
import sys
import sqlite3
import numpy as np
from datetime import datetime


def generate_retirement_age():
    """
    Generiert das Ruhestandsalter für einen Spieler.
    80% der Spieler gehen zwischen 35 und 40 Jahren in den Ruhestand.
    
    Verwendet Normalverteilung mit:
    - Mittelwert (μ): 37.5 Jahre
    - Standardabweichung (σ): 1.95 Jahre
    
    Dies ergibt ~80% zwischen 35-40 Jahren, Rest zwischen 30-45 Jahren.
    
    Returns:
        int: Ruhestandsalter zwischen 30 und 45 Jahren
    """
    retirement_age = int(np.random.normal(37.5, 1.95))
    # Clamp auf sinnvollen Bereich (30-45 Jahre)
    retirement_age = max(30, min(45, retirement_age))
    return retirement_age


def migrate_database(db_path):
    """
    Migrate a database to add retirement system fields.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        dict: Migration result with success status and message
    """
    if not os.path.exists(db_path):
        return {
            "success": False,
            "message": f"Database file not found: {db_path}"
        }
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(player)")
        columns = [col[1] for col in cursor.fetchall()]
        
        needs_migration = False
        fields_to_add = []
        
        if 'retirement_age' not in columns:
            fields_to_add.append('retirement_age')
            needs_migration = True
            
        if 'is_retired' not in columns:
            fields_to_add.append('is_retired')
            needs_migration = True
            
        if 'retirement_season_id' not in columns:
            fields_to_add.append('retirement_season_id')
            needs_migration = True
        
        if not needs_migration:
            conn.close()
            return {
                "success": True,
                "message": "Database already has retirement system fields"
            }
        
        print(f"Migrating database: {db_path}")
        print(f"Adding fields: {', '.join(fields_to_add)}")
        
        # Add new columns if they don't exist
        if 'retirement_age' in fields_to_add:
            cursor.execute("ALTER TABLE player ADD COLUMN retirement_age INTEGER")
            print("  Added column: retirement_age")
        
        if 'is_retired' in fields_to_add:
            cursor.execute("ALTER TABLE player ADD COLUMN is_retired BOOLEAN DEFAULT 0")
            print("  Added column: is_retired")
        
        if 'retirement_season_id' in fields_to_add:
            cursor.execute("ALTER TABLE player ADD COLUMN retirement_season_id INTEGER")
            print("  Added column: retirement_season_id")
        
        # Create index for is_retired for better query performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_retired ON player(is_retired)")
            print("  Created index: idx_player_retired")
        except Exception as e:
            print(f"  Warning: Could not create index: {e}")
        
        # Generate retirement ages for existing players
        cursor.execute("SELECT id, age FROM player WHERE retirement_age IS NULL")
        players = cursor.fetchall()
        
        print(f"  Generating retirement ages for {len(players)} players...")
        
        for player_id, current_age in players:
            retirement_age = generate_retirement_age()
            
            # If player is already older than generated retirement age, set it to current age + 1-5 years
            if current_age and current_age >= retirement_age:
                retirement_age = current_age + np.random.randint(1, 6)
            
            cursor.execute(
                "UPDATE player SET retirement_age = ?, is_retired = 0 WHERE id = ?",
                (retirement_age, player_id)
            )
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"Migration completed successfully!")
        
        return {
            "success": True,
            "message": f"Successfully migrated database. Added fields: {', '.join(fields_to_add)}. Updated {len(players)} players."
        }
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Migration failed: {str(e)}"
        }


def migrate_all_databases():
    """
    Migrate all databases in the Datenbanken directory.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(script_dir, "Datenbanken")
    instance_dir = os.path.join(script_dir, "instance")
    
    databases = []
    
    # Find all .db files in Datenbanken directory
    if os.path.exists(db_dir):
        for filename in os.listdir(db_dir):
            if filename.endswith('.db'):
                databases.append(os.path.join(db_dir, filename))
    
    # Find all .db files in instance directory
    if os.path.exists(instance_dir):
        for filename in os.listdir(instance_dir):
            if filename.endswith('.db'):
                databases.append(os.path.join(instance_dir, filename))
    
    if not databases:
        print("No databases found to migrate")
        return
    
    print(f"Found {len(databases)} database(s) to migrate:")
    for db_path in databases:
        print(f"  - {os.path.basename(db_path)}")
    
    print("\nStarting migration...\n")
    
    results = []
    for db_path in databases:
        print(f"\n{'='*60}")
        print(f"Migrating: {os.path.basename(db_path)}")
        print(f"{'='*60}")
        result = migrate_database(db_path)
        results.append({
            'database': os.path.basename(db_path),
            'result': result
        })
    
    # Print summary
    print(f"\n{'='*60}")
    print("Migration Summary")
    print(f"{'='*60}")
    
    for item in results:
        status = "✓ SUCCESS" if item['result']['success'] else "✗ FAILED"
        print(f"{status}: {item['database']}")
        print(f"  {item['result']['message']}")
    
    successful = sum(1 for item in results if item['result']['success'])
    print(f"\nTotal: {successful}/{len(results)} databases migrated successfully")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Migrate specific database
        db_path = sys.argv[1]
        result = migrate_database(db_path)
        print(result['message'])
        sys.exit(0 if result['success'] else 1)
    else:
        # Migrate all databases
        migrate_all_databases()

