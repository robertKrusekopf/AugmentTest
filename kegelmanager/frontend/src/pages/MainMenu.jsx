import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DatabaseService from '../services/DatabaseService';
import '../styles/MainMenu.css';

const MainMenu = () => {
  const [databases, setDatabases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newDbName, setNewDbName] = useState('');
  const [withSampleData, setWithSampleData] = useState(true);
  const [showNewDbForm, setShowNewDbForm] = useState(false);
  const [selectedDb, setSelectedDb] = useState(null);
  const [message, setMessage] = useState(null);

  const navigate = useNavigate();

  // Load databases on component mount
  useEffect(() => {
    loadDatabases();
  }, []);

  const loadDatabases = async () => {
    try {
      setLoading(true);
      const data = await DatabaseService.listDatabases();
      setDatabases(data);
      setError(null);
    } catch (err) {
      setError('Fehler beim Laden der Datenbanken: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDatabase = async (e) => {
    e.preventDefault();
    if (!newDbName.trim()) {
      setMessage({ type: 'error', text: 'Bitte geben Sie einen Datenbanknamen ein.' });
      return;
    }

    try {
      setLoading(true);
      const result = await DatabaseService.createDatabase(newDbName, withSampleData);
      if (result.success) {
        // Zeige eine detailliertere Erfolgsmeldung an
        setMessage({
          type: 'success',
          text: `${result.message} Die Datei neue_DB.py wurde ausgeführt, um die Datenbank zu erstellen. Sie können die Datenbank jetzt nach Ihren Wünschen anpassen.`
        });
        setNewDbName('');
        setShowNewDbForm(false);

        // Zeige einen Hinweis an, wie man die Datenbank bearbeiten kann
        alert(`Die Datenbank wurde erfolgreich erstellt!\n\nSie können die Datenbank jetzt bearbeiten, indem Sie die Datei 'neue_DB.py' in Ihrem Editor öffnen und anpassen.`);

        // Aktualisiere die Datenbankliste
        await loadDatabases();
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Fehler beim Erstellen der Datenbank: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDatabase = async (dbName) => {
    try {
      setLoading(true);
      console.log(`Wähle Datenbank aus: ${dbName}`);

      const result = await DatabaseService.selectDatabase(dbName);
      console.log('Ergebnis der Datenbankauswahl:', result);

      if (result.success) {
        // Zeige eine Erfolgsmeldung an
        setMessage({ type: 'success', text: result.message });

        // Speichere die ausgewählte Datenbank in localStorage
        localStorage.setItem('selectedDatabase', dbName);
        console.log(`Datenbank "${dbName}" in localStorage gespeichert`);

        // Zeige einen Hinweis an, dass die Anwendung neu gestartet werden muss
        setTimeout(() => {
          const confirmRestart = window.confirm(
            `Die Datenbank "${dbName}" wurde ausgewählt. Um die Änderungen zu übernehmen, muss die Anwendung neu gestartet werden. Möchten Sie die Anwendung jetzt neu starten?`
          );

          if (confirmRestart) {
            console.log('Neustart der Anwendung bestätigt');

            // Navigiere zur Hauptseite, was einen "Neustart" simuliert
            navigate('/');

            // Lade die Seite neu, um die Änderungen zu übernehmen
            console.log('Lade die Seite neu...');
            window.location.reload();
          } else {
            console.log('Neustart der Anwendung abgebrochen');
          }
        }, 500);
      } else {
        console.error('Fehler bei der Datenbankauswahl:', result.message);
        setMessage({ type: 'error', text: result.message });
      }
    } catch (err) {
      console.error('Fehler beim Auswählen der Datenbank:', err);
      setMessage({ type: 'error', text: 'Fehler beim Auswählen der Datenbank: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDatabase = async (dbName) => {
    if (!window.confirm(`Sind Sie sicher, dass Sie die Datenbank "${dbName}" löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden.`)) {
      return;
    }

    try {
      setLoading(true);
      const result = await DatabaseService.deleteDatabase(dbName);
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        await loadDatabases();
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Fehler beim Löschen der Datenbank: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-menu-container">
      <div className="main-menu">
        <div className="main-menu-header">
          <h1>Kegelmanager</h1>
          <p>Bowling Simulation Game</p>
        </div>

        {message && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        <div className="main-menu-content">
          <h2>Datenbank auswählen</h2>

          {loading ? (
            <div className="loading">Laden...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : (
            <>
              {databases.length === 0 ? (
                <div className="no-databases">
                  <p>Keine Datenbanken gefunden. Erstellen Sie eine neue Datenbank, um zu beginnen.</p>
                </div>
              ) : (
                <div className="database-list">
                  {databases.map((db, index) => (
                    <div
                      key={index}
                      className={`database-item ${selectedDb === db.name ? 'selected' : ''}`}
                      onClick={() => setSelectedDb(db.name)}
                    >
                      <div className="database-info">
                        <h3>{db.name}</h3>
                        <div className="database-details">
                          <p><strong>Saison:</strong> {db.current_season}</p>
                          <p><strong>Vereine:</strong> {db.club_count}</p>
                          <p><strong>Spieler:</strong> {db.player_count}</p>
                          <p><strong>Größe:</strong> {db.size_mb} MB</p>
                          <p><strong>Zuletzt geändert:</strong> {db.modified}</p>
                        </div>
                      </div>
                      <div className="database-actions">
                        <button
                          className="btn btn-primary"
                          onClick={() => handleSelectDatabase(db.name)}
                        >
                          Auswählen
                        </button>
                        <button
                          className="btn btn-danger"
                          onClick={() => handleDeleteDatabase(db.name)}
                        >
                          Löschen
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {showNewDbForm ? (
                <div className="new-database-form">
                  <h3>Neue Datenbank erstellen</h3>
                  <p className="info-text">
                    Beim Erstellen einer neuen Datenbank wird die Datei <strong>neue_DB.py</strong> ausgeführt.
                    Sie können diese Datei anschließend bearbeiten, um die Datenbank nach Ihren Wünschen anzupassen.
                  </p>
                  <form onSubmit={handleCreateDatabase}>
                    <div className="form-group">
                      <label htmlFor="dbName">Datenbankname:</label>
                      <input
                        type="text"
                        id="dbName"
                        value={newDbName}
                        onChange={(e) => setNewDbName(e.target.value)}
                        placeholder="z.B. meine_liga_2025"
                        required
                      />
                    </div>
                    <div className="form-group checkbox">
                      <input
                        type="checkbox"
                        id="withSampleData"
                        checked={withSampleData}
                        onChange={(e) => setWithSampleData(e.target.checked)}
                      />
                      <label htmlFor="withSampleData">Mit Beispieldaten initialisieren</label>
                    </div>
                    <div className="form-actions">
                      <button type="submit" className="btn btn-primary" disabled={loading}>
                        Erstellen und neue_DB.py ausführen
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => setShowNewDbForm(false)}
                        disabled={loading}
                      >
                        Abbrechen
                      </button>
                    </div>
                  </form>
                </div>
              ) : (
                <div className="new-database-button">
                  <button
                    className="btn btn-primary"
                    onClick={() => setShowNewDbForm(true)}
                    disabled={loading}
                  >
                    Neue Datenbank erstellen
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        <div className="main-menu-footer">
          <p>&copy; 2023 Kegelmanager - Bowling Simulation Game</p>
        </div>
      </div>
    </div>
  );
};

export default MainMenu;
