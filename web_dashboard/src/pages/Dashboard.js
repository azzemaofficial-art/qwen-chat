import React, { useEffect, useState } from 'react';
import { Grid, Box, Typography, CircularProgress } from '@mui/material';
import { useSelector, useDispatch } from 'react-redux';
import MetricCard from '../components/MetricCard';
import PriceChart from '../components/PriceChart';
import AllocationChart from '../components/AllocationChart';
import SignalTable from '../components/SignalTable';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import PsychologyIcon from '@mui/icons-material/Psychology';
import { portfolioApi, signalsApi } from '../services/api';
import { setPortfolio, updateRealTimeData } from '../store/slices/portfolioSlice';
import { setActiveSignals } from '../store/slices/tradingSignalsSlice';
import wsService from '../services/websocket';

const Dashboard = () => {
  const dispatch = useDispatch();
  const portfolio = useSelector((state) => state.portfolio);
  const signals = useSelector((state) => state.tradingSignals.activeSignals);
  const [loading, setLoading] = useState(true);
  const [priceHistory, setPriceHistory] = useState([]);

  useEffect(() => {
    // Load initial data
    const loadData = async () => {
      try {
        const [portfolioData, signalsData] = await Promise.all([
          portfolioApi.getPortfolio(),
          signalsApi.getActiveSignals(),
        ]);
        
        dispatch(setPortfolio(portfolioData.data));
        dispatch(setActiveSignals(signalsData.data));
        
        // Generate mock price history for demo
        const mockHistory = Array.from({ length: 50 }, (_, i) => ({
          timestamp: new Date(Date.now() - (50 - i) * 60000).toISOString(),
          price: 45000 + Math.random() * 1000,
        }));
        setPriceHistory(mockHistory);
        
        setLoading(false);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
        setLoading(false);
      }
    };

    loadData();

    // Connect WebSocket for real-time updates
    wsService.connect(
      () => console.log('Connected to WebSocket'),
      () => console.log('Disconnected from WebSocket'),
      (error) => console.error('WebSocket error:', error)
    );

    // Subscribe to real-time updates
    wsService.subscribe('price_update', (data) => {
      dispatch(updateRealTimeData(data));
    });

    wsService.subscribe('signal_generated', (data) => {
      dispatch(setActiveSignals(prev => [data, ...prev]));
    });

    return () => {
      wsService.disconnect();
    };
  }, [dispatch]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress color="primary" />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight="bold" mb={3}>
        Dashboard Overview
      </Typography>

      {/* Key Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Portfolio Value"
            value={`$${portfolio.totalValue.toLocaleString()}`}
            change={portfolio.dayChange}
            changePercent={portfolio.dayChangePercent}
            icon={AccountBalanceWalletIcon}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Return"
            value={`${portfolio.totalReturnPercent.toFixed(2)}%`}
            change={portfolio.totalReturn}
            changePercent={portfolio.totalReturnPercent}
            icon={TrendingUpIcon}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="AI Confidence"
            value={`${signals.length > 0 ? '87' : '0'}%`}
            change={5}
            changePercent={6.1}
            icon={PsychologyIcon}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Signals"
            value={signals.length.toString()}
            change={signals.length}
            changePercent={signals.length > 0 ? 100 : 0}
            icon={PsychologyIcon}
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={8}>
          <Box p={2} bgcolor="#1b263b" borderRadius={2}>
            <Typography variant="h6" mb={2}>Price Chart (BTC/USD)</Typography>
            <PriceChart data={priceHistory} symbol="BTC" timeframe="1H" />
          </Box>
        </Grid>
        <Grid item xs={12} md={4}>
          <Box p={2} bgcolor="#1b263b" borderRadius={2}>
            <Typography variant="h6" mb={2}>Asset Allocation</Typography>
            <AllocationChart allocation={portfolio.allocation} />
          </Box>
        </Grid>
      </Grid>

      {/* Active Signals */}
      <Box p={2} bgcolor="#1b263b" borderRadius={2}>
        <Typography variant="h6" mb={2}>Active Trading Signals</Typography>
        <SignalTable 
          signals={signals} 
          onExecute={(signal) => console.log('Execute signal:', signal)} 
        />
      </Box>
    </Box>
  );
};

export default Dashboard;
