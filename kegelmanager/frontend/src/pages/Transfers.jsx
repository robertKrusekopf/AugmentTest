import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Transfers.css';

const Transfers = () => {
  const [loading, setLoading] = useState(true);
  const [transferData, setTransferData] = useState(null);
  const [activeTab, setActiveTab] = useState('market');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPosition, setFilterPosition] = useState('');
  const [filterAgeMin, setFilterAgeMin] = useState('');
  const [filterAgeMax, setFilterAgeMax] = useState('');
  
  // Simulierte Daten für die Demonstration
  useEffect(() => {
    // In einer echten Anwendung würden wir hier die API aufrufen
    
    // Simulierte Daten
    setTimeout(() => {
      const mockTransferData = {
        transferBudget: 500000,
        marketPlayers: [
          { id: 1, name: 'Thomas Schmidt', age: 31, position: 'Angriff', strength: 89, team: 'SV Kegelfreunde', value: 350000, salary: 45000 },
          { id: 2, name: 'Felix Müller', age: 24, position: 'Abwehr', strength: 87, team: 'TSV Kegelhausen', value: 400000, salary: 40000 },
          { id: 3, name: 'Jan Becker', age: 22, position: 'Mittelfeld', strength: 82, team: 'FC Kegelsport', value: 320000, salary: 35000 },
          { id: 4, name: 'Lukas Weber', age: 29, position: 'Angriff', strength: 85, team: 'Kegel Union', value: 330000, salary: 42000 },
          { id: 5, name: 'Niklas Fischer', age: 26, position: 'Abwehr', strength: 84, team: 'SC Kegeltal', value: 310000, salary: 38000 },
          { id: 6, name: 'Tim Hoffmann', age: 33, position: 'Angriff', strength: 86, team: 'SV Kegelfreunde', value: 280000, salary: 44000 },
          { id: 7, name: 'Jonas Schäfer', age: 21, position: 'Abwehr', strength: 78, team: 'TSV Kegelhausen', value: 250000, salary: 30000 },
          { id: 8, name: 'David Wagner', age: 25, position: 'Mittelfeld', strength: 83, team: 'FC Kegelsport', value: 300000, salary: 36000 }
        ],
        myOffers: [
          { 
            id: 101, 
            player: { id: 3, name: 'Jan Becker', age: 22, position: 'Mittelfeld', strength: 82, team: 'FC Kegelsport' },
            offerAmount: 350000,
            status: 'pending',
            date: '2025-07-25'
          },
          { 
            id: 102, 
            player: { id: 7, name: 'Jonas Schäfer', age: 21, position: 'Abwehr', strength: 78, team: 'TSV Kegelhausen' },
            offerAmount: 270000,
            status: 'accepted',
            date: '2025-07-23'
          }
        ],
        receivedOffers: [
          { 
            id: 201, 
            player: { id: 101, name: 'Max Mustermann', age: 28, position: 'Mittelfeld', strength: 92, team: 'Kegel Sport Club' },
            fromTeam: 'SV Kegelfreunde',
            offerAmount: 450000,
            status: 'pending',
            date: '2025-07-26'
          },
          { 
            id: 202, 
            player: { id: 102, name: 'Leon Schneider', age: 19, position: 'Mittelfeld', strength: 75, team: 'Kegel Sport Club' },
            fromTeam: 'TSV Kegelhausen',
            offerAmount: 200000,
            status: 'rejected',
            date: '2025-07-22'
          }
        ],
        transferHistory: [
          { 
            id: 301, 
            player: { name: 'Kevin Fischer', age: 27, position: 'Abwehr', strength: 86 },
            fromTeam: 'Kegel Sport Club',
            toTeam: 'SV Kegelfreunde',
            amount: 380000,
            date: '2025-06-15'
          },
          { 
            id: 302, 
            player: { name: 'Michael Hoffmann', age: 24, position: 'Mittelfeld', strength: 81 },
            fromTeam: 'TSV Kegelhausen',
            toTeam: 'Kegel Sport Club',
            amount: 320000,
            date: '2025-06-10'
          },
          { 
            id: 303, 
            player: { name: 'Simon Koch', age: 29, position: 'Angriff', strength: 88 },
            fromTeam: 'FC Kegelsport',
            toTeam: 'Kegel Union',
            amount: 410000,
            date: '2025-06-05'
          }
        ]
      };
      
      setTransferData(mockTransferData);
      setLoading(false);
    }, 1000);
  }, []);
  
  if (loading) {
    return <div className="loading">Lade Transferdaten...</div>;
  }
  
  if (!transferData) {
    return <div className="error">Transferdaten konnten nicht geladen werden</div>;
  }
  
  // Filtern der Spieler auf dem Transfermarkt
  const filteredPlayers = transferData.marketPlayers.filter(player => {
    const nameMatch = player.name.toLowerCase().includes(searchTerm.toLowerCase());
    const positionMatch = filterPosition === '' || player.position === filterPosition;
    const ageMinMatch = filterAgeMin === '' || player.age >= parseInt(filterAgeMin);
    const ageMaxMatch = filterAgeMax === '' || player.age <= parseInt(filterAgeMax);
    
    return nameMatch && positionMatch && ageMinMatch && ageMaxMatch;
  });
  
  return (
    <div className="transfers-page">
      <h1 className="page-title">Transfers</h1>
      
      <div className="transfer-budget-card">
        <div className="budget-info">
          <h3>Transferbudget</h3>
          <div className="budget-amount">€{transferData.transferBudget.toLocaleString()}</div>
        </div>
        <div className="budget-actions">
          <button className="btn btn-primary">Budget anpassen</button>
        </div>
      </div>
      
      <div className="transfers-tabs card">
        <div className="tabs">
          <div 
            className={`tab ${activeTab === 'market' ? 'active' : ''}`}
            onClick={() => setActiveTab('market')}
          >
            Transfermarkt
          </div>
          <div 
            className={`tab ${activeTab === 'my-offers' ? 'active' : ''}`}
            onClick={() => setActiveTab('my-offers')}
          >
            Meine Angebote
          </div>
          <div 
            className={`tab ${activeTab === 'received-offers' ? 'active' : ''}`}
            onClick={() => setActiveTab('received-offers')}
          >
            Erhaltene Angebote
          </div>
          <div 
            className={`tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            Transferhistorie
          </div>
        </div>
        
        <div className="tab-content">
          {activeTab === 'market' && (
            <div className="market-tab">
              <div className="filters">
                <div className="search-bar">
                  <input
                    type="text"
                    placeholder="Spieler suchen..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                  <button>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8"></circle>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                  </button>
                </div>
                
                <div className="filter-bar">
                  <select 
                    className="filter-select"
                    value={filterPosition}
                    onChange={(e) => setFilterPosition(e.target.value)}
                  >
                    <option value="">Alle Positionen</option>
                    <option value="Angriff">Angriff</option>
                    <option value="Mittelfeld">Mittelfeld</option>
                    <option value="Abwehr">Abwehr</option>
                  </select>
                  
                  <div className="age-filter">
                    <input
                      type="number"
                      placeholder="Min. Alter"
                      min="16"
                      max="40"
                      value={filterAgeMin}
                      onChange={(e) => setFilterAgeMin(e.target.value)}
                    />
                    <span>-</span>
                    <input
                      type="number"
                      placeholder="Max. Alter"
                      min="16"
                      max="40"
                      value={filterAgeMax}
                      onChange={(e) => setFilterAgeMax(e.target.value)}
                    />
                  </div>
                </div>
              </div>
              
              <table className="table market-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Alter</th>
                    <th>Position</th>
                    <th>Stärke</th>
                    <th>Verein</th>
                    <th>Marktwert</th>
                    <th>Gehalt</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPlayers.map(player => (
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
                      <td>{player.team}</td>
                      <td>€{player.value.toLocaleString()}</td>
                      <td>€{player.salary.toLocaleString()}</td>
                      <td>
                        <button className="btn btn-small">
                          Angebot machen
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {activeTab === 'my-offers' && (
            <div className="my-offers-tab">
              <h3>Meine Angebote</h3>
              <table className="table offers-table">
                <thead>
                  <tr>
                    <th>Spieler</th>
                    <th>Alter</th>
                    <th>Position</th>
                    <th>Stärke</th>
                    <th>Aktueller Verein</th>
                    <th>Angebotsbetrag</th>
                    <th>Datum</th>
                    <th>Status</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {transferData.myOffers.map(offer => (
                    <tr key={offer.id}>
                      <td>{offer.player.name}</td>
                      <td>{offer.player.age}</td>
                      <td>{offer.player.position}</td>
                      <td>
                        <div className="strength-display">
                          <div className="strength-bar">
                            <div 
                              className="strength-fill" 
                              style={{ width: `${offer.player.strength}%` }}
                            ></div>
                          </div>
                          <span>{offer.player.strength}</span>
                        </div>
                      </td>
                      <td>{offer.player.team}</td>
                      <td>€{offer.offerAmount.toLocaleString()}</td>
                      <td>{new Date(offer.date).toLocaleDateString('de-DE')}</td>
                      <td>
                        <span className={`status-badge ${offer.status}`}>
                          {offer.status === 'pending' ? 'Ausstehend' : 
                           offer.status === 'accepted' ? 'Akzeptiert' : 'Abgelehnt'}
                        </span>
                      </td>
                      <td>
                        {offer.status === 'pending' && (
                          <button className="btn btn-small btn-danger">
                            Zurückziehen
                          </button>
                        )}
                        {offer.status === 'accepted' && (
                          <button className="btn btn-small btn-success">
                            Abschließen
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {activeTab === 'received-offers' && (
            <div className="received-offers-tab">
              <h3>Erhaltene Angebote</h3>
              <table className="table offers-table">
                <thead>
                  <tr>
                    <th>Spieler</th>
                    <th>Alter</th>
                    <th>Position</th>
                    <th>Stärke</th>
                    <th>Von Verein</th>
                    <th>Angebotsbetrag</th>
                    <th>Datum</th>
                    <th>Status</th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  {transferData.receivedOffers.map(offer => (
                    <tr key={offer.id}>
                      <td>{offer.player.name}</td>
                      <td>{offer.player.age}</td>
                      <td>{offer.player.position}</td>
                      <td>
                        <div className="strength-display">
                          <div className="strength-bar">
                            <div 
                              className="strength-fill" 
                              style={{ width: `${offer.player.strength}%` }}
                            ></div>
                          </div>
                          <span>{offer.player.strength}</span>
                        </div>
                      </td>
                      <td>{offer.fromTeam}</td>
                      <td>€{offer.offerAmount.toLocaleString()}</td>
                      <td>{new Date(offer.date).toLocaleDateString('de-DE')}</td>
                      <td>
                        <span className={`status-badge ${offer.status}`}>
                          {offer.status === 'pending' ? 'Ausstehend' : 
                           offer.status === 'accepted' ? 'Akzeptiert' : 'Abgelehnt'}
                        </span>
                      </td>
                      <td>
                        {offer.status === 'pending' && (
                          <div className="action-buttons">
                            <button className="btn btn-small btn-success">
                              Akzeptieren
                            </button>
                            <button className="btn btn-small btn-danger">
                              Ablehnen
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {activeTab === 'history' && (
            <div className="history-tab">
              <h3>Transferhistorie</h3>
              <table className="table history-table">
                <thead>
                  <tr>
                    <th>Spieler</th>
                    <th>Alter</th>
                    <th>Position</th>
                    <th>Stärke</th>
                    <th>Von Verein</th>
                    <th>Zu Verein</th>
                    <th>Betrag</th>
                    <th>Datum</th>
                  </tr>
                </thead>
                <tbody>
                  {transferData.transferHistory.map(transfer => (
                    <tr key={transfer.id}>
                      <td>{transfer.player.name}</td>
                      <td>{transfer.player.age}</td>
                      <td>{transfer.player.position}</td>
                      <td>
                        <div className="strength-display">
                          <div className="strength-bar">
                            <div 
                              className="strength-fill" 
                              style={{ width: `${transfer.player.strength}%` }}
                            ></div>
                          </div>
                          <span>{transfer.player.strength}</span>
                        </div>
                      </td>
                      <td>{transfer.fromTeam}</td>
                      <td>{transfer.toTeam}</td>
                      <td>€{transfer.amount.toLocaleString()}</td>
                      <td>{new Date(transfer.date).toLocaleDateString('de-DE')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Transfers;
