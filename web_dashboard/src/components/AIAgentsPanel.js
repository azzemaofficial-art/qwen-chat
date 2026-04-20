import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Stack,
  Card,
  CardContent,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import SecurityIcon from '@mui/icons-material/Security';
import ShowChartIcon from '@mui/icons-material/ShowChart';

const AIAgentsPanel = ({ agents }) => {
  const [activeAgent, setActiveAgent] = useState(null);

  const defaultAgents = [
    {
      id: 1,
      name: 'Quantum Predictor',
      type: 'Deep Learning',
      status: 'active',
      confidence: 94.5,
      accuracy: 87.3,
      signalsToday: 23,
      profitLoss: +12450,
      specialty: 'Price Prediction',
      model: 'Transformer-XL',
    },
    {
      id: 2,
      name: 'Sentiment Analyzer',
      type: 'NLP Engine',
      status: 'active',
      confidence: 89.2,
      accuracy: 82.1,
      signalsToday: 45,
      profitLoss: +8320,
      specialty: 'Market Sentiment',
      model: 'BERT-Finance',
    },
    {
      id: 3,
      name: 'Arbitrage Hunter',
      type: 'Real-time Scanner',
      status: 'active',
      confidence: 96.8,
      accuracy: 91.5,
      signalsToday: 12,
      profitLoss: +18900,
      specialty: 'Cross-Exchange Arbitrage',
      model: 'Reinforcement Learning',
    },
    {
      id: 4,
      name: 'Risk Guardian',
      type: 'Risk Management',
      status: 'monitoring',
      confidence: 98.1,
      accuracy: 95.2,
      signalsToday: 8,
      profitLoss: +5600,
      specialty: 'Portfolio Protection',
      model: 'Monte Carlo + VaR',
    },
    {
      id: 5,
      name: 'DeFi Yield Optimizer',
      type: 'Yield Strategy',
      status: 'active',
      confidence: 91.3,
      accuracy: 84.7,
      signalsToday: 15,
      profitLoss: +22100,
      specialty: 'Yield Farming',
      model: 'Multi-Chain Analyzer',
    },
  ];

  const agentList = agents || defaultAgents;

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return '#00ff9d';
      case 'monitoring':
        return '#ffb700';
      case 'inactive':
        return '#ff2d55';
      default:
        return '#94a3b8';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 90) return '#00ff9d';
    if (confidence >= 80) return '#00d4ff';
    if (confidence >= 70) return '#ffb700';
    return '#ff2d55';
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box display="flex" alignItems="center" gap={2}>
            <Box
              sx={{
                p: 1.5,
                borderRadius: 3,
                background: 'linear-gradient(135deg, #00f5ff 0%, #bd00ff 100%)',
                display: 'flex',
              }}
            >
              <PsychologyIcon sx={{ color: '#0d1b2a', fontSize: 28 }} />
            </Box>
            <Box>
              <Typography variant="h5" fontWeight="bold">
                AI Agents Command Center
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {agentList.filter(a => a.status === 'active').length} active agents •{' '}
                {agentList.reduce((acc, a) => acc + a.signalsToday, 0)} signals today
              </Typography>
            </Box>
          </Box>
          <Chip
            label="Consensus: 92.4%"
            sx={{
              background: 'linear-gradient(135deg, #00ff9d 0%, #00d4ff 100%)',
              color: '#0d1b2a',
              fontWeight: 'bold',
              px: 2,
              py: 2.5,
            }}
          />
        </Box>

        <Stack spacing={2}>
          {agentList.map((agent, index) => (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Box
                onClick={() => setActiveAgent(activeAgent === agent.id ? null : agent.id)}
                sx={{
                  p: 2.5,
                  borderRadius: 3,
                  background: activeAgent === agent.id
                    ? 'rgba(0, 245, 255, 0.08)'
                    : 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid',
                  borderColor: activeAgent === agent.id
                    ? 'rgba(0, 245, 255, 0.3)'
                    : 'rgba(255, 255, 255, 0.06)',
                  cursor: 'pointer',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&:hover': {
                    borderColor: 'rgba(0, 245, 255, 0.2)',
                    background: 'rgba(0, 245, 255, 0.05)',
                    transform: 'translateX(4px)',
                  },
                }}
              >
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box display="flex" alignItems="center" gap={2.5} flex={1}>
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        borderRadius: 3,
                        background: `linear-gradient(135deg, ${getStatusColor(agent.status)}20, ${getStatusColor(agent.status)}10)`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        position: 'relative',
                      }}
                    >
                      {agent.type.includes('Deep Learning') && <AutoAwesomeIcon sx={{ color: getStatusColor(agent.status) }} />}
                      {agent.type.includes('NLP') && <PsychologyIcon sx={{ color: getStatusColor(agent.status) }} />}
                      {agent.type.includes('Scanner') && <ShowChartIcon sx={{ color: getStatusColor(agent.status) }} />}
                      {agent.type.includes('Risk') && <SecurityIcon sx={{ color: getStatusColor(agent.status) }} />}
                      {!agent.type.includes('Deep Learning') && !agent.type.includes('NLP') && !agent.type.includes('Scanner') && !agent.type.includes('Risk') && (
                        <AutoAwesomeIcon sx={{ color: getStatusColor(agent.status) }} />
                      )}
                      <Box
                        sx={{
                          position: 'absolute',
                          bottom: -2,
                          right: -2,
                          width: 12,
                          height: 12,
                          borderRadius: '50%',
                          bgcolor: getStatusColor(agent.status),
                          border: '2px solid',
                          borderColor: '#0f172a',
                        }}
                      />
                    </Box>

                    <Box flex={1}>
                      <Box display="flex" alignItems="center" gap={1.5} mb={0.5}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {agent.name}
                        </Typography>
                        <Chip
                          label={agent.type}
                          size="small"
                          sx={{
                            bgcolor: 'rgba(255, 255, 255, 0.08)',
                            color: '#94a3b8',
                            fontSize: '0.65rem',
                            fontWeight: 600,
                            height: 20,
                          }}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary" mb={1}>
                        {agent.specialty} • {agent.model}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={3}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <LinearProgress
                            variant="determinate"
                            value={agent.confidence}
                            sx={{
                              width: 100,
                              height: 6,
                              borderRadius: 3,
                              bgcolor: 'rgba(255, 255, 255, 0.1)',
                              '& .MuiLinearProgress-bar': {
                                borderRadius: 3,
                                background: `linear-gradient(90deg, ${getConfidenceColor(agent.confidence)}, ${getConfidenceColor(agent.confidence)}aa)`,
                              },
                            }}
                          />
                          <Typography
                            variant="caption"
                            fontWeight="bold"
                            sx={{ color: getConfidenceColor(agent.confidence), minWidth: 45 }}
                          >
                            {agent.confidence}%
                          </Typography>
                        </Box>
                        <Typography
                          variant="caption"
                          fontWeight="bold"
                          color={agent.profitLoss >= 0 ? '#00ff9d' : '#ff2d55'}
                        >
                          {agent.profitLoss >= 0 ? '+' : ''}${agent.profitLoss.toLocaleString()}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>

                  <Box display="flex" alignItems="center" gap={2}>
                    <Box textAlign="right">
                      <Typography variant="body2" color="text.secondary" fontSize="0.7rem">
                        Signals
                      </Typography>
                      <Typography variant="h6" fontWeight="bold" color="primary">
                        {agent.signalsToday}
                      </Typography>
                    </Box>
                    <Box textAlign="right">
                      <Typography variant="body2" color="text.secondary" fontSize="0.7rem">
                        Accuracy
                      </Typography>
                      <Typography
                        variant="h6"
                        fontWeight="bold"
                        sx={{ color: getConfidenceColor(agent.accuracy) }}
                      >
                        {agent.accuracy}%
                      </Typography>
                    </Box>
                    <Tooltip title={agent.status === 'active' ? 'Active & Trading' : 'Monitoring Only'}>
                      <IconButton
                        size="small"
                        sx={{
                          color: getStatusColor(agent.status),
                          '&:hover': {
                            bgcolor: `${getStatusColor(agent.status)}20`,
                          },
                        }}
                      >
                        {agent.status === 'active' ? <TrendingUpIcon /> : <ShowChartIcon />}
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                <AnimatePresence>
                  {activeAgent === agent.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Box
                        mt={2}
                        pt={2}
                        borderTop="1px solid rgba(255, 255, 255, 0.06)"
                        display="grid"
                        gridTemplateColumns="repeat(4, 1fr)"
                        gap={2}
                      >
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Win Rate
                          </Typography>
                          <Typography variant="h6" fontWeight="bold" color="#00ff9d">
                            {(agent.accuracy + 2).toFixed(1)}%
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Avg Return
                          </Typography>
                          <Typography variant="h6" fontWeight="bold" color="#00d4ff">
                            +{(Math.random() * 5 + 2).toFixed(2)}%
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Total Trades
                          </Typography>
                          <Typography variant="h6" fontWeight="bold" color="#f8fafc">
                            {Math.floor(Math.random() * 500 + 100)}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Sharpe Ratio
                          </Typography>
                          <Typography variant="h6" fontWeight="bold" color="#bd00ff">
                            {(Math.random() * 2 + 1).toFixed(2)}
                          </Typography>
                        </Box>
                      </Box>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Box>
            </motion.div>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};

export default AIAgentsPanel;
