import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const portfolioApi = {
  getPortfolio: () => api.get('/portfolio'),
  getPositions: () => api.get('/portfolio/positions'),
  getAllocation: () => api.get('/portfolio/allocation'),
  getPerformance: (timeframe) => api.get(`/portfolio/performance?timeframe=${timeframe}`),
};

export const marketDataApi = {
  getRealTimePrices: (symbols) => api.get('/market/prices', { params: { symbols } }),
  getHistoricalData: (symbol, timeframe) => 
    api.get(`/market/historical/${symbol}`, { params: { timeframe } }),
  getMarketStatus: () => api.get('/market/status'),
  getTopMovers: () => api.get('/market/movers'),
  getIndicators: () => api.get('/market/indicators'),
};

export const signalsApi = {
  getSignals: () => api.get('/signals'),
  getActiveSignals: () => api.get('/signals/active'),
  getHistoricalSignals: () => api.get('/signals/history'),
  getSignalStats: () => api.get('/signals/stats'),
  executeSignal: (signalId) => api.post(`/signals/${signalId}/execute`),
};

export const aiAgentsApi = {
  getAgents: () => api.get('/ai/agents'),
  getAgentStatus: () => api.get('/ai/agents/status'),
  getAgentPerformance: () => api.get('/ai/agents/performance'),
  getConsensusDecisions: () => api.get('/ai/consensus'),
  toggleAgent: (agentId, status) => api.patch(`/ai/agents/${agentId}`, { status }),
};

export const defiApi = {
  getProtocols: () => api.get('/defi/protocols'),
  getPositions: () => api.get('/defi/positions'),
  getYieldFarming: () => api.get('/defi/yield-farming'),
  getArbitrageOpportunities: () => api.get('/defi/arbitrage'),
  getTVL: () => api.get('/defi/tvl'),
  getApyRates: () => api.get('/defi/apy'),
  getGasPrices: () => api.get('/defi/gas'),
  getBlockchainStatus: () => api.get('/defi/blockchain/status'),
};

export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  refreshToken: () => api.post('/auth/refresh'),
  getUser: () => api.get('/auth/user'),
};

export default api;
