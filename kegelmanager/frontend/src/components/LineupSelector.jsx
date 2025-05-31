import { useState, useEffect } from 'react';
import { getAvailablePlayersForMatch, saveLineup } from '../services/api';
import './LineupSelector.css';

const LineupSelector = ({ matchId, managedClubId, onSave, onCancel }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [availablePlayers, setAvailablePlayers] = useState([]);
  const [selectedPlayers, setSelectedPlayers] = useState([null, null, null, null, null, null]);
  const [teamInfo, setTeamInfo] = useState(null);
  const [opponentLineup, setOpponentLineup] = useState(null);
  const [homeTeamLineupRequired, setHomeTeamLineupRequired] = useState(false);

  // Load available players when component mounts
  useEffect(() => {
    const fetchAvailablePlayers = async () => {
      try {
        setLoading(true);
        const data = await getAvailablePlayersForMatch(matchId, managedClubId);
        setAvailablePlayers(data.players);
        setTeamInfo({
          team_id: data.team_id,
          team_name: data.team_name,
          is_home_team: data.is_home_team
        });

        // If there's an existing lineup, use it
        if (data.has_lineup) {
          const positionedPlayers = Array(6).fill(null);
          data.players.forEach(player => {
            if (player.position !== null) {
              positionedPlayers[player.position - 1] = player;
            }
          });
          setSelectedPlayers(positionedPlayers);
        }

        // If this is the away team and the home team has set their lineup,
        // store the opponent's lineup
        if (!data.is_home_team) {
          if (data.opponent_has_lineup && data.opponent_lineup) {
            setOpponentLineup(data.opponent_lineup);
          } else {
            setHomeTeamLineupRequired(true);
          }
        }

        setLoading(false);
      } catch (err) {
        setError('Fehler beim Laden der verfügbaren Spieler: ' + err.message);
        setLoading(false);
      }
    };

    fetchAvailablePlayers();
  }, [matchId, managedClubId]);

  // Handle player selection for a position
  const handlePlayerSelect = (position, playerId) => {
    // Create a copy of the current selections
    const newSelections = [...selectedPlayers];

    // If a player is already selected for this position, remove them
    if (newSelections[position] !== null) {
      newSelections[position] = null;
    }

    // If a new player is selected (not just deselecting)
    if (playerId !== null) {
      // Find the player object
      const player = availablePlayers.find(p => p.id === playerId);

      // Check if this player is already selected in another position
      const existingPosition = newSelections.findIndex(p => p && p.id === playerId);
      if (existingPosition !== -1) {
        // Remove the player from the other position
        newSelections[existingPosition] = null;
      }

      // Add the player to the new position
      newSelections[position] = player;
    }

    setSelectedPlayers(newSelections);
  };

  // Save the lineup
  const handleSave = async () => {
    // Check if all positions are filled
    if (selectedPlayers.some(player => player === null)) {
      setError('Bitte alle Positionen besetzen');
      return;
    }

    try {
      const lineupData = {
        team_id: teamInfo.team_id,
        is_home_team: teamInfo.is_home_team,
        positions: selectedPlayers.map((player, index) => ({
          player_id: player.id,
          position: index + 1
        }))
      };

      await saveLineup(matchId, lineupData);
      if (onSave) onSave();
    } catch (err) {
      // Check if the error is related to home team lineup creation
      if (err.response && err.response.data && err.response.data.code === 'HOME_TEAM_LINEUP_CREATION_FAILED') {
        setError('Fehler beim Erstellen der Heimmannschaftsaufstellung.');
        setHomeTeamLineupRequired(true);
      } else {
        setError('Fehler beim Speichern der Aufstellung: ' + (err.response?.data?.error || err.message));
      }
    }
  };

  if (loading) {
    return <div className="loading">Lade Spielerdaten...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  // This code block is no longer needed as we automatically create a lineup for the home team
  // We'll keep a simplified version just in case there's an error
  if (!teamInfo?.is_home_team && homeTeamLineupRequired) {
    return (
      <div className="lineup-selector">
        <h2>Aufstellung für {teamInfo?.team_name}</h2>
        <div className="home-team-lineup-required">
          <div className="alert-icon">⚠️</div>
          <h3>Fehler beim Laden der Heimmannschaftsaufstellung</h3>
          <p>
            Es gab ein Problem beim Laden der Aufstellung der Heimmannschaft.
            Bitte versuchen Sie es später erneut.
          </p>
          <div className="lineup-actions">
            <button className="btn btn-secondary" onClick={onCancel}>Zurück</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="lineup-selector">
      <h2>Aufstellung für {teamInfo?.team_name}</h2>

      {/* Zeige unterschiedliche Anweisungen je nach Heim- oder Auswärtsteam */}
      {teamInfo?.is_home_team ? (
        <p className="instructions">
          Als Heimmannschaft stellen Sie zuerst auf. Wählen Sie für jede Position einen Spieler aus.
          Nicht verfügbare Spieler sind ausgegraut.
        </p>
      ) : (
        <p className="instructions">
          Als Auswärtsmannschaft können Sie Ihre Aufstellung gegen die bereits festgelegte Heimaufstellung setzen.
          Wählen Sie für jede Position einen Spieler aus. Nicht verfügbare Spieler sind ausgegraut.
        </p>
      )}

      {/* Zeige die Aufstellung der Heimmannschaft, wenn wir das Auswärtsteam sind */}
      {!teamInfo?.is_home_team && opponentLineup && (
        <div className="opponent-lineup">
          <h3>Aufstellung der Heimmannschaft</h3>
          <div className="opponent-positions">
            {opponentLineup.map(pos => (
              <div key={pos.position} className="opponent-player">
                <div className="position-number">Position {pos.position}</div>
                <div className="player-name">{pos.player_name}</div>
                <div className="player-strength">Stärke: {pos.player_strength}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="positions-container">
        {selectedPlayers.map((selectedPlayer, position) => (
          <div key={position} className="position-selector">
            <div className="position-label">Position {position + 1}</div>
            {/* Zeige den gegnerischen Spieler an, wenn wir das Auswärtsteam sind */}
            {!teamInfo?.is_home_team && opponentLineup && (
              <div className="opponent-at-position">
                Gegen: {opponentLineup.find(p => p.position === position + 1)?.player_name || 'Unbekannt'}
              </div>
            )}
            <select
              value={selectedPlayer ? selectedPlayer.id : ''}
              onChange={(e) => handlePlayerSelect(position, e.target.value ? parseInt(e.target.value) : null)}
            >
              <option value="">-- Spieler auswählen --</option>
              {availablePlayers
                .filter(player => player.is_available)
                .map(player => (
                  <option
                    key={player.id}
                    value={player.id}
                    disabled={selectedPlayers.some(p => p && p.id === player.id && p !== selectedPlayer)}
                  >
                    {player.name} (Stärke: {player.strength})
                  </option>
                ))
              }
            </select>
            {selectedPlayer && (
              <div className="selected-player-info">
                <span className="player-name">{selectedPlayer.name}</span>
                <span className="player-strength">Stärke: {selectedPlayer.strength}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="unavailable-players">
        <h3>Nicht verfügbare Spieler</h3>
        <ul>
          {availablePlayers
            .filter(player => !player.is_available)
            .map(player => (
              <li key={player.id} className="unavailable-player">
                {player.name} (Stärke: {player.strength})
              </li>
            ))
          }
        </ul>
      </div>

      <div className="lineup-actions">
        <button className="btn btn-secondary" onClick={onCancel}>Abbrechen</button>
        <button className="btn btn-primary" onClick={handleSave}>Aufstellung speichern</button>
      </div>
    </div>
  );
};

export default LineupSelector;
