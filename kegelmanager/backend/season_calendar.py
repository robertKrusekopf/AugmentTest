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
    Erstellt den Kalender für eine Saison mit 52 Samstagen.
    Verteilt Liga- und Pokalspieltage gleichmäßig über die Saison.
    """
    season = Season.query.get(season_id)
    if not season:
        raise ValueError(f"Season with ID {season_id} not found")
    
    print(f"Creating calendar for season {season.name} (ID: {season_id})")
    
    # Lösche existierende Kalendereinträge für diese Saison
    SeasonCalendar.query.filter_by(season_id=season_id).delete()
    
    # Berechne alle 52 Samstage des Jahres basierend auf dem Saisonstartdatum
    saturdays = calculate_saturdays_for_season(season.start_date)
    
    # Ermittle benötigte Liga- und Pokalspieltage
    league_match_days_needed = calculate_league_match_days_needed(season_id)
    cup_match_days_needed = calculate_cup_match_days_needed(season_id)
    
    print(f"Calendar needs: {league_match_days_needed} league days, {cup_match_days_needed} cup days")
    
    # Erstelle Kalenderverteilung
    calendar_distribution = create_calendar_distribution(
        total_weeks=52,
        league_days=league_match_days_needed,
        cup_days=cup_match_days_needed
    )
    
    # Erstelle Kalendereinträge in der Datenbank
    match_day_counter = 1
    for week_num, (saturday_date, day_type) in enumerate(zip(saturdays, calendar_distribution), 1):
        calendar_entry = SeasonCalendar(
            season_id=season_id,
            week_number=week_num,
            calendar_date=saturday_date,
            day_type=day_type,
            match_day_number=match_day_counter if day_type in ['LEAGUE_DAY', 'CUP_DAY'] else None,
            is_simulated=False
        )
        db.session.add(calendar_entry)
        
        if day_type in ['LEAGUE_DAY', 'CUP_DAY']:
            match_day_counter += 1
    
    db.session.commit()
    print(f"Created calendar with {len(saturdays)} weeks for season {season.name}")
    
    return calendar_distribution


def calculate_saturdays_for_season(start_date):
    """
    Berechnet alle 52 Samstage eines Jahres basierend auf dem Saisonstartdatum.
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


def create_calendar_distribution(total_weeks, league_days, cup_days):
    """
    Erstellt eine gleichmäßige Verteilung von Liga-, Pokal- und spielfreien Tagen.
    """
    if league_days + cup_days > total_weeks:
        raise ValueError(f"Not enough weeks ({total_weeks}) for {league_days} league days and {cup_days} cup days")
    
    # Berechne spielfreie Tage
    free_days = total_weeks - league_days - cup_days
    
    print(f"Distribution: {league_days} league, {cup_days} cup, {free_days} free days")
    
    # Erstelle Liste mit allen Tagen
    days = ['LEAGUE_DAY'] * league_days + ['CUP_DAY'] * cup_days + ['FREE_DAY'] * free_days
    
    # Mische für gleichmäßige Verteilung, aber stelle sicher, dass nicht zu viele
    # aufeinanderfolgende Spieltage entstehen
    distribution = distribute_days_evenly(days, total_weeks)
    
    return distribution


def distribute_days_evenly(days, total_weeks):
    """
    Verteilt die Spieltage gleichmäßig über die Saison.
    Vermeidet zu viele aufeinanderfolgende Spieltage.
    """
    # Zähle jeden Typ
    league_count = days.count('LEAGUE_DAY')
    cup_count = days.count('CUP_DAY')
    free_count = days.count('FREE_DAY')
    
    # Erstelle gleichmäßige Verteilung
    distribution = []
    
    # Berechne Intervalle für gleichmäßige Verteilung
    if league_count > 0:
        league_interval = total_weeks / league_count
    else:
        league_interval = float('inf')
        
    if cup_count > 0:
        cup_interval = total_weeks / cup_count
    else:
        cup_interval = float('inf')
    
    # Verteile Tage basierend auf Intervallen
    league_positions = [int(i * league_interval) for i in range(league_count)]
    cup_positions = [int(i * cup_interval + cup_interval/2) for i in range(cup_count)]  # Offset für Pokale
    
    # Initialisiere mit spielfreien Tagen
    distribution = ['FREE_DAY'] * total_weeks
    
    # Setze Ligaspieltage
    for pos in league_positions:
        if pos < total_weeks:
            distribution[pos] = 'LEAGUE_DAY'
    
    # Setze Pokalspieltage (vermeide Überschneidungen)
    for pos in cup_positions:
        if pos < total_weeks:
            # Finde nächste freie Position
            while pos < total_weeks and distribution[pos] != 'FREE_DAY':
                pos += 1
            if pos < total_weeks:
                distribution[pos] = 'CUP_DAY'
    
    return distribution


def get_next_calendar_day(season_id):
    """
    Gibt den nächsten zu simulierenden Kalendertag zurück.
    """
    next_day = SeasonCalendar.query.filter_by(
        season_id=season_id,
        is_simulated=False
    ).order_by(SeasonCalendar.week_number).first()
    
    return next_day


def mark_calendar_day_simulated(season_id, week_number):
    """
    Markiert einen Kalendertag als simuliert.
    """
    calendar_day = SeasonCalendar.query.filter_by(
        season_id=season_id,
        week_number=week_number
    ).first()
    
    if calendar_day:
        calendar_day.is_simulated = True
        db.session.commit()


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
    """
    # Hole alle Ligaspieltage aus dem Kalender
    league_days = SeasonCalendar.query.filter_by(
        season_id=season_id,
        day_type='LEAGUE_DAY'
    ).order_by(SeasonCalendar.week_number).all()
    
    # Hole alle Pokalspieltage aus dem Kalender
    cup_days = SeasonCalendar.query.filter_by(
        season_id=season_id,
        day_type='CUP_DAY'
    ).order_by(SeasonCalendar.week_number).all()
    
    print(f"Updating match days: {len(league_days)} league days, {len(cup_days)} cup days")
    
    # Aktualisiere Ligaspiele
    for i, calendar_day in enumerate(league_days, 1):
        matches = Match.query.join(League).filter(
            League.season_id == season_id,
            Match.match_day == i
        ).all()
        
        for match in matches:
            match.match_day = calendar_day.match_day_number
    
    # Aktualisiere Pokalspiele
    for i, calendar_day in enumerate(cup_days, 1):
        cup_matches = CupMatch.query.join(Cup).filter(
            Cup.season_id == season_id,
            CupMatch.cup_match_day == i
        ).all()
        
        for cup_match in cup_matches:
            cup_match.cup_match_day = calendar_day.match_day_number
    
    db.session.commit()
    print("Updated match day numbers from calendar")
