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
  Chip,
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
import SecurityIcon from '@mui/icons-material/Security';
import ShieldIcon from '@mui/icons-material/Shield';

const drawerWidth = 280;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: 'dashboard' },
  { text: 'Markets', icon: <ShowChartIcon />, path: 'markets' },
  {
    text: 'Risk Management',
    icon: <ShieldIcon />,
    path: 'risk-management',
    highlight: true,
  },
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
          bgcolor: 'linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(3, 7, 18, 0.98) 100%)',
          background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(3, 7, 18, 0.98) 100%)',
          borderRight: '1px solid rgba(0, 245, 255, 0.1)',
        },
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="space-between" p={2}>
        <Box>
          <Typography 
            variant="h6" 
            fontWeight="bold" 
            sx={{
              background: 'linear-gradient(135deg, #00f5ff 0%, #bd00ff 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            QUANTUM TAP
          </Typography>
          <Chip 
            label="v7.0 PRO" 
            size="small" 
            sx={{ 
              mt: 0.5,
              bgcolor: 'rgba(0, 255, 157, 0.15)',
              color: '#00ff9d',
              border: '1px solid rgba(0, 255, 157, 0.3)',
              fontSize: '0.6rem',
              fontWeight: 'bold',
            }}
          />
        </Box>
        <IconButton onClick={onClose}>
          <ChevronLeftIcon sx={{ color: '#ffffff' }} />
        </IconButton>
      </Box>
      
      {/* Capital Protection Status */}
      <Box 
        px={2} 
        py={1.5} 
        mx={2} 
        mt={1}
        sx={{
          background: 'rgba(0, 255, 157, 0.08)',
          borderRadius: 2,
          border: '1px solid rgba(0, 255, 157, 0.2)',
        }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          <SecurityIcon sx={{ color: '#00ff9d', fontSize: 18 }} />
          <Typography variant="caption" fontWeight="bold" sx={{ color: '#00ff9d' }}>
            Capital Shield: ON
          </Typography>
        </Box>
      </Box>
      
      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.08)', my: 1 }} />
      <List>
        {menuItems.map((item) => (
          <React.Fragment key={item.text}>
            {item.subItems ? (
              <>
                <ListItem disablePadding>
                  <ListItemButton onClick={() => handleSubMenuClick(item.text)}>
                    <ListItemIcon sx={{ color: item.highlight ? '#00ff9d' : '#00bcd4', minWidth: 40 }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText 
                      primary={item.text} 
                      sx={{ ml: 1 }}
                      primaryTypographyProps={{
                        fontWeight: item.highlight ? 'bold' : 'regular',
                        color: item.highlight ? '#00ff9d' : 'inherit',
                      }}
                    />
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
                <ListItemButton 
                  onClick={() => onNavigate(item.path)}
                  sx={{
                    background: item.highlight && currentView === item.path 
                      ? 'rgba(0, 255, 157, 0.1)' 
                      : 'transparent',
                    borderLeft: item.highlight && currentView === item.path
                      ? '3px solid #00ff9d'
                      : '3px solid transparent',
                  }}
                >
                  <ListItemIcon sx={{ color: item.highlight ? '#00ff9d' : '#00bcd4', minWidth: 40 }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    sx={{
                      ml: 1,
                      color: currentView === item.path 
                        ? (item.highlight ? '#00ff9d' : '#00bcd4') 
                        : '#b0bec5',
                    }}
                    primaryTypographyProps={{
                      fontWeight: item.highlight ? 'bold' : 'regular',
                    }}
                  />
                  {item.highlight && (
                    <Chip 
                      label="PROTECTED" 
                      size="small" 
                      sx={{ 
                        ml: 1,
                        bgcolor: 'rgba(0, 255, 157, 0.15)',
                        color: '#00ff9d',
                        border: '1px solid rgba(0, 255, 157, 0.3)',
                        fontSize: '0.6rem',
                        fontWeight: 'bold',
                        height: 20,
                      }}
                    />
                  )}
                </ListItemButton>
              </ListItem>
            )}
          </React.Fragment>
        ))}
      </List>
      <Box sx={{ position: 'absolute', bottom: 0, width: '100%' }}>
        <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.08)' }} />
        <Box px={2} py={2}>
          <Box 
            sx={{
              background: 'rgba(189, 0, 255, 0.08)',
              borderRadius: 2,
              border: '1px solid rgba(189, 0, 255, 0.2)',
              p: 1.5,
            }}
          >
            <Typography variant="caption" fontWeight="bold" sx={{ color: '#bd00ff' }} display="block">
              ⚡ Quantum AI Edition
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              v7.0.0 - Institutional Grade
            </Typography>
          </Box>
        </Box>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
