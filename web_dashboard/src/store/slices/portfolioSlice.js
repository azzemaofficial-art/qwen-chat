import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  totalValue: 0,
  cashBalance: 0,
  investedValue: 0,
  totalReturn: 0,
  totalReturnPercent: 0,
  dayChange: 0,
  dayChangePercent: 0,
  positions: [],
  allocation: {
    stocks: 0,
    crypto: 0,
    defi: 0,
    forex: 0,
    commodities: 0,
  },
  performance: {
    daily: [],
    weekly: [],
    monthly: [],
    yearly: [],
  },
  loading: false,
  error: null,
};

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    setPortfolio: (state, action) => {
      state.totalValue = action.payload.totalValue;
      state.cashBalance = action.payload.cashBalance;
      state.investedValue = action.payload.investedValue;
      state.totalReturn = action.payload.totalReturn;
      state.totalReturnPercent = action.payload.totalReturnPercent;
      state.positions = action.payload.positions;
      state.allocation = action.payload.allocation;
    },
    updatePositions: (state, action) => {
      state.positions = action.payload;
      state.investedValue = action.payload.reduce((sum, pos) => sum + pos.value, 0);
    },
    updateAllocation: (state, action) => {
      state.allocation = action.payload;
    },
    addPosition: (state, action) => {
      state.positions.push(action.payload);
      state.investedValue += action.payload.value;
    },
    removePosition: (state, action) => {
      state.positions = state.positions.filter(p => p.symbol !== action.payload);
    },
    updatePerformance: (state, action) => {
      state.performance = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    updateRealTimeData: (state, action) => {
      const { prices, changes } = action.payload;
      state.positions = state.positions.map(pos => ({
        ...pos,
        currentPrice: prices[pos.symbol] || pos.currentPrice,
        change: changes[pos.symbol] || pos.change,
        value: pos.quantity * (prices[pos.symbol] || pos.currentPrice),
      }));
      state.investedValue = state.positions.reduce((sum, pos) => sum + pos.value, 0);
      state.totalValue = state.cashBalance + state.investedValue;
    },
  },
});

export const {
  setPortfolio,
  updatePositions,
  updateAllocation,
  addPosition,
  removePosition,
  updatePerformance,
  setLoading,
  setError,
  updateRealTimeData,
} = portfolioSlice.actions;

export default portfolioSlice.reducer;
