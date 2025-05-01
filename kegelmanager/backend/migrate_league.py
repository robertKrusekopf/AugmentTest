import os
import sqlite3
from flask import Flask
from models import db, League

def migrate_league_table():
    """
    Migriert die League-Tabelle, um die neuen Felder hinzuzufügen.
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
        
        # Überprüfe, ob die League-Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='league'")
        if not cursor.fetchone():
            print(f"  League-Tabelle existiert nicht in {db_file}.")
            conn.close()
            continue
        
        # Überprüfe, welche Spalten bereits existieren
        cursor.execute("PRAGMA table_info(league)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Neue Spalten, die hinzugefügt werden sollen
        new_columns = {
            'bundesland': 'TEXT',
            'landkreis': 'TEXT',
            'altersklasse': 'TEXT',
            'aufstieg_liga_id': 'INTEGER REFERENCES league(id)',
            'abstieg_liga_id': 'INTEGER REFERENCES league(id)',
            'anzahl_aufsteiger': 'INTEGER DEFAULT 2',
            'anzahl_absteiger': 'INTEGER DEFAULT 2'
        }
        
        # Füge fehlende Spalten hinzu
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE league ADD COLUMN {column_name} {column_type}")
                    print(f"  Spalte '{column_name}' zur League-Tabelle hinzugefügt.")
                except sqlite3.OperationalError as e:
                    print(f"  Fehler beim Hinzufügen der Spalte '{column_name}': {e}")
        
        # Speichere die Änderungen
        conn.commit()
        conn.close()
        print(f"  Migration für {db_file} abgeschlossen.")

if __name__ == "__main__":
    migrate_league_table()
    print("Migration abgeschlossen.")
