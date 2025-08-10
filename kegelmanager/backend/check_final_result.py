import sqlite3

# Check the final result
db_path = 'instance/test_extend_final.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Final result check:")

# Check table structure
cursor.execute("PRAGMA table_info(club)")
columns = cursor.fetchall()
print("\nClub table structure:")
for col in columns:
    if col[1] == 'verein_id':
        print(f"  {col[1]} {col[2]} - FOUND!")

# Check verein_id values
cursor.execute("SELECT id, name, verein_id FROM club LIMIT 10")
print("\nFirst 10 clubs:")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, verein_id: '{row[2]}'")

# Count clubs with verein_id
cursor.execute("SELECT COUNT(*) FROM club WHERE verein_id IS NOT NULL AND verein_id != ''")
count_with_verein_id = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM club")
total_count = cursor.fetchone()[0]

print(f"\nTotal clubs: {total_count}")
print(f"Clubs with verein_id: {count_with_verein_id}")
print(f"Success rate: {count_with_verein_id}/{total_count} = {100*count_with_verein_id/total_count:.1f}%")

conn.close()
