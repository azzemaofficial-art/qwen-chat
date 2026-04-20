import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import SecurityIcon from '@mui/icons-material/Security';
import { motion } from 'framer-motion';

const MetricCard = ({ title, value, change, changePercent, icon: Icon, protectionMode = false }) => {
  const isPositive = change >= 0;
  
  return (
    <motion.div
      whileHover={{ scale: 1.03, y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Card 
        sx={{ 
          height: '100%',
          position: 'relative',
          overflow: 'visible',
          background: protectionMode 
            ? 'linear-gradient(135deg, rgba(0, 255, 157, 0.08) 0%, rgba(0, 212, 255, 0.05) 100%)'
            : 'linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
          border: protectionMode
            ? '1px solid rgba(0, 255, 157, 0.3)'
            : '1px solid rgba(255, 255, 255, 0.08)',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: -2,
            left: '10%',
            right: '10%',
            height: '2px',
            background: isPositive 
              ? 'linear-gradient(90deg, transparent, #00ff9d, transparent)'
              : 'linear-gradient(90deg, transparent, #ff2d55, transparent)',
            borderRadius: '2px',
          },
        }}
      >
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start">
            <Box>
              <Typography 
                variant="body2" 
                color="text.secondary" 
                gutterBottom
                sx={{ 
                  fontWeight: protectionMode ? 600 : 400,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  fontSize: '0.7rem',
                }}
              >
                {title}
              </Typography>
              <Typography 
                variant="h4" 
                fontWeight="bold" 
                color="primary"
                sx={{
                  textShadow: protectionMode ? '0 0 20px rgba(0, 245, 255, 0.3)' : 'none',
                  fontFamily: '"Inter", monospace',
                }}
              >
                {value}
              </Typography>
            </Box>
            {Icon && (
              <Box
                sx={{
                  p: 1.5,
                  borderRadius: 3,
                  bgcolor: isPositive 
                    ? 'rgba(0, 255, 157, 0.15)' 
                    : 'rgba(255, 45, 85, 0.15)',
                  boxShadow: protectionMode 
                    ? isPositive 
                      ? '0 0 20px rgba(0, 255, 157, 0.3)'
                      : '0 0 20px rgba(255, 45, 85, 0.3)'
                    : 'none',
                  position: 'relative',
                }}
              >
                {protectionMode && (
                  <SecurityIcon 
                    sx={{ 
                      position: 'absolute',
                      top: -8,
                      right: -8,
                      fontSize: 16,
                      color: '#00ff9d',
                    }} 
                  />
                )}
                <Icon sx={{ color: isPositive ? '#00e676' : '#ff5252', fontSize: 24 }} />
              </Box>
            )}
          </Box>
          {change !== undefined && (
            <Box display="flex" alignItems="center" mt={2}>
              {isPositive ? (
                <TrendingUpIcon sx={{ color: '#00e676', mr: 0.5 }} fontSize="small" />
              ) : (
                <TrendingDownIcon sx={{ color: '#ff5252', mr: 0.5 }} fontSize="small" />
              )}
              <Typography
                variant="body2"
                color={isPositive ? 'success.main' : 'error.main'}
                fontWeight="bold"
                sx={{
                  fontFamily: '"Inter", monospace',
                  textShadow: isPositive && protectionMode ? '0 0 10px rgba(0, 255, 157, 0.5)' : 'none',
                }}
              >
                {isPositive ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
              </Typography>
            </Box>
          )}
          {protectionMode && (
            <Box 
              mt={2} 
              pt={2} 
              borderTop="1px dashed rgba(0, 255, 157, 0.2)"
            >
              <Typography 
                variant="caption" 
                sx={{ 
                  color: '#00ff9d',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                }}
              >
                <SecurityIcon fontSize="small" />
                Protected by Capital Shield
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default MetricCard;
