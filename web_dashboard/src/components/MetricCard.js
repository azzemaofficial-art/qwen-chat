import React from 'react';
import { Card, CardContent, Typography, Box, Grid } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import { motion } from 'framer-motion';

const MetricCard = ({ title, value, change, changePercent, icon: Icon }) => {
  const isPositive = change >= 0;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start">
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {title}
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {value}
              </Typography>
            </Box>
            {Icon && (
              <Box
                sx={{
                  p: 1,
                  borderRadius: 2,
                  bgcolor: isPositive ? 'success.dark' : 'error.dark',
                }}
              >
                <Icon sx={{ color: isPositive ? '#00e676' : '#ff5252' }} />
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
              >
                {isPositive ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default MetricCard;
