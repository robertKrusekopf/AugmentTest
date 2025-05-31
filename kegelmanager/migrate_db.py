import requests
import os
import sys

def migrate_database():
    """Run the database migration to add new tables."""
    print("Starting database migration...")
    
    # Get the API URL from environment or use default
    api_url = os.environ.get('API_URL', 'http://localhost:5000')
    
    try:
        # Call the migration endpoint
        response = requests.post(f"{api_url}/api/migrate_db")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Migration successful: {result['message']}")
            
            if result['new_tables_created']:
                print(f"New tables created: {', '.join(result['new_tables_created'])}")
            else:
                print("No new tables needed to be created.")
                
            return True
        else:
            print(f"Migration failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
