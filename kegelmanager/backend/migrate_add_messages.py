"""
Migration script to add the Message table to existing databases.
This script adds the messages table for the in-game notification system.
"""

import os
import sys
from flask import Flask
from models import db, Message

def migrate_database(db_path):
    """Add Message table to the database."""
    print(f"\n{'='*60}")
    print(f"Migrating database: {db_path}")
    print(f"{'='*60}\n")
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        # Check if Message table already exists
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'message' in existing_tables:
            print("✓ Message table already exists. Skipping migration.")
            return True
        
        try:
            # Create the Message table
            print("Creating Message table...")
            Message.__table__.create(db.engine)
            print("✓ Message table created successfully!")
            
            # Commit changes
            db.session.commit()
            print("✓ Migration completed successfully!")
            
            return True
            
        except Exception as e:
            print(f"✗ Error during migration: {str(e)}")
            db.session.rollback()
            return False


def main():
    """Main migration function."""
    print("\n" + "="*60)
    print("MESSAGE TABLE MIGRATION")
    print("="*60)
    
    # Get the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for databases in the Datenbanken directory
    datenbanken_dir = os.path.join(backend_dir, "Datenbanken")
    instance_dir = os.path.join(backend_dir, "instance")
    
    databases_to_migrate = []
    
    # Find all .db files in Datenbanken directory
    if os.path.exists(datenbanken_dir):
        for file in os.listdir(datenbanken_dir):
            if file.endswith('.db'):
                db_path = os.path.join(datenbanken_dir, file)
                databases_to_migrate.append(db_path)
    
    # Find all .db files in instance directory
    if os.path.exists(instance_dir):
        for file in os.listdir(instance_dir):
            if file.endswith('.db'):
                db_path = os.path.join(instance_dir, file)
                databases_to_migrate.append(db_path)
    
    # Also check for kegelmanager.db in the backend directory
    main_db = os.path.join(backend_dir, "kegelmanager.db")
    if os.path.exists(main_db):
        databases_to_migrate.append(main_db)
    
    if not databases_to_migrate:
        print("\n✗ No databases found to migrate.")
        print(f"  Checked directories:")
        print(f"  - {datenbanken_dir}")
        print(f"  - {instance_dir}")
        print(f"  - {backend_dir}")
        return
    
    print(f"\nFound {len(databases_to_migrate)} database(s) to migrate:")
    for db_path in databases_to_migrate:
        print(f"  - {os.path.basename(db_path)}")
    
    # Ask for confirmation
    response = input("\nProceed with migration? (y/n): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Migrate each database
    success_count = 0
    for db_path in databases_to_migrate:
        if migrate_database(db_path):
            success_count += 1
    
    # Print summary
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Total databases: {len(databases_to_migrate)}")
    print(f"Successfully migrated: {success_count}")
    print(f"Failed: {len(databases_to_migrate) - success_count}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

