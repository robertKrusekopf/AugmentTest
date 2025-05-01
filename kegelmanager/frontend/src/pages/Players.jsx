import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPlayers } from '../services/api';
import './Players.css';

const Players = () => {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPosition, setFilterPosition] = useState('');
  const [sortBy, setSortBy] = useState('strength');
  const [sortDirection, setSortDirection] = useState('desc');

  // Lade Daten aus der Datenbank
  useEffect(() => {
    console.log('Lade Spieler aus der Datenbank...');

    // Lade die Daten aus der API
    getPlayers()
      .then(data => {
        console.log('Geladene Spieler:', data);

        // Wenn keine Daten zurückgegeben werden, verwende leere Liste
        if (!data || data.length === 0) {
          console.warn('Keine Spieler in der Datenbank gefunden.');
          setPlayers([]);
        } else {
          // Verarbeite die Daten und füge fehlende Eigenschaften hinzu
          const processedPlayers = data.map(player => {
            // Bestimme den Verein des Spielers
            let teamName = 'Unbekannt';
            if (player.club && player.club.name) {
              teamName = player.club.name;
            } else if (player.teams && player.teams.length > 0 && player.teams[0].club) {
              teamName = player.teams[0].club.name;
            }

            // Stelle sicher, dass alle benötigten Eigenschaften vorhanden sind
            return {
              id: player.id,
              name: player.name,
              age: player.age || 20,
              position: player.position || 'Unbekannt',
              strength: player.strength || 50,
              talent: player.talent || 5,
              team: teamName
            };
          });

          setPlayers(processedPlayers);
        }

        setLoading(false);
      })
      .catch(error => {
        console.error('Fehler beim Laden der Spieler:', error);
        setLoading(false);
      });
  }, []);

  // Filtern und Sortieren der Spieler
  const filteredAndSortedPlayers = players
    .filter(player =>
      player.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
      (filterPosition === '' || player.position === filterPosition)
    )
    .sort((a, b) => {
      const factor = sortDirection === 'asc' ? 1 : -1;

      if (sortBy === 'name') {
        return factor * a.name.localeCompare(b.name);
      } else if (sortBy === 'age') {
        return factor * (a.age - b.age);
      } else if (sortBy === 'strength') {
        return factor * (a.strength - b.strength);
      } else if (sortBy === 'talent') {
        return factor * (a.talent - b.talent);
      } else if (sortBy === 'team') {
        return factor * a.team.localeCompare(b.team);
      }

      return 0;
    });

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDirection('desc');
    }
  };

  if (loading) {
    return <div className="loading">Lade Spieler...</div>;
  }

  return (
    <div className="players-page">
      <h1 className="page-title">Spieler</h1>

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
        </div>
      </div>

      <div className="card">
        <table className="table players-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('name')} className={sortBy === 'name' ? 'sorted' : ''}>
                Name
                {sortBy === 'name' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('age')} className={sortBy === 'age' ? 'sorted' : ''}>
                Alter
                {sortBy === 'age' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('position')} className={sortBy === 'position' ? 'sorted' : ''}>
                Position
                {sortBy === 'position' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('strength')} className={sortBy === 'strength' ? 'sorted' : ''}>
                Stärke
                {sortBy === 'strength' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('talent')} className={sortBy === 'talent' ? 'sorted' : ''}>
                Talent
                {sortBy === 'talent' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('team')} className={sortBy === 'team' ? 'sorted' : ''}>
                Verein
                {sortBy === 'team' && (
                  <span className="sort-icon">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th>Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedPlayers.map(player => (
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
    </div>
  );
};

export default Players;
