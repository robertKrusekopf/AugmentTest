import os
import sys
import random
import numpy as np
from datetime import datetime, timedelta
from flask import Flask
from models import db, Player, Team, Club, League, Match, Season, Finance
import xlrd
import requests
from bs4 import BeautifulSoup


# Funktionen für die Namensgenerierung und Spielerstärke
def load_names_from_excel(file_path):
    """Load names and their cumulative frequencies from an Excel file."""
    book = xlrd.open_workbook(file_path)
    sheet = book.sheet_by_index(0)

    names = []
    frequencies = []

    for r in range(sheet.nrows):
        name = sheet.cell_value(r, 0)
        frequency = sheet.cell_value(r, 1)

        names.append(name)
        frequencies.append(frequency)

    return names, frequencies

def select_random_name(names, frequencies):
    """Select a random name based on cumulative frequencies."""
    # Get the maximum cumulative frequency (last value)
    max_frequency = frequencies[-1]

    # Generate a random number between 0 and max_frequency
    random_value = random.uniform(0, max_frequency)

    # Find the first name with a cumulative frequency greater than the random value
    for i, freq in enumerate(frequencies):
        if random_value <= freq:
            return names[i]

    # Fallback (should not happen)
    return names[-1]

def calculate_lane_quality_for_club(club):
    """
    Berechnet die Bahnqualität für einen Verein basierend auf der besten Ligaebene seiner Teams.
    Ligaebene 5 bleibt bei der ursprünglichen Berechnung (0.9-1.05).
    Für jede Ligaebene darüber wird der Bereich um 0.01 besser.
    Für jede Ligaebene darunter wird der Bereich um 0.01 schlechter.
    """
    best_league_level = club.get_best_league_level()

    if best_league_level is None:
        # Fallback: Standardberechnung für Ligaebene 5
        best_league_level = 5

    # Basis-Berechnung für Ligaebene 5: 0.9 bis 1.05 (Mittelwert 0.975)
    base_min = 0.9
    base_max = 1.05
    base_mean = 0.975

    # Anpassung basierend auf Ligaebene
    level_diff = 5 - best_league_level  # Positiv für bessere Ligen, negativ für schlechtere
    adjustment = level_diff * 0.01

    # Neue Bereiche berechnen
    adjusted_min = base_min + adjustment
    adjusted_max = base_max + adjustment
    adjusted_mean = base_mean + adjustment

    # Standardabweichung so berechnen, dass 90% der Werte im Bereich liegen
    std_dev = (adjusted_max - adjusted_min) / (2 * 1.645)

    # Normalverteilte Bahnqualität generieren
    lane_quality = np.random.normal(adjusted_mean, std_dev)

    # Auf den gewünschten Bereich begrenzen
    lane_quality = max(adjusted_min, min(adjusted_max, lane_quality))

    print(f"INFO: Club {club.name} - Beste Liga: {best_league_level}, Bahnqualität: {lane_quality:.3f} (Bereich: {adjusted_min:.2f}-{adjusted_max:.2f})")

    return lane_quality

def calculate_player_attribute_by_league_level(league_level, is_youth_team=False, is_second_team=False, team_staerke=None):
    """
    Calculate player attributes based on league level and team strength.

    Args:
        league_level: The level of the league (1 is top level, 10 is lowest)
        is_youth_team: Whether the team is a youth team
        is_second_team: Whether the team is a second team (e.g. "Club Name II")
        team_staerke: The strength value of the team, used as a small modifier

    Returns:
        A dictionary with base values for player attributes
    """
    # Linear interpolation between level 1 (avg 80) and level 10 (avg 30)
    # Base formula: 80 - (league_level - 1) * 5.5
    base_strength = 80 - (league_level - 1) * 5.5

    # Add small team strength modifier (max ±5 points)
    if team_staerke is not None:
        team_modifier = (team_staerke - 50) * 0.1  # Convert 30-99 range to -2 to +4.9
        base_strength += team_modifier

    # Youth team penalty
    if is_youth_team:
        base_strength -= 10

    # Second team penalty
    if is_second_team:
        base_strength -= 5

    # Calculate standard deviation (higher leagues have more consistent players)
    std_dev = 5 + (league_level - 1) * 0.5

    # Generate attribute values using normal distribution
    player_strength = max(30, min(99, int(np.random.normal(base_strength, std_dev))))

    attributes = {
        'strength': player_strength,
        'talent': random.randint(1, 10),  # Talent is independent of league level
    }

    # Calculate other attributes based on strength
    base_attr_value = 60 + (attributes['strength'] - 50) * 0.6
    attr_std_dev = 5 + (league_level - 1) * 0.3

    # Generate all other attributes
    for attr in ['ausdauer', 'konstanz', 'drucksicherheit',
                'volle', 'raeumer', 'sicherheit', 'auswaerts', 'start', 'mitte', 'schluss']:
        attributes[attr] = min(99, int(np.random.normal(base_attr_value, attr_std_dev)))

    return attributes


# Erstelle eine Flask-App, aber konfiguriere sie nicht sofort
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False




def create_sample_data(custom_app=None):
    book = xlrd.open_workbook("Daten.xls")
    sheet = book.sheet_by_name("Input")
    url_arr = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]


    print("=== DEBUG: USING CUSTOM INIT_DB.PY WITH MODIFIED CLUB NAMES ===")
    print(f"DEBUG: custom_app wurde übergeben: {custom_app is not None}")
    if custom_app:
        print(f"DEBUG: SQLALCHEMY_DATABASE_URI der übergebenen App: {custom_app.config['SQLALCHEMY_DATABASE_URI']}")

    # Verwende die übergebene App oder die Standard-App
    current_app = custom_app if custom_app else app

    # Wenn keine App übergeben wurde, konfiguriere die Standard-App
    if not custom_app:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager_new.db'
        db.init_app(app)

    with current_app.app_context():
        # Create a season
        season = Season(
            name="Season 2025",
            start_date=datetime(2025, 8, 1).date(),
            end_date=datetime(2026, 5, 31).date(),
            is_current=True
        )
        db.session.add(season)
        db.session.commit()

        # Create leagues
        leagues = []


        # Bundesländer und Landkreise werden aus der Excel-Datei gelesen


        # Erstelle die Ligen (erste Phase: ohne Liga-Referenzen)
        for i in range(1,len(url_arr)):
            # Wähle zufällige Werte für Bundesland und Landkreis
            bundesland = url_arr[i][4]
            landkreis = url_arr[i][5]

            altersklasse = url_arr[i][8]

            league = League(
                name=url_arr[i][6],
                level= int(url_arr[i][0]),
                season_id=season.id,
                bundesland=bundesland,
                landkreis=landkreis,
                altersklasse=altersklasse,
                anzahl_aufsteiger=1,
                anzahl_absteiger=1,
                aufstieg_liga_id=None,  # Will be set in second phase
                abstieg_liga_id=None   # Will be set in second phase
            )
            leagues.append(league)
            db.session.add(league)
        db.session.commit()

        # Zweite Phase: Setze Liga-Referenzen basierend auf Excel-Zeilen-Referenzen
        print("Setting up league promotion/relegation references...")
        for i in range(1, len(url_arr)):
            league = leagues[i-1]  # Current league (i-1 because we start from index 1)

            # Aufstiegsliga setzen (url_arr[i][2] ist Excel-Zeilen-Referenz oder mehrere getrennt durch Semikolon)
            try:
                aufstieg_data = url_arr[i][2] if url_arr[i][2] else ""
                if aufstieg_data:
                    # Handle multiple league references separated by semicolon
                    aufstieg_rows = [s.strip() for s in str(aufstieg_data).split(';') if s.strip()]
                    target_league_ids = []
                    target_league_names = []

                    for aufstieg_row_str in aufstieg_rows:
                        try:
                            aufstieg_row = int(float(aufstieg_row_str))
                            if aufstieg_row > 0 and aufstieg_row <= len(leagues):
                                target_league = leagues[aufstieg_row - 1]  # -1 because Excel is 1-based, list is 0-based
                                target_league_ids.append(str(target_league.id))
                                target_league_names.append(target_league.name)
                        except (ValueError, TypeError):
                            print(f"  WARNING: Could not parse promotion row '{aufstieg_row_str}' for {league.name}")

                    if target_league_ids:
                        league.aufstieg_liga_id = ';'.join(target_league_ids)
                        print(f"  {league.name} -> Promotion to: {', '.join(target_league_names)} (IDs: {', '.join(target_league_ids)})")
            except (ValueError, TypeError, IndexError) as e:
                print(f"  WARNING: Could not set promotion target for {league.name}: {e}")

            # Abstiegsliga setzen (url_arr[i][1] ist Excel-Zeilen-Referenz oder mehrere getrennt durch Semikolon)
            try:
                abstieg_data = url_arr[i][1] if url_arr[i][1] else ""
                if abstieg_data:
                    # Handle multiple league references separated by semicolon
                    abstieg_rows = [s.strip() for s in str(abstieg_data).split(';') if s.strip()]
                    target_league_ids = []
                    target_league_names = []

                    for abstieg_row_str in abstieg_rows:
                        try:
                            abstieg_row = int(float(abstieg_row_str))
                            if abstieg_row > 0 and abstieg_row <= len(leagues):
                                target_league = leagues[abstieg_row - 1]  # -1 because Excel is 1-based, list is 0-based
                                target_league_ids.append(str(target_league.id))
                                target_league_names.append(target_league.name)
                        except (ValueError, TypeError):
                            print(f"  WARNING: Could not parse relegation row '{abstieg_row_str}' for {league.name}")

                    if target_league_ids:
                        league.abstieg_liga_id = ';'.join(target_league_ids)
                        print(f"  {league.name} -> Relegation to: {', '.join(target_league_names)} (IDs: {', '.join(target_league_ids)})")
            except (ValueError, TypeError, IndexError) as e:
                print(f"  WARNING: Could not set relegation target for {league.name}: {e}")

        db.session.commit()
        print("League references set up successfully!")

        # Balance promotion and relegation spots after creating all leagues and setting references
        from simulation import balance_promotion_relegation_spots
        balance_promotion_relegation_spots(season.id)


        # Stelle sicher, dass der Ordner für die Vereinswappen existiert
        #logos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "public", "logos")
        #if not os.path.exists(logos_dir):
        #    os.makedirs(logos_dir)
        #    print(f"Ordner für Vereinswappen erstellt: {logos_dir}")


        clubs = []
        # Dictionary zum Speichern von Vereinen nach verein_id
        clubs_by_verein_id = {}
        # Dictionary zum Zählen der Teams pro Verein
        team_count_by_club_id = {}

        for i in range(1,len(url_arr)):
            # Prüfen, ob die URL vorhanden ist
            if i >= len(url_arr) or len(url_arr[i]) < 8 or not url_arr[i][7]:
                print(f"WARNING: Keine gültige URL für Liga {i} gefunden. Überspringe...")
                continue

            # Prüfen, ob die Liga existiert
            if i-1 >= len(leagues):
                print(f"WARNING: Keine Liga mit Index {i-1} gefunden. Überspringe...")
                continue

            league = leagues[i-1]  # Die aktuelle Liga
            print(f"INFO: Verarbeite Liga: {league.name} (ID: {league.id})")

            try:
                # Daten von der Website abrufen
                print(f"  Lade Daten von: {url_arr[i][7]}")
                reqs = requests.get(url_arr[i][7], timeout=15)
                print(f"  HTTP Status: {reqs.status_code}")

                if reqs.status_code != 200:
                    print(f"WARNING: HTTP Error {reqs.status_code} für {url_arr[i][7]}. Überspringe...")
                    continue

                soup = BeautifulSoup(reqs.text, 'html.parser')

                # Tabelle rausfiltern da sonst Namen aus News mit enthalten
                soup = soup.find("table", attrs={'class':'table table-striped table-full-width'})
                if not soup:
                    print(f"WARNING: Keine Tabelle in der URL {url_arr[i][7]} gefunden. Überspringe...")
                    # Debug: Show what tables are available
                    all_tables = BeautifulSoup(reqs.text, 'html.parser').find_all("table")
                    print(f"  Gefundene Tabellen auf der Seite: {len(all_tables)}")
                    for idx, table in enumerate(all_tables[:3]):  # Show first 3 tables
                        table_class = table.get('class', [])
                        print(f"    Tabelle {idx+1}: class={table_class}")
                    continue

                # Über alle Zeilen, außer erste (Tabellenheader)
                table_rows = soup.find_all("tr")[1:]
                print(f"  Gefundene Team-Zeilen: {len(table_rows)}")

                if len(table_rows) == 0:
                    print(f"  WARNING: Keine Team-Daten in Tabelle für {league.name}")
                elif len(table_rows) == 1:
                    print(f"  WARNING: Nur 1 Team in Tabelle für {league.name}")

                teams_created_for_league = 0

                for row_idx, tr in enumerate(table_rows):
                    zeile_arr = []
                    verein_id = None

                    for td in tr.find_all("td"):
                        if td.get_text() != '':
                            # Strip, wegen Escape Sequenzen usw.
                            zeile_arr.append(td.get_text().strip())
                        # ID vom Verein einlesen
                        for link in td.find_all('img', src=True):
                            try:
                                lnk = list("https:"+link.get("src"))
                                if len(lnk) > 61:  # Sicherstellen, dass der Index existiert
                                    lnk[61]="2"
                                    lnk = ''.join(lnk)
                                    verein_id = lnk.split("/")[-3]
                            except Exception as e:
                                print(f"WARNING: Fehler beim Verarbeiten des Vereins-Links: {e}")

                    # Überprüfen, ob wir genügend Daten haben
                    if not zeile_arr or len(zeile_arr) < 2 or not verein_id:
                        print(f"    WARNING: Unvollständige Daten für Zeile {row_idx+1}: {zeile_arr}, verein_id: {verein_id}")
                        continue

                    # Prüfen, ob der Verein bereits existiert
                    club = None
                    if verein_id in clubs_by_verein_id:
                        club = clubs_by_verein_id[verein_id]
                        print(f"DEBUG: Bestehender Verein gefunden: {club.name} (ID: {club.id}, verein_id: {verein_id})")
                    else:
                        # Prüfen, ob das Wappen bereits existiert
                        wappen_path = 'wappen/' + str(verein_id) + ".png"
                        if not os.path.exists(wappen_path):
                            # Wappen nur downloaden, wenn es noch nicht existiert
                            print(f"INFO: Lade Wappen für Verein {verein_id} herunter...")
                            url = "https://www.fussball.de/export.media/-/action/getLogo/format/2/id/" + str(verein_id)
                            img_data = requests.get(url).content
                            os.makedirs('wappen', exist_ok=True)
                            with open(wappen_path, 'wb') as handler:
                                handler.write(img_data)
                        else:
                            print(f"INFO: Wappen für Verein {verein_id} bereits vorhanden, überspringe Download.")
                        # Bahnqualität wird später nach der Team-Erstellung berechnet
                        # Hier setzen wir erstmal einen Standardwert
                        lane_quality = 1.0

                        # Neuen Verein erstellen
                        club = Club(
                            name=zeile_arr[1],
                            founded=random.randint(1900, 1980),
                            reputation=random.randint(50, 90),
                            fans=random.randint(500, 10000),
                            training_facilities=random.randint(30, 90),
                            coaching=random.randint(30, 90),
                            logo_path=wappen_path,
                            verein_id=verein_id,
                            lane_quality=lane_quality
                        )
                        clubs.append(club)
                        db.session.add(club)

                        # Commit, um die ID zu erhalten
                        db.session.flush()

                        # Verein im Dictionary speichern
                        clubs_by_verein_id[verein_id] = club
                        team_count_by_club_id[club.id] = 0

                        # Add initial finances
                        finance = Finance(
                            club_id=club.id,
                            balance=random.randint(500000, 2000000),
                            income=random.randint(50000, 200000),
                            expenses=random.randint(40000, 180000),
                            date=datetime.now().date(),
                            description="Initial balance"
                        )
                        db.session.add(finance)
                        print(f"DEBUG: Neuer Verein erstellt: {club.name} (ID: {club.id}, verein_id: {verein_id})")

                    # Zähler für Teams dieses Vereins erhöhen
                    team_count = team_count_by_club_id.get(club.id, 0) + 1
                    team_count_by_club_id[club.id] = team_count

                    # Team-Namen basierend auf der Anzahl der Teams für diesen Verein erstellen
                    team_name = club.name
                    if team_count > 1:
                        # Für zweites, drittes Team usw. römische Zahlen verwenden
                        roman_numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
                        if team_count <= len(roman_numerals) - 1:
                            team_name = f"{club.name} {roman_numerals[team_count]}"
                        else:
                            team_name = f"{club.name} {team_count}"

                    # Calculate team strength based on league level and table position
                    # For new seasons, generate realistic team strength based on league level and position
                    try:
                        # Try to get points and goal difference from table data
                        points = float(zeile_arr[9]) if len(zeile_arr) > 9 and zeile_arr[9] else 0
                        goal_diff = float(zeile_arr[8]) if len(zeile_arr) > 8 and zeile_arr[8] else 0

                        if points > 0:
                            # Use actual table data if available
                            staerke = int(points / 10 + goal_diff / 20)
                        else:
                            # Generate realistic team strength for new season based on league level and position
                            # Higher leagues have stronger teams, position in table affects strength
                            table_position = row_idx + 1  # 1-based position

                            # Base strength by league level (higher level = stronger teams)
                            league_base = max(30, 70 - (league.level - 1) * 4)  # Level 1: ~70, Level 10: ~34

                            # Position modifier (top teams stronger, bottom teams weaker)
                            # Assume 16 teams per league for calculation
                            position_modifier = (17 - table_position) * 1.5  # Top team: +24, bottom team: -9

                            # Random variation
                            random_modifier = random.randint(-5, 5)

                            staerke = int(league_base + position_modifier + random_modifier)

                        staerke = max(30, min(99, staerke))  # Clamp between 30 and 99
                    except (ValueError, IndexError):
                        # Fallback: random strength based on league level
                        league_base = max(30, 70 - (league.level - 1) * 4)
                        staerke = random.randint(max(30, league_base - 10), min(99, league_base + 10))

                    # Team erstellen und mit dem Verein verknüpfen
                    team = Team(
                        name=team_name,
                        club_id=club.id,
                        league_id=league.id,
                        staerke = staerke,
                        is_youth_team=False,
                    )
                    db.session.add(team)
                    teams_created_for_league += 1
                    print(f"    Team {teams_created_for_league}: {team_name} (Club: {club.name})")

                # Nach jeder Tabelle committen
                db.session.commit()
                print(f"  ✓ {teams_created_for_league} Teams für Liga {league.name} erstellt.")

                # Special attention for Landesliga 2
                if "Landesliga 2" in league.name:
                    print(f"  🎯 LANDESLIGA 2 RESULT: {teams_created_for_league} teams created")
                    if teams_created_for_league <= 1:
                        print(f"     ❌ PROBLEM: Only {teams_created_for_league} teams created for Landesliga 2!")
                    else:
                        print(f"     ✓ Landesliga 2 team creation successful")

            except Exception as e:
                print(f"ERROR: Fehler beim Verarbeiten der Liga {league.name}: {e}")
                continue

        # Abschließendes Commit
        db.session.commit()
        print(f"DEBUG: Insgesamt {len(clubs)} Vereine und {sum(team_count_by_club_id.values())} Teams erstellt.")

        # Bahnqualität für alle Vereine basierend auf ihrer besten Ligaebene berechnen
        print("INFO: Berechne Bahnqualität für alle Vereine basierend auf ihrer besten Ligaebene...")
        for club in clubs:
            new_lane_quality = calculate_lane_quality_for_club(club)
            club.lane_quality = new_lane_quality

        # Commit der aktualisierten Bahnqualitäten
        db.session.commit()
        print("INFO: Bahnqualität für alle Vereine aktualisiert.")

        # Spieler für jedes Team generieren
        # Load name pools from Excel files
        try:
            first_names, first_name_freqs = load_names_from_excel('Vornamen.xls')
            last_names, last_name_freqs = load_names_from_excel('Nachnamen.xls')
            print(f"Loaded {len(first_names)} first names and {len(last_names)} last names from Excel files")
        except Exception as e:
            print(f"Error loading names from Excel files: {e}")

        # Alle Teams abrufen
        all_teams = Team.query.all()
        print(f"DEBUG: Generiere Spieler für {len(all_teams)} Teams")

        for team in all_teams:
            # Generate players per team based on league level
            # Levels 1-4: 8-10 players
            # Levels 5-8: 7-9 players
            # Levels 9+: 7-8 players
            league_level = team.league.level if team.league else 5  # Default to middle level if no league

            if league_level <= 4:
                num_players = random.randint(8, 10)
            elif league_level <= 8:
                num_players = random.randint(7, 9)
            else:  # Level 9 and below
                num_players = random.randint(7, 8)

            print(f"Generating {num_players} players for team {team.name} (League Level {league_level})")

            for _ in range(num_players):
                # Get the league level for this team
                league_level = team.league.level if team.league else 5  # Default to middle level if no league

                # Check if it's a second team
                is_second_team = "II" in team.name

                # Calculate player attributes based on league level and team strength
                attributes = calculate_player_attribute_by_league_level(
                    league_level,
                    is_youth_team=team.is_youth_team,
                    is_second_team=is_second_team,
                    team_staerke=team.staerke  # Pass the team's strength value
                )

                # Youth players are younger
                if team.is_youth_team:
                    age = random.randint(16, 19)
                else:
                    age = random.randint(20, 35)

                # Get attributes from the calculated values
                strength = attributes['strength']
                talent = attributes['talent']

                # Contract length based on age
                if age < 23:
                    contract_years = random.randint(3, 5)
                elif age < 30:
                    contract_years = random.randint(2, 4)
                else:
                    contract_years = random.randint(1, 2)

                contract_end = datetime.now() + timedelta(days=365 * contract_years)

                # Salary based on strength and age
                base_salary = strength * 100
                age_factor = 1.5 if 25 <= age <= 30 else 1.0
                salary = base_salary * age_factor

                # Random position
                position = random.choice(["Angriff", "Mittelfeld", "Abwehr"])

                # Get all the other attributes from the calculated values
                ausdauer = attributes['ausdauer']
                konstanz = attributes['konstanz']
                drucksicherheit = attributes['drucksicherheit']
                volle = attributes['volle']
                raeumer = attributes['raeumer']
                sicherheit = attributes['sicherheit']
                auswaerts = attributes['auswaerts']
                start = attributes['start']
                mitte = attributes['mitte']
                schluss = attributes['schluss']

                # Generate name using frequency-based selection if available
                if first_name_freqs and last_name_freqs:
                    first_name = select_random_name(first_names, first_name_freqs)
                    last_name = select_random_name(last_names, last_name_freqs)
                    full_name = f"{first_name} {last_name}"
                else:
                    full_name = f"{random.choice(first_names)} {random.choice(last_names)}"

                player = Player(
                    name=full_name,
                    age=age,
                    strength=strength,
                    talent=talent,
                    position=position,
                    salary=salary,
                    contract_end=contract_end.date(),
                    # Verknüpfung zum Verein
                    club_id=team.club_id,
                    ausdauer=ausdauer,
                    # Neue Attribute
                    konstanz=konstanz,
                    drucksicherheit=drucksicherheit,
                    volle=volle,
                    raeumer=raeumer,
                    sicherheit=sicherheit,
                    # Weitere Attribute
                    auswaerts=auswaerts,
                    start=start,
                    mitte=mitte,
                    schluss=schluss
                )
                db.session.add(player)

                # Associate player with team (für Rückwärtskompatibilität)
                player.teams.append(team)

        # Commit the player changes
        db.session.commit()
        print("Players generated successfully!")

        # Perform initial player distribution for UI display purposes
        print("Performing initial player distribution...")
        from player_redistribution import initial_player_distribution
        initial_player_distribution()

        # Generate fixtures for each league using the proper round-robin algorithm
        print("Generating match fixtures...")
        for league in leagues:
            league_teams = Team.query.filter_by(league_id=league.id).all()

            if len(league_teams) < 2:
                print(f"WARNING: Not enough teams in league {league.name} to create fixtures")
                continue

            print(f"Creating fixtures for league {league.name} with {len(league_teams)} teams")

            # Import the simulation module to use the generate_fixtures function
            import simulation
            simulation.generate_fixtures(league, season)

        # Generate cups for the season
        print("Generating cup competitions...")
        try:
            from app import auto_initialize_cups
            auto_initialize_cups(season.id)
            print("Cup competitions generated successfully!")
        except Exception as e:
            print(f"Error generating cup competitions: {str(e)}")

        # Final commit
        db.session.commit()
        print("Match fixtures created successfully!")










if __name__ == "__main__":
    # Konfiguriere die Standard-App für die direkte Ausführung
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kegelmanager_new.db'
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created.")

    # Check if we should create sample data
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        create_sample_data(custom_app=app)
