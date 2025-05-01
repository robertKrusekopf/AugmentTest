import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getPlayer } from '../services/api';
import './PlayerDetail.css';

const PlayerDetail = () => {
  const { id } = useParams();
  const [player, setPlayer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

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
            // Füge Statistiken hinzu (in einer echten Anwendung würden diese aus der Datenbank kommen)
            stats: {
              matches: 0,
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
              consistency: data.consistency || 0,
              precision: data.precision || 0,
              stamina: data.stamina || 0
            },
            // In einer echten Anwendung würden diese aus der Datenbank kommen
            history: [],
            development: []
          };

          setPlayer(processedPlayer);
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
          <button className="btn btn-primary">Transferangebot</button>
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
            </div>
          </div>
          <div className="player-ratings">
            <div className="rating-item">
              <span className="rating-label">Stärke</span>
              <span className="rating-value">{player.strength}</span>
              <div className="strength-bar">
                <div className="strength-fill" style={{ width: `${player.strength}%` }}></div>
              </div>
            </div>
            <div className="rating-item">
              <span className="rating-label">Talent</span>
              <div className="talent-stars">
                {Array.from({ length: 10 }, (_, i) => (
                  <span
                    key={i}
                    className={`star ${i < player.talent ? 'filled' : ''}`}
                  >★</span>
                ))}
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
                  <h3>Statistiken</h3>
                  <div className="info-list">
                    <div className="info-item">
                      <span className="info-label">Spiele:</span>
                      <span className="info-value">{player.stats.matches}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Tore:</span>
                      <span className="info-value">{player.stats.goals}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Vorlagen:</span>
                      <span className="info-value">{player.stats.assists}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Durchschnittliche Bewertung:</span>
                      <span className="info-value">{player.stats.rating}</span>
                    </div>
                  </div>
                </div>
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
                      <div className="attribute-fill" style={{ width: `${value}%` }}></div>
                    </div>
                    <span className="attribute-value">{value}</span>
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
                    const prevStrength = index > 0 ? player.development[index - 1].strength : dev.strength;
                    const change = dev.strength - prevStrength;

                    return (
                      <tr key={index}>
                        <td>{dev.age}</td>
                        <td>{dev.strength}</td>
                        <td className={change > 0 ? 'positive' : change < 0 ? 'negative' : ''}>
                          {change > 0 ? `+${change}` : change}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayerDetail;
