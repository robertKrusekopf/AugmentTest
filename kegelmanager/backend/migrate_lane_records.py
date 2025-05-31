"""
Migration script to add the LaneRecord table to the database.
"""

import os
import sqlite3
from flask import Flask
from models import db, LaneRecord

def migrate_lane_records():
    """
    Migrate the database to add the LaneRecord table.
    """
    # Find all databases in the instance directory
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    db_files = [f for f in os.listdir(instance_dir) if f.endswith('.db')]
    
    if not db_files:
        print("No databases found.")
        return
    
    # Create a Flask app to use with SQLAlchemy
    app = Flask(__name__)
    
    # Process each database
    for db_file in db_files:
        db_path = os.path.join(instance_dir, db_file)
        print(f"Processing database: {db_path}")
        
        # Configure SQLAlchemy
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize the database
        db.init_app(app)
        
        # Create or update the LaneRecord table
        with app.app_context():
            try:
                # Check if the table already exists
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lane_record'")
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    # Check if the lane_number column exists
                    cursor.execute("PRAGMA table_info(lane_record)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    
                    if 'lane_number' in column_names:
                        print(f"  Migrating 'lane_record' table in {db_file} to remove lane_number column")
                        
                        # Create a new table without the lane_number column
                        cursor.execute("""
                        CREATE TABLE lane_record_new (
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
                        
                        # Drop old table and rename new table
                        cursor.execute("DROP TABLE lane_record")
                        cursor.execute("ALTER TABLE lane_record_new RENAME TO lane_record")
                        
                        conn.commit()
                        print(f"  Successfully migrated 'lane_record' table in {db_file}")
                    else:
                        print(f"  Table 'lane_record' already exists with correct schema in {db_file}")
                else:
                    # Create the table
                    db.create_all(tables=[LaneRecord.__table__])
                    print(f"  Created 'lane_record' table in {db_file}")
                
                conn.close()
                    
            except Exception as e:
                print(f"  Error migrating 'lane_record' table in {db_file}: {e}")
    
    print("Migration completed.")

if __name__ == "__main__":
    migrate_lane_records()
