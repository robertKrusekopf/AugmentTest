"""
Check if VSG Löbitz 71 exists in the database and what its ID is.
"""
from app import app, db
from models import Club

with app.app_context():
    # Find VSG Löbitz 71
    club = Club.query.filter(Club.name.like('%Löbitz%')).first()
    
    if club:
        print(f"Found club: {club.name}")
        print(f"Club ID: {club.id}")
        print(f"\nThis suggests that localStorage has managedClubId={club.id}")
        print(f"from a previous database session.")
    else:
        print("VSG Löbitz 71 not found in database")
    
    # List all clubs to see the order
    print("\n" + "="*60)
    print("All clubs in database (ordered by ID):")
    print("="*60)
    clubs = Club.query.order_by(Club.id).all()
    for c in clubs[:10]:  # Show first 10
        print(f"ID {c.id}: {c.name}")

