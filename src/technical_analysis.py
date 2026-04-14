"""
Technical Analysis - Analisi tecnica avanzata
Include indicatori, pattern recognition e segnali
Aggiornato con: Ichimoku, VWAP, Fibonacci, Pattern Candlestick
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


@dataclass
class CandlestickPattern:
    """Pattern candlestick rilevato"""
    name: str
    type: str  # 'bullish' o 'bearish'
    strength: float  # 0-100
    description: str


class TechnicalAnalyzer:
    """Analizzatore tecnico per identificare opportunità di trading"""
    
    def __init__(self, df=None):
        """
        Args:
            df: DataFrame con dati OHLCV (Open, High, Low, Close, Volume)
        """
        self.df = df.copy() if df is not None else None
        self.signals = []
        self.indicators = {}
        self.patterns = []
        
        if self.df is not None and not self._validate_data():
            raise ValueError("Dati non validi per l'analisi tecnica")
    
    def _validate_data(self) -> bool:
        """Valida che il DataFrame contenga i dati necessari"""
        if self.df is None:
            return False
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        return all(col in self.df.columns for col in required_cols) and len(self.df) >= 50
    
    # === Indicatori di Trend ===
    
    def calculate_sma(self, prices: Optional[pd.Series] = None, period: int = 20, window: Optional[int] = None) -> pd.Series:
        """
        Simple Moving Average - Media Mobile Semplice
        
        Args:
            prices: Serie di prezzi opzionale (se non fornita, usa self.df['Close'])
            period: Periodo della media mobile (default 20)
            window: Alias per period (per compatibilità)
            
        Returns:
            Serie con la SMA calcolata
            
        Note:
            Supporta sia l'uso con DataFrame interno che con serie esterna
        """
        # Supporta alias 'window' per compatibilità
        if window is not None:
            period = window
        
        # Determina quale serie di prezzi usare
        if prices is not None:
            data = prices
        elif self.df is not None:
            data = self.df['Close']
        else:
            return pd.Series()
        
        sma = pd.Series(data).rolling(window=period).mean()
        
        if self.df is not None:
            self.indicators[f'SMA_{period}'] = sma
        
        return sma
    
    def calculate_ema(self, period: int = 20) -> pd.Series:
        """Exponential Moving Average"""
        ema = self.df['Close'].ewm(span=period, adjust=False).mean()
        self.indicators[f'EMA_{period}'] = ema
        return ema
    
    def calculate_vwap(self) -> pd.Series:
        """Volume Weighted Average Price - Prezzo medio ponderato per volume"""
        typical_price = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        vwap = (typical_price * self.df['Volume']).cumsum() / self.df['Volume'].cumsum()
        self.indicators['VWAP'] = vwap
        return vwap
    
    def calculate_ichimoku_cloud(
        self,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52
    ) -> Dict[str, pd.Series]:
        """
        Ichimoku Cloud - Sistema completo di trend following
        """
        # Tenkan-sen (Conversion Line)
        high_tenkan = self.df['High'].rolling(window=tenkan_period).max()
        low_tenkan = self.df['Low'].rolling(window=tenkan_period).min()
        tenkan_sen = (high_tenkan + low_tenkan) / 2
        
        # Kijun-sen (Base Line)
        high_kijun = self.df['High'].rolling(window=kijun_period).max()
        low_kijun = self.df['Low'].rolling(window=kijun_period).min()
        kijun_sen = (high_kijun + low_kijun) / 2
        
        # Senkou Span A (Leading Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
        
        # Senkou Span B (Leading Span B)
        high_senkou_b = self.df['High'].rolling(window=senkou_b_period).max()
        low_senkou_b = self.df['Low'].rolling(window=senkou_b_period).min()
        senkou_span_b = ((high_senkou_b + low_senkou_b) / 2).shift(kijun_period)
        
        # Chikou Span (Lagging Span)
        chikou_span = self.df['Close'].shift(-kijun_period)
        
        result = {
            'tenkan': tenkan_sen,
            'kijun': kijun_sen,
            'senkou_a': senkou_span_a,
            'senkou_b': senkou_span_b,
            'chikou': chikou_span
        }
        
        self.indicators['Ichimoku'] = result
        return result
    
    def calculate_macd(
        self, 
        prices=None,
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: Serie di prezzi opzionale (se non fornita, usa self.df['Close'])
            fast_period: Periodo EMA veloce (default 12)
            slow_period: Periodo EMA lento (default 26)
            signal_period: Periodo linea di segnale (default 9)
        """
        # Determina quale serie di prezzi usare
        if prices is not None:
            data = pd.Series(prices)
        elif self.df is not None:
            data = self.df['Close']
        else:
            return {'macd': pd.Series(), 'signal': pd.Series(), 'histogram': pd.Series()}
        
        ema_fast = data.ewm(span=fast_period, adjust=False).mean()
        ema_slow = data.ewm(span=slow_period, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        result = {
            'macd_line': macd_line,
            'signal_line': signal_line,
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
    
    def calculate_rsi(self, prices: Optional[pd.Series] = None, period: int = 14, window: Optional[int] = None) -> pd.Series:
        """Relative Strength Index
        
        Args:
            prices: Serie di prezzi opzionale (se non fornita, usa self.df['Close'])
            period: Periodo per il calcolo (default 14)
            window: Alias per period (per compatibilità)
        """
        if window is not None:
            period = window
        if prices is not None:
            data = prices
        elif self.df is not None:
            data = self.df['Close']
        else:
            return pd.Series()
        
        data = pd.Series(data)
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Riempie i NaN iniziali con bfill per garantire che tutti i valori siano validi
        # Questo è necessario perché i primi 'period' valori sono NaN a causa del rolling window
        rsi = rsi.bfill()
        
        # Clamp tra 0 e 100 per garantire che l'RSI sia sempre nel range corretto
        rsi = rsi.clip(0, 100)
        
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
    
    def calculate_williams_r(self, period: int = 14) -> pd.Series:
        """Williams %R - Indicatore di momentum"""
        highest_high = self.df['High'].rolling(window=period).max()
        lowest_low = self.df['Low'].rolling(window=period).min()
        
        williams_r = -100 * (highest_high - self.df['Close']) / (highest_high - lowest_low)
        self.indicators['Williams_R'] = williams_r
        return williams_r
    
    # === Indicatori di Volatilità ===
    
    def calculate_bollinger_bands(
        self,
        prices=None,
        period: int = 20,
        std_dev: float = 2.0,
        window=None
    ) -> Dict[str, pd.Series]:
        """Bollinger Bands - Bande di volatilità
        
        Args:
            prices: Serie di prezzi opzionale
            period: Periodo (default 20)
            std_dev: Deviazioni standard (default 2.0)
            window: Alias per period
        """
        if window is not None:
            period = window
        if prices is not None:
            data = prices
        elif self.df is not None:
            data = self.df['Close']
        else:
            return {'upper': pd.Series(), 'middle': pd.Series(), 'lower': pd.Series(), 'bandwidth': pd.Series(), 'percent_b': pd.Series()}
        
        data = pd.Series(data)
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        # Bandwidth e %B
        bandwidth = (upper - lower) / sma * 100
        # Usa 'data' invece di 'self.df['Close']' per supportare prezzi esterni
        percent_b = (data - lower) / (upper - lower)
        
        # Riempie i NaN iniziali con ffill per garantire che tutti i valori siano validi
        # Questo è necessario perché i primi 'period' valori sono NaN a causa del rolling window
        upper = upper.bfill()
        sma = sma.bfill()
        lower = lower.bfill()
        bandwidth = bandwidth.bfill()
        percent_b = percent_b.bfill()
        
        result = {
            'upper': upper,
            'middle': sma,
            'lower': lower,
            'bandwidth': bandwidth,
            'percent_b': percent_b
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
    
    def calculate_keltner_channels(
        self,
        ema_period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0
    ) -> Dict[str, pd.Series]:
        """Keltner Channels - Canali basati su ATR"""
        ema = self.df['Close'].ewm(span=ema_period, adjust=False).mean()
        atr = self.calculate_atr(atr_period)
        
        upper = ema + (atr * multiplier)
        lower = ema - (atr * multiplier)
        
        result = {
            'upper': upper,
            'middle': ema,
            'lower': lower
        }
        
        self.indicators['Keltner'] = result
        return result
    
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
    
    def calculate_mfi(self, period: int = 14) -> pd.Series:
        """Money Flow Index - RSI ponderato per volume"""
        typical_price = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        money_flow = typical_price * self.df['Volume']
        
        delta = typical_price.diff()
        positive_flow = money_flow.where(delta > 0, 0)
        negative_flow = money_flow.where(delta < 0, 0)
        
        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()
        
        mfi = 100 - (100 / (1 + positive_mf / negative_mf))
        self.indicators['MFI'] = mfi
        return mfi
    
    # === Fibonacci Retracement ===
    
    def calculate_fibonacci_levels(self, lookback: int = 100) -> Dict[str, float]:
        """Calcola livelli di ritracciamento di Fibonacci"""
        df = self.df[-lookback:]
        
        high = df['High'].max()
        low = df['Low'].min()
        
        diff = high - low
        
        levels = {
            '0.0%': low,
            '23.6%': low + diff * 0.236,
            '38.2%': low + diff * 0.382,
            '50.0%': low + diff * 0.5,
            '61.8%': low + diff * 0.618,
            '78.6%': low + diff * 0.786,
            '100.0%': high
        }
        
        self.indicators['Fibonacci'] = levels
        return levels
    
    # === Pattern Recognition ===
    
    def detect_candlestick_patterns(self) -> List[CandlestickPattern]:
        """Rileva pattern candlestick significativi"""
        patterns = []
        df = self.df
        
        for i in range(2, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            prev2 = df.iloc[i-2]
            
            # Doji
            body_size = abs(current['Close'] - current['Open'])
            total_range = current['High'] - current['Low']
            if total_range > 0 and body_size / total_range < 0.1:
                patterns.append(CandlestickPattern(
                    name="Doji",
                    type="neutral",
                    strength=60,
                    description="Indecisione del mercato"
                ))
            
            # Hammer
            lower_shadow = min(current['Open'], current['Close']) - current['Low']
            upper_shadow = current['High'] - max(current['Open'], current['Close'])
            body = abs(current['Close'] - current['Open'])
            
            if lower_shadow > body * 2 and upper_shadow < body * 0.5:
                if current['Close'] > current['Open']:
                    patterns.append(CandlestickPattern(
                        name="Hammer",
                        type="bullish",
                        strength=75,
                        description="Possibile inversione rialzista"
                    ))
            
            # Engulfing Bullish
            if (prev['Close'] < prev['Open'] and 
                current['Close'] > current['Open'] and
                current['Open'] < prev['Close'] and
                current['Close'] > prev['Open']):
                patterns.append(CandlestickPattern(
                    name="Engulfing Bullish",
                    type="bullish",
                    strength=80,
                    description="Forte segnale di acquisto"
                ))
            
            # Engulfing Bearish
            if (prev['Close'] > prev['Open'] and 
                current['Close'] < current['Open'] and
                current['Open'] > prev['Close'] and
                current['Close'] < prev['Open']):
                patterns.append(CandlestickPattern(
                    name="Engulfing Bearish",
                    type="bearish",
                    strength=80,
                    description="Forte segnale di vendita"
                ))
            
            # Morning Star
            if (len(df) > i+2 and
                prev2['Close'] < prev2['Open'] and
                body < prev2['Close'] - prev2['Open'] and
                current['Close'] > current['Open'] and
                current['Close'] > (prev2['Open'] + prev2['Close']) / 2):
                patterns.append(CandlestickPattern(
                    name="Morning Star",
                    type="bullish",
                    strength=85,
                    description="Inversione rialzista a 3 candele"
                ))
        
        # Mantieni solo ultimi pattern rilevanti
        self.patterns = patterns[-10:]
        return self.patterns
    
    # === Analisi completa ===
    
    def calculate_all_indicators(self):
        """Calcola tutti gli indicatori principali"""
        print("Calcolo indicatori tecnici avanzati...")
        
        # Trend
        self.calculate_sma(20)
        self.calculate_sma(50)
        self.calculate_sma(200)
        self.calculate_ema(12)
        self.calculate_ema(26)
        self.calculate_vwap()
        self.calculate_ichimoku_cloud()
        self.calculate_macd()
        self.calculate_adx()
        
        # Momentum
        self.calculate_rsi()
        self.calculate_stochastic()
        self.calculate_cci()
        self.calculate_williams_r()
        self.calculate_mfi()
        
        # Volatilità
        self.calculate_bollinger_bands()
        self.calculate_atr()
        self.calculate_keltner_channels()
        
        # Volumi
        self.calculate_obv()
        self.calculate_volume_sma()
        
        # Fibonacci
        self.calculate_fibonacci_levels()
        
        # Pattern
        self.detect_candlestick_patterns()
        
        print(f"Calcolati {len(self.indicators)} gruppi di indicatori")
        print(f"Rilevati {len(self.patterns)} pattern candlestick")
    
    def generate_signals(self) -> List[TechnicalIndicator]:
        """
        Genera segnali di trading basati su tutti gli indicatori
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
        percent_b = bb['percent_b'].iloc[-1]
        
        if price <= lower or percent_b < 0:
            signals.append(TechnicalIndicator(
                name="Bollinger", value=price, signal=Signal.BUY,
                description="Prezzo tocca/supera banda inferiore"
            ))
        elif price >= upper or percent_b > 1:
            signals.append(TechnicalIndicator(
                name="Bollinger", value=price, signal=Signal.SELL,
                description="Prezzo tocca/supera banda superiore"
            ))
        else:
            signals.append(TechnicalIndicator(
                name="Bollinger", value=price, signal=Signal.NEUTRAL,
                description="Prezzo dentro le bande"
            ))
        
        # ADX Signal
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
        
        # Ichimoku Cloud Signal
        ichimoku = self.indicators['Ichimoku']
        price = latest['Close']
        tenkan = ichimoku['tenkan'].iloc[-1]
        kijun = ichimoku['kijun'].iloc[-1]
        senkou_a = ichimoku['senkou_a'].iloc[-1]
        senkou_b = ichimoku['senkou_b'].iloc[-1]
        
        cloud_top = max(senkou_a, senkou_b) if pd.notna(senkou_a) and pd.notna(senkou_b) else None
        cloud_bottom = min(senkou_a, senkou_b) if pd.notna(senkou_a) and pd.notna(senkou_b) else None
        
        if cloud_top and cloud_bottom:
            if price > cloud_top and tenkan > kijun:
                signals.append(TechnicalIndicator(
                    name="Ichimoku", value=price, signal=Signal.STRONG_BUY,
                    description="Prezzo sopra cloud + Tenkan > Kijun"
                ))
            elif price < cloud_bottom and tenkan < kijun:
                signals.append(TechnicalIndicator(
                    name="Ichimoku", value=price, signal=Signal.STRONG_SELL,
                    description="Prezzo sotto cloud + Tenkan < Kijun"
                ))
            else:
                signals.append(TechnicalIndicator(
                    name="Ichimoku", value=price, signal=Signal.NEUTRAL,
                    description="Segnale Ichimoku misto"
                ))
        
        # VWAP Signal
        vwap = self.indicators['VWAP'].iloc[-1]
        if price < vwap * 0.97:
            signals.append(TechnicalIndicator(
                name="VWAP", value=vwap, signal=Signal.BUY,
                description="Prezzo significativamente sotto VWAP"
            ))
        elif price > vwap * 1.03:
            signals.append(TechnicalIndicator(
                name="VWAP", value=vwap, signal=Signal.SELL,
                description="Prezzo significativamente sopra VWAP"
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
        
        # Pattern Signals
        bullish_patterns = [p for p in self.patterns if p.type == 'bullish']
        bearish_patterns = [p for p in self.patterns if p.type == 'bearish']
        
        if len(bullish_patterns) >= 2:
            signals.append(TechnicalIndicator(
                name="Patterns", value=len(bullish_patterns), signal=Signal.BUY,
                description=f"{len(bullish_patterns)} pattern rialzisti rilevati"
            ))
        elif len(bearish_patterns) >= 2:
            signals.append(TechnicalIndicator(
                name="Patterns", value=len(bearish_patterns), signal=Signal.SELL,
                description=f"{len(bearish_patterns)} pattern ribassisti rilevati"
            ))
        
        self.signals = signals
        return signals
    
    def get_overall_signal(self) -> Tuple[Signal, float, str]:
        """
        Calcola un segnale complessivo basato su tutti gli indicatori
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
        confidence = abs(total_score) / max_score * 100 if max_score > 0 else 0
        
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
        
        # Aggiungi livelli Fibonacci
        fib_levels = self.indicators.get('Fibonacci', {})
        if fib_levels:
            for level_name, level_value in fib_levels.items():
                if '38.2%' in level_name or '61.8%' in level_name:
                    support_levels.append(level_value)
        
        # Prendi i livelli più significativi
        current_price = df['Close'].iloc[-1]
        
        supports = sorted([s for s in support_levels if s < current_price], reverse=True)[:3]
        resistances = sorted([r for r in resistance_levels if r > current_price])[:3]
        
        # Aggiungi VWAP come supporto/resistenza dinamica
        vwap = self.indicators.get('VWAP', pd.Series([0])).iloc[-1]
        if vwap > 0:
            if vwap < current_price:
                resistances.insert(0, vwap)
            else:
                supports.insert(0, vwap)
        
        return {
            'supports': list(set(supports))[:3],
            'resistances': list(set(resistances))[:3],
            'current_price': current_price,
            'vwap': vwap,
            'fibonacci': fib_levels
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
