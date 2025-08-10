import sqlite3
import os

# Check if RealeDB_complete.db exists
db_path = 'instance/RealeDB_complete.db'
if os.path.exists(db_path):
    print(f"Checking {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check club table structure
    cursor.execute("PRAGMA table_info(club)")
    columns = cursor.fetchall()
    print("Club table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check verein_id values
    cursor.execute('SELECT id, name, verein_id FROM club LIMIT 10')
    print('\nFirst 10 clubs:')
    for row in cursor.fetchall():
        print(f'ID: {row[0]}, Name: {row[1]}, verein_id: {row[2]}')
    
    # Count clubs with and without verein_id
    cursor.execute('SELECT COUNT(*) FROM club WHERE verein_id IS NULL OR verein_id = ""')
    null_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM club')
    total_count = cursor.fetchone()[0]
    
    print(f'\nTotal clubs: {total_count}')
    print(f'Clubs without verein_id: {null_count}')
    print(f'Clubs with verein_id: {total_count - null_count}')
    
    conn.close()
else:
    print(f"Database {db_path} not found!")

# Also check original RealeDB.db
original_db_path = 'instance/RealeDB.db'
if os.path.exists(original_db_path):
    print(f"\nChecking original {original_db_path}...")
    conn = sqlite3.connect(original_db_path)
    cursor = conn.cursor()
    
    # Check verein_id values in original
    cursor.execute('SELECT id, name, verein_id FROM club LIMIT 5')
    print('First 5 clubs in original:')
    for row in cursor.fetchall():
        print(f'ID: {row[0]}, Name: {row[1]}, verein_id: {row[2]}')
    
    conn.close()
else:
    print(f"Original database {original_db_path} not found!")
