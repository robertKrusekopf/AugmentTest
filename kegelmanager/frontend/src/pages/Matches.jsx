import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getMatches } from '../services/api';
import './Matches.css';

const Matches = () => {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterLeague, setFilterLeague] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  // Lade Daten aus der Datenbank
  useEffect(() => {
    console.log('Lade Spiele aus der Datenbank...');

    // Lade die Daten aus der API
    getMatches()
      .then(data => {
        console.log('Geladene Spiele:', data);

        // Wenn keine Daten zurückgegeben werden, verwende leere Liste
        if (!data || data.length === 0) {
          console.warn('Keine Spiele in der Datenbank gefunden.');
          setMatches([]);
        } else {
          // Verarbeite die Daten und füge fehlende Eigenschaften hinzu
          const processedMatches = data.map(match => {
            // Bestimme die Teams
            const homeTeam = match.home_team ? match.home_team.name : 'Unbekannt';
            const awayTeam = match.away_team ? match.away_team.name : 'Unbekannt';

            // Bestimme die Liga
            let leagueName = 'Unbekannt';
            if (match.league && match.league.name) {
              leagueName = match.league.name;
            }

            // Bestimme den Status des Spiels
            const status = match.home_score !== null && match.away_score !== null ? 'played' : 'upcoming';

            // Bestimme die Runde des Spiels
            const round = match.round || 1;

            // Stelle sicher, dass alle benötigten Eigenschaften vorhanden sind
            return {
              id: match.id,
              date: match.date || new Date().toISOString(),
              homeTeam: homeTeam,
              awayTeam: awayTeam,
              homeScore: match.home_score,
              awayScore: match.away_score,
              league: leagueName,
              status: status,
              round: round
            };
          });

          setMatches(processedMatches);
        }

        setLoading(false);
      })
      .catch(error => {
        console.error('Fehler beim Laden der Spiele:', error);
        setLoading(false);
      });
  }, []);

  // Filtern der Spiele basierend auf Liga und Status
  const filteredMatches = matches.filter(match => {
    const leagueMatch = filterLeague === '' || match.league === filterLeague;
    const statusMatch = filterStatus === '' || match.status === filterStatus;

    return leagueMatch && statusMatch;
  });

  // Gruppieren der Spiele nach Runde
  const groupedMatches = filteredMatches.reduce((groups, match) => {
    const round = match.round;
    if (!groups[round]) {
      groups[round] = [];
    }
    groups[round].push(match);
    return groups;
  }, {});

  // Sortieren der Runden in absteigender Reihenfolge
  const sortedRounds = Object.keys(groupedMatches).sort((a, b) => b - a);

  // Extrahieren der verfügbaren Ligen für den Filter
  const leagues = [...new Set(matches.map(match => match.league))];

  if (loading) {
    return <div className="loading">Lade Spiele...</div>;
  }

  return (
    <div className="matches-page">
      <h1 className="page-title">Spiele</h1>

      <div className="filters">
        <div className="filter-bar">
          <select
            className="filter-select"
            value={filterLeague}
            onChange={(e) => setFilterLeague(e.target.value)}
          >
            <option value="">Alle Ligen</option>
            {leagues.map(league => (
              <option key={league} value={league}>{league}</option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">Alle Spiele</option>
            <option value="upcoming">Anstehende Spiele</option>
            <option value="played">Gespielte Spiele</option>
          </select>
        </div>
      </div>

      <div className="matches-container">
        {sortedRounds.map(round => (
          <div key={round} className="round-section">
            <h2 className="round-title">Spieltag {round}</h2>
            <div className="matches-grid">
              {groupedMatches[round].map(match => (
                <Link to={`/matches/${match.id}`} key={match.id} className="match-card">
                  <div className="match-header">
                    <div className="match-date">
                      {new Date(match.date).toLocaleDateString('de-DE', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                      })}
                    </div>
                    <div className="match-time">
                      {new Date(match.date).toLocaleTimeString('de-DE', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                    <div className="match-league">{match.league}</div>
                  </div>

                  <div className="match-teams">
                    <div className="team home">{match.homeTeam}</div>
                    <div className="match-result">
                      {match.status === 'played' ? (
                        <span className="score">{match.homeScore} - {match.awayScore}</span>
                      ) : (
                        <span className="vs">vs</span>
                      )}
                    </div>
                    <div className="team away">{match.awayTeam}</div>
                  </div>

                  <div className="match-footer">
                    <div className={`match-status ${match.status}`}>
                      {match.status === 'played' ? 'Gespielt' : 'Anstehend'}
                    </div>
                    <button className="btn btn-small">Details</button>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Matches;
