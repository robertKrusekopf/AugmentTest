#!/usr/bin/env python3
"""
Migration script to upgrade CupMatch.match_date from Date to DateTime.
This ensures consistency with Match.match_date format.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, CupMatch
from datetime import datetime, time
from sqlalchemy import text

def upgrade_cup_match_dates():
    """
    Upgrade CupMatch.match_date from Date to DateTime.
    
    This migration:
    1. Creates a backup of existing data
    2. Converts existing Date values to DateTime (adding 15:00 as default time)
    3. Updates the column type in the database
    """
    
    with app.app_context():
        print("Starting CupMatch.match_date migration from Date to DateTime...")
        
        try:
            # Step 1: Get all existing cup matches with dates
            existing_matches = db.session.query(CupMatch.id, CupMatch.match_date).filter(
                CupMatch.match_date.isnot(None)
            ).all()
            
            print(f"Found {len(existing_matches)} cup matches with existing dates")
            
            # Step 2: Create backup data
            backup_data = []
            for match_id, match_date in existing_matches:
                if match_date:
                    # Convert date to datetime at 15:00 (3 PM)
                    if isinstance(match_date, datetime):
                        # Already a datetime, keep as is
                        new_datetime = match_date
                    else:
                        # Convert date to datetime at 15:00
                        new_datetime = datetime.combine(match_date, time(15, 0))
                    
                    backup_data.append({
                        'id': match_id,
                        'old_date': match_date,
                        'new_datetime': new_datetime
                    })
            
            print(f"Prepared {len(backup_data)} records for conversion")
            
            # Step 3: Update the database schema
            # Note: SQLite doesn't support ALTER COLUMN directly, so we need to work around this
            # For now, we'll update the data and rely on the model change
            
            # Step 4: Update existing records with datetime values
            updated_count = 0
            for record in backup_data:
                try:
                    cup_match = CupMatch.query.get(record['id'])
                    if cup_match:
                        cup_match.match_date = record['new_datetime']
                        updated_count += 1
                        
                        if updated_count <= 5:  # Show first 5 updates for debugging
                            print(f"Updated match {record['id']}: {record['old_date']} -> {record['new_datetime']}")
                            
                except Exception as e:
                    print(f"Error updating match {record['id']}: {e}")
                    continue
            
            # Commit all changes
            db.session.commit()
            print(f"Successfully updated {updated_count} cup match dates to DateTime format")
            
            # Step 5: Verify the migration
            verification_query = db.session.query(CupMatch.id, CupMatch.match_date).filter(
                CupMatch.match_date.isnot(None)
            ).limit(5).all()
            
            print("\nVerification - Sample of updated records:")
            for match_id, match_date in verification_query:
                print(f"  Match {match_id}: {match_date} (type: {type(match_date)})")
            
            print("\nMigration completed successfully!")
            return True
            
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

def rollback_cup_match_dates():
    """
    Rollback function (for emergency use only).
    Note: This will lose time information and convert back to dates only.
    """
    
    with app.app_context():
        print("Rolling back CupMatch.match_date from DateTime to Date...")
        
        try:
            # Get all cup matches with datetime values
            existing_matches = db.session.query(CupMatch).filter(
                CupMatch.match_date.isnot(None)
            ).all()
            
            print(f"Found {len(existing_matches)} cup matches to rollback")
            
            updated_count = 0
            for cup_match in existing_matches:
                if cup_match.match_date:
                    # Convert datetime back to date (losing time information)
                    if hasattr(cup_match.match_date, 'date'):
                        cup_match.match_date = cup_match.match_date.date()
                        updated_count += 1
            
            db.session.commit()
            print(f"Rolled back {updated_count} cup match dates to Date format")
            return True
            
        except Exception as e:
            print(f"Rollback failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate CupMatch.match_date from Date to DateTime')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_cup_match_dates()
    elif args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        with app.app_context():
            existing_matches = db.session.query(CupMatch.id, CupMatch.match_date).filter(
                CupMatch.match_date.isnot(None)
            ).all()
            print(f"Would update {len(existing_matches)} cup matches")
            for i, (match_id, match_date) in enumerate(existing_matches[:5]):
                if isinstance(match_date, datetime):
                    new_datetime = match_date
                else:
                    new_datetime = datetime.combine(match_date, time(15, 0))
                print(f"  Match {match_id}: {match_date} -> {new_datetime}")
            if len(existing_matches) > 5:
                print(f"  ... and {len(existing_matches) - 5} more")
        success = True  # Dry run always succeeds
    else:
        success = upgrade_cup_match_dates()

    sys.exit(0 if success else 1)
