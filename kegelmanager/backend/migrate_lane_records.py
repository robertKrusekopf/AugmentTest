#!/usr/bin/env python3
"""
Migration script to make match_id nullable in lane_record table.
"""

import sqlite3
import os
from app import app

def migrate_lane_records():
    """Migrate the lane_record table to make match_id nullable."""
    
    with app.app_context():
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"Migrating database: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"Database file not found: {db_path}")
            return
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check current schema
            cursor.execute("PRAGMA table_info(lane_record)")
            columns = cursor.fetchall()
            print("Current lane_record schema:")
            for col in columns:
                print(f"  {col}")
            
            # Check if match_id is already nullable
            match_id_col = None
            for col in columns:
                if col[1] == 'match_id':  # col[1] is column name
                    match_id_col = col
                    break
            
            if match_id_col and match_id_col[3] == 0:  # col[3] is notnull (0 = nullable, 1 = not null)
                print("match_id is already nullable, no migration needed.")
                return
            
            print("Making match_id nullable...")
            
            # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
            
            # 1. Create new table with correct schema
            cursor.execute("""
                CREATE TABLE lane_record_new (
                    id INTEGER PRIMARY KEY,
                    record_type VARCHAR(20) NOT NULL,
                    category VARCHAR(20) NOT NULL,
                    club_id INTEGER NOT NULL,
                    player_id INTEGER,
                    team_id INTEGER,
                    score INTEGER NOT NULL,
                    match_id INTEGER,
                    record_date DATETIME,
                    FOREIGN KEY(club_id) REFERENCES club (id),
                    FOREIGN KEY(player_id) REFERENCES player (id),
                    FOREIGN KEY(team_id) REFERENCES team (id),
                    FOREIGN KEY(match_id) REFERENCES match (id)
                )
            """)
            
            # 2. Copy data from old table to new table
            cursor.execute("""
                INSERT INTO lane_record_new 
                SELECT id, record_type, category, club_id, player_id, team_id, score, match_id, record_date
                FROM lane_record
            """)
            
            # 3. Drop old table
            cursor.execute("DROP TABLE lane_record")
            
            # 4. Rename new table
            cursor.execute("ALTER TABLE lane_record_new RENAME TO lane_record")
            
            # Commit changes
            conn.commit()
            print("Migration completed successfully!")
            
            # Verify the new schema
            cursor.execute("PRAGMA table_info(lane_record)")
            columns = cursor.fetchall()
            print("New lane_record schema:")
            for col in columns:
                print(f"  {col}")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    migrate_lane_records()
