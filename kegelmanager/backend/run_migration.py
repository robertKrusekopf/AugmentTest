"""
Script to run the team status fields migration through Flask app context.
"""

from app import app, db
from sqlalchemy import text

def add_team_status_fields():
    """Add new fields to Team table for tracking previous season status."""
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('team')]
            
            if 'previous_season_status' in columns:
                print("Team status fields already exist in database")
                return
            
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
            raise e

if __name__ == "__main__":
    add_team_status_fields()
