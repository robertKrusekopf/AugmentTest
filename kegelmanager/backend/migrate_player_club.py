import os
import sqlite3
from flask import Flask
from models import db, Player, Club

def migrate_player_club_relationship():
    """
    Migriert die Player-Tabelle, um die Verknüpfung zum Verein hinzuzufügen.
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
        if 'club_id' not in existing_columns:
            try:
                cursor.execute("ALTER TABLE player ADD COLUMN club_id INTEGER REFERENCES club(id)")
                print(f"  Spalte 'club_id' zur Player-Tabelle hinzugefügt.")
            except sqlite3.OperationalError as e:
                print(f"  Fehler beim Hinzufügen der Spalte 'club_id': {e}")
        
        # Speichere die Änderungen
        conn.commit()
        
        # Jetzt müssen wir die bestehenden Spieler mit ihren Vereinen verknüpfen
        # Wir nehmen an, dass ein Spieler zum Verein des ersten Teams gehört, in dem er spielt
        cursor.execute("""
            SELECT p.id, t.club_id
            FROM player p
            JOIN player_team pt ON p.id = pt.player_id
            JOIN team t ON pt.team_id = t.id
            WHERE p.club_id IS NULL
        """)
        
        player_club_mappings = cursor.fetchall()
        
        for player_id, club_id in player_club_mappings:
            cursor.execute("UPDATE player SET club_id = ? WHERE id = ?", (club_id, player_id))
            print(f"  Spieler {player_id} mit Verein {club_id} verknüpft.")
        
        # Speichere die Änderungen
        conn.commit()
        conn.close()
        print(f"  Migration für {db_file} abgeschlossen.")

if __name__ == "__main__":
    migrate_player_club_relationship()
    print("Migration abgeschlossen.")
