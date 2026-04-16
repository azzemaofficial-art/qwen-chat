import { io } from 'socket.io-client';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = {};
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect(onConnect, onDisconnect, onError) {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      this.socket = io(WS_URL, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
      });

      this.socket.on('connect', () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        if (onConnect) onConnect();
      });

      this.socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        if (onDisconnect) onDisconnect(reason);
      });

      this.socket.on('error', (error) => {
        console.error('WebSocket error:', error);
        if (onError) onError(error);
      });

      this.socket.on('reconnect_attempt', (attemptNumber) => {
        console.log(`Reconnecting... Attempt ${attemptNumber}`);
      });

      this.socket.on('reconnect_error', (error) => {
        console.error('Reconnection error:', error);
      });

      // Market data events
      this.socket.on('price_update', (data) => {
        this.emit('price_update', data);
      });

      this.socket.on('signal_generated', (data) => {
        this.emit('signal_generated', data);
      });

      this.socket.on('trade_executed', (data) => {
        this.emit('trade_executed', data);
      });

      this.socket.on('portfolio_update', (data) => {
        this.emit('portfolio_update', data);
      });

      this.socket.on('ai_decision', (data) => {
        this.emit('ai_decision', data);
      });

      this.socket.on('defi_opportunity', (data) => {
        this.emit('defi_opportunity', data);
      });

      this.socket.on('alert', (data) => {
        this.emit('alert', data);
      });

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      if (onError) onError(error);
    }
  }

  subscribe(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);

    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  unsubscribe(event, callback) {
    if (callback) {
      this.listeners[event] = this.listeners[event]?.filter(cb => cb !== callback);
      if (this.socket) {
        this.socket.off(event, callback);
      }
    } else {
      delete this.listeners[event];
      if (this.socket) {
        this.socket.removeAllListeners(event);
      }
    }
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  send(event, data) {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected, message not sent:', event);
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.listeners = {};
    }
  }

  isConnected() {
    return this.socket?.connected || false;
  }
}

export const wsService = new WebSocketService();
export default wsService;
