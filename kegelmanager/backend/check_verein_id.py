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

# Check the manually created test database
test_db_path = 'instance/test_extend_manual.db'
if os.path.exists(test_db_path):
    print(f"\nChecking manually created {test_db_path}...")
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Check verein_id values in test database
    cursor.execute('SELECT id, name, verein_id FROM club LIMIT 5')
    print('First 5 clubs in test database:')
    for row in cursor.fetchall():
        print(f'ID: {row[0]}, Name: {row[1]}, verein_id: {row[2]}')

    # Count clubs with and without verein_id
    cursor.execute('SELECT COUNT(*) FROM club WHERE verein_id IS NULL OR verein_id = ""')
    null_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM club')
    total_count = cursor.fetchone()[0]

    print(f'Total clubs: {total_count}')
    print(f'Clubs without verein_id: {null_count}')
    print(f'Clubs with verein_id: {total_count - null_count}')

    conn.close()
else:
    print(f"Test database {test_db_path} not found!")

# Check the fixed test database
fixed_db_path = 'instance/test_extend_fixed.db'
if os.path.exists(fixed_db_path):
    print(f"\nChecking fixed {fixed_db_path}...")
    conn = sqlite3.connect(fixed_db_path)
    cursor = conn.cursor()

    # Check verein_id values in fixed database
    cursor.execute('SELECT id, name, verein_id FROM club LIMIT 5')
    print('First 5 clubs in fixed database:')
    for row in cursor.fetchall():
        print(f'ID: {row[0]}, Name: {row[1]}, verein_id: {row[2]}')

    # Count clubs with and without verein_id
    cursor.execute('SELECT COUNT(*) FROM club WHERE verein_id IS NULL OR verein_id = ""')
    null_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM club')
    total_count = cursor.fetchone()[0]

    print(f'Total clubs: {total_count}')
    print(f'Clubs without verein_id: {null_count}')
    print(f'Clubs with verein_id: {total_count - null_count}')

    conn.close()
else:
    print(f"Fixed database {fixed_db_path} not found!")

# Check the string fix test database
string_fix_db_path = 'instance/test_extend_string_fix.db'
if os.path.exists(string_fix_db_path):
    print(f"\nChecking string fix {string_fix_db_path}...")
    conn = sqlite3.connect(string_fix_db_path)
    cursor = conn.cursor()

    # Check verein_id values in string fix database
    cursor.execute('SELECT id, name, verein_id FROM club LIMIT 5')
    print('First 5 clubs in string fix database:')
    for row in cursor.fetchall():
        print(f'ID: {row[0]}, Name: {row[1]}, verein_id: {row[2]}')

    # Count clubs with and without verein_id
    cursor.execute('SELECT COUNT(*) FROM club WHERE verein_id IS NULL OR verein_id = ""')
    null_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM club')
    total_count = cursor.fetchone()[0]

    print(f'Total clubs: {total_count}')
    print(f'Clubs without verein_id: {null_count}')
    print(f'Clubs with verein_id: {total_count - null_count}')

    conn.close()
else:
    print(f"String fix database {string_fix_db_path} not found!")

# Check the migration test database
migration_db_path = 'instance/test_extend_migration.db'
if os.path.exists(migration_db_path):
    print(f"\nChecking migration {migration_db_path}...")
    conn = sqlite3.connect(migration_db_path)
    cursor = conn.cursor()

    # Check table structure
    cursor.execute("PRAGMA table_info(club)")
    columns = cursor.fetchall()
    print("Club table columns after migration:")
    for col in columns:
        if col[1] == 'verein_id':
            print(f"  {col[1]} ({col[2]}) - FOUND!")

    # Check verein_id values in migration database
    cursor.execute('SELECT id, name, verein_id FROM club LIMIT 5')
    print('First 5 clubs in migration database:')
    for row in cursor.fetchall():
        print(f'ID: {row[0]}, Name: {row[1]}, verein_id: {row[2]}')

    # Count clubs with and without verein_id
    cursor.execute('SELECT COUNT(*) FROM club WHERE verein_id IS NULL OR verein_id = ""')
    null_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM club')
    total_count = cursor.fetchone()[0]

    print(f'Total clubs: {total_count}')
    print(f'Clubs without verein_id: {null_count}')
    print(f'Clubs with verein_id: {total_count - null_count}')

    conn.close()
else:
    print(f"Migration database {migration_db_path} not found!")

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
