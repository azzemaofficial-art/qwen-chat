import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  signals: [],
  activeSignals: [],
  historicalSignals: [],
  signalStats: {
    total: 0,
    profitable: 0,
    winRate: 0,
    avgReturn: 0,
    sharpeRatio: 0,
  },
  aiConfidence: 0,
  loading: false,
  error: null,
};

const tradingSignalsSlice = createSlice({
  name: 'tradingSignals',
  initialState,
  reducers: {
    addSignal: (state, action) => {
      state.signals.unshift(action.payload);
      state.signalStats.total += 1;
    },
    setActiveSignals: (state, action) => {
      state.activeSignals = action.payload;
    },
    setHistoricalSignals: (state, action) => {
      state.historicalSignals = action.payload;
    },
    updateSignalStats: (state, action) => {
      state.signalStats = action.payload;
    },
    updateAiConfidence: (state, action) => {
      state.aiConfidence = action.payload;
    },
    removeSignal: (state, action) => {
      state.signals = state.signals.filter(s => s.id !== action.payload);
      state.activeSignals = state.activeSignals.filter(s => s.id !== action.payload);
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
  addSignal,
  setActiveSignals,
  setHistoricalSignals,
  updateSignalStats,
  updateAiConfidence,
  removeSignal,
  setLoading,
  setError,
} = tradingSignalsSlice.actions;

export default tradingSignalsSlice.reducer;
