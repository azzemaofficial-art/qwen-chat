import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Box,
  Typography,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import InfoIcon from '@mui/icons-material/Info';

const SignalTable = ({ signals, onExecute }) => {
  const getActionColor = (action) => {
    switch (action) {
      case 'BUY':
        return '#00e676';
      case 'SELL':
        return '#ff5252';
      case 'HOLD':
        return '#ffc400';
      default:
        return '#b0bec5';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return '#00e676';
    if (confidence >= 60) return '#ffc400';
    return '#ff5252';
  };

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Action</TableCell>
            <TableCell>Price</TableCell>
            <TableCell>Target</TableCell>
            <TableCell>Stop Loss</TableCell>
            <TableCell>Confidence</TableCell>
            <TableCell>AI Agent</TableCell>
            <TableCell>Time</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {signals.map((signal) => (
            <TableRow key={signal.id} hover>
              <TableCell>
                <Typography fontWeight="bold">{signal.symbol}</Typography>
              </TableCell>
              <TableCell>
                <Chip
                  label={signal.action}
                  sx={{
                    bgcolor: getActionColor(signal.action),
                    color: '#000',
                    fontWeight: 'bold',
                  }}
                  size="small"
                />
              </TableCell>
              <TableCell>${signal.price?.toFixed(2)}</TableCell>
              <TableCell>${signal.targetPrice?.toFixed(2)}</TableCell>
              <TableCell>${signal.stopLoss?.toFixed(2)}</TableCell>
              <TableCell>
                <Chip
                  label={`${signal.confidence}%`}
                  sx={{
                    bgcolor: getConfidenceColor(signal.confidence),
                    color: '#000',
                    fontWeight: 'bold',
                  }}
                  size="small"
                />
              </TableCell>
              <TableCell>{signal.agent}</TableCell>
              <TableCell>{new Date(signal.timestamp).toLocaleTimeString()}</TableCell>
              <TableCell align="right">
                <IconButton
                  size="small"
                  onClick={() => onExecute(signal)}
                  color="success"
                >
                  <PlayArrowIcon />
                </IconButton>
                <IconButton size="small" color="info">
                  <InfoIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
          {signals.length === 0 && (
            <TableRow>
              <TableCell colSpan={9} align="center">
                <Typography color="text.secondary" py={3}>
                  No active signals
                </Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default SignalTable;
