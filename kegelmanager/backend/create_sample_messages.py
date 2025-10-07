"""
Script to create sample messages for testing the message system.
"""

import os
from datetime import datetime, timedelta
from flask import Flask
from models import db, Message, Club, Team, Player, Match

def create_sample_messages(db_path):
    """Create sample messages in the database."""
    print(f"\n{'='*60}")
    print(f"Creating sample messages in: {db_path}")
    print(f"{'='*60}\n")
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        try:
            # Get some entities for linking
            first_club = Club.query.first()
            first_team = Team.query.first()
            first_player = Player.query.first()
            first_match = Match.query.first()
            
            # Sample messages
            sample_messages = [
                {
                    'subject': 'Willkommen im Kegelmanager!',
                    'content': 'Herzlich willkommen im Kegelmanager! Dies ist Ihr Postfach für wichtige Nachrichten und Benachrichtigungen.\n\nHier erhalten Sie Informationen über:\n- Spielergebnisse\n- Transferangebote\n- Verletzungen\n- Vertragsverlängerungen\n- Und vieles mehr!\n\nViel Erfolg bei der Verwaltung Ihres Vereins!',
                    'message_type': 'info',
                    'is_read': False,
                    'created_at': datetime.utcnow()
                },
                {
                    'subject': 'Neuer Spieltag verfügbar',
                    'content': 'Der nächste Spieltag steht an! Vergessen Sie nicht, Ihre Aufstellung zu überprüfen und gegebenenfalls anzupassen.\n\nViel Erfolg bei den kommenden Spielen!',
                    'message_type': 'info',
                    'is_read': False,
                    'created_at': datetime.utcnow() - timedelta(hours=2)
                },
                {
                    'subject': 'Wichtig: Vertrag läuft aus',
                    'content': 'Der Vertrag eines Ihrer Spieler läuft bald aus. Denken Sie daran, rechtzeitig Verhandlungen aufzunehmen, um den Spieler zu halten.',
                    'message_type': 'warning',
                    'is_read': False,
                    'created_at': datetime.utcnow() - timedelta(hours=5),
                    'related_player_id': first_player.id if first_player else None
                },
                {
                    'subject': 'Glückwunsch zum Sieg!',
                    'content': 'Herzlichen Glückwunsch! Ihre Mannschaft hat das letzte Spiel gewonnen. Weiter so!',
                    'message_type': 'success',
                    'is_read': True,
                    'created_at': datetime.utcnow() - timedelta(days=1),
                    'related_team_id': first_team.id if first_team else None,
                    'related_match_id': first_match.id if first_match else None
                },
                {
                    'subject': 'Transferangebot erhalten',
                    'content': 'Sie haben ein Transferangebot für einen Ihrer Spieler erhalten. Prüfen Sie die Details im Transfer-Bereich.',
                    'message_type': 'info',
                    'is_read': True,
                    'created_at': datetime.utcnow() - timedelta(days=2),
                    'related_club_id': first_club.id if first_club else None
                },
                {
                    'subject': 'Finanzielle Warnung',
                    'content': 'Achtung! Der Kontostand Ihres Vereins ist niedrig. Achten Sie auf Ihre Ausgaben und versuchen Sie, die Einnahmen zu erhöhen.',
                    'message_type': 'warning',
                    'is_read': True,
                    'created_at': datetime.utcnow() - timedelta(days=3),
                    'related_club_id': first_club.id if first_club else None
                },
                {
                    'subject': 'Saisonende naht',
                    'content': 'Die aktuelle Saison geht bald zu Ende. Bereiten Sie sich auf die Saisonwechsel-Phase vor und planen Sie Ihre Transfers.',
                    'message_type': 'info',
                    'is_read': True,
                    'created_at': datetime.utcnow() - timedelta(days=5)
                }
            ]
            
            # Create messages
            created_count = 0
            for msg_data in sample_messages:
                message = Message(**msg_data)
                db.session.add(message)
                created_count += 1
            
            # Commit changes
            db.session.commit()
            print(f"✓ Created {created_count} sample messages successfully!")
            
            return True
            
        except Exception as e:
            print(f"✗ Error creating sample messages: {str(e)}")
            db.session.rollback()
            return False


def main():
    """Main function."""
    print("\n" + "="*60)
    print("CREATE SAMPLE MESSAGES")
    print("="*60)
    
    # Get the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for databases
    datenbanken_dir = os.path.join(backend_dir, "Datenbanken")
    instance_dir = os.path.join(backend_dir, "instance")
    
    databases = []
    
    # Find all .db files
    if os.path.exists(datenbanken_dir):
        for file in os.listdir(datenbanken_dir):
            if file.endswith('.db'):
                db_path = os.path.join(datenbanken_dir, file)
                databases.append((file, db_path))
    
    if os.path.exists(instance_dir):
        for file in os.listdir(instance_dir):
            if file.endswith('.db'):
                db_path = os.path.join(instance_dir, file)
                databases.append((file, db_path))
    
    main_db = os.path.join(backend_dir, "kegelmanager.db")
    if os.path.exists(main_db):
        databases.append(("kegelmanager.db", main_db))
    
    if not databases:
        print("\n✗ No databases found.")
        return
    
    print(f"\nFound {len(databases)} database(s):")
    for i, (name, path) in enumerate(databases, 1):
        print(f"  {i}. {name}")
    
    # Ask user to select database
    print("\nSelect database (enter number, or 'all' for all databases):")
    choice = input("> ").strip().lower()
    
    if choice == 'all':
        selected_databases = databases
    else:
        try:
            index = int(choice) - 1
            if 0 <= index < len(databases):
                selected_databases = [databases[index]]
            else:
                print("Invalid selection.")
                return
        except ValueError:
            print("Invalid input.")
            return
    
    # Create sample messages
    for name, db_path in selected_databases:
        create_sample_messages(db_path)
    
    print("\n" + "="*60)
    print("DONE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

