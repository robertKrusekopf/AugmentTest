import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { globalSearch } from '../services/api';
import './GlobalSearch.css';

const GlobalSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState({
    players: [],
    teams: [],
    clubs: [],
    leagues: []
  });
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const searchRef = useRef(null);
  const navigate = useNavigate();

  // Debounce search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (query.length >= 2) {
        performSearch();
      } else {
        setResults({
          players: [],
          teams: [],
          clubs: [],
          leagues: []
        });
        setIsOpen(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const performSearch = async () => {
    setLoading(true);
    try {
      const searchResults = await globalSearch(query);
      setResults(searchResults);
      setIsOpen(true);
    } catch (error) {
      console.error('Search error:', error);
      setResults({
        players: [],
        teams: [],
        clubs: [],
        leagues: []
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResultClick = (type, id) => {
    setQuery('');
    setIsOpen(false);
    
    switch (type) {
      case 'player':
        navigate(`/players/${id}`);
        break;
      case 'team':
        navigate(`/teams/${id}`);
        break;
      case 'club':
        navigate(`/clubs/${id}`);
        break;
      case 'league':
        navigate(`/leagues/${id}`);
        break;
      default:
        break;
    }
  };

  const handleInputChange = (e) => {
    setQuery(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      setQuery('');
    }
  };

  const getTotalResults = () => {
    return results.players.length + results.teams.length + results.clubs.length + results.leagues.length;
  };

  return (
    <div className="global-search" ref={searchRef}>
      <div className="search-input-container">
        <input
          type="text"
          placeholder="Spieler, Teams, Vereine, Ligen suchen..."
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          className="search-input"
        />
        <div className="search-icon">
          {loading ? (
            <div className="loading-spinner"></div>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          )}
        </div>
      </div>

      {isOpen && (
        <div className="search-dropdown">
          {getTotalResults() === 0 && !loading ? (
            <div className="no-results">
              Keine Ergebnisse für "{query}"
            </div>
          ) : (
            <>
              {results.players.length > 0 && (
                <div className="result-category">
                  <div className="category-header">Spieler</div>
                  {results.players.map((player) => (
                    <div
                      key={`player-${player.id}`}
                      className="result-item"
                      onClick={() => handleResultClick('player', player.id)}
                    >
                      <div className="result-name">{player.name}</div>
                      <div className="result-details">{player.team} • {player.club}</div>
                    </div>
                  ))}
                </div>
              )}

              {results.teams.length > 0 && (
                <div className="result-category">
                  <div className="category-header">Mannschaften</div>
                  {results.teams.map((team) => (
                    <div
                      key={`team-${team.id}`}
                      className="result-item"
                      onClick={() => handleResultClick('team', team.id)}
                    >
                      <div className="result-name">{team.name}</div>
                      <div className="result-details">{team.league} • {team.club}</div>
                    </div>
                  ))}
                </div>
              )}

              {results.clubs.length > 0 && (
                <div className="result-category">
                  <div className="category-header">Vereine</div>
                  {results.clubs.map((club) => (
                    <div
                      key={`club-${club.id}`}
                      className="result-item"
                      onClick={() => handleResultClick('club', club.id)}
                    >
                      <div className="result-name">{club.name}</div>
                    </div>
                  ))}
                </div>
              )}

              {results.leagues.length > 0 && (
                <div className="result-category">
                  <div className="category-header">Ligen</div>
                  {results.leagues.map((league) => (
                    <div
                      key={`league-${league.id}`}
                      className="result-item"
                      onClick={() => handleResultClick('league', league.id)}
                    >
                      <div className="result-name">{league.name}</div>
                      <div className="result-details">Level {league.level}</div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default GlobalSearch;
