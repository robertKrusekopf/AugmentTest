import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAppContext } from '../contexts/AppContext';
import { getLeague } from '../services/api';
import './Leagues.css';

const Leagues = () => {
  const { getLeagues } = useAppContext();
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingLeague, setLoadingLeague] = useState(false);
  const [activeTab, setActiveTab] = useState('standings');
  const [selectedStat, setSelectedStat] = useState('avg_score'); // Default statistic is average score

  // Lade Daten aus dem Context (mit Caching)
  useEffect(() => {
    const loadLeagues = async () => {
      try {
        console.log('Lade Ligen aus dem Context...');
        setLoading(true);

        const data = await getLeagues();

        // Wenn keine Daten zurückgegeben werden, verwende leere Liste
        if (!data || data.length === 0) {
          console.warn('Keine Ligen in der Datenbank gefunden.');
          setLeagues([]);
        } else {
          // Verarbeite die Daten und füge fehlende Eigenschaften hinzu
          const processedLeagues = data.map(league => {
            // Stelle sicher, dass alle benötigten Eigenschaften vorhanden sind
            return {
              id: league.id,
              name: league.name,
              level: league.level || 0,
              teams: league.teams ? league.teams.length : 0
            };
          });

          setLeagues(processedLeagues);

          // Wenn Ligen vorhanden sind, lade automatisch die erste Liga
          if (processedLeagues.length > 0) {
            loadLeagueDetails(processedLeagues[0].id);
          }
        }
      } catch (error) {
        console.error('Fehler beim Laden der Ligen:', error);
      } finally {
        setLoading(false);
      }
    };

    loadLeagues();
  }, [getLeagues]);

  // Funktion zum Laden der Details einer Liga
  const loadLeagueDetails = (leagueId) => {
    setLoadingLeague(true);

    getLeague(leagueId)
      .then(data => {
        console.log('Geladene Liga-Details:', data);

        if (data) {
          // Verarbeite die Daten
          const processedLeague = {
            ...data,
            teams: data.teams_info || [],
            standings: data.standings || [],
            fixtures: data.fixtures || [],
            stats: data.stats || {
              topScorers: [],
              teamStats: []
            }
          };

          // Erstelle Tabellenstände für die Teams in der Liga nur wenn keine Standings aus der API kommen
          if (!data.standings && data.teams_info && data.teams_info.length > 0) {
            console.log('Keine Standings aus der API, erstelle Dummy-Standings');
            processedLeague.standings = data.teams_info.map((team, index) => {
              return {
                position: index + 1,
                team_id: team.id,
                team: team.name,
                club_name: team.club_name || 'Unbekannt',
                emblem_url: team.emblem_url,
                played: 0,
                won: 0,
                drawn: 0,
                lost: 0,
                points: 0
              };
            });
          }

          setSelectedLeague(processedLeague);
        }

        setLoadingLeague(false);
      })
      .catch(error => {
        console.error(`Fehler beim Laden der Liga ${leagueId}:`, error);
        setLoadingLeague(false);
      });
  };

  // Handler für die Änderung der ausgewählten Liga
  const handleLeagueChange = (e) => {
    const leagueId = parseInt(e.target.value);
    if (leagueId) {
      loadLeagueDetails(leagueId);
    } else {
      setSelectedLeague(null);
    }
  };

  if (loading) {
    return <div className="loading">Lade Ligen...</div>;
  }

  return (
    <div className="leagues-page">
      <h1 className="page-title">Ligen</h1>

      <div className="league-selector">
        <select
          className="league-dropdown"
          onChange={handleLeagueChange}
          value={selectedLeague?.id || ''}
        >
          <option value="">-- Liga auswählen --</option>
          {leagues.map(league => (
            <option key={league.id} value={league.id}>
              {league.name} (Level {league.level})
            </option>
          ))}
        </select>
      </div>

      {loadingLeague ? (
        <div className="loading">Lade Liga-Details...</div>
      ) : selectedLeague ? (
        <div className="league-profile card">
          <div className="league-header">
            <div className="league-title">
              <h1 className="league-name">{selectedLeague.name}</h1>
              <div className="league-meta">
                <span className="league-season">{selectedLeague.season}</span>
                <span className="league-level">Level: {selectedLeague.level}</span>
                <span className="league-teams">Teams: {selectedLeague.teams.length}</span>
              </div>
            </div>

            <div className="league-actions">
              <button className="btn btn-primary">Spieltag simulieren</button>
            </div>
          </div>

          <div className="league-tabs">
            <div
              className={`tab ${activeTab === 'standings' ? 'active' : ''}`}
              onClick={() => setActiveTab('standings')}
            >
              Tabelle
            </div>
            <div
              className={`tab ${activeTab === 'fixtures' ? 'active' : ''}`}
              onClick={() => setActiveTab('fixtures')}
            >
              Spielplan
            </div>
            <div
              className={`tab ${activeTab === 'stats' ? 'active' : ''}`}
              onClick={() => setActiveTab('stats')}
            >
              Statistiken
            </div>
            <div
              className={`tab ${activeTab === 'teams' ? 'active' : ''}`}
              onClick={() => setActiveTab('teams')}
            >
              Teams
            </div>
          </div>

          <div className="league-content">
            {activeTab === 'standings' && (
              <div className="standings-tab">
                <table className="table standings-table">
                  <thead>
                    <tr>
                      <th>Pos</th>
                      <th>Team</th>
                      <th>Sp</th>
                      <th>S</th>
                      <th>U</th>
                      <th>N</th>
                      <th>Pkt</th>
                      <th>Ø Heim</th>
                      <th>Ø Ausw</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedLeague.standings.map(team => (
                      <tr key={team.position} className={
                        team.position <= 2 ? 'promotion-zone' :
                        team.position >= selectedLeague.standings.length - 1 ? 'relegation-zone' : ''
                      }>
                        <td>{team.position}</td>
                        <td>
                          <Link to={`/teams/${team.team_id}`} className="team-link">
                            <div className="club-row-info">
                              {team.emblem_url ? (
                                <img
                                  src={team.emblem_url}
                                  alt={`${team.team} Wappen`}
                                  className="club-emblem-small"
                                  onError={(e) => {
                                    console.log(`Fehler beim Laden des Emblems für ${team.team}:`, e);
                                    e.target.style.display = 'none';
                                  }}
                                />
                              ) : null}
                              <span>{team.team}</span>
                            </div>
                          </Link>
                        </td>
                        <td>{team.played}</td>
                        <td>{team.won}</td>
                        <td>{team.drawn}</td>
                        <td>{team.lost}</td>
                        <td><strong>{team.points}</strong></td>
                        <td>{team.avg_home_score}</td>
                        <td>{team.avg_away_score}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div className="standings-legend">
                  <div className="legend-item promotion">
                    <div className="legend-color"></div>
                    <span>Aufstiegsplätze</span>
                  </div>
                  <div className="legend-item relegation">
                    <div className="legend-color"></div>
                    <span>Abstiegsplätze</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'fixtures' && (
              <div className="fixtures-tab">
                {selectedLeague.fixtures && selectedLeague.fixtures.length > 0 ? (
                  selectedLeague.fixtures.map(matchDay => (
                    <div key={matchDay.match_day} className="fixture-round">
                      <h3 className="round-title">
                        Spieltag {matchDay.match_day}
                        {matchDay.matches[0]?.round === 1 ? ' (Hinrunde)' : ' (Rückrunde)'}
                      </h3>
                      <div className="matches-list">
                        {matchDay.matches.map(match => (
                          <Link to={`/matches/${match.id}`} key={match.id} className="match-item">
                            <div className="match-date">
                              {match.date ? new Date(match.date).toLocaleDateString('de-DE', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              }) : 'Datum nicht festgelegt'}
                            </div>
                            <div className="match-teams">
                              <div className="team home">
                                {match.home_emblem_url && (
                                  <img
                                    src={match.home_emblem_url}
                                    alt={`${match.home_team} Wappen`}
                                    className="team-emblem-small"
                                    onError={(e) => {
                                      e.target.style.display = 'none';
                                    }}
                                  />
                                )}
                                <span>{match.home_team}</span>
                              </div>
                              {match.played ? (
                                <span className="score">{match.home_score} - {match.away_score}</span>
                              ) : (
                                <span className="vs">vs</span>
                              )}
                              <div className="team away">
                                <span>{match.away_team}</span>
                                {match.away_emblem_url && (
                                  <img
                                    src={match.away_emblem_url}
                                    alt={`${match.away_team} Wappen`}
                                    className="team-emblem-small"
                                    onError={(e) => {
                                      e.target.style.display = 'none';
                                    }}
                                  />
                                )}
                              </div>
                            </div>
                            <div className="match-status">
                              {match.played ? (
                                <span className="badge badge-success">Gespielt</span>
                              ) : (
                                <span className="badge">Anstehend</span>
                              )}
                            </div>
                          </Link>
                        ))}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-fixtures">
                    <p>Keine Spielpläne verfügbar.</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'stats' && (
              <div className="stats-tab">
                <div className="stats-grid">
                  <div className="stats-card full-width">
                    <h3>Spielerstatistiken</h3>
                    <div className="stats-controls">
                      <label htmlFor="stat-select">Statistik auswählen:</label>
                      <select
                        id="stat-select"
                        value={selectedStat}
                        onChange={(e) => setSelectedStat(e.target.value)}
                        className="stat-select"
                      >
                        <option value="avg_score">Gesamtschnitt</option>
                        <option value="avg_home_score">Heimschnitt</option>
                        <option value="avg_away_score">Auswärtsschnitt</option>
                        <option value="avg_volle">Volle-Schnitt</option>
                        <option value="avg_raeumer">Räumer-Schnitt</option>
                        <option value="avg_fehler">Fehler-Schnitt</option>
                        <option value="mp_win_percentage">MP-Gewinnquote (%)</option>
                      </select>
                    </div>

                    {selectedLeague.player_statistics && selectedLeague.player_statistics.length > 0 ? (
                      <table className="table stats-table">
                        <thead>
                          <tr>
                            <th>Rang</th>
                            <th>Spieler</th>
                            <th>Team</th>
                            <th>Spiele</th>
                            <th>
                              {selectedStat === 'avg_score' && 'Gesamtschnitt'}
                              {selectedStat === 'avg_home_score' && 'Heimschnitt'}
                              {selectedStat === 'avg_away_score' && 'Auswärtsschnitt'}
                              {selectedStat === 'avg_volle' && 'Volle-Schnitt'}
                              {selectedStat === 'avg_raeumer' && 'Räumer-Schnitt'}
                              {selectedStat === 'avg_fehler' && 'Fehler-Schnitt'}
                              {selectedStat === 'mp_win_percentage' && 'MP-Gewinnquote (%)'}
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {[...selectedLeague.player_statistics]
                            .sort((a, b) => {
                              // Für Fehler-Schnitt sortieren wir aufsteigend (weniger ist besser)
                              if (selectedStat === 'avg_fehler') {
                                return a[selectedStat] - b[selectedStat];
                              }
                              // Für alle anderen Statistiken sortieren wir absteigend (mehr ist besser)
                              return b[selectedStat] - a[selectedStat];
                            })
                            .map((player, index) => (
                              <tr key={player.player_id}>
                                <td>{index + 1}</td>
                                <td>
                                  <Link to={`/players/${player.player_id}`}>
                                    {player.player_name}
                                  </Link>
                                </td>
                                <td>
                                  <Link to={`/teams/${player.team_id}`}>
                                    {player.team_name}
                                  </Link>
                                </td>
                                <td>{player.matches}</td>
                                <td>{player[selectedStat]}</td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    ) : (
                      <div className="no-stats">
                        <p>Keine Spielerstatistiken verfügbar. Spieler müssen erst Spiele in dieser Liga absolvieren.</p>
                      </div>
                    )}
                  </div>

                  <div className="stats-card">
                    <h3>Top Scorer</h3>
                    <table className="table stats-table">
                      <thead>
                        <tr>
                          <th>Spieler</th>
                          <th>Team</th>
                          <th>Punkte</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedLeague.stats.topScorers && selectedLeague.stats.topScorers.length > 0 ? (
                          selectedLeague.stats.topScorers.map((player, index) => (
                            <tr key={index}>
                              <td>{player.player}</td>
                              <td>{player.team}</td>
                              <td>{player.score}</td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="3">Keine Daten verfügbar</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  <div className="stats-card">
                    <h3>Team Statistiken</h3>
                    <table className="table stats-table">
                      <thead>
                        <tr>
                          <th>Team</th>
                          <th>Spiele</th>
                          <th>Ø Punkte</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedLeague.stats.teamStats && selectedLeague.stats.teamStats.length > 0 ? (
                          selectedLeague.stats.teamStats.map((team, index) => (
                            <tr key={index}>
                              <td>{team.team}</td>
                              <td>{team.matches}</td>
                              <td>{typeof team.avgScore === 'number' ? team.avgScore.toFixed(1) : '0.0'}</td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="3">Keine Daten verfügbar</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'teams' && (
              <div className="teams-tab">
                <div className="teams-grid">
                  {selectedLeague.teams.map(team => (
                    <Link to={`/teams/${team.id}`} key={team.id} className="team-card">
                      <div className="team-logo">
                        {team.emblem_url ? (
                          <img
                            src={team.emblem_url}
                            alt={`${team.name} Wappen`}
                            className="club-emblem"
                            onError={(e) => {
                              console.log(`Fehler beim Laden des Emblems für ${team.name}:`, e);
                              e.target.style.display = 'none';
                              e.target.parentNode.innerHTML = `<span>${team.name.split(' ').map(word => word[0]).join('')}</span>`;
                            }}
                          />
                        ) : (
                          <span>{team.name.split(' ').map(word => word[0]).join('')}</span>
                        )}
                      </div>
                      <div className="team-info">
                        <h3 className="team-name">{team.name}</h3>
                        <div className="team-position">
                          {selectedLeague.standings.find(s => s.team_id === team.id)?.position || '?'}. Platz
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="no-league-selected">
          <p>Bitte wählen Sie eine Liga aus dem Dropdown-Menü aus.</p>
        </div>
      )}
    </div>
  );
};

export default Leagues;
