import React, { useState, useEffect } from 'react';
import { useAppContext } from '../contexts/AppContext';
import { getTransfers, createTransferOffer, updateTransferOffer, withdrawTransferOffer } from '../services/api';
import TransferOfferModal from '../components/TransferOfferModal';
import './Transfers.css';

const Transfers = () => {
  const { managedClubId } = useAppContext();
  const [loading, setLoading] = useState(true);
  const [transferData, setTransferData] = useState(null);
  const [activeTab, setActiveTab] = useState('market');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPosition, setFilterPosition] = useState('');
  const [filterAgeMin, setFilterAgeMin] = useState('');
  const [filterAgeMax, setFilterAgeMax] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [showOfferModal, setShowOfferModal] = useState(false);

  const loadTransferData = async () => {
    if (!managedClubId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await getTransfers(managedClubId);
      setTransferData(data);
    } catch (error) {
      console.error('Error loading transfer data:', error);
      setTransferData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransferData();
  }, [managedClubId]);

  const handleMakeOffer = (player) => {
    setSelectedPlayer(player);
    setShowOfferModal(true);
  };

  const handleSubmitOffer = async (playerId, offerAmount) => {
    try {
      await createTransferOffer(playerId, managedClubId, offerAmount);
      await loadTransferData(); // Reload data
      alert('Transferangebot erfolgreich erstellt!');
    } catch (error) {
      console.error('Error creating offer:', error);
      throw error;
    }
  };

  const handleOfferAction = async (offerId, action) => {
    try {
      await updateTransferOffer(offerId, action);
      await loadTransferData(); // Reload data

      const messages = {
        accept: 'Transfer erfolgreich abgeschlossen!',
        reject: 'Angebot abgelehnt.',
        withdraw: 'Angebot zurückgezogen.'
      };
      alert(messages[action] || 'Aktion erfolgreich ausgeführt.');
    } catch (error) {
      console.error('Error updating offer:', error);
      alert('Fehler beim Ausführen der Aktion. Bitte versuchen Sie es erneut.');
    }
  };

  const handleWithdrawOffer = async (offerId) => {
    try {
      await withdrawTransferOffer(offerId);
      await loadTransferData(); // Reload data
      alert('Angebot zurückgezogen.');
    } catch (error) {
      console.error('Error withdrawing offer:', error);
      alert('Fehler beim Zurückziehen des Angebots.');
    }
  };

  if (loading) {
    return <div className="loading">Lade Transferdaten...</div>;
  }

  if (!managedClubId) {
    return <div className="error">Bitte wählen Sie einen Verein in den Einstellungen aus.</div>;
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
                        <button
                          className="btn btn-small"
                          onClick={() => handleMakeOffer(player)}
                        >
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
                          <button
                            className="btn btn-small btn-danger"
                            onClick={() => handleWithdrawOffer(offer.id)}
                          >
                            Zurückziehen
                          </button>
                        )}
                        {offer.status === 'accepted' && (
                          <button
                            className="btn btn-small btn-success"
                            onClick={() => handleOfferAction(offer.id, 'accept')}
                          >
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
                            <button
                              className="btn btn-small btn-success"
                              onClick={() => handleOfferAction(offer.id, 'accept')}
                            >
                              Akzeptieren
                            </button>
                            <button
                              className="btn btn-small btn-danger"
                              onClick={() => handleOfferAction(offer.id, 'reject')}
                            >
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

      <TransferOfferModal
        player={selectedPlayer}
        isOpen={showOfferModal}
        onClose={() => {
          setShowOfferModal(false);
          setSelectedPlayer(null);
        }}
        onSubmit={handleSubmitOffer}
      />
    </div>
  );
};

export default Transfers;
