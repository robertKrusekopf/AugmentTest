import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getClubs, getTeams, getPlayers, getMatches, getLeagues } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    clubs: 0,
    teams: 0,
    players: 0,
    matches: 0
  });

  // State für die geladenen Daten
  const [clubsData, setClubsData] = useState([]);
  const [matchesData, setMatchesData] = useState([]);
  const [playersData, setPlayersData] = useState([]);
  const [leagueData, setLeagueData] = useState(null);

  // Lade Daten aus der Datenbank
  useEffect(() => {
    console.log('Lade Dashboard-Daten aus der Datenbank...');

    // Lade die Statistiken aus der API
    Promise.all([
      getClubs(),
      getTeams(),
      getPlayers(),
      getMatches(),
      getLeagues()
    ])
      .then(([clubs, teams, players, matches, leagues]) => {
        console.log('Geladene Daten:', { clubs, teams, players, matches, leagues });

        setStats({
          clubs: clubs ? clubs.length : 0,
          teams: teams ? teams.length : 0,
          players: players ? players.length : 0,
          matches: matches ? matches.length : 0
        });

        // Speichere die Daten für die Anzeige
        setClubsData(clubs || []);
        setMatchesData(matches || []);
        setPlayersData(players || []);

        // Finde die Bundesliga (Liga mit ID 1 oder Level 1)
        const bundesliga = leagues ? leagues.find(league => league.id === 1 || league.level === 1) : null;
        setLeagueData(bundesliga);
        console.log('Bundesliga Daten:', bundesliga);

        setLoading(false);
      })
      .catch(error => {
        console.error('Fehler beim Laden der Dashboard-Daten:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="loading">Lade Dashboard...</div>;
  }

  return (
    <div className="dashboard">
      <h1 className="page-title">Dashboard</h1>

      <div className="dashboard-stats">
        <div className="stat-card">
          <h3>Vereine</h3>
          <div className="value">{stats.clubs}</div>
          <div className="change positive">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="18 15 12 9 6 15"></polyline>
            </svg>
            <span>+2 seit letzter Saison</span>
          </div>
        </div>

        <div className="stat-card">
          <h3>Mannschaften</h3>
          <div className="value">{stats.teams}</div>
          <div className="change positive">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="18 15 12 9 6 15"></polyline>
            </svg>
            <span>+6 seit letzter Saison</span>
          </div>
        </div>

        <div className="stat-card">
          <h3>Spieler</h3>
          <div className="value">{stats.players}</div>
          <div className="change positive">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="18 15 12 9 6 15"></polyline>
            </svg>
            <span>+48 seit letzter Saison</span>
          </div>
        </div>

        <div className="stat-card">
          <h3>Spiele</h3>
          <div className="value">{stats.matches}</div>
          <div className="change">
            <span>Nächstes Spiel: 18. August</span>
          </div>
        </div>
      </div>

      <div className="dashboard-row">
        <div className="card league-standings">
          <div className="card-header">
            <h2>Bundesliga - Tabelle</h2>
            <Link to="/leagues/1" className="btn btn-secondary">Alle anzeigen</Link>
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
              {leagueData && leagueData.standings && leagueData.standings.slice(0, 5).map((team) => (
                <tr key={team.team_id}>
                  <td>{team.position}</td>
                  <td>
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
                  </td>
                  <td>{team.played}</td>
                  <td>{team.won}</td>
                  <td>{team.drawn}</td>
                  <td>{team.lost}</td>
                  <td>{team.points}</td>
                </tr>
              ))}
              {(!leagueData || !leagueData.standings || leagueData.standings.length === 0) && (
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
            <Link to="/matches" className="btn btn-secondary">Alle anzeigen</Link>
          </div>
          <div className="match-list">
            {matchesData.filter(match => !match.is_played).slice(0, 4).map((match, index) => {
              // Finde die Home- und Away-Teams
              const homeTeam = match.home_team ? match.home_team.name : 'Unbekannt';
              const awayTeam = match.away_team ? match.away_team.name : 'Unbekannt';
              const league = match.league ? match.league.name : 'Unbekannt';
              const matchDate = match.match_date ? new Date(match.match_date).toLocaleDateString() : 'TBD';

              return (
                <div className="match-item" key={match.id || index}>
                  <div className="match-date">{matchDate}</div>
                  <div className="match-teams">
                    <span className="team home">{homeTeam}</span>
                    <span className="vs">vs</span>
                    <span className="team away">{awayTeam}</span>
                  </div>
                  <div className="match-league">{league}</div>
                </div>
              );
            })}

            {matchesData.filter(match => !match.is_played).length === 0 && (
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
        <div className="card top-players">
          <div className="card-header">
            <h2>Top Spieler</h2>
            <Link to="/players" className="btn btn-secondary">Alle anzeigen</Link>
          </div>
          <div className="player-grid">
            {playersData.slice(0, 3).map((player, index) => {
              // Finde den Verein des Spielers
              const clubName = player.club ? player.club.name : 'Unbekannt';

              // Berechne die Stärke des Spielers (0-100)
              const strength = player.strength || 50;

              return (
                <div className="player-card" key={player.id || index}>
                  <div className="player-info">
                    <h3 className="player-name">{player.name}</h3>
                    <div className="player-team">{clubName}</div>
                    <div className="player-stats">
                      <div className="player-stat">
                        <span>Alter</span>
                        <span>{player.age || 'N/A'}</span>
                      </div>
                      <div className="player-stat">
                        <span>Position</span>
                        <span>{player.position || 'N/A'}</span>
                      </div>
                      <div className="player-stat">
                        <span>Stärke</span>
                        <div className="strength-bar">
                          <div className="strength-fill" style={{ width: `${strength}%` }}></div>
                        </div>
                        <span>{strength}</span>
                      </div>
                      <div className="player-stat">
                        <span>Talent</span>
                        <span>{player.talent || 5}/10</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}

            {playersData.length === 0 && (
              <div className="player-card">
                <div className="player-info">
                  <h3 className="player-name">Keine Spieler gefunden</h3>
                  <div className="player-team">-</div>
                  <div className="player-stats">
                    <div className="player-stat">
                      <span>Alter</span>
                      <span>-</span>
                    </div>
                    <div className="player-stat">
                      <span>Position</span>
                      <span>-</span>
                    </div>
                    <div className="player-stat">
                      <span>Stärke</span>
                      <div className="strength-bar">
                        <div className="strength-fill" style={{ width: '0%' }}></div>
                      </div>
                      <span>-</span>
                    </div>
                    <div className="player-stat">
                      <span>Talent</span>
                      <span>-</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="card finances-summary">
          <div className="card-header">
            <h2>Finanzen</h2>
            <Link to="/finances" className="btn btn-secondary">Details anzeigen</Link>
          </div>
          <div className="finance-overview">
            <div className="finance-balance">
              <h3>Kontostand</h3>
              <div className="balance-amount">€1,250,000</div>
            </div>
            <div className="finance-chart">
              <div className="chart-placeholder">
                [Hier würde ein Finanz-Chart angezeigt werden]
              </div>
            </div>
            <div className="finance-details">
              <div className="finance-detail-item">
                <span className="detail-label">Einnahmen (monatlich):</span>
                <span className="detail-value positive">€125,000</span>
              </div>
              <div className="finance-detail-item">
                <span className="detail-label">Ausgaben (monatlich):</span>
                <span className="detail-value negative">€100,000</span>
              </div>
              <div className="finance-detail-item">
                <span className="detail-label">Gewinn/Verlust:</span>
                <span className="detail-value positive">€25,000</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
