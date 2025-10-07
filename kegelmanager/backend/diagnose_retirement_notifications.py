"""
Comprehensive diagnostic script to investigate retirement notification issues.
This script checks:
1. Whether the GameSettings table exists and has a manager_club_id set
2. Whether there are any retired players in the database
3. Whether retired players belong to the manager's club
4. Whether retirement messages were created for those players
5. The complete flow from retirement to message creation
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import GameSettings, Club, Player, Message, Season


def diagnose_retirement_notifications():
    """Comprehensive diagnosis of retirement notification system."""
    with app.app_context():
        print("=" * 80)
        print("RETIREMENT NOTIFICATION DIAGNOSTIC REPORT")
        print("=" * 80)
        
        # Step 1: Check GameSettings
        print("\n" + "=" * 80)
        print("STEP 1: Checking Game Settings")
        print("=" * 80)
        
        settings = GameSettings.query.first()
        
        if not settings:
            print("\n❌ ISSUE FOUND: No GameSettings record exists in database!")
            print("   This means the game_settings table is empty.")
            print("   The retirement notification system requires a GameSettings record.")
            print("\n   SOLUTION: Create a GameSettings record and set manager_club_id")
            return
        
        print(f"\n✅ GameSettings record found (ID: {settings.id})")
        print(f"   Manager Club ID: {settings.manager_club_id}")
        
        if not settings.manager_club_id:
            print("\n⚠️  ISSUE FOUND: manager_club_id is NULL!")
            print("   No manager club has been selected in the Settings page.")
            print("   Retirement notifications will NOT be created without a manager club.")
            print("\n   SOLUTION: Go to Settings page and select a manager club")
            
            # Show available clubs
            print("\n   Available clubs to choose from:")
            clubs = Club.query.order_by(Club.name).limit(10).all()
            for club in clubs:
                print(f"      ID {club.id}: {club.name}")
            print(f"      ... (showing first 10 of {Club.query.count()} clubs)")
            return
        
        # Get the manager club
        manager_club = Club.query.get(settings.manager_club_id)
        if not manager_club:
            print(f"\n❌ ISSUE FOUND: Manager club ID {settings.manager_club_id} does not exist!")
            print("   The manager_club_id points to a non-existent club.")
            print("\n   SOLUTION: Update manager_club_id to a valid club ID")
            return
        
        print(f"   Manager Club Name: {manager_club.name}")
        print(f"\n✅ Manager club is properly configured")
        
        # Step 2: Check for retired players
        print("\n" + "=" * 80)
        print("STEP 2: Checking for Retired Players")
        print("=" * 80)
        
        all_retired_players = Player.query.filter_by(is_retired=True).all()
        print(f"\nTotal retired players in database: {len(all_retired_players)}")
        
        if len(all_retired_players) == 0:
            print("\n⚠️  No retired players found in database!")
            print("   This could mean:")
            print("   - No season transition has occurred yet")
            print("   - No players have reached retirement age yet")
            print("   - The retirement system is not working")
            
            # Check if any players are close to retirement
            current_season = Season.query.filter_by(is_current=True).first()
            if current_season:
                print(f"\n   Current season: {current_season.year}")
            
            # Find players who should retire soon
            players_near_retirement = Player.query.filter(
                Player.is_retired == False,
                Player.retirement_age.isnot(None),
                Player.age >= Player.retirement_age - 2
            ).limit(10).all()
            
            if players_near_retirement:
                print(f"\n   Players close to retirement (within 2 years):")
                for p in players_near_retirement:
                    club_name = p.club.name if p.club else "No Club"
                    print(f"      {p.name} - Age: {p.age}, Retirement Age: {p.retirement_age}, Club: {club_name}")
            else:
                print("\n   No players are close to retirement age")
            
            return
        
        # Show some retired players
        print(f"\nRetired players (showing first 10):")
        for p in all_retired_players[:10]:
            club_name = p.club.name if p.club else "No Club"
            season_name = p.retirement_season.year if p.retirement_season else "Unknown"
            print(f"   {p.name} - Age: {p.age}, Club: {club_name}, Retired in: {season_name}")
        
        # Step 3: Check retired players from manager's club
        print("\n" + "=" * 80)
        print("STEP 3: Checking Retired Players from Manager's Club")
        print("=" * 80)
        
        manager_club_retired_players = Player.query.filter_by(
            is_retired=True,
            club_id=settings.manager_club_id
        ).all()
        
        print(f"\nRetired players from {manager_club.name}: {len(manager_club_retired_players)}")
        
        if len(manager_club_retired_players) == 0:
            print(f"\n⚠️  No players from {manager_club.name} have retired yet!")
            print("   This is why you haven't seen any retirement notifications.")
            print("   Retirement notifications are only created for players from your managed club.")
            
            # Check active players from manager's club
            active_players = Player.query.filter_by(
                is_retired=False,
                club_id=settings.manager_club_id
            ).all()
            print(f"\n   Active players in {manager_club.name}: {len(active_players)}")
            
            if active_players:
                # Find players close to retirement
                near_retirement = [p for p in active_players if p.retirement_age and p.age >= p.retirement_age - 2]
                if near_retirement:
                    print(f"\n   Players from {manager_club.name} close to retirement:")
                    for p in near_retirement[:5]:
                        print(f"      {p.name} - Age: {p.age}, Retirement Age: {p.retirement_age}")
                else:
                    print(f"\n   No players from {manager_club.name} are close to retirement")
            
            return
        
        print(f"\nRetired players from {manager_club.name}:")
        for p in manager_club_retired_players:
            season_name = p.retirement_season.year if p.retirement_season else "Unknown"
            print(f"   {p.name} - Age: {p.age}, Retired in: {season_name}")
        
        # Step 4: Check if messages were created for these players
        print("\n" + "=" * 80)
        print("STEP 4: Checking Retirement Messages")
        print("=" * 80)
        
        # Get all retirement messages
        all_messages = Message.query.all()
        print(f"\nTotal messages in database: {len(all_messages)}")
        
        # Filter retirement messages
        retirement_messages = [m for m in all_messages if "Ruhestand" in m.subject or "retired" in m.subject.lower()]
        print(f"Retirement-related messages: {len(retirement_messages)}")
        
        if len(retirement_messages) == 0:
            print("\n❌ ISSUE FOUND: No retirement messages exist!")
            print(f"   Expected: {len(manager_club_retired_players)} messages (one for each retired player)")
            print(f"   Found: 0 messages")
            print("\n   This indicates the create_retirement_message() function is not being called")
            print("   or is failing silently.")
            
            # Check if the issue is in the code
            print("\n   Possible causes:")
            print("   1. The start_new_season() function is not calling create_retirement_message()")
            print("   2. The create_retirement_message() function is encountering an error")
            print("   3. The database commit is failing")
            print("   4. The manager_club_id was set AFTER the players retired")
            
            # Check when players retired vs when manager club was set
            if manager_club_retired_players:
                latest_retirement_season = max(
                    p.retirement_season_id for p in manager_club_retired_players if p.retirement_season_id
                )
                print(f"\n   Latest retirement season ID: {latest_retirement_season}")
                print("   If the manager club was set AFTER these retirements occurred,")
                print("   no messages would have been created.")
                print("\n   SOLUTION: Wait for the next season transition to test the system")
            
            return
        
        # Show retirement messages
        print(f"\nRetirement messages found:")
        for msg in retirement_messages:
            player_name = msg.related_player.name if msg.related_player else "Unknown"
            club_name = msg.related_club.name if msg.related_club else "Unknown"
            print(f"   Message ID {msg.id}: {msg.subject}")
            print(f"      Player: {player_name}, Club: {club_name}")
            print(f"      Created: {msg.created_at}, Read: {msg.is_read}")
        
        # Check if all retired players from manager's club have messages
        players_with_messages = set(m.related_player_id for m in retirement_messages if m.related_player_id)
        retired_player_ids = set(p.id for p in manager_club_retired_players)
        
        missing_messages = retired_player_ids - players_with_messages
        
        if missing_messages:
            print(f"\n⚠️  ISSUE FOUND: {len(missing_messages)} retired players are missing messages!")
            print("   Players without retirement messages:")
            for player_id in missing_messages:
                player = Player.query.get(player_id)
                if player:
                    season_name = player.retirement_season.year if player.retirement_season else "Unknown"
                    print(f"      {player.name} - Retired in: {season_name}")
            
            print("\n   This likely means the manager club was set AFTER these players retired.")
            print("   Messages are only created at the moment of retirement, not retroactively.")
        else:
            print(f"\n✅ All retired players from {manager_club.name} have retirement messages!")
        
        # Final summary
        print("\n" + "=" * 80)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 80)
        print(f"\n✅ GameSettings configured: Yes")
        print(f"✅ Manager club set: {manager_club.name} (ID: {settings.manager_club_id})")
        print(f"✅ Total retired players: {len(all_retired_players)}")
        print(f"✅ Retired from manager's club: {len(manager_club_retired_players)}")
        print(f"✅ Retirement messages: {len(retirement_messages)}")
        
        if missing_messages:
            print(f"\n⚠️  {len(missing_messages)} players retired before manager club was set")
            print("   Wait for next season transition to test the notification system")
        elif len(manager_club_retired_players) == 0:
            print(f"\n⚠️  No players from {manager_club.name} have retired yet")
            print("   Wait for season transitions until players reach retirement age")
        else:
            print("\n✅ System is working correctly!")
        
        print("\n" + "=" * 80)


if __name__ == '__main__':
    diagnose_retirement_notifications()

