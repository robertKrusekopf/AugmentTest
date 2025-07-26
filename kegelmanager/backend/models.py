from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text

db = SQLAlchemy()

# Constants for ID ranges
CUP_MATCH_ID_OFFSET = 1000000  # Cup match IDs start at 1,000,000

def get_cup_match_frontend_id(db_id):
    """Convert database cup match ID to frontend ID."""
    return db_id + CUP_MATCH_ID_OFFSET

# Association table for many-to-many relationship between players and teams
player_team = db.Table('player_team',
    db.Column('player_id', db.Integer, db.ForeignKey('player.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True)
)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    strength = db.Column(db.Integer, nullable=False)  # 1-99
    talent = db.Column(db.Integer, nullable=False)    # 1-10
    position = db.Column(db.String(50))
    salary = db.Column(db.Float, default=0.0)
    contract_end = db.Column(db.Date)

    # Neue Verknüpfung zum Verein
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), index=True)

    # Flag, ob der Spieler am aktuellen Spieltag bereits gespielt hat
    has_played_current_matchday = db.Column(db.Boolean, default=False, index=True)
    last_played_matchday = db.Column(db.Integer, nullable=True, index=True)  # Speichert den letzten Spieltag, an dem der Spieler gespielt hat

    # Flag, ob der Spieler am aktuellen Spieltag verfügbar ist (nicht durch Schichtarbeit o.ä. verhindert)
    is_available_current_matchday = db.Column(db.Boolean, default=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Kegeln-spezifische Attribute
    ausdauer = db.Column(db.Integer, default=70)      # 1-99: Ausdauer über alle Bahnen

    # Neue Attribute
    konstanz = db.Column(db.Integer, default=70)     # 1-99: Konstanz über mehrere Spiele hinweg
    drucksicherheit = db.Column(db.Integer, default=70)  # 1-99: Leistung unter Druck
    volle = db.Column(db.Integer, default=70)        # 1-99: Fähigkeit auf die vollen Kegel
    raeumer = db.Column(db.Integer, default=70)      # 1-99: Fähigkeit beim Abräumen
    sicherheit = db.Column(db.Integer, default=70)   # 1-99: Vermeidung von Fehlwürfen

    # Weitere Attribute
    auswaerts = db.Column(db.Integer, default=70)    # 1-99: Leistung bei Auswärtsspielen
    start = db.Column(db.Integer, default=70)        # 1-99: Leistung zu Beginn eines Spiels
    mitte = db.Column(db.Integer, default=70)        # 1-99: Leistung in der Mitte eines Spiels
    schluss = db.Column(db.Integer, default=70)      # 1-99: Leistung am Ende eines Spiels

    # Form-System: Modifikatoren für unterschiedliche Zeiträume
    form_short_term = db.Column(db.Float, default=0.0)           # -20 bis +20: Kurzfristige Form (1-3 Spieltage)
    form_medium_term = db.Column(db.Float, default=0.0)          # -15 bis +15: Mittelfristige Form (4-8 Spieltage)
    form_long_term = db.Column(db.Float, default=0.0)            # -10 bis +10: Langfristige Form (10-20 Spieltage)

    # Verbleibende Tage für Form-Modifikatoren
    form_short_remaining_days = db.Column(db.Integer, default=0)  # Verbleibende Tage für kurzfristige Form
    form_medium_remaining_days = db.Column(db.Integer, default=0) # Verbleibende Tage für mittelfristige Form
    form_long_remaining_days = db.Column(db.Integer, default=0)   # Verbleibende Tage für langfristige Form

    # Relationships
    club = db.relationship('Club', back_populates='players')
    teams = db.relationship('Team', secondary=player_team, back_populates='players')
    performances = db.relationship('PlayerMatchPerformance', back_populates='player')

    def calculate_stats(self):
        """Calculate player statistics based on played matches."""
        # Get all performances for this player
        performances = self.performances

        # Initialize statistics
        home_performances = [p for p in performances if p.is_home_team]
        away_performances = [p for p in performances if not p.is_home_team]

        total_matches = len(performances)
        home_matches = len(home_performances)
        away_matches = len(away_performances)

        # Initialize statistics
        total_score = sum(p.total_score for p in performances) if performances else 0
        home_score = sum(p.total_score for p in home_performances) if home_performances else 0
        away_score = sum(p.total_score for p in away_performances) if away_performances else 0

        total_volle = sum(p.volle_score for p in performances) if performances else 0
        home_volle = sum(p.volle_score for p in home_performances) if home_performances else 0
        away_volle = sum(p.volle_score for p in away_performances) if away_performances else 0

        total_raeumer = sum(p.raeumer_score for p in performances) if performances else 0
        home_raeumer = sum(p.raeumer_score for p in home_performances) if home_performances else 0
        away_raeumer = sum(p.raeumer_score for p in away_performances) if away_performances else 0

        total_fehler = sum(p.fehler_count for p in performances) if performances else 0
        home_fehler = sum(p.fehler_count for p in home_performances) if home_performances else 0
        away_fehler = sum(p.fehler_count for p in away_performances) if away_performances else 0

        # Calculate match points won percentage
        total_mp_won = sum(1 for p in performances if p.match_points > 0) if performances else 0
        mp_win_percentage = (total_mp_won / total_matches * 100) if total_matches > 0 else 0

        # Calculate averages
        avg_total_score = total_score / total_matches if total_matches > 0 else 0
        avg_home_score = home_score / home_matches if home_matches > 0 else 0
        avg_away_score = away_score / away_matches if away_matches > 0 else 0

        avg_total_volle = total_volle / total_matches if total_matches > 0 else 0
        avg_home_volle = home_volle / home_matches if home_matches > 0 else 0
        avg_away_volle = away_volle / away_matches if away_matches > 0 else 0

        avg_total_raeumer = total_raeumer / total_matches if total_matches > 0 else 0
        avg_home_raeumer = home_raeumer / home_matches if home_matches > 0 else 0
        avg_away_raeumer = away_raeumer / away_matches if away_matches > 0 else 0

        avg_total_fehler = total_fehler / total_matches if total_matches > 0 else 0
        avg_home_fehler = home_fehler / home_matches if home_matches > 0 else 0
        avg_away_fehler = away_fehler / away_matches if away_matches > 0 else 0

        return {
            'total_matches': total_matches,
            'home_matches': home_matches,
            'away_matches': away_matches,
            'avg_total_score': round(avg_total_score, 1),
            'avg_home_score': round(avg_home_score, 1),
            'avg_away_score': round(avg_away_score, 1),
            'avg_total_volle': round(avg_total_volle, 1),
            'avg_home_volle': round(avg_home_volle, 1),
            'avg_away_volle': round(avg_away_volle, 1),
            'avg_total_raeumer': round(avg_total_raeumer, 1),
            'avg_home_raeumer': round(avg_home_raeumer, 1),
            'avg_away_raeumer': round(avg_away_raeumer, 1),
            'avg_total_fehler': round(avg_total_fehler, 1),
            'avg_home_fehler': round(avg_home_fehler, 1),
            'avg_away_fehler': round(avg_away_fehler, 1),
            'mp_win_percentage': round(mp_win_percentage, 1)
        }

    def calculate_team_specific_stats(self, team_id, season_id=None):
        """Calculate player statistics for a specific team.

        Args:
            team_id: The team ID to calculate stats for
            season_id: If provided, calculate stats only for this season.
                      If None, calculate stats for all seasons.
        """
        # Get all performances for this player with this team
        if season_id:
            # Filter performances by team and season
            performances = []
            for p in self.performances:
                if p.team_id == team_id and p.match and p.match.season_id == season_id:
                    performances.append(p)
        else:
            performances = [p for p in self.performances if p.team_id == team_id]

        # Initialize statistics
        home_performances = [p for p in performances if p.is_home_team]
        away_performances = [p for p in performances if not p.is_home_team]

        total_matches = len(performances)
        home_matches = len(home_performances)
        away_matches = len(away_performances)

        # Initialize statistics
        total_score = sum(p.total_score for p in performances) if performances else 0
        home_score = sum(p.total_score for p in home_performances) if home_performances else 0
        away_score = sum(p.total_score for p in away_performances) if away_performances else 0

        total_volle = sum(p.volle_score for p in performances) if performances else 0
        home_volle = sum(p.volle_score for p in home_performances) if home_performances else 0
        away_volle = sum(p.volle_score for p in away_performances) if away_performances else 0

        total_raeumer = sum(p.raeumer_score for p in performances) if performances else 0
        home_raeumer = sum(p.raeumer_score for p in home_performances) if home_performances else 0
        away_raeumer = sum(p.raeumer_score for p in away_performances) if away_performances else 0

        total_fehler = sum(p.fehler_count for p in performances) if performances else 0
        home_fehler = sum(p.fehler_count for p in home_performances) if home_performances else 0
        away_fehler = sum(p.fehler_count for p in away_performances) if away_performances else 0

        # Calculate match points won percentage
        total_mp_won = sum(1 for p in performances if p.match_points > 0) if performances else 0
        mp_win_percentage = (total_mp_won / total_matches * 100) if total_matches > 0 else 0

        # Calculate averages
        avg_total_score = total_score / total_matches if total_matches > 0 else 0
        avg_home_score = home_score / home_matches if home_matches > 0 else 0
        avg_away_score = away_score / away_matches if away_matches > 0 else 0

        avg_total_volle = total_volle / total_matches if total_matches > 0 else 0
        avg_home_volle = home_volle / home_matches if home_matches > 0 else 0
        avg_away_volle = away_volle / away_matches if away_matches > 0 else 0

        avg_total_raeumer = total_raeumer / total_matches if total_matches > 0 else 0
        avg_home_raeumer = home_raeumer / home_matches if home_matches > 0 else 0
        avg_away_raeumer = away_raeumer / away_matches if away_matches > 0 else 0

        avg_total_fehler = total_fehler / total_matches if total_matches > 0 else 0
        avg_home_fehler = home_fehler / home_matches if home_matches > 0 else 0
        avg_away_fehler = away_fehler / away_matches if away_matches > 0 else 0

        return {
            'total_matches': total_matches,
            'home_matches': home_matches,
            'away_matches': away_matches,
            'avg_total_score': round(avg_total_score, 1),
            'avg_home_score': round(avg_home_score, 1),
            'avg_away_score': round(avg_away_score, 1),
            'avg_total_volle': round(avg_total_volle, 1),
            'avg_home_volle': round(avg_home_volle, 1),
            'avg_away_volle': round(avg_away_volle, 1),
            'avg_total_raeumer': round(avg_total_raeumer, 1),
            'avg_home_raeumer': round(avg_home_raeumer, 1),
            'avg_away_raeumer': round(avg_away_raeumer, 1),
            'avg_total_fehler': round(avg_total_fehler, 1),
            'avg_home_fehler': round(avg_home_fehler, 1),
            'avg_away_fehler': round(avg_away_fehler, 1),
            'mp_win_percentage': round(mp_win_percentage, 1)
        }

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'strength': self.strength,
            'talent': self.talent,
            'position': self.position,
            'salary': self.salary,
            'contract_end': self.contract_end.isoformat() if self.contract_end else None,
            'club_id': self.club_id,
            # Kegeln-spezifische Attribute
            'ausdauer': self.ausdauer,
            # Neue Attribute
            'konstanz': self.konstanz,
            'drucksicherheit': self.drucksicherheit,
            'volle': self.volle,
            'raeumer': self.raeumer,
            'sicherheit': self.sicherheit,
            'auswaerts': self.auswaerts,
            'start': self.start,
            'mitte': self.mitte,
            'schluss': self.schluss,
            # Form-System
            'form_short_term': self.form_short_term,
            'form_medium_term': self.form_medium_term,
            'form_long_term': self.form_long_term,
            'form_short_remaining_days': self.form_short_remaining_days,
            'form_medium_remaining_days': self.form_medium_remaining_days,
            'form_long_remaining_days': self.form_long_remaining_days,
            'teams': [team.id for team in self.teams],
            # Spieltag-bezogene Flags
            'has_played_current_matchday': self.has_played_current_matchday,
            'is_available_current_matchday': self.is_available_current_matchday,
            # Include player statistics
            'statistics': self.calculate_stats()
        }

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'))
    is_youth_team = db.Column(db.Boolean, default=False)
    staerke = db.Column(db.Integer, default=0)  # Stärke des Teams, wird bei Spielergenerierung aufaddiert

    # Status from previous season for display in league tables
    previous_season_status = db.Column(db.String(20), nullable=True)  # 'promoted', 'relegated', 'champion', or None
    previous_season_position = db.Column(db.Integer, nullable=True)  # Position in previous season
    previous_season_league_level = db.Column(db.Integer, nullable=True)  # League level in previous season

    # Temporary fields for cheat function: target league for next season
    target_league_level = db.Column(db.Integer, nullable=True)  # Target league level for next season
    target_league_bundesland = db.Column(db.String(50), nullable=True)  # Target league bundesland
    target_league_landkreis = db.Column(db.String(100), nullable=True)  # Target league landkreis
    target_league_altersklasse = db.Column(db.String(50), nullable=True)  # Target league altersklasse

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    club = db.relationship('Club', back_populates='teams')
    league = db.relationship('League', back_populates='teams')
    players = db.relationship('Player', secondary=player_team, back_populates='teams')
    home_matches = db.relationship('Match', foreign_keys='Match.home_team_id', back_populates='home_team')
    away_matches = db.relationship('Match', foreign_keys='Match.away_team_id', back_populates='away_team')

    def get_substitute_players(self):
        """Get all players who have played for this team but are not regular team members."""
        # Get all performances for this team
        performances = PlayerMatchPerformance.query.filter_by(team_id=self.id).all()

        # Get all player IDs who have played for this team
        player_ids = set(perf.player_id for perf in performances)

        # Get all regular player IDs
        regular_player_ids = set(player.id for player in self.players)

        # Get all substitute player IDs (players who have played but are not regular team members)
        substitute_player_ids = player_ids - regular_player_ids

        # Get all substitute players
        substitute_players = Player.query.filter(Player.id.in_(substitute_player_ids)).all() if substitute_player_ids else []

        return substitute_players

    def to_dict(self):
        # Get club information for the team
        club_info = None
        if self.club:
            club_info = {
                'id': self.club.id,
                'name': self.club.name,
                'verein_id': self.club.verein_id
            }
            # Add emblem URL if verein_id exists
            if self.club.verein_id:
                # Check if the emblem file exists
                import os
                wappen_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wappen")
                emblem_path = os.path.join(wappen_dir, f"{self.club.verein_id}.png")

                if os.path.exists(emblem_path):
                    club_info['emblem_url'] = f"/api/club-emblem/{self.club.verein_id}"
                    #print(f"DEBUG: Team {self.name} (ID: {self.id}) has club {self.club.name} with verein_id: {self.club.verein_id}, emblem_url: {club_info['emblem_url']}")
                else:
                    print(f"DEBUG: Team {self.name} (ID: {self.id}) has club {self.club.name} with verein_id: {self.club.verein_id}, but no emblem file found at {emblem_path}")
            else:
                print(f"DEBUG: Team {self.name} (ID: {self.id}) has club {self.club.name} with no verein_id")
        else:
            print(f"DEBUG: Team {self.name} (ID: {self.id}) has no club")

        # Get league information
        league_info = None
        if self.league:
            league_info = {
                'id': self.league.id,
                'name': self.league.name,
                'level': self.league.level
            }

        # Get detailed player information for regular team members
        players_info = []
        current_season = Season.query.filter_by(is_current=True).first()

        for player in self.players:
            # Calculate statistics for this player specifically for this team (all-time)
            team_stats = player.calculate_team_specific_stats(self.id)
            # Calculate current season statistics
            current_season_team_stats = player.calculate_team_specific_stats(self.id, current_season.id) if current_season else team_stats

            player_info = {
                'id': player.id,
                'name': player.name,
                'age': player.age,
                'strength': player.strength,
                'talent': player.talent,
                'position': player.position,
                'salary': player.salary,
                'contract_end': player.contract_end.isoformat() if player.contract_end else None,
                'ausdauer': player.ausdauer,
                'konstanz': player.konstanz,
                'drucksicherheit': player.drucksicherheit,
                'volle': player.volle,
                'raeumer': player.raeumer,
                'sicherheit': player.sicherheit,
                'auswaerts': player.auswaerts,
                'start': player.start,
                'mitte': player.mitte,
                'schluss': player.schluss,
                'statistics': team_stats,  # Verwende teamspezifische Statistiken (all-time)
                'current_season_statistics': current_season_team_stats,  # Current season statistics
                'is_substitute': False,  # Regular team member
                'club_id': player.club_id,
                'club_name': player.club.name if player.club else 'Kein Verein'
            }
            players_info.append(player_info)

        # Get detailed player information for substitute players
        substitute_players = self.get_substitute_players()
        for player in substitute_players:
            # Calculate statistics for this player specifically for this team (all-time)
            team_stats = player.calculate_team_specific_stats(self.id)
            # Calculate current season statistics
            current_season_team_stats = player.calculate_team_specific_stats(self.id, current_season.id) if current_season else team_stats

            player_info = {
                'id': player.id,
                'name': player.name,
                'age': player.age,
                'strength': player.strength,
                'talent': player.talent,
                'position': player.position,
                'salary': player.salary,
                'contract_end': player.contract_end.isoformat() if player.contract_end else None,
                'ausdauer': player.ausdauer,
                'konstanz': player.konstanz,
                'drucksicherheit': player.drucksicherheit,
                'volle': player.volle,
                'raeumer': player.raeumer,
                'sicherheit': player.sicherheit,
                'auswaerts': player.auswaerts,
                'start': player.start,
                'mitte': player.mitte,
                'schluss': player.schluss,
                'statistics': team_stats,  # All-time statistics
                'current_season_statistics': current_season_team_stats,  # Current season statistics
                'is_substitute': True,  # Substitute player
                'club_id': player.club_id,
                'club_name': player.club.name if player.club else 'Kein Verein'
            }
            players_info.append(player_info)

        # Calculate average team strength if there are players (only regular team members)
        avg_strength = 0
        regular_players_info = [p for p in players_info if not p['is_substitute']]
        if regular_players_info:
            avg_strength = sum(player['strength'] for player in regular_players_info) / len(regular_players_info)

        # Get recent matches (played matches)
        recent_matches = []
        all_played_matches = []

        # Get current season for filtering
        current_season = Season.query.filter_by(is_current=True).first()
        current_season_id = current_season.id if current_season else None

        # Get home league matches (only from current season)
        home_matches = Match.query.filter_by(home_team_id=self.id, is_played=True, season_id=current_season_id).all()
        for match in home_matches:
            match_data = {
                'id': match.id,
                'date': match.match_date.isoformat() if match.match_date else None,
                'homeTeam': self.name,
                'awayTeam': match.away_team.name,
                'homeScore': match.home_score,
                'awayScore': match.away_score,
                'league': match.league.name,
                'status': 'played',
                'match_type': 'league',
                'match_day': match.match_day or 0
            }
            all_played_matches.append((match_data['date'] or '1900-01-01', match_data))

        # Get away league matches (only from current season)
        away_matches = Match.query.filter_by(away_team_id=self.id, is_played=True, season_id=current_season_id).all()
        for match in away_matches:
            match_data = {
                'id': match.id,
                'date': match.match_date.isoformat() if match.match_date else None,
                'homeTeam': match.home_team.name,
                'awayTeam': self.name,
                'homeScore': match.home_score,
                'awayScore': match.away_score,
                'league': match.league.name,
                'status': 'played',
                'match_type': 'league',
                'match_day': match.match_day or 0
            }
            all_played_matches.append((match_data['date'] or '1900-01-01', match_data))

        # Get home cup matches - use raw SQL to avoid circular dependency
        try:
            from sqlalchemy import text
            # Query cup matches using raw SQL to avoid circular import (only current season)
            home_cup_matches_raw = db.session.execute(
                text("""
                    SELECT cm.id, cm.match_date, cm.home_score, cm.away_score,
                           cm.round_name, cm.cup_match_day, c.name as cup_name, t.name as away_team_name
                    FROM cup_match cm
                    JOIN cup c ON cm.cup_id = c.id
                    LEFT JOIN team t ON cm.away_team_id = t.id
                    WHERE cm.home_team_id = :team_id AND cm.is_played = 1 AND c.season_id = :season_id
                """),
                {"team_id": self.id, "season_id": current_season_id}
            ).fetchall()

            for cup_match_row in home_cup_matches_raw:
                # Handle match_date - could be datetime or string
                match_datetime = cup_match_row.match_date
                if match_datetime:
                    if hasattr(match_datetime, 'isoformat'):
                        date_str = match_datetime.isoformat()
                    else:
                        date_str = str(match_datetime)
                else:
                    date_str = None

                match_data = {
                    'id': get_cup_match_frontend_id(cup_match_row.id),  # Convert to frontend ID
                    'date': date_str,
                    'homeTeam': self.name,
                    'awayTeam': cup_match_row.away_team_name if cup_match_row.away_team_name else 'Freilos',
                    'homeScore': cup_match_row.home_score,
                    'awayScore': cup_match_row.away_score,
                    'league': f"{cup_match_row.cup_name} - {cup_match_row.round_name}",
                    'status': 'played',
                    'match_type': 'cup',
                    'match_day': cup_match_row.cup_match_day or 0
                }
                all_played_matches.append((match_data['date'] or '1900-01-01', match_data))

            # Get away cup matches (only current season)
            away_cup_matches_raw = db.session.execute(
                text("""
                    SELECT cm.id, cm.match_date, cm.home_score, cm.away_score,
                           cm.round_name, cm.cup_match_day, c.name as cup_name, t.name as home_team_name
                    FROM cup_match cm
                    JOIN cup c ON cm.cup_id = c.id
                    JOIN team t ON cm.home_team_id = t.id
                    WHERE cm.away_team_id = :team_id AND cm.is_played = 1 AND c.season_id = :season_id
                """),
                {"team_id": self.id, "season_id": current_season_id}
            ).fetchall()

            for cup_match_row in away_cup_matches_raw:
                # Handle match_date - could be datetime or string
                match_datetime = cup_match_row.match_date
                if match_datetime:
                    if hasattr(match_datetime, 'isoformat'):
                        date_str = match_datetime.isoformat()
                    else:
                        date_str = str(match_datetime)
                else:
                    date_str = None

                match_data = {
                    'id': get_cup_match_frontend_id(cup_match_row.id),  # Convert to frontend ID
                    'date': date_str,
                    'homeTeam': cup_match_row.home_team_name,
                    'awayTeam': self.name,
                    'homeScore': cup_match_row.home_score,
                    'awayScore': cup_match_row.away_score,
                    'league': f"{cup_match_row.cup_name} - {cup_match_row.round_name}",
                    'status': 'played',
                    'match_type': 'cup',
                    'match_day': cup_match_row.cup_match_day or 0
                }
                all_played_matches.append((match_data['date'] or '1900-01-01', match_data))
        except Exception as e:
            print(f"Error loading cup matches for team {self.id}: {e}")
            # Continue without cup matches if there's an error

        # Sort by actual match date (newest first for recent matches)
        all_played_matches.sort(key=lambda x: x[0], reverse=True)
        # Get all recent matches but mark the first 5 as visible by default
        recent_matches = []
        for i, match_tuple in enumerate(all_played_matches):
            match_data = match_tuple[1]
            match_data['visible'] = i < 5  # Only first 5 are visible by default
            recent_matches.append(match_data)

        # Get upcoming matches (unplayed matches)
        upcoming_matches = []
        all_upcoming_matches = []

        # Get home league matches (only from current season)
        home_matches = Match.query.filter_by(home_team_id=self.id, is_played=False, season_id=current_season_id).all()
        for match in home_matches:
            match_data = {
                'id': match.id,
                'date': match.match_date.isoformat() if match.match_date else None,
                'match_date': match.match_date.isoformat() if match.match_date else None,
                'homeTeam': self.name,
                'awayTeam': match.away_team.name,
                'opponent_name': match.away_team.name,
                'is_home': True,
                'league': match.league.name,
                'status': 'upcoming',
                'match_type': 'league',
                'match_day': match.match_day or 0
            }
            all_upcoming_matches.append((match_data['date'] or '9999-12-31', match_data))

        # Get away league matches (only from current season)
        away_matches = Match.query.filter_by(away_team_id=self.id, is_played=False, season_id=current_season_id).all()
        for match in away_matches:
            match_data = {
                'id': match.id,
                'date': match.match_date.isoformat() if match.match_date else None,
                'match_date': match.match_date.isoformat() if match.match_date else None,
                'homeTeam': match.home_team.name,
                'awayTeam': self.name,
                'opponent_name': match.home_team.name,
                'is_home': False,
                'league': match.league.name,
                'status': 'upcoming',
                'match_type': 'league',
                'match_day': match.match_day or 0
            }
            all_upcoming_matches.append((match_data['date'] or '9999-12-31', match_data))

        # Get upcoming cup matches - use raw SQL to avoid circular import
        try:
            # Query upcoming home cup matches (only current season)
            home_cup_matches_raw = db.session.execute(
                text("""
                    SELECT cm.id, cm.match_date, cm.round_name, cm.cup_match_day, c.name as cup_name, t.name as away_team_name
                    FROM cup_match cm
                    JOIN cup c ON cm.cup_id = c.id
                    LEFT JOIN team t ON cm.away_team_id = t.id
                    WHERE cm.home_team_id = :team_id AND cm.is_played = 0 AND c.season_id = :season_id
                """),
                {"team_id": self.id, "season_id": current_season_id}
            ).fetchall()

            for cup_match_row in home_cup_matches_raw:
                # Handle match_date - could be datetime or string
                match_datetime = cup_match_row.match_date
                if match_datetime:
                    if hasattr(match_datetime, 'isoformat'):
                        date_str = match_datetime.isoformat()
                    else:
                        date_str = str(match_datetime)
                else:
                    date_str = None

                match_data = {
                    'id': get_cup_match_frontend_id(cup_match_row.id),  # Convert to frontend ID
                    'date': date_str,
                    'match_date': date_str,
                    'homeTeam': self.name,
                    'awayTeam': cup_match_row.away_team_name if cup_match_row.away_team_name else 'Freilos',
                    'opponent_name': cup_match_row.away_team_name if cup_match_row.away_team_name else 'Freilos',
                    'is_home': True,
                    'league': f"{cup_match_row.cup_name} - {cup_match_row.round_name}",
                    'status': 'upcoming',
                    'match_type': 'cup',
                    'match_day': cup_match_row.cup_match_day or 0
                }
                all_upcoming_matches.append((match_data['date'] or '9999-12-31', match_data))

            # Query upcoming away cup matches (only current season)
            away_cup_matches_raw = db.session.execute(
                text("""
                    SELECT cm.id, cm.match_date, cm.round_name, cm.cup_match_day, c.name as cup_name, t.name as home_team_name
                    FROM cup_match cm
                    JOIN cup c ON cm.cup_id = c.id
                    JOIN team t ON cm.home_team_id = t.id
                    WHERE cm.away_team_id = :team_id AND cm.is_played = 0 AND c.season_id = :season_id
                """),
                {"team_id": self.id, "season_id": current_season_id}
            ).fetchall()

            for cup_match_row in away_cup_matches_raw:
                # Handle match_date - could be datetime or string
                match_datetime = cup_match_row.match_date
                if match_datetime:
                    if hasattr(match_datetime, 'isoformat'):
                        date_str = match_datetime.isoformat()
                    else:
                        date_str = str(match_datetime)
                else:
                    date_str = None

                match_data = {
                    'id': get_cup_match_frontend_id(cup_match_row.id),  # Convert to frontend ID
                    'date': date_str,
                    'match_date': date_str,
                    'homeTeam': cup_match_row.home_team_name,
                    'awayTeam': self.name,
                    'opponent_name': cup_match_row.home_team_name,
                    'is_home': False,
                    'league': f"{cup_match_row.cup_name} - {cup_match_row.round_name}",
                    'status': 'upcoming',
                    'match_type': 'cup',
                    'match_day': cup_match_row.cup_match_day or 0
                }
                all_upcoming_matches.append((match_data['date'] or '9999-12-31', match_data))
        except Exception as e:
            print(f"Error loading upcoming cup matches for team {self.id}: {e}")
            # Continue without cup matches if there's an error

        # Sort by actual match date (earliest first for upcoming matches)
        all_upcoming_matches.sort(key=lambda x: x[0])
        # Get all upcoming matches but mark the first 5 as visible by default
        upcoming_matches = []
        for i, match_tuple in enumerate(all_upcoming_matches):
            match_data = match_tuple[1]
            match_data['visible'] = i < 5  # Only first 5 are visible by default
            upcoming_matches.append(match_data)

        # Calculate team statistics (all-time)
        stats = self.calculate_stats()

        # Calculate current season statistics
        current_season = Season.query.filter_by(is_current=True).first()
        current_season_stats = self.calculate_stats(current_season.id) if current_season else stats

        return {
            'id': self.id,
            'name': self.name,
            'club_id': self.club_id,
            'league_id': self.league_id,
            'is_youth_team': self.is_youth_team,
            'staerke': self.staerke,  # Include the team's strength value
            'club': club_info,
            'league': league_info,
            'players': players_info,
            'player_ids': [player.id for player in self.players],
            'avg_strength': round(avg_strength, 1),
            'recentMatches': recent_matches,
            'upcomingMatches': upcoming_matches,
            'stats': stats,
            'current_season_stats': current_season_stats
        }

    def calculate_stats(self, season_id=None):
        """Calculate team statistics based on played matches.

        Args:
            season_id: If provided, calculate stats only for this season.
                      If None, calculate stats for all seasons.
        """
        # Get all matches for this team
        if season_id:
            home_matches = Match.query.filter_by(home_team_id=self.id, is_played=True, season_id=season_id).all()
            away_matches = Match.query.filter_by(away_team_id=self.id, is_played=True, season_id=season_id).all()
        else:
            home_matches = Match.query.filter_by(home_team_id=self.id, is_played=True).all()
            away_matches = Match.query.filter_by(away_team_id=self.id, is_played=True).all()

        matches = 0
        wins = 0
        draws = 0
        losses = 0
        points = 0
        goals_for = 0
        goals_against = 0

        # Neue Statistiken für Heim- und Auswärtsergebnisse
        home_matches_count = len(home_matches)
        away_matches_count = len(away_matches)
        home_goals_for = 0
        home_goals_against = 0
        away_goals_for = 0
        away_goals_against = 0

        # Calculate stats from home matches
        for match in home_matches:
            matches += 1
            goals_for += match.home_score
            goals_against += match.away_score

            # Für Heimstatistik
            home_goals_for += match.home_score
            home_goals_against += match.away_score

            if match.home_score > match.away_score:
                wins += 1
                points += 3
            elif match.home_score == match.away_score:
                draws += 1
                points += 1
            else:
                losses += 1

        # Calculate stats from away matches
        for match in away_matches:
            matches += 1
            goals_for += match.away_score
            goals_against += match.home_score

            # Für Auswärtsstatistik
            away_goals_for += match.away_score
            away_goals_against += match.home_score

            if match.away_score > match.home_score:
                wins += 1
                points += 3
            elif match.away_score == match.home_score:
                draws += 1
                points += 1
            else:
                losses += 1

        # Berechne Durchschnittswerte
        avg_home_score = home_goals_for / home_matches_count if home_matches_count > 0 else 0
        avg_away_score = away_goals_for / away_matches_count if away_matches_count > 0 else 0

        return {
            'matches': matches,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'points': points,
            'goalsFor': goals_for,
            'goalsAgainst': goals_against,
            'goalDifference': goals_for - goals_against,
            'homeMatches': home_matches_count,
            'awayMatches': away_matches_count,
            'homeGoalsFor': home_goals_for,
            'homeGoalsAgainst': home_goals_against,
            'awayGoalsFor': away_goals_for,
            'awayGoalsAgainst': away_goals_against,
            'avgHomeScore': avg_home_score,
            'avgAwayScore': avg_away_score
        }

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    founded = db.Column(db.Integer)
    reputation = db.Column(db.Integer, default=50)  # 1-100
    verein_id = db.Column(db.Integer)

    # Neue Felder
    fans = db.Column(db.Integer, default=1000)  # Anzahl der Fans
    training_facilities = db.Column(db.Integer, default=50)  # Qualität der Trainingseinrichtungen (1-100)
    coaching = db.Column(db.Integer, default=50)  # Qualität der Trainer (1-100)
    logo_path = db.Column(db.String(255))  # Pfad zum Vereinswappen
    lane_quality = db.Column(db.Float, default=1.0)  # Qualität der Kegelbahn (0.9-1.05)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teams = db.relationship('Team', back_populates='club')
    players = db.relationship('Player', back_populates='club')
    finances = db.relationship('Finance', back_populates='club')

    def get_best_league_level(self):
        """Get the best (lowest) league level of all teams belonging to this club."""
        if not self.teams:
            return None

        # Get all league levels of teams belonging to this club
        league_levels = []
        for team in self.teams:
            if team.league and team.league.level:
                league_levels.append(team.league.level)

        if not league_levels:
            return None

        # Return the best (lowest) league level
        return min(league_levels)

    def to_dict(self):
        # Create emblem URL based on verein_id
        emblem_url = None
        if self.verein_id:
            # Check if the emblem file exists
            import os
            wappen_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wappen")
            emblem_path = os.path.join(wappen_dir, f"{self.verein_id}.png")

            if os.path.exists(emblem_path):
                emblem_url = f"/api/club-emblem/{self.verein_id}"
            else:
                print(f"DEBUG: Club {self.name} (ID: {self.id}) has verein_id: {self.verein_id}, but no emblem file found at {emblem_path}")
        else:
            print(f"DEBUG: Club {self.name} (ID: {self.id}) has no verein_id")

        # Create detailed team information
        teams_info = []
        for team in self.teams:
            team_info = {
                'id': team.id,
                'name': team.name,
                'is_youth_team': team.is_youth_team,
                'league_id': team.league_id,
                'league': team.league.name if team.league else 'Keine Liga',
                'position': 0  # In a real application, this would come from the database
            }

            # Add emblem URL to each team
            if self.verein_id and emblem_url:
                team_info['emblem_url'] = emblem_url

            teams_info.append(team_info)

        # Get detailed player information
        players_info = []
        for player in self.players:
            player_info = {
                'id': player.id,
                'name': player.name,
                'age': player.age,
                'strength': player.strength,
                'talent': player.talent,
                'position': player.position,
                'salary': player.salary,
                'contract_end': player.contract_end.isoformat() if player.contract_end else None,
                'ausdauer': player.ausdauer,
                'konstanz': player.konstanz,
                'drucksicherheit': player.drucksicherheit,
                'volle': player.volle,
                'raeumer': player.raeumer,
                'sicherheit': player.sicherheit,
                'auswaerts': player.auswaerts,
                'start': player.start,
                'mitte': player.mitte,
                'schluss': player.schluss
            }
            players_info.append(player_info)

        # Get lane records for this club
        lane_records = {
            'team': [],
            'individual': {
                'Herren': [],
                'U19': [],
                'U14': []
            }
        }

        # Get team records
        team_records = LaneRecord.query.filter_by(
            club_id=self.id,
            record_type='team'
        ).all()

        for record in team_records:
            lane_records['team'].append(record.to_dict())

        # Get individual records by category
        for category in ['Herren', 'U19', 'U14']:
            individual_records = LaneRecord.query.filter_by(
                club_id=self.id,
                record_type='individual',
                category=category
            ).all()

            for record in individual_records:
                lane_records['individual'][category].append(record.to_dict())

        return {
            'id': self.id,
            'verein_id': self.verein_id,
            'name': self.name,
            'founded': self.founded,
            'reputation': self.reputation,
            'fans': self.fans,
            'training_facilities': self.training_facilities,
            'coaching': self.coaching,
            'logo_path': self.logo_path,
            'lane_quality': self.lane_quality,
            'emblem_url': emblem_url,
            'teams': [team.id for team in self.teams],
            'teams_info': teams_info,
            'players': players_info,
            'player_ids': [player.id for player in self.players],
            'lane_records': lane_records
        }

class League(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1 is top level
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'))

    # Neue Felder für Bundesland und Landkreis
    bundesland = db.Column(db.String(50))
    landkreis = db.Column(db.String(100))

    # Neue Felder für Altersklasse
    altersklasse = db.Column(db.String(50))  # z.B. "Herren", "Damen", "U23", "U19", etc.

    # Neue Felder für Auf- und Abstieg (können mehrere IDs enthalten, getrennt durch Semikolon)
    aufstieg_liga_id = db.Column(db.String(255))  # Liga(s), in die Aufsteiger gehen (mehrere IDs getrennt durch Semikolon)
    abstieg_liga_id = db.Column(db.String(255))  # Liga(s), in die Absteiger gehen (mehrere IDs getrennt durch Semikolon)

    # Anzahl der Auf- und Abstiegsplätze
    anzahl_aufsteiger = db.Column(db.Integer, default=2)
    anzahl_absteiger = db.Column(db.Integer, default=2)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teams = db.relationship('Team', back_populates='league')
    season = db.relationship('Season', back_populates='leagues')
    matches = db.relationship('Match', back_populates='league')

    # Self-referential relationships für Auf- und Abstieg
    # NOTE: Relationships disabled because aufstieg_liga_id and abstieg_liga_id now contain multiple IDs as strings
    # aufstieg_liga = db.relationship('League', remote_side=[id], foreign_keys=[aufstieg_liga_id], backref=db.backref('abstiegs_ligen', lazy='dynamic'))
    # abstieg_liga = db.relationship('League', remote_side=[id], foreign_keys=[abstieg_liga_id], backref=db.backref('aufstiegs_ligen', lazy='dynamic'))

    def get_aufstieg_liga_ids(self):
        """Get list of promotion league IDs from semicolon-separated string."""
        if not self.aufstieg_liga_id:
            return []
        ids = []
        for id_str in self.aufstieg_liga_id.split(';'):
            id_str = id_str.strip()
            if id_str:
                try:
                    # Convert float strings (like "1.0") to int
                    ids.append(int(float(id_str)))
                except (ValueError, TypeError):
                    print(f"WARNING: Could not convert '{id_str}' to integer in aufstieg_liga_id")
        return ids

    def get_abstieg_liga_ids(self):
        """Get list of relegation league IDs from semicolon-separated string."""
        if not self.abstieg_liga_id:
            return []
        ids = []
        for id_str in self.abstieg_liga_id.split(';'):
            id_str = id_str.strip()
            if id_str:
                try:
                    # Convert float strings (like "1.0") to int
                    ids.append(int(float(id_str)))
                except (ValueError, TypeError):
                    print(f"WARNING: Could not convert '{id_str}' to integer in abstieg_liga_id")
        return ids

    def get_aufstieg_ligen(self):
        """Get list of promotion league objects."""
        ids = self.get_aufstieg_liga_ids()
        if not ids:
            return []
        return League.query.filter(League.id.in_(ids)).all()

    def get_abstieg_ligen(self):
        """Get list of relegation league objects."""
        ids = self.get_abstieg_liga_ids()
        if not ids:
            return []
        return League.query.filter(League.id.in_(ids)).all()

    def get_fixtures(self):
        """Get all matches for this league organized by match day."""
        # Get all matches for this league
        matches = Match.query.filter_by(league_id=self.id).order_by(Match.match_day, Match.id).all()

        # Group matches by match day
        fixtures = {}
        for match in matches:
            if match.match_day is None:
                continue

            if match.match_day not in fixtures:
                fixtures[match.match_day] = []

            # Create match data with team names
            match_data = {
                'id': match.id,
                'home_team': match.home_team.name,
                'away_team': match.away_team.name,
                'home_team_id': match.home_team_id,
                'away_team_id': match.away_team_id,
                'date': match.match_date.isoformat() if match.match_date else None,
                'played': match.is_played,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'round': match.round
            }

            # Add club emblems if available
            if match.home_team.club and match.home_team.club.verein_id:
                match_data['home_emblem_url'] = f"/api/club-emblem/{match.home_team.club.verein_id}"
            if match.away_team.club and match.away_team.club.verein_id:
                match_data['away_emblem_url'] = f"/api/club-emblem/{match.away_team.club.verein_id}"

            fixtures[match.match_day].append(match_data)

        # Convert to list format for frontend
        fixtures_list = []
        for match_day, matches in sorted(fixtures.items()):
            fixtures_list.append({
                'match_day': match_day,
                'matches': matches
            })

        return fixtures_list

    def get_player_statistics(self):
        """Get statistics for all players who played in this league."""
        # Get all matches played in this league
        matches = Match.query.filter_by(league_id=self.id, is_played=True).all()

        if not matches:
            return []

        # Get all player performances from these matches
        match_ids = [match.id for match in matches]
        performances = PlayerMatchPerformance.query.filter(PlayerMatchPerformance.match_id.in_(match_ids)).all()

        # Group performances by player
        player_performances = {}
        for perf in performances:
            if perf.player_id not in player_performances:
                player_performances[perf.player_id] = []
            player_performances[perf.player_id].append(perf)

        # Calculate statistics for each player
        player_stats = []
        for player_id, perfs in player_performances.items():
            player = Player.query.get(player_id)
            if not player:
                continue

            # Get team name
            team = Team.query.get(perfs[0].team_id)
            team_name = team.name if team else "Unknown"

            # Calculate statistics
            total_matches = len(perfs)
            total_score = sum(p.total_score for p in perfs)
            avg_score = total_score / total_matches if total_matches > 0 else 0

            # Calculate Volle and Räumer averages
            total_volle = sum(p.volle_score for p in perfs if p.volle_score is not None)
            total_raeumer = sum(p.raeumer_score for p in perfs if p.raeumer_score is not None)
            avg_volle = total_volle / total_matches if total_matches > 0 else 0
            avg_raeumer = total_raeumer / total_matches if total_matches > 0 else 0

            # Calculate error average
            total_fehler = sum(p.fehler_count for p in perfs if p.fehler_count is not None)
            avg_fehler = total_fehler / total_matches if total_matches > 0 else 0

            # Calculate home/away averages
            home_perfs = [p for p in perfs if p.is_home_team]
            away_perfs = [p for p in perfs if not p.is_home_team]

            home_matches = len(home_perfs)
            away_matches = len(away_perfs)

            home_score = sum(p.total_score for p in home_perfs)
            away_score = sum(p.total_score for p in away_perfs)

            avg_home_score = home_score / home_matches if home_matches > 0 else 0
            avg_away_score = away_score / away_matches if away_matches > 0 else 0

            # Calculate match points won percentage
            mp_won = sum(1 for p in perfs if p.match_points > 0)
            mp_win_percentage = (mp_won / total_matches * 100) if total_matches > 0 else 0

            player_stats.append({
                'player_id': player_id,
                'player_name': player.name,
                'team_id': team.id if team else None,
                'team_name': team_name,
                'matches': total_matches,
                'avg_score': round(avg_score, 1),
                'avg_volle': round(avg_volle, 1),
                'avg_raeumer': round(avg_raeumer, 1),
                'avg_fehler': round(avg_fehler, 1),
                'avg_home_score': round(avg_home_score, 1),
                'avg_away_score': round(avg_away_score, 1),
                'mp_win_percentage': round(mp_win_percentage, 1)
            })

        return player_stats

    def to_dict(self):
        # Erstelle eine Liste mit detaillierten Team-Informationen
        teams_info = []
        for team in self.teams:
            team_info = {
                'id': team.id,
                'name': team.name,
                'club_id': team.club_id,
                'is_youth_team': team.is_youth_team
            }

            # Füge Club-Informationen hinzu, wenn verfügbar
            if team.club:
                team_info['club_name'] = team.club.name
                if team.club.verein_id:
                    team_info['emblem_url'] = f"/api/club-emblem/{team.club.verein_id}"

            teams_info.append(team_info)

        # Calculate standings for the league
        import simulation
        standings_data = simulation.calculate_standings(self)

        # Check if any matches have been played in this league
        played_matches_count = Match.query.filter_by(league_id=self.id, is_played=True).count()

        # Convert standings to a format suitable for the frontend
        standings = []
        for i, standing in enumerate(standings_data):
            team = standing['team']

            # Berechne Durchschnittswerte für Heim- und Auswärtsergebnisse
            team_stats = team.calculate_stats()

            # If no matches have been played, use 0 for avg_home_score and avg_away_score
            avg_home_score = round(team_stats['avgHomeScore'], 1) if played_matches_count > 0 else 0
            avg_away_score = round(team_stats['avgAwayScore'], 1) if played_matches_count > 0 else 0

            # Determine team display name with status suffix
            team_display_name = team.name
            if team.previous_season_status == 'promoted':
                team_display_name += ' (Au)'
            elif team.previous_season_status == 'relegated':
                team_display_name += ' (Ab)'
            elif team.previous_season_status == 'champion':
                team_display_name += ' (Me)'

            standings.append({
                'position': i + 1,
                'team_id': team.id,
                'team': team_display_name,
                'team_name_base': team.name,  # Original name without suffix
                'club_name': team.club.name if team.club else 'Unbekannt',
                'emblem_url': f"/api/club-emblem/{team.club.verein_id}" if team.club and team.club.verein_id else None,
                'played': standing['wins'] + standing['draws'] + standing['losses'],
                'won': standing['wins'],
                'drawn': standing['draws'],
                'lost': standing['losses'],
                'points': standing['points'],
                'goals_for': standing['goals_for'],
                'goals_against': standing['goals_against'],
                'goal_difference': standing['goal_difference'],
                'avg_home_score': avg_home_score,
                'avg_away_score': avg_away_score,
                'previous_season_status': team.previous_season_status
            })

        # Get fixtures (match schedule)
        fixtures = self.get_fixtures()

        # Get player statistics
        player_stats = self.get_player_statistics()

        return {
            'id': self.id,
            'name': self.name,
            'level': self.level,
            'season_id': self.season_id,
            'bundesland': self.bundesland,
            'landkreis': self.landkreis,
            'altersklasse': self.altersklasse,
            'aufstieg_liga_id': self.aufstieg_liga_id,
            'abstieg_liga_id': self.abstieg_liga_id,
            'anzahl_aufsteiger': self.anzahl_aufsteiger,
            'anzahl_absteiger': self.anzahl_absteiger,
            'teams': [team.id for team in self.teams],
            'teams_info': teams_info,
            'standings': standings,
            'fixtures': fixtures,
            'player_statistics': player_stats,
            'stats': {
                'topScorers': [],
                'teamStats': []
            }
        }

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False, index=True)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False, index=True)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'), nullable=False, index=True)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False, index=True)
    match_date = db.Column(db.DateTime)
    home_score = db.Column(db.Integer)  # Gesamtholz Heimteam
    away_score = db.Column(db.Integer)  # Gesamtholz Auswärtsteam
    home_match_points = db.Column(db.Integer, default=0)  # Mannschaftspunkte (MP) Heimteam
    away_match_points = db.Column(db.Integer, default=0)  # Mannschaftspunkte (MP) Auswärtsteam
    is_played = db.Column(db.Boolean, default=False, index=True)
    match_day = db.Column(db.Integer, index=True)  # Spieltag (1, 2, 3, ...)
    round = db.Column(db.Integer, default=1)  # 1 = Hinrunde, 2 = Rückrunde
    stroh_performances = db.Column(db.Text)  # JSON string for Stroh player performances
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    home_team = db.relationship('Team', foreign_keys=[home_team_id], back_populates='home_matches')
    away_team = db.relationship('Team', foreign_keys=[away_team_id], back_populates='away_matches')
    league = db.relationship('League', back_populates='matches')
    season = db.relationship('Season', back_populates='matches')
    performances = db.relationship('PlayerMatchPerformance', back_populates='match')

    def to_dict(self):
        # Get verein_id for home and away teams
        home_team_verein_id = None
        away_team_verein_id = None

        if self.home_team and self.home_team.club:
            home_team_verein_id = self.home_team.club.verein_id

        if self.away_team and self.away_team.club:
            away_team_verein_id = self.away_team.club.verein_id

        return {
            'id': self.id,
            'home_team_id': self.home_team_id,
            'away_team_id': self.away_team_id,
            'home_team_name': self.home_team.name,
            'away_team_name': self.away_team.name,
            'home_team_club_id': self.home_team.club_id,
            'away_team_club_id': self.away_team.club_id,
            'home_team_verein_id': home_team_verein_id,
            'away_team_verein_id': away_team_verein_id,
            'league_id': self.league_id,
            'league_name': self.league.name,
            'season_id': self.season_id,
            'match_date': self.match_date.isoformat() if self.match_date else None,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'home_match_points': self.home_match_points,
            'away_match_points': self.away_match_points,
            'is_played': self.is_played,
            'match_day': self.match_day,
            'round': self.round,
            'performances': self._get_all_performances()
        }

    def _get_all_performances(self):
        """Get all performances including Stroh players."""
        performances = [perf.to_dict() for perf in self.performances] if self.is_played else []

        # Add Stroh performances if they exist
        if self.stroh_performances:
            import json
            try:
                stroh_perfs = json.loads(self.stroh_performances)
                performances.extend(stroh_perfs)
            except (json.JSONDecodeError, TypeError):
                pass  # Ignore invalid JSON

        return performances

class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    leagues = db.relationship('League', back_populates='season')
    matches = db.relationship('Match', back_populates='season')
    calendar_days = db.relationship('SeasonCalendar', back_populates='season')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_current': self.is_current
        }


class SeasonCalendar(db.Model):
    """
    Kalender für eine Saison mit 104 Spielmöglichkeiten (52 Samstage + 52 Mittwoche).
    Verwaltet die Verteilung von Liga-, Pokal- und spielfreien Tagen.
    """
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False, index=True)
    week_number = db.Column(db.Integer, nullable=False)  # 1-52
    calendar_date = db.Column(db.Date, nullable=False)  # Datum des Spieltags (Samstag oder Mittwoch)
    weekday = db.Column(db.String(10), nullable=False)  # 'Saturday' oder 'Wednesday'
    day_type = db.Column(db.String(20), nullable=False)  # 'FREE_DAY', 'LEAGUE_DAY', 'CUP_DAY'
    match_day_number = db.Column(db.Integer, nullable=True)  # Spieltag-Nummer (Liga oder Pokal)
    is_simulated = db.Column(db.Boolean, default=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    season = db.relationship('Season', back_populates='calendar_days')

    def to_dict(self):
        return {
            'id': self.id,
            'season_id': self.season_id,
            'week_number': self.week_number,
            'calendar_date': self.calendar_date.isoformat(),
            'weekday': self.weekday,
            'day_type': self.day_type,
            'match_day_number': self.match_day_number,
            'is_simulated': self.is_simulated
        }

class Cup(db.Model):
    """Pokalwettbewerbe: DKBC-Pokal, Landespokal, Kreispokal."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # z.B. "DKBC-Pokal", "Sachsen-Anhalt-Pokal", "Landkreis Harz-Pokal"
    cup_type = db.Column(db.String(20), nullable=False)  # "DKBC", "Landespokal", "Kreispokal"
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)

    # Geografische Zuordnung
    bundesland = db.Column(db.String(50))  # Nur für Landespokal und Kreispokal
    landkreis = db.Column(db.String(100))  # Nur für Kreispokal

    # Status
    is_active = db.Column(db.Boolean, default=True)
    current_round = db.Column(db.String(50), default="1. Runde")  # "1. Runde", "Achtelfinale", "Viertelfinale", etc.
    total_rounds = db.Column(db.Integer, default=1)  # Gesamtanzahl der Runden
    current_round_number = db.Column(db.Integer, default=1)  # Aktuelle Rundennummer

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    season = db.relationship('Season', backref='cups')
    cup_matches = db.relationship('CupMatch', back_populates='cup', cascade='all, delete-orphan')

    def get_eligible_teams(self):
        """Ermittelt alle teilnahmeberechtigten Teams für diesen Pokal."""
        from sqlalchemy import and_, or_

        if self.cup_type == "DKBC":
            # Teams aus Ligen ohne Bundesland und Landkreis
            eligible_teams = Team.query.join(League).filter(
                and_(
                    League.season_id == self.season_id,
                    or_(League.bundesland.is_(None), League.bundesland == ''),
                    or_(League.landkreis.is_(None), League.landkreis == '')
                )
            ).all()
        elif self.cup_type == "Landespokal":
            # Teams aus Ligen mit Bundesland aber ohne Landkreis
            eligible_teams = Team.query.join(League).filter(
                and_(
                    League.season_id == self.season_id,
                    League.bundesland == self.bundesland,
                    or_(League.landkreis.is_(None), League.landkreis == '')
                )
            ).all()
        elif self.cup_type == "Kreispokal":
            # Teams aus Ligen mit Landkreis
            eligible_teams = Team.query.join(League).filter(
                and_(
                    League.season_id == self.season_id,
                    League.landkreis == self.landkreis
                )
            ).all()
        else:
            eligible_teams = []

        return eligible_teams

    def calculate_total_rounds(self, num_teams):
        """Berechnet die Gesamtanzahl der Runden basierend auf der Anzahl der Teams."""
        import math
        if num_teams <= 1:
            return 1
        return math.ceil(math.log2(num_teams))

    def get_round_name(self, round_number, total_rounds):
        """Gibt den Namen der Runde basierend auf der Rundennummer zurück."""
        # Berechne wie viele Teams in dieser Runde noch übrig sind
        # In Runde 1 sind es die ursprünglichen Teams
        # In Runde 2 sind es die Hälfte, usw.
        teams_in_round = 2 ** (total_rounds - round_number + 1)

        if teams_in_round == 2:
            return "Finale"
        elif teams_in_round == 4:
            return "Halbfinale"
        elif teams_in_round == 8:
            return "Viertelfinale"
        elif teams_in_round == 16:
            return "Achtelfinale"
        elif teams_in_round == 32:
            return "Sechzehntelfinale"
        else:
            return f"{round_number}. Runde"

    def generate_cup_fixtures(self):
        """Generiert die Pokalspiele für alle Runden mit korrekter Freilos-Logik."""
        import random
        import math

        eligible_teams = self.get_eligible_teams()
        if len(eligible_teams) < 2:
            return

        # Berechne die nächsthöhere 2er-Potenz für die zweite Runde
        next_power_of_2 = 2 ** math.ceil(math.log2(len(eligible_teams)))

        # Berechne die Gesamtanzahl der Runden basierend auf der nächsthöheren 2er-Potenz
        total_rounds = int(math.log2(next_power_of_2))
        self.total_rounds = total_rounds

        # Mische die Teams zufällig
        teams = eligible_teams.copy()
        random.shuffle(teams)

        # Berechne Anzahl der Freilose und Spiele in der ersten Runde
        num_byes = next_power_of_2 - len(eligible_teams)
        num_first_round_matches = (len(eligible_teams) - num_byes) // 2

        print(f"Cup {self.name}: {len(eligible_teams)} Teams, {num_byes} Freilose, {num_first_round_matches} Spiele in Runde 1")

        # Teams für die erste Runde (die spielen müssen)
        teams_to_play = teams[:num_first_round_matches * 2]

        # Teams mit Freilosen (kommen direkt in die zweite Runde)
        teams_with_byes = teams[num_first_round_matches * 2:]

        # Erstelle Spiele für die erste Runde
        for i in range(0, len(teams_to_play), 2):
            if i + 1 < len(teams_to_play):
                home_team = teams_to_play[i]
                away_team = teams_to_play[i + 1]

                cup_match_day = self.calculate_cup_match_day(1, total_rounds)
                print(f"POKAL: Creating match {home_team.name} vs {away_team.name} for match day {cup_match_day}")

                cup_match = CupMatch(
                    cup_id=self.id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    round_name=self.get_round_name(1, total_rounds),
                    round_number=1,
                    cup_match_day=cup_match_day
                )
                db.session.add(cup_match)

        # Speichere Teams mit Freilosen für die nächste Runde
        # Diese werden in advance_to_next_round() berücksichtigt
        for team in teams_with_byes:
            # Erstelle einen "Dummy"-Match für Teams mit Freilosen
            # Diese werden als bereits "gewonnen" markiert
            cup_match_day = self.calculate_cup_match_day(1, total_rounds)
            print(f"POKAL: Creating bye match for {team.name} for match day {cup_match_day}")

            bye_match = CupMatch(
                cup_id=self.id,
                home_team_id=team.id,
                away_team_id=None,  # Kein Gegner = Freilos
                round_name=self.get_round_name(1, total_rounds),
                round_number=1,
                cup_match_day=cup_match_day,
                is_played=True,  # Freilos ist automatisch "gespielt"
                winner_team_id=team.id,  # Team gewinnt automatisch
                home_score=0,
                away_score=0
            )
            db.session.add(bye_match)

        # Aktualisiere Cup-Status
        self.current_round = self.get_round_name(1, total_rounds)
        self.current_round_number = 1

        db.session.commit()

    def calculate_cup_match_day(self, round_number, total_rounds):
        """Berechnet den Pokalspieltag basierend auf der Rundennummer und verfügbaren CUP_DAYs."""
        from sqlalchemy import func

        # Hole alle verfügbaren CUP_DAYs aus dem Saisonkalender
        cup_days = db.session.query(SeasonCalendar.match_day_number).filter_by(
            season_id=self.season_id,
            day_type='CUP_DAY'
        ).order_by(SeasonCalendar.id).all()

        if not cup_days:
            print(f"POKAL: Cup {self.name} - No CUP_DAYs found in calendar, using fallback")
            # Fallback: Verwende einfache Berechnung
            return round_number

        available_cup_days = [day[0] for day in cup_days if day[0] is not None]
        print(f"POKAL: Cup {self.name} - Available cup days: {available_cup_days}")

        if not available_cup_days:
            print(f"POKAL: Cup {self.name} - No valid cup days found, using fallback")
            return round_number

        # Berechne einen Offset basierend auf dem Pokal-Typ und der ID
        # um verschiedene Pokale auf verschiedene CUP_DAYs zu verteilen
        cup_offset = 0
        if self.cup_type == "DKBC":
            cup_offset = 0  # DKBC-Pokal startet bei den ersten CUP_DAYs
        elif self.cup_type == "Landespokal":
            cup_offset = 1  # Landespokal startet einen CUP_DAY später
        elif self.cup_type == "Kreispokal":
            cup_offset = 2  # Kreispokal startet zwei CUP_DAYs später

        # Zusätzlicher Offset basierend auf der Cup-ID für mehrere Pokale desselben Typs
        additional_offset = (self.id % 3) * 3  # Verteile mehrere Pokale desselben Typs

        total_offset = cup_offset + additional_offset

        # Verwende die verfügbaren CUP_DAYs für die Verteilung
        if total_rounds == 1:
            # Bei nur einer Runde, verwende den entsprechenden CUP_DAY basierend auf dem Offset
            day_index = total_offset % len(available_cup_days)
            cup_match_day = available_cup_days[day_index]
            print(f"POKAL: Cup {self.name} - Single round, using cup day {cup_match_day} (offset: {total_offset})")
            return cup_match_day

        # Bei mehreren Runden, verteile gleichmäßig über die verfügbaren CUP_DAYs
        day_index = (round_number - 1 + total_offset) % len(available_cup_days)
        cup_match_day = available_cup_days[day_index]
        print(f"POKAL: Cup {self.name} - Round {round_number}/{total_rounds}, using cup day {cup_match_day} (offset: {total_offset})")

        return cup_match_day

    def advance_to_next_round(self):
        """Lässt Teams zur nächsten Runde aufsteigen basierend auf den Ergebnissen."""
        print(f"DEBUG: Checking advancement for Cup {self.name}, current round {self.current_round_number}")

        current_round_matches = CupMatch.query.filter_by(
            cup_id=self.id,
            round_number=self.current_round_number,
            is_played=True
        ).all()

        # Prüfe, ob alle Spiele der aktuellen Runde gespielt wurden
        total_current_round_matches = CupMatch.query.filter_by(
            cup_id=self.id,
            round_number=self.current_round_number
        ).count()

        print(f"DEBUG: Cup {self.name} - Played matches: {len(current_round_matches)}, Total matches: {total_current_round_matches}")

        if len(current_round_matches) < total_current_round_matches:
            print(f"DEBUG: Cup {self.name} - Not all matches played yet, cannot advance")
            return False  # Noch nicht alle Spiele gespielt

        # Wenn wir im Finale sind, ist der Pokal beendet
        if self.current_round_number >= self.total_rounds:
            print(f"DEBUG: Cup {self.name} - Final round completed, cup finished")
            self.is_active = False
            db.session.commit()
            return True

        # Sammle alle Gewinner für die nächste Runde (inklusive Freilose)
        winners = []
        matches_without_winner = []
        for match in current_round_matches:
            if match.winner_team_id:
                winners.append(Team.query.get(match.winner_team_id))
            else:
                matches_without_winner.append(match.id)

        print(f"DEBUG: Cup {self.name}: {len(winners)} Gewinner aus Runde {self.current_round_number}")
        if matches_without_winner:
            print(f"DEBUG: Cup {self.name}: Matches without winner: {matches_without_winner}")

        # Alle Teams für die nächste Runde sind die Gewinner
        # (Freilose wurden bereits in der ersten Runde als "gewonnene" Matches erstellt)
        all_next_round_teams = winners

        # Prüfe, ob wir eine 2er-Potenz haben (sollte nach der ersten Runde immer der Fall sein)
        if len(all_next_round_teams) % 2 != 0:
            print(f"WARNUNG: Ungerade Anzahl Teams ({len(all_next_round_teams)}) in Runde {self.current_round_number + 1}")
            # Entferne das letzte Team (bekommt Freilos)
            all_next_round_teams = all_next_round_teams[:-1]

        if len(all_next_round_teams) == 0:
            print(f"ERROR: Cup {self.name} - No teams for next round!")
            return False

        # Erstelle Spiele für die nächste Runde
        next_round_number = self.current_round_number + 1
        next_round_name = self.get_round_name(next_round_number, self.total_rounds)

        print(f"DEBUG: Cup {self.name} - Creating {len(all_next_round_teams)//2} matches for round {next_round_number} ({next_round_name})")

        # Mische die Teams für faire Paarungen
        import random
        random.shuffle(all_next_round_teams)

        matches_created = 0
        for i in range(0, len(all_next_round_teams), 2):
            if i + 1 < len(all_next_round_teams):
                home_team = all_next_round_teams[i]
                away_team = all_next_round_teams[i + 1]

                cup_match_day = self.calculate_cup_match_day(next_round_number, self.total_rounds)
                print(f"DEBUG: Creating match {home_team.name} vs {away_team.name} for match day {cup_match_day}")

                cup_match = CupMatch(
                    cup_id=self.id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    round_name=next_round_name,
                    round_number=next_round_number,
                    cup_match_day=cup_match_day
                )
                db.session.add(cup_match)
                matches_created += 1

        # Aktualisiere Cup-Status
        self.current_round = next_round_name
        self.current_round_number = next_round_number

        print(f"DEBUG: Cup {self.name} - Advanced to round {next_round_number}, created {matches_created} matches")

        db.session.commit()

        # Setze Datumszuweisung nur für die neu erstellten Spiele dieser Runde
        try:
            # Hole alle neu erstellten Spiele dieser Runde (ohne Datum)
            new_cup_matches = CupMatch.query.filter_by(
                cup_id=self.id,
                round_number=next_round_number,
                match_date=None
            ).all()

            if new_cup_matches:
                print(f"DEBUG: Setting dates for {len(new_cup_matches)} new cup matches in round {next_round_number}")

                # Hole die verfügbaren CUP_DAYs aus dem Saisonkalender
                cup_calendar_days = SeasonCalendar.query.filter_by(
                    season_id=self.season_id,
                    day_type='CUP_DAY'
                ).filter(
                    SeasonCalendar.match_day_number.isnot(None)
                ).order_by(SeasonCalendar.id).all()

                # Erstelle Mapping von cup_match_day zu Datum
                cup_match_day_to_date = {}
                for calendar_day in cup_calendar_days:
                    if calendar_day.match_day_number:
                        cup_match_day_to_date[calendar_day.match_day_number] = calendar_day.calendar_date

                # Setze Daten nur für die neuen Spiele
                for cup_match in new_cup_matches:
                    if cup_match.cup_match_day and cup_match.cup_match_day in cup_match_day_to_date:
                        cup_match.match_date = cup_match_day_to_date[cup_match.cup_match_day]
                        print(f"DEBUG: Set date for new cup match {cup_match.id}: {cup_match.match_date}")

                db.session.commit()
                print(f"DEBUG: Successfully set dates for {len(new_cup_matches)} new cup matches")
            else:
                print(f"DEBUG: No new cup matches without dates found for round {next_round_number}")

        except Exception as e:
            print(f"ERROR: Failed to set dates for new cup matches: {e}")
            # Don't raise the exception - cup advancement should still work

        return True

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cup_type': self.cup_type,
            'season_id': self.season_id,
            'bundesland': self.bundesland,
            'landkreis': self.landkreis,
            'is_active': self.is_active,
            'current_round': self.current_round,
            'current_round_number': self.current_round_number,
            'total_rounds': self.total_rounds,
            'eligible_teams_count': len(self.get_eligible_teams()),
            'matches_count': len(self.cup_matches)
        }


class CupMatch(db.Model):
    """Pokalspiele."""
    id = db.Column(db.Integer, primary_key=True)
    cup_id = db.Column(db.Integer, db.ForeignKey('cup.id'), nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)  # NULL für Freilose

    # Spielinformationen
    round_name = db.Column(db.String(50), nullable=False)  # "1. Runde", "Achtelfinale", etc.
    round_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    cup_match_day = db.Column(db.Integer)  # Pokalspieltag (zwischen normalen Ligaspieltagen verteilt)
    match_date = db.Column(db.DateTime)  # Vereinheitlicht mit Liga-Spielen
    is_played = db.Column(db.Boolean, default=False)

    # Ergebnisse
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    home_set_points = db.Column(db.Float)
    away_set_points = db.Column(db.Float)
    winner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    stroh_performances = db.Column(db.Text)  # JSON string for Stroh player performances

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cup = db.relationship('Cup', back_populates='cup_matches')
    home_team = db.relationship('Team', foreign_keys=[home_team_id], backref='home_cup_matches')
    away_team = db.relationship('Team', foreign_keys=[away_team_id], backref='away_cup_matches')
    winner_team = db.relationship('Team', foreign_keys=[winner_team_id], backref='won_cup_matches')

    def to_dict(self):
        # Handle bye matches (away_team_id is None)
        away_team_data = None
        if self.away_team_id and self.away_team:
            away_team_data = {
                'id': self.away_team.id,
                'name': self.away_team.name,
                'club_name': self.away_team.club.name if self.away_team.club else None,
                'league_level': self.away_team.league.level if self.away_team.league else None,
                'emblem_url': f"/api/club-emblem/{self.away_team.club.verein_id}" if self.away_team.club and self.away_team.club.verein_id else None
            }

        return {
            'id': self.id,
            'cup_id': self.cup_id,
            'home_team_id': self.home_team.id,
            'away_team_id': self.away_team.id if self.away_team else None,
            'home_team_name': self.home_team.name,
            'away_team_name': self.away_team.name if self.away_team else None,
            'home_team_league_level': self.home_team.league.level if self.home_team.league else None,
            'away_team_league_level': self.away_team.league.level if self.away_team and self.away_team.league else None,
            'home_team_emblem_url': f"/api/club-emblem/{self.home_team.club.verein_id}" if self.home_team.club and self.home_team.club.verein_id else None,
            'away_team_emblem_url': f"/api/club-emblem/{self.away_team.club.verein_id}" if self.away_team and self.away_team.club and self.away_team.club.verein_id else None,
            'home_team': {
                'id': self.home_team.id,
                'name': self.home_team.name,
                'club_name': self.home_team.club.name if self.home_team.club else None,
                'league_level': self.home_team.league.level if self.home_team.league else None,
                'emblem_url': f"/api/club-emblem/{self.home_team.club.verein_id}" if self.home_team.club and self.home_team.club.verein_id else None
            },
            'away_team': away_team_data,
            'is_bye': self.away_team_id is None,  # Freilos-Flag
            'round_name': self.round_name,
            'round_number': self.round_number,
            'cup_match_day': self.cup_match_day,
            'match_date': self.match_date.isoformat() if self.match_date else None,
            'is_played': self.is_played,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'home_set_points': self.home_set_points,
            'away_set_points': self.away_set_points,
            'winner_team_id': self.winner_team_id,
            'performances': self._get_all_cup_performances()
        }

    def _get_all_cup_performances(self):
        """Get all cup performances including Stroh players."""
        from models import PlayerCupMatchPerformance
        performances = []

        # Get regular performances
        if self.is_played:
            cup_performances = PlayerCupMatchPerformance.query.filter_by(cup_match_id=self.id).all()
            performances = [perf.to_dict() for perf in cup_performances]

        # Add Stroh performances if they exist
        if self.stroh_performances:
            import json
            try:
                stroh_perfs = json.loads(self.stroh_performances)
                performances.extend(stroh_perfs)
            except (json.JSONDecodeError, TypeError):
                pass  # Ignore invalid JSON

        return performances


class LeagueHistory(db.Model):
    """Speichert die Endtabellen vergangener Saisons für jede Liga."""
    id = db.Column(db.Integer, primary_key=True)
    league_name = db.Column(db.String(100), nullable=False)  # Name der Liga
    league_level = db.Column(db.Integer, nullable=False)  # Level der Liga
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    season_name = db.Column(db.String(100), nullable=False)  # Name der Saison für einfachere Abfragen

    # Team-Informationen
    team_id = db.Column(db.Integer, nullable=False)  # Original Team ID
    team_name = db.Column(db.String(100), nullable=False)
    club_name = db.Column(db.String(100))
    club_id = db.Column(db.Integer)
    verein_id = db.Column(db.Integer)  # Für Wappen

    # Tabellenplatz und Statistiken
    position = db.Column(db.Integer, nullable=False)
    games_played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    table_points = db.Column(db.Integer, default=0)  # Tabellenpunkte
    match_points_for = db.Column(db.Integer, default=0)  # Mannschaftspunkte für
    match_points_against = db.Column(db.Integer, default=0)  # Mannschaftspunkte gegen
    pins_for = db.Column(db.Integer, default=0)  # Holz für
    pins_against = db.Column(db.Integer, default=0)  # Holz gegen
    avg_home_score = db.Column(db.Float, default=0.0)  # Durchschnitt Heim
    avg_away_score = db.Column(db.Float, default=0.0)  # Durchschnitt Auswärts

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    season = db.relationship('Season', backref='league_histories')

    def to_dict(self):
        emblem_url = None
        if self.verein_id:
            emblem_url = f"/api/club-emblem/{self.verein_id}"

        return {
            'id': self.id,
            'league_name': self.league_name,
            'league_level': self.league_level,
            'season_id': self.season_id,
            'season_name': self.season_name,
            'team_id': self.team_id,
            'team_name': self.team_name,
            'club_name': self.club_name,
            'club_id': self.club_id,
            'verein_id': self.verein_id,
            'emblem_url': emblem_url,
            'position': self.position,
            'games_played': self.games_played,
            'wins': self.wins,
            'draws': self.draws,
            'losses': self.losses,
            'table_points': self.table_points,
            'match_points_for': self.match_points_for,
            'match_points_against': self.match_points_against,
            'pins_for': self.pins_for,
            'pins_against': self.pins_against,
            'avg_home_score': self.avg_home_score,
            'avg_away_score': self.avg_away_score
        }


class CupHistory(db.Model):
    """Speichert die Sieger und Finalisten vergangener Pokale für jede Saison."""
    id = db.Column(db.Integer, primary_key=True)
    cup_name = db.Column(db.String(100), nullable=False)  # Name des Pokals
    cup_type = db.Column(db.String(20), nullable=False)  # "DKBC", "Landespokal", "Kreispokal"
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    season_name = db.Column(db.String(100), nullable=False)  # Name der Saison für einfachere Abfragen

    # Geografische Zuordnung (für Landes- und Kreispokale)
    bundesland = db.Column(db.String(50))  # Nur für Landespokal und Kreispokal
    landkreis = db.Column(db.String(100))  # Nur für Kreispokal

    # Sieger-Informationen
    winner_team_id = db.Column(db.Integer, nullable=False)  # Original Team ID des Siegers
    winner_team_name = db.Column(db.String(100), nullable=False)
    winner_club_name = db.Column(db.String(100))
    winner_club_id = db.Column(db.Integer)
    winner_verein_id = db.Column(db.Integer)  # Für Wappen

    # Finalist-Informationen
    finalist_team_id = db.Column(db.Integer, nullable=False)  # Original Team ID des Finalisten
    finalist_team_name = db.Column(db.String(100), nullable=False)
    finalist_club_name = db.Column(db.String(100))
    finalist_club_id = db.Column(db.Integer)
    finalist_verein_id = db.Column(db.Integer)  # Für Wappen

    # Finale-Ergebnis
    final_winner_score = db.Column(db.Integer)  # Holz des Siegers im Finale
    final_finalist_score = db.Column(db.Integer)  # Holz des Finalisten im Finale
    final_winner_set_points = db.Column(db.Float)  # Satzpunkte des Siegers im Finale
    final_finalist_set_points = db.Column(db.Float)  # Satzpunkte des Finalisten im Finale

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    season = db.relationship('Season', backref='cup_histories')

    def to_dict(self):
        winner_emblem_url = None
        if self.winner_verein_id:
            winner_emblem_url = f"/api/club-emblem/{self.winner_verein_id}"

        finalist_emblem_url = None
        if self.finalist_verein_id:
            finalist_emblem_url = f"/api/club-emblem/{self.finalist_verein_id}"

        return {
            'id': self.id,
            'cup_name': self.cup_name,
            'cup_type': self.cup_type,
            'season_id': self.season_id,
            'season_name': self.season_name,
            'bundesland': self.bundesland,
            'landkreis': self.landkreis,
            'winner': {
                'team_id': self.winner_team_id,
                'team_name': self.winner_team_name,
                'club_name': self.winner_club_name,
                'club_id': self.winner_club_id,
                'verein_id': self.winner_verein_id,
                'emblem_url': winner_emblem_url
            },
            'finalist': {
                'team_id': self.finalist_team_id,
                'team_name': self.finalist_team_name,
                'club_name': self.finalist_club_name,
                'club_id': self.finalist_club_id,
                'verein_id': self.finalist_verein_id,
                'emblem_url': finalist_emblem_url
            },
            'final_result': {
                'winner_score': self.final_winner_score,
                'finalist_score': self.final_finalist_score,
                'winner_set_points': self.final_winner_set_points,
                'finalist_set_points': self.final_finalist_set_points
            }
        }


class TeamAchievement(db.Model):
    """Speichert die Erfolge (Meisterschaften und Pokalsiege) der Teams für jede Saison."""
    id = db.Column(db.Integer, primary_key=True)

    # Team-Informationen
    team_id = db.Column(db.Integer, nullable=False)  # Original Team ID
    team_name = db.Column(db.String(100), nullable=False)
    club_name = db.Column(db.String(100))
    club_id = db.Column(db.Integer)
    verein_id = db.Column(db.Integer)  # Für Wappen

    # Saison-Informationen
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    season_name = db.Column(db.String(100), nullable=False)

    # Erfolg-Informationen
    achievement_type = db.Column(db.String(20), nullable=False)  # "LEAGUE_CHAMPION", "CUP_WINNER"
    achievement_name = db.Column(db.String(100), nullable=False)  # Name der Liga oder des Pokals
    achievement_level = db.Column(db.Integer)  # Liga-Level (nur für Meisterschaften)

    # Geografische Zuordnung (für Pokale)
    bundesland = db.Column(db.String(50))  # Nur für Landes- und Kreispokale
    landkreis = db.Column(db.String(100))  # Nur für Kreispokale
    cup_type = db.Column(db.String(20))  # "DKBC", "Landespokal", "Kreispokal" (nur für Pokale)

    # Zusätzliche Informationen
    final_opponent_team_name = db.Column(db.String(100))  # Finalgegner (nur für Pokale)
    final_opponent_club_name = db.Column(db.String(100))  # Finalgegner Verein (nur für Pokale)
    final_score_for = db.Column(db.Integer)  # Eigenes Ergebnis im Finale (nur für Pokale)
    final_score_against = db.Column(db.Integer)  # Gegnerisches Ergebnis im Finale (nur für Pokale)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    season = db.relationship('Season', backref='team_achievements')

    def to_dict(self):
        emblem_url = None
        if self.verein_id:
            emblem_url = f"/api/club-emblem/{self.verein_id}"

        return {
            'id': self.id,
            'team_id': self.team_id,
            'team_name': self.team_name,
            'club_name': self.club_name,
            'club_id': self.club_id,
            'verein_id': self.verein_id,
            'emblem_url': emblem_url,
            'season': {
                'season_id': self.season_id,
                'season_name': self.season_name
            },
            'achievement_type': self.achievement_type,
            'achievement_name': self.achievement_name,
            'achievement_level': self.achievement_level,
            'bundesland': self.bundesland,
            'landkreis': self.landkreis,
            'cup_type': self.cup_type,
            'final_opponent': {
                'team_name': self.final_opponent_team_name,
                'club_name': self.final_opponent_club_name
            } if self.final_opponent_team_name else None,
            'final_result': {
                'score_for': self.final_score_for,
                'score_against': self.final_score_against
            } if self.final_score_for is not None else None
        }


class TeamCupHistory(db.Model):
    """Speichert die Pokal-Teilnahmen und -Ergebnisse der Teams für jede Saison."""
    id = db.Column(db.Integer, primary_key=True)

    # Team-Informationen
    team_id = db.Column(db.Integer, nullable=False)  # Original Team ID
    team_name = db.Column(db.String(100), nullable=False)
    club_name = db.Column(db.String(100))
    club_id = db.Column(db.Integer)
    verein_id = db.Column(db.Integer)  # Für Wappen

    # Pokal-Informationen
    cup_name = db.Column(db.String(100), nullable=False)  # Name des Pokals
    cup_type = db.Column(db.String(20), nullable=False)  # "DKBC", "Landespokal", "Kreispokal"
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    season_name = db.Column(db.String(100), nullable=False)  # Name der Saison für einfachere Abfragen

    # Geografische Zuordnung (für Landes- und Kreispokale)
    bundesland = db.Column(db.String(50))  # Nur für Landespokal und Kreispokal
    landkreis = db.Column(db.String(100))  # Nur für Kreispokal

    # Turnier-Verlauf
    reached_round = db.Column(db.String(50), nullable=False)  # "1. Runde", "Achtelfinale", "Viertelfinale", "Halbfinale", "Finale", "Sieger"
    reached_round_number = db.Column(db.Integer, nullable=False)  # Rundennummer (1, 2, 3, etc.)
    total_rounds = db.Column(db.Integer, nullable=False)  # Gesamtanzahl der Runden im Pokal

    # Ausscheidung (falls nicht Sieger)
    eliminated_by_team_id = db.Column(db.Integer)  # Team ID des Gegners, der das Team eliminiert hat
    eliminated_by_team_name = db.Column(db.String(100))  # Name des eliminierenden Teams
    eliminated_by_club_name = db.Column(db.String(100))  # Club des eliminierenden Teams
    eliminated_by_verein_id = db.Column(db.Integer)  # Für Wappen des eliminierenden Teams

    # Finale-Informationen (falls erreicht)
    elimination_match_score_for = db.Column(db.Integer)  # Eigenes Ergebnis im Ausscheidungsspiel
    elimination_match_score_against = db.Column(db.Integer)  # Gegner-Ergebnis im Ausscheidungsspiel
    elimination_match_set_points_for = db.Column(db.Float)  # Eigene Satzpunkte im Ausscheidungsspiel
    elimination_match_set_points_against = db.Column(db.Float)  # Gegner-Satzpunkte im Ausscheidungsspiel

    # Status-Flags
    is_winner = db.Column(db.Boolean, default=False)  # True wenn das Team den Pokal gewonnen hat
    is_finalist = db.Column(db.Boolean, default=False)  # True wenn das Team das Finale erreicht hat

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    season = db.relationship('Season', backref='team_cup_histories')

    def to_dict(self):
        team_emblem_url = None
        if self.verein_id:
            team_emblem_url = f"/api/club-emblem/{self.verein_id}"

        eliminated_by_emblem_url = None
        if self.eliminated_by_verein_id:
            eliminated_by_emblem_url = f"/api/club-emblem/{self.eliminated_by_verein_id}"

        return {
            'id': self.id,
            'team': {
                'team_id': self.team_id,
                'team_name': self.team_name,
                'club_name': self.club_name,
                'club_id': self.club_id,
                'verein_id': self.verein_id,
                'emblem_url': team_emblem_url
            },
            'cup': {
                'cup_name': self.cup_name,
                'cup_type': self.cup_type,
                'bundesland': self.bundesland,
                'landkreis': self.landkreis
            },
            'season': {
                'season_id': self.season_id,
                'season_name': self.season_name
            },
            'performance': {
                'reached_round': self.reached_round,
                'reached_round_number': self.reached_round_number,
                'total_rounds': self.total_rounds,
                'is_winner': self.is_winner,
                'is_finalist': self.is_finalist
            },
            'elimination': {
                'eliminated_by_team_id': self.eliminated_by_team_id,
                'eliminated_by_team_name': self.eliminated_by_team_name,
                'eliminated_by_club_name': self.eliminated_by_club_name,
                'eliminated_by_verein_id': self.eliminated_by_verein_id,
                'eliminated_by_emblem_url': eliminated_by_emblem_url,
                'match_score_for': self.elimination_match_score_for,
                'match_score_against': self.elimination_match_score_against,
                'match_set_points_for': self.elimination_match_set_points_for,
                'match_set_points_against': self.elimination_match_set_points_against
            }
        }


class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    income = db.Column(db.Float, default=0.0)
    expenses = db.Column(db.Float, default=0.0)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    club = db.relationship('Club', back_populates='finances')

    def to_dict(self):
        return {
            'id': self.id,
            'club_id': self.club_id,
            'balance': self.balance,
            'income': self.income,
            'expenses': self.expenses,
            'date': self.date.isoformat(),
            'description': self.description
        }

class TransferOffer(db.Model):
    """Model for transfer offers between clubs."""
    id = db.Column(db.Integer, primary_key=True)

    # Player being offered
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)

    # Club making the offer
    offering_club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)

    # Club receiving the offer (current player's club)
    receiving_club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)

    # Offer amount
    offer_amount = db.Column(db.Integer, nullable=False)

    # Status: 'pending', 'accepted', 'rejected', 'withdrawn'
    status = db.Column(db.String(20), default='pending')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = db.relationship('Player', backref='transfer_offers')
    offering_club = db.relationship('Club', foreign_keys=[offering_club_id], backref='made_offers')
    receiving_club = db.relationship('Club', foreign_keys=[receiving_club_id], backref='received_offers')

    def to_dict(self):
        return {
            'id': self.id,
            'player': {
                'id': self.player.id,
                'name': self.player.name,
                'age': self.player.age,
                'position': self.player.position,
                'strength': self.player.strength,
                'team': self.player.teams[0].name if self.player.teams else 'Vereinslos'
            },
            'offering_club': self.offering_club.name,
            'receiving_club': self.receiving_club.name,
            'offer_amount': self.offer_amount,
            'status': self.status,
            'date': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class TransferHistory(db.Model):
    """Model for completed transfers."""
    id = db.Column(db.Integer, primary_key=True)

    # Player who was transferred
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)

    # Clubs involved in the transfer
    from_club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    to_club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)

    # Transfer amount
    transfer_amount = db.Column(db.Integer, nullable=False)

    # Season when the transfer happened
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)

    # Timestamp
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    player = db.relationship('Player', backref='transfer_history')
    from_club = db.relationship('Club', foreign_keys=[from_club_id], backref='players_sold')
    to_club = db.relationship('Club', foreign_keys=[to_club_id], backref='players_bought')
    season = db.relationship('Season', backref='transfers')

    def to_dict(self):
        return {
            'id': self.id,
            'player': {
                'id': self.player.id,
                'name': self.player.name,
                'age': self.player.age,
                'position': self.player.position,
                'strength': self.player.strength
            },
            'from_club': self.from_club.name,
            'to_club': self.to_club.name,
            'transfer_amount': self.transfer_amount,
            'transfer_date': self.transfer_date.isoformat(),
            'season': self.season.year
        }


class LaneRecord(db.Model):
    """Model for tracking lane records (Bahnrekorde) for clubs, teams, and players."""
    id = db.Column(db.Integer, primary_key=True)

    # Record type: 'team' or 'individual'
    record_type = db.Column(db.String(20), nullable=False)

    # Age category: 'Herren', 'U19', 'U14'
    category = db.Column(db.String(20), nullable=False)

    # Club where the lane is located
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)

    # Player who set the record (for individual records)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)

    # Team that set the record (for team records)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)

    # Score achieved (total across all 4 lanes)
    score = db.Column(db.Integer, nullable=False)

    # Match where the record was set
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)

    # Date when the record was set
    record_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    club = db.relationship('Club', backref=db.backref('lane_records', lazy='dynamic'))
    player = db.relationship('Player', backref=db.backref('lane_records', lazy='dynamic'))
    team = db.relationship('Team', backref=db.backref('lane_records', lazy='dynamic'))
    match = db.relationship('Match', backref=db.backref('lane_records', lazy='dynamic'))

    def to_dict(self):
        """Convert the record to a dictionary for API responses."""
        result = {
            'id': self.id,
            'record_type': self.record_type,
            'category': self.category,
            'club_id': self.club_id,
            'club_name': self.club.name,
            'score': self.score,
            'match_id': self.match_id,
            'record_date': self.record_date.isoformat() if self.record_date else None
        }

        # Add player or team information based on record type
        if self.record_type == 'individual' and self.player:
            result['player_id'] = self.player_id
            result['player_name'] = self.player.name
            result['player_age'] = self.player.age
        elif self.record_type == 'team' and self.team:
            result['team_id'] = self.team_id
            result['team_name'] = self.team.name

        return result

    @staticmethod
    def get_age_category(age):
        """Determine the age category based on player age."""
        if age < 14:
            return 'U14'
        elif age < 19:
            return 'U19'
        else:
            return 'Herren'

    @staticmethod
    def check_and_update_record(club_id, score, player=None, team=None, match_id=None):
        """
        Check if a new record has been set and update the database if needed.

        Args:
            club_id: ID of the club where the lane is located
            score: Total score achieved across all 4 lanes
            player: Player object (for individual records)
            team: Team object (for team records)
            match_id: ID of the match where the record was set

        Returns:
            True if a new record was set, False otherwise
        """
        if player:
            # Individual record
            record_type = 'individual'
            category = LaneRecord.get_age_category(player.age)

            # Check if there's an existing record
            existing_record = LaneRecord.query.filter_by(
                record_type=record_type,
                category=category,
                club_id=club_id
            ).first()

            if not existing_record or score > existing_record.score:
                # New record!
                if existing_record:
                    # Update existing record
                    existing_record.score = score
                    existing_record.player_id = player.id
                    existing_record.match_id = match_id
                    existing_record.record_date = datetime.utcnow()
                else:
                    # Create new record
                    new_record = LaneRecord(
                        record_type=record_type,
                        category=category,
                        club_id=club_id,
                        player_id=player.id,
                        score=score,
                        match_id=match_id
                    )
                    db.session.add(new_record)

                db.session.commit()
                return True

        elif team:
            # Team record
            record_type = 'team'

            # Check if there's an existing record
            existing_record = LaneRecord.query.filter_by(
                record_type=record_type,
                club_id=club_id
            ).first()

            if not existing_record or score > existing_record.score:
                # New record!
                if existing_record:
                    # Update existing record
                    existing_record.score = score
                    existing_record.team_id = team.id
                    existing_record.match_id = match_id
                    existing_record.record_date = datetime.utcnow()
                else:
                    # Create new record
                    new_record = LaneRecord(
                        record_type=record_type,
                        category='Herren',  # Default category for team records
                        club_id=club_id,
                        team_id=team.id,
                        score=score,
                        match_id=match_id
                    )
                    db.session.add(new_record)

                db.session.commit()
                return True

        return False


class UserLineup(db.Model):
    """Model for storing user-selected lineups for matches."""
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    is_home_team = db.Column(db.Boolean, nullable=False)  # True für Heimteam, False für Auswärtsteam
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    match = db.relationship('Match', backref=db.backref('lineups', lazy='dynamic'))
    team = db.relationship('Team')
    positions = db.relationship('LineupPosition', back_populates='lineup', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'team_id': self.team_id,
            'team_name': self.team.name,
            'is_home_team': self.is_home_team,
            'positions': [pos.to_dict() for pos in self.positions]
        }


class LineupPosition(db.Model):
    """Model for storing player positions in a user-selected lineup."""
    id = db.Column(db.Integer, primary_key=True)
    lineup_id = db.Column(db.Integer, db.ForeignKey('user_lineup.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    position_number = db.Column(db.Integer, nullable=False)  # Position im Team (1-6)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lineup = db.relationship('UserLineup', back_populates='positions')
    player = db.relationship('Player')

    def to_dict(self):
        return {
            'id': self.id,
            'lineup_id': self.lineup_id,
            'player_id': self.player_id,
            'player_name': self.player.name,
            'position_number': self.position_number
        }


class PlayerMatchPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    is_home_team = db.Column(db.Boolean, nullable=False)  # True für Heimteam, False für Auswärtsteam
    position_number = db.Column(db.Integer, nullable=False)  # Position im Team (1-6)
    is_substitute = db.Column(db.Boolean, default=False)  # True wenn Spieler ein Ersatzspieler ist

    # Ergebnisse der 4 Bahnen (je 30 Wurf)
    lane1_score = db.Column(db.Integer)
    lane2_score = db.Column(db.Integer)
    lane3_score = db.Column(db.Integer)
    lane4_score = db.Column(db.Integer)
    total_score = db.Column(db.Integer)  # Gesamtergebnis aller Bahnen

    # Detaillierte Statistiken
    volle_score = db.Column(db.Integer)  # Ergebnis auf die vollen Bilder (15 Wurf pro Bahn)
    raeumer_score = db.Column(db.Integer)  # Ergebnis auf die Räumer (15 Wurf pro Bahn)
    fehler_count = db.Column(db.Integer)  # Anzahl der Fehlwürfe

    # Neue Felder für das Punktesystem
    set_points = db.Column(db.Float, default=0.0)  # Satzpunkte (SP) - kann auch 0.5 sein
    match_points = db.Column(db.Integer, default=0)  # Mannschaftspunkte (MP)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = db.relationship('Player', back_populates='performances')
    match = db.relationship('Match', back_populates='performances')
    team = db.relationship('Team')

    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'player_name': self.player.name,
            'match_id': self.match_id,
            'team_id': self.team_id,
            'team_name': self.team.name,
            'is_home_team': self.is_home_team,
            'position_number': self.position_number,
            'is_substitute': self.is_substitute,
            'lane1_score': self.lane1_score,
            'lane2_score': self.lane2_score,
            'lane3_score': self.lane3_score,
            'lane4_score': self.lane4_score,
            'total_score': self.total_score,
            'volle_score': self.volle_score,
            'raeumer_score': self.raeumer_score,
            'fehler_count': self.fehler_count,
            'set_points': self.set_points,
            'match_points': self.match_points
        }


class PlayerCupMatchPerformance(db.Model):
    """Spielerleistungen für Pokalspiele."""
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    cup_match_id = db.Column(db.Integer, db.ForeignKey('cup_match.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    is_home_team = db.Column(db.Boolean, nullable=False)  # True für Heimteam, False für Auswärtsteam
    position_number = db.Column(db.Integer, nullable=False)  # Position im Team (1-6)
    is_substitute = db.Column(db.Boolean, default=False)  # True wenn Spieler ein Ersatzspieler ist

    # Ergebnisse der 4 Bahnen (je 30 Wurf)
    lane1_score = db.Column(db.Integer)
    lane2_score = db.Column(db.Integer)
    lane3_score = db.Column(db.Integer)
    lane4_score = db.Column(db.Integer)
    total_score = db.Column(db.Integer)  # Gesamtergebnis aller Bahnen

    # Detaillierte Statistiken
    volle_score = db.Column(db.Integer)  # Ergebnis auf die vollen Bilder (15 Wurf pro Bahn)
    raeumer_score = db.Column(db.Integer)  # Ergebnis auf die Räumer (15 Wurf pro Bahn)
    fehler_count = db.Column(db.Integer)  # Anzahl der Fehlwürfe

    # Neue Felder für das Punktesystem
    set_points = db.Column(db.Float, default=0.0)  # Satzpunkte (SP) - kann auch 0.5 sein
    match_points = db.Column(db.Integer, default=0)  # Mannschaftspunkte (MP)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = db.relationship('Player', backref='cup_performances')
    cup_match = db.relationship('CupMatch', backref='performances')
    team = db.relationship('Team')

    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'player_name': self.player.name,
            'cup_match_id': self.cup_match_id,
            'team_id': self.team_id,
            'team_name': self.team.name,
            'is_home_team': self.is_home_team,
            'position_number': self.position_number,
            'is_substitute': self.is_substitute,
            'lane1_score': self.lane1_score,
            'lane2_score': self.lane2_score,
            'lane3_score': self.lane3_score,
            'lane4_score': self.lane4_score,
            'total_score': self.total_score,
            'volle_score': self.volle_score,
            'raeumer_score': self.raeumer_score,
            'fehler_count': self.fehler_count,
            'set_points': self.set_points,
            'match_points': self.match_points
        }
