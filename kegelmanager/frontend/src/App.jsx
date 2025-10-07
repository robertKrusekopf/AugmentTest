import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import './App.css'

// Context
import { AppProvider } from './contexts/AppContext'

// Components
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'

// Pages
import MainMenu from './pages/MainMenu'
import Dashboard from './pages/Dashboard'
import Messages from './pages/Messages'
import Clubs from './pages/Clubs'
import ClubDetail from './pages/ClubDetail'
import Teams from './pages/Teams'
import TeamDetail from './pages/TeamDetail'
import Players from './pages/Players'
import PlayerDetail from './pages/PlayerDetail'
import Leagues from './pages/Leagues'
import LeagueDetail from './pages/LeagueDetail'
import Matches from './pages/Matches'
import MatchDetail from './pages/MatchDetail'
import Finances from './pages/Finances'
import Youth from './pages/Youth'
import Transfers from './pages/Transfers'
import Settings from './pages/Settings'
import CupsOverview from './pages/CupsOverview'
import Cups from './pages/Cups'

import CupMatchDays from './pages/CupMatchDays'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [databaseSelected, setDatabaseSelected] = useState(false);
  const location = useLocation();

  useEffect(() => {
    // Check if a database has been selected
    const selectedDb = localStorage.getItem('selectedDatabase');
    if (selectedDb) {
      setDatabaseSelected(true);
    }
  }, [location]);

  // If we're at the root path and no database is selected, show the main menu
  const showMainMenu = location.pathname === '/' && !databaseSelected;

  // If we're at the main menu path, show the main menu
  const isMainMenuPath = location.pathname === '/main-menu';

  // Render the main menu if we're at the main menu path or at root with no database selected
  if (isMainMenuPath || showMainMenu) {
    return <MainMenu />;
  }

  return (
    <AppProvider>
      <div className="app-container">
        <Navbar
          toggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onLogout={() => {
            localStorage.removeItem('selectedDatabase');
            setDatabaseSelected(false);
          }}
        />
        <div className="content-container">
          <Sidebar isOpen={sidebarOpen} />
          <main className={`main-content ${sidebarOpen ? 'sidebar-open' : ''}`}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/main-menu" element={<MainMenu />} />
              <Route path="/messages" element={<Messages />} />
              <Route path="/clubs" element={<Clubs />} />
              <Route path="/clubs/:id" element={<ClubDetail />} />
              <Route path="/teams" element={<Teams />} />
              <Route path="/teams/:id" element={<TeamDetail />} />
              <Route path="/players" element={<Players />} />
              <Route path="/players/:id" element={<PlayerDetail />} />
              <Route path="/leagues" element={<Leagues />} />
              <Route path="/leagues/:id" element={<LeagueDetail />} />
              <Route path="/matches" element={<Matches />} />
              <Route path="/matches/:id" element={<MatchDetail />} />
              <Route path="/cups" element={<CupsOverview />} />
              <Route path="/cups/:cupType" element={<Cups />} />

              <Route path="/cup-match-days" element={<CupMatchDays />} />
              <Route path="/youth" element={<Youth />} />
              <Route path="/transfers" element={<Transfers />} />
              <Route path="/finances" element={<Finances />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </AppProvider>
  );
}

export default App
