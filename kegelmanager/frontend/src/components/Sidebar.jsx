import { useState, useEffect } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { getClubs, getClub, getUnreadMessageCount } from '../services/api';
import { useAppContext } from '../contexts/AppContext';
import './Sidebar.css';

const Sidebar = ({ isOpen }) => {
  const { managedClubId } = useAppContext();
  const [userClub, setUserClub] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unreadMessageCount, setUnreadMessageCount] = useState(0);


  // Lade den Verein des Benutzers basierend auf managedClubId aus AppContext
  const loadUserClub = async () => {
    try {
      setLoading(true);

      // Verwende managedClubId aus AppContext (bereits vom Backend geladen)
      if (managedClubId) {
        try {
          const club = await getClub(managedClubId);
          setUserClub(club);
        } catch (error) {
          console.error(`Fehler beim Laden des Vereins mit ID ${managedClubId}:`, error);
          // Fallback: Setze keinen Verein als aktiv
          setUserClub(null);
        }
      } else {
        // Kein Verein ausgewählt (vereinslos)
        setUserClub(null);
      }

      setLoading(false);
    } catch (error) {
      console.error('Fehler beim Laden des Vereins:', error);
      setLoading(false);
    }
  };

  // Lade die Anzahl ungelesener Nachrichten
  const loadUnreadMessageCount = async () => {
    try {
      const data = await getUnreadMessageCount();
      setUnreadMessageCount(data.count || 0);
    } catch (error) {
      console.error('Fehler beim Laden der ungelesenen Nachrichten:', error);
      setUnreadMessageCount(0);
    }
  };

  // Lade den Verein wenn managedClubId sich ändert
  useEffect(() => {
    loadUserClub();
  }, [managedClubId]);

  // Lade ungelesene Nachrichten beim ersten Rendern
  useEffect(() => {
    loadUnreadMessageCount();
  }, []);

  // Aktualisiere die Anzahl ungelesener Nachrichten regelmäßig
  useEffect(() => {
    // Lade initial
    loadUnreadMessageCount();

    // Aktualisiere alle 30 Sekunden
    const interval = setInterval(() => {
      loadUnreadMessageCount();
    }, 30000);

    // Event-Listener für manuelle Aktualisierung
    const handleMessageUpdate = () => {
      loadUnreadMessageCount();
    };

    window.addEventListener('messagesUpdated', handleMessageUpdate);

    // Cleanup
    return () => {
      clearInterval(interval);
      window.removeEventListener('messagesUpdated', handleMessageUpdate);
    };
  }, []);

  // Note: We no longer need to listen to localStorage changes
  // because we use managedClubId from AppContext which is the source of truth
  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-content">
        <div className="club-info">
          {loading ? (
            <div className="loading-club">Laden...</div>
          ) : userClub ? (
            <Link to={`/clubs/${userClub.id}`} className="club-info-link">
              <div className="club-logo">
                {userClub.emblem_url ? (
                  <img
                    src={userClub.emblem_url}
                    alt={`${userClub.name} Wappen`}
                    className="club-emblem"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                ) : (
                  <span>{userClub.name.substring(0, 3).toUpperCase()}</span>
                )}
              </div>
              <div className="club-details">
                <h3 className="club-name">{userClub.name}</h3>
                <p className="club-league">
                  {userClub.teams && userClub.teams.length > 0
                    ? `${userClub.teams.length} Teams`
                    : 'Keine Teams'}
                </p>
              </div>
            </Link>
          ) : (
            <div className="no-club">
              <div className="no-club-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
              </div>
              <span>Vereinslos</span>
            </div>
          )}
        </div>

        <nav className="sidebar-nav">
          <ul>
            <li>
              <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="7" height="9"></rect>
                  <rect x="14" y="3" width="7" height="5"></rect>
                  <rect x="14" y="12" width="7" height="9"></rect>
                  <rect x="3" y="16" width="7" height="5"></rect>
                </svg>
                <span>Dashboard</span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/messages" className={({ isActive }) => isActive ? 'active' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                  <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
                <span>
                  Nachrichten
                  {unreadMessageCount > 0 && (
                    <span className="unread-badge">{unreadMessageCount}</span>
                  )}
                </span>
              </NavLink>
            </li>
            <li>
              <NavLink
                to={userClub ? `/clubs/${userClub.id}` : "/clubs"}
                className={({ isActive }) => isActive ? 'active' : ''}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                  <polyline points="9 22 9 12 15 12 15 22"></polyline>
                </svg>
                <span>{userClub ? 'Verein' : 'Vereine'}</span>
              </NavLink>
            </li>
            <li>
              <NavLink
                to={userClub && userClub.teams_info && userClub.teams_info.length > 0
                  ? `/teams/${(() => {
                      // Finde die erste Nicht-Jugendmannschaft
                      const firstTeam = userClub.teams_info.find(team => !team.is_youth_team);
                      return firstTeam ? firstTeam.id : userClub.teams_info[0].id;
                    })()}`
                  : "/teams"}
                className={({ isActive }) => isActive ? 'active' : ''}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <span>{userClub ? 'Mannschaft' : 'Mannschaften'}</span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/players" className={({ isActive }) => isActive ? 'active' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
                <span>Spieler</span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/leagues" className={({ isActive }) => isActive ? 'active' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="8" y1="6" x2="21" y2="6"></line>
                  <line x1="8" y1="12" x2="21" y2="12"></line>
                  <line x1="8" y1="18" x2="21" y2="18"></line>
                  <line x1="3" y1="6" x2="3.01" y2="6"></line>
                  <line x1="3" y1="12" x2="3.01" y2="12"></line>
                  <line x1="3" y1="18" x2="3.01" y2="18"></line>
                </svg>
                <span>Ligen</span>
              </NavLink>
            </li>
            <li>
              <NavLink
                to={userClub && userClub.teams_info && userClub.teams_info.length > 0
                  ? `/teams/${(() => {
                      // Finde die erste Nicht-Jugendmannschaft
                      const firstTeam = userClub.teams_info.find(team => !team.is_youth_team);
                      return firstTeam ? firstTeam.id : userClub.teams_info[0].id;
                    })()}?tab=matches`
                  : "/matches"}
                className={({ isActive }) => isActive ? 'active' : ''}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polygon points="10 8 16 12 10 16 10 8"></polygon>
                </svg>
                <span>Spiele</span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/cups" className={({ isActive }) => isActive ? 'active' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
                  <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
                  <path d="M4 22h16"></path>
                  <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path>
                  <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path>
                  <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>
                </svg>
                <span>Pokal</span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/youth" className={({ isActive }) => isActive ? 'active' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <span>Jugend</span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/transfers" className={({ isActive }) => isActive ? 'active' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <polyline points="19 12 12 19 5 12"></polyline>
                </svg>
                <span>Transfers</span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/finances" className={({ isActive }) => isActive ? 'active' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="1" x2="12" y2="23"></line>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
                <span>Finanzen</span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/settings" className={({ isActive }) => isActive ? 'active' : ''}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
                <span>Einstellungen</span>
              </NavLink>
            </li>
          </ul>
        </nav>

        <div className="sidebar-footer">
          <div className="finance-summary">
            {loading ? (
              <div className="loading-finance">Laden...</div>
            ) : userClub ? (
              <>
                <div className="finance-item">
                  <span className="finance-label">Kontostand:</span>
                  <span className="finance-value">
                    {userClub.finances && userClub.finances.balance
                      ? `€${userClub.finances.balance.toLocaleString('de-DE')}`
                      : '€0'}
                  </span>
                </div>
                <div className="finance-item">
                  <span className="finance-label">Wöchentlich:</span>
                  <span className={`finance-value ${userClub.finances && userClub.finances.weekly_balance > 0 ? 'positive' : 'negative'}`}>
                    {userClub.finances && userClub.finances.weekly_balance
                      ? `${userClub.finances.weekly_balance > 0 ? '+' : ''}€${userClub.finances.weekly_balance.toLocaleString('de-DE')}`
                      : '€0'}
                  </span>
                </div>
              </>
            ) : (
              <div className="no-finance">
                {userClub === null ? "Als vereinsloser Manager sind keine Finanzdaten verfügbar" : "Keine Finanzdaten verfügbar"}
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
