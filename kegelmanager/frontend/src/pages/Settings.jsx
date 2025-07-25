import { useState, useEffect } from 'react';
import { getClubs, simulateSeason, getCurrentSeason, transitionToNewSeason } from '../services/api';
import { invalidateAfterSimulation, invalidateAfterSeasonTransition } from '../services/apiCache';
import './Settings.css';

const Settings = () => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('general');
  const [clubs, setClubs] = useState([]);
  const [multiSeasonCount, setMultiSeasonCount] = useState(1);
  const [simulatingMultiSeason, setSimulatingMultiSeason] = useState(false);
  const [settings, setSettings] = useState({
    general: {
      language: 'de',
      darkMode: false,
      notifications: true
    },
    game: {
      difficulty: 'normal',
      simulationSpeed: 'normal',
      autoSave: true,
      autoSaveInterval: 15,
      managerClubId: null // null means vereinslos (no club)
    },
    display: {
      showTutorials: true,
      compactView: false,
      showStatistics: true
    }
  });
  const [message, setMessage] = useState({ show: false, type: '', text: '' });

  useEffect(() => {
    const loadData = async () => {
      try {
        // Load settings from localStorage if available
        const savedSettings = localStorage.getItem('gameSettings');
        if (savedSettings) {
          try {
            setSettings(JSON.parse(savedSettings));
          } catch (e) {
            console.error('Failed to parse saved settings:', e);
          }
        }

        // Check if there's a managedClubId in localStorage (for backward compatibility)
        const managedClubId = localStorage.getItem('managedClubId');
        if (managedClubId) {
          // Update the settings with the managedClubId
          setSettings(prev => ({
            ...prev,
            game: {
              ...prev.game,
              managerClubId: parseInt(managedClubId)
            }
          }));
        }

        // Load clubs for the manager club selection
        const clubsData = await getClubs();
        setClubs(clubsData);

        setLoading(false);
      } catch (error) {
        console.error('Error loading data:', error);
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleSettingChange = (category, setting, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: value
      }
    }));
  };

  const saveSettings = () => {
    // In a real application, we would save to an API
    // For now, we'll just save to localStorage
    localStorage.setItem('gameSettings', JSON.stringify(settings));

    // Also save the managedClubId separately for compatibility with the lineup selector
    if (settings.game.managerClubId) {
      localStorage.setItem('managedClubId', settings.game.managerClubId.toString());
    } else {
      localStorage.removeItem('managedClubId');
    }

    // Dispatch a storage event to notify other components (like Sidebar)
    // that the settings have changed
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'gameSettings',
      newValue: JSON.stringify(settings)
    }));

    setMessage({
      show: true,
      type: 'success',
      text: 'Einstellungen wurden gespeichert!'
    });

    // Hide message after 3 seconds
    setTimeout(() => {
      setMessage({ show: false, type: '', text: '' });
    }, 3000);
  };

  const handleMultiSeasonSimulation = async () => {
    if (multiSeasonCount < 1 || multiSeasonCount > 50) {
      alert('Bitte geben Sie eine Anzahl zwischen 1 und 50 ein.');
      return;
    }

    const confirmed = window.confirm(`Sind Sie sicher, dass Sie ${multiSeasonCount} Saison(en) simulieren möchten? Dies kann einige Zeit dauern.`);
    if (!confirmed) return;

    try {
      setSimulatingMultiSeason(true);

      for (let i = 0; i < multiSeasonCount; i++) {
        console.log(`Simuliere Saison ${i + 1} von ${multiSeasonCount}...`);

        // Hole aktuelle Saison
        const currentSeason = await getCurrentSeason();

        // Simuliere die komplette Saison
        await simulateSeason(currentSeason.id, false);

        // Führe Saisonwechsel durch (außer bei der letzten Iteration)
        if (i < multiSeasonCount - 1) {
          await transitionToNewSeason();
        }
      }

      // Invalidiere Cache nach der Simulation
      invalidateAfterSimulation();
      invalidateAfterSeasonTransition();

      // Sende Event für Dashboard-Aktualisierung
      window.dispatchEvent(new CustomEvent('simulationComplete'));

      setMessage({
        show: true,
        type: 'success',
        text: `${multiSeasonCount} Saison(en) erfolgreich simuliert!`
      });

      // Verstecke Nachricht nach 5 Sekunden
      setTimeout(() => {
        setMessage({ show: false, type: '', text: '' });
      }, 5000);

    } catch (error) {
      console.error('Fehler bei der Multi-Saison-Simulation:', error);
      setMessage({
        show: true,
        type: 'error',
        text: 'Fehler bei der Multi-Saison-Simulation. Bitte versuchen Sie es erneut.'
      });

      setTimeout(() => {
        setMessage({ show: false, type: '', text: '' });
      }, 5000);
    } finally {
      setSimulatingMultiSeason(false);
    }
  };

  const resetSettings = () => {
    if (window.confirm('Möchten Sie wirklich alle Einstellungen zurücksetzen?')) {
      const defaultSettings = {
        general: {
          language: 'de',
          darkMode: false,
          notifications: true
        },
        game: {
          difficulty: 'normal',
          simulationSpeed: 'normal',
          autoSave: true,
          autoSaveInterval: 15,
          managerClubId: null // Reset to vereinslos (no club)
        },
        display: {
          showTutorials: true,
          compactView: false,
          showStatistics: true
        }
      };

      setSettings(defaultSettings);

      // Save to localStorage and dispatch event
      localStorage.setItem('gameSettings', JSON.stringify(defaultSettings));

      // Remove the managedClubId from localStorage
      localStorage.removeItem('managedClubId');

      // Dispatch a storage event to notify other components
      window.dispatchEvent(new StorageEvent('storage', {
        key: 'gameSettings',
        newValue: JSON.stringify(defaultSettings)
      }));

      setMessage({
        show: true,
        type: 'info',
        text: 'Einstellungen wurden zurückgesetzt!'
      });

      // Hide message after 3 seconds
      setTimeout(() => {
        setMessage({ show: false, type: '', text: '' });
      }, 3000);
    }
  };

  if (loading) {
    return <div className="loading">Lade Einstellungen...</div>;
  }

  return (
    <div className="settings-container">
      <div className="card">
        <div className="card-header">
          <h1>Einstellungen</h1>
        </div>

        {message.show && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        <div className="settings-tabs">
          <div
            className={`tab ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            Allgemein
          </div>
          <div
            className={`tab ${activeTab === 'game' ? 'active' : ''}`}
            onClick={() => setActiveTab('game')}
          >
            Spiel
          </div>
          <div
            className={`tab ${activeTab === 'display' ? 'active' : ''}`}
            onClick={() => setActiveTab('display')}
          >
            Anzeige
          </div>
          <div
            className={`tab ${activeTab === 'cheats' ? 'active' : ''}`}
            onClick={() => setActiveTab('cheats')}
          >
            Cheats
          </div>
        </div>

        <div className="settings-content">
          {activeTab === 'general' && (
            <div className="settings-section">
              <h2>Allgemeine Einstellungen</h2>

              <div className="setting-item">
                <label htmlFor="language">Sprache</label>
                <select
                  id="language"
                  value={settings.general.language}
                  onChange={(e) => handleSettingChange('general', 'language', e.target.value)}
                >
                  <option value="de">Deutsch</option>
                  <option value="en">Englisch</option>
                </select>
              </div>

              <div className="setting-item">
                <label htmlFor="darkMode">Dunkler Modus</label>
                <input
                  type="checkbox"
                  id="darkMode"
                  checked={settings.general.darkMode}
                  onChange={(e) => handleSettingChange('general', 'darkMode', e.target.checked)}
                />
              </div>

              <div className="setting-item">
                <label htmlFor="notifications">Benachrichtigungen</label>
                <input
                  type="checkbox"
                  id="notifications"
                  checked={settings.general.notifications}
                  onChange={(e) => handleSettingChange('general', 'notifications', e.target.checked)}
                />
              </div>
            </div>
          )}

          {activeTab === 'game' && (
            <div className="settings-section">
              <h2>Spieleinstellungen</h2>

              <div className="setting-item">
                <label htmlFor="managerClub">Manager Verein</label>
                <select
                  id="managerClub"
                  value={settings.game.managerClubId || ''}
                  onChange={(e) => handleSettingChange('game', 'managerClubId', e.target.value ? parseInt(e.target.value) : null)}
                >
                  <option value="">Vereinslos</option>
                  {clubs
                    .sort((a, b) => a.name.localeCompare(b.name, 'de')) // Alphabetisch nach deutschem Alphabet sortieren
                    .map(club => (
                      <option key={club.id} value={club.id}>{club.name}</option>
                    ))
                  }
                </select>
              </div>

              <div className="setting-item">
                <label htmlFor="difficulty">Schwierigkeitsgrad</label>
                <select
                  id="difficulty"
                  value={settings.game.difficulty}
                  onChange={(e) => handleSettingChange('game', 'difficulty', e.target.value)}
                >
                  <option value="easy">Leicht</option>
                  <option value="normal">Normal</option>
                  <option value="hard">Schwer</option>
                </select>
              </div>

              <div className="setting-item">
                <label htmlFor="simulationSpeed">Simulationsgeschwindigkeit</label>
                <select
                  id="simulationSpeed"
                  value={settings.game.simulationSpeed}
                  onChange={(e) => handleSettingChange('game', 'simulationSpeed', e.target.value)}
                >
                  <option value="slow">Langsam</option>
                  <option value="normal">Normal</option>
                  <option value="fast">Schnell</option>
                </select>
              </div>

              <div className="setting-item">
                <label htmlFor="autoSave">Automatisches Speichern</label>
                <input
                  type="checkbox"
                  id="autoSave"
                  checked={settings.game.autoSave}
                  onChange={(e) => handleSettingChange('game', 'autoSave', e.target.checked)}
                />
              </div>

              {settings.game.autoSave && (
                <div className="setting-item">
                  <label htmlFor="autoSaveInterval">Speicherintervall (Minuten)</label>
                  <input
                    type="number"
                    id="autoSaveInterval"
                    min="1"
                    max="60"
                    value={settings.game.autoSaveInterval}
                    onChange={(e) => handleSettingChange('game', 'autoSaveInterval', parseInt(e.target.value) || 15)}
                  />
                </div>
              )}
            </div>
          )}

          {activeTab === 'display' && (
            <div className="settings-section">
              <h2>Anzeigeeinstellungen</h2>

              <div className="setting-item">
                <label htmlFor="showTutorials">Tutorials anzeigen</label>
                <input
                  type="checkbox"
                  id="showTutorials"
                  checked={settings.display.showTutorials}
                  onChange={(e) => handleSettingChange('display', 'showTutorials', e.target.checked)}
                />
              </div>

              <div className="setting-item">
                <label htmlFor="compactView">Kompakte Ansicht</label>
                <input
                  type="checkbox"
                  id="compactView"
                  checked={settings.display.compactView}
                  onChange={(e) => handleSettingChange('display', 'compactView', e.target.checked)}
                />
              </div>

              <div className="setting-item">
                <label htmlFor="showStatistics">Statistiken anzeigen</label>
                <input
                  type="checkbox"
                  id="showStatistics"
                  checked={settings.display.showStatistics}
                  onChange={(e) => handleSettingChange('display', 'showStatistics', e.target.checked)}
                />
              </div>
            </div>
          )}

          {activeTab === 'cheats' && (
            <div className="settings-section">
              <h2>Cheat-Optionen</h2>
              <p className="cheat-warning">
                ⚠️ Diese Optionen sind nur für Testzwecke gedacht und können das Spielerlebnis beeinträchtigen.
              </p>

              <div className="setting-item">
                <label htmlFor="multiSeasonCount">Mehrere Saisons simulieren</label>
                <div className="multi-season-controls">
                  <input
                    type="number"
                    id="multiSeasonCount"
                    min="1"
                    max="50"
                    value={multiSeasonCount}
                    onChange={(e) => setMultiSeasonCount(parseInt(e.target.value) || 1)}
                    disabled={simulatingMultiSeason}
                  />
                  <button
                    className={`btn btn-warning ${simulatingMultiSeason ? 'loading' : ''}`}
                    onClick={handleMultiSeasonSimulation}
                    disabled={simulatingMultiSeason}
                  >
                    {simulatingMultiSeason ? 'Simuliere...' : `${multiSeasonCount} Saison(en) simulieren`}
                  </button>
                </div>
                <small className="setting-description">
                  Simuliert die angegebene Anzahl von Saisons automatisch hintereinander.
                  Jede Saison wird vollständig simuliert und anschließend wird ein Saisonwechsel durchgeführt.
                </small>
              </div>
            </div>
          )}

          <div className="settings-actions">
            <button className="btn btn-primary" onClick={saveSettings}>Speichern</button>
            <button className="btn btn-secondary" onClick={resetSettings}>Zurücksetzen</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
