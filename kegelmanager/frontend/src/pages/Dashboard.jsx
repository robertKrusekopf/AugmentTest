import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getClub, getTeam, getMatch, getLeagues } from '../services/api';
import LineupSelector from '../components/LineupSelector';
import './Dashboard.css';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [managerClub, setManagerClub] = useState(null);
  const [firstTeam, setFirstTeam] = useState(null);
  const [teamLeague, setTeamLeague] = useState(null);
  const [recentMatches, setRecentMatches] = useState([]);
  const [upcomingMatches, setUpcomingMatches] = useState([]);
  const [lastMatch, setLastMatch] = useState(null);
  const [noClubSelected, setNoClubSelected] = useState(false);
  const [showLineupSelector, setShowLineupSelector] = useState(false);
  const [nextMatchId, setNextMatchId] = useState(null);
  const [managedClubId, setManagedClubId] = useState(null);

  // Lade Daten des gemanagten Vereins
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        console.log('Lade Dashboard-Daten...');
        setLoading(true);

        // Lade die Manager-Einstellungen aus dem localStorage
        const savedSettings = localStorage.getItem('gameSettings');
        let managerClubId = null;

        if (savedSettings) {
          try {
            const settings = JSON.parse(savedSettings);
            managerClubId = settings.game?.managerClubId || null;
            setManagedClubId(managerClubId); // Speichere die Club-ID für spätere Verwendung
          } catch (e) {
            console.error('Failed to parse saved settings:', e);
          }
        }

        // Wenn kein Verein ausgewählt wurde, zeige eine entsprechende Meldung
        if (!managerClubId) {
          setNoClubSelected(true);
          setLoading(false);
          return;
        }

        // Lade den Verein des Managers
        const clubData = await getClub(managerClubId);
        setManagerClub(clubData);

        // Finde die erste Mannschaft des Vereins (nicht Jugendmannschaft)
        if (clubData.teams_info && clubData.teams_info.length > 0) {
          // Sortiere Teams nach Jugendmannschaft (erst Erwachsenenteams)
          const sortedTeams = [...clubData.teams_info].sort((a, b) => {
            if (a.is_youth_team && !b.is_youth_team) return 1;
            if (!a.is_youth_team && b.is_youth_team) return -1;
            return 0;
          });

          const firstTeamInfo = sortedTeams[0];

          if (firstTeamInfo) {
            // Lade detaillierte Informationen über die erste Mannschaft
            const teamData = await getTeam(firstTeamInfo.id);
            setFirstTeam(teamData);

            // Setze die letzten und nächsten Spiele
            if (teamData.recentMatches) {
              setRecentMatches(teamData.recentMatches);

              // Setze das letzte Spiel für die Detailansicht
              if (teamData.recentMatches.length > 0) {
                const lastMatchData = await getMatch(teamData.recentMatches[0].id);
                setLastMatch(lastMatchData);
              }
            }

            if (teamData.upcomingMatches && teamData.upcomingMatches.length > 0) {
              setUpcomingMatches(teamData.upcomingMatches);
              // Speichere die ID des nächsten Spiels
              setNextMatchId(teamData.upcomingMatches[0].id);
            }

            // Lade die Liga der ersten Mannschaft
            if (teamData.league_id) {
              const leagues = await getLeagues();
              const teamLeague = leagues.find(league => league.id === teamData.league_id);
              setTeamLeague(teamLeague);
            }
          }
        }

        setLoading(false);
      } catch (error) {
        console.error('Fehler beim Laden der Dashboard-Daten:', error);
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // Handler für das Öffnen des Aufstellungs-Selektors
  const handleOpenLineupSelector = () => {
    setShowLineupSelector(true);
  };

  // Handler für das Schließen des Aufstellungs-Selektors
  const handleCloseLineupSelector = () => {
    setShowLineupSelector(false);
  };

  // Handler für das Speichern der Aufstellung
  const handleSaveLineup = () => {
    setShowLineupSelector(false);
    // Lade die Dashboard-Daten neu, um die aktualisierte Aufstellung anzuzeigen
    window.location.reload();
  };

  if (loading) {
    return <div className="loading">Lade Dashboard...</div>;
  }

  // Wenn kein Verein ausgewählt wurde, zeige eine entsprechende Meldung
  if (noClubSelected) {
    return (
      <div className="dashboard">
        <h1 className="page-title">Dashboard</h1>
        <div className="no-club-message">
          <div className="no-club-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
          </div>
          <h2>Kein Verein ausgewählt</h2>
          <p>Sie haben derzeit keinen Verein ausgewählt, den Sie managen möchten.</p>
          <p>Gehen Sie zu <Link to="/settings">Einstellungen</Link>, um einen Verein auszuwählen.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h1 className="page-title">
        {managerClub?.name || 'Dashboard'}
        {managerClub?.emblem_url && (
          <img
            src={managerClub.emblem_url}
            alt={`${managerClub.name} Wappen`}
            className="club-emblem-medium"
            onError={(e) => {
              console.log(`Fehler beim Laden des Emblems für ${managerClub.name}:`, e);
              e.target.style.display = 'none';
            }}
          />
        )}
      </h1>

      {firstTeam && (
        <div className="dashboard-stats">
          <div className="stat-card">
            <h3>Erste Mannschaft</h3>
            <div className="value">{firstTeam.name}</div>
            <div className="change">
              <span>{firstTeam.league?.name || 'Keine Liga'}</span>
            </div>
          </div>

          <div className="stat-card">
            <h3>Spieler</h3>
            <div className="value">{firstTeam.players?.length || 0}</div>
            <div className="change">
              <span>Ø Stärke: {firstTeam.avg_strength || '-'}</span>
            </div>
          </div>

          <div className="stat-card">
            <h3>Tabellenplatz</h3>
            <div className="value">
              {teamLeague?.standings?.find(team => team.team_id === firstTeam.id)?.position || '-'}
            </div>
            <div className="change">
              <span>von {teamLeague?.standings?.length || '-'} Teams</span>
            </div>
          </div>

          <div className="stat-card">
            <h3>Nächstes Spiel</h3>
            <div className="value">
              {upcomingMatches && upcomingMatches.length > 0 ? (
                <Link to={`/matches/${upcomingMatches[0].id}`}>
                  {upcomingMatches[0].is_home ?
                    `vs ${upcomingMatches[0].opponent_name}` :
                    `@ ${upcomingMatches[0].opponent_name}`}
                </Link>
              ) : '-'}
            </div>
            <div className="change">
              <span>
                {upcomingMatches && upcomingMatches.length > 0 && upcomingMatches[0].match_date ?
                  new Date(upcomingMatches[0].match_date).toLocaleDateString() :
                  'Kein Spiel geplant'}
              </span>
            </div>
            {upcomingMatches && upcomingMatches.length > 0 && managedClubId && (
              <div className="card-actions">
                <button
                  className="btn btn-primary btn-sm"
                  onClick={handleOpenLineupSelector}
                >
                  Aufstellung festlegen
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="dashboard-row">
        <div className="card league-standings">
          <div className="card-header">
            <h2>{teamLeague ? `${teamLeague.name} - Tabelle` : 'Tabelle'}</h2>
            {teamLeague && <Link to={`/leagues/${teamLeague.id}`} className="btn btn-secondary">Alle anzeigen</Link>}
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Pos</th>
                <th>Verein</th>
                <th>Sp</th>
                <th>S</th>
                <th>U</th>
                <th>N</th>
                <th>Pkt</th>
              </tr>
            </thead>
            <tbody>
              {teamLeague && teamLeague.standings && teamLeague.standings.map((team) => {
                // Hervorheben des eigenen Teams
                const isOwnTeam = firstTeam && team.team_id === firstTeam.id;
                return (
                  <tr key={team.team_id} className={isOwnTeam ? 'own-team' : ''}>
                    <td>{team.position}</td>
                    <td>
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
                    </td>
                    <td>{team.played}</td>
                    <td>{team.won}</td>
                    <td>{team.drawn}</td>
                    <td>{team.lost}</td>
                    <td>{team.points}</td>
                  </tr>
                );
              })}
              {(!teamLeague || !teamLeague.standings || teamLeague.standings.length === 0) && (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center' }}>Keine Tabellendaten gefunden</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="card upcoming-matches">
          <div className="card-header">
            <h2>Nächste Spiele</h2>
            {firstTeam && <Link to={`/teams/${firstTeam.id}`} className="btn btn-secondary">Alle anzeigen</Link>}
          </div>
          <div className="match-list">
            {upcomingMatches && upcomingMatches.length > 0 ? upcomingMatches.slice(0, 4).map((match, index) => {
              const matchDate = match.match_date ? new Date(match.match_date).toLocaleDateString() : 'TBD';
              const isHome = match.is_home;

              return (
                <div className="match-item" key={match.id || index}>
                  <div className="match-date">{matchDate}</div>
                  <div className="match-teams">
                    <span className={`team ${isHome ? 'home' : ''}`}>{isHome ? firstTeam.name : match.opponent_name}</span>
                    <span className="vs">vs</span>
                    <span className={`team ${!isHome ? 'home' : ''}`}>{!isHome ? firstTeam.name : match.opponent_name}</span>
                  </div>
                  <div className="match-league">{match.league_name || 'Unbekannte Liga'}</div>
                </div>
              );
            }) : (
              <div className="match-item">
                <div className="match-date">Keine Spiele geplant</div>
                <div className="match-teams">
                  <span className="team home">-</span>
                  <span className="vs">vs</span>
                  <span className="team away">-</span>
                </div>
                <div className="match-league">-</div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="dashboard-row">
        <div className="card recent-matches">
          <div className="card-header">
            <h2>Letzte Spiele</h2>
            {firstTeam && <Link to={`/teams/${firstTeam.id}`} className="btn btn-secondary">Alle anzeigen</Link>}
          </div>
          <div className="match-list">
            {recentMatches && recentMatches.length > 0 ? recentMatches.slice(0, 4).map((match, index) => {
              const matchDate = match.match_date ? new Date(match.match_date).toLocaleDateString() : 'TBD';
              const isHome = match.is_home;
              const result = match.result || '';
              const isWin = result.includes('W');
              const isDraw = result.includes('D');
              const isLoss = result.includes('L');

              return (
                <div className="match-item" key={match.id || index}>
                  <div className="match-date">{matchDate}</div>
                  <div className="match-teams">
                    <span className={`team ${isHome ? 'home' : ''}`}>{isHome ? firstTeam.name : match.opponent_name}</span>
                    <span className={`result ${isWin ? 'win' : isDraw ? 'draw' : isLoss ? 'loss' : ''}`}>
                      {match.score || '0:0'}
                    </span>
                    <span className={`team ${!isHome ? 'home' : ''}`}>{!isHome ? firstTeam.name : match.opponent_name}</span>
                  </div>
                  <div className="match-league">{match.league_name || 'Unbekannte Liga'}</div>
                </div>
              );
            }) : (
              <div className="match-item">
                <div className="match-date">Keine Spiele gespielt</div>
                <div className="match-teams">
                  <span className="team home">-</span>
                  <span className="vs">vs</span>
                  <span className="team away">-</span>
                </div>
                <div className="match-league">-</div>
              </div>
            )}
          </div>
        </div>

        <div className="card last-match-detail">
          <div className="card-header">
            <h2>Letztes Spiel</h2>
            {lastMatch && <Link to={`/matches/${lastMatch.id}`} className="btn btn-secondary">Details</Link>}
          </div>
          {lastMatch ? (
            <div className="last-match-content">
              <div className="match-header">
                <div className="match-teams-large">
                  <div className="team-info">
                    <span className="team-name">{lastMatch.home_team_name}</span>
                    {lastMatch.home_team_verein_id && (
                      <img
                        src={`/api/club-emblem/${lastMatch.home_team_verein_id}`}
                        alt={`${lastMatch.home_team_name} Wappen`}
                        className="team-emblem"
                      />
                    )}
                  </div>
                  <div className="match-score">
                    <span className="score">{lastMatch.home_match_points}</span>
                    <span className="separator">:</span>
                    <span className="score">{lastMatch.away_match_points}</span>
                  </div>
                  <div className="team-info">
                    <span className="team-name">{lastMatch.away_team_name}</span>
                    {lastMatch.away_team_verein_id && (
                      <img
                        src={`/api/club-emblem/${lastMatch.away_team_verein_id}`}
                        alt={`${lastMatch.away_team_name} Wappen`}
                        className="team-emblem"
                      />
                    )}
                  </div>
                </div>
                <div className="match-details">
                  <div className="match-date-large">
                    {lastMatch.match_date ? new Date(lastMatch.match_date).toLocaleDateString() : 'Unbekanntes Datum'}
                  </div>
                  <div className="match-league-large">{lastMatch.league_name}</div>
                </div>
              </div>
              <div className="match-stats">
                <div className="stat-row">
                  <span className="stat-label">Gesamtholz:</span>
                  <span className="stat-value">{lastMatch.home_score}</span>
                  <span className="stat-separator">:</span>
                  <span className="stat-value">{lastMatch.away_score}</span>
                </div>
                {lastMatch.performances && lastMatch.performances.length > 0 && (
                  <div className="player-performances">
                    <h4>Spieler-Leistungen</h4>
                    <div className="performances-list">
                      {lastMatch.performances.slice(0, 3).map((perf, index) => (
                        <div className="performance-item" key={index}>
                          <span className="player-name">{perf.player_name}</span>
                          <span className="player-score">{perf.total_score} Holz</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="no-match-data">
              <p>Keine Spieldaten verfügbar</p>
            </div>
          )}
        </div>
      </div>

      {/* Aufstellungs-Selektor anzeigen, wenn geöffnet */}
      {showLineupSelector && nextMatchId && (
        <div className="lineup-selector-overlay">
          <div className="lineup-selector-container">
            <LineupSelector
              matchId={nextMatchId}
              managedClubId={managedClubId}
              onSave={handleSaveLineup}
              onCancel={handleCloseLineupSelector}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
