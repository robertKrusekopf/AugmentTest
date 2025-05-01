import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getClub } from '../services/api';
import './ClubDetail.css';

const ClubDetail = () => {
  const { id } = useParams();
  const [club, setClub] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Lade Daten aus der API
  useEffect(() => {
    console.log(`Lade Club mit ID ${id} aus der API...`);

    getClub(id)
      .then(data => {
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
        } else {
          console.error(`Keine Daten für Club ${id} gefunden`);
        }

        setLoading(false);
      })
      .catch(error => {
        console.error(`Fehler beim Laden des Clubs ${id}:`, error);
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return <div className="loading">Lade Vereinsdaten...</div>;
  }

  if (!club) {
    return <div className="error">Verein nicht gefunden</div>;
  }

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
                          <span className="player-strength">{player.strength}</span>
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
                          <span>{player.strength}</span>
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
        </div>
      </div>
    </div>
  );
};

export default ClubDetail;
