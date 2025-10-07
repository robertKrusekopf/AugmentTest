import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getPlayer, updatePlayer, getPlayerHistory, getPlayerMatches, createTransferOffer } from '../services/api';
import './PlayerDetail.css';

const PlayerDetail = () => {
  const { id } = useParams();
  const [player, setPlayer] = useState(null);
  const [playerHistory, setPlayerHistory] = useState(null);
  const [playerMatches, setPlayerMatches] = useState(null);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [matchesLoading, setMatchesLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [cheatForm, setCheatForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState({ show: false, type: '', text: '' });
  const [cheatModeEnabled, setCheatModeEnabled] = useState(false);
  const [managedClubId, setManagedClubId] = useState(null);
  const [transferring, setTransferring] = useState(false);


  // Lade Spielerdaten aus der API
  useEffect(() => {
    console.log(`Lade Spieler mit ID ${id} aus der API...`);

    getPlayer(id)
      .then(data => {
        console.log('Geladene Spielerdaten:', data);

        if (data) {
          // Verarbeite die Daten und füge fehlende Eigenschaften hinzu
          const processedPlayer = {
            ...data,
            // Verwende die Daten aus der API oder setze Standardwerte
            team: data.teams && data.teams.length > 0 ? data.teams[0] : 'Kein Team',
            salary: data.salary || 0,
            contractEnd: data.contract_end || new Date().toISOString(),
            // Verwende die Statistiken aus der API oder setze Standardwerte
            statistics: data.statistics || {
              total_matches: 0,
              home_matches: 0,
              away_matches: 0,
              avg_total_score: 0,
              avg_home_score: 0,
              avg_away_score: 0,
              avg_total_volle: 0,
              avg_home_volle: 0,
              avg_away_volle: 0,
              avg_total_raeumer: 0,
              avg_home_raeumer: 0,
              avg_away_raeumer: 0,
              avg_total_fehler: 0,
              avg_home_fehler: 0,
              avg_away_fehler: 0,
              mp_win_percentage: 0
            },
            // Für die Übersichtsseite
            stats: {
              matches: data.statistics?.total_matches || 0,
              goals: 0,
              assists: 0,
              rating: 0
            },
            // Verwende die Kegeln-spezifischen Attribute
            attributes: {
              konstanz: data.konstanz || 0,
              drucksicherheit: data.drucksicherheit || 0,
              volle: data.volle || 0,
              raeumer: data.raeumer || 0,
              sicherheit: data.sicherheit || 0,
              auswaerts: data.auswaerts || 0,
              start: data.start || 0,
              mitte: data.mitte || 0,
              schluss: data.schluss || 0,
              ausdauer: data.ausdauer || 0
            },
            // In einer echten Anwendung würden diese aus der Datenbank kommen
            history: [],
            development: []
          };

          setPlayer(processedPlayer);

          // Load cheat mode status and managed club ID
          const savedSettings = localStorage.getItem('gameSettings');
          if (savedSettings) {
            try {
              const settings = JSON.parse(savedSettings);
              setCheatModeEnabled(settings.cheats?.cheatMode || false);
              setManagedClubId(settings.game?.managerClubId || null);
            } catch (e) {
              console.error('Failed to parse saved settings:', e);
            }
          }

          // Initialize cheat form with player data
          setCheatForm({
            name: processedPlayer.name,
            age: processedPlayer.age,
            position: processedPlayer.position,
            strength: processedPlayer.strength,
            talent: processedPlayer.talent,
            salary: processedPlayer.salary,
            contract_end: processedPlayer.contractEnd.split('T')[0], // Format as YYYY-MM-DD
            konstanz: processedPlayer.attributes.konstanz,
            drucksicherheit: processedPlayer.attributes.drucksicherheit,
            volle: processedPlayer.attributes.volle,
            raeumer: processedPlayer.attributes.raeumer,
            sicherheit: processedPlayer.attributes.sicherheit,
            auswaerts: processedPlayer.attributes.auswaerts,
            start: processedPlayer.attributes.start,
            mitte: processedPlayer.attributes.mitte,
            schluss: processedPlayer.attributes.schluss,
            ausdauer: processedPlayer.attributes.ausdauer,
            // Form system attributes
            form_short_term: processedPlayer.form_short_term || 0,
            form_medium_term: processedPlayer.form_medium_term || 0,
            form_long_term: processedPlayer.form_long_term || 0,
            form_short_remaining_days: processedPlayer.form_short_remaining_days || 0,
            form_medium_remaining_days: processedPlayer.form_medium_remaining_days || 0,
            form_long_remaining_days: processedPlayer.form_long_remaining_days || 0,
            // Retirement system attributes
            retirement_age: processedPlayer.retirement_age || 40
          });
        } else {
          console.error(`Keine Daten für Spieler ${id} gefunden`);
        }

        setLoading(false);
      })
      .catch(error => {
        console.error(`Fehler beim Laden des Spielers ${id}:`, error);
        setLoading(false);
      });
  }, [id]);

  // Lade Spieler-Historie aus der API
  useEffect(() => {
    console.log(`Lade Spieler-Historie für ID ${id} aus der API...`);

    getPlayerHistory(id)
      .then(data => {
        console.log('Geladene Spieler-Historie:', data);

        // If no history data exists, try to load demo data
        if (!data.history || data.history.length === 0) {
          console.log('Keine Historie gefunden, lade Demo-Daten...');
          return fetch(`http://localhost:5000/api/players/${id}/history?demo=true`)
            .then(response => response.json());
        }
        return data;
      })
      .then(data => {
        console.log('Finale Spieler-Historie:', data);
        setPlayerHistory(data);
        setHistoryLoading(false);
      })
      .catch(error => {
        console.error('Fehler beim Laden der Spieler-Historie:', error);
        setHistoryLoading(false);
      });
  }, [id]);

  // Lade Spieler-Spiele aus der API
  useEffect(() => {
    console.log(`Lade Spieler-Spiele für ID ${id} aus der API...`);

    getPlayerMatches(id)
      .then(data => {
        console.log('Geladene Spieler-Spiele:', data);
        setPlayerMatches(data);
        setMatchesLoading(false);
      })
      .catch(error => {
        console.error('Fehler beim Laden der Spieler-Spiele:', error);
        setMatchesLoading(false);
      });
  }, [id]);

  // Handle form input changes
  const handleCheatInputChange = (e) => {
    const { name, value } = e.target;
    setCheatForm({
      ...cheatForm,
      [name]: name === 'name' || name === 'position' ? value : Number(value)
    });
  };

  // Handle form submission
  const handleCheatSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveMessage({ show: false, type: '', text: '' });

    try {
      const response = await updatePlayer(id, cheatForm);

      if (response.success) {
        // Update the player state with the new data
        setPlayer({
          ...player,
          ...response.player,
          team: response.player.teams && response.player.teams.length > 0 ? response.player.teams[0] : 'Kein Team',
          contractEnd: response.player.contract_end || new Date().toISOString(),
          attributes: {
            konstanz: response.player.konstanz || 0,
            drucksicherheit: response.player.drucksicherheit || 0,
            volle: response.player.volle || 0,
            raeumer: response.player.raeumer || 0,
            sicherheit: response.player.sicherheit || 0,
            auswaerts: response.player.auswaerts || 0,
            start: response.player.start || 0,
            mitte: response.player.mitte || 0,
            schluss: response.player.schluss || 0,
            ausdauer: response.player.ausdauer || 0
          }
        });

        setSaveMessage({
          show: true,
          type: 'success',
          text: 'Spieler erfolgreich aktualisiert!'
        });
      } else {
        setSaveMessage({
          show: true,
          type: 'error',
          text: response.message || 'Fehler beim Aktualisieren des Spielers'
        });
      }
    } catch (error) {
      console.error('Fehler beim Aktualisieren des Spielers:', error);
      setSaveMessage({
        show: true,
        type: 'error',
        text: 'Fehler beim Aktualisieren des Spielers: ' + error.message
      });
    } finally {
      setSaving(false);

      // Hide message after 3 seconds
      setTimeout(() => {
        setSaveMessage({ show: false, type: '', text: '' });
      }, 3000);
    }
  };

  // Handle transfer offer creation
  const handleTransferOffer = async () => {
    if (!managedClubId) {
      alert('Bitte wählen Sie zuerst einen Verein in den Einstellungen aus.');
      return;
    }

    if (!player.club_id) {
      alert('Dieser Spieler ist keinem Verein zugeordnet und kann nicht transferiert werden.');
      return;
    }

    if (player.club_id === managedClubId) {
      alert('Dieser Spieler gehört bereits zu Ihrem Verein.');
      return;
    }

    // Calculate a reasonable offer amount based on player strength
    const offerAmount = player.strength * 5000; // Same calculation as in backend

    try {
      setTransferring(true);
      const result = await createTransferOffer(player.id, managedClubId, offerAmount);

      // Show different messages based on cheat mode
      if (result.cheat_mode) {
        alert(`${player.name} wurde erfolgreich zu Ihrem Verein transferiert (Cheat-Modus aktiviert)!`);
        // Reload player data to reflect the transfer
        window.location.reload();
      } else {
        alert(`Transferangebot für ${player.name} erfolgreich erstellt!`);
      }
    } catch (error) {
      console.error('Error creating transfer offer:', error);
      alert('Fehler beim Erstellen des Transferangebots. Bitte versuchen Sie es erneut.');
    } finally {
      setTransferring(false);
    }
  };



  if (loading) {
    return <div className="loading">Lade Spielerdaten...</div>;
  }

  if (!player) {
    return <div className="error">Spieler nicht gefunden</div>;
  }

  return (
    <div className="player-detail-page">
      <div className="page-header">
        <div className="breadcrumbs">
          <Link to="/players">Spieler</Link> / {player.name}
        </div>
        <div className="header-actions">
          <button
            className="btn btn-primary"
            onClick={handleTransferOffer}
            disabled={transferring || !managedClubId || (player && player.club_id === managedClubId)}
            title={
              !managedClubId ? 'Bitte wählen Sie zuerst einen Verein in den Einstellungen aus' :
              (player && player.club_id === managedClubId) ? 'Dieser Spieler gehört bereits zu Ihrem Verein' :
              cheatModeEnabled ? 'Spieler sofort zu Ihrem Verein transferieren (Cheat-Modus)' :
              'Transferangebot für diesen Spieler erstellen'
            }
          >
            {transferring ? 'Wird verarbeitet...' :
             (player && player.club_id === managedClubId) ? 'Bereits in Ihrem Verein' :
             cheatModeEnabled ? 'Sofort transferieren' : 'Transferangebot'}
          </button>
        </div>
      </div>

      <div className="player-profile card">
        <div className="player-header">
          <div className="player-avatar">
            <span>{player.name.charAt(0)}</span>
          </div>
          <div className="player-header-info">
            <h1 className="player-name">{player.name}</h1>
            <div className="player-meta">
              <span className="player-position">{player.position}</span>
              <span className="player-team">{player.team}</span>
              <span className="player-age">{player.age} Jahre</span>
              {cheatModeEnabled && (
                <span className="cheat-mode-indicator">
                  ⚡ Cheat-Modus aktiv
                </span>
              )}
            </div>
          </div>
          <div className="player-ratings">
            <div className="rating-item">
              <span className="rating-label">Stärke</span>
              <span className="rating-value">???</span>
              <div className="strength-bar">
                <div className="strength-fill" style={{ width: `0%` }}></div>
              </div>
            </div>
            <div className="rating-item">
              <span className="rating-label">Talent</span>
              <div className="talent-stars">
                <span>???</span>
              </div>
            </div>
          </div>
        </div>

        <div className="player-tabs">
          <div
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Übersicht
          </div>
          <div
            className={`tab ${activeTab === 'attributes' ? 'active' : ''}`}
            onClick={() => setActiveTab('attributes')}
          >
            Attribute
          </div>
          <div
            className={`tab ${activeTab === 'statistics' ? 'active' : ''}`}
            onClick={() => setActiveTab('statistics')}
          >
            Statistiken
          </div>
          <div
            className={`tab ${activeTab === 'matches' ? 'active' : ''}`}
            onClick={() => setActiveTab('matches')}
          >
            Spiele
          </div>
          <div
            className={`tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            Verlauf
          </div>
          <div
            className={`tab ${activeTab === 'development' ? 'active' : ''}`}
            onClick={() => setActiveTab('development')}
          >
            Entwicklung
          </div>
          <div
            className={`tab ${activeTab === 'cheat' ? 'active' : ''}`}
            onClick={() => setActiveTab('cheat')}
          >
            Cheat
          </div>
        </div>

        <div className="player-content">
          {activeTab === 'overview' && (
            <div className="overview-tab">
              <div className="overview-grid">
                <div className="overview-card">
                  <h3>Persönliche Daten</h3>
                  <div className="info-list">
                    <div className="info-item">
                      <span className="info-label">Name:</span>
                      <span className="info-value">{player.name}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Alter:</span>
                      <span className="info-value">{player.age} Jahre</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Position:</span>
                      <span className="info-value">{player.position}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Verein:</span>
                      <span className="info-value">{player.team}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Gehalt:</span>
                      <span className="info-value">€{player.salary.toLocaleString()} / Monat</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Vertrag bis:</span>
                      <span className="info-value">{new Date(player.contractEnd).toLocaleDateString('de-DE')}</span>
                    </div>
                  </div>
                </div>

                <div className="overview-card">
                  <h3>Aktuelle Saison</h3>
                  <div className="info-list">
                    <div className="info-item">
                      <span className="info-label">Spiele:</span>
                      <span className="info-value">{player.stats.matches}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Durchschnitt:</span>
                      <span className="info-value">{player.statistics?.avg_total_score || 0}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Heim-Durchschnitt:</span>
                      <span className="info-value">{player.statistics?.avg_home_score || 0}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Auswärts-Durchschnitt:</span>
                      <span className="info-value">{player.statistics?.avg_away_score || 0}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Spieler-Historie Tabelle */}
              <div className="overview-card" style={{ marginTop: '20px' }}>
                <h3>Spieler-Historie {playerHistory && playerHistory.history && playerHistory.history.length > 0 && playerHistory.history[0].season_name === 'Season 2024' ? '(Demo-Daten)' : ''}</h3>
                {historyLoading ? (
                  <div className="loading">Lade Historie...</div>
                ) : playerHistory && playerHistory.history && playerHistory.history.length > 0 ? (
                  <div className="history-table-container">
                    <table className="table history-table">
                      <thead>
                        <tr>
                          <th>Saison</th>
                          <th>Mannschaft</th>
                          <th>Liga</th>
                          <th>Level</th>
                          <th>Platz</th>
                          <th>Einsätze</th>
                          <th>Ø Heim</th>
                          <th>Ø Auswärts</th>
                          <th>Ø Gesamt</th>
                          <th>Ø Fehler</th>
                        </tr>
                      </thead>
                      <tbody>
                        {playerHistory.history.map((entry, index) => (
                          <tr key={`${entry.season_id}-${entry.team_id}-${index}`} className="history-row">
                            <td className="season-name">{entry.season_name}</td>
                            <td className="team-name">{entry.team_name}</td>
                            <td className="league-name">{entry.league_name}</td>
                            <td className="league-level">{entry.league_level}</td>
                            <td className={`position ${entry.final_position ? (entry.final_position <= 3 ? 'top-position' : '') : 'current-season'}`}>
                              {entry.final_position ? `${entry.final_position}.` : 'Laufend'}
                            </td>
                            <td className="appearances">{entry.appearances}</td>
                            <td className="avg-score home">{entry.avg_home_score ? entry.avg_home_score.toFixed(1) : '-'}</td>
                            <td className="avg-score away">{entry.avg_away_score ? entry.avg_away_score.toFixed(1) : '-'}</td>
                            <td className="avg-score total">{entry.avg_total_score ? entry.avg_total_score.toFixed(1) : '-'}</td>
                            <td className="avg-errors">{entry.avg_total_errors ? entry.avg_total_errors.toFixed(1) : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="no-history">Keine Historie verfügbar</div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'attributes' && (
            <div className="attributes-tab">
              <div className="attributes-grid">
                {Object.entries(player.attributes).map(([key, value]) => (
                  <div key={key} className="attribute-item">
                    <span className="attribute-label">{key.charAt(0).toUpperCase() + key.slice(1)}</span>
                    <div className="attribute-bar">
                      <div className="attribute-fill" style={{ width: `0%` }}></div>
                    </div>
                    <span className="attribute-value">???</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="history-tab">
              <table className="table history-table">
                <thead>
                  <tr>
                    <th>Saison</th>
                    <th>Verein</th>
                    <th>Spiele</th>
                    <th>Tore</th>
                    <th>Vorlagen</th>
                  </tr>
                </thead>
                <tbody>
                  {player.history.map((season, index) => (
                    <tr key={index}>
                      <td>{season.season}</td>
                      <td>{season.team}</td>
                      <td>{season.matches}</td>
                      <td>{season.goals}</td>
                      <td>{season.assists}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'statistics' && (
            <div className="statistics-tab">
              <div className="statistics-grid">
                <div className="statistics-card">
                  <h3>Allgemeine Statistiken</h3>
                  <div className="info-list">
                    <div className="info-item">
                      <span className="info-label">Gespielte Spiele:</span>
                      <span className="info-value">{player.statistics?.total_matches || 0}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Heimspiele:</span>
                      <span className="info-value">{player.statistics?.home_matches || 0}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Auswärtsspiele:</span>
                      <span className="info-value">{player.statistics?.away_matches || 0}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">MP-Gewinnquote:</span>
                      <span className="info-value">{player.statistics?.mp_win_percentage || 0}%</span>
                    </div>
                  </div>
                </div>
              </div>

              <h3>Detaillierte Statistiken</h3>
              <table className="table statistics-table">
                <thead>
                  <tr>
                    <th>Statistik</th>
                    <th>Heim</th>
                    <th>Auswärts</th>
                    <th>Gesamt</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Durchschnitt</strong></td>
                    <td>{player.statistics?.avg_home_score || 0}</td>
                    <td>{player.statistics?.avg_away_score || 0}</td>
                    <td>{player.statistics?.avg_total_score || 0}</td>
                  </tr>
                  <tr>
                    <td><strong>Volle</strong></td>
                    <td>{player.statistics?.avg_home_volle || 0}</td>
                    <td>{player.statistics?.avg_away_volle || 0}</td>
                    <td>{player.statistics?.avg_total_volle || 0}</td>
                  </tr>
                  <tr>
                    <td><strong>Räumer</strong></td>
                    <td>{player.statistics?.avg_home_raeumer || 0}</td>
                    <td>{player.statistics?.avg_away_raeumer || 0}</td>
                    <td>{player.statistics?.avg_total_raeumer || 0}</td>
                  </tr>
                  <tr>
                    <td><strong>Fehlwürfe</strong></td>
                    <td>{player.statistics?.avg_home_fehler || 0}</td>
                    <td>{player.statistics?.avg_away_fehler || 0}</td>
                    <td>{player.statistics?.avg_total_fehler || 0}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'matches' && (
            <div className="matches-tab">
              {matchesLoading ? (
                <div className="loading">Lade Spiele...</div>
              ) : playerMatches ? (
                <>
                  <div className="section-header">
                    <h3>Alle Spiele</h3>
                  </div>
                  <table className="table matches-table">
                    <thead>
                      <tr>
                        <th>Datum</th>
                        <th>Heimteam</th>
                        <th>Ergebnis</th>
                        <th>Auswärtsteam</th>
                        <th>Liga/Pokal</th>
                        <th>Teilnahme</th>
                        <th>Gespielt für</th>
                        <th>Leistung</th>
                        <th>Aktionen</th>
                      </tr>
                    </thead>
                    <tbody>
                      {/* Alle Spiele chronologisch sortiert - vergangene Spiele zuerst (älteste oben), dann kommende Spiele */}
                      {playerMatches.recent_matches && [...playerMatches.recent_matches].reverse().map(match => (
                        <tr key={`recent-${match.id}`} className={`recent-match ${!match.player_participated ? 'not-participated' : ''}`}>
                          <td>
                            {match.date ? new Date(match.date).toLocaleDateString('de-DE', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            }) : 'Kein Datum'}
                          </td>
                          <td>{match.homeTeam}</td>
                          <td>
                            {match.is_played ? (
                              <strong>{match.homeScore} - {match.awayScore}</strong>
                            ) : (
                              'Nicht gespielt'
                            )}
                          </td>
                          <td>{match.awayTeam}</td>
                          <td>
                            <span className={`match-type ${match.type}`}>
                              {match.league}
                            </span>
                          </td>
                          <td>
                            <span className={`participation-status ${match.player_participated ? 'participated' : 'not-participated'}`}>
                              {match.player_participated ? '✓ Gespielt' : '✗ Nicht gespielt'}
                            </span>
                          </td>
                          <td>
                            {match.played_for_team ? (
                              <span className={`team-name ${match.played_for_team !== player.team ? 'substitute-team' : 'regular-team'}`}>
                                {match.played_for_team}
                              </span>
                            ) : (
                              '-'
                            )}
                          </td>
                          <td>
                            {match.player_participated && match.player_performance ? (
                              <span className="player-score">
                                {match.player_performance.total_score} Holz
                              </span>
                            ) : (
                              '-'
                            )}
                          </td>
                          <td>
                            <Link to={`/matches/${match.id}`} className="btn btn-small">
                              Details
                            </Link>
                          </td>
                        </tr>
                      ))}

                      {/* Kommende Spiele (bereits chronologisch sortiert vom Backend) */}
                      {playerMatches.upcoming_matches && playerMatches.upcoming_matches.map(match => (
                        <tr key={`upcoming-${match.id}`} className={`upcoming-match ${!match.player_participated ? 'not-participated' : ''}`}>
                          <td>
                            {match.date ? new Date(match.date).toLocaleDateString('de-DE', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            }) : 'TBD'}
                          </td>
                          <td>{match.homeTeam}</td>
                          <td>
                            {match.is_played ? (
                              <strong>{match.homeScore} - {match.awayScore}</strong>
                            ) : (
                              '-'
                            )}
                          </td>
                          <td>{match.awayTeam}</td>
                          <td>
                            <span className={`match-type ${match.type}`}>
                              {match.league}
                            </span>
                          </td>
                          <td>
                            <span className={`participation-status ${match.player_participated ? 'participated' : 'not-participated'}`}>
                              {match.player_participated ? '✓ Gespielt' : '✗ Nicht gespielt'}
                            </span>
                          </td>
                          <td>
                            {match.played_for_team ? (
                              <span className={`team-name ${match.played_for_team !== player.team ? 'substitute-team' : 'regular-team'}`}>
                                {match.played_for_team}
                              </span>
                            ) : (
                              '-'
                            )}
                          </td>
                          <td>
                            {match.player_participated && match.player_performance ? (
                              <span className="player-score">
                                {match.player_performance.total_score} Holz
                              </span>
                            ) : (
                              '-'
                            )}
                          </td>
                          <td>
                            <Link to={`/matches/${match.id}`} className="btn btn-small">
                              Details
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : (
                <div className="no-matches">Keine Spiele gefunden</div>
              )}
            </div>
          )}

          {activeTab === 'development' && (
            <div className="development-tab">
              <div className="development-chart">
                <h3>Stärkeentwicklung</h3>
                <div className="chart-placeholder">
                  [Hier würde ein Entwicklungs-Chart angezeigt werden]
                </div>
              </div>
              <table className="table development-table">
                <thead>
                  <tr>
                    <th>Alter</th>
                    <th>Stärke</th>
                    <th>Veränderung</th>
                  </tr>
                </thead>
                <tbody>
                  {player.development.map((dev, index) => {
                    return (
                      <tr key={index}>
                        <td>{dev.age}</td>
                        <td>???</td>
                        <td>???</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'cheat' && (
            <div className="cheat-tab">
              <h3>Spieler bearbeiten (Cheat-Modus)</h3>

              {saveMessage.show && (
                <div className={`message ${saveMessage.type}`}>
                  {saveMessage.text}
                </div>
              )}

              <form className="cheat-form" onSubmit={handleCheatSubmit}>
                <div className="form-grid">
                  <div className="form-section">
                    <h4>Persönliche Daten</h4>

                    <div className="form-group">
                      <label htmlFor="name">Name:</label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={cheatForm.name || ''}
                        onChange={handleCheatInputChange}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="age">Alter:</label>
                      <input
                        type="number"
                        id="age"
                        name="age"
                        min="16"
                        max="45"
                        value={cheatForm.age || ''}
                        onChange={handleCheatInputChange}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="position">Position:</label>
                      <input
                        type="text"
                        id="position"
                        name="position"
                        value={cheatForm.position || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="strength">Stärke (1-99):</label>
                      <input
                        type="number"
                        id="strength"
                        name="strength"
                        min="1"
                        max="99"
                        value={cheatForm.strength || ''}
                        onChange={handleCheatInputChange}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="talent">Talent (1-10):</label>
                      <input
                        type="number"
                        id="talent"
                        name="talent"
                        min="1"
                        max="10"
                        value={cheatForm.talent || ''}
                        onChange={handleCheatInputChange}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="salary">Gehalt (€):</label>
                      <input
                        type="number"
                        id="salary"
                        name="salary"
                        min="0"
                        step="100"
                        value={cheatForm.salary || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="contract_end">Vertragsende:</label>
                      <input
                        type="date"
                        id="contract_end"
                        name="contract_end"
                        value={cheatForm.contract_end || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="retirement_age">Ruhestandsalter (30-45):</label>
                      <input
                        type="number"
                        id="retirement_age"
                        name="retirement_age"
                        min="30"
                        max="45"
                        value={cheatForm.retirement_age || ''}
                        onChange={handleCheatInputChange}
                        title="Alter, in dem der Spieler in den Ruhestand geht"
                      />
                    </div>
                  </div>

                  <div className="form-section">
                    <h4>Bowling-Attribute</h4>

                    <div className="form-group">
                      <label htmlFor="konstanz">Konstanz (1-99):</label>
                      <input
                        type="number"
                        id="konstanz"
                        name="konstanz"
                        min="1"
                        max="99"
                        value={cheatForm.konstanz || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="drucksicherheit">Drucksicherheit (1-99):</label>
                      <input
                        type="number"
                        id="drucksicherheit"
                        name="drucksicherheit"
                        min="1"
                        max="99"
                        value={cheatForm.drucksicherheit || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="volle">Volle (1-99):</label>
                      <input
                        type="number"
                        id="volle"
                        name="volle"
                        min="1"
                        max="99"
                        value={cheatForm.volle || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="raeumer">Räumer (1-99):</label>
                      <input
                        type="number"
                        id="raeumer"
                        name="raeumer"
                        min="1"
                        max="99"
                        value={cheatForm.raeumer || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="sicherheit">Sicherheit (1-99):</label>
                      <input
                        type="number"
                        id="sicherheit"
                        name="sicherheit"
                        min="1"
                        max="99"
                        value={cheatForm.sicherheit || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="auswaerts">Auswärts (1-99):</label>
                      <input
                        type="number"
                        id="auswaerts"
                        name="auswaerts"
                        min="1"
                        max="99"
                        value={cheatForm.auswaerts || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="start">Start (1-99):</label>
                      <input
                        type="number"
                        id="start"
                        name="start"
                        min="1"
                        max="99"
                        value={cheatForm.start || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="mitte">Mitte (1-99):</label>
                      <input
                        type="number"
                        id="mitte"
                        name="mitte"
                        min="1"
                        max="99"
                        value={cheatForm.mitte || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="schluss">Schluss (1-99):</label>
                      <input
                        type="number"
                        id="schluss"
                        name="schluss"
                        min="1"
                        max="99"
                        value={cheatForm.schluss || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="ausdauer">Ausdauer (1-99):</label>
                      <input
                        type="number"
                        id="ausdauer"
                        name="ausdauer"
                        min="1"
                        max="99"
                        value={cheatForm.ausdauer || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>
                  </div>

                  <div className="form-section">
                    <h4>Form-System (Unsichtbar im normalen Spiel)</h4>

                    <div className="form-group">
                      <label htmlFor="form_short_term">Kurzfristige Form (-20 bis +20):</label>
                      <input
                        type="number"
                        id="form_short_term"
                        name="form_short_term"
                        min="-20"
                        max="20"
                        step="0.1"
                        value={cheatForm.form_short_term || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="form_short_remaining_days">Kurzfristige Form - Verbleibende Tage:</label>
                      <input
                        type="number"
                        id="form_short_remaining_days"
                        name="form_short_remaining_days"
                        min="0"
                        max="10"
                        value={cheatForm.form_short_remaining_days || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="form_medium_term">Mittelfristige Form (-15 bis +15):</label>
                      <input
                        type="number"
                        id="form_medium_term"
                        name="form_medium_term"
                        min="-15"
                        max="15"
                        step="0.1"
                        value={cheatForm.form_medium_term || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="form_medium_remaining_days">Mittelfristige Form - Verbleibende Tage:</label>
                      <input
                        type="number"
                        id="form_medium_remaining_days"
                        name="form_medium_remaining_days"
                        min="0"
                        max="15"
                        value={cheatForm.form_medium_remaining_days || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="form_long_term">Langfristige Form (-10 bis +10):</label>
                      <input
                        type="number"
                        id="form_long_term"
                        name="form_long_term"
                        min="-10"
                        max="10"
                        step="0.1"
                        value={cheatForm.form_long_term || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="form_long_remaining_days">Langfristige Form - Verbleibende Tage:</label>
                      <input
                        type="number"
                        id="form_long_remaining_days"
                        name="form_long_remaining_days"
                        min="0"
                        max="25"
                        value={cheatForm.form_long_remaining_days || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>
                  </div>
                </div>

                <div className="form-actions">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={saving}
                  >
                    {saving ? 'Speichern...' : 'Änderungen speichern'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayerDetail;
