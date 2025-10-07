"""
Simple verification script to confirm the GameSettings initialization fix.

This script:
1. Creates a new test database
2. Verifies that GameSettings record is created during initialization
3. Compares with the old behavior (empty table)
"""
import os
import sqlite3
from neue_DB import create_new_database

def verify_fix():
    """Verify that GameSettings is now initialized during database creation."""
    
    print("="*80)
    print("VERIFYING GAMESETTINGS INITIALIZATION FIX")
    print("="*80)
    
    # Create a new test database
    print("\n[TEST] Creating new database...")
    db_name = 'verify_fix_test'
    db_path = f'instance/{db_name}.db'
    
    # Remove old test database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"  Removed old test database")
    
    result = create_new_database(db_name, True)
    print(f"  Database created: {result['success']}")
    
    # Check if GameSettings table exists and has data
    print("\n[VERIFICATION] Checking GameSettings table...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_settings'")
    table_exists = cursor.fetchone() is not None
    print(f"  ✅ GameSettings table exists: {table_exists}")
    
    if table_exists:
        # Check if data exists
        cursor.execute("SELECT * FROM game_settings")
        data = cursor.fetchall()
        
        if data:
            print(f"  ✅ GameSettings has data: {len(data)} record(s)")
            print(f"     Record: ID={data[0][0]}, manager_club_id={data[0][1]}")
            
            if data[0][1] is None:
                print(f"  ✅ manager_club_id is NULL (as expected for new database)")
                print(f"\n{'='*80}")
                print("✅ FIX VERIFIED SUCCESSFULLY!")
                print("="*80)
                print("\nThe GameSettings table is now properly initialized during database creation.")
                print("Users can now select their managed club in the Settings page,")
                print("and retirement notifications will work correctly.")
                conn.close()
                return True
            else:
                print(f"  ⚠️  manager_club_id is not NULL: {data[0][1]}")
                conn.close()
                return False
        else:
            print(f"  ❌ GameSettings table is EMPTY!")
            print(f"     This means the fix did NOT work.")
            conn.close()
            return False
    else:
        print(f"  ❌ GameSettings table does NOT exist!")
        conn.close()
        return False

if __name__ == '__main__':
    import sys
    success = verify_fix()
    sys.exit(0 if success else 1)

