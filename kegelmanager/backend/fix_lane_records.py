"""
Fix script to recreate the LaneRecord table without the lane_number column.
This script should be run to fix the "NOT NULL constraint failed: lane_record.lane_number" error.
"""

import os
import sqlite3
from flask import Flask
from models import db, LaneRecord

def fix_lane_records():
    """
    Fix the LaneRecord table by recreating it without the lane_number column.
    """
    # Find all databases in the instance directory
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

    db_files = [f for f in os.listdir(instance_dir) if f.endswith('.db')]

    if not db_files:
        print("No databases found.")
        return

    # Process each database
    for db_file in db_files:
        db_path = os.path.join(instance_dir, db_file)
        print(f"Processing database: {db_path}")

        try:
            # Connect to the database directly with SQLite
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if the lane_record table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lane_record'")
            table_exists = cursor.fetchone() is not None

            if table_exists:
                print(f"  Recreating 'lane_record' table in {db_file}")

                # Create a new table without the lane_number column
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS lane_record_new (
                    id INTEGER PRIMARY KEY,
                    record_type VARCHAR(20) NOT NULL,
                    category VARCHAR(20) NOT NULL,
                    club_id INTEGER NOT NULL,
                    player_id INTEGER,
                    team_id INTEGER,
                    score INTEGER NOT NULL,
                    match_id INTEGER NOT NULL,
                    record_date DATETIME,
                    FOREIGN KEY (club_id) REFERENCES club (id),
                    FOREIGN KEY (player_id) REFERENCES player (id),
                    FOREIGN KEY (team_id) REFERENCES team (id),
                    FOREIGN KEY (match_id) REFERENCES match (id)
                )
                """)

                # Check if there's any data to migrate
                cursor.execute("SELECT COUNT(*) FROM lane_record")
                record_count = cursor.fetchone()[0]

                if record_count > 0:
                    # Check if lane_number column exists
                    cursor.execute("PRAGMA table_info(lane_record)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]

                    if 'lane_number' in column_names:
                        # Copy data from old table to new table, ignoring lane_number
                        cursor.execute("""
                        INSERT INTO lane_record_new (
                            id, record_type, category, club_id, player_id, team_id,
                            score, match_id, record_date
                        )
                        SELECT
                            id, record_type, category, club_id, player_id, team_id,
                            score, match_id, record_date
                        FROM lane_record
                        """)
                        print(f"  Migrated {record_count} records from old table")

                # Drop old table and rename new table
                cursor.execute("DROP TABLE lane_record")
                cursor.execute("ALTER TABLE lane_record_new RENAME TO lane_record")

                conn.commit()
                print(f"  Successfully recreated 'lane_record' table in {db_file}")
            else:
                print(f"  Table 'lane_record' does not exist in {db_file}")
                # Create the table with the correct schema
                cursor.execute("""
                CREATE TABLE lane_record (
                    id INTEGER PRIMARY KEY,
                    record_type VARCHAR(20) NOT NULL,
                    category VARCHAR(20) NOT NULL,
                    club_id INTEGER NOT NULL,
                    player_id INTEGER,
                    team_id INTEGER,
                    score INTEGER NOT NULL,
                    match_id INTEGER NOT NULL,
                    record_date DATETIME,
                    FOREIGN KEY (club_id) REFERENCES club (id),
                    FOREIGN KEY (player_id) REFERENCES player (id),
                    FOREIGN KEY (team_id) REFERENCES team (id),
                    FOREIGN KEY (match_id) REFERENCES match (id)
                )
                """)
                conn.commit()
                print(f"  Created 'lane_record' table in {db_file}")

            conn.close()

        except Exception as e:
            print(f"  Error fixing 'lane_record' table in {db_file}: {e}")

    print("Fix completed.")

if __name__ == "__main__":
    fix_lane_records()
