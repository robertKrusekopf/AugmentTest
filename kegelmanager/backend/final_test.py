import init_db
from flask import Flask
from models import db

# Create a new Flask app for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///final_test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables and sample data
with app.app_context():
    db.create_all()
    print("Database tables created.")

    # Create sample data with our custom app
    init_db.create_sample_data_alt(custom_app=app)

print("Test completed successfully!")
