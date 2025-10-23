import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getClub, getTeam, getMatch, getLeagues, getClubRecentMatches } from '../services/api';
import LineupSelector from '../components/LineupSelector';
import ClubEmblem from '../components/ClubEmblem';
import TeamLink from '../components/TeamLink';
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
  const [clubRecentMatches, setClubRecentMatches] = useState([]);

  // Funktion zum Laden der Dashboard-Daten (wiederverwendbar)
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
                // Merge the opponent emblem information from recent match data
                const recentMatchInfo = teamData.recentMatches[0];
                lastMatchData.opponent_emblem_url = recentMatchInfo.opponent_emblem_url;
                lastMatchData.opponent_club_id = recentMatchInfo.opponent_club_id;
                lastMatchData.opponent_club_name = recentMatchInfo.opponent_club_name;
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

        // Lade alle letzten Spiele aller Teams des Vereins
        if (managerClubId) {
          try {
            const clubMatchesData = await getClubRecentMatches(managerClubId);
            setClubRecentMatches(clubMatchesData.recent_matches || []);
          } catch (error) {
            console.error('Fehler beim Laden der Vereinsspiele:', error);
            setClubRecentMatches([]);
          }
        }

        setLoading(false);
      } catch (error) {
        console.error('Fehler beim Laden der Dashboard-Daten:', error);
        setLoading(false);
      }
    };

  // Lade Daten des gemanagten Vereins beim ersten Laden
  useEffect(() => {
    loadDashboardData();
  }, []);

  // Event-Listener für Simulation-Events
  useEffect(() => {
    const handleSimulationComplete = () => {
      console.log('Simulation completed, reloading dashboard data...');
      // Setze Loading-State, aber nicht für die gesamte Seite
      setLoading(false); // Behalte die Seite sichtbar
      loadDashboardData();
    };

    // Füge Event-Listener hinzu
    window.addEventListener('simulationComplete', handleSimulationComplete);

    // Cleanup beim Unmount
    return () => {
      window.removeEventListener('simulationComplete', handleSimulationComplete);
    };
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
        {managerClub && (
          <ClubEmblem
            emblemUrl={managerClub.emblem_url}
            clubName={managerClub.name}
            className="club-emblem-medium"
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
            <h3>Letztes Spiel</h3>
            <div className="value">
              {lastMatch ? (
                <Link to={`/matches/${lastMatch.id}`}>
                  {lastMatch.home_score} : {lastMatch.away_score}
                  <div style={{ fontSize: '16px', fontWeight: '500', marginTop: '4px' }}>
                    ({lastMatch.home_match_points} : {lastMatch.away_match_points} MP)
                  </div>
                </Link>
              ) : '-'}
            </div>
            <div className="change">
              <span>
                {lastMatch ? (
                  <div className="match-info-container">
                    <div className="match-opponent-info">
                      <span className={`home-away-indicator ${firstTeam && lastMatch.home_team_id === firstTeam.id ? 'home' : 'away'}`}>
                        {firstTeam && lastMatch.home_team_id === firstTeam.id ? 'H' : 'A'}
                      </span>
                      {lastMatch.opponent_emblem_url && (
                        <img
                          src={lastMatch.opponent_emblem_url}
                          alt="Gegner Wappen"
                          className="opponent-emblem-small"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                      <span className="opponent-name">
                        {firstTeam && lastMatch.home_team_id === firstTeam.id ?
                          `vs ${lastMatch.away_team_name}` :
                          `@ ${lastMatch.home_team_name}`}
                      </span>
                    </div>
                    {lastMatch.match_date && (
                      <div className="match-date">
                        {new Date(lastMatch.match_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                ) : 'Kein Spiel verfügbar'}
              </span>
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
                {upcomingMatches && upcomingMatches.length > 0 ? (
                  <div className="match-info-container">
                    <div className="match-opponent-info">
                      <span className={`home-away-indicator ${upcomingMatches[0].is_home ? 'home' : 'away'}`}>
                        {upcomingMatches[0].is_home ? 'H' : 'A'}
                      </span>
                      {upcomingMatches[0].opponent_emblem_url && (
                        <img
                          src={upcomingMatches[0].opponent_emblem_url}
                          alt="Gegner Wappen"
                          className="opponent-emblem-small"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                    </div>
                    {upcomingMatches[0].match_date && (
                      <div className="match-date">
                        {new Date(upcomingMatches[0].match_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                ) : 'Kein Spiel geplant'}
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
                      <TeamLink
                        teamId={team.team_id}
                        clubId={team.club_id}
                        teamName={team.team}
                      >
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
                      </TeamLink>
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

        <div className="card recent-matches">
          <div className="card-header">
            <h2>Letzte Spiele aller Teams</h2>
            {managerClub && <Link to={`/clubs/${managerClub.id}`} className="btn btn-secondary">Alle anzeigen</Link>}
          </div>
          <div className="match-list">
            {clubRecentMatches && clubRecentMatches.length > 0 ? clubRecentMatches.slice(0, 6).map((match, index) => {
              const matchDate = match.match_date ? new Date(match.match_date).toLocaleDateString() : 'TBD';
              const isHome = match.is_home;
              const homeScore = match.home_score || 0;
              const awayScore = match.away_score || 0;

              return (
                <Link
                  to={`/matches/${match.id}`}
                  className="match-item clickable"
                  key={match.id || index}
                >
                  <div className="match-date">{matchDate}</div>
                  <div className="match-teams">
                    <span className={`team ${isHome ? 'home' : ''}`}>
                      {isHome ? match.team_name : match.opponent_name}
                    </span>
                    <span className="result">
                      {isHome ? `${homeScore}:${awayScore}` : `${awayScore}:${homeScore}`}
                    </span>
                    <span className={`team ${!isHome ? 'home' : ''}`}>
                      {!isHome ? match.team_name : match.opponent_name}
                    </span>
                  </div>
                  <div className="match-info">
                    <span className="team-name">{match.team_name}</span>
                    <span className="league-name">{match.league_name}</span>
                  </div>
                </Link>
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
      </div>

      <div className="dashboard-row">
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
                  <div className="match-venue-indicator">
                    <span className={`home-away-indicator-large ${firstTeam && lastMatch.home_team_id === firstTeam.id ? 'home' : 'away'}`}>
                      {firstTeam && lastMatch.home_team_id === firstTeam.id ? 'Heimspiel' : 'Auswärtsspiel'}
                    </span>
                  </div>
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
