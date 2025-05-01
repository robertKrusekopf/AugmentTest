import os
import init_db
from flask import Flask
from models import db

# Create a test Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Create the database tables and sample data
with app.app_context():
    # Create tables
    db.create_all()
    print("Database tables created.")
    
    # Create sample data
    init_db.create_sample_data_alt(app)
    
print("Test completed successfully!")
