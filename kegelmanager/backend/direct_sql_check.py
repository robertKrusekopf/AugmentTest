import sqlite3

# Direct SQL check of migration database
db_path = 'instance/test_extend_migration.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Direct SQL check of migration database:")

# Check table structure
cursor.execute("PRAGMA table_info(club)")
columns = cursor.fetchall()
print("\nClub table structure:")
for col in columns:
    print(f"  {col[1]} {col[2]} (nullable: {col[3] == 0})")

# Check actual data with direct SQL
cursor.execute("SELECT id, name, verein_id FROM club LIMIT 5")
print("\nFirst 5 clubs (direct SQL):")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, verein_id: '{row[2]}'")

# Check if any verein_id values exist
cursor.execute("SELECT COUNT(*) FROM club WHERE verein_id IS NOT NULL AND verein_id != ''")
count_with_verein_id = cursor.fetchone()[0]
print(f"\nClubs with non-empty verein_id: {count_with_verein_id}")

# Show all verein_id values
cursor.execute("SELECT DISTINCT verein_id FROM club")
verein_ids = cursor.fetchall()
print(f"\nAll distinct verein_id values:")
for vid in verein_ids:
    print(f"  '{vid[0]}'")

conn.close()
