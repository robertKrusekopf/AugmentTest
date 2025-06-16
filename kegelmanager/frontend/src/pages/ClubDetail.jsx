import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getClub, updateClub, addTeamToClub, getLeagues, getSeasonStatus } from '../services/api';
import './ClubDetail.css';

const ClubDetail = () => {
  const { id } = useParams();
  const [club, setClub] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [cheatForm, setCheatForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState({ show: false, type: '', text: '' });
  const [showAddTeamModal, setShowAddTeamModal] = useState(false);
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState('');
  const [teamName, setTeamName] = useState('');
  const [seasonCompleted, setSeasonCompleted] = useState(false);
  const [addingTeam, setAddingTeam] = useState(false);

  // Lade Daten aus der API
  useEffect(() => {
    console.log(`Lade Club mit ID ${id} aus der API...`);

    const loadData = async () => {
      try {
        // Load club data
        const data = await getClub(id);
        console.log('Geladene Club-Daten:', data);

        // Verarbeite die Daten
        if (data) {
          console.log('Spielerdaten aus API:', data.players);

          // Füge fehlende Eigenschaften hinzu, falls nötig
          const processedClub = {
            ...data,
            balance: data.balance || 0,
            income: data.income || 0,
            expenses: data.expenses || 0,
            teams: data.teams || [],
            teams_info: data.teams_info || [],
            players: data.players || [], // Verwende die Spielerdaten aus der API
            upcomingMatches: data.upcomingMatches || [],
            recentMatches: data.recentMatches || []
          };

          // Überprüfe, ob ein Emblem-URL vorhanden ist
          if (data.emblem_url) {
            console.log(`Club ${data.name} hat ein Emblem: ${data.emblem_url}`);
          } else {
            console.log(`Club ${data.name} hat kein Emblem`);
          }

          setClub(processedClub);

          // Initialize cheat form with club data
          setCheatForm({
            name: data.name,
            founded: data.founded || 2000,
            reputation: data.reputation || 50,
            fans: data.fans || 1000,
            training_facilities: data.training_facilities || 50,
            coaching: data.coaching || 50,
            lane_quality: data.lane_quality || 1.0
          });
        } else {
          console.error(`Keine Daten für Club ${id} gefunden`);
        }

        // Load leagues for team creation
        const leaguesData = await getLeagues();
        setLeagues(leaguesData);

        // Check season status
        const seasonStatus = await getSeasonStatus();
        setSeasonCompleted(seasonStatus.is_completed);

        setLoading(false);
      } catch (error) {
        console.error(`Fehler beim Laden der Daten für Club ${id}:`, error);
        setLoading(false);
      }
    };

    loadData();
  }, [id]);

  if (loading) {
    return <div className="loading">Lade Vereinsdaten...</div>;
  }

  if (!club) {
    return <div className="error">Verein nicht gefunden</div>;
  }

  // Handle form input changes
  const handleCheatInputChange = (e) => {
    const { name, value } = e.target;
    setCheatForm({
      ...cheatForm,
      [name]: name === 'name' ? value : Number(value)
    });
  };

  // Handle form submission
  const handleCheatSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveMessage({ show: false, type: '', text: '' });

    try {
      const response = await updateClub(id, cheatForm);
      console.log('Club update response:', response);

      // Update the club state with the new data
      setClub({
        ...club,
        ...response.club
      });

      setSaveMessage({
        show: true,
        type: 'success',
        text: 'Vereinsdaten erfolgreich aktualisiert!'
      });
    } catch (error) {
      console.error('Error updating club:', error);
      setSaveMessage({
        show: true,
        type: 'error',
        text: `Fehler beim Aktualisieren: ${error.message}`
      });
    } finally {
      setSaving(false);
    }
  };

  // Handle add team modal
  const handleAddTeamClick = () => {
    setShowAddTeamModal(true);
    setSelectedLeague('');
    setTeamName('');
  };

  const handleAddTeamSubmit = async (e) => {
    e.preventDefault();
    if (!selectedLeague) {
      alert('Bitte wählen Sie eine Liga aus.');
      return;
    }

    setAddingTeam(true);
    try {
      const response = await addTeamToClub(id, {
        league_id: selectedLeague,
        team_name: teamName || undefined
      });

      setSaveMessage({
        show: true,
        type: 'success',
        text: response.message
      });

      setShowAddTeamModal(false);

      // Reload club data to show the new team
      const updatedClub = await getClub(id);
      setClub(updatedClub);

    } catch (error) {
      console.error('Error adding team:', error);
      setSaveMessage({
        show: true,
        type: 'error',
        text: `Fehler beim Hinzufügen der Mannschaft: ${error.response?.data?.error || error.message}`
      });
    } finally {
      setAddingTeam(false);
    }
  };

  return (
    <div className="club-detail-page">
      <div className="page-header">
        <div className="breadcrumbs">
          <Link to="/clubs">Vereine</Link> / {club.name}
        </div>
      </div>

      <div className="club-profile card">
        <div className="club-header">
          <div className="club-logo">
            {club.emblem_url ? (
              <img
                src={club.emblem_url}
                alt={`${club.name} Wappen`}
                className="club-emblem"
                onError={(e) => {
                  console.log(`Fehler beim Laden des Emblems für ${club.name}:`, e);
                  e.target.style.display = 'none';
                  e.target.parentNode.innerHTML = `<span>${club.name.split(' ').map(word => word[0]).join('')}</span>`;
                }}
              />
            ) : (
              <span>{club.name.split(' ').map(word => word[0]).join('')}</span>
            )}
          </div>
          <div className="club-header-info">
            <h1 className="club-name">{club.name}</h1>
            <div className="club-meta">
              <span className="club-founded">Gegründet: {club.founded}</span>
              <span className="club-reputation">Reputation: {club.reputation}/100</span>
            </div>
          </div>
          <div className="club-finances">
            <div className="finance-item">
              <span className="finance-label">Kontostand:</span>
              <span className="finance-value">€{club.balance.toLocaleString()}</span>
            </div>
            <div className="finance-item">
              <span className="finance-label">Einnahmen:</span>
              <span className="finance-value positive">+€{club.income.toLocaleString()}</span>
            </div>
            <div className="finance-item">
              <span className="finance-label">Ausgaben:</span>
              <span className="finance-value negative">-€{club.expenses.toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="club-tabs">
          <div
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Übersicht
          </div>
          <div
            className={`tab ${activeTab === 'teams' ? 'active' : ''}`}
            onClick={() => setActiveTab('teams')}
          >
            Mannschaften
          </div>
          <div
            className={`tab ${activeTab === 'players' ? 'active' : ''}`}
            onClick={() => setActiveTab('players')}
          >
            Spieler
          </div>
          <div
            className={`tab ${activeTab === 'matches' ? 'active' : ''}`}
            onClick={() => setActiveTab('matches')}
          >
            Spiele
          </div>
          <div
            className={`tab ${activeTab === 'finances' ? 'active' : ''}`}
            onClick={() => setActiveTab('finances')}
          >
            Finanzen
          </div>
          <div
            className={`tab ${activeTab === 'records' ? 'active' : ''}`}
            onClick={() => setActiveTab('records')}
          >
            Bahnrekorde
          </div>
          <div
            className={`tab ${activeTab === 'cheat' ? 'active' : ''}`}
            onClick={() => setActiveTab('cheat')}
          >
            Cheat
          </div>
        </div>

        <div className="club-content">
          {activeTab === 'overview' && (
            <div className="overview-tab">
              <div className="overview-grid">
                <div className="overview-card">
                  <h3>Mannschaften</h3>
                  <div className="teams-list">
                    {(club.teams_info || []).map(team => (
                      <Link to={`/teams/${team.id}`} key={team.id} className="team-item">
                        <div className="team-item-logo">
                          {team.emblem_url ? (
                            <img
                              src={team.emblem_url}
                              alt={`${club.name} Wappen`}
                              className="team-item-emblem"
                              onError={(e) => {
                                console.log(`Fehler beim Laden des Emblems für ${club.name}:`, e);
                                e.target.style.display = 'none';
                                e.target.parentNode.innerHTML = `<span>${team.name.charAt(0)}</span>`;
                              }}
                            />
                          ) : (
                            <span>{team.name.charAt(0)}</span>
                          )}
                        </div>
                        <div className="team-item-content">
                          <span className="team-name">{team.name}</span>
                          <div className="team-info">
                            <span className="team-league">{team.league}</span>
                            <span className="team-position">Pos: {team.position}</span>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>

                <div className="overview-card">
                  <h3>Top Spieler</h3>
                  <div className="players-list">
                    {club.players.slice(0, 5).map(player => (
                      <Link to={`/players/${player.id}`} key={player.id} className="player-item">
                        <span className="player-name">{player.name}</span>
                        <div className="player-info">
                          <span className="player-position">{player.position}</span>
                          <span className="player-strength">{Math.floor(player.strength)}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              </div>

              <div className="overview-grid">
                <div className="overview-card">
                  <h3>Nächste Spiele</h3>
                  <div className="matches-list">
                    {club.upcomingMatches.map(match => (
                      <Link to={`/matches/${match.id}`} key={match.id} className="match-item">
                        <div className="match-date">
                          {new Date(match.date).toLocaleDateString('de-DE', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                        <div className="match-teams">
                          <span className={`team ${match.homeTeam === club.name ? 'home' : ''}`}>
                            {match.homeTeam}
                          </span>
                          <span className="vs">vs</span>
                          <span className={`team ${match.awayTeam === club.name ? 'home' : ''}`}>
                            {match.awayTeam}
                          </span>
                        </div>
                        <div className="match-league">{match.league}</div>
                      </Link>
                    ))}
                  </div>
                </div>

                <div className="overview-card">
                  <h3>Letzte Ergebnisse</h3>
                  <div className="matches-list">
                    {club.recentMatches.map(match => (
                      <Link to={`/matches/${match.id}`} key={match.id} className="match-item">
                        <div className="match-date">
                          {new Date(match.date).toLocaleDateString('de-DE', {
                            day: '2-digit',
                            month: '2-digit'
                          })}
                        </div>
                        <div className="match-teams">
                          <span className={`team ${match.homeTeam === club.name ? 'home' : ''}`}>
                            {match.homeTeam}
                          </span>
                          <span className="score">
                            {match.homeScore} - {match.awayScore}
                          </span>
                          <span className={`team ${match.awayTeam === club.name ? 'home' : ''}`}>
                            {match.awayTeam}
                          </span>
                        </div>
                        <div className="match-league">{match.league}</div>
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'teams' && (
            <div className="teams-tab">
              <div className="teams-grid">
                {(club.teams_info || []).map(team => (
                  <div key={team.id} className="team-card">
                    <div className="team-header">
                      <div className="team-logo">
                        {team.emblem_url ? (
                          <img
                            src={team.emblem_url}
                            alt={`${club.name} Wappen`}
                            className="club-emblem"
                            onError={(e) => {
                              console.log(`Fehler beim Laden des Emblems für ${club.name}:`, e);
                              e.target.style.display = 'none';
                              e.target.parentNode.innerHTML = `<span>${team.name.split(' ').map(word => word[0]).join('')}</span>`;
                            }}
                          />
                        ) : (
                          <span>{team.name.split(' ').map(word => word[0]).join('')}</span>
                        )}
                      </div>
                      <div className="team-title-container">
                        <h3 className="team-title">{team.name}</h3>
                        <div className="team-badge">
                          {team.is_youth_team ? 'Jugend' : 'Senior'}
                        </div>
                      </div>
                    </div>
                    <div className="team-details">
                      <div className="team-detail">
                        <span className="detail-label">Liga:</span>
                        <span className="detail-value">{team.league}</span>
                      </div>
                      <div className="team-detail">
                        <span className="detail-label">Position:</span>
                        <span className="detail-value">{team.position}.</span>
                      </div>
                    </div>
                    <Link to={`/teams/${team.id}`} className="btn btn-primary team-btn">
                      Details anzeigen
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'players' && (
            <div className="players-tab">
              <table className="table players-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Alter</th>
                    <th>Position</th>
                    <th>Stärke</th>
                    <th>Mannschaft</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {club.players.map(player => (
                    <tr key={player.id}>
                      <td>
                        <Link to={`/players/${player.id}`} className="player-name-link">
                          {player.name}
                        </Link>
                      </td>
                      <td>{player.age}</td>
                      <td>{player.position}</td>
                      <td>
                        <div className="strength-display">
                          <div className="strength-bar">
                            <div
                              className="strength-fill"
                              style={{ width: `${player.strength}%` }}
                            ></div>
                          </div>
                          <span>{Math.floor(player.strength)}</span>
                        </div>
                      </td>
                      <td>{player.team}</td>
                      <td>
                        <div className="actions">
                          <Link to={`/players/${player.id}`} className="btn btn-small">
                            Details
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'matches' && (
            <div className="matches-tab">
              <h3>Nächste Spiele</h3>
              <table className="table matches-table">
                <thead>
                  <tr>
                    <th>Datum</th>
                    <th>Heimteam</th>
                    <th>Auswärtsteam</th>
                    <th>Liga</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {club.upcomingMatches.map(match => (
                    <tr key={match.id}>
                      <td>
                        {new Date(match.date).toLocaleDateString('de-DE', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className={match.homeTeam === club.name ? 'home-team' : ''}>
                        {match.homeTeam}
                      </td>
                      <td className={match.awayTeam === club.name ? 'home-team' : ''}>
                        {match.awayTeam}
                      </td>
                      <td>{match.league}</td>
                      <td>
                        <Link to={`/matches/${match.id}`} className="btn btn-small">
                          Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <h3>Letzte Ergebnisse</h3>
              <table className="table matches-table">
                <thead>
                  <tr>
                    <th>Datum</th>
                    <th>Heimteam</th>
                    <th>Ergebnis</th>
                    <th>Auswärtsteam</th>
                    <th>Liga</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {club.recentMatches.map(match => (
                    <tr key={match.id}>
                      <td>
                        {new Date(match.date).toLocaleDateString('de-DE', {
                          day: '2-digit',
                          month: '2-digit'
                        })}
                      </td>
                      <td className={match.homeTeam === club.name ? 'home-team' : ''}>
                        {match.homeTeam}
                      </td>
                      <td>
                        <strong>{match.homeScore} - {match.awayScore}</strong>
                      </td>
                      <td className={match.awayTeam === club.name ? 'home-team' : ''}>
                        {match.awayTeam}
                      </td>
                      <td>{match.league}</td>
                      <td>
                        <Link to={`/matches/${match.id}`} className="btn btn-small">
                          Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'finances' && (
            <div className="finances-tab">
              <div className="finances-overview">
                <div className="finance-summary">
                  <h3>Finanzübersicht</h3>
                  <div className="finance-balance">
                    <span className="balance-label">Aktueller Kontostand:</span>
                    <span className="balance-value">€{club.finances.balance.toLocaleString()}</span>
                  </div>

                  <div className="finance-chart">
                    <div className="chart-placeholder">
                      [Hier würde ein Finanz-Chart angezeigt werden]
                    </div>
                  </div>
                </div>

                <div className="finance-details">
                  <div className="income-section">
                    <h3>Einnahmen (monatlich)</h3>
                    <div className="finance-list">
                      {Object.entries(club.finances.income).map(([key, value]) => (
                        <div key={key} className="finance-list-item">
                          <span className="item-label">{key.charAt(0).toUpperCase() + key.slice(1)}:</span>
                          <span className="item-value positive">€{value.toLocaleString()}</span>
                        </div>
                      ))}
                      <div className="finance-list-item total">
                        <span className="item-label">Gesamt:</span>
                        <span className="item-value positive">
                          €{Object.values(club.finances.income).reduce((a, b) => a + b, 0).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="expenses-section">
                    <h3>Ausgaben (monatlich)</h3>
                    <div className="finance-list">
                      {Object.entries(club.finances.expenses).map(([key, value]) => (
                        <div key={key} className="finance-list-item">
                          <span className="item-label">{key.charAt(0).toUpperCase() + key.slice(1)}:</span>
                          <span className="item-value negative">€{value.toLocaleString()}</span>
                        </div>
                      ))}
                      <div className="finance-list-item total">
                        <span className="item-label">Gesamt:</span>
                        <span className="item-value negative">
                          €{Object.values(club.finances.expenses).reduce((a, b) => a + b, 0).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'records' && (
            <div className="records-tab">
              <h3>Bahnrekorde</h3>
              <div className="info-text">
                Hier werden alle Bahnrekorde angezeigt, die auf den Bahnen dieses Vereins erzielt wurden.
              </div>

              <div className="records-section">
                <h4>Mannschaftsrekorde</h4>
                {club.lane_records && club.lane_records.team && club.lane_records.team.length > 0 ? (
                  <table className="table records-table">
                    <thead>
                      <tr>
                        <th>Mannschaft</th>
                        <th>Ergebnis</th>
                        <th>Datum</th>
                      </tr>
                    </thead>
                    <tbody>
                      {club.lane_records.team.sort((a, b) => b.score - a.score).map(record => (
                        <tr key={`team-${record.id}`}>
                          <td>{record.team_name}</td>
                          <td className="record-score">{record.score}</td>
                          <td>{new Date(record.record_date).toLocaleDateString('de-DE')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="no-records">Noch keine Mannschaftsrekorde vorhanden.</p>
                )}
              </div>

              <div className="records-section">
                <h4>Einzelrekorde - Herren</h4>
                {club.lane_records && club.lane_records.individual && club.lane_records.individual.Herren && club.lane_records.individual.Herren.length > 0 ? (
                  <table className="table records-table">
                    <thead>
                      <tr>
                        <th>Spieler</th>
                        <th>Ergebnis</th>
                        <th>Datum</th>
                      </tr>
                    </thead>
                    <tbody>
                      {club.lane_records.individual.Herren.sort((a, b) => b.score - a.score).map(record => (
                        <tr key={`herren-${record.id}`}>
                          <td>{record.player_name}</td>
                          <td className="record-score">{record.score}</td>
                          <td>{new Date(record.record_date).toLocaleDateString('de-DE')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="no-records">Noch keine Herren-Einzelrekorde vorhanden.</p>
                )}
              </div>

              <div className="records-section">
                <h4>Einzelrekorde - U19</h4>
                {club.lane_records && club.lane_records.individual && club.lane_records.individual.U19 && club.lane_records.individual.U19.length > 0 ? (
                  <table className="table records-table">
                    <thead>
                      <tr>
                        <th>Spieler</th>
                        <th>Ergebnis</th>
                        <th>Datum</th>
                      </tr>
                    </thead>
                    <tbody>
                      {club.lane_records.individual.U19.sort((a, b) => b.score - a.score).map(record => (
                        <tr key={`u19-${record.id}`}>
                          <td>{record.player_name}</td>
                          <td className="record-score">{record.score}</td>
                          <td>{new Date(record.record_date).toLocaleDateString('de-DE')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="no-records">Noch keine U19-Einzelrekorde vorhanden.</p>
                )}
              </div>

              <div className="records-section">
                <h4>Einzelrekorde - U14</h4>
                {club.lane_records && club.lane_records.individual && club.lane_records.individual.U14 && club.lane_records.individual.U14.length > 0 ? (
                  <table className="table records-table">
                    <thead>
                      <tr>
                        <th>Spieler</th>
                        <th>Ergebnis</th>
                        <th>Datum</th>
                      </tr>
                    </thead>
                    <tbody>
                      {club.lane_records.individual.U14.sort((a, b) => b.score - a.score).map(record => (
                        <tr key={`u14-${record.id}`}>
                          <td>{record.player_name}</td>
                          <td className="record-score">{record.score}</td>
                          <td>{new Date(record.record_date).toLocaleDateString('de-DE')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="no-records">Noch keine U14-Einzelrekorde vorhanden.</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'cheat' && (
            <div className="cheat-tab">
              <h3>Cheat-Modus: Vereinsattribute bearbeiten</h3>
              <p className="info-text">
                Hier können Sie die Attribute des Vereins bearbeiten. Diese Änderungen wirken sich sofort auf das Spielgeschehen aus.
              </p>

              {saveMessage.show && (
                <div className={`message ${saveMessage.type}`}>
                  {saveMessage.text}
                </div>
              )}

              <form className="cheat-form" onSubmit={handleCheatSubmit}>
                <div className="form-grid">
                  <div className="form-section">
                    <h4>Allgemeine Informationen</h4>

                    <div className="form-group">
                      <label htmlFor="name">Vereinsname:</label>
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
                      <label htmlFor="founded">Gründungsjahr:</label>
                      <input
                        type="number"
                        id="founded"
                        name="founded"
                        min="1800"
                        max={new Date().getFullYear()}
                        value={cheatForm.founded || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="reputation">Reputation (1-100):</label>
                      <input
                        type="number"
                        id="reputation"
                        name="reputation"
                        min="1"
                        max="100"
                        value={cheatForm.reputation || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>
                  </div>

                  <div className="form-section">
                    <h4>Vereinsattribute</h4>

                    <div className="form-group">
                      <label htmlFor="fans">Fans:</label>
                      <input
                        type="number"
                        id="fans"
                        name="fans"
                        min="0"
                        step="100"
                        value={cheatForm.fans || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="training_facilities">Trainingseinrichtungen (1-100):</label>
                      <input
                        type="number"
                        id="training_facilities"
                        name="training_facilities"
                        min="1"
                        max="100"
                        value={cheatForm.training_facilities || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="coaching">Trainerqualität (1-100):</label>
                      <input
                        type="number"
                        id="coaching"
                        name="coaching"
                        min="1"
                        max="100"
                        value={cheatForm.coaching || ''}
                        onChange={handleCheatInputChange}
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="lane_quality">Bahnqualität (0.9-1.05):</label>
                      <input
                        type="number"
                        id="lane_quality"
                        name="lane_quality"
                        min="0.9"
                        max="1.05"
                        step="0.01"
                        value={cheatForm.lane_quality || ''}
                        onChange={handleCheatInputChange}
                      />
                      <div className="input-help">
                        Beeinflusst die Ergebnisse aller Spieler auf dieser Bahn.
                        Höhere Werte führen zu besseren Ergebnissen.
                      </div>
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

              <div className="cheat-section">
                <h4>Mannschaftsverwaltung</h4>
                <p className="info-text">
                  Hier können Sie neue Mannschaften für die nächste Saison hinzufügen.
                </p>

                <div className="form-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleAddTeamClick}
                    disabled={!seasonCompleted}
                    title={!seasonCompleted ? 'Diese Funktion ist nur nach dem letzten Spieltag verfügbar' : 'Neue Mannschaft hinzufügen'}
                  >
                    Mannschaft hinzufügen
                  </button>
                  {!seasonCompleted && (
                    <p className="warning-text">
                      Diese Funktion ist nur nach dem letzten Spieltag verfügbar.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Add Team Modal */}
          {showAddTeamModal && (
            <div className="modal-overlay" onClick={() => setShowAddTeamModal(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Neue Mannschaft hinzufügen</h3>
                  <button
                    className="modal-close"
                    onClick={() => setShowAddTeamModal(false)}
                  >
                    ×
                  </button>
                </div>

                <form onSubmit={handleAddTeamSubmit}>
                  <div className="modal-body">
                    <div className="form-group">
                      <label htmlFor="teamName">Mannschaftsname (optional):</label>
                      <input
                        type="text"
                        id="teamName"
                        value={teamName}
                        onChange={(e) => setTeamName(e.target.value)}
                        placeholder={`${club?.name} ${(club?.teams_info?.length || 0) + 1}`}
                      />
                      <div className="input-help">
                        Leer lassen für automatischen Namen
                      </div>
                    </div>

                    <div className="form-group">
                      <label htmlFor="targetLeague">Ziel-Liga:</label>
                      <select
                        id="targetLeague"
                        value={selectedLeague}
                        onChange={(e) => setSelectedLeague(e.target.value)}
                        required
                      >
                        <option value="">Liga auswählen...</option>
                        {leagues.map(league => (
                          <option key={league.id} value={league.id}>
                            {league.name} (Level {league.level})
                          </option>
                        ))}
                      </select>
                      <div className="input-help">
                        Die Mannschaft wird zur nächsten Saison zu dieser Liga hinzugefügt
                      </div>
                    </div>
                  </div>

                  <div className="modal-footer">
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setShowAddTeamModal(false)}
                      disabled={addingTeam}
                    >
                      Abbrechen
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={addingTeam || !selectedLeague}
                    >
                      {addingTeam ? 'Hinzufügen...' : 'Mannschaft hinzufügen'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClubDetail;
