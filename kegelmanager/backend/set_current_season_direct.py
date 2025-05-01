from flask import Flask
from models import db, Season
import sqlite3

# Direkter Zugriff auf die Datenbank
conn = sqlite3.connect('instance/kegelmanager_new.db')
cursor = conn.cursor()

# Setze alle Saisons auf nicht aktuell
cursor.execute("UPDATE season SET is_current = 0")

# Finde die erste Saison und setze sie auf aktuell
cursor.execute("SELECT id FROM season LIMIT 1")
season_id = cursor.fetchone()[0]
cursor.execute("UPDATE season SET is_current = 1 WHERE id = ?", (season_id,))

# Speichere die Änderungen
conn.commit()
conn.close()

print(f"Saison mit ID {season_id} wurde als aktuelle Saison gesetzt.")
