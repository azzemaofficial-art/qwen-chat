import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Slider,
  Switch,
  FormControlLabel,
  Stack,
  Alert,
  AlertTitle,
  Button,
  LinearProgress,
} from '@mui/material';
import { motion } from 'framer-motion';
import SecurityIcon from '@mui/icons-material/Security';
import ShieldIcon from '@mui/icons-material/Shield';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';

const RiskManagement = () => {
  // Capital Protection Settings
  const [maxDailyLoss, setMaxDailyLoss] = useState(1.5);
  const [maxPositionSize, setMaxPositionSize] = useState(5);
  const [stopLossEnabled, setStopLossEnabled] = useState(true);
  const [trailingStopEnabled, setTrailingStopEnabled] = useState(true);
  const [correlationCheckEnabled, setCorrelationCheckEnabled] = useState(true);
  const [blackSwanProtection, setBlackSwanProtection] = useState(true);
  
  // Real-time metrics
  const [currentDailyPL, setCurrentDailyPL] = useState(2.3);
  const [totalExposure, setTotalExposure] = useState(45);
  const [riskScore, setRiskScore] = useState(23);
  const [activePositions, setActivePositions] = useState(8);
  
  // Risk levels
  const getRiskLevel = (score) => {
    if (score < 30) return { level: 'LOW', color: '#00ff9d' };
    if (score < 60) return { level: 'MEDIUM', color: '#ffb700' };
    return { level: 'HIGH', color: '#ff2d55' };
  };
  
  const riskInfo = getRiskLevel(riskScore);

  return (
    <Box p={3}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box mb={4}>
          <Typography variant="h3" fontWeight="bold" sx={{
            background: 'linear-gradient(135deg, #00f5ff 0%, #bd00ff 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            🛡️ Risk Management Command Center
          </Typography>
          <Typography variant="body1" color="text.secondary" mt={1}>
            Advanced Capital Protection System • Institutional-Grade Risk Control
          </Typography>
        </Box>
      </motion.div>

      {/* Critical Alert - Always Visible */}
      <Alert 
        severity="success" 
        sx={{ 
          mb: 3, 
          border: '1px solid #00ff9d', 
          bgcolor: 'rgba(0, 255, 157, 0.1)',
          '& .MuiAlert-icon': { color: '#00ff9d' }
        }}
        icon={<ShieldIcon />}
      >
        <AlertTitle sx={{ color: '#00ff9d', fontWeight: 'bold' }}>
          ✅ CAPITAL PROTECTION SYSTEM ACTIVE
        </AlertTitle>
        Your funds are protected by multi-layer risk management. Maximum daily loss limited to {maxDailyLoss}%.
        All positions have automatic stop-loss and trailing-stop protection.
      </Alert>

      {/* Real-time Risk Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            height: '100%',
            background: 'linear-gradient(135deg, rgba(0, 255, 157, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%)',
            border: '1px solid rgba(0, 255, 157, 0.3)',
          }}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <SecurityIcon sx={{ color: '#00ff9d', fontSize: 32 }} />
                <Typography variant="body2" color="text.secondary">
                  Risk Score
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" sx={{ color: riskInfo.color }}>
                {riskScore}/100
              </Typography>
              <Chip 
                label={`${riskInfo.level} RISK`}
                size="small"
                sx={{ 
                  mt: 1,
                  bgcolor: `${riskInfo.color}20`,
                  color: riskInfo.color,
                  border: `1px solid ${riskInfo.color}`,
                  fontWeight: 'bold',
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            height: '100%',
            background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 245, 255, 0.05) 100%)',
            border: '1px solid rgba(0, 212, 255, 0.3)',
          }}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <TrendingUpIcon sx={{ color: '#00d4ff', fontSize: 32 }} />
                <Typography variant="body2" color="text.secondary">
                  Daily P&L
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" sx={{ color: '#00d4ff' }}>
                +{currentDailyPL}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={(currentDailyPL + maxDailyLoss) / (maxDailyLoss * 2) * 100}
                sx={{ 
                  mt: 2, 
                  height: 6, 
                  borderRadius: 3,
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    background: `linear-gradient(90deg, #00ff9d, #00d4ff)`,
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary" mt={1} display="block">
                Max allowed: {maxDailyLoss}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            height: '100%',
            background: 'linear-gradient(135deg, rgba(189, 0, 255, 0.1) 0%, rgba(255, 0, 110, 0.05) 100%)',
            border: '1px solid rgba(189, 0, 255, 0.3)',
          }}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <AccountBalanceIcon sx={{ color: '#bd00ff', fontSize: 32 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Exposure
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" sx={{ color: '#bd00ff' }}>
                {totalExposure}%
              </Typography>
              <Typography variant="caption" color="text.secondary" mt={1} display="block">
                Across {activePositions} positions
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            height: '100%',
            background: 'linear-gradient(135deg, rgba(255, 183, 0, 0.1) 0%, rgba(255, 215, 0, 0.05) 100%)',
            border: '1px solid rgba(255, 183, 0, 0.3)',
          }}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <CheckCircleIcon sx={{ color: '#ffb700', fontSize: 32 }} />
                <Typography variant="body2" color="text.secondary">
                  Protection Layers
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" sx={{ color: '#ffb700' }}>
                6/6 ACTIVE
              </Typography>
              <Typography variant="caption" color="text.secondary" mt={1} display="block">
                All systems operational
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Protection Settings */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ 
            background: 'rgba(30, 41, 59, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={3} sx={{ color: '#00ff9d' }}>
                🔒 Loss Prevention Controls
              </Typography>
              
              <Stack spacing={4}>
                <Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="subtitle2">Max Daily Loss</Typography>
                    <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#00ff9d' }}>
                      {maxDailyLoss}%
                    </Typography>
                  </Box>
                  <Slider
                    value={maxDailyLoss}
                    onChange={(e, newValue) => setMaxDailyLoss(newValue)}
                    min={0.5}
                    max={5}
                    step={0.1}
                    sx={{
                      color: '#00ff9d',
                      '& .MuiSlider-thumb': {
                        backgroundColor: '#00ff9d',
                        boxShadow: '0 0 10px rgba(0, 255, 157, 0.5)',
                      },
                    }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Trading stops automatically when daily loss reaches this threshold
                  </Typography>
                </Box>

                <Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="subtitle2">Max Position Size</Typography>
                    <Typography variant="subtitle2" fontWeight="bold" sx={{ color: '#00d4ff' }}>
                      {maxPositionSize}%
                    </Typography>
                  </Box>
                  <Slider
                    value={maxPositionSize}
                    onChange={(e, newValue) => setMaxPositionSize(newValue)}
                    min={1}
                    max={20}
                    step={0.5}
                    sx={{
                      color: '#00d4ff',
                      '& .MuiSlider-thumb': {
                        backgroundColor: '#00d4ff',
                        boxShadow: '0 0 10px rgba(0, 212, 255, 0.5)',
                      },
                    }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Maximum capital allocation per single position
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ 
            background: 'rgba(30, 41, 59, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" mb={3} sx={{ color: '#bd00ff' }}>
                🛡️ Active Protection Systems
              </Typography>
              
              <Stack spacing={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={stopLossEnabled}
                      onChange={(e) => setStopLossEnabled(e.target.checked)}
                      sx={{
                        '& .MuiSwitch-switchBase.Mui-checked': {
                          color: '#00ff9d',
                        },
                        '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                          backgroundColor: '#00ff9d',
                        },
                      }}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="subtitle2" fontWeight="bold">
                        Automatic Stop-Loss
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Automatically closes positions at predefined loss levels
                      </Typography>
                    </Box>
                  }
                  sx={{ width: '100%' }}
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={trailingStopEnabled}
                      onChange={(e) => setTrailingStopEnabled(e.target.checked)}
                      sx={{
                        '& .MuiSwitch-switchBase.Mui-checked': {
                          color: '#00d4ff',
                        },
                        '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                          backgroundColor: '#00d4ff',
                        },
                      }}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="subtitle2" fontWeight="bold">
                        Trailing Stop
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Locks in profits by following price movements
                      </Typography>
                    </Box>
                  }
                  sx={{ width: '100%' }}
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={correlationCheckEnabled}
                      onChange={(e) => setCorrelationCheckEnabled(e.target.checked)}
                      sx={{
                        '& .MuiSwitch-switchBase.Mui-checked': {
                          color: '#bd00ff',
                        },
                        '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                          backgroundColor: '#bd00ff',
                        },
                      }}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="subtitle2" fontWeight="bold">
                        Correlation Check
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Prevents overexposure to correlated assets
                      </Typography>
                    </Box>
                  }
                  sx={{ width: '100%' }}
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={blackSwanProtection}
                      onChange={(e) => setBlackSwanProtection(e.target.checked)}
                      sx={{
                        '& .MuiSwitch-switchBase.Mui-checked': {
                          color: '#ffb700',
                        },
                        '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                          backgroundColor: '#ffb700',
                        },
                      }}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="subtitle2" fontWeight="bold">
                        Black Swan Protection
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Emergency shutdown during extreme market volatility
                      </Typography>
                    </Box>
                  }
                  sx={{ width: '100%' }}
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Safety Notice */}
      <Alert 
        severity="info" 
        sx={{ 
          mt: 3, 
          border: '1px solid #00d4ff', 
          bgcolor: 'rgba(0, 212, 255, 0.1)',
        }}
        icon={<WarningAmberIcon />}
      >
        <AlertTitle sx={{ fontWeight: 'bold' }}>
          ⚠️ IMPORTANT SAFETY NOTICE
        </AlertTitle>
        This is a SIMULATION for educational purposes. Even with advanced risk management, 
        real trading involves substantial risk of loss. Never trade with money you cannot 
        afford to lose. These protections help manage risk but cannot eliminate it entirely.
      </Alert>
    </Box>
  );
};

export default RiskManagement;
