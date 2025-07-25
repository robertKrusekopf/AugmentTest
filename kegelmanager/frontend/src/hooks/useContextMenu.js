import { useState, useCallback } from 'react';

const useContextMenu = () => {
  const [contextMenu, setContextMenu] = useState({
    visible: false,
    x: 0,
    y: 0,
    items: []
  });

  const showContextMenu = useCallback((event, items) => {
    event.preventDefault();
    event.stopPropagation();

    // Get viewport dimensions
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Estimate menu dimensions (you might want to measure actual menu)
    const menuWidth = 200;
    const menuHeight = items.length * 32 + 8; // Rough estimate
    
    // Calculate position, ensuring menu stays within viewport
    let x = event.clientX;
    let y = event.clientY;
    
    if (x + menuWidth > viewportWidth) {
      x = viewportWidth - menuWidth - 10;
    }
    
    if (y + menuHeight > viewportHeight) {
      y = viewportHeight - menuHeight - 10;
    }

    setContextMenu({
      visible: true,
      x,
      y,
      items
    });
  }, []);

  const hideContextMenu = useCallback(() => {
    setContextMenu(prev => ({
      ...prev,
      visible: false
    }));
  }, []);

  const getContextMenuProps = useCallback((items) => ({
    onContextMenu: (event) => showContextMenu(event, items)
  }), [showContextMenu]);

  return {
    contextMenu,
    showContextMenu,
    hideContextMenu,
    getContextMenuProps
  };
};

export default useContextMenu;
