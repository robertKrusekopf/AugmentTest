import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCupMatchDaysOptimized } from '../services/apiCache';
import './CupMatchDays.css';

const CupMatchDays = () => {
  const [matchDays, setMatchDays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCupMatchDays();
  }, []);

  const loadCupMatchDays = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await getCupMatchDaysOptimized();
      setMatchDays(data);
    } catch (err) {
      console.error('Error loading cup match days:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="cup-match-days-page">
        <div className="loading">Lade Pokalspieltage...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cup-match-days-page">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={loadCupMatchDays} className="btn btn-secondary">
            Erneut versuchen
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="cup-match-days-page">
      <div className="page-header">
        <h1 className="page-title">Pokalspieltage</h1>
        <p className="page-description">
          Übersicht aller Pokalspieltage der aktuellen Saison
        </p>
      </div>

      {matchDays.length === 0 ? (
        <div className="no-match-days">
          <div className="no-match-days-content">
            <h3>Keine Pokalspieltage gefunden</h3>
            <p>Es wurden noch keine Pokalspiele für diese Saison erstellt.</p>
            <Link to="/cups/DKBC" className="btn btn-primary">
              Zu den Pokalen
            </Link>
          </div>
        </div>
      ) : (
        <div className="match-days-list">
          {matchDays.map(matchDay => (
            <div key={matchDay.match_day} className="match-day-card">
              <div className="match-day-header">
                <h3 className="match-day-title">Spieltag {matchDay.match_day}</h3>
                <div className="match-day-stats">
                  <span className="stat">
                    {matchDay.total_played} / {matchDay.total_matches} Spiele gespielt
                  </span>
                  <span className={`progress-indicator ${
                    matchDay.total_played === matchDay.total_matches ? 'complete' : 'incomplete'
                  }`}>
                    {matchDay.total_played === matchDay.total_matches ? 'Abgeschlossen' : 'Ausstehend'}
                  </span>
                </div>
              </div>
              
              <div className="cups-list">
                {matchDay.cups.map((cup, index) => (
                  <div key={index} className="cup-item">
                    <div className="cup-info">
                      <span className="cup-name">{cup.name}</span>
                      <span className="cup-round">{cup.round}</span>
                    </div>
                    
                    <div className="cup-stats">
                      <span className="matches-count">
                        {cup.played} / {cup.matches} Spiele
                      </span>
                      <span className={`cup-type ${cup.type.toLowerCase()}`}>
                        {cup.type}
                      </span>
                    </div>
                    
                    <div className="cup-actions">
                      <Link 
                        to={`/cups/${cup.type}`} 
                        className="btn btn-sm btn-secondary"
                      >
                        Pokal anzeigen
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ 
                    width: `${(matchDay.total_played / matchDay.total_matches) * 100}%` 
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CupMatchDays;
