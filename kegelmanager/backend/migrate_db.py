"""
Migrations-Skript zum Hinzufügen der neuen Spieler-Flags zur Datenbank.
"""
import os
import sys
import sqlite3

def add_player_matchday_flags():
    """Fügt die neuen Spieler-Flags zur Datenbank hinzu."""
    # Finde den Datenbankpfad
    db_path = None
    if os.path.exists('selected_db.txt'):
        with open('selected_db.txt', 'r') as f:
            db_path = f.read().strip()
            print(f"DEBUG: Datenbankpfad aus Konfigurationsdatei: {db_path}")
    else:
        db_path = 'instance/kegelmanager_default.db'
        print(f"DEBUG: Verwende Standard-Datenbankpfad: {db_path}")

    print(f"DEBUG: Verwende Datenbank: {db_path}")

    # Verbinde zur Datenbank
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Überprüfe, ob die Spalten bereits existieren
    cursor.execute("PRAGMA table_info(player)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'has_played_current_matchday' not in columns or 'last_played_matchday' not in columns:
        print("Füge neue Spalten zur Player-Tabelle hinzu...")

        # Führe die ALTER TABLE-Befehle aus
        if 'has_played_current_matchday' not in columns:
            cursor.execute("ALTER TABLE player ADD COLUMN has_played_current_matchday BOOLEAN DEFAULT 0")
            print("Spalte 'has_played_current_matchday' hinzugefügt.")

        if 'last_played_matchday' not in columns:
            cursor.execute("ALTER TABLE player ADD COLUMN last_played_matchday INTEGER")
            print("Spalte 'last_played_matchday' hinzugefügt.")

        # Commit die Änderungen
        conn.commit()
        print("Migration abgeschlossen.")
    else:
        print("Die Spalten existieren bereits. Keine Migration notwendig.")

    # Schließe die Verbindung
    conn.close()

if __name__ == "__main__":
    add_player_matchday_flags()
