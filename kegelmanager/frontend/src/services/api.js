import axios from 'axios';

const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Club endpoints
export const getClubs = async () => {
  try {
    const response = await api.get('/clubs');
    return response.data;
  } catch (error) {
    console.error('Error fetching clubs:', error);
    throw error;
  }
};

export const getClub = async (id) => {
  try {
    const response = await api.get(`/clubs/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching club ${id}:`, error);
    throw error;
  }
};

// Team endpoints
export const getTeams = async () => {
  try {
    const response = await api.get('/teams');
    return response.data;
  } catch (error) {
    console.error('Error fetching teams:', error);
    throw error;
  }
};

export const getTeam = async (id) => {
  try {
    const response = await api.get(`/teams/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching team ${id}:`, error);
    throw error;
  }
};

// Player endpoints
export const getPlayers = async () => {
  try {
    const response = await api.get('/players');
    return response.data;
  } catch (error) {
    console.error('Error fetching players:', error);
    throw error;
  }
};

export const getPlayer = async (id) => {
  try {
    const response = await api.get(`/players/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching player ${id}:`, error);
    throw error;
  }
};

export const updatePlayer = async (id, playerData) => {
  try {
    const response = await api.patch(`/players/${id}`, playerData);
    return response.data;
  } catch (error) {
    console.error(`Error updating player ${id}:`, error);
    throw error;
  }
};

// League endpoints
export const getLeagues = async () => {
  try {
    const response = await api.get('/leagues');
    return response.data;
  } catch (error) {
    console.error('Error fetching leagues:', error);
    throw error;
  }
};

export const getLeague = async (id) => {
  try {
    const response = await api.get(`/leagues/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching league ${id}:`, error);
    throw error;
  }
};

// Match endpoints
export const getMatches = async () => {
  try {
    const response = await api.get('/matches');
    return response.data;
  } catch (error) {
    console.error('Error fetching matches:', error);
    throw error;
  }
};

export const getMatch = async (id) => {
  try {
    const response = await api.get(`/matches/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching match ${id}:`, error);
    throw error;
  }
};

// Season endpoints
export const getSeasons = async () => {
  try {
    const response = await api.get('/seasons');
    return response.data;
  } catch (error) {
    console.error('Error fetching seasons:', error);
    throw error;
  }
};

export const getSeason = async (id) => {
  try {
    const response = await api.get(`/seasons/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching season ${id}:`, error);
    throw error;
  }
};

export const getCurrentSeason = async () => {
  try {
    // Get all seasons
    const seasons = await getSeasons();
    // Find the current season
    const currentSeason = seasons.find(season => season.is_current);
    if (!currentSeason) {
      throw new Error('No current season found');
    }
    return currentSeason;
  } catch (error) {
    console.error('Error fetching current season:', error);
    throw error;
  }
};

// Simulation endpoints
export const simulateMatch = async (homeTeamId, awayTeamId) => {
  try {
    const response = await api.post('/simulate/match', {
      home_team_id: homeTeamId,
      away_team_id: awayTeamId
    });
    return response.data;
  } catch (error) {
    console.error('Error simulating match:', error);
    throw error;
  }
};

export const simulateSeason = async (seasonId, createNewSeason = true) => {
  try {
    const response = await api.post('/simulate/season', {
      season_id: seasonId,
      create_new_season: createNewSeason
    });
    return response.data;
  } catch (error) {
    console.error('Error simulating season:', error);
    throw error;
  }
};

export const simulateMatchDay = async () => {
  try {
    const response = await api.post('/simulate/match_day');
    return response.data;
  } catch (error) {
    console.error('Error simulating match day:', error);
    throw error;
  }
};

// Database initialization
export const initializeDatabase = async () => {
  try {
    const response = await api.post('/init_db');
    return response.data;
  } catch (error) {
    console.error('Error initializing database:', error);
    throw error;
  }
};

export default api;
