import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Box,
  IconButton,
  Typography,
  Collapse,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import PsychologyIcon from '@mui/icons-material/Psychology';
import DnsIcon from '@mui/icons-material/Dns';
import SettingsIcon from '@mui/icons-material/Settings';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import BitcoinIcon from '@mui/icons-material/Bitcoin';
import StorageIcon from '@mui/icons-material/Storage';

const drawerWidth = 260;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: 'dashboard' },
  { text: 'Markets', icon: <ShowChartIcon />, path: 'markets' },
  {
    text: 'Portfolio',
    icon: <AccountBalanceWalletIcon />,
    path: 'portfolio',
    subItems: [
      { text: 'Overview', path: 'portfolio-overview' },
      { text: 'Positions', path: 'portfolio-positions' },
      { text: 'Performance', path: 'portfolio-performance' },
    ],
  },
  {
    text: 'AI Agents',
    icon: <PsychologyIcon />,
    path: 'ai-agents',
    subItems: [
      { text: 'Agents Status', path: 'ai-status' },
      { text: 'Signals', path: 'ai-signals' },
      { text: 'Consensus', path: 'ai-consensus' },
    ],
  },
  {
    text: 'DeFi',
    icon: <BitcoinIcon />,
    path: 'defi',
    subItems: [
      { text: 'Protocols', path: 'defi-protocols' },
      { text: 'Yield Farming', path: 'defi-yield' },
      { text: 'Arbitrage', path: 'defi-arbitrage' },
    ],
  },
  { text: 'Alternative Data', icon: <DnsIcon />, path: 'alt-data' },
  { text: 'Settings', icon: <SettingsIcon />, path: 'settings' },
];

const Sidebar = ({ open, onClose, currentView, onNavigate }) => {
  const theme = useTheme();
  const [expandedMenu, setExpandedMenu] = useState(null);

  const handleSubMenuClick = (menu) => {
    setExpandedMenu(expandedMenu === menu ? null : menu);
  };

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: open ? drawerWidth : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          bgcolor: '#1b263b',
          borderRight: '1px solid rgba(255, 255, 255, 0.1)',
        },
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" p={2}>
        <Typography variant="h6" fontWeight="bold" color="primary">
          TAP v7.0
        </Typography>
        <IconButton onClick={onClose}>
          <ChevronLeftIcon sx={{ color: '#ffffff' }} />
        </IconButton>
      </Box>
      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />
      <List>
        {menuItems.map((item) => (
          <React.Fragment key={item.text}>
            {item.subItems ? (
              <>
                <ListItem disablePadding>
                  <ListItemButton onClick={() => handleSubMenuClick(item.text)}>
                    <ListItemIcon sx={{ color: '#00bcd4', minWidth: 40 }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText primary={item.text} sx={{ ml: 1 }} />
                    {expandedMenu === item.text ? (
                      <ExpandLessIcon sx={{ color: '#b0bec5' }} />
                    ) : (
                      <ExpandMoreIcon sx={{ color: '#b0bec5' }} />
                    )}
                  </ListItemButton>
                </ListItem>
                <Collapse in={expandedMenu === item.text} timeout="auto" unmountOnExit>
                  <List component="div" disablePadding>
                    {item.subItems.map((subItem) => (
                      <ListItemButton
                        key={subItem.path}
                        sx={{ pl: 6 }}
                        onClick={() => onNavigate(subItem.path)}
                      >
                        <ListItemText
                          primary={subItem.text}
                          sx={{
                            color: currentView === subItem.path ? '#00bcd4' : '#b0bec5',
                          }}
                        />
                      </ListItemButton>
                    ))}
                  </List>
                </Collapse>
              </>
            ) : (
              <ListItem disablePadding>
                <ListItemButton onClick={() => onNavigate(item.path)}>
                  <ListItemIcon sx={{ color: '#00bcd4', minWidth: 40 }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    sx={{
                      ml: 1,
                      color: currentView === item.path ? '#00bcd4' : '#b0bec5',
                    }}
                  />
                </ListItemButton>
              </ListItem>
            )}
          </React.Fragment>
        ))}
      </List>
      <Box sx={{ position: 'absolute', bottom: 0, width: '100%' }}>
        <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />
        <ListItem>
          <ListItemText
            primary="Quantum AI Edition"
            secondary="v7.0.0"
            sx={{ textAlign: 'center' }}
          />
        </ListItem>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
