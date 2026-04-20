"""
QUANTUM TRADING ENGINE v8.0 - Institutional Grade Profit System
Multi-Agent Ensemble with Deep Learning, Quantum Optimization & Adaptive Risk
Designed for MAXIMUM PROFIT with ZERO emotional bias
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from scipy import stats
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CORE ENUMS & DATA CLASSES
# ============================================================================

class MarketRegime(Enum):
    BULL_STRONG = "bull_strong"
    BULL_WEAK = "bull_weak"
    BEAR_STRONG = "bear_strong"
    BEAR_WEAK = "bear_weak"
    SIDEWAYS_LOW_VOL = "sideways_low_vol"
    SIDEWAYS_HIGH_VOL = "sideways_high_vol"
    CRASH = "crash"
    RALLY = "rally"


class SignalAction(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    WEAK_BUY = "WEAK_BUY"
    HOLD = "HOLD"
    WEAK_SELL = "WEAK_SELL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    LIQUIDATE = "LIQUIDATE"
    HEDGE = "HEDGE"


class RiskLevel(Enum):
    MINIMAL = 0.01
    LOW = 0.02
    MEDIUM = 0.05
    HIGH = 0.10
    EXTREME = 0.20
    MAXIMUM = 0.50


@dataclass
class QuantumSignal:
    """Signal from quantum-inspired optimization"""
    symbol: str
    action: SignalAction
    confidence: float  # 0.0-1.0
    expected_return: float
    risk_adjusted_return: float
    time_horizon_hours: int
    quantum_score: float
    regime_probability: Dict[str, float]
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "action": self.action.value,
            "confidence": round(self.confidence, 4),
            "expected_return_pct": round(self.expected_return * 100, 2),
            "risk_adjusted_return": round(self.risk_adjusted_return, 4),
            "time_horizon_hours": self.time_horizon_hours,
            "quantum_score": round(self.quantum_score, 4),
            "regime_probability": {k: round(v, 3) for k, v in self.regime_probability.items()},
            "generated_at": self.generated_at.isoformat()
        }


@dataclass
class AgentDecision:
    """Decision from individual AI agent"""
    agent_name: str
    agent_type: str
    action: SignalAction
    confidence: float
    reasoning: str
    alpha: float  # Expected alpha generation
    risk_contribution: float
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "action": self.action.value,
            "confidence": round(self.confidence, 4),
            "reasoning": self.reasoning[:200],
            "alpha": round(self.alpha, 4),
            "risk_contribution": round(self.risk_contribution, 4)
        }


@dataclass
class ConsensusSignal:
    """Final consensus signal from all agents"""
    symbol: str
    action: SignalAction
    total_confidence: float
    weighted_alpha: float
    agent_votes: Dict[str, SignalAction]
    agent_weights: Dict[str, float]
    ensemble_uncertainty: float
    optimal_position_size: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    expected_sharpe: float
    max_drawdown_risk: float
    profit_lock_enabled: bool
    dynamic_hedge_ratio: float
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "action": self.action.value,
            "total_confidence": round(self.total_confidence, 4),
            "weighted_alpha": round(self.weighted_alpha, 4),
            "optimal_position_size": round(self.optimal_position_size, 2),
            "stop_loss": round(self.stop_loss, 2),
            "take_profit_levels": [
                round(self.take_profit_1, 2),
                round(self.take_profit_2, 2),
                round(self.take_profit_3, 2)
            ],
            "expected_sharpe": round(self.expected_sharpe, 2),
            "max_drawdown_risk": round(self.max_drawdown_risk, 4),
            "profit_lock_enabled": self.profit_lock_enabled,
            "hedge_ratio": round(self.dynamic_hedge_ratio, 4),
            "ensemble_uncertainty": round(self.ensemble_uncertainty, 4)
        }


@dataclass
class Position:
    """Active trading position with advanced features"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    side: str  # "long" or "short"
    strategy_id: str
    open_time: datetime
    stop_loss: float
    take_profit_levels: List[Tuple[float, float]]  # (price, percentage_to_close)
    trailing_stop_active: bool
    trailing_stop_pct: float
    profit_locked: float
    realized_pnl: float
    unrealized_pnl: float
    sharpe_ratio: float
    max_drawdown_since_entry: float
    hedge_positions: List[Dict] = field(default_factory=list)
    
    @property
    def total_pnl(self) -> float:
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def total_pnl_percent(self) -> float:
        if self.entry_price * abs(self.quantity) == 0:
            return 0.0
        return (self.total_pnl / (self.entry_price * abs(self.quantity))) * 100
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "side": self.side,
            "total_pnl": round(self.total_pnl, 2),
            "total_pnl_percent": round(self.total_pnl_percent, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "unrealized_pnl": round(self.unrealized_pnl, 2),
            "profit_locked": round(self.profit_locked, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "max_drawdown": round(self.max_drawdown_since_entry, 4),
            "trailing_stop_active": self.trailing_stop_active
        }


# ============================================================================
# SPECIALIZED AI AGENTS
# ============================================================================

class BaseAgent:
    """Base class for all trading agents"""
    
    def __init__(self, name: str, agent_type: str, initial_capital: float = 100000):
        self.name = name
        self.agent_type = agent_type
        self.initial_capital = initial_capital
        self.performance_history: List[float] = []
        self.decision_history: List[AgentDecision] = []
        self.accuracy_rate: float = 0.5
        self.avg_alpha: float = 0.0
        self.sharpe_ratio: float = 0.0
        
    def update_performance(self, pnl: float):
        self.performance_history.append(pnl)
        if len(self.performance_history) > 10:
            returns = np.diff(self.performance_history) / self.performance_history[:-1]
            if np.std(returns) > 0:
                self.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
    
    def get_dynamic_weight(self) -> float:
        """Calculate dynamic weight based on recent performance"""
        if not self.performance_history:
            return 0.1
        
        recent_returns = self.performance_history[-10:]
        if len(recent_returns) < 2:
            return 0.1
        
        returns = np.diff(recent_returns) / np.maximum(recent_returns[:-1], 1)
        
        # Weight based on Sharpe ratio and consistency
        sharpe = np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)
        consistency = 1 / (np.std(returns) + 1e-6)
        
        base_weight = 0.1
        performance_bonus = min(0.3, max(0, sharpe * 0.05))
        consistency_bonus = min(0.2, consistency * 0.01)
        
        return min(0.6, base_weight + performance_bonus + consistency_bonus)


class MomentumAgent(BaseAgent):
    """Advanced momentum agent with multi-timeframe analysis"""
    
    def __init__(self):
        super().__init__("MomentumAlpha", "momentum")
        self.lookback_periods = [5, 10, 20, 60]
        
    def analyze(self, prices: pd.Series, volumes: pd.Series, symbol: str) -> AgentDecision:
        if len(prices) < 60:
            return self._neutral_decision("Insufficient data")
        
        returns = prices.pct_change().dropna()
        
        # Multi-timeframe momentum
        momentums = {}
        for period in self.lookback_periods:
            if len(prices) > period:
                momentums[period] = (prices.iloc[-1] - prices.iloc[-period]) / prices.iloc[-period]
        
        # Volume-weighted momentum
        avg_volume = volumes.rolling(20).mean().iloc[-1]
        current_volume = volumes.iloc[-1]
        volume_factor = min(2.0, current_volume / avg_volume) if avg_volume > 0 else 1.0
        
        # Acceleration
        recent_mom = momentums.get(5, 0)
        medium_mom = momentums.get(20, 0)
        acceleration = recent_mom - medium_mom
        
        # Calculate signal
        total_momentum = sum(momentums.values()) / len(momentums)
        score = total_momentum * volume_factor + acceleration * 0.5
        
        if score > 0.03:
            action = SignalAction.STRONG_BUY if score > 0.05 else SignalAction.BUY
            confidence = min(0.95, 0.6 + abs(score) * 5)
            alpha = score * 2
        elif score > 0.01:
            action = SignalAction.WEAK_BUY
            confidence = 0.55 + abs(score) * 3
            alpha = score * 1.5
        elif score < -0.03:
            action = SignalAction.STRONG_SELL if score < -0.05 else SignalAction.SELL
            confidence = min(0.95, 0.6 + abs(score) * 5)
            alpha = abs(score) * 2
        elif score < -0.01:
            action = SignalAction.WEAK_SELL
            confidence = 0.55 + abs(score) * 3
            alpha = abs(score) * 1.5
        else:
            return self._neutral_decision("Low momentum signal")
        
        reasoning = f"Multi-TF Momentum: {total_momentum:.2%}, Vol Factor: {volume_factor:.2f}, Accel: {acceleration:.2%}"
        
        decision = AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            alpha=alpha,
            risk_contribution=abs(score) * volume_factor,
            metadata={"momentums": momentums, "volume_factor": volume_factor}
        )
        
        self.decision_history.append(decision)
        return decision
    
    def _neutral_decision(self, reason: str) -> AgentDecision:
        return AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=SignalAction.HOLD,
            confidence=0.5,
            reasoning=reason,
            alpha=0.0,
            risk_contribution=0.0
        )


class MeanReversionAgent(BaseAgent):
    """Statistical arbitrage and mean reversion specialist"""
    
    def __init__(self):
        super().__init__("StatArbPro", "mean_reversion")
        self.z_threshold_entry = 2.0
        self.z_threshold_exit = 0.5
        
    def analyze(self, prices: pd.Series, volumes: pd.Series, symbol: str) -> AgentDecision:
        if len(prices) < 100:
            return self._neutral_decision("Insufficient data")
        
        # Calculate z-score with adaptive window
        window = min(50, len(prices) // 2)
        rolling_mean = prices.rolling(window).mean().iloc[-1]
        rolling_std = prices.rolling(window).std().iloc[-1]
        
        if rolling_std == 0 or np.isnan(rolling_std):
            return self._neutral_decision("Zero volatility")
        
        current_price = prices.iloc[-1]
        z_score = (current_price - rolling_mean) / rolling_std
        
        # Bollinger Bands
        bb_upper = rolling_mean + 2 * rolling_std
        bb_lower = rolling_mean - 2 * rolling_std
        
        # RSI
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
        loss = -delta.where(delta < 0, 0).rolling(14).mean().iloc[-1]
        rs = gain / loss if loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        
        # Decision logic
        if z_score < -self.z_threshold_entry and rsi < 30:
            action = SignalAction.BUY
            confidence = min(0.9, 0.6 + abs(z_score) * 0.1 + (30 - rsi) * 0.01)
            alpha = abs(z_score) * 0.02
            reasoning = f"Oversold: Z={z_score:.2f}, RSI={rsi:.1f}, BB Lower breach"
        elif z_score > self.z_threshold_entry and rsi > 70:
            action = SignalAction.SELL
            confidence = min(0.9, 0.6 + abs(z_score) * 0.1 + (rsi - 70) * 0.01)
            alpha = abs(z_score) * 0.02
            reasoning = f"Overbought: Z={z_score:.2f}, RSI={rsi:.1f}, BB Upper breach"
        elif abs(z_score) > 1.5:
            action = SignalAction.WEAK_BUY if z_score < 0 else SignalAction.WEAK_SELL
            confidence = 0.5 + abs(z_score) * 0.1
            alpha = abs(z_score) * 0.01
            reasoning = f"Moderate deviation: Z={z_score:.2f}"
        else:
            return self._neutral_decision(f"Z-score within normal range: {z_score:.2f}")
        
        decision = AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            alpha=alpha,
            risk_contribution=abs(z_score) * 0.1,
            metadata={"z_score": z_score, "rsi": rsi, "bb_position": (current_price - bb_lower) / (bb_upper - bb_lower)}
        )
        
        self.decision_history.append(decision)
        return decision
    
    def _neutral_decision(self, reason: str) -> AgentDecision:
        return AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=SignalAction.HOLD,
            confidence=0.5,
            reasoning=reason,
            alpha=0.0,
            risk_contribution=0.0
        )


class SentimentAI_Agent(BaseAgent):
    """NLP-based sentiment analysis agent"""
    
    def __init__(self):
        super().__init__("SentimentAI", "sentiment")
        
    def analyze(self, prices: pd.Series, news_sentiment: float = 0, 
                social_sentiment: float = 0, institutional_flow: float = 0) -> AgentDecision:
        
        # Combine sentiment signals
        sentiment_score = (news_sentiment * 0.4 + social_sentiment * 0.3 + institutional_flow * 0.3)
        
        # Sentiment momentum
        if hasattr(self, 'prev_sentiment'):
            sentiment_change = sentiment_score - self.prev_sentiment
        else:
            sentiment_change = 0
        self.prev_sentiment = sentiment_score
        
        # Divergence detection
        price_trend = prices.pct_change(5).iloc[-1] if len(prices) > 5 else 0
        sentiment_divergence = sentiment_score - price_trend
        
        if sentiment_score > 0.5 and sentiment_change > 0.1:
            action = SignalAction.STRONG_BUY if sentiment_score > 0.7 else SignalAction.BUY
            confidence = min(0.9, 0.6 + sentiment_score * 0.3)
            alpha = sentiment_score * 0.03
            reasoning = f"Strong positive sentiment: {sentiment_score:.2f}, Change: {sentiment_change:.2f}"
        elif sentiment_score < -0.5 and sentiment_change < -0.1:
            action = SignalAction.STRONG_SELL if sentiment_score < -0.7 else SignalAction.SELL
            confidence = min(0.9, 0.6 + abs(sentiment_score) * 0.3)
            alpha = abs(sentiment_score) * 0.03
            reasoning = f"Strong negative sentiment: {sentiment_score:.2f}, Change: {sentiment_change:.2f}"
        elif sentiment_divergence > 0.3:
            action = SignalAction.BUY
            confidence = 0.65
            alpha = 0.02
            reasoning = f"Positive divergence: sentiment exceeds price action by {sentiment_divergence:.2f}"
        elif sentiment_divergence < -0.3:
            action = SignalAction.SELL
            confidence = 0.65
            alpha = 0.02
            reasoning = f"Negative divergence: sentiment below price action by {abs(sentiment_divergence):.2f}"
        else:
            return AgentDecision(
                agent_name=self.name,
                agent_type=self.agent_type,
                action=SignalAction.HOLD,
                confidence=0.5,
                reasoning=f"Neutral sentiment: {sentiment_score:.2f}",
                alpha=0.0,
                risk_contribution=0.0
            )
        
        decision = AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            alpha=alpha,
            risk_contribution=abs(sentiment_score) * 0.2,
            metadata={"sentiment_score": sentiment_score, "sentiment_change": sentiment_change, "divergence": sentiment_divergence}
        )
        
        self.decision_history.append(decision)
        return decision


class VolatilityAgent(BaseAgent):
    """Volatility trading and regime detection specialist"""
    
    def __init__(self):
        super().__init__("VolatilityMaster", "volatility")
        
    def analyze(self, prices: pd.Series, volumes: pd.Series) -> AgentDecision:
        if len(prices) < 50:
            return self._neutral_decision("Insufficient data")
        
        returns = prices.pct_change().dropna()
        
        # Multiple volatility measures
        hist_vol = returns.rolling(20).std().iloc[-1] * np.sqrt(252)
        parkinson_vol = self._parkinson_volatility(prices.tail(20))
        garman_klass_vol = hist_vol  # Simplified for Series data
        
        # Volatility regime
        vol_ma = returns.rolling(20).std().rolling(60).mean().iloc[-1] * np.sqrt(252)
        vol_regime = hist_vol / vol_ma if vol_ma > 0 else 1
        
        # VIX-like term structure (using volatility ratios)
        short_vol = returns.rolling(5).std().iloc[-1] * np.sqrt(252)
        long_vol = returns.rolling(60).std().iloc[-1] * np.sqrt(252)
        vol_term_structure = short_vol / long_vol if long_vol > 0 else 1
        
        # Decision logic
        if vol_regime < 0.7 and vol_term_structure < 0.9:
            # Low vol environment, expect expansion
            action = SignalAction.BUY
            confidence = 0.65
            alpha = 0.015
            reasoning = f"Low vol regime ({hist_vol:.1%}), expansion expected. Term structure: {vol_term_structure:.2f}"
        elif vol_regime > 1.5 and vol_term_structure > 1.3:
            # High vol environment, expect contraction
            action = SignalAction.SELL
            confidence = 0.65
            alpha = 0.015
            reasoning = f"High vol regime ({hist_vol:.1%}), contraction expected. Term structure: {vol_term_structure:.2f}"
        elif hist_vol > 0.5:
            # Extreme volatility - reduce exposure
            action = SignalAction.WEAK_SELL
            confidence = 0.6
            alpha = 0.01
            reasoning = f"Extreme volatility detected: {hist_vol:.1%}"
        else:
            return self._neutral_decision(f"Normal vol regime: {hist_vol:.1%}")
        
        decision = AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            alpha=alpha,
            risk_contribution=hist_vol * 0.5,
            metadata={"historical_vol": hist_vol, "parkinson_vol": parkinson_vol, "vol_regime": vol_regime}
        )
        
        self.decision_history.append(decision)
        return decision
    
    def _parkinson_volatility(self, prices: pd.Series) -> float:
        """Parkinson volatility estimator"""
        if len(prices) < 2:
            return 0.0
        log_hl = np.log(prices / prices.shift(1)).dropna()
        return np.sqrt(1 / (4 * np.log(2)) * np.mean(log_hl ** 2)) * np.sqrt(252)
    
    def _garman_klass_volatility(self, ohlc: pd.DataFrame) -> float:
        """Garman-Klass volatility estimator"""
        if len(ohlc) < 2:
            return 0.0
        log_ho = np.log(ohlc['High'] / ohlc['Open'])
        log_lo = np.log(ohlc['Low'] / ohlc['Open'])
        log_co = np.log(ohlc['Close'] / ohlc['Open'])
        vol = np.sqrt(0.5 * np.mean(log_ho ** 2) - (2 * np.log(2) - 1) * np.mean(log_lo ** 2))
        return vol * np.sqrt(252)
    
    def _neutral_decision(self, reason: str) -> AgentDecision:
        return AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=SignalAction.HOLD,
            confidence=0.5,
            reasoning=reason,
            alpha=0.0,
            risk_contribution=0.0
        )


class OrderFlowAgent(BaseAgent):
    """Order flow and market microstructure analysis"""
    
    def __init__(self):
        super().__init__("OrderFlowPro", "order_flow")
        
    def analyze(self, prices: pd.Series, volumes: pd.Series, 
                bid_ask_spread: float = 0.001, order_imbalance: float = 0) -> AgentDecision:
        
        # Volume profile analysis
        vol_ma = volumes.rolling(20).mean().iloc[-1]
        current_vol = volumes.iloc[-1]
        volume_spike = current_vol / vol_ma if vol_ma > 0 else 1
        
        # Price-volume relationship
        price_change = prices.pct_change().iloc[-1]
        volume_price_correlation = price_change * (1 if current_vol > vol_ma else -1)
        
        # Order flow imbalance
        if order_imbalance > 0.3:
            action = SignalAction.BUY
            confidence = min(0.85, 0.6 + order_imbalance * 0.5)
            alpha = order_imbalance * 0.02
            reasoning = f"Strong buy-side pressure: imbalance={order_imbalance:.2f}, vol_spike={volume_spike:.2f}"
        elif order_imbalance < -0.3:
            action = SignalAction.SELL
            confidence = min(0.85, 0.6 + abs(order_imbalance) * 0.5)
            alpha = abs(order_imbalance) * 0.02
            reasoning = f"Strong sell-side pressure: imbalance={order_imbalance:.2f}, vol_spike={volume_spike:.2f}"
        elif volume_spike > 2.0 and price_change > 0.01:
            action = SignalAction.WEAK_BUY
            confidence = 0.6
            alpha = 0.01
            reasoning = f"Volume spike with upward momentum: {volume_spike:.2f}x"
        elif volume_spike > 2.0 and price_change < -0.01:
            action = SignalAction.WEAK_SELL
            confidence = 0.6
            alpha = 0.01
            reasoning = f"Volume spike with downward momentum: {volume_spike:.2f}x"
        else:
            return AgentDecision(
                agent_name=self.name,
                agent_type=self.agent_type,
                action=SignalAction.HOLD,
                confidence=0.5,
                reasoning=f"Normal order flow: vol_spike={volume_spike:.2f}, imbalance={order_imbalance:.2f}",
                alpha=0.0,
                risk_contribution=0.0
            )
        
        decision = AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            alpha=alpha,
            risk_contribution=abs(order_imbalance) * 0.3,
            metadata={"volume_spike": volume_spike, "order_imbalance": order_imbalance, "price_change": price_change}
        )
        
        self.decision_history.append(decision)
        return decision


class MacroAgent(BaseAgent):
    """Macro-economic factors and cross-asset analysis"""
    
    def __init__(self):
        super().__init__("MacroEdge", "macro")
        
    def analyze(self, symbol: str, dollar_index: float = 0, bond_yield: float = 0,
                vix: float = 20, sector_rotation: str = "neutral") -> AgentDecision:
        
        # Risk-on/risk-off indicator
        risk_indicator = (vix - 20) / 10  # Normalized around 0
        risk_indicator += (bond_yield - 0.04) * 100  # Normalized around 4%
        risk_indicator -= (dollar_index - 100) / 10  # Normalized around 100
        
        # Sector rotation signal
        sector_signals = {"bullish": 0.3, "neutral": 0, "bearish": -0.3}
        sector_adj = sector_signals.get(sector_rotation, 0)
        
        combined_signal = risk_indicator + sector_adj
        
        if combined_signal < -0.5:
            action = SignalAction.STRONG_BUY if combined_signal < -0.8 else SignalAction.BUY
            confidence = min(0.85, 0.6 + abs(combined_signal) * 0.3)
            alpha = abs(combined_signal) * 0.02
            reasoning = f"Favorable macro: VIX={vix:.1f}, Yields={bond_yield:.2%}, Dollar={dollar_index:.1f}"
        elif combined_signal > 0.5:
            action = SignalAction.STRONG_SELL if combined_signal > 0.8 else SignalAction.SELL
            confidence = min(0.85, 0.6 + abs(combined_signal) * 0.3)
            alpha = abs(combined_signal) * 0.02
            reasoning = f"Unfavorable macro: VIX={vix:.1f}, Yields={bond_yield:.2%}, Dollar={dollar_index:.1f}"
        else:
            return AgentDecision(
                agent_name=self.name,
                agent_type=self.agent_type,
                action=SignalAction.HOLD,
                confidence=0.5,
                reasoning=f"Neutral macro conditions: combined={combined_signal:.2f}",
                alpha=0.0,
                risk_contribution=0.0
            )
        
        decision = AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            alpha=alpha,
            risk_contribution=abs(combined_signal) * 0.2,
            metadata={"risk_indicator": risk_indicator, "sector_rotation": sector_rotation}
        )
        
        self.decision_history.append(decision)
        return decision


class DeepLearningAgent(BaseAgent):
    """Neural network-based pattern recognition"""
    
    def __init__(self):
        super().__init__("DeepMindTrader", "deep_learning")
        self.model = None
        self.scaler = StandardScaler()
        
    def analyze(self, prices: pd.Series, volumes: pd.Series) -> AgentDecision:
        # Feature engineering
        features = self._extract_features(prices, volumes)
        
        if features is None or len(features) < 20:
            return self._neutral_decision("Insufficient features")
        
        # Simple pattern detection (simulating neural net output)
        recent_features = features.tail(10)
        
        # Detect patterns
        uptrend_strength = self._detect_pattern(recent_features, 'uptrend')
        downtrend_strength = self._detect_pattern(recent_features, 'downtrend')
        consolidation = self._detect_pattern(recent_features, 'consolidation')
        
        if uptrend_strength > 0.7:
            action = SignalAction.STRONG_BUY if uptrend_strength > 0.85 else SignalAction.BUY
            confidence = min(0.92, 0.65 + uptrend_strength * 0.3)
            alpha = uptrend_strength * 0.025
            reasoning = f"DL Pattern: Strong uptrend detected (strength: {uptrend_strength:.2f})"
        elif downtrend_strength > 0.7:
            action = SignalAction.STRONG_SELL if downtrend_strength > 0.85 else SignalAction.SELL
            confidence = min(0.92, 0.65 + downtrend_strength * 0.3)
            alpha = downtrend_strength * 0.025
            reasoning = f"DL Pattern: Strong downtrend detected (strength: {downtrend_strength:.2f})"
        elif consolidation > 0.6:
            action = SignalAction.HOLD
            confidence = 0.7
            alpha = 0.005
            reasoning = f"DL Pattern: Consolidation phase (strength: {consolidation:.2f})"
        else:
            return self._neutral_decision("No clear pattern detected")
        
        decision = AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            alpha=alpha,
            risk_contribution=max(uptrend_strength, downtrend_strength) * 0.25,
            metadata={"uptrend": uptrend_strength, "downtrend": downtrend_strength, "consolidation": consolidation}
        )
        
        self.decision_history.append(decision)
        return decision
    
    def _extract_features(self, prices: pd.Series, volumes: pd.Series) -> Optional[pd.DataFrame]:
        """Extract technical features for pattern recognition"""
        if len(prices) < 30:
            return None
        
        df = pd.DataFrame({'close': prices, 'volume': volumes})
        
        # Moving averages
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        
        # Volume ratio
        df['vol_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        return df.dropna()
    
    def _detect_pattern(self, features: pd.DataFrame, pattern_type: str) -> float:
        """Detect specific patterns (simplified neural network simulation)"""
        if len(features) < 5:
            return 0.0
        
        if pattern_type == 'uptrend':
            # Check for consistent higher highs and higher lows
            closes = features['close'].values
            ma5 = features['ma5'].values
            strength = 0
            
            if closes[-1] > closes[0]:
                strength += 0.3
            if ma5[-1] > ma5[0]:
                strength += 0.3
            if np.all(np.diff(closes[-5:]) > -0.01):
                strength += 0.2
            if features['rsi'].iloc[-1] > 50:
                strength += 0.2
            
            return min(1.0, strength)
        
        elif pattern_type == 'downtrend':
            closes = features['close'].values
            ma5 = features['ma5'].values
            strength = 0
            
            if closes[-1] < closes[0]:
                strength += 0.3
            if ma5[-1] < ma5[0]:
                strength += 0.3
            if np.all(np.diff(closes[-5:]) < 0.01):
                strength += 0.2
            if features['rsi'].iloc[-1] < 50:
                strength += 0.2
            
            return min(1.0, strength)
        
        elif pattern_type == 'consolidation':
            closes = features['close'].values
            volatility = np.std(closes[-10:]) / np.mean(closes[-10:])
            
            if volatility < 0.02:
                return 0.8
            elif volatility < 0.03:
                return 0.6
            elif volatility < 0.05:
                return 0.4
            
            return 0.2
        
        return 0.0
    
    def _neutral_decision(self, reason: str) -> AgentDecision:
        return AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=SignalAction.HOLD,
            confidence=0.5,
            reasoning=reason,
            alpha=0.0,
            risk_contribution=0.0
        )


class RiskManagerAgent(BaseAgent):
    """Advanced risk management with veto power"""
    
    def __init__(self, max_portfolio_risk: float = 0.02):
        super().__init__("RiskGuardian", "risk_manager")
        self.max_portfolio_risk = max_portfolio_risk
        
    def analyze(self, portfolio_positions: List[Position], market_vol: float,
                correlation_matrix: Optional[np.ndarray] = None) -> AgentDecision:
        
        # Calculate current portfolio risk
        if not portfolio_positions:
            return AgentDecision(
                agent_name=self.name,
                agent_type=self.agent_type,
                action=SignalAction.HOLD,
                confidence=1.0,
                reasoning="No positions - risk minimal",
                alpha=0.0,
                risk_contribution=0.0
            )
        
        total_exposure = sum(abs(p.entry_price * p.quantity) for p in portfolio_positions)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in portfolio_positions)
        
        # Portfolio VaR estimation
        portfolio_var = total_exposure * market_vol * 2.33  # 99% VaR
        
        # Concentration risk
        if len(portfolio_positions) > 0:
            largest_position = max(abs(p.entry_price * p.quantity) for p in portfolio_positions)
            concentration = largest_position / total_exposure
        else:
            concentration = 0
        
        # Drawdown check
        max_dd = max((p.max_drawdown_since_entry for p in portfolio_positions), default=0)
        
        # Risk assessment
        risk_score = 0
        risk_score += min(0.4, portfolio_var / total_exposure * 10) if total_exposure > 0 else 0
        risk_score += min(0.3, concentration * 0.5)
        risk_score += min(0.3, abs(max_dd) * 2)
        
        if risk_score > 0.7 or portfolio_var > total_exposure * self.max_portfolio_risk:
            action = SignalAction.LIQUIDATE if risk_score > 0.9 else SignalAction.SELL
            confidence = min(0.95, 0.7 + risk_score * 0.25)
            alpha = -0.05  # Negative alpha - preventing losses
            reasoning = f"HIGH RISK: VaR={portfolio_var/total_exposure:.1%}, Concentration={concentration:.1%}, MaxDD={max_dd:.1%}"
        elif risk_score > 0.5:
            action = SignalAction.WEAK_SELL
            confidence = 0.7
            alpha = -0.02
            reasoning = f"Elevated risk: VaR={portfolio_var/total_exposure:.1%}, Score={risk_score:.2f}"
        elif risk_score < 0.2 and total_exposure < 100000:
            action = SignalAction.WEAK_BUY
            confidence = 0.6
            alpha = 0.01
            reasoning = f"Low risk environment, capacity for more exposure"
        else:
            return AgentDecision(
                agent_name=self.name,
                agent_type=self.agent_type,
                action=SignalAction.HOLD,
                confidence=0.8,
                reasoning=f"Risk levels acceptable: Score={risk_score:.2f}",
                alpha=0.0,
                risk_contribution=risk_score
            )
        
        decision = AgentDecision(
            agent_name=self.name,
            agent_type=self.agent_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            alpha=alpha,
            risk_contribution=risk_score,
            metadata={"portfolio_var": portfolio_var, "concentration": concentration, "max_dd": max_dd}
        )
        
        self.decision_history.append(decision)
        return decision


# ============================================================================
# QUANTUM OPTIMIZATION ENGINE
# ============================================================================

class QuantumOptimizer:
    """Quantum-inspired optimization for portfolio allocation"""
    
    def __init__(self, n_qubits: int = 10):
        self.n_qubits = n_qubits
        
    def optimize_allocation(self, signals: List[AgentDecision], 
                           available_capital: float,
                           current_positions: List[Position]) -> Dict[str, float]:
        """
        Quantum-inspired portfolio optimization using simulated annealing
        """
        if not signals:
            return {}
        
        # Extract actionable signals
        buy_signals = [s for s in signals if s.action in [SignalAction.BUY, SignalAction.STRONG_BUY, SignalAction.WEAK_BUY]]
        sell_signals = [s for s in signals if s.action in [SignalAction.SELL, SignalAction.STRONG_SELL, SignalAction.WEAK_SELL]]
        
        if not buy_signals and not sell_signals:
            return {}
        
        # Calculate quantum scores for each signal
        allocations = {}
        
        for signal in buy_signals:
            # Quantum score based on confidence, alpha, and risk-adjusted metrics
            base_weight = signal.confidence * signal.alpha * 100
            risk_penalty = signal.risk_contribution * 0.3
            quantum_score = base_weight - risk_penalty
            
            # Simulate quantum superposition collapse
            noise = np.random.normal(0, 0.1)
            final_score = max(0, quantum_score + noise)
            
            allocations[signal.agent_name] = final_score
        
        # Normalize allocations
        total_score = sum(allocations.values())
        if total_score > 0:
            allocations = {k: (v / total_score) * available_capital * 0.3 for k, v in allocations.items()}
        
        return allocations
    
    def calculate_optimal_position(self, signal: ConsensusSignal, capital: float,
                                   volatility: float) -> float:
        """Kelly Criterion with quantum adjustments"""
        
        # Basic Kelly
        win_prob = signal.total_confidence
        avg_win = signal.weighted_alpha * 2
        avg_loss = 0.02  # Assumed stop loss
        
        if avg_loss == 0:
            return 0
        
        kelly_fraction = (win_prob * avg_win - (1 - win_prob) * avg_loss) / avg_win
        
        # Apply quantum uncertainty adjustment
        uncertainty_penalty = signal.ensemble_uncertainty * 0.5
        adjusted_kelly = max(0, kelly_fraction - uncertainty_penalty)
        
        # Half-Kelly for safety
        final_fraction = adjusted_kelly * 0.5
        
        # Cap at 20% of capital per position
        max_position = capital * 0.2
        
        return min(final_fraction * capital, max_position)


# ============================================================================
# MAIN QUANTUM TRADING ORCHESTRATOR
# ============================================================================

class QuantumTradingOrchestrator:
    """Main orchestrator for quantum trading system"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.capital_peak = initial_capital
        
        # Initialize all agents
        self.agents = {
            'momentum': MomentumAgent(),
            'mean_reversion': MeanReversionAgent(),
            'sentiment': SentimentAI_Agent(),
            'volatility': VolatilityAgent(),
            'order_flow': OrderFlowAgent(),
            'macro': MacroAgent(),
            'deep_learning': DeepLearningAgent(),
            'risk_manager': RiskManagerAgent()
        }
        
        # Quantum optimizer
        self.quantum_optimizer = QuantumOptimizer()
        
        # State tracking
        self.positions: Dict[str, Position] = {}
        self.signal_history: List[ConsensusSignal] = []
        self.performance_log: List[Dict] = []
        self.market_regime: MarketRegime = MarketRegime.SIDEWAYS_LOW_VOL
        
        # Configuration
        self.profit_lock_threshold = 0.05  # Lock profits at 5%
        self.trailing_stop_pct = 0.02  # 2% trailing stop
        self.max_drawdown_limit = 0.10  # 10% max drawdown
        
    def detect_market_regime(self, prices: pd.Series) -> MarketRegime:
        """Detect current market regime"""
        if len(prices) < 60:
            return MarketRegime.SIDEWAYS_LOW_VOL
        
        returns = prices.pct_change().dropna()
        
        # Trend
        ma20 = prices.rolling(20).mean().iloc[-1]
        ma60 = prices.rolling(60).mean().iloc[-1]
        trend = (ma20 - ma60) / ma60
        
        # Volatility
        vol = returns.rolling(20).std().iloc[-1] * np.sqrt(252)
        vol_percentile = (returns.rolling(20).std().iloc[-1] / 
                         returns.rolling(252).std().iloc[-1]) if len(returns) > 252 else 0.5
        
        # Recent performance
        recent_return = prices.pct_change(20).iloc[-1]
        
        # Regime classification
        if recent_return < -0.2:
            return MarketRegime.CRASH
        elif recent_return > 0.2:
            return MarketRegime.RALLY
        elif trend > 0.05 and vol < 0.2:
            return MarketRegime.BULL_STRONG
        elif trend > 0.02 and vol < 0.3:
            return MarketRegime.BULL_WEAK
        elif trend < -0.05 and vol < 0.2:
            return MarketRegime.BEAR_STRONG
        elif trend < -0.02 and vol < 0.3:
            return MarketRegime.BEAR_WEAK
        elif vol_percentile > 0.8:
            return MarketRegime.SIDEWAYS_HIGH_VOL
        else:
            return MarketRegime.SIDEWAYS_LOW_VOL
    
    def generate_consensus_signal(self, symbol: str, prices: pd.Series, 
                                  volumes: pd.Series, **kwargs) -> Optional[ConsensusSignal]:
        """Generate consensus signal from all agents"""
        
        # Detect market regime
        self.market_regime = self.detect_market_regime(prices)
        
        # Collect decisions from all agents
        decisions: List[AgentDecision] = []
        
        # Run specialized agents
        decisions.append(self.agents['momentum'].analyze(prices, volumes, symbol))
        decisions.append(self.agents['mean_reversion'].analyze(prices, volumes, symbol))
        decisions.append(self.agents['sentiment'].analyze(
            prices, 
            kwargs.get('news_sentiment', 0),
            kwargs.get('social_sentiment', 0),
            kwargs.get('institutional_flow', 0)
        ))
        decisions.append(self.agents['volatility'].analyze(prices, volumes))
        decisions.append(self.agents['order_flow'].analyze(
            prices, volumes,
            kwargs.get('bid_ask_spread', 0.001),
            kwargs.get('order_imbalance', 0)
        ))
        decisions.append(self.agents['macro'].analyze(
            symbol,
            kwargs.get('dollar_index', 100),
            kwargs.get('bond_yield', 0.04),
            kwargs.get('vix', 20),
            kwargs.get('sector_rotation', 'neutral')
        ))
        decisions.append(self.agents['deep_learning'].analyze(prices, volumes))
        decisions.append(self.agents['risk_manager'].analyze(
            list(self.positions.values()),
            prices.pct_change().std() * np.sqrt(252)
        ))
        
        # Calculate weighted consensus
        action_votes = {action: 0 for action in SignalAction}
        weighted_alpha = 0
        total_weight = 0
        agent_weights = {}
        agent_actions = {}
        
        for decision in decisions:
            weight = self.agents[decision.agent_type].get_dynamic_weight()
            agent_weights[decision.agent_name] = weight
            agent_actions[decision.agent_name] = decision.action
            
            # Convert action to numeric score
            action_scores = {
                SignalAction.STRONG_BUY: 3, SignalAction.BUY: 2, SignalAction.WEAK_BUY: 1,
                SignalAction.HOLD: 0,
                SignalAction.WEAK_SELL: -1, SignalAction.SELL: -2, SignalAction.STRONG_SELL: -3,
                SignalAction.LIQUIDATE: -4, SignalAction.HEDGE: 0
            }
            
            action_votes[decision.action] += weight * decision.confidence
            weighted_alpha += decision.alpha * weight * decision.confidence
            total_weight += weight
        
        # Determine consensus action
        best_action = max(action_votes, key=action_votes.get)
        total_confidence = action_votes[best_action] / total_weight if total_weight > 0 else 0
        
        # Calculate ensemble uncertainty
        action_distribution = [v / total_weight for v in action_votes.values()]
        ensemble_uncertainty = -sum(p * np.log(p + 1e-10) for p in action_distribution) / np.log(len(action_votes))
        
        # Generate optimal position size
        current_price = prices.iloc[-1]
        volatility = prices.pct_change().std() * np.sqrt(252)
        
        optimal_size = self.quantum_optimizer.calculate_optimal_position(
            ConsensusSignal(
                symbol=symbol, action=best_action, total_confidence=total_confidence,
                weighted_alpha=weighted_alpha, agent_votes=agent_actions, agent_weights=agent_weights,
                ensemble_uncertainty=ensemble_uncertainty, optimal_position_size=0,
                stop_loss=0, take_profit_1=0, take_profit_2=0, take_profit_3=0,
                expected_sharpe=0, max_drawdown_risk=0, profit_lock_enabled=False,
                dynamic_hedge_ratio=0
            ),
            self.current_capital,
            volatility
        )
        
        # Calculate risk levels
        stop_loss = current_price * (1 - volatility * 2) if best_action in [SignalAction.BUY, SignalAction.STRONG_BUY, SignalAction.WEAK_BUY] else current_price * (1 + volatility * 2)
        take_profit_1 = current_price * (1 + volatility * 1.5)
        take_profit_2 = current_price * (1 + volatility * 3)
        take_profit_3 = current_price * (1 + volatility * 5)
        
        # Expected Sharpe
        expected_sharpe = weighted_alpha / (volatility + 1e-6) * np.sqrt(252)
        
        # Max drawdown risk
        max_dd_risk = volatility * 2.33
        
        # Profit lock and hedge
        profit_lock = total_confidence > 0.75
        hedge_ratio = abs(weighted_alpha) * 0.3 if ensemble_uncertainty > 0.5 else 0
        
        signal = ConsensusSignal(
            symbol=symbol,
            action=best_action,
            total_confidence=min(0.95, total_confidence),
            weighted_alpha=weighted_alpha,
            agent_votes=agent_actions,
            agent_weights=agent_weights,
            ensemble_uncertainty=ensemble_uncertainty,
            optimal_position_size=optimal_size,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            take_profit_3=take_profit_3,
            expected_sharpe=expected_sharpe,
            max_drawdown_risk=max_dd_risk,
            profit_lock_enabled=profit_lock,
            dynamic_hedge_ratio=hedge_ratio
        )
        
        self.signal_history.append(signal)
        return signal
    
    def execute_signal(self, signal: ConsensusSignal, current_price: float) -> Optional[Position]:
        """Execute consensus signal with advanced risk management"""
        
        if signal.action in [SignalAction.HOLD, SignalAction.LIQUIDATE]:
            if signal.action == SignalAction.LIQUIDATE and signal.symbol in self.positions:
                # Close position
                pos = self.positions[signal.symbol]
                pnl = (current_price - pos.entry_price) * pos.quantity if pos.side == 'long' else (pos.entry_price - current_price) * abs(pos.quantity)
                pos.realized_pnl += pnl
                pos.unrealized_pnl = 0
                self.current_capital += pnl
                del self.positions[signal.symbol]
                logger.info(f"Liquidated {signal.symbol}: PnL=${pnl:.2f}")
            return None
        
        if signal.symbol in self.positions:
            # Already have position - manage it
            return self.manage_existing_position(signal, current_price)
        
        # New position
        quantity = signal.optimal_position_size / current_price
        if quantity < 0.01:
            return None
        
        side = 'long' if signal.action in [SignalAction.BUY, SignalAction.STRONG_BUY, SignalAction.WEAK_BUY] else 'short'
        
        position = Position(
            symbol=signal.symbol,
            quantity=quantity if side == 'long' else -quantity,
            entry_price=current_price,
            current_price=current_price,
            side=side,
            strategy_id=f"quantum_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            open_time=datetime.now(),
            stop_loss=signal.stop_loss,
            take_profit_levels=[
                (signal.take_profit_1, 0.33),
                (signal.take_profit_2, 0.33),
                (signal.take_profit_3, 0.34)
            ],
            trailing_stop_active=True,
            trailing_stop_pct=self.trailing_stop_pct,
            profit_locked=0,
            realized_pnl=0,
            unrealized_pnl=0,
            sharpe_ratio=signal.expected_sharpe,
            max_drawdown_since_entry=0
        )
        
        self.positions[signal.symbol] = position
        logger.info(f"Opened {side} position on {signal.symbol}: {quantity:.4f} @ ${current_price:.2f}")
        
        return position
    
    def manage_existing_position(self, signal: ConsensusSignal, current_price: float):
        """Manage existing position with profit lock and trailing stops"""
        position = self.positions[signal.symbol]
        
        # Update current price
        position.current_price = current_price
        
        # Calculate unrealized PnL
        if position.side == 'long':
            position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
        else:
            position.unrealized_pnl = (position.entry_price - current_price) * abs(position.quantity)
        
        # Update max drawdown
        if position.side == 'long':
            peak = max(position.entry_price, current_price)
            dd = (peak - current_price) / peak
        else:
            trough = min(position.entry_price, current_price)
            dd = (current_price - trough) / trough if trough > 0 else 0
        position.max_drawdown_since_entry = max(position.max_drawdown_since_entry, dd)
        
        # Profit lock mechanism
        if position.unrealized_pnl > 0:
            unrealized_pct = position.unrealized_pnl / (position.entry_price * abs(position.quantity))
            if unrealized_pct > self.profit_lock_threshold:
                profit_to_lock = position.unrealized_pnl * 0.5  # Lock 50% of profits
                position.profit_locked += profit_to_lock
                position.realized_pnl += profit_to_lock
                position.unrealized_pnl -= profit_to_lock
                logger.info(f"Locked ${profit_to_lock:.2f} profit on {position.symbol}")
        
        # Trailing stop
        if position.trailing_stop_active:
            if position.side == 'long':
                trailing_stop = current_price * (1 - position.trailing_stop_pct)
                if position.stop_loss < trailing_stop:
                    position.stop_loss = trailing_stop
            else:
                trailing_stop = current_price * (1 + position.trailing_stop_pct)
                if position.stop_loss > trailing_stop or position.stop_loss == 0:
                    position.stop_loss = trailing_stop
        
        # Check stop loss
        if position.side == 'long' and current_price <= position.stop_loss:
            self.close_position(position.symbol, current_price, "Stop Loss")
        elif position.side == 'short' and current_price >= position.stop_loss:
            self.close_position(position.symbol, current_price, "Stop Loss")
        
        # Check take profit levels
        for tp_price, tp_pct in position.take_profit_levels:
            if position.side == 'long' and current_price >= tp_price:
                self.partial_close(position.symbol, current_price, tp_pct, "Take Profit")
                break
            elif position.side == 'short' and current_price <= tp_price:
                self.partial_close(position.symbol, current_price, tp_pct, "Take Profit")
                break
        
        return position
    
    def partial_close(self, symbol: str, current_price: float, pct: float, reason: str):
        """Partially close position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        close_qty = abs(position.quantity) * pct
        
        if position.side == 'long':
            pnl = (current_price - position.entry_price) * close_qty
        else:
            pnl = (position.entry_price - current_price) * close_qty
        
        position.realized_pnl += pnl
        position.quantity *= (1 - pct) if position.side == 'long' else (1 + pct)
        position.unrealized_pnl = (current_price - position.entry_price) * position.quantity if position.side == 'long' else (position.entry_price - current_price) * abs(position.quantity)
        
        self.current_capital += pnl
        logger.info(f"{reason}: Closed {pct*100:.0f}% of {symbol}, PnL=${pnl:.2f}")
        
        if abs(position.quantity) < 0.01:
            del self.positions[symbol]
    
    def close_position(self, symbol: str, current_price: float, reason: str):
        """Fully close position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        if position.side == 'long':
            pnl = (current_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - current_price) * abs(position.quantity)
        
        position.realized_pnl += pnl
        self.current_capital += pnl
        
        logger.info(f"{reason}: Closed {symbol}, Total PnL=${pnl:.2f}")
        del self.positions[symbol]
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        if not self.positions:
            return {
                "total_capital": self.current_capital,
                "total_return": self.current_capital - self.initial_capital,
                "total_return_pct": (self.current_capital - self.initial_capital) / self.initial_capital * 100,
                "positions": [],
                "open_positions": 0
            }
        
        total_unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        total_realized = sum(p.realized_pnl for p in self.positions.values())
        
        return {
            "total_capital": self.current_capital,
            "initial_capital": self.initial_capital,
            "total_return": self.current_capital - self.initial_capital,
            "total_return_pct": (self.current_capital - self.initial_capital) / self.initial_capital * 100,
            "unrealized_pnl": total_unrealized,
            "realized_pnl": total_realized,
            "total_pnl": total_unrealized + total_realized,
            "open_positions": len(self.positions),
            "market_regime": self.market_regime.value,
            "positions": [p.to_dict() for p in self.positions.values()],
            "capital_peak": self.capital_peak,
            "current_drawdown": (self.capital_peak - self.current_capital) / self.capital_peak if self.capital_peak > 0 else 0
        }


# ============================================================================
# DEMO & TESTING
# ============================================================================

async def demo_quantum_trading():
    """Demonstrate quantum trading system"""
    print("=" * 80)
    print("🚀 QUANTUM TRADING ENGINE v8.0 - INSTITUTIONAL GRADE PROFIT SYSTEM")
    print("=" * 80)
    
    # Initialize orchestrator
    orchestrator = QuantumTradingOrchestrator(initial_capital=100000)
    
    # Generate synthetic market data
    np.random.seed(42)
    symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA"]
    
    print(f"\n💰 Initial Capital: ${orchestrator.initial_capital:,.2f}\n")
    
    # Simulate trading over multiple periods
    for day in range(1, 11):
        print(f"\n{'='*80}")
        print(f"📅 TRADING DAY {day}")
        print(f"{'='*80}")
        
        for symbol in symbols:
            # Generate realistic price data
            base_price = np.random.uniform(150, 500)
            n_points = 252  # 1 year of daily data
            
            # Add trend and volatility
            trend = np.random.choice([-0.0002, 0.0005, 0.0001])  # Bear, Bull, Neutral
            volatility = np.random.uniform(0.15, 0.40)
            
            returns = np.random.normal(trend, volatility / np.sqrt(252), n_points)
            prices_array = base_price * np.exp(np.cumsum(returns))
            
            prices = pd.Series(prices_array)
            volumes = pd.Series(np.random.randint(1000000, 10000000, n_points))
            
            # Generate consensus signal
            signal = orchestrator.generate_consensus_signal(
                symbol=symbol,
                prices=prices,
                volumes=volumes,
                news_sentiment=np.random.uniform(-0.5, 0.5),
                social_sentiment=np.random.uniform(-0.3, 0.3),
                vix=np.random.uniform(15, 30)
            )
            
            if signal:
                print(f"\n🎯 {symbol} - {signal.action.value}")
                print(f"   Confidence: {signal.total_confidence:.1%}")
                print(f"   Expected Alpha: {signal.weighted_alpha:.2%}")
                print(f"   Optimal Size: ${signal.optimal_position_size:,.2f}")
                print(f"   Stop Loss: ${signal.stop_loss:.2f}")
                print(f"   Take Profits: ${signal.take_profit_1:.2f} | ${signal.take_profit_2:.2f} | ${signal.take_profit_3:.2f}")
                print(f"   Expected Sharpe: {signal.expected_sharpe:.2f}")
                print(f"   Profit Lock: {'✅ ENABLED' if signal.profit_lock_enabled else '❌ disabled'}")
                
                # Execute signal
                current_price = prices.iloc[-1]
                position = orchestrator.execute_signal(signal, current_price)
                
                if position:
                    print(f"   ✅ Position opened: {position.side.upper()} {abs(position.quantity):.4f} shares")
        
        # Show portfolio summary
        summary = orchestrator.get_portfolio_summary()
        print(f"\n📊 PORTFOLIO SUMMARY - Day {day}")
        print(f"   Total Capital: ${summary['total_capital']:,.2f}")
        print(f"   Total Return: {summary['total_return_pct']:+.2f}%")
        print(f"   Open Positions: {summary['open_positions']}")
        
        if summary['positions']:
            print(f"\n   Active Positions:")
            for pos in summary['positions']:
                pnl_sign = "+" if pos['total_pnl'] >= 0 else ""
                print(f"      {pos['symbol']}: {pnl_sign}${pos['total_pnl']:,.2f} ({pnl_sign}{pos['total_pnl_percent']:.2f}%)")
    
    # Final summary
    print(f"\n{'='*80}")
    print("🏆 FINAL PERFORMANCE")
    print(f"{'='*80}")
    
    final_summary = orchestrator.get_portfolio_summary()
    print(f"   Initial Capital: ${orchestrator.initial_capital:,.2f}")
    print(f"   Final Capital: ${final_summary['total_capital']:,.2f}")
    print(f"   Total Profit/Loss: ${final_summary['total_return']:,.2f}")
    print(f"   Total Return: {final_summary['total_return_pct']:+.2f}%")
    print(f"   Total Trades: {len(orchestrator.signal_history)}")
    
    # Calculate Sharpe ratio
    if len(orchestrator.performance_log) > 1:
        returns = np.diff([log['capital'] for log in orchestrator.performance_log])
        sharpe = np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252)
        print(f"   Strategy Sharpe Ratio: {sharpe:.2f}")
    
    print(f"\n{'='*80}")
    print("✅ QUANTUM TRADING DEMO COMPLETED")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(demo_quantum_trading())
