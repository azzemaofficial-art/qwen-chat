import { configureStore } from '@reduxjs/toolkit';
import portfolioReducer from './slices/portfolioSlice';
import marketDataReducer from './slices/marketDataSlice';
import tradingSignalsReducer from './slices/tradingSignalsSlice';
import aiAgentsReducer from './slices/aiAgentsSlice';
import defiReducer from './slices/defiSlice';
import uiReducer from './slices/uislice';

export const store = configureStore({
  reducer: {
    portfolio: portfolioReducer,
    marketData: marketDataReducer,
    tradingSignals: tradingSignalsReducer,
    aiAgents: aiAgentsReducer,
    defi: defiReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['portfolio/updateRealTimeData'],
        ignoredPaths: ['marketData.realTimePrices'],
      },
    }),
});

export default store;
