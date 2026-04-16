import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  protocols: [],
  positions: [],
  yieldFarming: [],
  arbitrageOpportunities: [],
  totalValueLocked: 0,
  apyRates: {},
  gasPrices: {},
  blockchainStatus: {},
  loading: false,
  error: null,
};

const defiSlice = createSlice({
  name: 'defi',
  initialState,
  reducers: {
    setProtocols: (state, action) => {
      state.protocols = action.payload;
    },
    setPositions: (state, action) => {
      state.positions = action.payload;
    },
    setYieldFarming: (state, action) => {
      state.yieldFarming = action.payload;
    },
    setArbitrageOpportunities: (state, action) => {
      state.arbitrageOpportunities = action.payload;
    },
    updateTVL: (state, action) => {
      state.totalValueLocked = action.payload;
    },
    updateApyRates: (state, action) => {
      state.apyRates = action.payload;
    },
    updateGasPrices: (state, action) => {
      state.gasPrices = action.payload;
    },
    setBlockchainStatus: (state, action) => {
      state.blockchainStatus = action.payload;
    },
    addPosition: (state, action) => {
      state.positions.push(action.payload);
    },
    removePosition: (state, action) => {
      state.positions = state.positions.filter(p => p.id !== action.payload);
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
  setProtocols,
  setPositions,
  setYieldFarming,
  setArbitrageOpportunities,
  updateTVL,
  updateApyRates,
  updateGasPrices,
  setBlockchainStatus,
  addPosition,
  removePosition,
  setLoading,
  setError,
} = defiSlice.actions;

export default defiSlice.reducer;
