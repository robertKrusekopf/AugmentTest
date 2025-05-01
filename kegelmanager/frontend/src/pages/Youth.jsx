import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Youth.css';

const Youth = () => {
  const [loading, setLoading] = useState(true);
  const [youthData, setYouthData] = useState(null);
  const [activeTab, setActiveTab] = useState('academy');
  
  // Simulierte Daten für die Demonstration
  useEffect(() => {
    // In einer echten Anwendung würden wir hier die API aufrufen
    
    // Simulierte Daten
    setTimeout(() => {
      const mockYouthData = {
        academy: {
          level: 7,
          nextUpgradeCost: 250000,
          facilities: {
            training: 6,
            scouting: 5,
            coaching: 6
          },
          budget: 50000,
          youthPlayers: [
            { id: 101, name: 'Jonas Müller', age: 16, position: 'Mittelfeld', potential: 9, progress: 65 },
            { id: 102, name: 'Lukas Schmidt', age: 17, position: 'Angriff', potential: 8, progress: 72 },
            { id: 103, name: 'Tim Weber', age: 15, position: 'Abwehr', potential: 10, progress: 58 },
            { id: 104, name: 'Felix Becker', age: 16, position: 'Mittelfeld', potential: 7, progress: 68 },
            { id: 105, name: 'Niklas Fischer', age: 17, position: 'Angriff', potential: 8, progress: 75 },
            { id: 106, name: 'Jan Hoffmann', age: 15, position: 'Abwehr', potential: 9, progress: 60 }
          ]
        },
        youthTeam: {
          name: 'Kegel Sport Club U19',
          league: '3. Liga',
          position: 2,
          matches: [
            { id: 201, date: '2025-07-14', home: 'Kegel Sport Club U19', away: 'Kegel SV U19', result: '3-0', played: true },
            { id: 202, date: '2025-07-21', home: 'SV Kegelfreunde U19', away: 'Kegel Sport Club U19', result: '1-2', played: true },
            { id: 203, date: '2025-07-28', home: 'Kegel Sport Club U19', away: 'TSV Kegelhausen U19', result: '2-1', played: true },
            { id: 204, date: '2025-08-18', home: 'FC Kegelsport U19', away: 'Kegel Sport Club U19', result: null, played: false }
          ],
          players: [
            { id: 201, name: 'Jonas Müller', age: 16, position: 'Mittelfeld', strength: 65, talent: 9 },
            { id: 202, name: 'Lukas Schmidt', age: 17, position: 'Angriff', strength: 72, talent: 8 },
            { id: 203, name: 'Tim Weber', age: 15, position: 'Abwehr', strength: 58, talent: 10 },
            { id: 204, name: 'Felix Becker', age: 16, position: 'Mittelfeld', strength: 68, talent: 7 },
            { id: 205, name: 'Niklas Fischer', age: 17, position: 'Angriff', strength: 75, talent: 8 },
            { id: 206, name: 'Jan Hoffmann', age: 15, position: 'Abwehr', strength: 60, talent: 9 },
            { id: 207, name: 'David Wagner', age: 18, position: 'Mittelfeld', strength: 78, talent: 7 },
            { id: 208, name: 'Simon Koch', age: 18, position: 'Angriff', strength: 76, talent: 6 },
            { id: 209, name: 'Leon Bauer', age: 17, position: 'Abwehr', strength: 70, talent: 8 },
            { id: 210, name: 'Max Schneider', age: 16, position: 'Mittelfeld', strength: 67, talent: 9 },
            { id: 211, name: 'Philipp Meyer', age: 18, position: 'Angriff', strength: 74, talent: 7 }
          ]
        },
        development: {
          recentPromotions: [
            { id: 301, name: 'Thomas Schulz', age: 19, position: 'Mittelfeld', promoted: '2025-06-15', team: 'Kegel Sport Club II' },
            { id: 302, name: 'Michael Hoffmann', age: 19, position: 'Angriff', promoted: '2025-06-15', team: 'Kegel Sport Club II' },
            { id: 303, name: 'Kevin Fischer', age: 19, position: 'Abwehr', promoted: '2025-05-30', team: 'Kegel Sport Club' }
          ],
          upcomingTalents: [
            { id: 401, name: 'Tim Weber', age: 15, position: 'Abwehr', potential: 10, readiness: 35 },
            { id: 402, name: 'Jonas Müller', age: 16, position: 'Mittelfeld', potential: 9, readiness: 42 },
            { id: 403, name: 'Jan Hoffmann', age: 15, position: 'Abwehr', potential: 9, readiness: 38 }
          ]
        }
      };
      
      setYouthData(mockYouthData);
      setLoading(false);
    }, 1000);
  }, []);
  
  if (loading) {
    return <div className="loading">Lade Jugenddaten...</div>;
  }
  
  if (!youthData) {
    return <div className="error">Jugenddaten konnten nicht geladen werden</div>;
  }
  
  return (
    <div className="youth-page">
      <h1 className="page-title">Jugendentwicklung</h1>
      
      <div className="youth-tabs card">
        <div className="tabs">
          <div 
            className={`tab ${activeTab === 'academy' ? 'active' : ''}`}
            onClick={() => setActiveTab('academy')}
          >
            Jugendakademie
          </div>
          <div 
            className={`tab ${activeTab === 'team' ? 'active' : ''}`}
            onClick={() => setActiveTab('team')}
          >
            Jugendmannschaft
          </div>
          <div 
            className={`tab ${activeTab === 'development' ? 'active' : ''}`}
            onClick={() => setActiveTab('development')}
          >
            Entwicklung
          </div>
        </div>
        
        <div className="tab-content">
          {activeTab === 'academy' && (
            <div className="academy-tab">
              <div className="academy-header">
                <div className="academy-info">
                  <h2>Jugendakademie</h2>
                  <div className="academy-level">
                    <span className="level-label">Level:</span>
                    <div className="level-stars">
                      {Array.from({ length: 10 }, (_, i) => (
                        <span 
                          key={i} 
                          className={`star ${i < youthData.academy.level ? 'filled' : ''}`}
                        >★</span>
                      ))}
                    </div>
                  </div>
                  <div className="academy-budget">
                    <span className="budget-label">Budget:</span>
                    <span className="budget-value">€{youthData.academy.budget.toLocaleString()}</span>
                  </div>
                </div>
                <div className="academy-actions">
                  <button className="btn btn-primary">
                    Akademie ausbauen (€{youthData.academy.nextUpgradeCost.toLocaleString()})
                  </button>
                </div>
              </div>
              
              <div className="facilities-section">
                <h3>Einrichtungen</h3>
                <div className="facilities-grid">
                  <div className="facility-card">
                    <h4>Trainingsanlagen</h4>
                    <div className="facility-level">
                      <div className="level-stars">
                        {Array.from({ length: 10 }, (_, i) => (
                          <span 
                            key={i} 
                            className={`star ${i < youthData.academy.facilities.training ? 'filled' : ''}`}
                          >★</span>
                        ))}
                      </div>
                    </div>
                    <p className="facility-description">
                      Bessere Trainingsanlagen erhöhen die Entwicklungsgeschwindigkeit der Jugendspieler.
                    </p>
                    <button className="btn btn-secondary facility-btn">
                      Verbessern (€75,000)
                    </button>
                  </div>
                  
                  <div className="facility-card">
                    <h4>Scouting-Netzwerk</h4>
                    <div className="facility-level">
                      <div className="level-stars">
                        {Array.from({ length: 10 }, (_, i) => (
                          <span 
                            key={i} 
                            className={`star ${i < youthData.academy.facilities.scouting ? 'filled' : ''}`}
                          >★</span>
                        ))}
                      </div>
                    </div>
                    <p className="facility-description">
                      Ein besseres Scouting-Netzwerk erhöht die Chance, talentierte Jugendspieler zu finden.
                    </p>
                    <button className="btn btn-secondary facility-btn">
                      Verbessern (€60,000)
                    </button>
                  </div>
                  
                  <div className="facility-card">
                    <h4>Trainerstab</h4>
                    <div className="facility-level">
                      <div className="level-stars">
                        {Array.from({ length: 10 }, (_, i) => (
                          <span 
                            key={i} 
                            className={`star ${i < youthData.academy.facilities.coaching ? 'filled' : ''}`}
                          >★</span>
                        ))}
                      </div>
                    </div>
                    <p className="facility-description">
                      Ein besserer Trainerstab maximiert das Potenzial der Jugendspieler.
                    </p>
                    <button className="btn btn-secondary facility-btn">
                      Verbessern (€70,000)
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="youth-players-section">
                <h3>Akademie-Spieler</h3>
                <table className="table youth-players-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Alter</th>
                      <th>Position</th>
                      <th>Potenzial</th>
                      <th>Fortschritt</th>
                      <th>Aktionen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {youthData.academy.youthPlayers.map(player => (
                      <tr key={player.id}>
                        <td>{player.name}</td>
                        <td>{player.age}</td>
                        <td>{player.position}</td>
                        <td>
                          <div className="talent-stars">
                            {Array.from({ length: 10 }, (_, i) => (
                              <span 
                                key={i} 
                                className={`star ${i < player.potential ? 'filled' : ''}`}
                              >★</span>
                            ))}
                          </div>
                        </td>
                        <td>
                          <div className="progress-bar">
                            <div 
                              className="progress-fill" 
                              style={{ width: `${player.progress}%` }}
                            ></div>
                          </div>
                          <span className="progress-text">{player.progress}%</span>
                        </td>
                        <td>
                          <button className="btn btn-small">
                            Fördern
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="academy-actions center">
                  <button className="btn btn-primary">
                    Neue Talente scouten (€15,000)
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'team' && (
            <div className="team-tab">
              <div className="team-header">
                <div className="team-info">
                  <h2>{youthData.youthTeam.name}</h2>
                  <div className="team-meta">
                    <span className="team-league">{youthData.youthTeam.league}</span>
                    <span className="team-position">{youthData.youthTeam.position}. Platz</span>
                  </div>
                </div>
                <div className="team-actions">
                  <button className="btn btn-primary">
                    Mannschaft verwalten
                  </button>
                </div>
              </div>
              
              <div className="team-matches">
                <h3>Spiele</h3>
                <div className="matches-list">
                  {youthData.youthTeam.matches.map(match => (
                    <div key={match.id} className="match-item">
                      <div className="match-date">
                        {new Date(match.date).toLocaleDateString('de-DE')}
                      </div>
                      <div className="match-teams">
                        <span className={`team ${match.home === youthData.youthTeam.name ? 'home' : ''}`}>
                          {match.home}
                        </span>
                        {match.played ? (
                          <span className="score">{match.result}</span>
                        ) : (
                          <span className="vs">vs</span>
                        )}
                        <span className={`team ${match.away === youthData.youthTeam.name ? 'home' : ''}`}>
                          {match.away}
                        </span>
                      </div>
                      <div className="match-status">
                        {match.played ? (
                          <span className="badge badge-success">Gespielt</span>
                        ) : (
                          <span className="badge">Anstehend</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="team-players">
                <h3>Spieler</h3>
                <table className="table players-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Alter</th>
                      <th>Position</th>
                      <th>Stärke</th>
                      <th>Talent</th>
                      <th>Aktionen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {youthData.youthTeam.players.map(player => (
                      <tr key={player.id}>
                        <td>{player.name}</td>
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
                        <td>
                          <div className="talent-stars">
                            {Array.from({ length: 10 }, (_, i) => (
                              <span 
                                key={i} 
                                className={`star ${i < player.talent ? 'filled' : ''}`}
                              >★</span>
                            ))}
                          </div>
                        </td>
                        <td>
                          <div className="actions">
                            <button className="btn btn-small">
                              Details
                            </button>
                            {player.age >= 18 && (
                              <button className="btn btn-small promote-btn">
                                Befördern
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          
          {activeTab === 'development' && (
            <div className="development-tab">
              <div className="development-section">
                <h3>Kürzlich beförderte Spieler</h3>
                <div className="promotions-list">
                  {youthData.development.recentPromotions.map(player => (
                    <div key={player.id} className="promotion-item">
                      <div className="player-info">
                        <h4 className="player-name">{player.name}</h4>
                        <div className="player-meta">
                          <span className="player-age">{player.age} Jahre</span>
                          <span className="player-position">{player.position}</span>
                        </div>
                      </div>
                      <div className="promotion-details">
                        <div className="promotion-date">
                          Befördert am: {new Date(player.promoted).toLocaleDateString('de-DE')}
                        </div>
                        <div className="promotion-team">
                          Aktuelle Mannschaft: {player.team}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="development-section">
                <h3>Vielversprechende Talente</h3>
                <div className="talents-grid">
                  {youthData.development.upcomingTalents.map(player => (
                    <div key={player.id} className="talent-card">
                      <h4 className="player-name">{player.name}</h4>
                      <div className="player-details">
                        <div className="player-detail">
                          <span className="detail-label">Alter:</span>
                          <span className="detail-value">{player.age}</span>
                        </div>
                        <div className="player-detail">
                          <span className="detail-label">Position:</span>
                          <span className="detail-value">{player.position}</span>
                        </div>
                        <div className="player-detail">
                          <span className="detail-label">Potenzial:</span>
                          <div className="talent-stars">
                            {Array.from({ length: 10 }, (_, i) => (
                              <span 
                                key={i} 
                                className={`star ${i < player.potential ? 'filled' : ''}`}
                              >★</span>
                            ))}
                          </div>
                        </div>
                        <div className="player-detail">
                          <span className="detail-label">Bereitschaft:</span>
                          <div className="progress-bar">
                            <div 
                              className="progress-fill" 
                              style={{ width: `${player.readiness}%` }}
                            ></div>
                          </div>
                          <span className="progress-text">{player.readiness}%</span>
                        </div>
                      </div>
                      <div className="talent-actions">
                        <button className="btn btn-secondary">
                          Spezielles Training
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="development-section">
                <h3>Entwicklungsstrategie</h3>
                <div className="strategy-options">
                  <div className="strategy-option">
                    <h4>Fokus auf Talententwicklung</h4>
                    <p>
                      Konzentriert sich auf die langfristige Entwicklung von Spielern mit hohem Potenzial, 
                      auch wenn dies kurzfristig zu schlechteren Ergebnissen führen kann.
                    </p>
                    <button className="btn btn-primary">Auswählen</button>
                  </div>
                  
                  <div className="strategy-option active">
                    <h4>Ausgewogener Ansatz</h4>
                    <p>
                      Balanciert die Entwicklung von Talenten mit dem Streben nach guten Ergebnissen 
                      in der Jugendliga.
                    </p>
                    <button className="btn btn-primary">Ausgewählt</button>
                  </div>
                  
                  <div className="strategy-option">
                    <h4>Fokus auf Ergebnisse</h4>
                    <p>
                      Priorisiert gute Ergebnisse in der Jugendliga, was die Attraktivität des Vereins 
                      für junge Talente erhöhen kann.
                    </p>
                    <button className="btn btn-primary">Auswählen</button>
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

export default Youth;
