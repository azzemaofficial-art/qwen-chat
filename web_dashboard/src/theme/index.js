import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00f5ff',
      light: '#7afbff',
      dark: '#00c4cc',
      contrastText: '#0d1b2a',
    },
    secondary: {
      main: '#ff006e',
      light: '#ff4d94',
      dark: '#cc0058',
      contrastText: '#ffffff',
    },
    success: {
      main: '#00ff9d',
      light: '#5affbf',
      dark: '#00cc7e',
    },
    error: {
      main: '#ff2d55',
      light: '#ff6b88',
      dark: '#cc2444',
    },
    warning: {
      main: '#ffb700',
      light: '#ffd04d',
      dark: '#cc9200',
    },
    info: {
      main: '#00d4ff',
      light: '#4de5ff',
      dark: '#00aacc',
    },
    purple: {
      main: '#bd00ff',
      light: '#d64dff',
      dark: '#9700cc',
    },
    background: {
      default: '#030712',
      paper: '#0f172a',
      card: 'rgba(30, 41, 59, 0.7)',
      glass: 'rgba(255, 255, 255, 0.03)',
    },
    text: {
      primary: '#f8fafc',
      secondary: '#94a3b8',
      muted: '#64748b',
    },
    border: {
      light: 'rgba(255, 255, 255, 0.08)',
      medium: 'rgba(255, 255, 255, 0.12)',
      strong: 'rgba(255, 255, 255, 0.2)',
    },
    gradient: {
      primary: 'linear-gradient(135deg, #00f5ff 0%, #bd00ff 100%)',
      success: 'linear-gradient(135deg, #00ff9d 0%, #00d4ff 100%)',
      danger: 'linear-gradient(135deg, #ff2d55 0%, #ff006e 100%)',
      gold: 'linear-gradient(135deg, #ffd700 0%, #ffb700 100%)',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    fontWeightLight: 300,
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    fontWeightBold: 700,
    h1: {
      fontSize: '3rem',
      fontWeight: 800,
      letterSpacing: '-0.02em',
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '2rem',
      fontWeight: 700,
      letterSpacing: '-0.01em',
      lineHeight: 1.3,
    },
    h4: {
      fontSize: '1.75rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.5rem',
      fontWeight: 600,
      letterSpacing: '0',
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1.25rem',
      fontWeight: 600,
      letterSpacing: '0.01em',
      lineHeight: 1.5,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      letterSpacing: '0.01em',
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 600,
      letterSpacing: '0.02em',
      textTransform: 'uppercase',
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
    },
    button: {
      fontWeight: 600,
      letterSpacing: '0.02em',
      textTransform: 'none',
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 500,
      letterSpacing: '0.03em',
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 700,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
    },
  },
  shape: {
    borderRadius: 16,
    borderRadiusSm: 8,
    borderRadiusLg: 24,
  },
  shadows: [
    'none',
    '0 1px 2px rgba(0, 0, 0, 0.3)',
    '0 2px 4px rgba(0, 0, 0, 0.3)',
    '0 4px 8px rgba(0, 0, 0, 0.3)',
    '0 8px 16px rgba(0, 0, 0, 0.3)',
    '0 12px 24px rgba(0, 0, 0, 0.35)',
    '0 16px 32px rgba(0, 0, 0, 0.35)',
    '0 20px 40px rgba(0, 0, 0, 0.4)',
    '0 24px 48px rgba(0, 0, 0, 0.4)',
    '0 32px 64px rgba(0, 0, 0, 0.45)',
    '0 40px 80px rgba(0, 0, 0, 0.45)',
    '0 48px 96px rgba(0, 0, 0, 0.5)',
    '0 56px 112px rgba(0, 0, 0, 0.5)',
    '0 64px 128px rgba(0, 0, 0, 0.5)',
    '0 72px 144px rgba(0, 0, 0, 0.55)',
    '0 80px 160px rgba(0, 0, 0, 0.55)',
    '0 0 0 1px rgba(255, 255, 255, 0.08), 0 8px 32px rgba(0, 0, 0, 0.4)',
    '0 0 0 1px rgba(0, 245, 255, 0.2), 0 0 20px rgba(0, 245, 255, 0.3), 0 8px 32px rgba(0, 0, 0, 0.4)',
    '0 0 0 1px rgba(189, 0, 255, 0.2), 0 0 20px rgba(189, 0, 255, 0.3), 0 8px 32px rgba(0, 0, 0, 0.4)',
    '0 0 0 1px rgba(0, 255, 157, 0.2), 0 0 20px rgba(0, 255, 157, 0.3), 0 8px 32px rgba(0, 0, 0, 0.4)',
    '0 0 0 1px rgba(255, 45, 85, 0.2), 0 0 20px rgba(255, 45, 85, 0.3), 0 8px 32px rgba(0, 0, 0, 0.4)',
    '0 0 0 1px rgba(255, 215, 0, 0.2), 0 0 30px rgba(255, 215, 0, 0.4), 0 12px 48px rgba(0, 0, 0, 0.5)',
    'inset 0 0 0 1px rgba(255, 255, 255, 0.1), 0 8px 32px rgba(0, 0, 0, 0.4)',
    'inset 0 2px 4px rgba(255, 255, 255, 0.05), 0 8px 32px rgba(0, 0, 0, 0.4)',
    '0 0 40px rgba(0, 245, 255, 0.15), 0 0 80px rgba(189, 0, 255, 0.1)',
  ],
  components: {
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 12,
          fontWeight: 600,
          letterSpacing: '0.02em',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
          },
        },
        contained: {
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.3)',
          '&:hover': {
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.4)',
          },
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #00f5ff 0%, #00d4ff 100%)',
          color: '#0d1b2a',
        },
        containedSecondary: {
          background: 'linear-gradient(135deg, #ff006e 0%, #ff2d55 100%)',
        },
        outlined: {
          borderWidth: '1.5px',
          '&:hover': {
            borderWidth: '1.5px',
          },
        },
      },
    },
    MuiCard: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          borderRadius: 20,
          backgroundImage: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
          overflow: 'hidden',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '1px',
            background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
        },
        elevation1: {
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.35)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          borderRadius: 8,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            transition: 'all 0.2s ease',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
            },
            '&.Mui-focused': {
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              boxShadow: '0 0 0 2px rgba(0, 245, 255, 0.2)',
            },
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          padding: '16px 24px',
        },
        head: {
          fontWeight: 700,
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          fontSize: '0.75rem',
          color: '#94a3b8',
          backgroundColor: 'rgba(255, 255, 255, 0.02)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundImage: 'linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(3, 7, 18, 0.98) 100%)',
          backdropFilter: 'blur(20px)',
          borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(3, 7, 18, 0.95) 100%)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          height: 6,
        },
        bar: {
          borderRadius: 4,
        },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
    MuiBadge: {
      styleOverrides: {
        badge: {
          fontWeight: 700,
          fontSize: '0.7rem',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.98)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 10,
          padding: '10px 14px',
          fontSize: '0.875rem',
          fontWeight: 500,
        },
        arrow: {
          color: 'rgba(15, 23, 42, 0.98)',
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        root: {
          width: 48,
          height: 28,
          padding: 0,
        },
        switchBase: {
          padding: 6,
          '&.Mui-checked': {
            transform: 'translateX(20px)',
          },
        },
        thumb: {
          width: 16,
          height: 16,
        },
        track: {
          borderRadius: 14,
          opacity: 0.7,
        },
      },
    },
    MuiSlider: {
      styleOverrides: {
        root: {
          height: 6,
          borderRadius: 3,
        },
        thumb: {
          width: 18,
          height: 18,
          border: '3px solid currentColor',
          '&:hover': {
            boxShadow: '0 0 0 8px rgba(0, 245, 255, 0.16)',
          },
        },
        track: {
          border: 'none',
        },
        rail: {
          opacity: 0.3,
          height: 6,
        },
        markLabel: {
          fontSize: '0.75rem',
          color: '#64748b',
        },
      },
    },
    MuiListSubheader: {
      styleOverrides: {
        root: {
          fontWeight: 700,
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          fontSize: '0.7rem',
          color: '#64748b',
        },
      },
    },
  },
});

export default theme;
