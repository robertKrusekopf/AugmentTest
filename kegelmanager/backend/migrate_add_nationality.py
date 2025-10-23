#!/usr/bin/env python3
"""
Migration script to add nationality (nationalitaet) column to Player table.

This script:
1. Adds 'nationalitaet' column to the Player table with default value 'Deutsch'
2. Sets nationality to 'Deutsch' for all existing players
3. Works with multiple databases in the instance folder
4. Creates backups before making changes
5. Safe to run multiple times (idempotent)

Usage:
    python migrate_add_nationality.py                    # Migrate all databases
    python migrate_add_nationality.py path/to/db.db      # Migrate specific database
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime
from flask import Flask
from models import db, Player

def backup_database(db_path):
    """Create a backup of the database before making changes."""
    backup_path = db_path.replace('.db', f'_backup_nationality_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    print(f"Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print(f"Backup created successfully: {backup_path}")
    return backup_path

def check_column_exists(db_path, table_name, column_name):
    """Check if a column exists in a table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        return column_name in column_names
    finally:
        conn.close()

def add_nationality_column(db_path):
    """Add nationality column to Player table and set default values."""
    print(f"\n{'='*60}")
    print(f"Migrating database: {db_path}")
    print(f"{'='*60}\n")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Create backup
    backup_path = backup_database(db_path)
    
    try:
        # Check if column already exists
        if check_column_exists(db_path, 'player', 'nationalitaet'):
            print("✅ Column 'nationalitaet' already exists in Player table")
            return True
        
        # Create Flask app for this database
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize database
        db.init_app(app)
        
        with app.app_context():
            print("📝 Adding 'nationalitaet' column to Player table...")
            
            # Add the column using raw SQL
            db.session.execute("ALTER TABLE player ADD COLUMN nationalitaet VARCHAR(50) DEFAULT 'Deutsch' NOT NULL")
            db.session.commit()
            print("✅ Column 'nationalitaet' added successfully")
            
            # Update all existing players to have 'Deutsch' nationality
            print("📝 Setting nationality to 'Deutsch' for all existing players...")
            
            # Count existing players
            player_count = Player.query.count()
            print(f"Found {player_count} players to update")
            
            if player_count > 0:
                # Update all players
                db.session.execute("UPDATE player SET nationalitaet = 'Deutsch' WHERE nationalitaet IS NULL OR nationalitaet = ''")
                updated_count = db.session.execute("SELECT COUNT(*) FROM player WHERE nationalitaet = 'Deutsch'").scalar()
                db.session.commit()
                print(f"✅ Updated {updated_count} players with nationality 'Deutsch'")
            else:
                print("ℹ️  No existing players found")
            
            print(f"✅ Migration completed successfully for {db_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        print(f"🔄 Restoring backup from {backup_path}")
        
        # Restore backup
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            print("✅ Backup restored successfully")
        
        return False

def find_databases():
    """Find all database files in the instance folder."""
    instance_folder = 'instance'
    databases = []
    
    if os.path.exists(instance_folder):
        for file in os.listdir(instance_folder):
            if file.endswith('.db') and not file.endswith('_backup.db'):
                databases.append(os.path.join(instance_folder, file))
    
    # Also check for databases in current directory
    for file in os.listdir('.'):
        if file.endswith('.db') and not file.endswith('_backup.db'):
            databases.append(file)
    
    return databases

def main():
    """Main migration function."""
    print("🚀 Nationality Migration Script")
    print("Adding 'nationalitaet' column to Player table")
    print("=" * 60)
    
    # Check if specific database was provided
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            sys.exit(1)
        
        success = add_nationality_column(db_path)
        if success:
            print("\n✅ Migration completed successfully!")
        else:
            print("\n❌ Migration failed!")
            sys.exit(1)
    else:
        # Find all databases
        databases = find_databases()
        
        if not databases:
            print("❌ No database files found!")
            print("Make sure you're in the correct directory or specify a database path.")
            sys.exit(1)
        
        print(f"Found {len(databases)} database(s):")
        for db in databases:
            print(f"  - {db}")
        
        # Ask for confirmation
        response = input(f"\nMigrate all {len(databases)} database(s)? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)
        
        # Migrate all databases
        success_count = 0
        for db_path in databases:
            if add_nationality_column(db_path):
                success_count += 1
        
        print(f"\n{'='*60}")
        print(f"Migration Summary:")
        print(f"  Total databases: {len(databases)}")
        print(f"  Successful: {success_count}")
        print(f"  Failed: {len(databases) - success_count}")
        
        if success_count == len(databases):
            print("✅ All migrations completed successfully!")
        else:
            print("⚠️  Some migrations failed. Check the output above for details.")

if __name__ == "__main__":
    main()
