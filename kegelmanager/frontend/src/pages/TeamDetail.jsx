import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getTeam } from '../services/api';
import './TeamDetail.css';

const TeamDetail = () => {
  const { id } = useParams();
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Lade Teamdaten aus der API
  useEffect(() => {
    console.log(`Lade Team mit ID ${id} aus der API...`);

    getTeam(id)
      .then(data => {
        console.log('Geladene Teamdaten:', data);

        if (data) {
          console.log('Spielerdaten aus API:', data.players);

          // Verarbeite die Daten und füge fehlende Eigenschaften hinzu
          const processedTeam = {
            ...data,
            // Stelle sicher, dass club und league Objekte sind
            club: data.club || { id: 0, name: 'Unbekannt' },
            league: data.league || { id: data.league_id, name: 'Liga ' + data.league_id, level: 1 },
            position: 0, // In einer echten Anwendung würde dies aus der Datenbank kommen
            isYouth: data.is_youth_team || false,
            // Verwende die Spielerdaten aus der API
            players: data.players || [],
            // Verwende die Spieldaten aus der API
            upcomingMatches: data.upcomingMatches || [],
            recentMatches: data.recentMatches || [],
            // Verwende die Statistikdaten aus der API
            stats: data.stats || {
              matches: 0,
              wins: 0,
              draws: 0,
              losses: 0,
              goalsFor: 0,
              goalsAgainst: 0,
              points: 0,
              avgStrength: data.avg_strength || 0
            }
          };

          setTeam(processedTeam);
        } else {
          console.error(`Keine Daten für Team ${id} gefunden`);
        }

        setLoading(false);
      })
      .catch(error => {
        console.error(`Fehler beim Laden des Teams ${id}:`, error);
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return <div className="loading">Lade Teamdaten...</div>;
  }

  if (!team) {
    return <div className="error">Team nicht gefunden</div>;
  }

  return (
    <div className="team-detail-page">
      <div className="page-header">
        <div className="breadcrumbs">
          <Link to="/teams">Mannschaften</Link> / {team.name}
        </div>
      </div>

      <div className="team-profile card">
        <div className="team-header">
          <div className="team-logo">
            {team.club && team.club.emblem_url ? (
              <img
                src={team.club.emblem_url}
                alt={`${team.club.name} Wappen`}
                className="club-emblem"
                onError={(e) => {
                  console.log(`Fehler beim Laden des Emblems für ${team.club.name}:`, e);
                  e.target.style.display = 'none';
                  e.target.parentNode.innerHTML = `<span>${team.name.split(' ').map(word => word[0]).join('')}</span>`;
                }}
              />
            ) : (
              <span>{team.name.split(' ').map(word => word[0]).join('')}</span>
            )}
          </div>
          <div className="team-header-info">
            <h1 className="team-name">{team.name}</h1>
            <div className="team-meta">
              <Link to={`/clubs/${team.club.id}`} className="team-club">{team.club.name}</Link>
              <Link to={`/leagues/${team.league.id}`} className="team-league">{team.league.name}</Link>
              <span className="team-position">{team.position}. Platz</span>
            </div>
          </div>
          <div className="team-actions">
            <button className="btn btn-primary">Mannschaft verwalten</button>
          </div>
        </div>

        <div className="team-tabs">
          <div
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Übersicht
          </div>
          <div
            className={`tab ${activeTab === 'players' ? 'active' : ''}`}
            onClick={() => setActiveTab('players')}
          >
            Spieler
          </div>
          <div
            className={`tab ${activeTab === 'matches' ? 'active' : ''}`}
            onClick={() => setActiveTab('matches')}
          >
            Spiele
          </div>
          <div
            className={`tab ${activeTab === 'stats' ? 'active' : ''}`}
            onClick={() => setActiveTab('stats')}
          >
            Statistiken
          </div>
        </div>

        <div className="team-content">
          {activeTab === 'overview' && (
            <div className="overview-tab">
              <div className="overview-grid">
                <div className="overview-card">
                  <h3>Teamstatistik</h3>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="stat-label">Spiele:</span>
                      <span className="stat-value">{team.stats.matches}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Siege:</span>
                      <span className="stat-value">{team.stats.wins}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Unentschieden:</span>
                      <span className="stat-value">{team.stats.draws}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Niederlagen:</span>
                      <span className="stat-value">{team.stats.losses}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Punkte:</span>
                      <span className="stat-value">{team.stats.points}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Tore:</span>
                      <span className="stat-value">{team.stats.goalsFor}:{team.stats.goalsAgainst}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Ø Heimergebnis:</span>
                      <span className="stat-value">{team.stats.avgHomeScore?.toFixed(1) || '0.0'}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Ø Auswärtsergebnis:</span>
                      <span className="stat-value">{team.stats.avgAwayScore?.toFixed(1) || '0.0'}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Ø Stärke:</span>
                      <div className="strength-display">
                        <div className="strength-bar">
                          <div
                            className="strength-fill"
                            style={{ width: `${team.stats.avgStrength}%` }}
                          ></div>
                        </div>
                        <span>{team.stats.avgStrength}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="overview-card">
                  <h3>Top Spieler</h3>
                  <div className="players-list">
                    {team.players.slice(0, 5).map(player => (
                      <Link to={`/players/${player.id}`} key={player.id} className="player-item">
                        <span className="player-name">{player.name}</span>
                        <div className="player-info">
                          <span className="player-position">{player.position}</span>
                          <span className="player-strength">{player.strength}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              </div>

              <div className="overview-grid">
                <div className="overview-card">
                  <h3>Nächste Spiele</h3>
                  <div className="matches-list">
                    {team.upcomingMatches.map(match => (
                      <Link to={`/matches/${match.id}`} key={match.id} className="match-item">
                        <div className="match-date">
                          {new Date(match.date).toLocaleDateString('de-DE', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                        <div className="match-teams">
                          <span className={`team ${match.homeTeam === team.name ? 'home' : ''}`}>
                            {match.homeTeam}
                          </span>
                          <span className="vs">vs</span>
                          <span className={`team ${match.awayTeam === team.name ? 'home' : ''}`}>
                            {match.awayTeam}
                          </span>
                        </div>
                        <div className="match-league">{match.league}</div>
                      </Link>
                    ))}
                  </div>
                </div>

                <div className="overview-card">
                  <h3>Letzte Ergebnisse</h3>
                  <div className="matches-list">
                    {team.recentMatches.map(match => (
                      <Link to={`/matches/${match.id}`} key={match.id} className="match-item">
                        <div className="match-date">
                          {new Date(match.date).toLocaleDateString('de-DE', {
                            day: '2-digit',
                            month: '2-digit'
                          })}
                        </div>
                        <div className="match-teams">
                          <span className={`team ${match.homeTeam === team.name ? 'home' : ''}`}>
                            {match.homeTeam}
                          </span>
                          <span className="score">
                            {match.homeScore} - {match.awayScore}
                          </span>
                          <span className={`team ${match.awayTeam === team.name ? 'home' : ''}`}>
                            {match.awayTeam}
                          </span>
                        </div>
                        <div className="match-league">{match.league}</div>
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'players' && (
            <div className="players-tab">
              <table className="table players-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Alter</th>
                    <th>Position</th>
                    <th>Stärke</th>
                    <th>Talent</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {team.players.map(player => (
                    <tr key={player.id}>
                      <td>
                        <Link to={`/players/${player.id}`} className="player-name-link">
                          {player.name}
                        </Link>
                      </td>
                      <td>{player.age}</td>
                      <td>{player.position}</td>
                      <td>
                        <div className="strength-display">
                          <div className="strength-bar">
                            <div
                              className="strength-fill"
                              style={{ width: `${player.strength}%` }}
                            ></div>
                          </div>
                          <span>{player.strength}</span>
                        </div>
                      </td>
                      <td>
                        <div className="talent-stars">
                          {Array.from({ length: 10 }, (_, i) => (
                            <span
                              key={i}
                              className={`star ${i < player.talent ? 'filled' : ''}`}
                            >★</span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="actions">
                          <Link to={`/players/${player.id}`} className="btn btn-small">
                            Details
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="players-actions">
                <button className="btn btn-primary">Spieler transferieren</button>
              </div>
            </div>
          )}

          {activeTab === 'matches' && (
            <div className="matches-tab">
              <h3>Nächste Spiele</h3>
              <table className="table matches-table">
                <thead>
                  <tr>
                    <th>Datum</th>
                    <th>Heimteam</th>
                    <th>Auswärtsteam</th>
                    <th>Liga</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {team.upcomingMatches.map(match => (
                    <tr key={match.id}>
                      <td>
                        {new Date(match.date).toLocaleDateString('de-DE', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className={match.homeTeam === team.name ? 'home-team' : ''}>
                        {match.homeTeam}
                      </td>
                      <td className={match.awayTeam === team.name ? 'home-team' : ''}>
                        {match.awayTeam}
                      </td>
                      <td>{match.league}</td>
                      <td>
                        <Link to={`/matches/${match.id}`} className="btn btn-small">
                          Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <h3>Letzte Ergebnisse</h3>
              <table className="table matches-table">
                <thead>
                  <tr>
                    <th>Datum</th>
                    <th>Heimteam</th>
                    <th>Ergebnis</th>
                    <th>Auswärtsteam</th>
                    <th>Liga</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {team.recentMatches.map(match => (
                    <tr key={match.id}>
                      <td>
                        {new Date(match.date).toLocaleDateString('de-DE', {
                          day: '2-digit',
                          month: '2-digit'
                        })}
                      </td>
                      <td className={match.homeTeam === team.name ? 'home-team' : ''}>
                        {match.homeTeam}
                      </td>
                      <td>
                        <strong>{match.homeScore} - {match.awayScore}</strong>
                      </td>
                      <td className={match.awayTeam === team.name ? 'home-team' : ''}>
                        {match.awayTeam}
                      </td>
                      <td>{match.league}</td>
                      <td>
                        <Link to={`/matches/${match.id}`} className="btn btn-small">
                          Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="stats-tab">
              <div className="stats-section">
                <h3>Teamstatistiken</h3>
                <div className="stats-grid detailed">
                  <div className="stat-item">
                    <span className="stat-label">Spiele:</span>
                    <span className="stat-value">{team.stats.matches}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Siege:</span>
                    <span className="stat-value">{team.stats.wins}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Unentschieden:</span>
                    <span className="stat-value">{team.stats.draws}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Niederlagen:</span>
                    <span className="stat-value">{team.stats.losses}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Punkte:</span>
                    <span className="stat-value">{team.stats.points}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Tore:</span>
                    <span className="stat-value">{team.stats.goalsFor}:{team.stats.goalsAgainst}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Tordifferenz:</span>
                    <span className="stat-value">{team.stats.goalsFor - team.stats.goalsAgainst}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Ø Tore pro Spiel:</span>
                    <span className="stat-value">{(team.stats.goalsFor / team.stats.matches).toFixed(1)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Ø Gegentore pro Spiel:</span>
                    <span className="stat-value">{(team.stats.goalsAgainst / team.stats.matches).toFixed(1)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Ø Heimergebnis:</span>
                    <span className="stat-value">{team.stats.avgHomeScore?.toFixed(1) || '0.0'}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Ø Auswärtsergebnis:</span>
                    <span className="stat-value">{team.stats.avgAwayScore?.toFixed(1) || '0.0'}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Siegquote:</span>
                    <span className="stat-value">{((team.stats.wins / team.stats.matches) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Ø Stärke:</span>
                    <div className="strength-display">
                      <div className="strength-bar">
                        <div
                          className="strength-fill"
                          style={{ width: `${team.stats.avgStrength}%` }}
                        ></div>
                      </div>
                      <span>{team.stats.avgStrength}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="stats-section">
                <h3>Spielerstatistiken</h3>
                <div className="chart-placeholder">
                  [Hier würde ein Spielerstatistik-Chart angezeigt werden]
                </div>
              </div>

              <div className="stats-section">
                <h3>Saisonverlauf</h3>
                <div className="chart-placeholder">
                  [Hier würde ein Saisonverlauf-Chart angezeigt werden]
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeamDetail;
