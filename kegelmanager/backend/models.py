from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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

    def calculate_team_specific_stats(self, team_id):
        """Calculate player statistics for a specific team."""
        # Get all performances for this player with this team
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
        for player in self.players:
            # Calculate statistics for this player specifically for this team
            team_stats = player.calculate_team_specific_stats(self.id)

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
                'statistics': team_stats,  # Verwende teamspezifische Statistiken
                'is_substitute': False,  # Regular team member
                'club_id': player.club_id,
                'club_name': player.club.name if player.club else 'Kein Verein'
            }
            players_info.append(player_info)

        # Get detailed player information for substitute players
        substitute_players = self.get_substitute_players()
        for player in substitute_players:
            # Calculate statistics for this player specifically for this team
            team_stats = player.calculate_team_specific_stats(self.id)

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
                'statistics': team_stats,
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

        # Get home matches
        home_matches = Match.query.filter_by(home_team_id=self.id, is_played=True).order_by(Match.match_date.desc()).all()
        for match in home_matches:
            match_data = {
                'id': match.id,
                'date': match.match_date.isoformat() if match.match_date else None,
                'homeTeam': self.name,
                'awayTeam': match.away_team.name,
                'homeScore': match.home_score,
                'awayScore': match.away_score,
                'league': match.league.name,
                'status': 'played'
            }
            all_played_matches.append((match.match_date, match_data))

        # Get away matches
        away_matches = Match.query.filter_by(away_team_id=self.id, is_played=True).order_by(Match.match_date.desc()).all()
        for match in away_matches:
            match_data = {
                'id': match.id,
                'date': match.match_date.isoformat() if match.match_date else None,
                'homeTeam': match.home_team.name,
                'awayTeam': self.name,
                'homeScore': match.home_score,
                'awayScore': match.away_score,
                'league': match.league.name,
                'status': 'played'
            }
            all_played_matches.append((match.match_date, match_data))

        # Sort by date (newest first)
        all_played_matches.sort(key=lambda x: x[0] if x[0] else datetime.min, reverse=True)
        # Get all recent matches but mark the first 5 as visible by default
        recent_matches = []
        for i, match_tuple in enumerate(all_played_matches):
            match_data = match_tuple[1]
            match_data['visible'] = i < 5  # Only first 5 are visible by default
            recent_matches.append(match_data)

        # Get upcoming matches (unplayed matches)
        upcoming_matches = []
        all_upcoming_matches = []

        # Get home matches
        home_matches = Match.query.filter_by(home_team_id=self.id, is_played=False).order_by(Match.match_date).all()
        for match in home_matches:
            match_data = {
                'id': match.id,
                'date': match.match_date.isoformat() if match.match_date else None,
                'homeTeam': self.name,
                'awayTeam': match.away_team.name,
                'league': match.league.name,
                'status': 'upcoming'
            }
            all_upcoming_matches.append((match.match_date, match_data))

        # Get away matches
        away_matches = Match.query.filter_by(away_team_id=self.id, is_played=False).order_by(Match.match_date).all()
        for match in away_matches:
            match_data = {
                'id': match.id,
                'date': match.match_date.isoformat() if match.match_date else None,
                'homeTeam': match.home_team.name,
                'awayTeam': self.name,
                'league': match.league.name,
                'status': 'upcoming'
            }
            all_upcoming_matches.append((match.match_date, match_data))

        # Sort by date (oldest first)
        all_upcoming_matches.sort(key=lambda x: x[0] if x[0] else datetime.max)
        # Get all upcoming matches but mark the first 5 as visible by default
        upcoming_matches = []
        for i, match_tuple in enumerate(all_upcoming_matches):
            match_data = match_tuple[1]
            match_data['visible'] = i < 5  # Only first 5 are visible by default
            upcoming_matches.append(match_data)

        # Calculate team statistics
        stats = self.calculate_stats()

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
            'stats': stats
        }

    def calculate_stats(self):
        """Calculate team statistics based on played matches."""
        # Get all matches for this team
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

    # Neue Felder für Auf- und Abstieg
    aufstieg_liga_id = db.Column(db.Integer, db.ForeignKey('league.id'))  # Liga, in die Aufsteiger gehen
    abstieg_liga_id = db.Column(db.Integer, db.ForeignKey('league.id'))  # Liga, in die Absteiger gehen

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
    aufstieg_liga = db.relationship('League', remote_side=[id], foreign_keys=[aufstieg_liga_id], backref=db.backref('abstiegs_ligen', lazy='dynamic'))
    abstieg_liga = db.relationship('League', remote_side=[id], foreign_keys=[abstieg_liga_id], backref=db.backref('aufstiegs_ligen', lazy='dynamic'))

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

            standings.append({
                'position': i + 1,
                'team_id': team.id,
                'team': team.name,
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
                'avg_away_score': avg_away_score
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
            'performances': [perf.to_dict() for perf in self.performances] if self.is_played else []
        }

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

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_current': self.is_current
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
