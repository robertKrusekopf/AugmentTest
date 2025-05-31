import React, { createContext, useContext, useState, useEffect } from 'react';
import * as api from '../services/api';
import { 
  getClubsOptimized, 
  getTeamsOptimized, 
  getLeaguesOptimized, 
  getPlayersOptimized, 
  getMatchesOptimized,
  loadOverviewData,
  clearAllCache as clearApiCache
} from '../services/apiCache';

const AppContext = createContext();

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  // Global state
  const [globalLoading, setGlobalLoading] = useState(false);
  const [currentSeason, setCurrentSeason] = useState(null);
  const [managedClubId, setManagedClubId] = useState(null);
  
  // Cached data
  const [cachedData, setCachedData] = useState({
    clubs: null,
    teams: null,
    leagues: null,
    players: null,
    matches: null,
    lastUpdated: {}
  });

  // Cache expiry time (5 minutes)
  const CACHE_EXPIRY = 5 * 60 * 1000;

  // Initialize app data
  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      setGlobalLoading(true);
      
      // Load managed club from localStorage
      const storedManagedClubId = localStorage.getItem('managedClubId');
      if (storedManagedClubId) {
        setManagedClubId(parseInt(storedManagedClubId));
      }

      // Load current season
      const season = await api.getCurrentSeason();
      setCurrentSeason(season);
      
    } catch (error) {
      console.error('Error initializing app:', error);
    } finally {
      setGlobalLoading(false);
    }
  };

  // Check if cached data is still valid
  const isCacheValid = (dataType) => {
    const lastUpdated = cachedData.lastUpdated[dataType];
    if (!lastUpdated) return false;
    return Date.now() - lastUpdated < CACHE_EXPIRY;
  };

  // Generic cache getter with API fallback
  const getCachedData = async (dataType, apiFunction, forceRefresh = false) => {
    // Return cached data if valid and not forcing refresh
    if (!forceRefresh && cachedData[dataType] && isCacheValid(dataType)) {
      console.log(`Using cached ${dataType}`);
      return cachedData[dataType];
    }

    try {
      console.log(`Loading fresh ${dataType} from API`);
      const data = await apiFunction();
      
      // Update cache
      setCachedData(prev => ({
        ...prev,
        [dataType]: data,
        lastUpdated: {
          ...prev.lastUpdated,
          [dataType]: Date.now()
        }
      }));
      
      return data;
    } catch (error) {
      console.error(`Error loading ${dataType}:`, error);
      // Return cached data if available, even if expired
      return cachedData[dataType] || null;
    }
  };

  // Specific data getters using optimized API
  const getClubs = (forceRefresh = false) => 
    getClubsOptimized(!forceRefresh);

  const getTeams = (forceRefresh = false) => 
    getTeamsOptimized(!forceRefresh);

  const getLeagues = (forceRefresh = false) => 
    getLeaguesOptimized(!forceRefresh);

  const getPlayers = (forceRefresh = false) => 
    getPlayersOptimized(!forceRefresh);

  const getMatches = (forceRefresh = false) => 
    getMatchesOptimized(!forceRefresh);

  // Invalidate cache for specific data type
  const invalidateCache = (dataType) => {
    setCachedData(prev => ({
      ...prev,
      [dataType]: null,
      lastUpdated: {
        ...prev.lastUpdated,
        [dataType]: null
      }
    }));
  };

  // Invalidate all cache
  const invalidateAllCache = () => {
    setCachedData({
      clubs: null,
      teams: null,
      leagues: null,
      players: null,
      matches: null,
      lastUpdated: {}
    });
    // Also clear API cache
    clearApiCache();
  };

  // Preload common data using optimized parallel loading
  const preloadCommonData = async () => {
    try {
      setGlobalLoading(true);
      
      // Use optimized parallel loading
      await loadOverviewData();
      
    } catch (error) {
      console.error('Error preloading data:', error);
    } finally {
      setGlobalLoading(false);
    }
  };

  const value = {
    // Global state
    globalLoading,
    setGlobalLoading,
    currentSeason,
    setCurrentSeason,
    managedClubId,
    setManagedClubId,
    
    // Cached data getters
    getClubs,
    getTeams,
    getLeagues,
    getPlayers,
    getMatches,
    
    // Cache management
    invalidateCache,
    invalidateAllCache,
    preloadCommonData,
    
    // Direct cache access for read-only operations
    cachedData
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};
