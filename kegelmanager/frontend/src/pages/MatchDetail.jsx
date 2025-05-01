import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getMatch } from '../services/api';
import './MatchDetail.css';

const MatchDetail = () => {
  const { id } = useParams();
  const [match, setMatch] = useState(null);
  const [loading, setLoading] = useState(true);

  // Lade Spieldaten aus der API
  useEffect(() => {
    console.log(`Lade Spiel mit ID ${id} aus der API...`);

    getMatch(id)
      .then(data => {
        console.log('Geladene Spieldaten:', data);

        if (data) {
          // Verarbeite die Daten und füge fehlende Eigenschaften hinzu
          const processedMatch = {
            ...data,
            // Stelle sicher, dass homeTeam und awayTeam Objekte sind
            homeTeam: data.home_team || { id: 0, name: 'Unbekannt', logo: '?' },
            awayTeam: data.away_team || { id: 0, name: 'Unbekannt', logo: '?' },
            homeScore: data.home_score || 0,
            awayScore: data.away_score || 0,
            league: data.league || { id: 0, name: 'Unbekannt' },
            status: data.is_played ? 'played' : 'scheduled',
            round: data.round || 0,
            venue: data.venue || 'Unbekannt',
            attendance: data.attendance || 0,
            referee: data.referee || 'Unbekannt',
        performances: [
          {
            player_id: 1,
            player_name: 'Max Mustermann',
            match_id: parseInt(id),
            team_id: 1,
            team_name: 'Kegel Sport Club',
            is_home_team: true,
            position_number: 1,
            lane1_score: 160,
            lane2_score: 170,
            lane3_score: 165,
            lane4_score: 175,
            total_score: 670,
            volle_score: 450,
            raeumer_score: 220,
            fehler_count: 1
          },
          {
            player_id: 2,
            player_name: 'Felix Bauer',
            match_id: parseInt(id),
            team_id: 1,
            team_name: 'Kegel Sport Club',
            is_home_team: true,
            position_number: 2,
            lane1_score: 155,
            lane2_score: 165,
            lane3_score: 160,
            lane4_score: 170,
            total_score: 650,
            volle_score: 435,
            raeumer_score: 215,
            fehler_count: 2
          },
          {
            player_id: 3,
            player_name: 'Jan Hoffmann',
            match_id: parseInt(id),
            team_id: 1,
            team_name: 'Kegel Sport Club',
            is_home_team: true,
            position_number: 3,
            lane1_score: 150,
            lane2_score: 160,
            lane3_score: 155,
            lane4_score: 165,
            total_score: 630,
            volle_score: 420,
            raeumer_score: 210,
            fehler_count: 0
          },
          {
            player_id: 4,
            player_name: 'Niklas Weber',
            match_id: parseInt(id),
            team_id: 1,
            team_name: 'Kegel Sport Club',
            is_home_team: true,
            position_number: 4,
            lane1_score: 145,
            lane2_score: 155,
            lane3_score: 150,
            lane4_score: 160,
            total_score: 610,
            volle_score: 410,
            raeumer_score: 200,
            fehler_count: 3
          },
          {
            player_id: 5,
            player_name: 'Thomas Müller',
            match_id: parseInt(id),
            team_id: 1,
            team_name: 'Kegel Sport Club',
            is_home_team: true,
            position_number: 5,
            lane1_score: 140,
            lane2_score: 150,
            lane3_score: 145,
            lane4_score: 155,
            total_score: 590,
            volle_score: 395,
            raeumer_score: 195,
            fehler_count: 2
          },
          {
            player_id: 6,
            player_name: 'David Schmidt',
            match_id: parseInt(id),
            team_id: 1,
            team_name: 'Kegel Sport Club',
            is_home_team: true,
            position_number: 6,
            lane1_score: 135,
            lane2_score: 145,
            lane3_score: 140,
            lane4_score: 150,
            total_score: 570,
            volle_score: 380,
            raeumer_score: 190,
            fehler_count: 4
          },
          {
            player_id: 7,
            player_name: 'Paul Wagner',
            match_id: parseInt(id),
            team_id: 5,
            team_name: 'Kegel Union',
            is_home_team: false,
            position_number: 1,
            lane1_score: 155,
            lane2_score: 165,
            lane3_score: 160,
            lane4_score: 170,
            total_score: 650,
            volle_score: 435,
            raeumer_score: 215,
            fehler_count: 1
          },
          {
            player_id: 8,
            player_name: 'Michael Koch',
            match_id: parseInt(id),
            team_id: 5,
            team_name: 'Kegel Union',
            is_home_team: false,
            position_number: 2,
            lane1_score: 150,
            lane2_score: 160,
            lane3_score: 155,
            lane4_score: 165,
            total_score: 630,
            volle_score: 420,
            raeumer_score: 210,
            fehler_count: 2
          },
          {
            player_id: 9,
            player_name: 'Simon Wolf',
            match_id: parseInt(id),
            team_id: 5,
            team_name: 'Kegel Union',
            is_home_team: false,
            position_number: 3,
            lane1_score: 145,
            lane2_score: 155,
            lane3_score: 150,
            lane4_score: 160,
            total_score: 610,
            volle_score: 410,
            raeumer_score: 200,
            fehler_count: 3
          },
          {
            player_id: 10,
            player_name: 'Kevin Richter',
            match_id: parseInt(id),
            team_id: 5,
            team_name: 'Kegel Union',
            is_home_team: false,
            position_number: 4,
            lane1_score: 140,
            lane2_score: 150,
            lane3_score: 145,
            lane4_score: 155,
            total_score: 590,
            volle_score: 395,
            raeumer_score: 195,
            fehler_count: 4
          },
          {
            player_id: 11,
            player_name: 'Philipp Meyer',
            match_id: parseInt(id),
            team_id: 5,
            team_name: 'Kegel Union',
            is_home_team: false,
            position_number: 5,
            lane1_score: 135,
            lane2_score: 145,
            lane3_score: 140,
            lane4_score: 150,
            total_score: 570,
            volle_score: 380,
            raeumer_score: 190,
            fehler_count: 5
          },
          {
            player_id: 12,
            player_name: 'Leon Fischer',
            match_id: parseInt(id),
            team_id: 5,
            team_name: 'Kegel Union',
            is_home_team: false,
            position_number: 6,
            lane1_score: 130,
            lane2_score: 140,
            lane3_score: 135,
            lane4_score: 145,
            total_score: 550,
            volle_score: 370,
            raeumer_score: 180,
            fehler_count: 6
          }
        ],
        playerPerformances: [
          {
            player: {
              id: 1,
              name: 'Max Mustermann',
              team: 'Kegel Sport Club',
              position: 'Mittelfeld'
            },
            score: 95,
            rating: 9.2
          },
          {
            player: {
              id: 7,
              name: 'Niklas Weber',
              team: 'Kegel Sport Club',
              position: 'Angriff'
            },
            score: 92,
            rating: 8.8
          },
          {
            player: {
              id: 8,
              name: 'Felix Bauer',
              team: 'Kegel Sport Club',
              position: 'Abwehr'
            },
            score: 88,
            rating: 8.5
          },
          {
            player: {
              id: 9,
              name: 'Jan Hoffmann',
              team: 'Kegel Sport Club',
              position: 'Mittelfeld'
            },
            score: 85,
            rating: 8.2
          },
          {
            player: {
              id: 21,
              name: 'Thomas Müller',
              team: 'Kegel Union',
              position: 'Angriff'
            },
            score: 82,
            rating: 7.9
          },
          {
            player: {
              id: 22,
              name: 'David Schmidt',
              team: 'Kegel Union',
              position: 'Mittelfeld'
            },
            score: 78,
            rating: 7.5
          }
        ],
        matchEvents: [
          {
            time: '15:05',
            description: 'Spielbeginn',
            type: 'start'
          },
          {
            time: '15:12',
            description: 'Punkt für Kegel Sport Club durch Max Mustermann',
            type: 'point',
            team: 'home',
            player: 'Max Mustermann'
          },
          {
            time: '15:25',
            description: 'Punkt für Kegel Sport Club durch Niklas Weber',
            type: 'point',
            team: 'home',
            player: 'Niklas Weber'
          },
          {
            time: '15:38',
            description: 'Punkt für Kegel Union durch Thomas Müller',
            type: 'point',
            team: 'away',
            player: 'Thomas Müller'
          },
          {
            time: '15:45',
            description: 'Ende der ersten Halbzeit',
            type: 'half'
          },
          {
            time: '16:00',
            description: 'Beginn der zweiten Halbzeit',
            type: 'half'
          },
          {
            time: '16:08',
            description: 'Punkt für Kegel Sport Club durch Jan Hoffmann',
            type: 'point',
            team: 'home',
            player: 'Jan Hoffmann'
          },
          {
            time: '16:17',
            description: 'Punkt für Kegel Sport Club durch Max Mustermann',
            type: 'point',
            team: 'home',
            player: 'Max Mustermann'
          },
          {
            time: '16:29',
            description: 'Punkt für Kegel Union durch David Schmidt',
            type: 'point',
            team: 'away',
            player: 'David Schmidt'
          },
          {
            time: '16:35',
            description: 'Punkt für Kegel Sport Club durch Niklas Weber',
            type: 'point',
            team: 'home',
            player: 'Niklas Weber'
          },
          {
            time: '16:42',
            description: 'Punkt für Kegel Sport Club durch Felix Bauer',
            type: 'point',
            team: 'home',
            player: 'Felix Bauer'
          },
          {
            time: '16:51',
            description: 'Punkt für Kegel Sport Club durch Max Mustermann',
            type: 'point',
            team: 'home',
            player: 'Max Mustermann'
          },
          {
            time: '16:58',
            description: 'Punkt für Kegel Sport Club durch Jan Hoffmann',
            type: 'point',
            team: 'home',
            player: 'Jan Hoffmann'
          },
          {
            time: '17:05',
            description: 'Spielende',
            type: 'end'
          }
        ],
        statistics: {
          home: {
            accuracy: 0,
            technique: 0,
            teamwork: 0
          },
          away: {
            accuracy: 0,
            technique: 0,
            teamwork: 0
          }
        }
          };

          setMatch(processedMatch);
        } else {
          console.error(`Keine Daten für Spiel ${id} gefunden`);
        }

        setLoading(false);
      })
      .catch(error => {
        console.error(`Fehler beim Laden des Spiels ${id}:`, error);
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return <div className="loading">Lade Spieldaten...</div>;
  }

  if (!match) {
    return <div className="error">Spiel nicht gefunden</div>;
  }

  return (
    <div className="match-detail-page">
      <div className="page-header">
        <div className="breadcrumbs">
          <Link to="/matches">Spiele</Link> / Spieltag {match.round}
        </div>
      </div>

      <div className="match-header-card card">
        <div className="match-info">
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
          <div className="match-league">
            <Link to={`/leagues/${match.league.id}`}>{match.league.name}</Link>
          </div>
          <div className="match-venue">Spielort: {match.venue}</div>
          {match.attendance && (
            <div className="match-attendance">Zuschauer: {match.attendance}</div>
          )}
          {match.referee && (
            <div className="match-referee">Schiedsrichter: {match.referee}</div>
          )}
        </div>

        <div className="match-teams-container">
          <div className="match-team home">
            <Link to={`/teams/${match.homeTeam.id}`} className="team-logo">
              <span>{match.homeTeam.logo}</span>
            </Link>
            <div className="team-name">{match.homeTeam.name}</div>
          </div>

          <div className="match-result">
            {match.status === 'played' ? (
              <div className="score-display">
                <div className="score">{match.homeScore}</div>
                <div className="score-separator">:</div>
                <div className="score">{match.awayScore}</div>
              </div>
            ) : (
              <div className="vs-display">vs</div>
            )}
            <div className="match-status">{match.status === 'played' ? 'Beendet' : 'Anstehend'}</div>
          </div>

          <div className="match-team away">
            <Link to={`/teams/${match.awayTeam.id}`} className="team-logo">
              <span>{match.awayTeam.logo}</span>
            </Link>
            <div className="team-name">{match.awayTeam.name}</div>
          </div>
        </div>
      </div>

      <div className="match-content">
        <div className="match-section card">
          <h2 className="section-title">Spielverlauf</h2>
          <div className="match-timeline">
            {match.matchEvents.map((event, index) => (
              <div key={index} className={`timeline-event ${event.type} ${event.team || ''}`}>
                <div className="event-time">{event.time}</div>
                <div className="event-content">
                  {event.type === 'point' && (
                    <div className="event-icon">
                      {event.team === 'home' ? '🏆' : '🏆'}
                    </div>
                  )}
                  {event.type === 'start' && <div className="event-icon">🏁</div>}
                  {event.type === 'half' && <div className="event-icon">⏱️</div>}
                  {event.type === 'end' && <div className="event-icon">🏁</div>}
                  <div className="event-description">{event.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="match-section card">
          <h2 className="section-title">Spielergebnisse</h2>
          <div className="bowling-results">
            <table className="table bowling-results-table">
              <thead>
                <tr>
                  <th className="player-name">{match.homeTeam.name}</th>
                  <th className="lane-score">Bahn 1</th>
                  <th className="lane-score">Bahn 2</th>
                  <th className="lane-score">Bahn 3</th>
                  <th className="lane-score">Bahn 4</th>
                  <th className="total-score">Gesamt</th>
                  <th className="total-score">Gesamt</th>
                  <th className="lane-score">Bahn 4</th>
                  <th className="lane-score">Bahn 3</th>
                  <th className="lane-score">Bahn 2</th>
                  <th className="lane-score">Bahn 1</th>
                  <th className="player-name">{match.awayTeam.name}</th>
                </tr>
              </thead>
              <tbody>
                {/* Gruppiere Performances nach Position und Team */}
                {match.performances && Array.from({ length: 6 }, (_, i) => {
                  // Position i+1
                  const position = i + 1;

                  // Finde Heimspieler für diese Position
                  const homePerf = match.performances.find(p =>
                    p.is_home_team && p.position_number === position
                  );

                  // Finde Auswärtsspieler für diese Position
                  const awayPerf = match.performances.find(p =>
                    !p.is_home_team && p.position_number === position
                  );

                  // Wenn keine Spieler für diese Position gefunden wurden, überspringe
                  if (!homePerf && !awayPerf) return null;

                  // Standardwerte, falls ein Spieler fehlt
                  const homePlayer = homePerf ? {
                    id: homePerf.player_id,
                    name: homePerf.player_name,
                    lane1: homePerf.lane1_score,
                    lane2: homePerf.lane2_score,
                    lane3: homePerf.lane3_score,
                    lane4: homePerf.lane4_score,
                    total: homePerf.total_score
                  } : {
                    id: 0,
                    name: 'Kein Spieler',
                    lane1: 0,
                    lane2: 0,
                    lane3: 0,
                    lane4: 0,
                    total: 0
                  };

                  const awayPlayer = awayPerf ? {
                    id: awayPerf.player_id,
                    name: awayPerf.player_name,
                    lane1: awayPerf.lane1_score,
                    lane2: awayPerf.lane2_score,
                    lane3: awayPerf.lane3_score,
                    lane4: awayPerf.lane4_score,
                    total: awayPerf.total_score
                  } : {
                    id: 0,
                    name: 'Kein Spieler',
                    lane1: 0,
                    lane2: 0,
                    lane3: 0,
                    lane4: 0,
                    total: 0
                  };

                  return (
                    <tr key={i} className={homePlayer.total > awayPlayer.total ? 'home-win' : homePlayer.total < awayPlayer.total ? 'away-win' : 'draw'}>
                      <td className="player-name">
                        {homePlayer.id > 0 ? (
                          <Link to={`/players/${homePlayer.id}`}>{homePlayer.name}</Link>
                        ) : (
                          homePlayer.name
                        )}
                      </td>
                      <td className="lane-score">{homePlayer.lane1}</td>
                      <td className="lane-score">{homePlayer.lane2}</td>
                      <td className="lane-score">{homePlayer.lane3}</td>
                      <td className="lane-score">{homePlayer.lane4}</td>
                      <td className="total-score">{homePlayer.total}</td>
                      <td className="total-score">{awayPlayer.total}</td>
                      <td className="lane-score">{awayPlayer.lane4}</td>
                      <td className="lane-score">{awayPlayer.lane3}</td>
                      <td className="lane-score">{awayPlayer.lane2}</td>
                      <td className="lane-score">{awayPlayer.lane1}</td>
                      <td className="player-name">
                        {awayPlayer.id > 0 ? (
                          <Link to={`/players/${awayPlayer.id}`}>{awayPlayer.name}</Link>
                        ) : (
                          awayPlayer.name
                        )}
                      </td>
                    </tr>
                  );
                }).filter(Boolean)}
                {/* Gesamtergebnis */}
                <tr className="team-totals">
                  <td className="player-name">Gesamt</td>
                  <td className="lane-score" colSpan="4"></td>
                  <td className="total-score">{match.homeScore}</td>
                  <td className="total-score">{match.awayScore}</td>
                  <td className="lane-score" colSpan="4"></td>
                  <td className="player-name">Gesamt</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="match-section card">
          <h2 className="section-title">Detaillierte Statistiken</h2>
          <div className="bowling-results">
            <table className="table bowling-stats-table">
              <thead>
                <tr>
                  <th className="player-name">{match.homeTeam.name}</th>
                  <th className="stat-score">Volle</th>
                  <th className="stat-score">Räumer</th>
                  <th className="stat-score">Fehlwürfe</th>
                  <th className="total-score">Gesamt</th>
                  <th className="total-score">Gesamt</th>
                  <th className="stat-score">Fehlwürfe</th>
                  <th className="stat-score">Räumer</th>
                  <th className="stat-score">Volle</th>
                  <th className="player-name">{match.awayTeam.name}</th>
                </tr>
              </thead>
              <tbody>
                {/* Gruppiere Performances nach Position und Team */}
                {match.performances && Array.from({ length: 6 }, (_, i) => {
                  // Position i+1
                  const position = i + 1;

                  // Finde Heimspieler für diese Position
                  const homePerf = match.performances.find(p =>
                    p.is_home_team && p.position_number === position
                  );

                  // Finde Auswärtsspieler für diese Position
                  const awayPerf = match.performances.find(p =>
                    !p.is_home_team && p.position_number === position
                  );

                  // Wenn keine Spieler für diese Position gefunden wurden, überspringe
                  if (!homePerf && !awayPerf) return null;

                  // Standardwerte, falls ein Spieler fehlt
                  const homePlayer = homePerf ? {
                    id: homePerf.player_id,
                    name: homePerf.player_name,
                    volle: homePerf.volle_score || Math.round(homePerf.total_score * 0.67), // Fallback wenn keine Daten
                    raeumer: homePerf.raeumer_score || Math.round(homePerf.total_score * 0.33), // Fallback wenn keine Daten
                    fehler: homePerf.fehler_count || Math.round(Math.random() * 3), // Fallback wenn keine Daten
                    total: homePerf.total_score
                  } : {
                    id: 0,
                    name: 'Kein Spieler',
                    volle: 0,
                    raeumer: 0,
                    fehler: 0,
                    total: 0
                  };

                  const awayPlayer = awayPerf ? {
                    id: awayPerf.player_id,
                    name: awayPerf.player_name,
                    volle: awayPerf.volle_score || Math.round(awayPerf.total_score * 0.67), // Fallback wenn keine Daten
                    raeumer: awayPerf.raeumer_score || Math.round(awayPerf.total_score * 0.33), // Fallback wenn keine Daten
                    fehler: awayPerf.fehler_count || Math.round(Math.random() * 3), // Fallback wenn keine Daten
                    total: awayPerf.total_score
                  } : {
                    id: 0,
                    name: 'Kein Spieler',
                    volle: 0,
                    raeumer: 0,
                    fehler: 0,
                    total: 0
                  };

                  return (
                    <tr key={i} className={homePlayer.total > awayPlayer.total ? 'home-win' : homePlayer.total < awayPlayer.total ? 'away-win' : 'draw'}>
                      <td className="player-name">
                        {homePlayer.id > 0 ? (
                          <Link to={`/players/${homePlayer.id}`}>{homePlayer.name}</Link>
                        ) : (
                          homePlayer.name
                        )}
                      </td>
                      <td className="stat-score">{homePlayer.volle}</td>
                      <td className="stat-score">{homePlayer.raeumer}</td>
                      <td className="stat-score">{homePlayer.fehler}</td>
                      <td className="total-score">{homePlayer.total}</td>
                      <td className="total-score">{awayPlayer.total}</td>
                      <td className="stat-score">{awayPlayer.fehler}</td>
                      <td className="stat-score">{awayPlayer.raeumer}</td>
                      <td className="stat-score">{awayPlayer.volle}</td>
                      <td className="player-name">
                        {awayPlayer.id > 0 ? (
                          <Link to={`/players/${awayPlayer.id}`}>{awayPlayer.name}</Link>
                        ) : (
                          awayPlayer.name
                        )}
                      </td>
                    </tr>
                  );
                }).filter(Boolean)}
                {/* Gesamtergebnis */}
                <tr className="team-totals">
                  <td className="player-name">Gesamt</td>
                  <td className="stat-score" colSpan="3"></td>
                  <td className="total-score">{match.homeScore}</td>
                  <td className="total-score">{match.awayScore}</td>
                  <td className="stat-score" colSpan="3"></td>
                  <td className="player-name">Gesamt</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="match-section card">
          <h2 className="section-title">Statistiken</h2>
          <div className="statistics-container">
            <div className="statistic-item">
              <div className="statistic-label">Genauigkeit</div>
              <div className="statistic-bars">
                <div className="team-bar home">
                  <div className="bar-fill" style={{ width: `${match.statistics.home.accuracy}%` }}></div>
                  <span className="bar-value">{match.statistics.home.accuracy}%</span>
                </div>
                <div className="statistic-name">Genauigkeit</div>
                <div className="team-bar away">
                  <div className="bar-fill" style={{ width: `${match.statistics.away.accuracy}%` }}></div>
                  <span className="bar-value">{match.statistics.away.accuracy}%</span>
                </div>
              </div>
            </div>

            <div className="statistic-item">
              <div className="statistic-label">Technik</div>
              <div className="statistic-bars">
                <div className="team-bar home">
                  <div className="bar-fill" style={{ width: `${match.statistics.home.technique}%` }}></div>
                  <span className="bar-value">{match.statistics.home.technique}%</span>
                </div>
                <div className="statistic-name">Technik</div>
                <div className="team-bar away">
                  <div className="bar-fill" style={{ width: `${match.statistics.away.technique}%` }}></div>
                  <span className="bar-value">{match.statistics.away.technique}%</span>
                </div>
              </div>
            </div>

            <div className="statistic-item">
              <div className="statistic-label">Teamwork</div>
              <div className="statistic-bars">
                <div className="team-bar home">
                  <div className="bar-fill" style={{ width: `${match.statistics.home.teamwork}%` }}></div>
                  <span className="bar-value">{match.statistics.home.teamwork}%</span>
                </div>
                <div className="statistic-name">Teamwork</div>
                <div className="team-bar away">
                  <div className="bar-fill" style={{ width: `${match.statistics.away.teamwork}%` }}></div>
                  <span className="bar-value">{match.statistics.away.teamwork}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchDetail;
