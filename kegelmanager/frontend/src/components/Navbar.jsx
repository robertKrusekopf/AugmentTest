import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { simulateMatchDay, getCurrentSeason, getMatches } from '../services/api';
import './Navbar.css';

const Navbar = ({ toggleSidebar, onLogout }) => {
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);
  const [currentSeason, setCurrentSeason] = useState(null);
  const [currentDate, setCurrentDate] = useState(null);
  const [currentMatchDay, setCurrentMatchDay] = useState(null);
  const [nextMatchDay, setNextMatchDay] = useState(null);
  const [loading, setLoading] = useState(true);

  // Lade die aktuelle Saison, das aktuelle Datum und den aktuellen Spieltag
  useEffect(() => {
    const loadCurrentData = async () => {
      try {
        // Lade die aktuelle Saison
        const season = await getCurrentSeason();
        setCurrentSeason(season);

        // Setze ein Datum innerhalb der Saison als aktuelles Datum
        if (season && season.start_date) {
          const startDate = new Date(season.start_date);
          setCurrentDate(startDate);
        }

        try {
          // Lade alle Spiele, um den aktuellen und nächsten Spieltag zu bestimmen
          const matches = await getMatches();
          console.log("Geladene Matches:", matches.length);

          // Überprüfe, ob die Matches match_day-Werte haben
          const matchesWithMatchDay = matches.filter(match => match.match_day !== null && match.match_day !== undefined);
          console.log("Matches mit match_day:", matchesWithMatchDay.length);

          if (matchesWithMatchDay.length === 0) {
            console.log("Keine Matches mit match_day gefunden. Spielplan muss generiert werden.");
            // Wenn keine Matches mit match_day gefunden wurden, setze den nächsten Spieltag auf 1
            setCurrentMatchDay(0);
            setNextMatchDay(1);
          } else {
            // Finde den letzten gespielten Spieltag
            const playedMatches = matchesWithMatchDay.filter(match => match.is_played);
            console.log("Gespielte Matches:", playedMatches.length);

            if (playedMatches.length > 0) {
              const lastPlayedMatchDay = Math.max(...playedMatches.map(match => match.match_day));
              setCurrentMatchDay(lastPlayedMatchDay);
              console.log("Letzter gespielter Spieltag:", lastPlayedMatchDay);
            } else {
              setCurrentMatchDay(0); // Noch kein Spieltag gespielt
              console.log("Noch kein Spieltag gespielt");
            }

            // Finde den nächsten zu spielenden Spieltag
            const unplayedMatches = matchesWithMatchDay.filter(match => !match.is_played);
            console.log("Ungespielte Matches:", unplayedMatches.length);

            if (unplayedMatches.length > 0) {
              const nextMatchDay = Math.min(...unplayedMatches.map(match => match.match_day));
              setNextMatchDay(nextMatchDay);
              console.log("Nächster Spieltag:", nextMatchDay);
            } else {
              setNextMatchDay(null); // Keine ungespielte Spiele mehr
              console.log("Keine weiteren Spieltage");
            }
          }
        } catch (error) {
          console.error("Fehler beim Laden der Matches:", error);
          // Im Fehlerfall setze Standardwerte
          setCurrentMatchDay(0);
          setNextMatchDay(1);
        }

        setLoading(false);
      } catch (error) {
        console.error('Fehler beim Laden der aktuellen Daten:', error);
        setLoading(false);
      }
    };

    loadCurrentData();
  }, []);

  const handleSimulateMatchDay = async () => {
    try {
      setSimulating(true);
      const result = await simulateMatchDay();
      setSimulationResult(result);

      // Aktualisiere den aktuellen Spieltag
      if (result.match_day) {
        setCurrentMatchDay(result.match_day);
        setNextMatchDay(result.match_day + 1);
      }

      // Seite neu laden, um die aktualisierten Daten anzuzeigen
      window.location.reload();
    } catch (error) {
      console.error('Fehler bei der Simulation des Spieltags:', error);
      alert('Fehler bei der Simulation des Spieltags. Bitte versuche es erneut.');
    } finally {
      setSimulating(false);
    }
  };

  // Formatiere das Datum für die Anzeige
  const formatDate = (date) => {
    if (!date) return '';

    const options = { day: 'numeric', month: 'long', year: 'numeric' };
    return date.toLocaleDateString('de-DE', options);
  };

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <button className="menu-toggle" onClick={toggleSidebar}>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <Link to="/" className="logo">
          <span className="logo-text">Kegelmanager</span>
        </Link>
      </div>

      <div className="navbar-center">
        <div className="season-info">
          <span className="season-label">Saison:</span>
          <span className="season-value">
            {loading ? 'Laden...' : (currentSeason ? currentSeason.name : 'Keine Saison')}
          </span>
        </div>
        <div className="date-info">
          <span className="date-value">
            {loading ? 'Laden...' : (currentDate ? formatDate(currentDate) : 'Kein Datum')}
          </span>
        </div>
        <div className="matchday-info">
          <span className="matchday-label">Aktueller Spieltag:</span>
          <span className="matchday-value">
            {loading ? 'Laden...' : (currentMatchDay !== null ? currentMatchDay : 'Keiner')}
          </span>
          {nextMatchDay && (
            <span className="next-matchday">
              (Nächster: {nextMatchDay})
            </span>
          )}
        </div>
      </div>

      <div className="navbar-right">
        <button
          className={`sim-button btn btn-primary ${simulating ? 'loading' : ''}`}
          onClick={handleSimulateMatchDay}
          disabled={simulating || !nextMatchDay}
          title={!nextMatchDay ? 'Alle Spieltage wurden bereits simuliert' : ''}
        >
          {simulating ? 'Simuliere...' : nextMatchDay ? `Spieltag ${nextMatchDay} simulieren` : 'Keine weiteren Spieltage'}
        </button>

        <div className="user-menu">
          <button
            className="user-menu-button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
          >
            <div className="user-avatar">
              <span>M</span>
            </div>
            <span className="user-name">Manager</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>

          {dropdownOpen && (
            <div className="dropdown-menu">
              <Link to="/profile" className="dropdown-item">Profil</Link>
              <Link to="/settings" className="dropdown-item">Einstellungen</Link>
              <div className="dropdown-divider"></div>
              <button
                className="dropdown-item"
                onClick={() => {
                  if (onLogout) {
                    onLogout();
                  }
                  navigate('/main-menu');
                  setDropdownOpen(false);
                }}
              >
                Datenbank wechseln
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
