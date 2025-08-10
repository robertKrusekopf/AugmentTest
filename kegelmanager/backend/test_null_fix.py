from flask import Flask
from models import db, Player
from simulation import calculate_player_rating

# Create Flask app and context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/RealeDB_complete_final.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Test mit einem Spieler der NULL-Werte haben könnte
    player = Player.query.first()
    if player:
        print(f'Player: {player.name}')
        print(f'Strength: {player.strength}')
        print(f'Konstanz: {player.konstanz}')
        print(f'Drucksicherheit: {player.drucksicherheit}')
        print(f'Volle: {player.volle}')
        print(f'Raeumer: {player.raeumer}')
        
        try:
            rating = calculate_player_rating(player)
            print(f'Rating: {rating}')
            print('SUCCESS: Rating calculation worked!')
        except Exception as e:
            print(f'ERROR: {e}')
    else:
        print('No players found')
