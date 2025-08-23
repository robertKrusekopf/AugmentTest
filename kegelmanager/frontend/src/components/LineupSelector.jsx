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
          is_home_team: data.is_home_team,
          home_team_name: data.home_team_name,
          away_team_name: data.away_team_name
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

  // Helper function to get opponent team name
  const getOpponentTeamName = () => {
    if (!teamInfo) return 'Gegner';
    return teamInfo.is_home_team ? 'Auswärtsteam' : 'Heimteam';
  };

  return (
    <div className="lineup-selector">
      <h2>Aufstellung festlegen</h2>

      {/* Action buttons at the top */}
      <div className="lineup-actions-top">
        <button className="btn btn-secondary" onClick={onCancel}>Abbrechen</button>
        <button className="btn btn-primary" onClick={handleSave}>Aufstellung speichern</button>
      </div>

      {/* Instructions */}
      {teamInfo?.is_home_team ? (
        <p className="instructions">
          Als Heimmannschaft stellen Sie zuerst auf. Wählen Sie für jede Position einen Spieler aus.
        </p>
      ) : (
        <p className="instructions">
          Als Auswärtsmannschaft können Sie Ihre Aufstellung gegen die bereits festgelegte Heimaufstellung setzen.
        </p>
      )}

      {/* Two-column layout for lineups */}
      <div className="lineups-container">
        {/* Home team column */}
        <div className="team-lineup-column">
          <h3 className="team-header">
            {teamInfo?.home_team_name ? `${teamInfo.home_team_name} (Heim)` : 'Heimteam'}
          </h3>

          <div className="lineup-table">
            {[1, 2, 3, 4, 5, 6].map(position => {
              const isMyTeam = teamInfo?.is_home_team;
              const selectedPlayer = isMyTeam ? selectedPlayers[position - 1] : null;
              const opponentPlayer = !isMyTeam && opponentLineup ?
                opponentLineup.find(p => p.position === position) : null;

              return (
                <div key={position} className="position-row">
                  <div className="position-label">Position {position}</div>
                  <div className="player-selection">
                    {isMyTeam ? (
                      // Interactive selection for my team
                      <>
                        <select
                          value={selectedPlayer ? selectedPlayer.id : ''}
                          onChange={(e) => handlePlayerSelect(position - 1, e.target.value ? parseInt(e.target.value) : null)}
                          className="player-select"
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
                                {player.name}
                              </option>
                            ))
                          }
                        </select>
                        {selectedPlayer && (
                          <div className="selected-player-display">
                            {selectedPlayer.name}
                          </div>
                        )}
                      </>
                    ) : (
                      // Read-only display for opponent
                      <div className="opponent-player-display">
                        {opponentPlayer ? opponentPlayer.player_name : 'Noch nicht festgelegt'}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Away team column */}
        <div className="team-lineup-column">
          <h3 className="team-header">
            {teamInfo?.away_team_name ? `${teamInfo.away_team_name} (Auswärts)` : 'Auswärtsteam'}
          </h3>

          <div className="lineup-table">
            {[1, 2, 3, 4, 5, 6].map(position => {
              const isMyTeam = !teamInfo?.is_home_team;
              const selectedPlayer = isMyTeam ? selectedPlayers[position - 1] : null;

              return (
                <div key={position} className="position-row">
                  <div className="position-label">Position {position}</div>
                  <div className="player-selection">
                    {isMyTeam ? (
                      // Interactive selection for my team
                      <>
                        <select
                          value={selectedPlayer ? selectedPlayer.id : ''}
                          onChange={(e) => handlePlayerSelect(position - 1, e.target.value ? parseInt(e.target.value) : null)}
                          className="player-select"
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
                                {player.name}
                              </option>
                            ))
                          }
                        </select>
                        {selectedPlayer && (
                          <div className="selected-player-display">
                            {selectedPlayer.name}
                          </div>
                        )}
                      </>
                    ) : (
                      // Read-only display for opponent (away team not set yet)
                      <div className="opponent-player-display">
                        Noch nicht festgelegt
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Unavailable players section - unchanged */}
      <div className="unavailable-players">
        <h3>Nicht verfügbare Spieler</h3>
        <ul>
          {availablePlayers
            .filter(player => !player.is_available)
            .map(player => (
              <li key={player.id} className="unavailable-player">
                {player.name}
              </li>
            ))
          }
        </ul>
      </div>


    </div>
  );
};

export default LineupSelector;
