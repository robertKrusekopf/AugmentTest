"""
Check if GameSettings table exists in a newly created database.
"""
import sqlite3
import sys

db_path = 'instance/test_fix_verification.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if game_settings table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_settings'")
result = cursor.fetchone()

print(f"Database: {db_path}")
print(f"GameSettings table exists: {result is not None}")

if result:
    # Get data from game_settings
    cursor.execute("SELECT * FROM game_settings")
    data = cursor.fetchall()
    print(f"GameSettings data: {data}")
    
    if data:
        print(f"  ID: {data[0][0]}")
        print(f"  manager_club_id: {data[0][1]}")
    else:
        print("  No data in game_settings table")
else:
    print("  GameSettings table does NOT exist!")
    print("\n  This means init_db.py does NOT create the GameSettings table.")
    print("  The table is only created when:")
    print("    1. db.create_all() is called (which creates the schema)")
    print("    2. A migration script is run")
    print("    3. The API endpoint creates it on first access")

conn.close()

