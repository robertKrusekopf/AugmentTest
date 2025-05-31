import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getTeam, updateTeam } from '../services/api';
import './TeamDetail.css';

const TeamDetail = () => {
  const { id } = useParams();
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [upcomingMatchesExpanded, setUpcomingMatchesExpanded] = useState(false);
  const [recentMatchesExpanded, setRecentMatchesExpanded] = useState(false);
  const [isEditingStaerke, setIsEditingStaerke] = useState(false);
  const [staerkeValue, setStaerkeValue] = useState(0);
  const [savingStaerke, setSavingStaerke] = useState(false);

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
              goalsFor: 0, // Gesamtholz
              goalsAgainst: 0, // Gegnerisches Gesamtholz
              points: 0,
              homeMatches: 0,
              awayMatches: 0,
              homeGoalsFor: 0, // Heimholz
              homeGoalsAgainst: 0, // Gegnerisches Heimholz
              awayGoalsFor: 0, // Auswärtsholz
              awayGoalsAgainst: 0, // Gegnerisches Auswärtsholz
              avgHomeScore: 0,
              avgAwayScore: 0,
              avgStrength: data.avg_strength || 0
            }
          };

          setTeam(processedTeam);
          // Initialize the staerke value
          setStaerkeValue(data.staerke || 0);
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

  // Toggle functions for expanding/collapsing match lists
  const toggleUpcomingMatches = () => {
    setUpcomingMatchesExpanded(!upcomingMatchesExpanded);
  };

  const toggleRecentMatches = () => {
    setRecentMatchesExpanded(!recentMatchesExpanded);
  };

  // Function to handle editing team strength
  const handleEditStaerke = () => {
    setIsEditingStaerke(true);
  };

  // Function to handle saving team strength
  const handleSaveStaerke = async () => {
    setSavingStaerke(true);
    try {
      // Update the team strength via API
      const result = await updateTeam(id, { staerke: staerkeValue });

      // Update the local team data
      setTeam(prevTeam => ({
        ...prevTeam,
        staerke: staerkeValue
      }));

      setIsEditingStaerke(false);
      console.log('Team strength updated successfully:', result);
    } catch (error) {
      console.error('Error updating team strength:', error);
      // Revert to original value on error
      setStaerkeValue(team.staerke || 0);
    } finally {
      setSavingStaerke(false);
    }
  };

  // Function to handle canceling edit
  const handleCancelEdit = () => {
    setStaerkeValue(team.staerke || 0);
    setIsEditingStaerke(false);
  };

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
            <Link to={`/clubs/${team.club.id}`} className="btn btn-secondary">Zum Verein</Link>
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
              {/* Hauptinformationen */}
              <div className="overview-main-section">
                <div className="overview-card team-summary-card">
                  <h3>Mannschaftsübersicht</h3>
                  <div className="team-summary">
                    <div className="team-summary-stats">
                      <div className="summary-stat">
                        <div className="summary-stat-value">{team.stats.matches}</div>
                        <div className="summary-stat-label">Spiele</div>
                      </div>
                      <div className="summary-stat">
                        <div className="summary-stat-value">{team.stats.wins}</div>
                        <div className="summary-stat-label">Siege</div>
                      </div>
                      <div className="summary-stat">
                        <div className="summary-stat-value">{team.stats.draws}</div>
                        <div className="summary-stat-label">Unent.</div>
                      </div>
                      <div className="summary-stat">
                        <div className="summary-stat-value">{team.stats.losses}</div>
                        <div className="summary-stat-label">Niederl.</div>
                      </div>
                      <div className="summary-stat highlight">
                        <div className="summary-stat-value">{team.stats.points}</div>
                        <div className="summary-stat-label">Punkte</div>
                      </div>
                    </div>

                    <div className="team-record">
                      <div className="record-item">
                        <span className="record-label">Bilanz:</span>
                        <span className="record-value">
                          {team.stats.wins}-{team.stats.draws}-{team.stats.losses}
                        </span>
                      </div>
                      <div className="record-item">
                        <span className="record-label">Siegquote:</span>
                        <span className="record-value">
                          {team.stats.matches > 0
                            ? ((team.stats.wins / team.stats.matches) * 100).toFixed(1)
                            : '0.0'}%
                        </span>
                      </div>
                      <div className="record-item">
                        <span className="record-label">Heim:</span>
                        <span className="record-value">
                          {team.stats.homeMatches} Spiele
                        </span>
                      </div>
                      <div className="record-item">
                        <span className="record-label">Auswärts:</span>
                        <span className="record-value">
                          {team.stats.awayMatches} Spiele
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Zwei-Spalten-Layout für den Hauptinhalt */}
              <div className="overview-columns">
                <div className="overview-column">
                  {/* Kegelergebnisse */}
                  <div className="overview-card">
                    <h3>Kegelergebnisse</h3>
                    <div className="bowling-stats">
                      <div className="bowling-stat-row">
                        <div className="bowling-stat-label">Gesamtholz:</div>
                        <div className="bowling-stat-value">{team.stats.goalsFor}</div>
                      </div>
                      <div className="bowling-stat-row">
                        <div className="bowling-stat-label">Gegnerisches Holz:</div>
                        <div className="bowling-stat-value">{team.stats.goalsAgainst}</div>
                      </div>
                      <div className="bowling-stat-row highlight">
                        <div className="bowling-stat-label">Holzdifferenz:</div>
                        <div className="bowling-stat-value">{team.stats.goalsFor - team.stats.goalsAgainst}</div>
                      </div>
                      <div className="bowling-stat-row">
                        <div className="bowling-stat-label">Ø Holz pro Spiel:</div>
                        <div className="bowling-stat-value">
                          {team.stats.matches > 0
                            ? (team.stats.goalsFor / team.stats.matches).toFixed(1)
                            : '0.0'}
                        </div>
                      </div>
                      <div className="bowling-stat-row">
                        <div className="bowling-stat-label">Ø Holz pro Spieler:</div>
                        <div className="bowling-stat-value">
                          {team.stats.matches > 0
                            ? (team.stats.goalsFor / (team.stats.matches * 6)).toFixed(1)
                            : '0.0'}
                        </div>
                      </div>
                    </div>

                    <h4>Heim vs. Auswärts</h4>
                    <div className="home-away-comparison">
                      <div className="comparison-item">
                        <div className="comparison-label">Ø Heimergebnis</div>
                        <div className="comparison-value">{team.stats.avgHomeScore?.toFixed(1) || '0.0'}</div>
                        <div className="comparison-bar">
                          <div
                            className="comparison-fill home"
                            style={{
                              width: `${team.stats.homeMatches > 0
                                ? (team.stats.avgHomeScore / 10) * 100
                                : 0}%`
                            }}
                          ></div>
                        </div>
                      </div>
                      <div className="comparison-item">
                        <div className="comparison-label">Ø Auswärtsergebnis</div>
                        <div className="comparison-value">{team.stats.avgAwayScore?.toFixed(1) || '0.0'}</div>
                        <div className="comparison-bar">
                          <div
                            className="comparison-fill away"
                            style={{
                              width: `${team.stats.awayMatches > 0
                                ? (team.stats.avgAwayScore / 10) * 100
                                : 0}%`
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Mannschaftsstärke */}
                  <div className="overview-card">
                    <h3>Mannschaftsstärke</h3>
                    <div className="team-strength-display">
                      <div className="strength-value">{Math.floor(team.stats.avgStrength)}</div>
                      <div className="strength-bar-container">
                        <div className="strength-bar large">
                          <div
                            className="strength-fill"
                            style={{ width: `${team.stats.avgStrength}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>

                    <div className="team-attributes">
                      <div className="attribute-item">
                        <div className="attribute-label">Team-Stärke-Bonus:</div>
                        <div className="attribute-value">
                          {isEditingStaerke ? (
                            <div className="staerke-edit">
                              <input
                                type="number"
                                min="0"
                                max="20"
                                value={staerkeValue}
                                onChange={(e) => setStaerkeValue(parseInt(e.target.value) || 0)}
                                className="staerke-input"
                              />
                              <div className="edit-buttons">
                                <button
                                  onClick={handleSaveStaerke}
                                  disabled={savingStaerke}
                                  className="btn btn-small btn-save"
                                >
                                  {savingStaerke ? 'Speichern...' : 'Speichern'}
                                </button>
                                <button
                                  onClick={handleCancelEdit}
                                  className="btn btn-small btn-cancel"
                                >
                                  Abbrechen
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="staerke-display">
                              <span>{team.staerke || 0}</span>
                              <button
                                onClick={handleEditStaerke}
                                className="btn btn-small btn-edit"
                              >
                                Bearbeiten
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="attribute-item">
                        <div className="attribute-label">Trainingseinrichtungen:</div>
                        <div className="attribute-value">
                          {team.club && team.club.training_facilities
                            ? `${team.club.training_facilities}/100`
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="attribute-item">
                        <div className="attribute-label">Trainerqualität:</div>
                        <div className="attribute-value">
                          {team.club && team.club.coaching
                            ? `${team.club.coaching}/100`
                            : 'N/A'}
                        </div>
                      </div>
                      <div className="attribute-item">
                        <div className="attribute-label">Fans:</div>
                        <div className="attribute-value">
                          {team.club && team.club.fans
                            ? team.club.fans.toLocaleString('de-DE')
                            : 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Nächste Spiele */}
                  <div className="overview-card">
                    <div className="card-header">
                      <h3>Nächste Spiele</h3>
                      {team.upcomingMatches.length > 5 && (
                        <button
                          className="expand-button"
                          onClick={toggleUpcomingMatches}
                        >
                          {upcomingMatchesExpanded ? 'Einklappen' : 'Ausklappen'}
                        </button>
                      )}
                    </div>
                    <div className="matches-list">
                      {team.upcomingMatches.length > 0 ? (
                        team.upcomingMatches
                          .filter(match => match.visible || upcomingMatchesExpanded)
                          .map(match => (
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
                          ))
                      ) : (
                        <div className="no-matches-message">Keine anstehenden Spiele</div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="overview-column">
                  {/* Top Spieler */}
                  <div className="overview-card">
                    <h3>Spielerkader</h3>
                    <div className="player-roster">
                      {team.players
                        .sort((a, b) => b.strength - a.strength)
                        .map((player, index) => (
                          <Link to={`/players/${player.id}`} key={player.id} className="roster-player">
                            <div className="player-rank">{index + 1}</div>
                            <div className="player-info-container">
                              <div className="player-name-age">
                                <span className="player-name">{player.name}</span>
                                <span className="player-age">{player.age} Jahre</span>
                              </div>
                              <div className="player-attributes">
                                <div className="player-attribute">
                                  <span className="attribute-label">Stärke:</span>
                                  <span className="attribute-value">{Math.floor(player.strength)}</span>
                                </div>
                                <div className="player-attribute">
                                  <span className="attribute-label">Volle:</span>
                                  <span className="attribute-value">{Math.floor(player.volle)}</span>
                                </div>
                                <div className="player-attribute">
                                  <span className="attribute-label">Räumer:</span>
                                  <span className="attribute-value">{Math.floor(player.raeumer)}</span>
                                </div>
                              </div>
                            </div>
                            <div
                              className="player-strength-indicator"
                              style={{
                                height: `${(player.strength / 100) * 100}%`,
                                backgroundColor: `hsl(${120 * (player.strength / 100)}, 70%, 45%)`
                              }}
                            ></div>
                          </Link>
                        ))}
                    </div>
                  </div>

                  {/* Letzte Ergebnisse */}
                  <div className="overview-card">
                    <div className="card-header">
                      <h3>Letzte Ergebnisse</h3>
                      {team.recentMatches.length > 5 && (
                        <button
                          className="expand-button"
                          onClick={toggleRecentMatches}
                        >
                          {recentMatchesExpanded ? 'Einklappen' : 'Ausklappen'}
                        </button>
                      )}
                    </div>
                    <div className="matches-list">
                      {team.recentMatches.length > 0 ? (
                        team.recentMatches
                          .filter(match => match.visible || recentMatchesExpanded)
                          .map(match => (
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
                          ))
                      ) : (
                        <div className="no-matches-message">Keine vergangenen Spiele</div>
                      )}
                    </div>
                  </div>

                  {/* Formkurve (Placeholder für zukünftige Implementierung) */}
                  <div className="overview-card">
                    <h3>Formkurve</h3>
                    <div className="form-chart">
                      <div className="chart-placeholder">
                        Hier wird die Formkurve der Mannschaft angezeigt, sobald genügend Spiele absolviert wurden.
                      </div>
                    </div>
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
                          <span>{Math.floor(player.strength)}</span>
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
              <div className="section-header">
                <h3>Nächste Spiele</h3>
                {team.upcomingMatches.length > 5 && (
                  <button
                    className="expand-button"
                    onClick={toggleUpcomingMatches}
                  >
                    {upcomingMatchesExpanded ? 'Einklappen' : 'Ausklappen'}
                  </button>
                )}
              </div>
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
                  {team.upcomingMatches
                    .filter(match => match.visible || upcomingMatchesExpanded)
                    .map(match => (
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

              <div className="section-header">
                <h3>Letzte Ergebnisse</h3>
                {team.recentMatches.length > 5 && (
                  <button
                    className="expand-button"
                    onClick={toggleRecentMatches}
                  >
                    {recentMatchesExpanded ? 'Einklappen' : 'Ausklappen'}
                  </button>
                )}
              </div>
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
                  {team.recentMatches
                    .filter(match => match.visible || recentMatchesExpanded)
                    .map(match => (
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
                    <span className="stat-label">Siegquote:</span>
                    <span className="stat-value">{((team.stats.wins / team.stats.matches) * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              <div className="stats-section">
                <h3>Kegelergebnisse</h3>
                <div className="stats-grid detailed">
                  <div className="stat-item">
                    <span className="stat-label">Gesamtholz:</span>
                    <span className="stat-value">{team.stats.goalsFor}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Gegnerisches Holz:</span>
                    <span className="stat-value">{team.stats.goalsAgainst}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Holzdifferenz:</span>
                    <span className="stat-value">{team.stats.goalsFor - team.stats.goalsAgainst}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Ø Holz pro Spiel:</span>
                    <span className="stat-value">{(team.stats.goalsFor / team.stats.matches).toFixed(1)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Ø Gegnerholz pro Spiel:</span>
                    <span className="stat-value">{(team.stats.goalsAgainst / team.stats.matches).toFixed(1)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Ø Holz pro Spieler:</span>
                    <span className="stat-value">{(team.stats.goalsFor / (team.stats.matches * 6)).toFixed(1)}</span>
                  </div>
                </div>
              </div>

              <div className="stats-section">
                <h3>Heim- vs. Auswärtsstatistiken</h3>
                <div className="stats-grid detailed">
                  <div className="stat-item">
                    <span className="stat-label">Heimspiele:</span>
                    <span className="stat-value">{team.stats.homeMatches}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Auswärtsspiele:</span>
                    <span className="stat-value">{team.stats.awayMatches}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Heimholz gesamt:</span>
                    <span className="stat-value">{team.stats.homeGoalsFor}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Auswärtsholz gesamt:</span>
                    <span className="stat-value">{team.stats.awayGoalsFor}</span>
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
                    <span className="stat-label">Ø Heimholz pro Spieler:</span>
                    <span className="stat-value">
                      {team.stats.homeMatches > 0
                        ? (team.stats.homeGoalsFor / (team.stats.homeMatches * 6)).toFixed(1)
                        : '0.0'}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Ø Auswärtsholz pro Spieler:</span>
                    <span className="stat-value">
                      {team.stats.awayMatches > 0
                        ? (team.stats.awayGoalsFor / (team.stats.awayMatches * 6)).toFixed(1)
                        : '0.0'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="stats-section">
                <h3>Mannschaftsstärke</h3>
                <div className="stats-grid detailed">
                  <div className="stat-item">
                    <span className="stat-label">Ø Stärke:</span>
                    <div className="strength-display">
                      <div className="strength-bar">
                        <div
                          className="strength-fill"
                          style={{ width: `${team.stats.avgStrength}%` }}
                        ></div>
                      </div>
                      <span>{Math.floor(team.stats.avgStrength)}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="stats-section">
                <h3>Spielerstatistiken</h3>
                <table className="table statistics-table">
                  <thead>
                    <tr>
                      <th>Spieler</th>
                      <th>Spiele</th>
                      <th>Ø Gesamt</th>
                      <th>Ø Volle</th>
                      <th>Ø Räumer</th>
                      <th>Ø Fehler</th>
                      <th>MP-Quote</th>
                    </tr>
                  </thead>
                  <tbody>
                    {team.players
                      .filter(player => player.statistics && player.statistics.total_matches > 0)
                      .sort((a, b) => {
                        // Sortiere nach Anzahl der Spiele (absteigend)
                        const matchesA = a.statistics?.total_matches || 0;
                        const matchesB = b.statistics?.total_matches || 0;
                        if (matchesB !== matchesA) return matchesB - matchesA;

                        // Bei gleicher Spielanzahl nach Durchschnitt (absteigend)
                        const avgA = a.statistics?.avg_total_score || 0;
                        const avgB = b.statistics?.avg_total_score || 0;
                        return avgB - avgA;
                      })
                      .map(player => {
                        const stats = player.statistics || {};
                        return (
                          <tr key={player.id} className={player.is_substitute ? 'substitute-player' : ''}>
                            <td>
                              <Link to={`/players/${player.id}`} className="player-name-link">
                                {player.name}
                                {player.is_substitute && <span className="substitute-badge" title="Aushilfsspieler"> (A)</span>}
                              </Link>
                              {player.club_id !== team.club_id && (
                                <div className="player-club">{player.club_name}</div>
                              )}
                            </td>
                            <td>{stats.total_matches || 0}</td>
                            <td>{stats.avg_total_score?.toFixed(1) || '0.0'}</td>
                            <td>{stats.avg_total_volle?.toFixed(1) || '0.0'}</td>
                            <td>{stats.avg_total_raeumer?.toFixed(1) || '0.0'}</td>
                            <td>{stats.avg_total_fehler?.toFixed(1) || '0.0'}</td>
                            <td>{stats.mp_win_percentage?.toFixed(1) || '0.0'}%</td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>

              <div className="stats-section">
                <h3>Saisonverlauf</h3>
                <div className="stats-grid detailed">
                  <div className="stat-item full-width">
                    <div className="chart-placeholder">
                      [Hier würde ein Saisonverlauf-Chart mit Holzergebnissen angezeigt werden]
                    </div>
                  </div>
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
