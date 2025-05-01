from flask import Flask
from models import db, Season

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Setze alle Saisons auf nicht aktuell
    Season.query.update({Season.is_current: False})

    # Finde die erste Saison und setze sie auf aktuell
    season = Season.query.first()
    if season:
        season.is_current = True
        db.session.commit()
        print(f"Saison '{season.name}' wurde als aktuelle Saison gesetzt.")
    else:
        print("Keine Saison gefunden.")
