import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'kegelmanager', 'backend'))

from models import LeagueHistory, League, Season, db
from app import app

with app.app_context():
    # Test the API logic for a specific league
    current_season = Season.query.filter_by(is_current=True).first()
    print(f'Current season: {current_season.name} (ID: {current_season.id})')
    
    # Get a league from current season
    current_league = League.query.filter_by(season_id=current_season.id).first()
    if current_league:
        print(f'Testing with league: {current_league.name} (Level {current_league.level}, ID: {current_league.id})')
        
        # Test the same logic as the API endpoint
        history_entries = LeagueHistory.query.filter_by(
            league_name=current_league.name,
            league_level=current_league.level
        ).order_by(LeagueHistory.season_id.desc()).all()
        
        print(f'Found {len(history_entries)} history entries for this league')
        
        # Group by season like the API does
        seasons_data = {}
        for entry in history_entries:
            season_id = entry.season_id
            if season_id not in seasons_data:
                seasons_data[season_id] = {
                    'season_id': season_id,
                    'season_name': entry.season_name,
                    'standings': []
                }
            seasons_data[season_id]['standings'].append(entry.to_dict())
        
        print(f'Grouped into {len(seasons_data)} seasons:')
        for season_id, season_data in seasons_data.items():
            season_name = season_data['season_name']
            standings_count = len(season_data['standings'])
            print(f'  - Season {season_name} (ID: {season_id}): {standings_count} teams')
            
        # Test the API response format
        seasons_list = list(seasons_data.values())
        seasons_list.sort(key=lambda x: x['season_id'], reverse=True)
        
        result = {
            'league_name': current_league.name,
            'league_level': current_league.level,
            'seasons': seasons_list
        }
        
        print(f'API would return: {len(result["seasons"])} seasons')
        if result['seasons']:
            print(f'First season: {result["seasons"][0]["season_name"]} with {len(result["seasons"][0]["standings"])} teams')
    else:
        print('No leagues found in current season')
