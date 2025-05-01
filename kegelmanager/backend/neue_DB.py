import os
import sys
import sqlite3
from datetime import datetime
from flask import Flask
from models import db, Season, League, Club, Team, Player, Match, Finance

def create_new_database(db_name, with_sample_data=True):
    """
    Erstellt eine neue Datenbank mit dem angegebenen Namen.

    Args:
        db_name (str): Name der Datenbank (ohne .db Endung)
        with_sample_data (bool): Ob Beispieldaten erstellt werden sollen

    Returns:
        dict: Ergebnis der Operation
    """
    # Stelle sicher, dass der Name keine .db Endung hat
    if db_name.endswith('.db'):
        db_name = db_name[:-3]

    # Stelle sicher, dass der Instance-Ordner existiert
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

    # Vollständiger Pfad zur Datenbank
    db_path = os.path.join(instance_dir, f"{db_name}.db")

    # Überprüfe, ob die Datenbank bereits existiert
    if os.path.exists(db_path):
        print(f"Fehler: Datenbank '{db_name}.db' existiert bereits.")
        return {"success": False, "message": f"Datenbank '{db_name}.db' existiert bereits."}

    # Erstelle eine neue Flask-App und konfiguriere die Datenbank
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # Erstelle alle Tabellen
        db.create_all()
        print(f"Datenbank '{db_name}.db' wurde erstellt.")

        # Füge Beispieldaten hinzu, wenn gewünscht
        if with_sample_data:
            try:
                from init_db import create_sample_data
                create_sample_data(custom_app=app)
                print(f"Beispieldaten wurden zur Datenbank '{db_name}.db' hinzugefügt.")
                return {"success": True, "message": f"Datenbank '{db_name}.db' mit Beispieldaten erstellt."}
            except Exception as e:
                print(f"Fehler beim Hinzufügen von Beispieldaten: {str(e)}")
                return {"success": False, "message": f"Fehler beim Hinzufügen von Beispieldaten: {str(e)}"}
        else:
            print(f"Leere Datenbank '{db_name}.db' wurde erstellt.")
            return {"success": True, "message": f"Leere Datenbank '{db_name}.db' erstellt."}

if __name__ == "__main__":
    # Überprüfe, ob ein Datenbankname als Argument übergeben wurde
    if len(sys.argv) < 2:
        print("Fehler: Bitte geben Sie einen Datenbanknamen an.")
        print("Verwendung: python neue_DB.py <datenbankname> [--no-sample-data]")
        sys.exit(1)

    db_name = sys.argv[1]
    with_sample_data = "--no-sample-data" not in sys.argv

    result = create_new_database(db_name, with_sample_data)

    if result["success"]:
        print(result["message"])
        sys.exit(0)
    else:
        print(f"Fehler: {result['message']}")
        sys.exit(1)
