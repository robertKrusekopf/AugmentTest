#!/usr/bin/env python3
"""
Test script to debug simulation errors.
"""

import os
import sys
import traceback

# Add current directory to path
sys.path.append('.')

# Import Flask app and models
from app import app, db
from models import Season
from simulation import simulate_season

def test_simulation():
    """Test the simulation and catch any errors."""
    with app.app_context():
        try:
            # Get the first season
            season = Season.query.first()
            if not season:
                print("No season found in database")
                return
            
            print(f"Testing simulation with season: {season.name}")
            
            # Try to simulate the season
            result = simulate_season(season, create_new_season=False)
            print(f"Simulation completed successfully: {result}")
            
        except Exception as e:
            print(f"Simulation error: {str(e)}")
            print("Full traceback:")
            traceback.print_exc()

if __name__ == "__main__":
    test_simulation()
