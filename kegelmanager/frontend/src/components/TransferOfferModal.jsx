import React, { useState } from 'react';
import './TransferOfferModal.css';

const TransferOfferModal = ({ player, isOpen, onClose, onSubmit }) => {
  const [offerAmount, setOfferAmount] = useState(player?.value || 0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (offerAmount <= 0) {
      alert('Bitte geben Sie einen gültigen Angebotsbetrag ein.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(player.id, offerAmount);
      onClose();
    } catch (error) {
      console.error('Error submitting offer:', error);
      alert('Fehler beim Erstellen des Angebots. Bitte versuchen Sie es erneut.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !player) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content transfer-offer-modal">
        <div className="modal-header">
          <h2>Transferangebot für {player.name}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <div className="player-info">
            <div className="player-details">
              <h3>{player.name}</h3>
              <p><strong>Alter:</strong> {player.age}</p>
              <p><strong>Position:</strong> {player.position}</p>
              <p><strong>Stärke:</strong> {player.strength}</p>
              <p><strong>Aktueller Verein:</strong> {player.team}</p>
              <p><strong>Marktwert:</strong> €{player.value?.toLocaleString()}</p>
              <p><strong>Gehalt:</strong> €{player.salary?.toLocaleString()}</p>
            </div>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="offerAmount">Angebotsbetrag (€)</label>
              <input
                type="number"
                id="offerAmount"
                value={offerAmount}
                onChange={(e) => setOfferAmount(parseInt(e.target.value) || 0)}
                min="1"
                step="1000"
                required
                disabled={isSubmitting}
              />
              <small className="form-hint">
                Empfohlener Mindestbetrag: €{Math.round(player.value * 0.8)?.toLocaleString()}
              </small>
            </div>
            
            <div className="modal-actions">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={onClose}
                disabled={isSubmitting}
              >
                Abbrechen
              </button>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Wird gesendet...' : 'Angebot senden'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TransferOfferModal;
