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

export const updateClub = async (id, clubData) => {
  try {
    const response = await api.patch(`/clubs/${id}`, clubData);
    return response.data;
  } catch (error) {
    console.error(`Error updating club ${id}:`, error);
    throw error;
  }
};

export const addTeamToClub = async (clubId, teamData) => {
  try {
    const response = await api.post(`/clubs/${clubId}/teams`, teamData);
    return response.data;
  } catch (error) {
    console.error(`Error adding team to club ${clubId}:`, error);
    throw error;
  }
};

export const getClubRecentMatches = async (clubId) => {
  try {
    const response = await api.get(`/clubs/${clubId}/recent-matches`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching recent matches for club ${clubId}:`, error);
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

export const getTeamHistory = async (id) => {
  try {
    const response = await api.get(`/teams/${id}/history`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching team history for team ${id}:`, error);
    throw error;
  }
};

export const getTeamCupHistory = async (id) => {
  try {
    const response = await api.get(`/teams/${id}/cup-history`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching team cup history for team ${id}:`, error);
    throw error;
  }
};

export const getTeamAchievements = async (id) => {
  try {
    const response = await api.get(`/teams/${id}/achievements`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching team achievements for team ${id}:`, error);
    throw error;
  }
};

export const updateTeam = async (id, teamData) => {
  try {
    const response = await api.patch(`/teams/${id}`, teamData);
    return response.data;
  } catch (error) {
    console.error(`Error updating team ${id}:`, error);
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

export const getPlayerHistory = async (id) => {
  try {
    const response = await api.get(`/players/${id}/history`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching player history for ${id}:`, error);
    throw error;
  }
};

export const getPlayerMatches = async (id) => {
  try {
    const response = await api.get(`/players/${id}/matches`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching player matches for ${id}:`, error);
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

export const getLeagueHistory = async (id) => {
  try {
    const response = await api.get(`/leagues/${id}/history`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching league history for league ${id}:`, error);
    throw error;
  }
};

export const getLeagueHistorySeason = async (leagueId, seasonId) => {
  try {
    const response = await api.get(`/leagues/${leagueId}/history/${seasonId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching league history for league ${leagueId} and season ${seasonId}:`, error);
    throw error;
  }
};

// Cup history endpoints
export const getCupsHistory = async () => {
  try {
    const response = await api.get('/cups/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching cups history:', error);
    throw error;
  }
};

export const getCupsHistoryByType = async (cupType) => {
  try {
    const response = await api.get(`/cups/history/${cupType}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching cups history for type ${cupType}:`, error);
    throw error;
  }
};

export const getCupHistoryByName = async (cupName) => {
  try {
    const response = await api.get(`/cups/history/cup/${encodeURIComponent(cupName)}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching cup history for ${cupName}:`, error);
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

export const getSeasonStatus = async () => {
  try {
    const response = await api.get('/season/status');
    return response.data;
  } catch (error) {
    console.error('Error fetching season status:', error);
    throw error;
  }
};

export const transitionToNewSeason = async () => {
  try {
    const response = await api.post('/season/transition');
    return response.data;
  } catch (error) {
    console.error('Error transitioning to new season:', error);
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

// Lineup management endpoints
export const getAvailablePlayersForMatch = async (matchId, managedClubId) => {
  try {
    const response = await api.get(`/matches/${matchId}/available-players`, {
      params: { managed_club_id: managedClubId }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching available players for match:', error);
    throw error;
  }
};

export const saveLineup = async (matchId, lineupData) => {
  try {
    const response = await api.post(`/matches/${matchId}/lineup`, lineupData);
    return response.data;
  } catch (error) {
    console.error('Error saving lineup:', error);
    throw error;
  }
};

export const getLineup = async (matchId, teamId, isHomeTeam) => {
  try {
    const response = await api.get(`/matches/${matchId}/lineup`, {
      params: { team_id: teamId, is_home_team: isHomeTeam }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching lineup:', error);
    throw error;
  }
};

export const deleteLineup = async (matchId, teamId, isHomeTeam) => {
  try {
    const response = await api.delete(`/matches/${matchId}/lineup`, {
      params: { team_id: teamId, is_home_team: isHomeTeam }
    });
    return response.data;
  } catch (error) {
    console.error('Error deleting lineup:', error);
    throw error;
  }
};

// Transfer endpoints
export const getTransfers = async (managedClubId) => {
  try {
    const response = await api.get('/transfers', {
      params: { managed_club_id: managedClubId }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching transfers:', error);
    throw error;
  }
};

export const createTransferOffer = async (playerId, offeringClubId, offerAmount) => {
  try {
    // Check if cheat mode is enabled
    const savedSettings = localStorage.getItem('gameSettings');
    let cheatMode = false;

    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        cheatMode = settings.cheats?.cheatMode || false;
      } catch (e) {
        console.error('Failed to parse saved settings:', e);
      }
    }

    const response = await api.post('/transfers/offer', {
      player_id: playerId,
      offering_club_id: offeringClubId,
      offer_amount: offerAmount
    }, {
      headers: {
        'X-Cheat-Mode': cheatMode.toString()
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error creating transfer offer:', error);
    throw error;
  }
};

export const updateTransferOffer = async (offerId, action) => {
  try {
    const response = await api.patch(`/transfers/offer/${offerId}`, {
      action: action
    });
    return response.data;
  } catch (error) {
    console.error('Error updating transfer offer:', error);
    throw error;
  }
};

export const withdrawTransferOffer = async (offerId) => {
  try {
    const response = await api.delete(`/transfers/offer/${offerId}`);
    return response.data;
  } catch (error) {
    console.error('Error withdrawing transfer offer:', error);
    throw error;
  }
};

// Global search endpoint
export const globalSearch = async (query) => {
  try {
    const response = await api.get('/search', {
      params: { q: query }
    });
    return response.data;
  } catch (error) {
    console.error('Error performing global search:', error);
    throw error;
  }
};

export default api;
