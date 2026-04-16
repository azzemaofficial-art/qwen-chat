import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  realTimePrices: {},
  historicalData: {},
  marketStatus: {},
  topGainers: [],
  topLosers: [],
  volumeLeaders: [],
  volatilityIndex: 0,
  sentimentIndex: 0,
  fearGreedIndex: 0,
  loading: false,
  error: null,
};

const marketDataSlice = createSlice({
  name: 'marketData',
  initialState,
  reducers: {
    updateRealTimePrices: (state, action) => {
      state.realTimePrices = { ...state.realTimePrices, ...action.payload };
    },
    setHistoricalData: (state, action) => {
      state.historicalData = action.payload;
    },
    setMarketStatus: (state, action) => {
      state.marketStatus = action.payload;
    },
    setTopMovers: (state, action) => {
      state.topGainers = action.payload.gainers;
      state.topLosers = action.payload.losers;
      state.volumeLeaders = action.payload.volumeLeaders;
    },
    updateIndicators: (state, action) => {
      state.volatilityIndex = action.payload.volatility;
      state.sentimentIndex = action.payload.sentiment;
      state.fearGreedIndex = action.payload.fearGreed;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
  },
});

export const {
  updateRealTimePrices,
  setHistoricalData,
  setMarketStatus,
  setTopMovers,
  updateIndicators,
  setLoading,
  setError,
} = marketDataSlice.actions;

export default marketDataSlice.reducer;
