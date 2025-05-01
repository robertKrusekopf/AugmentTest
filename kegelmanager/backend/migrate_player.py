import os
import sqlite3
from flask import Flask
from models import db, Player

def migrate_player_table():
    """
    Migriert die Player-Tabelle, um die neuen Felder hinzuzufügen.
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
        
        # Überprüfe, ob die Player-Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player'")
        if not cursor.fetchone():
            print(f"  Player-Tabelle existiert nicht in {db_file}.")
            conn.close()
            continue
        
        # Überprüfe, welche Spalten bereits existieren
        cursor.execute("PRAGMA table_info(player)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Neue Spalten, die hinzugefügt werden sollen
        new_columns = {
            'konstanz': 'INTEGER DEFAULT 70',
            'drucksicherheit': 'INTEGER DEFAULT 70',
            'volle': 'INTEGER DEFAULT 70',
            'raeumer': 'INTEGER DEFAULT 70',
            'sicherheit': 'INTEGER DEFAULT 70'
        }
        
        # Füge fehlende Spalten hinzu
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE player ADD COLUMN {column_name} {column_type}")
                    print(f"  Spalte '{column_name}' zur Player-Tabelle hinzugefügt.")
                except sqlite3.OperationalError as e:
                    print(f"  Fehler beim Hinzufügen der Spalte '{column_name}': {e}")
        
        # Speichere die Änderungen
        conn.commit()
        conn.close()
        print(f"  Migration für {db_file} abgeschlossen.")

if __name__ == "__main__":
    migrate_player_table()
    print("Migration abgeschlossen.")
