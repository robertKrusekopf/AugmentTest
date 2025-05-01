import sqlite3

# Direkter Zugriff auf die Datenbank
conn = sqlite3.connect('instance/kegelmanager_new.db')
cursor = conn.cursor()

# Zeige alle Tabellen an
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tabellen in der Datenbank:")
for table in tables:
    print(table[0])

conn.close()
