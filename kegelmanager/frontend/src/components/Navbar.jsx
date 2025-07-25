import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAppContext } from '../contexts/AppContext';
import { simulateMatchDay, simulateSeason, getCurrentSeason, getSeasonStatus, transitionToNewSeason } from '../services/api';
import { invalidateAfterSimulation, invalidateAfterSeasonTransition } from '../services/apiCache';
import GlobalSearch from './GlobalSearch';
import './Navbar.css';

const Navbar = ({ toggleSidebar, onLogout }) => {
  const navigate = useNavigate();
  const { currentSeason, invalidateAllCache, getMatches } = useAppContext();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [simulatingSeason, setSimulatingSeason] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);
  const [currentDate, setCurrentDate] = useState(null);
  const [currentMatchDay, setCurrentMatchDay] = useState(null);
  const [nextMatchDay, setNextMatchDay] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seasonCompleted, setSeasonCompleted] = useState(false);

  // Lade die aktuelle Saison, das aktuelle Datum und den aktuellen Spieltag
  useEffect(() => {
    const loadCurrentData = async () => {
      try {
        // Verwende die Saison aus dem Context oder lade sie neu
        let season = currentSeason;
        if (!season) {
          season = await getCurrentSeason();
        }

        // Setze ein Datum innerhalb der Saison als aktuelles Datum
        if (season && season.start_date) {
          const startDate = new Date(season.start_date);
          setCurrentDate(startDate);
        }

        try {
          // Lade alle Spiele, um den aktuellen und nächsten Spieltag zu bestimmen
          const matches = await getMatches();
          console.log("=== NAVBAR DEBUG ===");
          console.log("Geladene Matches:", matches.length);
          console.log("Erste 3 Matches:", matches.slice(0, 3));

          // Überprüfe, ob die Matches match_day-Werte haben
          const matchesWithMatchDay = matches.filter(match => match.match_day !== null && match.match_day !== undefined);
          console.log("Matches mit match_day:", matchesWithMatchDay.length);

          if (matchesWithMatchDay.length === 0) {
            console.log("Keine Matches mit match_day gefunden. Spielplan muss generiert werden.");
            // Wenn keine Matches mit match_day gefunden wurden, setze den nächsten Spieltag auf 1
            setCurrentMatchDay(0);
            setNextMatchDay(1);
            console.log("Setze nextMatchDay auf 1 (kein Spielplan vorhanden)");
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
              console.log("Noch kein Spieltag gespielt - setze currentMatchDay auf 0");
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
              console.log("Keine weiteren Spieltage - setze nextMatchDay auf null");
            }

            // Prüfe den Saisonstatus immer, nicht nur wenn keine ungespielte Spiele vorhanden sind
            try {
              const seasonStatus = await getSeasonStatus();
              setSeasonCompleted(seasonStatus.is_completed);
              console.log("=== SAISONSTATUS DEBUG ===");
              console.log("Saisonstatus:", seasonStatus);
              console.log("is_completed:", seasonStatus.is_completed);
              console.log("total_matches:", seasonStatus.total_matches);
              console.log("played_matches:", seasonStatus.played_matches);
              console.log("unplayed_matches:", seasonStatus.unplayed_matches);
              console.log("matches_without_match_day:", seasonStatus.matches_without_match_day);
              console.log("seasonCompleted wird gesetzt auf:", seasonStatus.is_completed);
              console.log("=== END SAISONSTATUS DEBUG ===");
            } catch (error) {
              console.error("Fehler beim Laden des Saisonstatus:", error);
              setSeasonCompleted(false); // Fallback auf false bei Fehlern
            }
          }
          console.log("=== END NAVBAR DEBUG ===");
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
  }, [currentSeason]);

  const handleSimulateMatchDay = useCallback(async () => {
    try {
      setSimulating(true);
      const result = await simulateMatchDay();
      setSimulationResult(result);

      // Aktualisiere den aktuellen Spieltag
      if (result.match_day) {
        setCurrentMatchDay(result.match_day);
        setNextMatchDay(result.match_day + 1);
      }

      // Prüfe den Saisonstatus nach der Spieltag-Simulation
      try {
        const seasonStatus = await getSeasonStatus();
        setSeasonCompleted(seasonStatus.is_completed);
        console.log("=== SAISONSTATUS NACH SPIELTAG-SIMULATION ===");
        console.log("Saisonstatus nach Spieltag-Simulation:", seasonStatus);
        console.log("is_completed:", seasonStatus.is_completed);
        console.log("seasonCompleted wird gesetzt auf:", seasonStatus.is_completed);
        console.log("=== END SAISONSTATUS NACH SPIELTAG-SIMULATION ===");
      } catch (error) {
        console.error("Fehler beim Laden des Saisonstatus nach Spieltag-Simulation:", error);
      }

      // Invalidiere Cache nach Simulation
      invalidateAfterSimulation();
      invalidateAllCache();

      // Sende Event für Dashboard-Aktualisierung
      window.dispatchEvent(new CustomEvent('simulationComplete'));

      // Aktualisiere die Match-Daten ohne Seitenreload
      try {
        const matches = await getMatches();
        const matchesWithMatchDay = matches.filter(match => match.match_day !== null && match.match_day !== undefined);

        if (matchesWithMatchDay.length > 0) {
          const unplayedMatches = matchesWithMatchDay.filter(match => !match.is_played);
          if (unplayedMatches.length > 0) {
            const nextMatchDay = Math.min(...unplayedMatches.map(match => match.match_day));
            setNextMatchDay(nextMatchDay);
          } else {
            setNextMatchDay(null);
          }
        }
      } catch (error) {
        console.error("Fehler beim Aktualisieren der Match-Daten:", error);
      }
    } catch (error) {
      console.error('Fehler bei der Simulation des Spieltags:', error);
      alert('Fehler bei der Simulation des Spieltags. Bitte versuche es erneut.');
    } finally {
      setSimulating(false);
    }
  }, [invalidateAllCache]);

  const handleSimulateSeason = async () => {
    // Bestätigungsdialog anzeigen
    const confirmed = window.confirm('Bist du sicher, dass du die gesamte Saison simulieren möchtest? Alle verbleibenden Spieltage werden simuliert.');

    if (!confirmed) {
      return; // Abbrechen, wenn der Benutzer nicht bestätigt
    }

    try {
      setSimulatingSeason(true);

      if (!currentSeason || !currentSeason.id) {
        throw new Error('Keine aktuelle Saison gefunden');
      }

      console.log(`Simuliere komplette Saison mit ID: ${currentSeason.id}`);

      // Simuliere die gesamte Saison mit der aktuellen Saison-ID
      // Setze createNewSeason auf false, um keine neue Saison zu erstellen
      const result = await simulateSeason(currentSeason.id, false);
      setSimulationResult(result);

      console.log('Saison-Simulation abgeschlossen:', result);

      // Prüfe den Saisonstatus nach der Simulation
      try {
        const seasonStatus = await getSeasonStatus();
        setSeasonCompleted(seasonStatus.is_completed);
        console.log("=== SAISONSTATUS NACH SAISON-SIMULATION ===");
        console.log("Saisonstatus nach Simulation:", seasonStatus);
        console.log("is_completed:", seasonStatus.is_completed);
        console.log("total_matches:", seasonStatus.total_matches);
        console.log("played_matches:", seasonStatus.played_matches);
        console.log("unplayed_matches:", seasonStatus.unplayed_matches);
        console.log("seasonCompleted wird gesetzt auf:", seasonStatus.is_completed);
        console.log("=== END SAISONSTATUS NACH SAISON-SIMULATION ===");
      } catch (error) {
        console.error("Fehler beim Laden des Saisonstatus nach Simulation:", error);
      }

      // Invalidiere Cache nach Simulation
      invalidateAfterSimulation();
      invalidateAllCache();

      // Sende Event für Dashboard-Aktualisierung
      window.dispatchEvent(new CustomEvent('simulationComplete'));

      // Informiere den Benutzer, dass die Saison simuliert wurde
      alert('Die Saison wurde vollständig simuliert. Der Button sollte jetzt "Saisonwechsel" anzeigen.');
    } catch (error) {
      console.error('Fehler bei der Simulation der Saison:', error);
      alert('Fehler bei der Simulation der Saison. Bitte versuche es erneut.');
    } finally {
      setSimulatingSeason(false);
    }
  };

  const handleSeasonTransition = async () => {
    // Bestätigungsdialog anzeigen
    const confirmed = window.confirm('Bist du sicher, dass du den Saisonwechsel durchführen möchtest? Es wird eine neue Saison erstellt und Auf-/Abstieg verarbeitet.');

    if (!confirmed) {
      return; // Abbrechen, wenn der Benutzer nicht bestätigt
    }

    try {
      setSimulatingSeason(true);

      console.log('Starte Saisonwechsel...');

      // Führe den Saisonwechsel durch
      const result = await transitionToNewSeason();
      setSimulationResult(result);

      console.log('Saisonwechsel abgeschlossen:', result);

      // Invalidate all cache after season transition
      invalidateAfterSeasonTransition();

      // Sende Event für Dashboard-Aktualisierung
      window.dispatchEvent(new CustomEvent('simulationComplete'));

      // Informiere den Benutzer über den erfolgreichen Saisonwechsel
      alert(`Saisonwechsel erfolgreich! Neue Saison "${result.new_season}" wurde erstellt. Die Seite wird neu geladen.`);

      // Kurze Verzögerung vor dem Neuladen
      setTimeout(() => {
        // Seite neu laden, um die neue Saison anzuzeigen
        window.location.reload();
      }, 500);
    } catch (error) {
      console.error('Fehler beim Saisonwechsel:', error);
      alert('Fehler beim Saisonwechsel. Bitte versuche es erneut.');
    } finally {
      setSimulatingSeason(false);
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

      <div className="navbar-search">
        <GlobalSearch />
      </div>

      <div className="navbar-right">
        <button
          className={`sim-button btn btn-primary ${simulating ? 'loading' : ''}`}
          onClick={handleSimulateMatchDay}
          disabled={simulating || simulatingSeason || !nextMatchDay}
          title={!nextMatchDay ? 'Alle Spieltage wurden bereits simuliert' : ''}
        >
          {simulating ? 'Simuliere...' : nextMatchDay ? `Spieltag ${nextMatchDay} simulieren` : 'Keine weiteren Spieltage'}
        </button>

        <button
          className={`sim-season-button btn ${seasonCompleted ? 'btn-success' : 'btn-warning'} ${simulatingSeason ? 'loading' : ''}`}
          onClick={seasonCompleted ? handleSeasonTransition : handleSimulateSeason}
          disabled={simulating || simulatingSeason || (!nextMatchDay && !seasonCompleted)}
          title={seasonCompleted ? 'Neue Saison starten' : (!nextMatchDay ? 'Alle Spieltage wurden bereits simuliert' : 'Gesamte Saison simulieren')}
        >
          {simulatingSeason ? 'Simuliere...' : (seasonCompleted ? 'Saisonwechsel' : 'Saison simulieren')}
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
