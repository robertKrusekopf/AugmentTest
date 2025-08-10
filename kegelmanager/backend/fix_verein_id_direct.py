import sqlite3
import re

def clean_name_for_verein_id(name):
    """Erstelle verein_id aus dem Namen"""
    # Entferne Leerzeichen, Bindestriche und andere Sonderzeichen
    cleaned = re.sub(r'[^a-zA-ZäöüÄÖÜß0-9]', '', name)
    # Konvertiere zu Kleinbuchstaben
    return cleaned.lower()

# Fix verein_id directly with SQL
db_path = 'instance/test_extend_migration.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Fixing verein_id values directly with SQL...")

# Get all clubs
cursor.execute("SELECT id, name FROM club")
clubs = cursor.fetchall()

print(f"Found {len(clubs)} clubs to update:")

for club_id, club_name in clubs:
    verein_id = clean_name_for_verein_id(club_name)
    print(f"  {club_name} -> {verein_id}")
    
    # Update with direct SQL
    cursor.execute("UPDATE club SET verein_id = ? WHERE id = ?", (verein_id, club_id))

# Commit changes
conn.commit()

print("\nVerifying updates...")
cursor.execute("SELECT id, name, verein_id FROM club LIMIT 5")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, verein_id: '{row[2]}'")

# Check count
cursor.execute("SELECT COUNT(*) FROM club WHERE verein_id IS NOT NULL AND verein_id != ''")
count_with_verein_id = cursor.fetchone()[0]
print(f"\nClubs with verein_id: {count_with_verein_id}")

conn.close()
print("Done!")
