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

def calculate_player_attribute_by_league_level(league_level, is_youth_team=False, is_second_team=False):
    """
    Calculate player attributes based on league level.

    Args:
        league_level: The level of the league (1 is top level, 10 is lowest)
        is_youth_team: Whether the team is a youth team
        is_second_team: Whether the team is a second team (e.g. "Club Name II")

    Returns:
        A dictionary with base values for player attributes
    """
    # Linear interpolation between level 1 (avg 80) and level 10 (avg 30)
    base_strength = 80 - (league_level - 1) * 5.5

    # Calculate standard deviation (higher leagues have more consistent players)
    std_dev = 5 + (league_level - 1) * 0.5

    # Generate attribute values using normal distribution
    attributes = {
        'strength': max(30, min(99, int(np.random.normal(base_strength, std_dev)))),
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

def create_sample_data_alt(custom_app=None):
    """
    Create sample data for the application.

    Args:
        custom_app: Eine bereits konfigurierte Flask-App, die verwendet werden soll.
                   Wenn None, wird die Standard-App verwendet.
    """
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

        # Bundesländer und Landkreise für Beispieldaten
        bundeslaender = ["Bayern", "Nordrhein-Westfalen", "Baden-Württemberg", "Niedersachsen", "Hessen"]
        landkreise = {
            "Bayern": ["München", "Nürnberg", "Augsburg", "Regensburg", "Würzburg"],
            "Nordrhein-Westfalen": ["Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg"],
            "Baden-Württemberg": ["Stuttgart", "Karlsruhe", "Mannheim", "Freiburg", "Heidelberg"],
            "Niedersachsen": ["Hannover", "Braunschweig", "Osnabrück", "Oldenburg", "Wolfsburg"],
            "Hessen": ["Frankfurt", "Wiesbaden", "Kassel", "Darmstadt", "Offenbach"]
        }

        # Altersklassen (für Referenz)
        # Herren, Damen, U23, U19, U16

        # Erstelle die Ligen
        for i in range(1, 4):
            # Wähle zufällige Werte für Bundesland und Landkreis
            bundesland = random.choice(bundeslaender)
            landkreis = random.choice(landkreise[bundesland])

            # Wähle eine zufällige Altersklasse (für Beispieldaten)
            altersklasse = "Herren"  # Standardmäßig Herren-Liga

            league = League(
                name=f"{i}. Bundesliga" if i == 1 else f"{i}. Liga",
                level=i,
                season_id=season.id,
                bundesland=bundesland,
                landkreis=landkreis,
                altersklasse=altersklasse,
                anzahl_aufsteiger=2,
                anzahl_absteiger=2
            )
            leagues.append(league)
            db.session.add(league)

        # Füge noch einige Ligen für andere Altersklassen hinzu
        for altersklasse in ["Damen", "U23", "U19"]:
            bundesland = random.choice(bundeslaender)
            landkreis = random.choice(landkreise[bundesland])

            league = League(
                name=f"{altersklasse}-Liga",
                level=4,  # Niedrigere Ebene für diese Ligen
                season_id=season.id,
                bundesland=bundesland,
                landkreis=landkreis,
                altersklasse=altersklasse,
                anzahl_aufsteiger=1,
                anzahl_absteiger=1
            )
            leagues.append(league)
            db.session.add(league)

        db.session.commit()

        # Setze die Auf- und Abstiegsbeziehungen
        # 1. Bundesliga hat keinen Aufstieg
        leagues[0].abstieg_liga_id = leagues[1].id  # Abstieg in die 2. Liga

        # 2. Liga hat Auf- und Abstieg
        leagues[1].aufstieg_liga_id = leagues[0].id  # Aufstieg in die 1. Bundesliga
        leagues[1].abstieg_liga_id = leagues[2].id   # Abstieg in die 3. Liga

        # 3. Liga hat nur Aufstieg (für Beispieldaten)
        leagues[2].aufstieg_liga_id = leagues[1].id  # Aufstieg in die 2. Liga

        # Spezialligen haben keine Auf-/Abstiegsbeziehungen in diesem Beispiel

        db.session.commit()

        # Create clubs
        club_names = [
            "SG Wählitz2", "SV Kegeewrwerlfreunde", "TSV Kegelwerwehausen",
            "FC Kegelwerwersport", "Kegelwerwer Union", "SC Kwerweregeltal",
            "Kegewerwerl SV", "SG Wählitz"
        ]
        print(f"DEBUG: Verwende benutzerdefinierte Club-Namen: {club_names}")

        # Stelle sicher, dass der Ordner für die Vereinswappen existiert
        logos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "public", "logos")
        if not os.path.exists(logos_dir):
            os.makedirs(logos_dir)
            print(f"Ordner für Vereinswappen erstellt: {logos_dir}")

        clubs = []
        for name in club_names:
            # Generiere einen Standardpfad für das Vereinswappen
            # In einer realen Anwendung würde hier ein tatsächliches Bild verwendet werden
            club_name_slug = name.lower().replace(" ", "_").replace(".", "")
            logo_path = f"/logos/{club_name_slug}.png"

            # Zufällige Werte für die neuen Felder
            fans = random.randint(500, 10000)
            training_facilities = random.randint(30, 90)
            coaching = random.randint(30, 90)

            # Bessere Vereine haben bessere Einrichtungen und mehr Fans
            if "Sport Club" in name or "1. FC" in name:
                fans *= 2
                training_facilities = min(training_facilities + 20, 100)
                coaching = min(coaching + 20, 100)

            club = Club(
                name=name,
                founded=random.randint(1900, 1980),
                reputation=random.randint(50, 90),
                fans=fans,
                training_facilities=training_facilities,
                coaching=coaching,
                logo_path=logo_path
            )
            clubs.append(club)
            db.session.add(club)

            # Add initial finances
            finance = Finance(
                club_id=len(clubs),  # This will be the club's ID after commit
                balance=random.randint(500000, 2000000),
                income=random.randint(50000, 200000),
                expenses=random.randint(40000, 180000),
                date=datetime.now().date(),
                description="Initial balance"
            )
            db.session.add(finance)

        db.session.commit()

        # Überprüfe die hinzugefügten Clubs
        all_clubs = Club.query.all()
        print(f"DEBUG: Hinzugefügte Clubs nach dem Commit: {[club.name for club in all_clubs]}")

        # Create teams for each club
        teams = []
        for club in clubs:
            # Main team in first league
            if len(teams) < 8:
                league_id = leagues[0].id
            elif len(teams) < 16:
                league_id = leagues[1].id
            else:
                league_id = leagues[2].id

            team = Team(
                name=club.name,
                club_id=club.id,
                league_id=league_id,
                is_youth_team=False
            )
            teams.append(team)
            db.session.add(team)

            # Second team in second or third league
            second_league_id = leagues[1].id if league_id == leagues[0].id else leagues[2].id
            second_team = Team(
                name=f"{club.name} II",
                club_id=club.id,
                league_id=second_league_id,
                is_youth_team=False
            )
            teams.append(second_team)
            db.session.add(second_team)

            # Youth team
            youth_team = Team(
                name=f"{club.name} U19",
                club_id=club.id,
                league_id=leagues[2].id,
                is_youth_team=True
            )
            teams.append(youth_team)
            db.session.add(youth_team)

        db.session.commit()

        # Load name pools from Excel files
        try:
            first_names, first_name_freqs = load_names_from_excel('Vornamen.xls')
            last_names, last_name_freqs = load_names_from_excel('Nachnamen.xls')
            print(f"Loaded {len(first_names)} first names and {len(last_names)} last names from Excel files")
        except Exception as e:
            print(f"Error loading names from Excel files: {e}")
            # Fallback to hardcoded names if Excel files can't be loaded
            first_names = ["Max", "Thomas", "Felix", "Jan", "Lukas", "Niklas", "Leon", "Tim", "Jonas", "David", "Philipp", "Simon"]
            last_names = ["Mustermann", "Schmidt", "Müller", "Becker", "Weber", "Fischer", "Schneider", "Hoffmann", "Schäfer", "Wagner", "Bauer", "Koch"]
            first_name_freqs = None
            last_name_freqs = None
            print("Using fallback hardcoded names")

        for team in teams:
            # Generate 7-10 players per team
            num_players = random.randint(7, 10)
            print(f"Generating {num_players} players for team {team.name}")

            for _ in range(num_players):
                # Get the league level for this team
                league_level = team.league.level if team.league else 5  # Default to middle level if no league

                # Check if it's a second team
                is_second_team = "II" in team.name

                # Calculate player attributes based on league level
                attributes = calculate_player_attribute_by_league_level(
                    league_level,
                    is_youth_team=team.is_youth_team,
                    is_second_team=is_second_team
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

        db.session.commit()

        # Generate fixtures for each league using the proper round-robin algorithm
        for league in leagues:
            # Import the simulation module to use the generate_fixtures function
            import simulation
            simulation.generate_fixtures(league, season)

        db.session.commit()

        print("Sample data created successfully!")






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


        # Erstelle die Ligen
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
                aufstieg_liga_id=str(url_arr[i][2]),
                abstieg_liga_id=str(url_arr[i][1])
            )
            leagues.append(league)
            db.session.add(league)
        db.session.commit()


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
            print(f"INFO: Verarbeite Liga: {league.name}")

            try:
                # Daten von der Website abrufen
                reqs = requests.get(url_arr[i][7])
                soup = BeautifulSoup(reqs.text, 'html.parser')

                # Tabelle rausfiltern da sonst Namen aus News mit enthalten
                soup = soup.find("table", attrs={'class':'table table-striped table-full-width'})
                if not soup:
                    print(f"WARNING: Keine Tabelle in der URL {url_arr[i][7]} gefunden. Überspringe...")
                    continue

                # Über alle Zeilen, außer erste (Tabellenheader)
                for tr in soup.find_all("tr")[1:]:
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
                        print(f"WARNING: Unvollständige Daten für Zeile: {zeile_arr}")
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
                        # Neuen Verein erstellen
                        club = Club(
                            name=zeile_arr[1],
                            founded=random.randint(1900, 1980),
                            reputation=random.randint(50, 90),
                            fans=random.randint(500, 10000),
                            training_facilities=random.randint(30, 90),
                            coaching=random.randint(30, 90),
                            logo_path=wappen_path,
                            verein_id=verein_id
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

                    # Team erstellen und mit dem Verein verknüpfen
                    team = Team(
                        name=team_name,
                        club_id=club.id,
                        league_id=league.id,
                        is_youth_team=False
                    )
                    db.session.add(team)
                    print(f"DEBUG: Team erstellt: {team_name} (Club: {club.name}, Liga: {league.name})")

                # Nach jeder Tabelle committen
                db.session.commit()
                print(f"DEBUG: Teams für Liga {league.name} erstellt.")

            except Exception as e:
                print(f"ERROR: Fehler beim Verarbeiten der Liga {league.name}: {e}")
                continue

        # Abschließendes Commit
        db.session.commit()
        print(f"DEBUG: Insgesamt {len(clubs)} Vereine und {sum(team_count_by_club_id.values())} Teams erstellt.")

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
            # Generate 7-10 players per team
            num_players = 7#random.randint(7, 10)
            print(f"Generating {num_players} players for team {team.name}")

            for _ in range(num_players):
                # Get the league level for this team
                league_level = team.league.level if team.league else 5  # Default to middle level if no league

                # Check if it's a second team
                is_second_team = "II" in team.name

                # Calculate player attributes based on league level
                attributes = calculate_player_attribute_by_league_level(
                    league_level,
                    is_youth_team=team.is_youth_team,
                    is_second_team=is_second_team
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
