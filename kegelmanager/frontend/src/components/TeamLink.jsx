import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './TeamLink.css';

/**
 * TeamLink Component
 * 
 * A reusable component that displays a team name as a clickable link
 * with a context menu (right-click) to navigate to the club instead.
 * 
 * Props:
 * - teamId: ID of the team (required)
 * - clubId: ID of the club (required for context menu)
 * - teamName: Display name of the team (required)
 * - className: Additional CSS classes
 * - children: Custom content to display (if not provided, teamName is used)
 */
const TeamLink = ({ teamId, clubId, teamName, className = '', children }) => {
  const [contextMenu, setContextMenu] = useState(null);
  const navigate = useNavigate();
  const menuRef = useRef(null);

  // Handle right-click on team name
  const handleContextMenu = (event) => {
    event.preventDefault();
    event.stopPropagation();

    // Only show context menu if clubId is available
    if (!clubId) {
      return;
    }

    setContextMenu({
      mouseX: event.clientX,
      mouseY: event.clientY,
    });
  };

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setContextMenu(null);
      }
    };

    const handleScroll = () => {
      setContextMenu(null);
    };

    if (contextMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('scroll', handleScroll, true);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('scroll', handleScroll, true);
      };
    }
  }, [contextMenu]);

  // Handle navigation to club
  const handleNavigateToClub = () => {
    setContextMenu(null);
    navigate(`/clubs/${clubId}`);
  };

  // Handle navigation to team (for context menu option)
  const handleNavigateToTeam = () => {
    setContextMenu(null);
    navigate(`/teams/${teamId}`);
  };

  return (
    <>
      <Link
        to={`/teams/${teamId}`}
        className={`team-link ${className}`}
        onContextMenu={handleContextMenu}
      >
        {children || teamName}
      </Link>

      {contextMenu && (
        <div
          ref={menuRef}
          className="team-context-menu"
          style={{
            position: 'fixed',
            top: contextMenu.mouseY,
            left: contextMenu.mouseX,
          }}
        >
          <div className="context-menu-item" onClick={handleNavigateToTeam}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <span>Zur Mannschaft</span>
          </div>
          <div className="context-menu-item" onClick={handleNavigateToClub}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
              <polyline points="9 22 9 12 15 12 15 22"></polyline>
            </svg>
            <span>Zum Verein</span>
          </div>
        </div>
      )}
    </>
  );
};

export default TeamLink;

