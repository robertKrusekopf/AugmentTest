import os
import sys
import random
import shutil
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from flask import Flask
from models import db, Player, Team, Club, League, Match, Season, Finance
import xlrd
from config.config import get_config


def load_names_from_excel(file_path):
    """Load names and their cumulative frequencies from an Excel file."""
    try:
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
    except Exception as e:
        print(f"Warning: Could not load names from {file_path}: {e}")
        # Fallback names if Excel files are not available
        if 'Vornamen' in file_path:
            return ['Max', 'Hans', 'Klaus', 'Peter', 'Michael', 'Thomas', 'Andreas', 'Stefan'], [1] * 8
        else:
            return ['Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker'], [1] * 8


def select_random_name(names, frequencies):
    """Select a random name based on frequency distribution."""
    if not frequencies or all(f == 0 for f in frequencies):
        return random.choice(names)
    
    total_freq = sum(frequencies)
    rand_val = random.uniform(0, total_freq)
    
    cumulative = 0
    for name, freq in zip(names, frequencies):
        cumulative += freq
        if rand_val <= cumulative:
            return name
    
    return names[-1]  # Fallback


def generate_retirement_age():
    """
    Generiert das Ruhestandsalter für einen Spieler.

    Verwendet Werte aus der Konfigurationsdatei (game_config.json).
    Standard: ~80% zwischen 35-40 Jahren, Rest zwischen 30-45 Jahren.

    Returns:
        int: Ruhestandsalter zwischen min_age und max_age
    """
    config = get_config()
    mean_age = config.get('player_generation.retirement.mean_age', 37.5)
    std_dev = config.get('player_generation.retirement.std_dev', 1.95)
    min_age = config.get('player_generation.retirement.min_age', 30)
    max_age = config.get('player_generation.retirement.max_age', 45)

    retirement_age = int(np.random.normal(mean_age, std_dev))
    # Clamp auf konfigurierten Bereich
    retirement_age = max(min_age, min(max_age, retirement_age))
    return retirement_age


def get_age_range_for_altersklasse(altersklasse):
    """
    Bestimmt den Altersbereich basierend auf der Altersklasse der Liga.
    IDENTICAL to init_db.py version for consistency.

    Args:
        altersklasse: String mit der Altersklasse (z.B. "Herren", "A-Jugend", "A", etc.)

    Returns:
        tuple: (min_age, max_age) für die Altersklasse
    """
    if not altersklasse:
        return (18, 35)  # Default: Herren

    altersklasse_lower = altersklasse.lower().strip()

    # Jugendklassen (sowohl Langform "A-Jugend" als auch Kurzform "A")
    if 'a-jugend' in altersklasse_lower or 'a jugend' in altersklasse_lower or altersklasse_lower == 'a':
        return (17, 18)
    elif 'b-jugend' in altersklasse_lower or 'b jugend' in altersklasse_lower or altersklasse_lower == 'b':
        return (15, 16)
    elif 'c-jugend' in altersklasse_lower or 'c jugend' in altersklasse_lower or altersklasse_lower == 'c':
        return (13, 14)
    elif 'd-jugend' in altersklasse_lower or 'd jugend' in altersklasse_lower or altersklasse_lower == 'd':
        return (11, 12)
    elif 'e-jugend' in altersklasse_lower or 'e jugend' in altersklasse_lower or altersklasse_lower == 'e':
        return (9, 10)
    elif 'f-jugend' in altersklasse_lower or 'f jugend' in altersklasse_lower or altersklasse_lower == 'f':
        return (7, 8)
    else:
        # Herren oder unbekannte Altersklasse
        return (18, 35)


def calculate_player_attribute_by_league_level(league_level, is_youth_team=False, is_second_team=False, team_staerke=None):
    """
    Calculate player attributes based on team strength.
    IDENTICAL to init_db.py version for consistency.
    """

    # Calculate standard deviation (higher leagues have more consistent players)
    std_dev = 5 + (league_level - 1) * 0.5

    # Generate attribute values using normal distribution
    player_strength = max(1, min(99, int(np.random.normal(team_staerke, std_dev))))

    attributes = {
        'strength': player_strength,
        'talent': random.randint(1, 10),  # Talent is independent of league level
    }

    # Calculate other attributes based on strength - IDENTICAL to init_db.py
    base_attr_value = 60 + (attributes['strength'] - 50) * 0.6
    attr_std_dev = 5 + (league_level - 1) * 0.3

    # Generate all other attributes
    for attr in ['ausdauer', 'konstanz', 'drucksicherheit',
                'volle', 'raeumer', 'sicherheit', 'auswaerts', 'start', 'mitte', 'schluss']:
        attributes[attr] = max(1, min(99, int(np.random.normal(base_attr_value, attr_std_dev))))

    return attributes


def extend_existing_database(source_db_path, target_db_name):
    """
    Erstellt eine neue Datenbank basierend auf einer bestehenden .db-Datei
    und ergänzt fehlende Daten (Spieler, Saison, etc.).
    
    Args:
        source_db_path (str): Pfad zur Quell-Datenbank
        target_db_name (str): Name der neuen Ziel-Datenbank (ohne .db Endung)
    
    Returns:
        dict: Ergebnis der Operation
    """
    
    # Überprüfe, ob die Quell-Datenbank existiert
    if not os.path.exists(source_db_path):
        return {"success": False, "message": f"Quell-Datenbank '{source_db_path}' nicht gefunden."}
    
    # Stelle sicher, dass der Name keine .db Endung hat
    if target_db_name.endswith('.db'):
        target_db_name = target_db_name[:-3]

    # Stelle sicher, dass der Instance-Ordner existiert
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

    # Vollständiger Pfad zur neuen Datenbank
    target_db_path = os.path.join(instance_dir, f"{target_db_name}.db")

    # Überprüfe, ob die Ziel-Datenbank bereits existiert
    if os.path.exists(target_db_path):
        return {"success": False, "message": f"Ziel-Datenbank '{target_db_name}.db' existiert bereits."}

    try:
        # Kopiere die Quell-Datenbank zur Ziel-Datenbank
        shutil.copy2(source_db_path, target_db_path)
        print(f"Datenbank von '{source_db_path}' nach '{target_db_path}' kopiert.")

        # Erstelle eine Flask-App und konfiguriere die Datenbank
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{target_db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)

        with app.app_context():
            # Stelle sicher, dass alle Tabellen existieren (falls neue hinzugefügt wurden)
            db.create_all()
            
            # Analysiere die bestehende Datenbank
            analysis = analyze_existing_database()
            print(f"Datenbank-Analyse: {analysis}")
            
            # Ergänze fehlende Daten basierend auf der Analyse
            result = supplement_missing_data(analysis)
            
            if result["success"]:
                db.session.commit()
                print(f"Datenbank '{target_db_name}.db' erfolgreich erweitert.")
                return {"success": True, "message": f"Datenbank '{target_db_name}.db' erfolgreich erweitert."}
            else:
                return result

    except Exception as e:
        print(f"Fehler beim Erweitern der Datenbank: {str(e)}")
        # Lösche die Ziel-Datenbank bei Fehlern
        if os.path.exists(target_db_path):
            os.remove(target_db_path)
        return {"success": False, "message": f"Fehler beim Erweitern der Datenbank: {str(e)}"}


def analyze_existing_database():
    """
    Analysiert die bestehende Datenbank und gibt Informationen über vorhandene und fehlende Daten zurück.
    
    Returns:
        dict: Analyse-Ergebnisse
    """
    analysis = {
        "has_season": False,
        "has_leagues": False,
        "has_clubs": False,
        "has_teams": False,
        "has_players": False,
        "has_finances": False,
        "season_count": 0,
        "league_count": 0,
        "club_count": 0,
        "team_count": 0,
        "player_count": 0,
        "teams_without_players": [],
        "clubs_without_finances": [],
        "clubs_without_teams": [],
        "players_with_incomplete_attributes": []
    }
    
    # Überprüfe Saisons
    seasons = Season.query.all()
    analysis["season_count"] = len(seasons)
    analysis["has_season"] = len(seasons) > 0
    
    # Überprüfe Ligen
    leagues = League.query.all()
    analysis["league_count"] = len(leagues)
    analysis["has_leagues"] = len(leagues) > 0
    
    # Überprüfe Vereine
    clubs = Club.query.all()
    analysis["club_count"] = len(clubs)
    analysis["has_clubs"] = len(clubs) > 0
    
    # Überprüfe Teams
    teams = Team.query.all()
    analysis["team_count"] = len(teams)
    analysis["has_teams"] = len(teams) > 0
    
    # Überprüfe Spieler - verwende direkte SQL-Abfrage um Probleme mit leeren Datumsfeldern zu vermeiden
    try:
        players = Player.query.all()
        analysis["player_count"] = len(players)
        analysis["has_players"] = len(players) > 0
    except Exception as e:
        print(f"Fehler beim Laden der Spieler über ORM: {e}")
        # Fallback: Verwende direkte SQL-Abfrage
        result = db.session.execute(db.text("SELECT COUNT(*) FROM player"))
        player_count = result.scalar()
        analysis["player_count"] = player_count
        analysis["has_players"] = player_count > 0
        players = []  # Leere Liste für weitere Verarbeitung
    
    # Finde Teams ohne Spieler - verwende direkte SQL-Abfrage
    for team in teams:
        try:
            result = db.session.execute(db.text("SELECT COUNT(*) FROM player WHERE club_id = :club_id"),
                                      {'club_id': team.club_id})
            player_count = result.scalar()
            if player_count == 0:
                analysis["teams_without_players"].append(team.id)
        except Exception as e:
            print(f"Fehler beim Prüfen der Spieler für Team {team.id}: {e}")
            # Im Fehlerfall als Team ohne Spieler markieren
            analysis["teams_without_players"].append(team.id)
    
    # Finde Vereine ohne Finanzen
    for club in clubs:
        finances = Finance.query.filter_by(club_id=club.id).all()
        if len(finances) == 0:
            analysis["clubs_without_finances"].append(club.id)
    
    # Finde Vereine ohne Teams
    for club in clubs:
        club_teams = Team.query.filter_by(club_id=club.id).all()
        if len(club_teams) == 0:
            analysis["clubs_without_teams"].append(club.id)

    # Finde Spieler mit unvollständigen Attributen - verwende direkte SQL-Abfrage
    if analysis["has_players"]:
        try:
            # Verwende direkte SQL-Abfrage um Probleme mit leeren Datumsfeldern zu vermeiden
            result = db.session.execute(db.text("""
                SELECT id, name, club_id, age, talent, position, salary, contract_end,
                       ausdauer, konstanz, drucksicherheit, volle, raeumer, sicherheit,
                       auswaerts, start, mitte, schluss, retirement_age, is_retired
                FROM player
            """))

            for row in result:
                player_id, name, club_id, age, talent, position, salary, contract_end, \
                ausdauer, konstanz, drucksicherheit, volle, raeumer, sicherheit, \
                auswaerts, start, mitte, schluss, retirement_age, is_retired = row

                missing_attributes = []

                # Prüfe alle wichtigen Spielerattribute
                if age is None or age == 0 or age == "":
                    missing_attributes.append('age')
                if talent is None or talent == 0 or talent == "":
                    missing_attributes.append('talent')
                if position is None or position == "":
                    missing_attributes.append('position')
                if salary is None or salary == 0 or salary == "":
                    missing_attributes.append('salary')
                if contract_end is None or contract_end == "":
                    missing_attributes.append('contract_end')
                if ausdauer is None or ausdauer == 0 or ausdauer == "":
                    missing_attributes.append('ausdauer')
                if konstanz is None or konstanz == 0 or konstanz == "":
                    missing_attributes.append('konstanz')
                if drucksicherheit is None or drucksicherheit == 0 or drucksicherheit == "":
                    missing_attributes.append('drucksicherheit')
                if volle is None or volle == 0 or volle == "":
                    missing_attributes.append('volle')
                if raeumer is None or raeumer == 0 or raeumer == "":
                    missing_attributes.append('raeumer')
                if sicherheit is None or sicherheit == 0 or sicherheit == "":
                    missing_attributes.append('sicherheit')
                if auswaerts is None or auswaerts == 0 or auswaerts == "":
                    missing_attributes.append('auswaerts')
                if start is None or start == 0 or start == "":
                    missing_attributes.append('start')
                if mitte is None or mitte == 0 or mitte == "":
                    missing_attributes.append('mitte')
                if schluss is None or schluss == 0 or schluss == "":
                    missing_attributes.append('schluss')
                if retirement_age is None or retirement_age == 0 or retirement_age == "":
                    missing_attributes.append('retirement_age')
                if is_retired is None:
                    missing_attributes.append('is_retired')

                if missing_attributes:
                    analysis["players_with_incomplete_attributes"].append({
                        'player_id': player_id,
                        'player_name': name,
                        'club_id': club_id,
                        'missing_attributes': missing_attributes
                    })
        except Exception as e:
            print(f"Fehler beim Analysieren der Spielerattribute: {e}")
            # Fallback: Alle Spieler als unvollständig markieren
            result = db.session.execute(db.text("SELECT id, name, club_id FROM player"))
            for row in result:
                player_id, name, club_id = row
                analysis["players_with_incomplete_attributes"].append({
                    'player_id': player_id,
                    'player_name': name,
                    'club_id': club_id,
                    'missing_attributes': ['age', 'talent', 'position', 'salary', 'contract_end',
                                         'ausdauer', 'konstanz', 'drucksicherheit', 'volle', 'raeumer',
                                         'sicherheit', 'auswaerts', 'start', 'mitte', 'schluss',
                                         'retirement_age', 'is_retired']
                })

    return analysis


def supplement_missing_data(analysis):
    """
    Ergänzt fehlende Daten basierend auf der Analyse der bestehenden Datenbank.

    Args:
        analysis (dict): Analyse-Ergebnisse der bestehenden Datenbank

    Returns:
        dict: Ergebnis der Ergänzung
    """
    try:
        # Erstelle eine Saison, falls keine vorhanden ist
        if not analysis["has_season"]:
            print("Erstelle neue Saison...")
            season = Season(
                name="Season 2025",
                start_date=datetime(2025, 8, 1).date(),
                end_date=datetime(2026, 5, 31).date(),
                is_current=True
            )
            db.session.add(season)
            db.session.flush()  # Um die ID zu erhalten
            print(f"Saison '{season.name}' erstellt.")

        # Lade Namen aus Excel-Dateien
        try:
            first_names, first_name_freqs = load_names_from_excel('Vornamen.xls')
            last_names, last_name_freqs = load_names_from_excel('Nachnamen.xls')
            print(f"Loaded {len(first_names)} first names and {len(last_names)} last names from Excel files")
        except Exception as e:
            print(f"Error loading names from Excel files: {e}")
            # Fallback names
            first_names, first_name_freqs = load_names_from_excel('Vornamen.xls')
            last_names, last_name_freqs = load_names_from_excel('Nachnamen.xls')

        # Ergänze Finanzen für Vereine ohne Finanzen
        if analysis["clubs_without_finances"]:
            print(f"Ergänze Finanzen für {len(analysis['clubs_without_finances'])} Vereine...")
            for club_id in analysis["clubs_without_finances"]:
                finance = Finance(
                    club_id=club_id,
                    balance=random.randint(500000, 2000000),
                    income=random.randint(50000, 200000),
                    expenses=random.randint(40000, 180000),
                    date=datetime.now().date(),
                    description="Initial balance"
                )
                db.session.add(finance)

        # Ergänze Spieler für Teams ohne Spieler
        if analysis["teams_without_players"]:
            print(f"Ergänze Spieler für {len(analysis['teams_without_players'])} Teams...")

            for team_id in analysis["teams_without_players"]:
                team = Team.query.get(team_id)
                if not team:
                    continue

                # Bestimme Anzahl der Spieler basierend auf Liga-Level
                league_level = team.league.level if team.league else 5

                if league_level <= 4:
                    num_players = random.randint(8, 10)
                elif league_level <= 8:
                    num_players = random.randint(7, 9)
                else:  # Level 9 and below
                    num_players = random.randint(7, 8)

                print(f"Generiere {num_players} Spieler für Team {team.name} (Liga Level {league_level})")

                for _ in range(num_players):
                    # Überprüfe, ob es ein zweites Team ist
                    is_second_team = "II" in team.name

                    # Berechne Spieler-Attribute basierend auf Team-Stärke
                    attributes = calculate_player_attribute_by_league_level(
                        league_level,
                        is_youth_team=team.is_youth_team,
                        is_second_team=is_second_team,
                        team_staerke=team.staerke
                    )

                    # Determine age based on league's altersklasse
                    if team.league and team.league.altersklasse:
                        min_age, max_age = get_age_range_for_altersklasse(team.league.altersklasse)
                        age = random.randint(min_age, max_age)
                    elif team.is_youth_team:
                        # Fallback: use old logic if no altersklasse is set
                        age = random.randint(16, 19)
                    else:
                        # Default: Herren (18-35 Jahre)
                        age = random.randint(18, 35)

                    # Gehalt basierend auf Stärke und Alter - IDENTICAL to init_db.py
                    base_salary = attributes['strength'] * 100
                    age_factor = 1.5 if 25 <= age <= 30 else 1.0
                    salary = base_salary * age_factor

                    # Vertragsende basierend auf Alter - IDENTICAL to init_db.py
                    if age < 23:
                        contract_years = random.randint(3, 5)
                    elif age < 30:
                        contract_years = random.randint(2, 4)
                    else:
                        contract_years = random.randint(1, 2)
                    contract_end = datetime.now() + timedelta(days=365 * contract_years)

                    # Position - IDENTICAL to init_db.py
                    position = random.choice(["Angriff", "Mittelfeld", "Abwehr"])

                    # Name generieren
                    if first_name_freqs and last_name_freqs:
                        first_name = select_random_name(first_names, first_name_freqs)
                        last_name = select_random_name(last_names, last_name_freqs)
                        full_name = f"{first_name} {last_name}"
                    else:
                        full_name = f"{random.choice(first_names)} {random.choice(last_names)}"

                    # Generiere Ruhestandsalter
                    retirement_age = generate_retirement_age()

                    # Spieler erstellen
                    player = Player(
                        name=full_name,
                        age=age,
                        strength=attributes['strength'],
                        talent=attributes['talent'],
                        position=position,
                        salary=salary,
                        contract_end=contract_end.date(),
                        club_id=team.club_id,
                        ausdauer=attributes['ausdauer'],
                        konstanz=attributes['konstanz'],
                        drucksicherheit=attributes['drucksicherheit'],
                        volle=attributes['volle'],
                        raeumer=attributes['raeumer'],
                        sicherheit=attributes['sicherheit'],
                        auswaerts=attributes['auswaerts'],
                        start=attributes['start'],
                        mitte=attributes['mitte'],
                        schluss=attributes['schluss'],
                        # Ruhestandsalter
                        retirement_age=retirement_age,
                        is_retired=False
                    )
                    db.session.add(player)

        # Ergänze fehlende Attribute für bestehende Spieler
        if analysis["players_with_incomplete_attributes"]:
            print(f"Ergänze fehlende Attribute für {len(analysis['players_with_incomplete_attributes'])} Spieler...")

            for player_info in analysis["players_with_incomplete_attributes"]:
                player_id = player_info['player_id']
                player_name = player_info['player_name']
                club_id = player_info['club_id']
                missing_attributes = player_info['missing_attributes']

                print(f"Ergänze Attribute für Spieler {player_name} (ID: {player_id})")
                print(f"  Fehlende Attribute: {', '.join(missing_attributes)}")

                # Hole aktuelle Spielerdaten
                result = db.session.execute(db.text("SELECT strength FROM player WHERE id = :player_id"),
                                          {'player_id': player_id})
                row = result.fetchone()
                if not row:
                    continue

                current_strength = row[0]

                # Bestimme Team-Stärke und Altersklasse für Attribut-Berechnung
                team_result = db.session.execute(db.text("""
                    SELECT t.staerke, l.level, l.altersklasse
                    FROM team t
                    LEFT JOIN league l ON t.league_id = l.id
                    WHERE t.club_id = :club_id
                    ORDER BY l.level ASC
                    LIMIT 1
                """), {'club_id': club_id})

                team_row = team_result.fetchone()
                if team_row:
                    team_staerke, league_level, altersklasse = team_row
                    league_level = league_level or 5
                else:
                    team_staerke = 50
                    league_level = 5
                    altersklasse = None

                # Verwende bestehende Stärke falls vorhanden, sonst berechne neue
                if current_strength and current_strength > 0:
                    base_strength = current_strength
                else:
                    # Berechne neue Stärke basierend auf Team
                    std_dev = 5 + (league_level - 1) * 0.5
                    base_strength = max(1, min(99, int(np.random.normal(team_staerke, std_dev))))

                # Berechne alle Attribute basierend auf der Stärke - IDENTICAL to init_db.py
                base_attr_value = 60 + (base_strength - 50) * 0.6
                attr_std_dev = 5 + (league_level - 1) * 0.3

                # Erstelle Update-Dictionary
                updates = {}

                # Ergänze fehlende Attribute - IDENTICAL to init_db.py logic
                if 'age' in missing_attributes:
                    # Determine age based on league's altersklasse
                    if altersklasse:
                        min_age, max_age = get_age_range_for_altersklasse(altersklasse)
                        updates['age'] = random.randint(min_age, max_age)
                    else:
                        # Fallback: default Herren age range (18-35)
                        updates['age'] = random.randint(18, 35)

                if 'talent' in missing_attributes:
                    updates['talent'] = random.randint(1, 10)

                if 'position' in missing_attributes:
                    # IDENTICAL to init_db.py
                    updates['position'] = random.choice(["Angriff", "Mittelfeld", "Abwehr"])

                if 'salary' in missing_attributes:
                    # IDENTICAL to init_db.py - need age for this calculation
                    age = updates.get('age', random.randint(20, 35))
                    base_salary = base_strength * 100
                    age_factor = 1.5 if 25 <= age <= 30 else 1.0
                    updates['salary'] = base_salary * age_factor

                if 'contract_end' in missing_attributes:
                    # IDENTICAL to init_db.py - need age for this calculation
                    age = updates.get('age', random.randint(20, 35))
                    if age < 23:
                        contract_years = random.randint(3, 5)
                    elif age < 30:
                        contract_years = random.randint(2, 4)
                    else:
                        contract_years = random.randint(1, 2)
                    contract_end = datetime.now() + timedelta(days=365 * contract_years)
                    updates['contract_end'] = contract_end.date().isoformat()

                # Kegel-Attribute - IDENTICAL to init_db.py calculation
                for attr in ['ausdauer', 'konstanz', 'drucksicherheit', 'volle', 'raeumer',
                           'sicherheit', 'auswaerts', 'start', 'mitte', 'schluss']:
                    if attr in missing_attributes:
                        updates[attr] = max(1, min(99, int(np.random.normal(base_attr_value, attr_std_dev))))

                # Ruhestandsalter ergänzen falls fehlend
                if 'retirement_age' in missing_attributes:
                    updates['retirement_age'] = generate_retirement_age()

                if 'is_retired' in missing_attributes:
                    updates['is_retired'] = False

                # Führe Update aus
                if updates:
                    # Erstelle SET-Klausel
                    set_clauses = []
                    params = {'player_id': player_id}

                    for key, value in updates.items():
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value

                    update_sql = f"UPDATE player SET {', '.join(set_clauses)} WHERE id = :player_id"
                    db.session.execute(db.text(update_sql), params)

                print(f"  Spieler {player_name} erfolgreich ergänzt")

        # Migriere verein_id Spalte von INTEGER zu STRING
        print("Migriere verein_id Spalte von INTEGER zu STRING...")
        try:
            # Prüfe aktuelle Spaltenstruktur
            cursor = db.session.connection().connection.cursor()
            cursor.execute("PRAGMA table_info(club)")
            columns = cursor.fetchall()

            verein_id_column = None
            for col in columns:
                if col[1] == 'verein_id':
                    verein_id_column = col
                    break

            if verein_id_column and 'INTEGER' in verein_id_column[2]:
                print("  verein_id ist INTEGER, migriere zu STRING...")

                # Erstelle temporäre Tabelle mit neuer Struktur
                cursor.execute("""
                    CREATE TABLE club_temp AS
                    SELECT id, name, founded, reputation,
                           CAST(verein_id AS TEXT) as verein_id_temp,
                           fans, training_facilities, coaching, lane_quality,
                           created_at, updated_at
                    FROM club
                """)

                # Lösche alte Tabelle
                cursor.execute("DROP TABLE club")

                # Erstelle neue Tabelle mit korrekter Struktur
                cursor.execute("""
                    CREATE TABLE club (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        founded INTEGER,
                        reputation INTEGER DEFAULT 50,
                        verein_id VARCHAR(100),
                        fans INTEGER DEFAULT 1000,
                        training_facilities INTEGER DEFAULT 50,
                        coaching INTEGER DEFAULT 50,
                        lane_quality FLOAT,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """)

                # Kopiere Daten zurück
                cursor.execute("""
                    INSERT INTO club (id, name, founded, reputation, verein_id,
                                    fans, training_facilities, coaching, lane_quality,
                                    created_at, updated_at)
                    SELECT id, name, founded, reputation, verein_id_temp,
                           fans, training_facilities, coaching, lane_quality,
                           created_at, updated_at
                    FROM club_temp
                """)

                # Lösche temporäre Tabelle
                cursor.execute("DROP TABLE club_temp")

                # Commit der Migration
                db.session.commit()
                print("  Migration erfolgreich!")
            else:
                print("  verein_id ist bereits STRING oder existiert nicht")

        except Exception as e:
            print(f"  Fehler bei Migration: {e}")
            db.session.rollback()

        # Aktualisiere verein_id für Vereine ohne verein_id mit direktem SQL
        print("Aktualisiere verein_id für Vereine ohne verein_id...")
        try:
            cursor = db.session.connection().connection.cursor()

            # Hole alle Clubs
            cursor.execute("SELECT id, name FROM club")
            clubs = cursor.fetchall()

            for club_id, club_name in clubs:
                # Erstelle verein_id aus dem Namen ohne Leerzeichen und in Kleinbuchstaben
                import re
                verein_id_name = re.sub(r'[^a-zA-ZäöüÄÖÜß0-9]', '', club_name).lower()

                # Update mit direktem SQL
                cursor.execute("UPDATE club SET verein_id = ? WHERE id = ?", (verein_id_name, club_id))
                print(f"  {club_name} -> verein_id: {verein_id_name}")

            # Commit der Änderungen
            db.session.commit()
            print("  verein_id Updates erfolgreich!")

        except Exception as e:
            print(f"  Fehler beim Setzen der verein_id: {e}")
            db.session.rollback()

        # Aktualisiere Bahnqualität für alle Vereine
        print("Aktualisiere Bahnqualität für alle Vereine...")
        # Hole alle Clubs als ORM-Objekte
        all_clubs = Club.query.all()
        for club in all_clubs:
            # Finde das beste Team des Vereins
            best_team = Team.query.filter_by(club_id=club.id).order_by(Team.league_id).first()
            if best_team and best_team.league:
                # Berechne Bahnqualität basierend auf dem besten Team
                league_level = best_team.league.level
                if league_level <= 2:
                    lane_quality = random.uniform(1.02, 1.05)
                elif league_level <= 4:
                    lane_quality = random.uniform(1.00, 1.02)
                elif league_level <= 6:
                    lane_quality = random.uniform(0.98, 1.00)
                else:
                    lane_quality = random.uniform(0.90, 0.98)

                club.lane_quality = lane_quality

        # logo_path wurde entfernt - nicht mehr benötigt

        # Erstelle Player-Team-Zuordnungen falls noch nicht vorhanden
        player_team_count = db.session.execute(db.text("SELECT COUNT(*) FROM player_team")).scalar()

        if player_team_count == 0:
            print("Erstelle Player-Team-Zuordnungen...")
            try:
                # Für jeden Club: Ordne alle Spieler dem Team zu
                clubs = Club.query.all()
                total_assignments = 0

                for club in clubs:
                    teams = Team.query.filter_by(club_id=club.id).all()
                    players = Player.query.filter_by(club_id=club.id).all()

                    if not teams or not players:
                        continue

                    # Wenn nur ein Team: Alle Spieler diesem Team zuordnen
                    if len(teams) == 1:
                        team = teams[0]
                        for player in players:
                            if team not in player.teams:
                                player.teams.append(team)
                                total_assignments += 1
                        print(f"  {club.name}: {len(players)} Spieler zu {team.name} zugeordnet")

                    # Wenn mehrere Teams: Verwende initial_player_distribution
                    elif len(teams) > 1:
                        print(f"  {club.name}: Verwende Verteilungslogik für {len(teams)} Teams")
                        from player_redistribution import redistribute_club_players_by_strength
                        redistribute_club_players_by_strength(club.id)

                db.session.commit()
                print(f"Player-Team-Zuordnungen erfolgreich erstellt! ({total_assignments} Zuordnungen)")
            except Exception as e:
                db.session.rollback()
                print(f"Fehler beim Erstellen der Player-Team-Zuordnungen: {str(e)}")
        else:
            print(f"Player-Team-Zuordnungen bereits vorhanden ({player_team_count} Einträge)")

        # Generiere Fixtures für alle Ligen falls noch nicht vorhanden
        season = Season.query.filter_by(is_current=True).first()
        if season:
            print("Generiere Fixtures für Ligen...")
            try:
                from simulation import generate_fixtures
                from models import League, Match

                leagues = League.query.filter_by(season_id=season.id).all()
                total_fixtures_generated = 0

                for league in leagues:
                    # Prüfe ob bereits Fixtures vorhanden sind
                    existing_matches = Match.query.filter_by(league_id=league.id, season_id=season.id).count()

                    if existing_matches == 0:
                        # Prüfe ob genug Teams vorhanden sind
                        teams_in_league = Team.query.filter_by(league_id=league.id).all()

                        if len(teams_in_league) >= 2:
                            print(f"Generiere Fixtures für Liga {league.name} mit {len(teams_in_league)} Teams...")
                            generate_fixtures(league, season)

                            # Zähle generierte Fixtures
                            new_matches = Match.query.filter_by(league_id=league.id, season_id=season.id).count()
                            total_fixtures_generated += new_matches
                            print(f"  {new_matches} Fixtures generiert")
                        else:
                            print(f"  Liga {league.name} hat nur {len(teams_in_league)} Teams - überspringe")
                    else:
                        print(f"  Liga {league.name} hat bereits {existing_matches} Fixtures")

                print(f"Insgesamt {total_fixtures_generated} neue Fixtures generiert!")
            except Exception as e:
                print(f"Fehler beim Generieren der Fixtures: {str(e)}")

            # Erstelle Pokale falls noch nicht vorhanden (VOR dem Saisonkalender!)
            print("Erstelle Pokale...")
            try:
                from models import Cup
                existing_cups = Cup.query.filter_by(season_id=season.id).count()

                if existing_cups == 0:
                    from app import auto_initialize_cups
                    auto_initialize_cups(season.id)
                    print("Pokale erfolgreich erstellt!")
                else:
                    print(f"Pokale bereits vorhanden ({existing_cups} Pokale)")
            except Exception as e:
                print(f"Fehler beim Erstellen der Pokale: {str(e)}")

            # Erstelle Saisonkalender falls noch nicht vorhanden (NACH den Pokalen!)
            from models import SeasonCalendar
            calendar_count = SeasonCalendar.query.filter_by(season_id=season.id).count()

            if calendar_count == 0:
                print("Erstelle Saisonkalender...")
                try:
                    from season_calendar import create_season_calendar
                    create_season_calendar(season.id)
                    print("Saisonkalender erfolgreich erstellt!")
                except Exception as e:
                    print(f"Fehler beim Erstellen des Saisonkalenders: {str(e)}")

                # Setze Match-Daten für alle Spiele (Liga und Pokal)
                print("Setze Match-Daten für alle Spiele...")
                try:
                    from season_calendar import set_all_match_dates_unified
                    set_all_match_dates_unified(season.id)
                    print("Match-Daten erfolgreich gesetzt!")
                except Exception as e:
                    print(f"Fehler beim Setzen der Match-Daten: {str(e)}")

                # Neuberechnung der Pokal-Spieltage nach Erstellung des Saisonkalenders
                print("Neuberechnung der Pokal-Spieltage...")
                try:
                    from models import Cup, CupMatch
                    cups = Cup.query.filter_by(season_id=season.id).all()

                    for cup in cups:
                        print(f"Neuberechnung der Spieltage für {cup.name}...")
                        cup_matches = CupMatch.query.filter_by(cup_id=cup.id).all()

                        for match in cup_matches:
                            # Neuberechnung des Pokal-Spieltags mit der neuen Logik
                            new_cup_match_day = cup.calculate_cup_match_day(match.round_number, cup.total_rounds)
                            if new_cup_match_day != match.cup_match_day:
                                match.cup_match_day = new_cup_match_day

                        db.session.commit()

                    print("Pokal-Spieltage erfolgreich neuberechnet!")
                except Exception as e:
                    print(f"Fehler bei der Neuberechnung der Pokal-Spieltage: {str(e)}")
            else:
                print(f"Saisonkalender bereits vorhanden ({calendar_count} Einträge)")

                # Auch bei vorhandenem Kalender: Prüfe ob Match-Daten gesetzt werden müssen
                print("Prüfe Match-Daten für alle Spiele...")
                try:
                    from season_calendar import set_all_match_dates_unified
                    set_all_match_dates_unified(season.id)
                    print("Match-Daten überprüft und ggf. gesetzt!")
                except Exception as e:
                    print(f"Fehler beim Setzen der Match-Daten: {str(e)}")

        # Bereinige NULL-Werte in kritischen Feldern
        print("Bereinige NULL-Werte in kritischen Feldern...")
        try:
            # Bereinige NULL round_number in CupMatch
            cursor = db.session.connection().connection.cursor()

            # Prüfe ob CupMatch Tabelle existiert
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cup_match'")
            if cursor.fetchone():
                # Setze NULL round_number auf 1 (erste Runde)
                cursor.execute("UPDATE cup_match SET round_number = 1 WHERE round_number IS NULL")
                updated_cup_matches = cursor.rowcount
                if updated_cup_matches > 0:
                    print(f"  {updated_cup_matches} CupMatch-Einträge mit NULL round_number auf 1 gesetzt")

                # Setze leere round_name auf "1. Runde"
                cursor.execute("UPDATE cup_match SET round_name = '1. Runde' WHERE round_name IS NULL OR round_name = ''")
                updated_round_names = cursor.rowcount
                if updated_round_names > 0:
                    print(f"  {updated_round_names} CupMatch-Einträge mit leerem round_name auf '1. Runde' gesetzt")

            # Bereinige NULL current_round_number in Cup
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cup'")
            if cursor.fetchone():
                cursor.execute("UPDATE cup SET current_round_number = 1 WHERE current_round_number IS NULL")
                updated_cups = cursor.rowcount
                if updated_cups > 0:
                    print(f"  {updated_cups} Cup-Einträge mit NULL current_round_number auf 1 gesetzt")

                cursor.execute("UPDATE cup SET total_rounds = 1 WHERE total_rounds IS NULL")
                updated_total_rounds = cursor.rowcount
                if updated_total_rounds > 0:
                    print(f"  {updated_total_rounds} Cup-Einträge mit NULL total_rounds auf 1 gesetzt")

            db.session.commit()
            print("NULL-Werte erfolgreich bereinigt")

        except Exception as e:
            print(f"Fehler beim Bereinigen der NULL-Werte: {str(e)}")

        print("Alle fehlenden Daten erfolgreich ergänzt.")
        return {"success": True, "message": "Alle fehlenden Daten erfolgreich ergänzt."}

    except Exception as e:
        print(f"Fehler beim Ergänzen der Daten: {str(e)}")
        return {"success": False, "message": f"Fehler beim Ergänzen der Daten: {str(e)}"}


if __name__ == "__main__":
    # Überprüfe, ob die erforderlichen Argumente übergeben wurden
    if len(sys.argv) < 3:
        print("Fehler: Bitte geben Sie den Pfad zur Quell-Datenbank und den Namen der Ziel-Datenbank an.")
        print("Verwendung: python extend_existing_db.py <quell_db_pfad> <ziel_db_name>")
        sys.exit(1)

    source_db_path = sys.argv[1]
    target_db_name = sys.argv[2]

    result = extend_existing_database(source_db_path, target_db_name)

    if result["success"]:
        print(result["message"])
        sys.exit(0)
    else:
        print(f"Fehler: {result['message']}")
        sys.exit(1)
