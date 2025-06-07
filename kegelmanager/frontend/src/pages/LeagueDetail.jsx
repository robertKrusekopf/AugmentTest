import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getLeague, getLeagueHistory } from '../services/api';
import './LeagueDetail.css';

const LeagueDetail = () => {
  const { id } = useParams();
  const [league, setLeague] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('standings');
  const [selectedStat, setSelectedStat] = useState('avg_score'); // Default statistic is average score
  const [leagueHistory, setLeagueHistory] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [selectedHistorySeason, setSelectedHistorySeason] = useState('');

  // Lade Daten aus der API
  useEffect(() => {
    console.log(`Lade Liga mit ID ${id} aus der API...`);

    getLeague(id)
      .then(data => {
        console.log('Geladene Liga-Daten:', data);

        // Verarbeite die Daten
        if (data) {
          // Füge fehlende Eigenschaften hinzu, falls nötig
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
          } else {
            console.log('Standings aus der API:', data.standings);
          }

          setLeague(processedLeague);

          // Lade auch die Historie für diese Liga
          loadLeagueHistory(id);
        } else {
          console.error(`Keine Daten für Liga ${id} gefunden`);
        }

        setLoading(false);
      })
      .catch(error => {
        console.error(`Fehler beim Laden der Liga ${id}:`, error);
        setLoading(false);
      });
  }, [id]);

  // Funktion zum Laden der Liga-Historie
  const loadLeagueHistory = async (leagueId) => {
    if (!leagueId) return;

    console.log('Loading league history for league ID:', leagueId);
    setLoadingHistory(true);
    try {
      const historyData = await getLeagueHistory(leagueId);
      console.log('League history data received:', historyData);
      setLeagueHistory(historyData);

      // Setze die erste verfügbare Saison als Standard
      if (historyData.seasons && historyData.seasons.length > 0) {
        console.log('Setting default season:', historyData.seasons[0].season_id);
        setSelectedHistorySeason(historyData.seasons[0].season_id.toString());
      } else {
        console.log('No seasons found in history data');
      }
    } catch (error) {
      console.error('Fehler beim Laden der Liga-Historie:', error);
      setLeagueHistory(null);
    } finally {
      setLoadingHistory(false);
    }
  };

  if (loading) {
    return <div className="loading">Lade Ligadaten...</div>;
  }

  if (!league) {
    return <div className="error">Liga nicht gefunden</div>;
  }

  return (
    <div className="league-detail-page">
      <div className="page-header">
        <div className="breadcrumbs">
          <Link to="/leagues">Ligen</Link> / {league.name}
        </div>
      </div>

      <div className="league-profile card">
        <div className="league-header">
          <div className="league-title">
            <h1 className="league-name">{league.name}</h1>
            <div className="league-meta">
              <span className="league-season">{league.season}</span>
              <span className="league-level">Level: {league.level}</span>
              <span className="league-teams">Teams: {league.teams.length}</span>
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
          <div
            className={`tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            Historie
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
                  {league.standings.map(team => (
                    <tr key={team.position} className={
                      team.position <= 2 ? 'promotion-zone' :
                      team.position >= league.standings.length - 1 ? 'relegation-zone' : ''
                    }>
                      <td>{team.position}</td>
                      <td>
                        <Link to={`/teams/${team.team_id}`} className="team-link">
                          <div className="club-row-info">
                            {team.emblem_url ? (
                              <img
                                src={team.emblem_url}
                                alt={`${team.team_name_base || team.team} Wappen`}
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
              {league.fixtures && league.fixtures.length > 0 ? (
                league.fixtures.map(matchDay => (
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

                  {league.player_statistics && league.player_statistics.length > 0 ? (
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
                        {[...league.player_statistics]
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
                      {league.stats.topScorers && league.stats.topScorers.length > 0 ? (
                        league.stats.topScorers.map((player, index) => (
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
                      {league.stats.teamStats && league.stats.teamStats.length > 0 ? (
                        league.stats.teamStats.map((team, index) => (
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
                {league.teams.map(team => (
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
                        {league.standings.find(s => s.team_id === team.id)?.position || '?'}. Platz
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="history-tab">
              {loadingHistory ? (
                <div className="loading">Lade Historie...</div>
              ) : leagueHistory && leagueHistory.seasons && leagueHistory.seasons.length > 0 ? (
                <div className="history-content">
                  <div className="history-controls">
                    <label htmlFor="season-select">Saison auswählen:</label>
                    <select
                      id="season-select"
                      value={selectedHistorySeason}
                      onChange={(e) => setSelectedHistorySeason(e.target.value)}
                      className="season-select"
                    >
                      {leagueHistory.seasons.map(season => (
                        <option key={season.season_id} value={season.season_id}>
                          {season.season_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {selectedHistorySeason && (
                    <div className="historical-standings">
                      {(() => {
                        const selectedSeason = leagueHistory.seasons.find(
                          s => s.season_id.toString() === selectedHistorySeason
                        );

                        if (!selectedSeason) return null;

                        return (
                          <div>
                            <h3>Endtabelle {selectedSeason.season_name}</h3>
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
                                {selectedSeason.standings.map(team => (
                                  <tr key={team.position} className={
                                    team.position <= 2 ? 'promotion-zone' :
                                    team.position >= selectedSeason.standings.length - 1 ? 'relegation-zone' : ''
                                  }>
                                    <td>{team.position}</td>
                                    <td>
                                      <div className="club-row-info">
                                        {team.emblem_url ? (
                                          <img
                                            src={team.emblem_url}
                                            alt={`${team.team_name} Wappen`}
                                            className="club-emblem-small"
                                            onError={(e) => {
                                              e.target.style.display = 'none';
                                            }}
                                          />
                                        ) : null}
                                        <span>{team.team_name}</span>
                                      </div>
                                    </td>
                                    <td>{team.games_played}</td>
                                    <td>{team.wins}</td>
                                    <td>{team.draws}</td>
                                    <td>{team.losses}</td>
                                    <td><strong>{team.table_points}</strong></td>
                                    <td>{team.avg_home_score ? team.avg_home_score.toFixed(1) : '0.0'}</td>
                                    <td>{team.avg_away_score ? team.avg_away_score.toFixed(1) : '0.0'}</td>
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
                        );
                      })()}
                    </div>
                  )}
                </div>
              ) : (
                <div className="no-history">
                  <p>Keine historischen Daten verfügbar. Historische Tabellen werden nach dem ersten Saisonwechsel angezeigt.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LeagueDetail;
