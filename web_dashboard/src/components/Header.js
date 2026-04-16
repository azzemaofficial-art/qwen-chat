import React from 'react';
import { AppBar, Toolbar, Typography, Box, IconButton, Badge, Chip } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import NotificationsIcon from '@mui/icons-material/Notifications';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import { motion } from 'framer-motion';

const Header = ({ onMenuClick, wsConnected, notifications, user }) => {
  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        bgcolor: '#1b263b',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          onClick={onMenuClick}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>
        
        <Typography variant="h6" fontWeight="bold" sx={{ flexGrow: 1 }}>
          Trading Advisor Pro v7.0
        </Typography>

        <Box display="flex" alignItems="center" gap={2}>
          {/* Connection Status */}
          <Chip
            icon={wsConnected ? <WifiIcon /> : <WifiOffIcon />}
            label={wsConnected ? 'Connected' : 'Disconnected'}
            size="small"
            sx={{
              bgcolor: wsConnected ? 'rgba(0, 230, 118, 0.2)' : 'rgba(255, 82, 82, 0.2)',
              color: wsConnected ? '#00e676' : '#ff5252',
              border: `1px solid ${wsConnected ? '#00e676' : '#ff5252'}`,
            }}
          />

          {/* Notifications */}
          <motion.div whileHover={{ scale: 1.1 }}>
            <IconButton color="inherit">
              <Badge badgeContent={notifications.length} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </motion.div>

          {/* User Profile */}
          <motion.div whileHover={{ scale: 1.05 }}>
            <IconButton color="inherit">
              <AccountCircleIcon />
            </IconButton>
          </motion.div>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
