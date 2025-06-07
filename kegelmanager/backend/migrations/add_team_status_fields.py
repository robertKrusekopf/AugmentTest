"""
Migration script to add team status fields for previous season tracking.
This adds fields to track if a team was promoted, relegated, or champion in the previous season.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models import db

def upgrade():
    """Add new fields to Team table for tracking previous season status."""
    try:
        # Add the new columns to the Team table
        with db.engine.connect() as conn:
            # Add previous_season_status column
            conn.execute(text("""
                ALTER TABLE team 
                ADD COLUMN previous_season_status VARCHAR(20)
            """))
            
            # Add previous_season_position column
            conn.execute(text("""
                ALTER TABLE team 
                ADD COLUMN previous_season_position INTEGER
            """))
            
            # Add previous_season_league_level column
            conn.execute(text("""
                ALTER TABLE team 
                ADD COLUMN previous_season_league_level INTEGER
            """))
            
            conn.commit()
            
        print("Successfully added team status fields to database")
        
    except Exception as e:
        print(f"Error adding team status fields: {e}")
        # Check if columns already exist
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    PRAGMA table_info(team)
                """))
                columns = [row[1] for row in result.fetchall()]
                
                if 'previous_season_status' in columns:
                    print("Team status fields already exist in database")
                else:
                    print("Failed to add team status fields")
                    raise e
        except Exception as check_error:
            print(f"Error checking existing columns: {check_error}")
            raise e

def downgrade():
    """Remove the team status fields."""
    try:
        with db.engine.connect() as conn:
            # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
            # For now, we'll just print a warning
            print("Warning: SQLite doesn't support DROP COLUMN. Manual intervention required to remove columns.")
            print("Columns to remove: previous_season_status, previous_season_position, previous_season_league_level")
            
    except Exception as e:
        print(f"Error in downgrade: {e}")

if __name__ == "__main__":
    # Run the migration
    upgrade()
