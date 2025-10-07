"""
Migration script to add notification settings to existing databases.

This script:
1. Adds notification_category column to Message table
2. Creates NotificationSettings table
3. Sets default notification_category for existing messages
"""

import os
import sys
import sqlite3
from datetime import datetime

def migrate_database(db_path):
    """
    Add notification settings to an existing database.
    
    Args:
        db_path: Path to the database file
    """
    print(f"\n{'='*80}")
    print(f"Migrating database: {db_path}")
    print(f"{'='*80}\n")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if Message table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='message'
        """)
        
        if not cursor.fetchone():
            print("⚠️  Message table does not exist. Skipping migration.")
            conn.close()
            return True
        
        # Step 1: Add notification_category column to Message table if it doesn't exist
        print("Step 1: Checking Message table...")
        cursor.execute("PRAGMA table_info(message)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'notification_category' not in columns:
            print("  Adding notification_category column to Message table...")
            cursor.execute("""
                ALTER TABLE message 
                ADD COLUMN notification_category VARCHAR(50) DEFAULT 'general'
            """)
            
            # Create index on notification_category
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_message_notification_category 
                ON message (notification_category)
            """)
            
            # Set notification_category for existing retirement messages
            cursor.execute("""
                UPDATE message 
                SET notification_category = 'player_retirement'
                WHERE subject LIKE '%Ruhestand%' OR subject LIKE '%retirement%'
            """)
            
            rows_updated = cursor.rowcount
            print(f"  ✅ Added notification_category column")
            print(f"  ✅ Updated {rows_updated} retirement messages")
        else:
            print("  ✅ notification_category column already exists")
        
        # Step 2: Create NotificationSettings table if it doesn't exist
        print("\nStep 2: Checking NotificationSettings table...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='notification_settings'
        """)
        
        if not cursor.fetchone():
            print("  Creating NotificationSettings table...")
            cursor.execute("""
                CREATE TABLE notification_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_retirement BOOLEAN DEFAULT 1,
                    transfers BOOLEAN DEFAULT 1,
                    match_results BOOLEAN DEFAULT 1,
                    injuries BOOLEAN DEFAULT 1,
                    contracts BOOLEAN DEFAULT 1,
                    finances BOOLEAN DEFAULT 1,
                    achievements BOOLEAN DEFAULT 1,
                    general BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default settings
            cursor.execute("""
                INSERT INTO notification_settings 
                (player_retirement, transfers, match_results, injuries, contracts, finances, achievements, general)
                VALUES (1, 1, 1, 1, 1, 1, 1, 1)
            """)
            
            print("  ✅ Created NotificationSettings table with default settings")
        else:
            print("  ✅ NotificationSettings table already exists")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM message")
        message_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message WHERE notification_category = 'player_retirement'")
        retirement_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM notification_settings")
        settings_count = cursor.fetchone()[0]
        
        print(f"\nSummary:")
        print(f"  Total messages: {message_count}")
        print(f"  Retirement messages: {retirement_count}")
        print(f"  Notification settings records: {settings_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_all_databases():
    """Migrate all databases in the instance directory."""
    # Get the instance directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(backend_dir, 'instance')
    
    if not os.path.exists(instance_dir):
        print(f"❌ Instance directory not found: {instance_dir}")
        return
    
    # Find all .db files
    db_files = [f for f in os.listdir(instance_dir) if f.endswith('.db')]
    
    if not db_files:
        print(f"⚠️  No database files found in {instance_dir}")
        return
    
    print(f"\nFound {len(db_files)} database(s) to migrate:")
    for db_file in db_files:
        print(f"  - {db_file}")
    
    print("\n" + "="*80)
    response = input("Do you want to migrate all databases? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        return
    
    # Migrate each database
    success_count = 0
    for db_file in db_files:
        db_path = os.path.join(instance_dir, db_file)
        if migrate_database(db_path):
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"Migration complete: {success_count}/{len(db_files)} databases migrated successfully")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    print("="*80)
    print("Notification Settings Migration Script")
    print("="*80)
    print("\nThis script will add notification settings support to your databases.")
    print("It will:")
    print("  1. Add notification_category column to Message table")
    print("  2. Create NotificationSettings table")
    print("  3. Set default categories for existing messages")
    print("\n⚠️  IMPORTANT: Make sure to backup your databases before running this script!")
    print("="*80)
    
    migrate_all_databases()

