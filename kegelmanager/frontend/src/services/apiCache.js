import axios from 'axios';

const API_URL = '/api';

// Create axios instance with optimized settings
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and logging
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Cache implementation
class APICache {
  constructor() {
    this.cache = new Map();
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
  }

  generateKey(url, params = {}) {
    const paramString = Object.keys(params).length > 0 ? JSON.stringify(params) : '';
    return `${url}${paramString}`;
  }

  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  get(key) {
    const cached = this.cache.get(key);
    if (!cached) return null;

    const isExpired = Date.now() - cached.timestamp > this.cacheExpiry;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  invalidate(pattern) {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  clear() {
    this.cache.clear();
  }
}

const cache = new APICache();

// Generic cached request function
const cachedRequest = async (url, options = {}, useCache = true) => {
  const cacheKey = cache.generateKey(url, options.params);
  
  // Try to get from cache first
  if (useCache) {
    const cachedData = cache.get(cacheKey);
    if (cachedData) {
      console.log(`Cache hit for: ${url}`);
      return cachedData;
    }
  }

  try {
    console.log(`Cache miss, fetching: ${url}`);
    const response = await api.get(url, options);
    
    // Cache the response
    if (useCache) {
      cache.set(cacheKey, response.data);
    }
    
    return response.data;
  } catch (error) {
    console.error(`Error fetching ${url}:`, error);
    throw error;
  }
};

// Optimized API functions with parallel loading support
export const getClubsOptimized = (useCache = true) => 
  cachedRequest('/clubs', {}, useCache);

export const getTeamsOptimized = (useCache = true) => 
  cachedRequest('/teams', {}, useCache);

export const getLeaguesOptimized = (useCache = true) => 
  cachedRequest('/leagues', {}, useCache);

export const getPlayersOptimized = (useCache = true) => 
  cachedRequest('/players', {}, useCache);

export const getMatchesOptimized = (useCache = true) =>
  cachedRequest('/matches', {}, useCache);

export const getCupsOptimized = (useCache = true) =>
  cachedRequest('/cups', {}, useCache);

export const getCupsByTypeOptimized = (cupType, useCache = true) =>
  cachedRequest(`/cups/by-type/${cupType}`, {}, useCache);

export const getCupDetailOptimized = (cupId, useCache = true) =>
  cachedRequest(`/cups/${cupId}`, {}, useCache);

export const getCupMatchDaysOptimized = (useCache = true) =>
  cachedRequest('/cups/match-days', {}, useCache);

export const getCupsHistoryOptimized = (useCache = true) =>
  cachedRequest('/cups/history', {}, useCache);

export const getCupsHistoryByTypeOptimized = (cupType, useCache = true) =>
  cachedRequest(`/cups/history/${cupType}`, {}, useCache);

export const getCupHistoryByNameOptimized = (cupName, useCache = true) =>
  cachedRequest(`/cups/history/cup/${encodeURIComponent(cupName)}`, {}, useCache);

export const getTeamOptimized = (id, useCache = true) =>
  cachedRequest(`/teams/${id}`, {}, useCache);

export const getTeamHistoryOptimized = (id, useCache = true) =>
  cachedRequest(`/teams/${id}/history`, {}, useCache);

export const getTeamCupHistoryOptimized = (id, useCache = true) =>
  cachedRequest(`/teams/${id}/cup-history`, {}, useCache);

// Parallel data loading for common combinations
export const loadDashboardData = async () => {
  console.log('Loading dashboard data in parallel...');
  const startTime = Date.now();
  
  try {
    const [clubs, teams, leagues, matches] = await Promise.all([
      getClubsOptimized(),
      getTeamsOptimized(),
      getLeaguesOptimized(),
      getMatchesOptimized()
    ]);
    
    const endTime = Date.now();
    console.log(`Dashboard data loaded in ${endTime - startTime}ms`);
    
    return { clubs, teams, leagues, matches };
  } catch (error) {
    console.error('Error loading dashboard data:', error);
    throw error;
  }
};

export const loadOverviewData = async () => {
  console.log('Loading overview data in parallel...');
  const startTime = Date.now();
  
  try {
    const [clubs, teams, leagues] = await Promise.all([
      getClubsOptimized(),
      getTeamsOptimized(),
      getLeaguesOptimized()
    ]);
    
    const endTime = Date.now();
    console.log(`Overview data loaded in ${endTime - startTime}ms`);
    
    return { clubs, teams, leagues };
  } catch (error) {
    console.error('Error loading overview data:', error);
    throw error;
  }
};

// Cache management functions
export const invalidateCache = (pattern) => {
  console.log(`Invalidating cache for pattern: ${pattern}`);
  cache.invalidate(pattern);
};

export const clearAllCache = () => {
  console.log('Clearing all cache');
  cache.clear();
};

// Cache after data mutations
export const invalidateAfterSimulation = () => {
  invalidateCache('/matches');
  invalidateCache('/teams');
  invalidateCache('/leagues');
  invalidateCache('/players');
  invalidateCache('/cups'); // Invalidate cup data after simulation
};

export const invalidateAfterPlayerUpdate = () => {
  invalidateCache('/players');
  invalidateCache('/teams');
};

export const invalidateAfterClubUpdate = () => {
  invalidateCache('/clubs');
  invalidateCache('/teams');
};

export const invalidateAfterSeasonTransition = () => {
  // Clear all cache after season transition since leagues, teams, matches, and cup history change
  clearAllCache();
};

// Export the cache instance for direct access if needed
export { cache };

// Export original API instance for non-cached requests
export { api };
