"""
Technical Analysis - Analisi tecnica avanzata
Include indicatori, pattern recognition e segnali
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class Signal(Enum):
    STRONG_BUY = "FORTE_ACQUISTO"
    BUY = "ACQUISTO"
    NEUTRAL = "NEUTRALE"
    SELL = "VENDITA"
    STRONG_SELL = "FORTE_VENDITA"


@dataclass
class TechnicalIndicator:
    """Rappresenta un indicatore tecnico con il suo segnale"""
    name: str
    value: float
    signal: Signal
    description: str


class TechnicalAnalyzer:
    """Analizzatore tecnico per identificare opportunità di trading"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: DataFrame con dati OHLCV (Open, High, Low, Close, Volume)
        """
        self.df = df.copy()
        self.signals = []
        self.indicators = {}
        
        if not self._validate_data():
            raise ValueError("Dati non validi per l'analisi tecnica")
    
    def _validate_data(self) -> bool:
        """Valida che il DataFrame contenga i dati necessari"""
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        return all(col in self.df.columns for col in required_cols) and len(self.df) >= 50
    
    # === Indicatori di Trend ===
    
    def calculate_sma(self, period: int = 20) -> pd.Series:
        """Simple Moving Average"""
        sma = self.df['Close'].rolling(window=period).mean()
        self.indicators[f'SMA_{period}'] = sma
        return sma
    
    def calculate_ema(self, period: int = 20) -> pd.Series:
        """Exponential Moving Average"""
        ema = self.df['Close'].ewm(span=period, adjust=False).mean()
        self.indicators[f'EMA_{period}'] = ema
        return ema
    
    def calculate_macd(
        self, 
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)
        
        Returns:
            Dict con MACD line, Signal line e Histogram
        """
        ema_fast = self.df['Close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = self.df['Close'].ewm(span=slow_period, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        result = {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
        
        self.indicators['MACD'] = result
        return result
    
    def calculate_adx(self, period: int = 14) -> pd.Series:
        """Average Directional Index - misura la forza del trend"""
        high = self.df['High']
        low = self.df['Low']
        close = self.df['Close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        self.indicators['ADX'] = adx
        return adx
    
    # === Indicatori di Momentum ===
    
    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        self.indicators['RSI'] = rsi
        return rsi
    
    def calculate_stochastic(
        self, 
        k_period: int = 14, 
        d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        low_min = self.df['Low'].rolling(window=k_period).min()
        high_max = self.df['High'].rolling(window=k_period).max()
        
        k = 100 * (self.df['Close'] - low_min) / (high_max - low_min)
        d = k.rolling(window=d_period).mean()
        
        result = {'k': k, 'd': d}
        self.indicators['Stochastic'] = result
        return result
    
    def calculate_cci(self, period: int = 20) -> pd.Series:
        """Commodity Channel Index"""
        tp = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        cci = (tp - sma_tp) / (0.015 * mad)
        self.indicators['CCI'] = cci
        return cci
    
    # === Indicatori di Volatilità ===
    
    def calculate_bollinger_bands(
        self, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = self.df['Close'].rolling(window=period).mean()
        std = self.df['Close'].rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        result = {
            'upper': upper,
            'middle': sma,
            'lower': lower,
            'bandwidth': (upper - lower) / sma * 100
        }
        
        self.indicators['Bollinger'] = result
        return result
    
    def calculate_atr(self, period: int = 14) -> pd.Series:
        """Average True Range - misura la volatilità"""
        high = self.df['High']
        low = self.df['Low']
        close = self.df['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        self.indicators['ATR'] = atr
        return atr
    
    # === Volumi ===
    
    def calculate_obv(self) -> pd.Series:
        """On-Balance Volume"""
        obv = (np.sign(self.df['Close'].diff()) * self.df['Volume']).fillna(0).cumsum()
        self.indicators['OBV'] = obv
        return obv
    
    def calculate_volume_sma(self, period: int = 20) -> pd.Series:
        """Volume Simple Moving Average"""
        vol_sma = self.df['Volume'].rolling(window=period).mean()
        self.indicators['Volume_SMA'] = vol_sma
        return vol_sma
    
    # === Analisi completa ===
    
    def calculate_all_indicators(self):
        """Calcola tutti gli indicatori principali"""
        print("Calcolo indicatori tecnici...")
        
        # Trend
        self.calculate_sma(20)
        self.calculate_sma(50)
        self.calculate_sma(200)
        self.calculate_ema(12)
        self.calculate_ema(26)
        self.calculate_macd()
        self.calculate_adx()
        
        # Momentum
        self.calculate_rsi()
        self.calculate_stochastic()
        self.calculate_cci()
        
        # Volatilità
        self.calculate_bollinger_bands()
        self.calculate_atr()
        
        # Volumi
        self.calculate_obv()
        self.calculate_volume_sma()
        
        print(f"Calcolati {len(self.indicators)} gruppi di indicatori")
    
    def generate_signals(self) -> List[TechnicalIndicator]:
        """
        Genera segnali di trading basati su tutti gli indicatori
        
        Returns:
            Lista di segnali tecnici
        """
        signals = []
        latest = self.df.iloc[-1]
        
        # RSI Signal
        rsi = self.indicators['RSI'].iloc[-1]
        if rsi < 30:
            signals.append(TechnicalIndicator(
                name="RSI", value=rsi, signal=Signal.STRONG_BUY,
                description="Ipervenduto - possibile rimbalzo"
            ))
        elif rsi > 70:
            signals.append(TechnicalIndicator(
                name="RSI", value=rsi, signal=Signal.STRONG_SELL,
                description="Ipercomprato - possibile correzione"
            ))
        else:
            signals.append(TechnicalIndicator(
                name="RSI", value=rsi, signal=Signal.NEUTRAL,
                description="Zona neutrale"
            ))
        
        # MACD Signal
        macd = self.indicators['MACD']
        macd_line = macd['macd'].iloc[-1]
        signal_line = macd['signal'].iloc[-1]
        histogram = macd['histogram'].iloc[-1]
        
        if macd_line > signal_line and histogram > 0:
            signals.append(TechnicalIndicator(
                name="MACD", value=macd_line, signal=Signal.BUY,
                description="MACD sopra la signal line - momentum positivo"
            ))
        elif macd_line < signal_line and histogram < 0:
            signals.append(TechnicalIndicator(
                name="MACD", value=macd_line, signal=Signal.SELL,
                description="MACD sotto la signal line - momentum negativo"
            ))
        else:
            signals.append(TechnicalIndicator(
                name="MACD", value=macd_line, signal=Signal.NEUTRAL,
                description="MACD inconcludente"
            ))
        
        # Bollinger Bands Signal
        bb = self.indicators['Bollinger']
        price = latest['Close']
        upper = bb['upper'].iloc[-1]
        lower = bb['lower'].iloc[-1]
        
        if price <= lower:
            signals.append(TechnicalIndicator(
                name="Bollinger", value=price, signal=Signal.BUY,
                description="Prezzo tocca banda inferiore - possibile rimbalzo"
            ))
        elif price >= upper:
            signals.append(TechnicalIndicator(
                name="Bollinger", value=price, signal=Signal.SELL,
                description="Prezzo tocca banda superiore - possibile ritracciamento"
            ))
        else:
            signals.append(TechnicalIndicator(
                name="Bollinger", value=price, signal=Signal.NEUTRAL,
                description="Prezzo dentro le bande"
            ))
        
        # ADX Signal (forza del trend)
        adx = self.indicators['ADX'].iloc[-1]
        if adx > 25:
            signals.append(TechnicalIndicator(
                name="ADX", value=adx, signal=Signal.NEUTRAL,
                description=f"Trend forte ({adx:.1f}) - seguire la direzione"
            ))
        else:
            signals.append(TechnicalIndicator(
                name="ADX", value=adx, signal=Signal.NEUTRAL,
                description=f"Trend debole ({adx:.1f}) - mercato laterale"
            ))
        
        # Moving Averages Crossover
        sma_20 = self.indicators['SMA_20'].iloc[-1]
        sma_50 = self.indicators['SMA_50'].iloc[-1]
        sma_200 = self.indicators['SMA_200'].iloc[-1]
        
        if sma_20 > sma_50 and sma_50 > sma_200:
            signals.append(TechnicalIndicator(
                name="MA Trend", value=sma_20, signal=Signal.STRONG_BUY,
                description="Allineamento rialzista delle medie mobili"
            ))
        elif sma_20 < sma_50 and sma_50 < sma_200:
            signals.append(TechnicalIndicator(
                name="MA Trend", value=sma_20, signal=Signal.STRONG_SELL,
                description="Allineamento ribassista delle medie mobili"
            ))
        
        self.signals = signals
        return signals
    
    def get_overall_signal(self) -> Tuple[Signal, float, str]:
        """
        Calcola un segnale complessivo basato su tutti gli indicatori
        
        Returns:
            Tuple con (Segnale, Confidenza, Descrizione)
        """
        if not self.signals:
            self.generate_signals()
        
        signal_scores = {
            Signal.STRONG_BUY: 2,
            Signal.BUY: 1,
            Signal.NEUTRAL: 0,
            Signal.SELL: -1,
            Signal.STRONG_SELL: -2
        }
        
        total_score = sum(signal_scores[s.signal] for s in self.signals)
        max_score = len(self.signals) * 2
        confidence = abs(total_score) / max_score * 100
        
        if total_score >= 3:
            overall = Signal.STRONG_BUY
            action = "FORTE ACQUISTO"
        elif total_score >= 1:
            overall = Signal.BUY
            action = "ACQUISTO"
        elif total_score <= -3:
            overall = Signal.STRONG_SELL
            action = "FORTE VENDITA"
        elif total_score <= -1:
            overall = Signal.SELL
            action = "VENDITA"
        else:
            overall = Signal.NEUTRAL
            action = "ATTESA/NEUTRALE"
        
        description = f"{action} (confidenza: {confidence:.1f}%, score: {total_score})"
        
        return overall, confidence, description
    
    def get_support_resistance(self) -> Dict[str, float]:
        """Identifica livelli di supporto e resistenza"""
        df = self.df
        
        # Supporti e resistenze basati su massimi/minimi recenti
        support_levels = []
        resistance_levels = []
        
        # Pivot points
        for i in range(20, len(df) - 20):
            window = df.iloc[i-20:i+20]
            if df['Low'].iloc[i] == window['Low'].min():
                support_levels.append(df['Low'].iloc[i])
            if df['High'].iloc[i] == window['High'].max():
                resistance_levels.append(df['High'].iloc[i])
        
        # Prendi i livelli più significativi
        current_price = df['Close'].iloc[-1]
        
        supports = sorted([s for s in support_levels if s < current_price], reverse=True)[:3]
        resistances = sorted([r for r in resistance_levels if r > current_price])[:3]
        
        return {
            'supports': supports,
            'resistances': resistances,
            'current_price': current_price
        }


if __name__ == "__main__":
    # Test
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    df = fetcher.get_stock_data("AAPL", period="6mo")
    
    if df is not None:
        analyzer = TechnicalAnalyzer(df)
        analyzer.calculate_all_indicators()
        signals = analyzer.generate_signals()
        
        print("\n=== SEGNALI TECNICI ===")
        for sig in signals:
            print(f"{sig.name}: {sig.signal.value} - {sig.description}")
        
        overall, conf, desc = analyzer.get_overall_signal()
        print(f"\n=== SEGNALE COMPLESSIVO ===")
        print(desc)
        
        sr = analyzer.get_support_resistance()
        print(f"\n=== SUPPORTI/RESISTENZE ===")
        print(f"Supporti: {sr['supports']}")
        print(f"Resistenze: {sr['resistances']}")
