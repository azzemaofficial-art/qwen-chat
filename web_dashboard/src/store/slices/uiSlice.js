import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  sidebarOpen: true,
  currentView: 'dashboard',
  theme: 'dark',
  notifications: [],
  selectedTimeframe: '1D',
  watchlist: [],
  settings: {
    autoRefresh: true,
    refreshInterval: 5000,
    soundEnabled: true,
    pushNotifications: true,
    riskLevel: 'medium',
  },
  loading: false,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action) => {
      state.sidebarOpen = action.payload;
    },
    setCurrentView: (state, action) => {
      state.currentView = action.payload;
    },
    setTheme: (state, action) => {
      state.theme = action.payload;
    },
    addNotification: (state, action) => {
      state.notifications.unshift(action.payload);
    },
    removeNotification: (state, action) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    setSelectedTimeframe: (state, action) => {
      state.selectedTimeframe = action.payload;
    },
    setWatchlist: (state, action) => {
      state.watchlist = action.payload;
    },
    addToWatchlist: (state, action) => {
      if (!state.watchlist.includes(action.payload)) {
        state.watchlist.push(action.payload);
      }
    },
    removeFromWatchlist: (state, action) => {
      state.watchlist = state.watchlist.filter(w => w !== action.payload);
    },
    updateSettings: (state, action) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  setCurrentView,
  setTheme,
  addNotification,
  removeNotification,
  clearNotifications,
  setSelectedTimeframe,
  setWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  updateSettings,
  setLoading,
} = uiSlice.actions;

export default uiSlice.reducer;
