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
            // Verwende die Daten direkt aus der API
            home_team_id: data.home_team_id || 0,
            away_team_id: data.away_team_id || 0,
            home_team_name: data.home_team_name || 'Unbekannt',
            away_team_name: data.away_team_name || 'Unbekannt',
            home_team_club_id: data.home_team_club_id || 0,
            away_team_club_id: data.away_team_club_id || 0,
            home_team_verein_id: data.home_team_verein_id || 0,
            away_team_verein_id: data.away_team_verein_id || 0,
            homeScore: data.home_score || 0,
            awayScore: data.away_score || 0,
            homeMatchPoints: data.home_match_points || 0,
            awayMatchPoints: data.away_match_points || 0,
            league: { id: data.league_id || 0, name: data.league_name || 'Unbekannt' },
            status: data.is_played ? 'played' : 'scheduled',
            round: data.round || 0,
            venue: data.venue || 'Unbekannt',
            attendance: data.attendance || 0,
            referee: data.referee || 'Unbekannt',
            performances: data.performances || []
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
            <Link to={`/teams/${match.home_team_id}`} className="team-logo">
              <img
                src={`/api/club-emblem/${match.home_team_verein_id || match.home_team_club_id}`}
                alt={match.home_team_name}
                onError={(e) => { e.target.src = '/placeholder.png'; e.target.onerror = null; }}
              />
            </Link>
            <div className="team-name">{match.home_team_name}</div>
          </div>

          <div className="match-result">
            {match.status === 'played' ? (
              <div className="score-container">
                <div className="match-points-display">
                  <div className="match-points">{match.homeMatchPoints}</div>
                  <div className="score-separator">:</div>
                  <div className="match-points">{match.awayMatchPoints}</div>
                  <div className="match-points-label">MP</div>
                </div>
                <div className="score-display">
                  <div className="score">{match.homeScore}</div>
                  <div className="score-separator">:</div>
                  <div className="score">{match.awayScore}</div>
                  <div className="score-label">Holz</div>
                </div>
              </div>
            ) : (
              <div className="vs-display">vs</div>
            )}
            <div className="match-status">{match.status === 'played' ? 'Beendet' : 'Anstehend'}</div>
          </div>

          <div className="match-team away">
            <Link to={`/teams/${match.away_team_id}`} className="team-logo">
              <img
                src={`/api/club-emblem/${match.away_team_verein_id || match.away_team_club_id}`}
                alt={match.away_team_name}
                onError={(e) => { e.target.src = '/placeholder.png'; e.target.onerror = null; }}
              />
            </Link>
            <div className="team-name">{match.away_team_name}</div>
          </div>
        </div>
      </div>

      <div className="match-content">


        <div className="match-section card">
          <h2 className="section-title">Spielergebnisse</h2>
          <div className="bowling-results">
            <table className="table bowling-results-table">
              <thead>
                <tr>
                  <th className="player-name">{match.home_team_name}</th>
                  <th className="lane-score">Bahn 1</th>
                  <th className="lane-score">Bahn 2</th>
                  <th className="lane-score">Bahn 3</th>
                  <th className="lane-score">Bahn 4</th>
                  <th className="set-points">SP</th>
                  <th className="match-points">MP</th>
                  <th className="total-score">Gesamt</th>
                  <th className="total-score">Gesamt</th>
                  <th className="match-points">MP</th>
                  <th className="set-points">SP</th>
                  <th className="lane-score">Bahn 4</th>
                  <th className="lane-score">Bahn 3</th>
                  <th className="lane-score">Bahn 2</th>
                  <th className="lane-score">Bahn 1</th>
                  <th className="player-name">{match.away_team_name}</th>
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
                    setPoints: homePerf.set_points || 0,
                    matchPoints: homePerf.match_points || 0,
                    total: homePerf.total_score,
                    isSubstitute: homePerf.is_substitute || false
                  } : {
                    id: 0,
                    name: 'Kein Spieler',
                    lane1: 0,
                    lane2: 0,
                    lane3: 0,
                    lane4: 0,
                    setPoints: 0,
                    matchPoints: 0,
                    total: 0,
                    isSubstitute: false
                  };

                  const awayPlayer = awayPerf ? {
                    id: awayPerf.player_id,
                    name: awayPerf.player_name,
                    lane1: awayPerf.lane1_score,
                    lane2: awayPerf.lane2_score,
                    lane3: awayPerf.lane3_score,
                    lane4: awayPerf.lane4_score,
                    setPoints: awayPerf.set_points || 0,
                    matchPoints: awayPerf.match_points || 0,
                    total: awayPerf.total_score,
                    isSubstitute: awayPerf.is_substitute || false
                  } : {
                    id: 0,
                    name: 'Kein Spieler',
                    lane1: 0,
                    lane2: 0,
                    lane3: 0,
                    lane4: 0,
                    setPoints: 0,
                    matchPoints: 0,
                    total: 0,
                    isSubstitute: false
                  };

                  return (
                    <tr key={i} className={homePlayer.matchPoints > awayPlayer.matchPoints ? 'home-win' : homePlayer.matchPoints < awayPlayer.matchPoints ? 'away-win' : 'draw'}>
                      <td className="player-name">
                        {homePlayer.id > 0 ? (
                          <>
                            <Link to={`/players/${homePlayer.id}`}>{homePlayer.name}</Link>
                            {homePlayer.isSubstitute && <span className="substitute-badge" title="Ersatzspieler"> (E)</span>}
                          </>
                        ) : (
                          homePlayer.name
                        )}
                      </td>
                      <td className="lane-score">{homePlayer.lane1}</td>
                      <td className="lane-score">{homePlayer.lane2}</td>
                      <td className="lane-score">{homePlayer.lane3}</td>
                      <td className="lane-score">{homePlayer.lane4}</td>
                      <td className="set-points">{homePlayer.setPoints}</td>
                      <td className="match-points">{homePlayer.matchPoints}</td>
                      <td className="total-score">{homePlayer.total}</td>
                      <td className="total-score">{awayPlayer.total}</td>
                      <td className="match-points">{awayPlayer.matchPoints}</td>
                      <td className="set-points">{awayPlayer.setPoints}</td>
                      <td className="lane-score">{awayPlayer.lane4}</td>
                      <td className="lane-score">{awayPlayer.lane3}</td>
                      <td className="lane-score">{awayPlayer.lane2}</td>
                      <td className="lane-score">{awayPlayer.lane1}</td>
                      <td className="player-name">
                        {awayPlayer.id > 0 ? (
                          <>
                            <Link to={`/players/${awayPlayer.id}`}>{awayPlayer.name}</Link>
                            {awayPlayer.isSubstitute && <span className="substitute-badge" title="Ersatzspieler"> (E)</span>}
                          </>
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
                  <td className="set-points"></td>
                  <td className="match-points">{match.homeMatchPoints}</td>
                  <td className="total-score">{match.homeScore}</td>
                  <td className="total-score">{match.awayScore}</td>
                  <td className="match-points">{match.awayMatchPoints}</td>
                  <td className="set-points"></td>
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
                  <th className="player-name">{match.home_team_name}</th>
                  <th className="stat-score">Volle</th>
                  <th className="stat-score">Räumer</th>
                  <th className="stat-score">Fehlwürfe</th>
                  <th className="total-score">Gesamt</th>
                  <th className="total-score">Gesamt</th>
                  <th className="stat-score">Fehlwürfe</th>
                  <th className="stat-score">Räumer</th>
                  <th className="stat-score">Volle</th>
                  <th className="player-name">{match.away_team_name}</th>
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
                    fehler: homePerf.fehler_count || 0, // Keine zufälligen Werte mehr
                    setPoints: homePerf.set_points || 0,
                    matchPoints: homePerf.match_points || 0,
                    total: homePerf.total_score,
                    isSubstitute: homePerf.is_substitute || false
                  } : {
                    id: 0,
                    name: 'Kein Spieler',
                    volle: 0,
                    raeumer: 0,
                    fehler: 0,
                    setPoints: 0,
                    matchPoints: 0,
                    total: 0,
                    isSubstitute: false
                  };

                  const awayPlayer = awayPerf ? {
                    id: awayPerf.player_id,
                    name: awayPerf.player_name,
                    volle: awayPerf.volle_score || Math.round(awayPerf.total_score * 0.67), // Fallback wenn keine Daten
                    raeumer: awayPerf.raeumer_score || Math.round(awayPerf.total_score * 0.33), // Fallback wenn keine Daten
                    fehler: awayPerf.fehler_count || 0, // Keine zufälligen Werte mehr
                    setPoints: awayPerf.set_points || 0,
                    matchPoints: awayPerf.match_points || 0,
                    total: awayPerf.total_score,
                    isSubstitute: awayPerf.is_substitute || false
                  } : {
                    id: 0,
                    name: 'Kein Spieler',
                    volle: 0,
                    raeumer: 0,
                    fehler: 0,
                    setPoints: 0,
                    matchPoints: 0,
                    total: 0,
                    isSubstitute: false
                  };

                  return (
                    <tr key={i} className={homePlayer.matchPoints > awayPlayer.matchPoints ? 'home-win' : homePlayer.matchPoints < awayPlayer.matchPoints ? 'away-win' : 'draw'}>
                      <td className="player-name">
                        {homePlayer.id > 0 ? (
                          <>
                            <Link to={`/players/${homePlayer.id}`}>{homePlayer.name}</Link>
                            {homePlayer.isSubstitute && <span className="substitute-badge" title="Ersatzspieler"> (E)</span>}
                          </>
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
                          <>
                            <Link to={`/players/${awayPlayer.id}`}>{awayPlayer.name}</Link>
                            {awayPlayer.isSubstitute && <span className="substitute-badge" title="Ersatzspieler"> (E)</span>}
                          </>
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


      </div>
    </div>
  );
};

export default MatchDetail;
