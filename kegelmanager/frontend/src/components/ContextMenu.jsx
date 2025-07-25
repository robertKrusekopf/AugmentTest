import React, { useState, useEffect, useRef } from 'react';
import '../styles/ContextMenu.css';

const ContextMenu = ({ x, y, items, onClose, visible }) => {
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose();
      }
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (visible) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
      document.addEventListener('contextmenu', onClose); // Close on any other right-click
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('contextmenu', onClose);
    };
  }, [visible, onClose]);

  if (!visible) return null;

  return (
    <div
      ref={menuRef}
      className="context-menu"
      style={{
        position: 'fixed',
        top: y,
        left: x,
        zIndex: 1000,
      }}
    >
      <ul className="context-menu-list">
        {items.map((item, index) => (
          <li key={index} className="context-menu-item">
            {item.separator ? (
              <hr className="context-menu-separator" />
            ) : (
              <button
                className={`context-menu-button ${item.disabled ? 'disabled' : ''}`}
                onClick={() => {
                  if (!item.disabled && item.onClick) {
                    item.onClick();
                  }
                  onClose();
                }}
                disabled={item.disabled}
              >
                {item.icon && <span className="context-menu-icon">{item.icon}</span>}
                <span className="context-menu-label">{item.label}</span>
                {item.shortcut && <span className="context-menu-shortcut">{item.shortcut}</span>}
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ContextMenu;
