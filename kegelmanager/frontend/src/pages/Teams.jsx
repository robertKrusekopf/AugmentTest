import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAppContext } from '../contexts/AppContext';
import ClubEmblem from '../components/ClubEmblem';
import './Teams.css';

const Teams = () => {
  const { getTeams } = useAppContext();
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterLeague, setFilterLeague] = useState('');

  // Lade Daten aus dem Context (mit Caching)
  useEffect(() => {
    const loadTeams = async () => {
      try {
        console.log('Lade Teams aus dem Context...');
        setLoading(true);

        const data = await getTeams();

        // Wenn keine Daten zurückgegeben werden, verwende leere Liste
        if (!data || data.length === 0) {
          console.warn('Keine Teams in der Datenbank gefunden.');
          setTeams([]);
        } else {
          // Verarbeite die Daten und füge fehlende Eigenschaften hinzu
          const processedTeams = data.map(team => {
            // Bestimme den Verein des Teams und das Emblem
            let clubName = 'Unbekannt';
            let emblemUrl = null;
            if (team.club) {
              if (team.club.name) {
                clubName = team.club.name;
              }
              if (team.club.emblem_url) {
                emblemUrl = team.club.emblem_url;
              } else if (team.emblem_url) {
                emblemUrl = team.emblem_url;
              }
            }

            // Bestimme die Liga des Teams
            let leagueName = 'Unbekannt';
            if (team.league && team.league.name) {
              leagueName = team.league.name;
            }

            // Bestimme die Anzahl der Spieler im Team
            const playerCount = team.players ? team.players.length : 0;

            // Berechne die durchschnittliche Stärke der Spieler
            let avgStrength = 50;
            if (team.players && team.players.length > 0) {
              const totalStrength = team.players.reduce((sum, player) => sum + (player.strength || 50), 0);
              avgStrength = Math.round(totalStrength / team.players.length);
            }

            // Überprüfe, ob es sich um ein Jugendteam handelt
            const isYouth = team.name.includes('U19') || team.name.includes('U17') || team.name.includes('Jugend');

            // Stelle sicher, dass alle benötigten Eigenschaften vorhanden sind
            return {
              id: team.id,
              name: team.name,
              club: clubName,
              emblemUrl: emblemUrl, // Füge die Emblem-URL hinzu
              league: leagueName,
              position: team.position || 0,
              isYouth: isYouth,
              players: playerCount,
              avgStrength: avgStrength
            };
          });

          setTeams(processedTeams);
        }
      } catch (error) {
        console.error('Fehler beim Laden der Teams:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTeams();
  }, [getTeams]);

  // Filtern der Teams basierend auf dem Suchbegriff und der Liga
  const filteredTeams = teams.filter(team => {
    const nameMatch = team.name.toLowerCase().includes(searchTerm.toLowerCase());
    const leagueMatch = filterLeague === '' || team.league === filterLeague;

    return nameMatch && leagueMatch;
  });

  // Extrahieren der verfügbaren Ligen für den Filter
  const leagues = [...new Set(teams.map(team => team.league))];

  if (loading) {
    return <div className="loading">Lade Teams...</div>;
  }

  return (
    <div className="teams-page">
      <h1 className="page-title">Mannschaften</h1>

      <div className="filters">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Mannschaft suchen..."
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
            value={filterLeague}
            onChange={(e) => setFilterLeague(e.target.value)}
          >
            <option value="">Alle Ligen</option>
            {leagues.map(league => (
              <option key={league} value={league}>{league}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="teams-grid">
        {filteredTeams.map(team => (
          <Link to={`/teams/${team.id}`} key={team.id} className="team-card">
            <div className="team-header">
              <div className="team-logo">
                <ClubEmblem
                  emblemUrl={team.emblemUrl}
                  clubName={team.club}
                  className="club-emblem"
                />
              </div>
              <div className="team-title">
                <h2 className="team-name">{team.name}</h2>
                <div className="team-club">{team.club}</div>
              </div>
              {team.isYouth && (
                <div className="team-badge youth">Jugend</div>
              )}
            </div>

            <div className="team-details">
              <div className="team-detail">
                <span className="detail-label">Liga:</span>
                <span className="detail-value">{team.league}</span>
              </div>
              <div className="team-detail">
                <span className="detail-label">Position:</span>
                <span className="detail-value">{team.position}. Platz</span>
              </div>
              <div className="team-detail">
                <span className="detail-label">Spieler:</span>
                <span className="detail-value">{team.players}</span>
              </div>
              <div className="team-detail">
                <span className="detail-label">Ø Stärke:</span>
                <div className="strength-bar">
                  <div
                    className="strength-fill"
                    style={{ width: `${team.avgStrength}%` }}
                  ></div>
                </div>
                <span className="strength-value">{Math.floor(team.avgStrength)}</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Teams;
