"""
Script to run database migrations.
"""
import os
import sys
import importlib.util

def run_migration(migration_file, db_path):
    """
    Run a specific migration script.
    
    Args:
        migration_file: Path to the migration script
        db_path: Path to the database file
    """
    # Import the migration module dynamically
    spec = importlib.util.spec_from_file_location("migration", migration_file)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    
    # Run the migration
    return migration.run_migration(db_path)

if __name__ == "__main__":
    # Get the migration file and database path from command line arguments
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file> [db_path]")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    
    # Use provided database path or default
    if len(sys.argv) > 2:
        db_path = sys.argv[2]
    else:
        # Default database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kegelmanager.db")
    
    # Check if the migration file exists
    if not os.path.exists(migration_file):
        print(f"Migration file not found: {migration_file}")
        sys.exit(1)
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        sys.exit(1)
    
    # Run the migration
    success = run_migration(migration_file, db_path)
    
    if success:
        print("Migration completed successfully.")
        sys.exit(0)
    else:
        print("Migration failed.")
        sys.exit(1)
