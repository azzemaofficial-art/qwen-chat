"""
Data Fetcher - Recupero dati di mercato
Supporta Yahoo Finance per dati gratuiti
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class DataFetcher:
    """Classe per il recupero dei dati di mercato"""
    
    def __init__(self):
        self.cache = {}
    
    def get_stock_data(
        self, 
        symbol: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Recupera dati storici di un titolo
        
        Args:
            symbol: Simbolo del titolo (es. AAPL)
            period: Periodo storico (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            interval: Intervallo temporale (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            DataFrame con OHLCV data o None se errore
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"Nessun dato trovato per {symbol}")
                return None
            
            # Pulizia dati
            df = df.dropna()
            df.index = pd.to_datetime(df.index)
            
            print(f"Dati recuperati per {symbol}: {len(df)} righe")
            return df
            
        except Exception as e:
            print(f"Errore nel recupero dati per {symbol}: {str(e)}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Recupera il prezzo corrente di un titolo"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return data['Close'].iloc[-1]
            return None
        except Exception as e:
            print(f"Errore nel recupero prezzo: {str(e)}")
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Recupera informazioni fondamentali sul titolo"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info
        except Exception as e:
            print(f"Errore nel recupero info: {str(e)}")
            return None
    
    def get_multiple_timeframes(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Recupera dati su multipli timeframe per analisi completa
        
        Returns:
            Dict con dataframe per ogni timeframe
        """
        timeframes = {
            '1d': self.get_stock_data(symbol, period="5d", interval="1h"),
            '1w': self.get_stock_data(symbol, period="1mo", interval="1d"),
            '1m': self.get_stock_data(symbol, period="3mo", interval="1d"),
            '3m': self.get_stock_data(symbol, period="1y", interval="1d"),
            '1y': self.get_stock_data(symbol, period="2y", interval="1d")
        }
        
        # Rimuovi timeframes vuoti
        timeframes = {k: v for k, v in timeframes.items() if v is not None and not v.empty}
        
        return timeframes


if __name__ == "__main__":
    # Test
    fetcher = DataFetcher()
    df = fetcher.get_stock_data("AAPL", period="1mo")
    if df is not None:
        print(df.tail())
        print(f"\nPrezzo corrente: ${fetcher.get_current_price('AAPL')}")
