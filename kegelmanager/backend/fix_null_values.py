#!/usr/bin/env python3
"""
Script to fix NULL values in critical database fields that cause simulation errors.
"""

import sqlite3
import sys
import os

def fix_null_values(db_path):
    """Fix NULL values in critical fields."""
    print(f"Fixing NULL values in database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} does not exist")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Available tables: {tables}")
        
        total_fixes = 0
        
        # Fix CupMatch table if it exists
        if 'cup_match' in tables:
            print("\nFixing CupMatch table...")
            
            # Check for NULL round_number
            cursor.execute("SELECT COUNT(*) FROM cup_match WHERE round_number IS NULL")
            null_round_count = cursor.fetchone()[0]
            print(f"  Found {null_round_count} records with NULL round_number")
            
            if null_round_count > 0:
                cursor.execute("UPDATE cup_match SET round_number = 1 WHERE round_number IS NULL")
                print(f"  Fixed {cursor.rowcount} NULL round_number values")
                total_fixes += cursor.rowcount
            
            # Check for empty round_name
            cursor.execute("SELECT COUNT(*) FROM cup_match WHERE round_name IS NULL OR round_name = ''")
            empty_round_name_count = cursor.fetchone()[0]
            print(f"  Found {empty_round_name_count} records with empty round_name")
            
            if empty_round_name_count > 0:
                cursor.execute("UPDATE cup_match SET round_name = '1. Runde' WHERE round_name IS NULL OR round_name = ''")
                print(f"  Fixed {cursor.rowcount} empty round_name values")
                total_fixes += cursor.rowcount
        
        # Fix Cup table if it exists
        if 'cup' in tables:
            print("\nFixing Cup table...")
            
            # Check for NULL current_round_number
            cursor.execute("SELECT COUNT(*) FROM cup WHERE current_round_number IS NULL")
            null_current_round_count = cursor.fetchone()[0]
            print(f"  Found {null_current_round_count} records with NULL current_round_number")
            
            if null_current_round_count > 0:
                cursor.execute("UPDATE cup SET current_round_number = 1 WHERE current_round_number IS NULL")
                print(f"  Fixed {cursor.rowcount} NULL current_round_number values")
                total_fixes += cursor.rowcount
            
            # Check for NULL total_rounds
            cursor.execute("SELECT COUNT(*) FROM cup WHERE total_rounds IS NULL")
            null_total_rounds_count = cursor.fetchone()[0]
            print(f"  Found {null_total_rounds_count} records with NULL total_rounds")
            
            if null_total_rounds_count > 0:
                cursor.execute("UPDATE cup SET total_rounds = 1 WHERE total_rounds IS NULL")
                print(f"  Fixed {cursor.rowcount} NULL total_rounds values")
                total_fixes += cursor.rowcount

        # Fix Player table form fields if it exists
        if 'player' in tables:
            print("\nFixing Player table form fields...")

            # Check for NULL form fields
            form_fields = [
                'form_short_term', 'form_medium_term', 'form_long_term',
                'form_short_remaining_days', 'form_medium_remaining_days', 'form_long_remaining_days'
            ]

            for field in form_fields:
                cursor.execute(f"SELECT COUNT(*) FROM player WHERE {field} IS NULL")
                null_count = cursor.fetchone()[0]
                print(f"  Found {null_count} records with NULL {field}")

                if null_count > 0:
                    if 'remaining_days' in field:
                        # Set remaining days to 0
                        cursor.execute(f"UPDATE player SET {field} = 0 WHERE {field} IS NULL")
                    else:
                        # Set form modifiers to 0.0
                        cursor.execute(f"UPDATE player SET {field} = 0.0 WHERE {field} IS NULL")

                    print(f"  Fixed {cursor.rowcount} NULL {field} values")
                    total_fixes += cursor.rowcount

        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\nTotal fixes applied: {total_fixes}")
        print("Database successfully fixed!")
        return True
        
    except Exception as e:
        print(f"Error fixing database: {str(e)}")
        return False

if __name__ == "__main__":
    # Read the current database path from config
    config_file = "selected_db.txt"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            db_path = f.read().strip()
        
        # Convert relative path to absolute
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
        
        print(f"Using database from config: {db_path}")
        success = fix_null_values(db_path)
        
        if success:
            print("✅ Database fixed successfully!")
            sys.exit(0)
        else:
            print("❌ Failed to fix database")
            sys.exit(1)
    else:
        print("Error: No database configuration found (selected_db.txt)")
        sys.exit(1)
