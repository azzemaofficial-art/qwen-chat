"""
Advanced Trading Strategies Engine
Multi-strategy framework with signal generation and position management
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics


class StrategyType(Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    PAIRS_TRADING = "pairs_trading"
    STAT_ARB = "statistical_arbitrage"
    MARKET_MAKING = "market_making"
    TREND_FOLLOWING = "trend_following"
    VOLATILITY_TRADING = "volatility_trading"


class SignalStrength(Enum):
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


@dataclass
class TradingSignal:
    strategy: StrategyType
    symbol: str
    direction: int  # 1=buy, -1=sell, 0=neutral
    strength: SignalStrength
    confidence: float  # 0.0-1.0
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    time_horizon: int = 1  # days
    metadata: Dict = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "strategy": self.strategy.value,
            "symbol": self.symbol,
            "direction": "BUY" if self.direction > 0 else "SELL" if self.direction < 0 else "NEUTRAL",
            "strength": self.strength.name,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "time_horizon": self.time_horizon,
            "generated_at": self.generated_at.isoformat()
        }


@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    side: str  # "long" or "short"
    strategy: StrategyType
    open_time: datetime = field(default_factory=datetime.now)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def unrealized_pnl(self) -> float:
        if self.side == "long":
            return (self.current_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - self.current_price) * self.quantity
    
    @property
    def unrealized_pnl_percent(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.unrealized_pnl / (self.entry_price * abs(self.quantity))) * 100
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "side": self.side,
            "strategy": self.strategy.value,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_percent": self.unrealized_pnl_percent,
            "open_time": self.open_time.isoformat()
        }


class MomentumStrategy:
    """Momentum-based trading strategy"""
    
    def __init__(self, lookback_period: int = 20, threshold: float = 0.02):
        self.lookback = lookback_period
        self.threshold = threshold
    
    def generate_signal(self, prices: List[float], volumes: List[float], 
                       symbol: str) -> Optional[TradingSignal]:
        if len(prices) < self.lookback:
            return None
        
        recent_prices = prices[-self.lookback:]
        momentum = (prices[-1] - prices[-self.lookback]) / prices[-self.lookback]
        
        # Volume confirmation
        avg_volume = statistics.mean(volumes[-self.lookback:])
        recent_volume = volumes[-1]
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        
        if momentum > self.threshold:
            direction = 1
            strength = self._calculate_strength(momentum, volume_ratio)
            confidence = min(0.95, 0.5 + abs(momentum) * 5 + (volume_ratio - 1) * 0.1)
            
            entry_price = prices[-1]
            target_price = entry_price * (1 + momentum * 0.5)
            stop_loss = entry_price * (1 - self.threshold * 0.5)
            
            return TradingSignal(
                strategy=StrategyType.MOMENTUM,
                symbol=symbol,
                direction=direction,
                strength=strength,
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                metadata={"momentum": momentum, "volume_ratio": volume_ratio}
            )
        elif momentum < -self.threshold:
            direction = -1
            strength = self._calculate_strength(abs(momentum), volume_ratio)
            confidence = min(0.95, 0.5 + abs(momentum) * 5 + (volume_ratio - 1) * 0.1)
            
            entry_price = prices[-1]
            target_price = entry_price * (1 - abs(momentum) * 0.5)
            stop_loss = entry_price * (1 + self.threshold * 0.5)
            
            return TradingSignal(
                strategy=StrategyType.MOMENTUM,
                symbol=symbol,
                direction=direction,
                strength=strength,
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                metadata={"momentum": momentum, "volume_ratio": volume_ratio}
            )
        
        return None
    
    def _calculate_strength(self, momentum: float, volume_ratio: float) -> SignalStrength:
        score = abs(momentum) * 100 + (volume_ratio - 1) * 10
        if score > 5:
            return SignalStrength.VERY_STRONG
        elif score > 3:
            return SignalStrength.STRONG
        elif score > 2:
            return SignalStrength.MODERATE
        elif score > 1:
            return SignalStrength.WEAK
        return SignalStrength.VERY_WEAK


class MeanReversionStrategy:
    """Mean reversion trading strategy"""
    
    def __init__(self, lookback_period: int = 20, z_threshold: float = 2.0):
        self.lookback = lookback_period
        self.z_threshold = z_threshold
    
    def generate_signal(self, prices: List[float], symbol: str) -> Optional[TradingSignal]:
        if len(prices) < self.lookback:
            return None
        
        recent_prices = prices[-self.lookback:]
        mean_price = statistics.mean(recent_prices)
        std_price = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 1
        
        if std_price == 0:
            return None
        
        current_price = prices[-1]
        z_score = (current_price - mean_price) / std_price
        
        if z_score < -self.z_threshold:
            # Price is significantly below mean - BUY signal
            direction = 1
            confidence = min(0.9, 0.5 + abs(z_score) / 6)
            strength = self._calculate_strength(abs(z_score))
            
            entry_price = current_price
            target_price = mean_price
            stop_loss = current_price * (1 - 0.02)
            
            return TradingSignal(
                strategy=StrategyType.MEAN_REVERSION,
                symbol=symbol,
                direction=direction,
                strength=strength,
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                metadata={"z_score": z_score, "mean": mean_price, "std": std_price}
            )
        elif z_score > self.z_threshold:
            # Price is significantly above mean - SELL signal
            direction = -1
            confidence = min(0.9, 0.5 + abs(z_score) / 6)
            strength = self._calculate_strength(abs(z_score))
            
            entry_price = current_price
            target_price = mean_price
            stop_loss = current_price * (1 + 0.02)
            
            return TradingSignal(
                strategy=StrategyType.MEAN_REVERSION,
                symbol=symbol,
                direction=direction,
                strength=strength,
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                metadata={"z_score": z_score, "mean": mean_price, "std": std_price}
            )
        
        return None
    
    def _calculate_strength(self, z_score: float) -> SignalStrength:
        if z_score > 3:
            return SignalStrength.VERY_STRONG
        elif z_score > 2.5:
            return SignalStrength.STRONG
        elif z_score > 2:
            return SignalStrength.MODERATE
        return SignalStrength.WEAK


class BreakoutStrategy:
    """Breakout trading strategy based on support/resistance levels"""
    
    def __init__(self, lookback_period: int = 20, volume_multiplier: float = 1.5):
        self.lookback = lookback_period
        self.volume_mult = volume_multiplier
    
    def generate_signal(self, prices: List[float], volumes: List[float],
                       symbol: str) -> Optional[TradingSignal]:
        if len(prices) < self.lookback:
            return None
        
        recent_prices = prices[-self.lookback:-1]
        resistance = max(recent_prices)
        support = min(recent_prices)
        current_price = prices[-1]
        
        avg_volume = statistics.mean(volumes[-self.lookback:])
        current_volume = volumes[-1]
        
        # Bullish breakout
        if current_price > resistance and current_volume > avg_volume * self.volume_mult:
            breakout_strength = (current_price - resistance) / resistance
            confidence = min(0.9, 0.5 + breakout_strength * 10 + 
                           (current_volume / avg_volume - 1) * 0.1)
            
            entry_price = current_price
            target_price = resistance + (resistance - support) * 0.5
            stop_loss = resistance * 0.98
            
            return TradingSignal(
                strategy=StrategyType.BREAKOUT,
                symbol=symbol,
                direction=1,
                strength=self._calculate_strength(breakout_strength, current_volume/avg_volume),
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                metadata={"resistance": resistance, "support": support, 
                         "breakout_strength": breakout_strength}
            )
        
        # Bearish breakdown
        elif current_price < support and current_volume > avg_volume * self.volume_mult:
            breakdown_strength = (support - current_price) / support
            confidence = min(0.9, 0.5 + breakdown_strength * 10 + 
                           (current_volume / avg_volume - 1) * 0.1)
            
            entry_price = current_price
            target_price = support - (resistance - support) * 0.5
            stop_loss = support * 1.02
            
            return TradingSignal(
                strategy=StrategyType.BREAKOUT,
                symbol=symbol,
                direction=-1,
                strength=self._calculate_strength(breakdown_strength, current_volume/avg_volume),
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                metadata={"resistance": resistance, "support": support,
                         "breakdown_strength": breakdown_strength}
            )
        
        return None
    
    def _calculate_strength(self, price_strength: float, volume_ratio: float) -> SignalStrength:
        score = price_strength * 100 + (volume_ratio - 1) * 20
        if score > 5:
            return SignalStrength.VERY_STRONG
        elif score > 3:
            return SignalStrength.STRONG
        elif score > 2:
            return SignalStrength.MODERATE
        return SignalStrength.WEAK


class PairsTradingStrategy:
    """Statistical pairs trading strategy"""
    
    def __init__(self, correlation_threshold: float = 0.7, z_threshold: float = 2.0):
        self.corr_threshold = correlation_threshold
        self.z_threshold = z_threshold
    
    def generate_signal(self, prices_a: List[float], prices_b: List[float],
                       symbol_a: str, symbol_b: str) -> Optional[Dict]:
        if len(prices_a) < 20 or len(prices_b) < 20:
            return None
        
        # Calculate correlation
        returns_a = [(prices_a[i] - prices_a[i-1])/prices_a[i-1] 
                    for i in range(1, len(prices_a))]
        returns_b = [(prices_b[i] - prices_b[i-1])/prices_b[i-1] 
                    for i in range(1, len(prices_b))]
        
        if len(returns_a) != len(returns_b):
            min_len = min(len(returns_a), len(returns_b))
            returns_a = returns_a[:min_len]
            returns_b = returns_b[:min_len]
        
        correlation = self._calculate_correlation(returns_a, returns_b)
        
        if abs(correlation) < self.corr_threshold:
            return None
        
        # Calculate spread
        ratio = [prices_a[i] / prices_b[i] for i in range(len(prices_a))]
        mean_ratio = statistics.mean(ratio[-20:])
        std_ratio = statistics.stdev(ratio[-20:]) if len(ratio) > 1 else 1
        
        if std_ratio == 0:
            return None
        
        current_ratio = ratio[-1]
        z_score = (current_ratio - mean_ratio) / std_ratio
        
        if z_score > self.z_threshold:
            # Ratio is high - sell A, buy B
            return {
                "signal_type": "pairs_trade",
                "leg1": {"symbol": symbol_a, "action": "sell", "weight": 1},
                "leg2": {"symbol": symbol_b, "action": "buy", "weight": current_ratio},
                "z_score": z_score,
                "correlation": correlation,
                "confidence": min(0.9, 0.5 + abs(z_score) / 6)
            }
        elif z_score < -self.z_threshold:
            # Ratio is low - buy A, sell B
            return {
                "signal_type": "pairs_trade",
                "leg1": {"symbol": symbol_a, "action": "buy", "weight": 1},
                "leg2": {"symbol": symbol_b, "action": "sell", "weight": current_ratio},
                "z_score": z_score,
                "correlation": correlation,
                "confidence": min(0.9, 0.5 + abs(z_score) / 6)
            }
        
        return None
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        n = len(x)
        if n == 0:
            return 0
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denom_x = math.sqrt(sum((x[i] - mean_x)**2 for i in range(n)))
        denom_y = math.sqrt(sum((y[i] - mean_y)**2 for i in range(n)))
        
        if denom_x * denom_y == 0:
            return 0
        
        return numerator / (denom_x * denom_y)


class StrategyEngine:
    """Central engine for managing multiple trading strategies"""
    
    def __init__(self):
        self.strategies = {
            StrategyType.MOMENTUM: MomentumStrategy(),
            StrategyType.MEAN_REVERSION: MeanReversionStrategy(),
            StrategyType.BREAKOUT: BreakoutStrategy(),
            StrategyType.PAIRS_TRADING: PairsTradingStrategy()
        }
        self.active_signals: List[TradingSignal] = []
        self.positions: Dict[str, Position] = {}
        self.signal_history: List[TradingSignal] = []
        self.market_data: Dict[str, Dict] = {}
    
    def update_market_data(self, symbol: str, prices: List[float], 
                          volumes: List[float], **kwargs):
        """Update market data for a symbol"""
        self.market_data[symbol] = {
            "prices": prices,
            "volumes": volumes,
            **kwargs
        }
    
    def scan_market(self, symbols: Optional[List[str]] = None) -> List[TradingSignal]:
        """Scan market for trading opportunities"""
        if symbols is None:
            symbols = list(self.market_data.keys())
        
        new_signals = []
        
        for symbol in symbols:
            if symbol not in self.market_data:
                continue
            
            data = self.market_data[symbol]
            prices = data.get("prices", [])
            volumes = data.get("volumes", [])
            
            # Run each strategy
            for strategy_type, strategy in self.strategies.items():
                if strategy_type == StrategyType.MOMENTUM and hasattr(strategy, 'generate_signal'):
                    signal = strategy.generate_signal(prices, volumes, symbol)
                    if signal:
                        new_signals.append(signal)
                
                elif strategy_type == StrategyType.MEAN_REVERSION and hasattr(strategy, 'generate_signal'):
                    signal = strategy.generate_signal(prices, symbol)
                    if signal:
                        new_signals.append(signal)
                
                elif strategy_type == StrategyType.BREAKOUT and hasattr(strategy, 'generate_signal'):
                    signal = strategy.generate_signal(prices, volumes, symbol)
                    if signal:
                        new_signals.append(signal)
        
        # Sort by confidence and strength
        new_signals.sort(key=lambda s: (s.confidence, s.strength.value), reverse=True)
        
        self.active_signals = new_signals
        self.signal_history.extend(new_signals)
        
        return new_signals
    
    def execute_signal(self, signal: TradingSignal, quantity: float) -> Optional[Position]:
        """Execute a trading signal and create a position"""
        if signal.entry_price is None:
            return None
        
        side = "long" if signal.direction > 0 else "short"
        
        position = Position(
            symbol=signal.symbol,
            quantity=quantity if side == "long" else -quantity,
            entry_price=signal.entry_price,
            current_price=signal.entry_price,
            side=side,
            strategy=signal.strategy,
            stop_loss=signal.stop_loss,
            take_profit=signal.target_price
        )
        
        self.positions[signal.symbol] = position
        
        # Remove from active signals
        self.active_signals = [s for s in self.active_signals 
                              if not (s.symbol == signal.symbol and 
                                     s.strategy == signal.strategy)]
        
        return position
    
    def update_positions(self, current_prices: Dict[str, float]):
        """Update positions with current prices"""
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.current_price = current_prices[symbol]
    
    def get_portfolio_summary(self) -> Dict:
        """Get summary of all positions"""
        if not self.positions:
            return {
                "total_positions": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "long_exposure": 0,
                "short_exposure": 0
            }
        
        total_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        total_value = sum(abs(p.entry_price * p.quantity) for p in self.positions.values())
        
        long_positions = [p for p in self.positions.values() if p.side == "long"]
        short_positions = [p for p in self.positions.values() if p.side == "short"]
        
        long_exposure = sum(abs(p.entry_price * p.quantity) for p in long_positions)
        short_exposure = sum(abs(p.entry_price * p.quantity) for p in short_positions)
        
        return {
            "total_positions": len(self.positions),
            "total_pnl": total_pnl,
            "total_pnl_percent": (total_pnl / total_value * 100) if total_value > 0 else 0,
            "long_exposure": long_exposure,
            "short_exposure": short_exposure,
            "net_exposure": long_exposure - short_exposure,
            "positions": [p.to_dict() for p in self.positions.values()]
        }


def demo():
    """Demonstrate strategy engine capabilities"""
    print("=" * 70)
    print("🎯 ADVANCED TRADING STRATEGIES ENGINE DEMO")
    print("=" * 70)
    
    engine = StrategyEngine()
    
    # Generate synthetic market data
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    
    for symbol in symbols:
        base_price = random.uniform(150, 500)
        prices = [base_price * (1 + random.gauss(0, 0.02)) for _ in range(30)]
        volumes = [random.randint(1000000, 10000000) for _ in range(30)]
        
        # Add some trends
        if symbol == "AAPL":
            prices = [p * (1 + i * 0.005) for i, p in enumerate(prices)]
        elif symbol == "TSLA":
            prices = [p * (1 - i * 0.003) for i, p in enumerate(prices)]
        
        engine.update_market_data(symbol, prices, volumes)
    
    # Scan for signals
    print("\n📊 Scanning Market for Signals...")
    signals = engine.scan_market(symbols)
    
    print(f"\n   Found {len(signals)} trading signals:")
    for i, signal in enumerate(signals[:5], 1):
        print(f"\n   Signal {i}:")
        print(f"      Symbol: {signal.symbol}")
        print(f"      Strategy: {signal.strategy.value}")
        print(f"      Direction: {'BUY' if signal.direction > 0 else 'SELL'}")
        print(f"      Strength: {signal.strength.name}")
        print(f"      Confidence: {signal.confidence:.1%}")
        print(f"      Entry: ${signal.entry_price:.2f}")
        print(f"      Target: ${signal.target_price:.2f}")
        print(f"      Stop Loss: ${signal.stop_loss:.2f}")
    
    # Execute top signals
    print("\n\n💼 Executing Top Signals...")
    for signal in signals[:3]:
        position = engine.execute_signal(signal, quantity=100)
        if position:
            print(f"\n   ✅ Opened {position.side} position on {position.symbol}")
            print(f"      Quantity: {abs(position.quantity)}")
            print(f"      Entry Price: ${position.entry_price:.2f}")
    
    # Update positions with new prices
    print("\n\n📈 Updating Positions with New Prices...")
    new_prices = {}
    for symbol in symbols:
        if symbol in engine.positions:
            pos = engine.positions[symbol]
            change = random.gauss(0, 0.01)
            new_prices[symbol] = pos.entry_price * (1 + change)
    
    engine.update_positions(new_prices)
    
    # Portfolio summary
    print("\n\n📊 Portfolio Summary:")
    summary = engine.get_portfolio_summary()
    print(f"   Total Positions: {summary['total_positions']}")
    print(f"   Total P&L: ${summary['total_pnl']:.2f}")
    print(f"   Total P&L %: {summary['total_pnl_percent']:.2f}%")
    print(f"   Long Exposure: ${summary['long_exposure']:.2f}")
    print(f"   Short Exposure: ${summary['short_exposure']:.2f}")
    print(f"   Net Exposure: ${summary['net_exposure']:.2f}")
    
    if summary['positions']:
        print("\n   Active Positions:")
        for pos in summary['positions']:
            pnl_sign = "+" if pos['unrealized_pnl'] >= 0 else ""
            print(f"      {pos['symbol']}: {pnl_sign}${pos['unrealized_pnl']:.2f} ({pnl_sign}{pos['unrealized_pnl_percent']:.2f}%)")
    
    print("\n" + "=" * 70)
    print("✅ STRATEGY ENGINE DEMO COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    demo()
