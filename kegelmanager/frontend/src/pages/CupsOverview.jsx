import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCupsOptimized, getCupDetailOptimized, getCupHistoryByNameOptimized } from '../services/apiCache';
import ClubEmblem from '../components/ClubEmblem';
import TeamLink from '../components/TeamLink';
import './CupsOverview.css';

const CupsOverview = () => {
  const [selectedCupId, setSelectedCupId] = useState(null);
  const [allCups, setAllCups] = useState([]);
  const [selectedCup, setSelectedCup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('matches');
  const [selectedRound, setSelectedRound] = useState('all');
  const [cupHistory, setCupHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const loadAllCups = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await getCupsOptimized();
      setAllCups(data);

      // Automatisch den ersten Pokal auswählen, falls noch keiner ausgewählt ist
      if (data.length > 0 && !selectedCupId) {
        setSelectedCupId(data[0].id);
      }
    } catch (error) {
      console.error('Error loading cups:', error);
      setError('Fehler beim Laden der Pokale');
    } finally {
      setLoading(false);
    }
  };

  const loadCupDetails = async (cupId) => {
    try {
      setLoading(true);
      setError(null);

      const data = await getCupDetailOptimized(cupId);
      setSelectedCup(data);
    } catch (error) {
      console.error('Error loading cup details:', error);
      setError('Fehler beim Laden der Pokal-Details');
    } finally {
      setLoading(false);
    }
  };

  const loadCupHistory = async (cupName) => {
    try {
      setHistoryLoading(true);
      const data = await getCupHistoryByNameOptimized(cupName);
      setCupHistory(data);
    } catch (error) {
      console.error('Error loading cup history:', error);
      setCupHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    loadAllCups();
  }, []);

  useEffect(() => {
    if (selectedCupId) {
      loadCupDetails(selectedCupId);
      setSelectedRound('all'); // Reset round selection when cup changes
    }
  }, [selectedCupId]);

  useEffect(() => {
    if (selectedCup && selectedCup.name) {
      loadCupHistory(selectedCup.name);
    }
  }, [selectedCup]);

  // Get available rounds from matches
  const getAvailableRounds = () => {
    if (!selectedCup || !selectedCup.matches) return [];

    const rounds = [...new Set(selectedCup.matches.map(match => match.round_name))];
    return rounds.sort((a, b) => {
      // Sort rounds by round number if available
      const aMatch = selectedCup.matches.find(m => m.round_name === a);
      const bMatch = selectedCup.matches.find(m => m.round_name === b);
      return (aMatch?.round_number || 0) - (bMatch?.round_number || 0);
    });
  };

  // Filter matches by selected round
  const getFilteredMatches = () => {
    if (!selectedCup || !selectedCup.matches) return {};

    let matchesToShow = selectedCup.matches;

    if (selectedRound !== 'all') {
      matchesToShow = selectedCup.matches.filter(match => match.round_name === selectedRound);
    }

    return matchesToShow.reduce((acc, match) => {
      const round = match.round_name || 'Unbekannte Runde';
      if (!acc[round]) acc[round] = [];
      acc[round].push(match);
      return acc;
    }, {});
  };

  return (
    <div className="cups-overview-page">
      <div className="page-header">
        <h1 className="page-title">Pokale</h1>
        <p className="page-description">
          Übersicht über alle Pokalwettbewerbe der aktuellen Saison
        </p>
      </div>

      <div className="cups-navigation">
        <div className="cup-selector">
          <label htmlFor="cup-select" className="selector-label">
            Pokal auswählen:
          </label>
          <select
            id="cup-select"
            value={selectedCupId || ''}
            onChange={(e) => setSelectedCupId(parseInt(e.target.value))}
            className="cup-dropdown"
          >
            <option value="">-- Pokal auswählen --</option>
            {allCups.map(cup => (
              <option key={cup.id} value={cup.id}>
                {cup.name}
              </option>
            ))}
          </select>
        </div>


      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={loadAllCups} className="btn btn-secondary">
            Erneut versuchen
          </button>
        </div>
      )}

      {loading && (
        <div className="loading-message">
          <div className="loading-spinner"></div>
          <p>Lade Pokale...</p>
        </div>
      )}

      {allCups.length === 0 && !loading && !error && (
        <div className="no-cups">
          <div className="no-cups-content">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
              <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
              <path d="M4 22h16"></path>
              <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path>
              <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path>
              <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>
            </svg>
            <h3>Keine Pokale gefunden</h3>
            <p>Es wurden keine Pokale für die aktuelle Saison gefunden.</p>
          </div>
        </div>
      )}

      {selectedCup && !loading && (
        <div className="cup-detail-section">
          <div className="cup-detail-header">
            <h2 className="cup-detail-title">{selectedCup.name}</h2>
            <div className="cup-header-meta">
              <span className={`cup-status ${selectedCup.is_active ? 'active' : 'inactive'}`}>
                {selectedCup.is_active ? 'Aktiv' : 'Inaktiv'}
              </span>
              <span className="cup-round">
                Aktuelle Runde: {selectedCup.current_round} ({selectedCup.current_round_number || 1}/{selectedCup.total_rounds || '?'})
              </span>
            </div>
          </div>

          <div className="cup-detail-content">
            {/* Tab Navigation */}
            <div className="tab-navigation">
              <button
                className={`tab-button ${activeTab === 'matches' ? 'active' : ''}`}
                onClick={() => setActiveTab('matches')}
              >
                Spiele
              </button>
              <button
                className={`tab-button ${activeTab === 'teams' ? 'active' : ''}`}
                onClick={() => setActiveTab('teams')}
              >
                Teams
              </button>
              <button
                className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
                onClick={() => setActiveTab('history')}
              >
                Historie
              </button>
            </div>

            {/* Tab Content */}
            <div className="tab-content">
              {activeTab === 'matches' && (
                <div className="matches-tab">
                  {selectedCup.matches && selectedCup.matches.length > 0 ? (
                    <>
                      {/* Round Filter */}
                      <div className="matches-filter">
                        <label htmlFor="round-select" className="filter-label">
                          Runde auswählen:
                        </label>
                        <select
                          id="round-select"
                          value={selectedRound}
                          onChange={(e) => setSelectedRound(e.target.value)}
                          className="round-dropdown"
                        >
                          <option value="all">Alle Runden</option>
                          {getAvailableRounds().map(round => (
                            <option key={round} value={round}>
                              {round}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="matches-by-round">
                        {Object.entries(getFilteredMatches()).map(([roundName, matches]) => (
                          <div key={roundName} className="round-section">
                            <h3 className="round-title">{roundName}</h3>
                            <div className="matches-list">
                              {matches.map(match => {
                                // Nur gespielte Spiele (außer Freilose) sind klickbar
                                const isClickable = match.is_played && match.away_team_name; // Freilose haben kein away_team_name

                                if (isClickable) {
                                  return (
                                    <div key={match.id} className={`match-row ${match.is_played ? 'played' : 'upcoming'} clickable`}>
                                      {/* Home Team */}
                                      <div className="team-info home-team">
                                        <div className="team-emblem-container">
                                          {match.home_team_emblem_url && (
                                            <img
                                              src={match.home_team_emblem_url}
                                              alt={`${match.home_team_name} Wappen`}
                                              className="team-emblem-small"
                                              onError={(e) => {
                                                e.target.style.display = 'none';
                                              }}
                                            />
                                          )}
                                        </div>
                                        <div className="team-details">
                                          <TeamLink
                                            teamId={match.home_team_id}
                                            clubId={match.home_team_club_id}
                                            teamName={match.home_team_name}
                                            className="team-name"
                                          />
                                          {match.home_team_league_level && (
                                            <span className="league-level">Liga {match.home_team_league_level}</span>
                                          )}
                                        </div>
                                      </div>

                                      {/* Score/VS */}
                                      <Link to={`/matches/${match.id}`} className="match-score">
                                        {match.is_played ? (
                                          <div className="score-display">
                                            <span className="score">{match.home_score || 0}</span>
                                            <span className="score-separator">:</span>
                                            <span className="score">{match.away_score || 0}</span>
                                          </div>
                                        ) : (
                                          <span className="vs-text">vs</span>
                                        )}
                                      </Link>

                                      {/* Away Team */}
                                      <div className="team-info away-team">
                                        {match.away_team_name ? (
                                          <>
                                            <div className="team-details">
                                              <TeamLink
                                                teamId={match.away_team_id}
                                                clubId={match.away_team_club_id}
                                                teamName={match.away_team_name}
                                                className="team-name"
                                              />
                                              {match.away_team_league_level && (
                                                <span className="league-level">Liga {match.away_team_league_level}</span>
                                              )}
                                            </div>
                                            <div className="team-emblem-container">
                                              {match.away_team_emblem_url && (
                                                <img
                                                  src={match.away_team_emblem_url}
                                                  alt={`${match.away_team_name} Wappen`}
                                                  className="team-emblem-small"
                                                  onError={(e) => {
                                                    e.target.style.display = 'none';
                                                  }}
                                                />
                                              )}
                                            </div>
                                          </>
                                        ) : (
                                          <div className="bye-indicator">
                                            <span className="bye-text">Freilos</span>
                                          </div>
                                        )}
                                      </div>

                                      {/* Match Status */}
                                      <Link to={`/matches/${match.id}`} className="match-status-info">
                                        {match.match_date && (
                                          <span className="match-date">{new Date(match.match_date).toLocaleDateString('de-DE')}</span>
                                        )}
                                        <span className={`match-status ${match.is_played ? 'played' : 'upcoming'}`}>
                                          {match.is_played ? 'Gespielt' : 'Ausstehend'}
                                        </span>
                                      </Link>
                                    </div>
                                  );
                                } else {
                                  return (
                                    <div key={match.id} className={`match-row ${match.is_played ? 'played' : 'upcoming'}`}>
                                      {/* Home Team */}
                                      <div className="team-info home-team">
                                        <div className="team-emblem-container">
                                          {match.home_team_emblem_url && (
                                            <img
                                              src={match.home_team_emblem_url}
                                              alt={`${match.home_team_name} Wappen`}
                                              className="team-emblem-small"
                                              onError={(e) => {
                                                e.target.style.display = 'none';
                                              }}
                                            />
                                          )}
                                        </div>
                                        <div className="team-details">
                                          <TeamLink
                                            teamId={match.home_team_id}
                                            clubId={match.home_team_club_id}
                                            teamName={match.home_team_name}
                                            className="team-name"
                                          />
                                          {match.home_team_league_level && (
                                            <span className="league-level">Liga {match.home_team_league_level}</span>
                                          )}
                                        </div>
                                      </div>

                                      {/* Score/VS */}
                                      <div className="match-score">
                                        {match.is_played ? (
                                          <div className="score-display">
                                            <span className="score">{match.home_score || 0}</span>
                                            <span className="score-separator">:</span>
                                            <span className="score">{match.away_score || 0}</span>
                                          </div>
                                        ) : (
                                          <span className="vs-text">vs</span>
                                        )}
                                      </div>

                                      {/* Away Team */}
                                      <div className="team-info away-team">
                                        {match.away_team_name ? (
                                          <>
                                            <div className="team-details">
                                              <TeamLink
                                                teamId={match.away_team_id}
                                                clubId={match.away_team_club_id}
                                                teamName={match.away_team_name}
                                                className="team-name"
                                              />
                                              {match.away_team_league_level && (
                                                <span className="league-level">Liga {match.away_team_league_level}</span>
                                              )}
                                            </div>
                                            <div className="team-emblem-container">
                                              {match.away_team_emblem_url && (
                                                <img
                                                  src={match.away_team_emblem_url}
                                                  alt={`${match.away_team_name} Wappen`}
                                                  className="team-emblem-small"
                                                  onError={(e) => {
                                                    e.target.style.display = 'none';
                                                  }}
                                                />
                                              )}
                                            </div>
                                          </>
                                        ) : (
                                          <div className="bye-indicator">
                                            <span className="bye-text">Freilos</span>
                                          </div>
                                        )}
                                      </div>

                                      {/* Match Status */}
                                      <div className="match-status-info">
                                        {match.match_date && (
                                          <span className="match-date">{new Date(match.match_date).toLocaleDateString('de-DE')}</span>
                                        )}
                                        <span className={`match-status ${match.is_played ? 'played' : 'upcoming'}`}>
                                          {match.is_played ? 'Gespielt' : 'Ausstehend'}
                                        </span>
                                      </div>
                                    </div>
                                  );
                                }
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="no-matches">
                      <p>Noch keine Spiele für diesen Pokal generiert.</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'teams' && (
                <div className="teams-tab">
                  {selectedCup.eligible_teams && selectedCup.eligible_teams.length > 0 ? (
                    <div className="teams-grid">
                      {selectedCup.eligible_teams.map(team => (
                        <div key={team.id} className="team-card">
                          <div className="team-header">
                            {team.emblem_url && (
                              <ClubEmblem
                                emblemUrl={team.emblem_url}
                                clubName={team.club_name}
                                className="team-emblem"
                              />
                            )}
                            <div className="team-info">
                              <h4 className="team-name">{team.name}</h4>
                              <p className="club-name">{team.club_name}</p>
                              {team.league_name && (
                                <p className="league-name">{team.league_name}</p>
                              )}
                            </div>
                          </div>
                          <div className="team-actions">
                            <Link to={`/teams/${team.id}`} className="btn btn-sm btn-secondary">
                              Team anzeigen
                            </Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-teams">
                      <p>Keine teilnehmenden Teams gefunden.</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'history' && (
                <div className="history-tab">
                  {historyLoading ? (
                    <div className="loading">Lade Historie...</div>
                  ) : cupHistory && cupHistory.length > 0 ? (
                    <div className="history-content">
                      <h3 className="history-title">Pokal-Historie: {selectedCup.name}</h3>
                      <div className="history-list">
                        {cupHistory.map((entry, index) => (
                          <div key={entry.id} className="history-entry">
                            <div className="history-header">
                              <h4 className="season-name">{entry.season_name}</h4>
                              <div className="final-score">
                                {entry.final_result.winner_score} : {entry.final_result.finalist_score}
                                {entry.final_result.winner_set_points && entry.final_result.finalist_set_points && (
                                  <span className="set-points">
                                    ({entry.final_result.winner_set_points} : {entry.final_result.finalist_set_points} SP)
                                  </span>
                                )}
                              </div>
                            </div>

                            <div className="finalists">
                              {/* Winner */}
                              <div className="finalist winner">
                                <div className="finalist-header">
                                  <div className="trophy-icon">🏆</div>
                                  <span className="finalist-label">Sieger</span>
                                </div>
                                <div className="team-info">
                                  {entry.winner.emblem_url && (
                                    <img
                                      src={entry.winner.emblem_url}
                                      alt={`${entry.winner.club_name} Wappen`}
                                      className="team-emblem-small"
                                      onError={(e) => {
                                        e.target.style.display = 'none';
                                      }}
                                    />
                                  )}
                                  <div className="team-details">
                                    <span className="team-name">{entry.winner.team_name}</span>
                                    <span className="club-name">{entry.winner.club_name}</span>
                                  </div>
                                </div>
                              </div>

                              {/* Finalist */}
                              <div className="finalist runner-up">
                                <div className="finalist-header">
                                  <div className="medal-icon">🥈</div>
                                  <span className="finalist-label">Finalist</span>
                                </div>
                                <div className="team-info">
                                  {entry.finalist.emblem_url && (
                                    <img
                                      src={entry.finalist.emblem_url}
                                      alt={`${entry.finalist.club_name} Wappen`}
                                      className="team-emblem-small"
                                      onError={(e) => {
                                        e.target.style.display = 'none';
                                      }}
                                    />
                                  )}
                                  <div className="team-details">
                                    <span className="team-name">{entry.finalist.team_name}</span>
                                    <span className="club-name">{entry.finalist.club_name}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="no-history">
                      <h3>Keine Historie verfügbar</h3>
                      <p>Für diesen Pokal wurden noch keine historischen Daten gefunden. Die Historie wird automatisch gespeichert, sobald der Pokal in einer Saison abgeschlossen wurde.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CupsOverview;
