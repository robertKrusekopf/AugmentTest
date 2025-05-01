import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getLeagues } from '../services/api';
import './Leagues.css';

const Leagues = () => {
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);

  // Lade Daten aus der Datenbank
  useEffect(() => {
    console.log('Lade Ligen aus der Datenbank...');

    // Lade die Daten aus der API
    getLeagues()
      .then(data => {
        console.log('Geladene Ligen:', data);

        // Wenn keine Daten zurückgegeben werden, verwende leere Liste
        if (!data || data.length === 0) {
          console.warn('Keine Ligen in der Datenbank gefunden.');
          setLeagues([]);
        } else {
          // Verarbeite die Daten und füge fehlende Eigenschaften hinzu
          const processedLeagues = data.map(league => {
            // Bestimme die Anzahl der Teams in der Liga
            const teamsCount = league.teams ? league.teams.length : 0;

            // Verwende Tabellenstände aus der API, falls vorhanden
            const standings = league.standings || (league.teams_info ? league.teams_info.map((team, index) => {
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
            }) : []);

            // Stelle sicher, dass alle benötigten Eigenschaften vorhanden sind
            return {
              id: league.id,
              name: league.name,
              level: league.level || 0,
              teams: teamsCount,
              standings: standings
            };
          });

          setLeagues(processedLeagues);
        }

        setLoading(false);
      })
      .catch(error => {
        console.error('Fehler beim Laden der Ligen:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="loading">Lade Ligen...</div>;
  }

  return (
    <div className="leagues-page">
      <h1 className="page-title">Ligen</h1>

      <div className="leagues-container">
        {leagues.map(league => (
          <div key={league.id} className="league-card card">
            <div className="card-header">
              <h2 className="league-name">{league.name}</h2>
              <Link to={`/leagues/${league.id}`} className="btn btn-secondary">
                Details anzeigen
              </Link>
            </div>

            <div className="league-info">
              <div className="league-meta">
                <div className="meta-item">
                  <span className="meta-label">Level:</span>
                  <span className="meta-value">{league.level}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Teams:</span>
                  <span className="meta-value">{league.teams}</span>
                </div>
              </div>

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
                    <tr key={team.position}>
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
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Leagues;
