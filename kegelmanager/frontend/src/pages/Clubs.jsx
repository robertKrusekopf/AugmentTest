import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAppContext } from '../contexts/AppContext';
import './Clubs.css';

const Clubs = () => {
  const { getClubs } = useAppContext();
  const [clubs, setClubs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Lade Daten aus dem Context (mit Caching)
  useEffect(() => {
    const loadClubs = async () => {
      try {
        console.log('Lade Clubs aus dem Context...');
        setLoading(true);

        const data = await getClubs();

        // Wenn keine Daten zurückgegeben werden, verwende leere Liste
        if (!data || data.length === 0) {
          console.warn('Keine Clubs in der Datenbank gefunden.');
          setClubs([]);
        } else {
          // Verarbeite die Daten und füge fehlende Eigenschaften hinzu
          const processedClubs = data.map(club => {
            // Berechne die Anzahl der Teams (falls nicht vorhanden)
            const teams = club.teams ? club.teams.length : 0;

            // Bestimme die Liga des Hauptteams (falls vorhanden)
            let league = 'Unbekannt';
            if (club.teams && club.teams.length > 0 && club.teams[0].league) {
              league = club.teams[0].league.name;
            }

            // Stelle sicher, dass alle benötigten Eigenschaften vorhanden sind
            return {
              id: club.id,
              name: club.name,
              founded: club.founded || 2000,
              reputation: club.reputation || 50,
              teams: teams,
              league: league,
              balance: club.balance || 0,
              emblem_url: club.emblem_url // Wichtig: Emblem URL hinzufügen
            };
          });

          setClubs(processedClubs);
        }
      } catch (error) {
        console.error('Fehler beim Laden der Clubs:', error);
      } finally {
        setLoading(false);
      }
    };

    loadClubs();
  }, [getClubs]);

  // Filtern der Vereine basierend auf dem Suchbegriff
  const filteredClubs = clubs.filter(club =>
    club.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="loading">Lade Vereine...</div>;
  }

  return (
    <div className="clubs-page">
      <h1 className="page-title">Vereine</h1>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Verein suchen..."
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

      <div className="clubs-grid">
        {filteredClubs.map(club => (
          <Link to={`/clubs/${club.id}`} key={club.id} className="club-card">
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
            <div className="club-info">
              <h2 className="club-name">{club.name}</h2>
              <div className="club-details">
                <div className="club-detail">
                  <span className="detail-label">Gegründet:</span>
                  <span className="detail-value">{club.founded}</span>
                </div>
                <div className="club-detail">
                  <span className="detail-label">Liga:</span>
                  <span className="detail-value">{club.league}</span>
                </div>
                <div className="club-detail">
                  <span className="detail-label">Mannschaften:</span>
                  <span className="detail-value">{club.teams}</span>
                </div>
                <div className="club-detail">
                  <span className="detail-label">Reputation:</span>
                  <div className="reputation-bar">
                    <div
                      className="reputation-fill"
                      style={{ width: `${club.reputation}%` }}
                    ></div>
                  </div>
                </div>
                <div className="club-detail">
                  <span className="detail-label">Finanzen:</span>
                  <span className="detail-value">€{club.balance.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Clubs;
