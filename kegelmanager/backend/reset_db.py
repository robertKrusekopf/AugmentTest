import os
import sqlite3

def reset_database():
    """Reset the database to its initial state with no played matches."""
    # Bestimme den Pfad zur Datenbank
    db_path = "kegelmanager.db"
    instance_db_path = os.path.join("instance", "kegelmanager.db")

    if os.path.exists(instance_db_path):
        db_path = instance_db_path
    elif not os.path.exists(db_path):
        print("Database does not exist. Please run init_db.py first.")
        return

    print(f"Using database at: {db_path}")

    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Lösche alle Spielerleistungen
        print("Deleting all player performances...")
        cursor.execute("DELETE FROM player_match_performance")

        # 1.1 Lösche alle Spielerstatistiken und -verläufe, falls vorhanden
        try:
            cursor.execute("DELETE FROM player_statistics")
            print("Deleted player statistics.")
        except sqlite3.Error:
            print("No player_statistics table found.")

        try:
            cursor.execute("DELETE FROM player_history")
            print("Deleted player history.")
        except sqlite3.Error:
            print("No player_history table found.")

        # 2. Setze alle Spiele auf nicht gespielt
        print("Resetting all matches to unplayed...")
        cursor.execute("UPDATE match SET is_played = 0, home_score = NULL, away_score = NULL, match_date = NULL")

        # 3. Stelle sicher, dass eine aktuelle Saison gesetzt ist
        print("Setting current season...")
        cursor.execute("UPDATE season SET is_current = 0")
        cursor.execute("UPDATE season SET is_current = 1 WHERE id = (SELECT id FROM season LIMIT 1)")

        # 4. Speichere die Änderungen
        conn.commit()

        # 5. Überprüfe die Ergebnisse
        cursor.execute("SELECT COUNT(*) FROM match")
        total_matches = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM match WHERE is_played = 1")
        played_matches = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM player_match_performance")
        performances = cursor.fetchone()[0]

        print("Database reset complete!")
        print(f"Total matches: {total_matches}")
        print(f"Played matches: {played_matches}")
        print(f"Player performances: {performances}")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_database()
