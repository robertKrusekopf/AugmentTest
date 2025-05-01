import os
import sqlite3
from flask import Flask
from models import db, Club

def migrate_club_table():
    """
    Migriert die Club-Tabelle, um die neuen Felder hinzuzufügen.
    """
    # Finde alle Datenbanken im instance-Verzeichnis
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    db_files = [f for f in os.listdir(instance_dir) if f.endswith('.db')]
    
    if not db_files:
        print("Keine Datenbanken gefunden.")
        return
    
    for db_file in db_files:
        db_path = os.path.join(instance_dir, db_file)
        print(f"Migriere Datenbank: {db_path}")
        
        # Verbindung zur Datenbank herstellen
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Überprüfe, ob die Club-Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='club'")
        if not cursor.fetchone():
            print(f"  Club-Tabelle existiert nicht in {db_file}.")
            conn.close()
            continue
        
        # Überprüfe, welche Spalten bereits existieren
        cursor.execute("PRAGMA table_info(club)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Neue Spalten, die hinzugefügt werden sollen
        new_columns = {
            'fans': 'INTEGER DEFAULT 1000',
            'training_facilities': 'INTEGER DEFAULT 50',
            'coaching': 'INTEGER DEFAULT 50',
            'logo_path': 'TEXT'
        }
        
        # Füge fehlende Spalten hinzu
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE club ADD COLUMN {column_name} {column_type}")
                    print(f"  Spalte '{column_name}' zur Club-Tabelle hinzugefügt.")
                except sqlite3.OperationalError as e:
                    print(f"  Fehler beim Hinzufügen der Spalte '{column_name}': {e}")
        
        # Speichere die Änderungen
        conn.commit()
        conn.close()
        print(f"  Migration für {db_file} abgeschlossen.")

    # Erstelle den Ordner für die Vereinswappen, falls er nicht existiert
    logos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "public", "logos")
    if not os.path.exists(logos_dir):
        os.makedirs(logos_dir)
        print(f"Ordner für Vereinswappen erstellt: {logos_dir}")

if __name__ == "__main__":
    migrate_club_table()
    print("Migration abgeschlossen.")
