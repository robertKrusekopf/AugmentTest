"""
Saisonkalender-Logik für die Bowling-Simulation.

Verwaltet die 52 Samstage eines Jahres und teilt sie in drei Kategorien ein:
- FREE_DAY: Spielfreier Tag
- LEAGUE_DAY: Ligaspieltag
- CUP_DAY: Pokalspieltag
"""

from datetime import datetime, timedelta, date
from models import db, SeasonCalendar, Season, League, Match, Cup, CupMatch
from sqlalchemy import func
import random


def create_season_calendar(season_id):
    """
    Erstellt den Kalender für eine Saison mit 104 Spielmöglichkeiten (52 Samstage + 52 Mittwoche).
    Verteilt Liga- und Pokalspieltage gleichmäßig über die Saison.
    """
    season = Season.query.get(season_id)
    if not season:
        raise ValueError(f"Season with ID {season_id} not found")

    print(f"Creating calendar for season {season.name} (ID: {season_id})")

    # Lösche existierende Kalendereinträge für diese Saison
    SeasonCalendar.query.filter_by(season_id=season_id).delete()

    # Berechne alle Spielmöglichkeiten: 52 Samstage + 52 Mittwoche = 104 Slots
    match_slots = calculate_match_slots_for_season(season.start_date)

    # Ermittle benötigte Liga- und Pokalspieltage
    league_match_days_needed = calculate_league_match_days_needed(season_id)
    cup_match_days_needed = calculate_cup_match_days_needed(season_id)

    print(f"Calendar needs: {league_match_days_needed} league days, {cup_match_days_needed} cup days")

    # Erstelle Kalenderverteilung mit 104 Slots
    calendar_distribution = create_calendar_distribution(
        total_slots=104,
        league_days=league_match_days_needed,
        cup_days=cup_match_days_needed
    )
    
    # Erstelle Kalendereinträge in der Datenbank
    # Separate Zähler für Liga- und Pokaltage
    league_day_counter = 1
    cup_day_counter = 1
    weekdays = ['Saturday', 'Wednesday'] * 52  # Abwechselnd Samstag und Mittwoch

    for slot_num, (match_date, day_type) in enumerate(zip(match_slots, calendar_distribution), 1):
        match_day_number = None
        if day_type == 'LEAGUE_DAY':
            match_day_number = league_day_counter
            league_day_counter += 1
        elif day_type == 'CUP_DAY':
            match_day_number = cup_day_counter
            cup_day_counter += 1

        weekday = weekdays[slot_num - 1]  # Bestimme Wochentag basierend auf Slot-Position

        calendar_entry = SeasonCalendar(
            season_id=season_id,
            week_number=((slot_num - 1) // 2) + 1,  # Woche 1-52
            calendar_date=match_date,
            weekday=weekday,
            day_type=day_type,
            match_day_number=match_day_number,
            is_simulated=False
        )
        db.session.add(calendar_entry)

    db.session.commit()
    print(f"Created calendar with {len(match_slots)} match slots for season {season.name}")

    return calendar_distribution


def calculate_match_slots_for_season(start_date):
    """
    Berechnet alle 104 Spielmöglichkeiten einer Saison: 52 Samstage + 52 Mittwoche.
    Reihenfolge: Samstag Woche 1, Mittwoch Woche 1, Samstag Woche 2, Mittwoch Woche 2, ...
    """
    match_slots = []

    # Finde den ersten Samstag ab dem Startdatum
    current_saturday = start_date
    while current_saturday.weekday() != 5:  # 5 = Samstag
        current_saturday += timedelta(days=1)

    # Sammle 52 Wochen mit je Samstag und Mittwoch
    for week in range(52):
        # Samstag dieser Woche
        saturday = current_saturday + timedelta(weeks=week)
        match_slots.append(saturday)

        # Mittwoch dieser Woche (3 Tage nach Samstag, aber der nächsten Woche)
        wednesday = saturday + timedelta(days=4)  # Samstag + 4 Tage = Mittwoch
        match_slots.append(wednesday)

    return match_slots


def calculate_saturdays_for_season(start_date):
    """
    Berechnet alle 52 Samstage eines Jahres basierend auf dem Saisonstartdatum.
    (Legacy-Funktion für Kompatibilität)
    """
    saturdays = []

    # Finde den ersten Samstag ab dem Startdatum
    current_date = start_date
    while current_date.weekday() != 5:  # 5 = Samstag
        current_date += timedelta(days=1)

    # Sammle 52 Samstage
    for week in range(52):
        saturdays.append(current_date)
        current_date += timedelta(weeks=1)

    return saturdays


def calculate_league_match_days_needed(season_id):
    """
    Berechnet die Anzahl der benötigten Ligaspieltage basierend auf den Ligen.
    """
    # Ermittle die maximale Anzahl von Spieltagen über alle Ligen
    max_match_day = db.session.query(func.max(Match.match_day)).join(League).filter(
        League.season_id == season_id,
        Match.match_day.isnot(None)
    ).scalar()
    
    if max_match_day:
        print(f"Found existing league matches with max match day: {max_match_day}")
        return max_match_day
    
    # Fallback: Berechne basierend auf Teamanzahl
    leagues = League.query.filter_by(season_id=season_id).all()
    max_needed = 0
    
    for league in leagues:
        from models import Team
        teams_count = Team.query.filter_by(league_id=league.id).count()
        if teams_count >= 2:
            # Doppelrunde: (teams - 1) * 2 Spieltage
            needed_match_days = (teams_count - 1) * 2
            max_needed = max(max_needed, needed_match_days)
    
    print(f"Calculated league match days needed: {max_needed}")
    return max_needed or 34  # Fallback auf 34 Spieltage


def calculate_cup_match_days_needed(season_id):
    """
    Berechnet die Anzahl der benötigten Pokalspieltage basierend auf den Pokalen.
    """
    cups = Cup.query.filter_by(season_id=season_id).all()
    total_cup_days = 0
    
    for cup in cups:
        # Jeder Pokal benötigt so viele Spieltage wie er Runden hat
        total_cup_days += cup.total_rounds
    
    print(f"Calculated cup match days needed: {total_cup_days}")
    return total_cup_days


def create_calendar_distribution(total_slots, league_days, cup_days):
    """
    Erstellt eine Verteilung von Liga-, Pokal- und spielfreien Tagen über 104 Spielmöglichkeiten.
    Liga- und Pokalspieltage erhalten durchlaufende Spieltag-Nummern.
    """
    total_match_days = league_days + cup_days

    if total_match_days > total_slots:
        raise ValueError(f"Not enough slots ({total_slots}) for {league_days} league days and {cup_days} cup days")

    # Berechne spielfreie Slots
    free_slots = total_slots - league_days - cup_days

    print(f"Final distribution: {league_days} league, {cup_days} cup, {free_slots} free slots")

    # Verwende die bestehende gleichmäßige Verteilung
    # Liga- und Pokalspieltage werden separat nummeriert
    days = ['LEAGUE_DAY'] * league_days + ['CUP_DAY'] * cup_days + ['FREE_DAY'] * free_slots
    distribution = distribute_days_evenly(days, total_slots)

    return distribution


def distribute_days_evenly(days, total_slots):
    """
    Verteilt die Spieltage gleichmäßig über die 104 Spielmöglichkeiten.
    Vermeidet zu viele aufeinanderfolgende Spieltage und Kollisionen zwischen Liga- und Cup-Tagen.
    """
    # Zähle jeden Typ
    league_count = days.count('LEAGUE_DAY')
    cup_count = days.count('CUP_DAY')
    free_count = days.count('FREE_DAY')

    # Initialisiere mit spielfreien Tagen
    distribution = ['FREE_DAY'] * total_slots

    # Berechne Intervalle für gleichmäßige Verteilung
    if league_count > 0:
        league_interval = total_slots / league_count
    else:
        league_interval = float('inf')

    if cup_count > 0:
        cup_interval = total_slots / cup_count
    else:
        cup_interval = float('inf')

    # Verteile Liga-Tage zuerst (haben Priorität)
    league_positions = [int(i * league_interval) for i in range(league_count)]
    for pos in league_positions:
        if pos < total_slots:
            distribution[pos] = 'LEAGUE_DAY'

    # Verteile Cup-Tage mit intelligentem Placement (vermeide Kollisionen)
    cup_positions = []
    for i in range(cup_count):
        # Berechne ideale Position mit Offset
        ideal_pos = int(i * cup_interval + cup_interval/3)  # Kleinerer Offset für bessere Verteilung

        # Finde beste verfügbare Position in der Nähe der idealen Position
        best_pos = find_best_available_position(distribution, ideal_pos, total_slots)
        if best_pos is not None:
            distribution[best_pos] = 'CUP_DAY'
            cup_positions.append(best_pos)

    return distribution


def find_best_available_position(distribution, ideal_pos, total_slots):
    """
    Findet die beste verfügbare Position für einen Cup-Tag in der Nähe der idealen Position.
    Sucht zuerst nach links, dann nach rechts von der idealen Position.
    """
    # Prüfe zuerst die ideale Position
    if ideal_pos < total_slots and distribution[ideal_pos] == 'FREE_DAY':
        return ideal_pos

    # Suche in beide Richtungen von der idealen Position
    max_search_distance = min(20, total_slots // 4)  # Begrenze Suchbereich

    for distance in range(1, max_search_distance + 1):
        # Suche nach links
        left_pos = ideal_pos - distance
        if left_pos >= 0 and distribution[left_pos] == 'FREE_DAY':
            return left_pos

        # Suche nach rechts
        right_pos = ideal_pos + distance
        if right_pos < total_slots and distribution[right_pos] == 'FREE_DAY':
            return right_pos

    # Fallback: Finde irgendeine freie Position
    for pos in range(total_slots):
        if distribution[pos] == 'FREE_DAY':
            return pos

    return None  # Keine freie Position gefunden





def get_next_match_date(season_id):
    """
    Neue datums-basierte Logik: Findet das früheste Datum mit ungespielte Liga- oder Pokalspielen.
    Gibt ein Dictionary mit Informationen über den nächsten Spieltag zurück.
    """
    from sqlalchemy import func, union_all
    from models import Match, Cup, CupMatch

    # Finde das früheste Datum mit ungespielte Ligaspielen
    next_league_date = db.session.query(func.min(Match.match_date)).filter(
        Match.season_id == season_id,
        Match.is_played == False,
        Match.match_date.isnot(None)
    ).scalar()

    # Finde das früheste Datum mit ungespielte Pokalspielen
    next_cup_date = db.session.query(func.min(CupMatch.match_date)).filter(
        CupMatch.cup_id.in_(
            db.session.query(Cup.id).filter_by(season_id=season_id)
        ),
        CupMatch.is_played == False,
        CupMatch.match_date.isnot(None)
    ).scalar()

    # Bestimme das früheste Datum
    next_date = None
    if next_league_date and next_cup_date:
        # Beide sind jetzt DateTime - konvertiere zu Date für Vergleich
        league_date = next_league_date.date() if hasattr(next_league_date, 'date') else next_league_date
        cup_date = next_cup_date.date() if hasattr(next_cup_date, 'date') else next_cup_date
        next_date = min(league_date, cup_date)
    elif next_league_date:
        next_date = next_league_date.date() if hasattr(next_league_date, 'date') else next_league_date
    elif next_cup_date:
        next_date = next_cup_date.date() if hasattr(next_cup_date, 'date') else next_cup_date

    if not next_date:
        return None

    # Finde den entsprechenden SeasonCalendar Eintrag für dieses Datum
    calendar_day = SeasonCalendar.query.filter(
        SeasonCalendar.season_id == season_id,
        SeasonCalendar.calendar_date == next_date
    ).first()

    if not calendar_day:
        # Fallback: Erstelle einen temporären Kalendereintrag
        print(f"WARNING: No calendar entry found for date {next_date}, creating temporary entry")
        # Bestimme den Typ basierend auf welche Spiele an diesem Tag stattfinden
        has_league_matches = db.session.query(Match.id).filter(
            Match.season_id == season_id,
            Match.is_played == False,
            func.date(Match.match_date) == next_date
        ).first() is not None

        has_cup_matches = db.session.query(CupMatch.id).filter(
            CupMatch.cup_id.in_(
                db.session.query(Cup.id).filter_by(season_id=season_id)
            ),
            CupMatch.is_played == False,
            CupMatch.match_date == next_date
        ).first() is not None

        # Erstelle temporären Kalendereintrag
        day_type = 'LEAGUE_DAY' if has_league_matches else 'CUP_DAY'

        # Finde eine passende match_day_number
        if has_league_matches:
            match_day_number = db.session.query(Match.match_day).filter(
                Match.season_id == season_id,
                func.date(Match.match_date) == next_date
            ).first()
            match_day_number = match_day_number[0] if match_day_number else 1
        else:
            match_day_number = db.session.query(CupMatch.cup_match_day).filter(
                CupMatch.cup_id.in_(
                    db.session.query(Cup.id).filter_by(season_id=season_id)
                ),
                CupMatch.match_date == next_date
            ).first()
            match_day_number = match_day_number[0] if match_day_number else 1

        # Erstelle temporären Kalendereintrag (wird nicht in DB gespeichert)
        class TempCalendarDay:
            def __init__(self):
                self.id = -1  # Temporäre ID
                self.season_id = season_id
                self.calendar_date = next_date
                self.day_type = day_type
                self.match_day_number = match_day_number
                self.is_simulated = False
                self.week_number = 1  # Dummy-Wert
                self.weekday = 'Saturday'  # Dummy-Wert

        calendar_day = TempCalendarDay()

    return calendar_day


def mark_calendar_day_simulated(calendar_day_id):
    """
    Markiert einen spezifischen Kalendertag als simuliert.
    Markiert auch alle anderen Kalendereinträge mit derselben match_day_number als simuliert.
    Unterstützt auch temporäre Kalendereinträge (ID = -1).
    """
    if calendar_day_id == -1:
        # Temporärer Kalendereintrag - nichts zu markieren
        print("Temporary calendar day - no marking needed")
        return

    calendar_day = SeasonCalendar.query.get(calendar_day_id)

    if calendar_day and calendar_day.match_day_number:
        # Markiere alle Kalendereinträge mit derselben match_day_number als simuliert
        SeasonCalendar.query.filter(
            SeasonCalendar.season_id == calendar_day.season_id,
            SeasonCalendar.match_day_number == calendar_day.match_day_number
        ).update({'is_simulated': True})

        db.session.commit()
        print(f"Marked match day {calendar_day.match_day_number} (Week {calendar_day.week_number}, {calendar_day.day_type}) as simulated")
    else:
        print(f"Calendar day {calendar_day_id} not found or has no match_day_number")


def get_season_calendar(season_id):
    """
    Gibt den kompletten Kalender für eine Saison zurück.
    """
    calendar_days = SeasonCalendar.query.filter_by(
        season_id=season_id
    ).order_by(SeasonCalendar.week_number).all()
    
    return [day.to_dict() for day in calendar_days]


def update_match_days_from_calendar(season_id):
    """
    Aktualisiert die match_day Nummern in Liga- und Pokalspielen basierend auf dem Kalender.
    Liga- und Pokalspieltage haben separate Nummerierungen.
    """
    # Hole alle Ligaspieltage aus dem Kalender (sortiert nach Wochennummer)
    league_days = SeasonCalendar.query.filter_by(
        season_id=season_id,
        day_type='LEAGUE_DAY'
    ).order_by(SeasonCalendar.week_number).all()

    # Hole alle Pokalspieltage aus dem Kalender (sortiert nach Wochennummer)
    cup_days = SeasonCalendar.query.filter_by(
        season_id=season_id,
        day_type='CUP_DAY'
    ).order_by(SeasonCalendar.week_number).all()

    print(f"Updating match days: {len(league_days)} league days, {len(cup_days)} cup days")

    # Aktualisiere Ligaspiele - match_day_number entspricht der Liga-internen Nummerierung
    for calendar_day in league_days:
        matches = Match.query.join(League).filter(
            League.season_id == season_id,
            Match.match_day == calendar_day.match_day_number
        ).all()

        print(f"League day {calendar_day.match_day_number} (week {calendar_day.week_number}): {len(matches)} matches")

    # Aktualisiere Pokalspiele - match_day_number entspricht der Pokal-internen Nummerierung
    for calendar_day in cup_days:
        cup_matches = CupMatch.query.join(Cup).filter(
            Cup.season_id == season_id,
            CupMatch.cup_match_day == calendar_day.match_day_number
        ).all()

        print(f"Cup day {calendar_day.match_day_number} (week {calendar_day.week_number}): {len(cup_matches)} matches")

    db.session.commit()
    print("Match day numbers are already correctly set from calendar")


def set_cup_match_dates(season_id):
    """
    Setzt die match_date für alle Pokalspiele basierend auf dem SeasonCalendar.
    """
    season = Season.query.get(season_id)
    if not season:
        raise ValueError(f"Season with ID {season_id} not found")

    print(f"Setting cup match dates for season {season.name}")

    # Hole alle Pokalspieltage aus dem Kalender
    cup_days = SeasonCalendar.query.filter_by(
        season_id=season_id,
        day_type='CUP_DAY'
    ).all()

    if not cup_days:
        print("No cup days found in calendar")
        return

    # Erstelle ein Mapping von cup_match_day zu calendar_date (als DateTime)
    cup_day_to_date = {}
    for calendar_day in cup_days:
        if calendar_day.match_day_number:
            # Konvertiere das Datum zu einem datetime um 15:00 Uhr
            match_datetime = datetime.combine(
                calendar_day.calendar_date,
                datetime.min.time().replace(hour=15),
                tzinfo=timezone.utc
            )
            cup_day_to_date[calendar_day.match_day_number] = match_datetime

    print(f"Found {len(cup_day_to_date)} cup match days in calendar")

    # Aktualisiere alle ungespielte Pokalspiele mit den entsprechenden Daten
    cups = Cup.query.filter_by(season_id=season_id).all()
    updated_matches = 0

    for cup in cups:
        cup_matches = CupMatch.query.filter_by(cup_id=cup.id, is_played=False).all()

        for cup_match in cup_matches:
            if cup_match.cup_match_day and cup_match.cup_match_day in cup_day_to_date:
                # Setze das DateTime basierend auf dem Kalender
                cup_match.match_date = cup_day_to_date[cup_match.cup_match_day]
                updated_matches += 1
                print(f"Set date for cup match {cup_match.id}: {cup_match.match_date}")

    db.session.commit()
    print(f"Updated {updated_matches} cup matches with dates")


def set_cup_match_dates_simple(season_id):
    """
    Setzt die match_date für alle Pokalspiele basierend auf einer einfachen Berechnung.
    Verwendet die Pokalspieltag-Nummer und verteilt sie gleichmäßig über die Saison.
    """
    from datetime import timedelta

    season = Season.query.get(season_id)
    if not season:
        raise ValueError(f"Season with ID {season_id} not found")

    print(f"Setting cup match dates (simple) for season {season.name}")

    # Hole alle Pokale für diese Saison
    cups = Cup.query.filter_by(season_id=season.id).all()
    if not cups:
        print("No cups found for this season")
        return 0

    updated_matches = 0

    for cup in cups:
        cup_matches = CupMatch.query.filter_by(cup_id=cup.id, is_played=False).all()

        for cup_match in cup_matches:
            if cup_match.cup_match_day:
                # Berechne das Datum basierend auf dem Pokalspieltag
                # Pokalspieltage werden zwischen den Ligaspieltagen verteilt
                # Verwende eine einfache Formel: Saisonstart + (cup_match_day * 2 Wochen)
                weeks_offset = cup_match.cup_match_day * 2
                match_date = season.start_date + timedelta(weeks=weeks_offset)

                # Konvertiere zu DateTime um 15:00 Uhr
                match_datetime = datetime.combine(
                    match_date,
                    datetime.min.time().replace(hour=15),
                    tzinfo=timezone.utc
                )

                # Setze das DateTime
                cup_match.match_date = match_datetime
                updated_matches += 1
                print(f"Set date for cup match {cup_match.id} (day {cup_match.cup_match_day}): {match_datetime}")

    db.session.commit()
    print(f"Updated {updated_matches} cup matches with dates (simple method)")
    return updated_matches


def set_all_match_dates_unified(season_id):
    """
    Einheitliche Funktion zum Setzen aller Spieldaten (Liga und Pokal) basierend auf dem SeasonCalendar.
    Diese Funktion stellt sicher, dass Liga- und Pokalspiele nur auf ihre jeweiligen Kalendertage gesetzt werden.
    """
    from datetime import datetime, timezone

    season = Season.query.get(season_id)
    if not season:
        raise ValueError(f"Season with ID {season_id} not found")

    print(f"Setting unified match dates for season {season.name}")

    # Hole Liga-Kalendertage separat
    league_calendar_days = SeasonCalendar.query.filter_by(
        season_id=season_id,
        day_type='LEAGUE_DAY'
    ).filter(
        SeasonCalendar.match_day_number.isnot(None)
    ).all()

    # Hole Pokal-Kalendertage separat
    cup_calendar_days = SeasonCalendar.query.filter_by(
        season_id=season_id,
        day_type='CUP_DAY'
    ).filter(
        SeasonCalendar.match_day_number.isnot(None)
    ).all()

    print(f"Found {len(league_calendar_days)} league days and {len(cup_calendar_days)} cup days in calendar")

    # Erstelle separate Mappings für Liga- und Pokaltage
    league_match_day_to_date = {}
    for calendar_day in league_calendar_days:
        if calendar_day.match_day_number:
            # Konvertiere das Datum zu einem datetime um 15:00 Uhr
            match_datetime = datetime.combine(
                calendar_day.calendar_date,
                datetime.min.time().replace(hour=15),
                tzinfo=timezone.utc
            )
            league_match_day_to_date[calendar_day.match_day_number] = match_datetime

    cup_match_day_to_date = {}
    for calendar_day in cup_calendar_days:
        if calendar_day.match_day_number:
            # Konvertiere das Datum zu einem datetime um 15:00 Uhr
            match_datetime = datetime.combine(
                calendar_day.calendar_date,
                datetime.min.time().replace(hour=15),
                tzinfo=timezone.utc
            )
            cup_match_day_to_date[calendar_day.match_day_number] = match_datetime

    updated_league_matches = 0
    updated_cup_matches = 0

    # Setze Daten für Ligaspiele - nur auf LEAGUE_DAY Termine und nur für ungespielte Spiele
    from models import Match
    league_matches = Match.query.filter_by(season_id=season_id, is_played=False).all()

    for match in league_matches:
        if match.match_day and match.match_day in league_match_day_to_date:
            old_date = match.match_date
            match.match_date = league_match_day_to_date[match.match_day]
            updated_league_matches += 1
            # Debug: Zeige die ersten 3 Updates
            if updated_league_matches <= 3:
                print(f"DEBUG: Updated league match {match.id}: {old_date} -> {match.match_date}")

    # Zwischenspeichern für Liga-Spiele
    db.session.flush()
    print(f"DEBUG: Flushed {updated_league_matches} league match updates")

    # Setze Daten für Pokalspiele - nur auf CUP_DAY Termine und nur für ungespielte Spiele
    from models import Cup, CupMatch
    cups = Cup.query.filter_by(season_id=season_id).all()

    for cup in cups:
        cup_matches = CupMatch.query.filter_by(cup_id=cup.id, is_played=False).all()

        for cup_match in cup_matches:
            if cup_match.cup_match_day and cup_match.cup_match_day in cup_match_day_to_date:
                old_date = cup_match.match_date
                # Für Pokalspiele verwenden wir jetzt auch DateTime (wie Liga-Spiele)
                calendar_datetime = cup_match_day_to_date[cup_match.cup_match_day]
                cup_match.match_date = calendar_datetime
                updated_cup_matches += 1
                # Debug: Zeige die ersten 3 Updates
                if updated_cup_matches <= 3:
                    print(f"DEBUG: Updated cup match {cup_match.id}: {old_date} -> {cup_match.match_date}")

    # Zwischenspeichern für Pokal-Spiele
    db.session.flush()
    print(f"DEBUG: Flushed {updated_cup_matches} cup match updates")

    # Finaler Commit
    db.session.commit()
    print(f"DEBUG: Committed all changes to database")
    print(f"Updated {updated_league_matches} league matches and {updated_cup_matches} cup matches with unified dates")

    # Validierung: Prüfe auf Datumskonflikte
    validate_no_date_conflicts(season_id)

    return updated_league_matches + updated_cup_matches


def fix_existing_cup_match_dates():
    """
    Repariert die Datumszuweisung für alle bestehenden Pokalspiele in allen Saisons.
    """
    from models import Season

    seasons = Season.query.all()
    total_fixed = 0

    for season in seasons:
        print(f"Fixing cup match dates for season {season.name}")
        try:
            # Verwende die einfache Methode, falls der Saisonkalender nicht funktioniert
            try:
                fixed_count = set_cup_match_dates(season.id)
            except Exception as e:
                print(f"Calendar-based method failed: {e}, trying simple method")
                fixed_count = set_cup_match_dates_simple(season.id)

            total_fixed += fixed_count
            print(f"Fixed {fixed_count} cup matches in season {season.name}")
        except Exception as e:
            print(f"Error fixing cup match dates for season {season.name}: {e}")

    print(f"Total cup matches fixed: {total_fixed}")
    return total_fixed


def validate_no_date_conflicts(season_id):
    """
    Validiert, dass keine Liga- und Pokalspiele am selben Datum stattfinden.
    """
    from models import Match, CupMatch
    from sqlalchemy import func

    print(f"Validating no date conflicts for season {season_id}")

    # Hole alle Liga-Spieldaten
    league_dates = db.session.query(
        func.date(Match.match_date).label('match_date')
    ).filter(
        Match.season_id == season_id,
        Match.match_date.isnot(None)
    ).distinct().all()

    league_dates_set = {date[0] for date in league_dates if date[0]}

    # Hole alle Pokal-Spieldaten
    cup_dates = db.session.query(
        CupMatch.match_date
    ).join(Cup).filter(
        Cup.season_id == season_id,
        CupMatch.match_date.isnot(None)
    ).distinct().all()

    cup_dates_set = {date[0] for date in cup_dates if date[0]}

    # Prüfe auf Überschneidungen
    conflicts = league_dates_set.intersection(cup_dates_set)

    if conflicts:
        print(f"⚠️  WARNUNG: {len(conflicts)} Datumskonflikte gefunden:")
        for conflict_date in sorted(conflicts):
            print(f"  - {conflict_date}: Liga- und Pokalspiele am selben Tag")
        return False
    else:
        print(f"✅ Keine Datumskonflikte gefunden! Liga: {len(league_dates_set)} Tage, Pokal: {len(cup_dates_set)} Tage")
        return True
