import React, { useState } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Provider } from 'react-redux';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Box from '@mui/material/Box';
import theme from './theme';
import store from './store';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import RiskManagement from './pages/RiskManagement';
import wsService from './services/websocket';
import { useSelector } from 'react-redux';

const AppContent = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentView, setCurrentView] = useState('dashboard');
  const notifications = useSelector((state) => state.ui.notifications);
  const [wsConnected, setWsConnected] = useState(false);

  React.useEffect(() => {
    // Initialize WebSocket connection
    wsService.connect(
      () => setWsConnected(true),
      () => setWsConnected(false),
      (error) => console.error('WebSocket error:', error)
    );

    return () => wsService.disconnect();
  }, []);

  const handleNavigate = (path) => {
    setCurrentView(path);
  };

  return (
    <Box sx={{ display: 'flex', bgcolor: '#0d1b2a', minHeight: '100vh' }}>
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        currentView={currentView}
        onNavigate={handleNavigate}
      />
      <Box sx={{ flexGrow: 1, ml: sidebarOpen ? '280px' : 0, transition: 'margin-left 0.3s' }}>
        <Header
          onMenuClick={() => setSidebarOpen(!sidebarOpen)}
          wsConnected={wsConnected}
          notifications={notifications}
        />
        <Box
          component="main"
          sx={{
            pt: '64px',
            minHeight: 'calc(100vh - 64px)',
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/risk-management" element={<RiskManagement />} />
            {/* Add more routes as pages are created */}
          </Routes>
        </Box>
      </Box>
    </Box>
  );
};

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <AppContent />
        </Router>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
