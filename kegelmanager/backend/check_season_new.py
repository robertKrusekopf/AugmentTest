from flask import Flask
from models import db, Season

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    seasons = Season.query.all()
    print(f"Anzahl der Saisons: {len(seasons)}")
    
    for season in seasons:
        print(f"Saison: {season.name}, Aktuell: {season.is_current}")
