import os
import sqlite3
import glob
import shutil
from datetime import datetime
from flask import current_app

def get_database_dir():
    """Get the directory where databases are stored."""
    # Use the instance folder for database storage
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")

def ensure_db_dir_exists():
    """Ensure the database directory exists."""
    db_dir = get_database_dir()
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return db_dir

def list_databases():
    """List all available databases."""
    db_dir = ensure_db_dir_exists()

    # Find all .db files in the database directory
    db_files = glob.glob(os.path.join(db_dir, "*.db"))

    databases = []
    for db_file in db_files:
        db_name = os.path.basename(db_file)
        # Get creation date and last modified date
        stats = os.stat(db_file)
        created = datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

        # Get database size in MB
        size_mb = round(stats.st_size / (1024 * 1024), 2)

        # Try to get some basic info from the database
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Get season info
            cursor.execute("SELECT name FROM season WHERE is_current = 1")
            season_row = cursor.fetchone()
            current_season = season_row[0] if season_row else "Unbekannt"

            # Get club count
            cursor.execute("SELECT COUNT(*) FROM club")
            club_count = cursor.fetchone()[0]

            # Get player count
            cursor.execute("SELECT COUNT(*) FROM player")
            player_count = cursor.fetchone()[0]

            conn.close()

            status = "OK"
        except Exception as e:
            # Don't hide database errors with fallback values
            raise RuntimeError(f"Fehler beim Lesen der Datenbank {db_file}: {str(e)}")

        databases.append({
            "name": db_name,
            "path": db_file,
            "created": created,
            "modified": modified,
            "size_mb": size_mb,
            "current_season": current_season,
            "club_count": club_count,
            "player_count": player_count,
            "status": status
        })

    return databases

def create_new_database(db_name, with_sample_data=True):
    """Create a new database with the given name."""
    if not db_name.endswith('.db'):
        db_name = f"{db_name}.db"

    db_dir = ensure_db_dir_exists()
    db_path = os.path.join(db_dir, db_name)

    # Check if database already exists
    if os.path.exists(db_path):
        return {"success": False, "message": f"Datenbank '{db_name}' existiert bereits."}

    # Create a new database
    from flask import Flask
    from models import db, Season

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()

        # Add sample data if requested
        if with_sample_data:
            from init_db import create_sample_data
            create_sample_data()
            return {"success": True, "message": f"Datenbank '{db_name}' mit Beispieldaten erstellt."}
        else:
            return {"success": True, "message": f"Leere Datenbank '{db_name}' erstellt."}

def extend_existing_database(source_db_path, target_db_name):
    """Extend an existing database by copying it and adding missing data."""
    from extend_existing_db import extend_existing_database as extend_db
    return extend_db(source_db_path, target_db_name)

def select_database(db_name):
    """Select a database to use."""
    print(f"=== DEBUG: Wähle Datenbank aus: {db_name} ===")

    if not db_name.endswith('.db'):
        db_name = f"{db_name}.db"
        print(f"DEBUG: Datenbankname mit .db-Endung: {db_name}")

    db_dir = ensure_db_dir_exists()
    db_path = os.path.join(db_dir, db_name)
    print(f"DEBUG: Vollständiger Datenbankpfad: {db_path}")

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"DEBUG: Datenbank existiert nicht: {db_path}")
        return {"success": False, "message": f"Datenbank '{db_name}' existiert nicht."}

    try:
        # Überprüfe, ob die Datenbank gültig ist
        print(f"DEBUG: Überprüfe, ob die Datenbank gültig ist: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Versuche, eine einfache Abfrage auszuführen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
        tables = cursor.fetchall()
        print(f"DEBUG: Gefundene Tabellen: {tables}")

        # Überprüfe, ob die Club-Tabelle existiert und zeige die Clubs an
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='club'")
        if cursor.fetchone():
            cursor.execute("SELECT id, name FROM club")
            clubs = cursor.fetchall()
            print(f"DEBUG: Clubs in der Datenbank: {clubs}")
        else:
            print("DEBUG: Keine Club-Tabelle in der Datenbank gefunden")

        conn.close()

        # Speichere den Datenbanknamen in einer Umgebungsvariable oder Datei
        # für die nächste Anwendungsausführung
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        print(f"DEBUG: Schreibe Datenbankpfad in .env-Datei: {env_file}")

        # Sicherstellen, dass der Pfad absolut ist
        abs_db_path = os.path.abspath(db_path)
        print(f"DEBUG: Absoluter Datenbankpfad: {abs_db_path}")

        # Schreibe die .env-Datei
        with open(env_file, "w") as f:
            f.write(f"DATABASE_PATH={abs_db_path}\n")

        # Überprüfe, ob die .env-Datei korrekt geschrieben wurde
        with open(env_file, "r") as f:
            env_content = f.read()
            print(f"DEBUG: Inhalt der .env-Datei nach dem Schreiben: {env_content}")

        # Zusätzlich: Schreibe den Datenbankpfad in eine separate Datei
        db_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "selected_db.txt")
        print(f"DEBUG: Schreibe Datenbankpfad in separate Datei: {db_config_file}")
        with open(db_config_file, "w") as f:
            f.write(abs_db_path)

        print(f"DEBUG: Datenbankpfad in separate Datei geschrieben: {db_config_file}")

        print(f"DEBUG: Datenbank erfolgreich ausgewählt: {db_path}")
        return {
            "success": True,
            "message": f"Datenbank '{db_name}' ausgewählt. Die Anwendung wird die Datenbank beim nächsten Start verwenden.",
            "db_path": db_path
        }
    except Exception as e:
        print(f"DEBUG: Fehler beim Auswählen der Datenbank: {str(e)}")
        return {
            "success": False,
            "message": f"Fehler beim Auswählen der Datenbank: {str(e)}"
        }

def delete_database(db_name):
    """Delete a database."""
    if not db_name.endswith('.db'):
        db_name = f"{db_name}.db"

    db_dir = ensure_db_dir_exists()
    db_path = os.path.join(db_dir, db_name)

    # Check if database exists
    if not os.path.exists(db_path):
        return {"success": False, "message": f"Datenbank '{db_name}' existiert nicht."}

    # Delete the database file
    try:
        os.remove(db_path)
        return {"success": True, "message": f"Datenbank '{db_name}' wurde gelöscht."}
    except Exception as e:
        return {"success": False, "message": f"Fehler beim Löschen der Datenbank: {str(e)}"}
