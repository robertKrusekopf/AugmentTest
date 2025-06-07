import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCupsByTypeOptimized } from '../services/apiCache';
import './Cups.css';

const Cups = () => {
  const { cupType } = useParams();
  const [cups, setCups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const cupTypeNames = {
    'DKBC': 'DKBC-Pokal',
    'Landespokal': 'Landespokal',
    'Kreispokal': 'Kreispokal'
  };

  const cupTypeDescriptions = {
    'DKBC': 'Für Mannschaften aus Ligen ohne Bundesland- und Landkreis-Zugehörigkeit',
    'Landespokal': 'Für Mannschaften aus Ligen mit Bundesland-Zugehörigkeit aber ohne Landkreis',
    'Kreispokal': 'Für Mannschaften aus Ligen mit Landkreis-Zugehörigkeit'
  };

  useEffect(() => {
    loadCups();
  }, [cupType]);

  const loadCups = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await getCupsByTypeOptimized(cupType);
      setCups(data);
    } catch (err) {
      console.error('Error loading cups:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };



  if (loading) {
    return (
      <div className="cups-page">
        <div className="loading">Lade Pokale...</div>
      </div>
    );
  }

  return (
    <div className="cups-page">
      <div className="page-header">
        <div className="breadcrumb">
          <Link to="/cups" className="breadcrumb-link">Pokale</Link>
          <span className="breadcrumb-separator">›</span>
          <span className="breadcrumb-current">{cupTypeNames[cupType] || 'Pokale'}</span>
        </div>
        <h1 className="page-title">{cupTypeNames[cupType] || 'Pokale'}</h1>
        <p className="page-description">
          {cupTypeDescriptions[cupType] || 'Pokalwettbewerbe'}
        </p>
      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={loadCups} className="btn btn-secondary">
            Erneut versuchen
          </button>
        </div>
      )}

      {cups.length === 0 && !loading && !error && (
        <div className="no-cups">
          <div className="no-cups-content">
            <h3>Keine Pokale gefunden</h3>
            <p>Für diese Kategorie wurden keine Pokale gefunden. Dies kann bedeuten, dass keine entsprechenden Ligen existieren.</p>
          </div>
        </div>
      )}

      {cups.length > 0 && (
        <div className="cups-grid">
          {cups.map(cup => (
            <div key={cup.id} className="cup-card">
              <div className="cup-header">
                <h3 className="cup-name">{cup.name}</h3>
                <span className={`cup-status ${cup.is_active ? 'active' : 'inactive'}`}>
                  {cup.is_active ? 'Aktiv' : 'Inaktiv'}
                </span>
              </div>
              
              <div className="cup-info">
                <div className="cup-stat">
                  <span className="stat-label">Aktuelle Runde:</span>
                  <span className="stat-value">{cup.current_round}</span>
                </div>
                
                <div className="cup-stat">
                  <span className="stat-label">Teilnehmende Teams:</span>
                  <span className="stat-value">{cup.eligible_teams_count}</span>
                </div>
                
                <div className="cup-stat">
                  <span className="stat-label">Spiele:</span>
                  <span className="stat-value">{cup.matches_count}</span>
                </div>

                <div className="cup-stat">
                  <span className="stat-label">Runden gesamt:</span>
                  <span className="stat-value">{cup.total_rounds || 'Nicht berechnet'}</span>
                </div>

                <div className="cup-stat">
                  <span className="stat-label">Aktuelle Runde:</span>
                  <span className="stat-value">{cup.current_round_number || 1} / {cup.total_rounds || '?'}</span>
                </div>
                
                {cup.bundesland && (
                  <div className="cup-stat">
                    <span className="stat-label">Bundesland:</span>
                    <span className="stat-value">{cup.bundesland}</span>
                  </div>
                )}
                
                {cup.landkreis && (
                  <div className="cup-stat">
                    <span className="stat-label">Landkreis:</span>
                    <span className="stat-value">{cup.landkreis}</span>
                  </div>
                )}
              </div>
              

            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Cups;
