from app import app, db
from models import Season, Team, Player, Club
from simulation import simulate_match
import copy

def test_simulation():
    with app.app_context():
        # Get the first two teams
        teams = Team.query.limit(2).all()

        if len(teams) < 2:
            print("Not enough teams found for testing")
            return

        # Print team details
        print(f"Team 1: {teams[0].name}")
        print(f"Team 1 League Level: {teams[0].league.level}")
        print(f"Team 1 Players:")
        for player in teams[0].players[:6]:
            print(f"  - {player.name}: Strength={player.strength}, Volle={player.volle}, Räumer={player.raeumer}, Konstanz={player.konstanz}, Drucksicherheit={player.drucksicherheit}")

        print(f"\nTeam 2: {teams[1].name}")
        print(f"Team 2 League Level: {teams[1].league.level}")
        print(f"Team 2 Players:")
        for player in teams[1].players[:6]:
            print(f"  - {player.name}: Strength={player.strength}, Volle={player.volle}, Räumer={player.raeumer}, Konstanz={player.konstanz}, Drucksicherheit={player.drucksicherheit}")

        # Run simulation 3 times to see variation
        print("\nRunning 3 simulations with original teams:")
        for i in range(3):
            result = simulate_match(teams[0], teams[1])
            print(f"\nSimulation {i+1}:")
            print(f"Match result: {teams[0].name} vs {teams[1].name}")
            print(f"Score: {result['home_score']} - {result['away_score']}")
            print(f"Match points: {result['home_match_points']} - {result['away_match_points']}")
            print(f"Winner: {result['winner']}")

        # Test the new player selection logic
        print("\nTesting new player selection logic:")

        # Get all players from the first team's club
        club1 = teams[0].club
        club_players = Player.query.filter_by(club_id=club1.id).all()

        print(f"\nClub: {club1.name}")
        print(f"Total players in club: {len(club_players)}")

        # Get all teams from this club
        club_teams = Team.query.filter_by(club_id=club1.id).all()
        print(f"Teams in club: {len(club_teams)}")
        for team in club_teams:
            print(f"  - {team.name} (League Level: {team.league.level if team.league else 'None'})")

        # Run a simulation with the first team
        print("\nRunning simulation with team selection from club:")
        result = simulate_match(teams[0], teams[1])
        print(f"Match result: {teams[0].name} vs {teams[1].name}")
        print(f"Score: {result['home_score']} - {result['away_score']}")
        print(f"Match points: {result['home_match_points']} - {result['away_match_points']}")
        print(f"Winner: {result['winner']}")

if __name__ == "__main__":
    test_simulation()
