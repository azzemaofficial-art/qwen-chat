"""
ADVANCED BACKTESTING ENGINE v8.0
Professional-grade backtesting with realistic slippage, commissions, and market impact
Validates quantum trading strategies against historical data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Trade:
    """Individual trade record"""
    symbol: str
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    side: str  # long or short
    pnl: float = 0.0
    pnl_percent: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    holding_period: int = 0
    max_profit: float = 0.0
    max_loss: float = 0.0
    exit_reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "entry_date": self.entry_date.isoformat(),
            "exit_date": self.exit_date.isoformat() if self.exit_date else None,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "side": self.side,
            "pnl": round(self.pnl, 2),
            "pnl_percent": round(self.pnl_percent, 2),
            "commission": round(self.commission, 2),
            "slippage": round(self.slippage, 2),
            "holding_period": self.holding_period,
            "max_profit": round(self.max_profit, 2),
            "max_loss": round(self.max_loss, 2),
            "exit_reason": self.exit_reason
        }


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 100000
    commission_rate: float = 0.001  # 0.1% per trade
    slippage_rate: float = 0.0005  # 0.05% slippage
    position_size_pct: float = 0.1  # 10% of capital per position
    max_positions: int = 10
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.04  # 4% take profit
    margin_requirement: float = 1.0  # 100% for no leverage
    short_selling_allowed: bool = True
    benchmark_symbol: str = "SPY"


class AdvancedBacktester:
    """Professional backtesting engine"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.capital = config.initial_capital
        self.initial_capital = config.initial_capital
        self.positions: Dict[str, Dict] = {}
        self.closed_trades: List[Trade] = []
        self.open_trades: Dict[str, Trade] = {}
        self.equity_curve: List[float] = [config.initial_capital]
        self.daily_returns: List[float] = []
        self.trades_log: List[Dict] = []
        
    def run_backtest(self, signals: List[Dict], price_data: pd.DataFrame) -> Dict:
        """
        Run complete backtest
        
        Args:
            signals: List of trading signals with dates
            price_data: DataFrame with OHLCV data indexed by date
        """
        print("\n" + "="*80)
        print("🧪 ADVANCED BACKTESTING ENGINE v8.0")
        print("="*80)
        print(f"\n💰 Initial Capital: ${self.config.initial_capital:,.2f}")
        print(f"📊 Commission Rate: {self.config.commission_rate:.2%}")
        print(f"📉 Slippage Rate: {self.config.slippage_rate:.2%}")
        print(f"📈 Max Positions: {self.config.max_positions}")
        print("="*80 + "\n")
        
        # Process each day
        dates = sorted(price_data.index.unique())
        
        for i, date in enumerate(dates):
            day_signals = [s for s in signals if s.get('date') == date]
            
            # Update existing positions
            self._update_positions(date, price_data)
            
            # Check for new signals
            for signal in day_signals:
                if len(self.positions) < self.config.max_positions:
                    self._process_signal(signal, date, price_data)
            
            # Record equity
            total_equity = self._calculate_total_equity(date, price_data)
            self.equity_curve.append(total_equity)
            
            # Calculate daily return
            if i > 0:
                daily_return = (total_equity - self.equity_curve[-2]) / self.equity_curve[-2]
                self.daily_returns.append(daily_return)
        
        # Close all remaining positions
        final_date = dates[-1]
        self._close_all_positions(final_date, price_data)
        
        # Generate report
        return self._generate_report()
    
    def _process_signal(self, signal: Dict, date: datetime, price_data: pd.DataFrame):
        """Process trading signal"""
        symbol = signal['symbol']
        action = signal['action']
        
        if symbol in self.positions:
            return  # Already have position
        
        # Get current price
        if date not in price_data.index or symbol not in price_data.columns:
            return
        
        current_price = price_data.loc[date, symbol]
        
        # Determine side
        if action in ['BUY', 'STRONG_BUY', 'WEAK_BUY']:
            side = 'long'
        elif action in ['SELL', 'STRONG_SELL', 'WEAK_SELL']:
            if not self.config.short_selling_allowed:
                return
            side = 'short'
        else:
            return
        
        # Calculate position size
        position_value = self.capital * self.config.position_size_pct
        quantity = position_value / current_price
        
        # Apply commission and slippage
        commission = quantity * current_price * self.config.commission_rate
        slippage = quantity * current_price * self.config.slippage_rate
        
        # Adjust entry price for slippage
        if side == 'long':
            entry_price = current_price * (1 + self.config.slippage_rate)
        else:
            entry_price = current_price * (1 - self.config.slippage_rate)
        
        # Create trade
        trade = Trade(
            symbol=symbol,
            entry_date=date,
            exit_date=None,
            entry_price=entry_price,
            exit_price=None,
            quantity=quantity,
            side=side,
            commission=commission,
            slippage=slippage
        )
        
        # Open position
        self.positions[symbol] = {
            'quantity': quantity,
            'entry_price': entry_price,
            'side': side,
            'entry_date': date,
            'stop_loss': entry_price * (1 - self.config.stop_loss_pct) if side == 'long' else entry_price * (1 + self.config.stop_loss_pct),
            'take_profit': entry_price * (1 + self.config.take_profit_pct) if side == 'long' else entry_price * (1 - self.config.take_profit_pct)
        }
        
        self.open_trades[symbol] = trade
        self.capital -= commission + slippage
        
        print(f"📈 OPENED {side.upper()} {symbol} @ ${entry_price:.2f} | Qty: {quantity:.4f}")
    
    def _update_positions(self, date: datetime, price_data: pd.DataFrame):
        """Update and check existing positions"""
        symbols_to_close = []
        
        for symbol, pos in self.positions.items():
            if date not in price_data.index or symbol not in price_data.columns:
                continue
            
            current_price = price_data.loc[date, symbol]
            
            # Update max profit/loss for open trade
            if symbol in self.open_trades:
                trade = self.open_trades[symbol]
                if pos['side'] == 'long':
                    unrealized_pnl = (current_price - pos['entry_price']) * pos['quantity']
                    trade.max_profit = max(trade.max_profit, unrealized_pnl)
                    trade.max_loss = min(trade.max_loss, unrealized_pnl)
                else:
                    unrealized_pnl = (pos['entry_price'] - current_price) * pos['quantity']
                    trade.max_profit = max(trade.max_profit, unrealized_pnl)
                    trade.max_loss = min(trade.max_loss, unrealized_pnl)
            
            # Check stop loss
            if pos['side'] == 'long' and current_price <= pos['stop_loss']:
                symbols_to_close.append((symbol, current_price, 'Stop Loss'))
            elif pos['side'] == 'short' and current_price >= pos['stop_loss']:
                symbols_to_close.append((symbol, current_price, 'Stop Loss'))
            
            # Check take profit
            elif pos['side'] == 'long' and current_price >= pos['take_profit']:
                symbols_to_close.append((symbol, current_price, 'Take Profit'))
            elif pos['side'] == 'short' and current_price <= pos['take_profit']:
                symbols_to_close.append((symbol, current_price, 'Take Profit'))
        
        # Close positions
        for symbol, price, reason in symbols_to_close:
            self._close_position(symbol, price, date, reason)
    
    def _close_position(self, symbol: str, current_price: float, date: datetime, reason: str):
        """Close a position"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        trade = self.open_trades.get(symbol)
        
        # Calculate PnL
        if pos['side'] == 'long':
            pnl = (current_price - pos['entry_price']) * pos['quantity']
        else:
            pnl = (pos['entry_price'] - current_price) * pos['quantity']
        
        # Exit costs
        exit_commission = pos['quantity'] * current_price * self.config.commission_rate
        exit_slippage = pos['quantity'] * current_price * self.config.slippage_rate
        
        # Net PnL
        net_pnl = pnl - exit_commission - exit_slippage
        pnl_percent = net_pnl / (pos['entry_price'] * abs(pos['quantity'])) * 100
        
        # Update trade
        if trade:
            trade.exit_date = date
            trade.exit_price = current_price
            trade.pnl = net_pnl
            trade.pnl_percent = pnl_percent
            trade.commission += exit_commission
            trade.slippage += exit_slippage
            trade.holding_period = (date - trade.entry_date).days
            trade.exit_reason = reason
            
            self.closed_trades.append(trade)
            del self.open_trades[symbol]
        
        # Update capital
        self.capital += net_pnl - exit_commission - exit_slippage
        
        # Remove position
        del self.positions[symbol]
        
        print(f"❌ CLOSED {symbol} @ ${current_price:.2f} | PnL: ${net_pnl:.2f} ({pnl_percent:+.2f}%) | Reason: {reason}")
    
    def _close_all_positions(self, date: datetime, price_data: pd.DataFrame):
        """Close all remaining positions at end of backtest"""
        for symbol in list(self.positions.keys()):
            if date in price_data.index and symbol in price_data.columns:
                current_price = price_data.loc[date, symbol]
                self._close_position(symbol, current_price, date, 'End of Backtest')
    
    def _calculate_total_equity(self, date: datetime, price_data: pd.DataFrame) -> float:
        """Calculate total equity including open positions"""
        equity = self.capital
        
        for symbol, pos in self.positions.items():
            if date in price_data.index and symbol in price_data.columns:
                current_price = price_data.loc[date, symbol]
                if pos['side'] == 'long':
                    equity += (current_price - pos['entry_price']) * pos['quantity']
                else:
                    equity += (pos['entry_price'] - current_price) * pos['quantity']
        
        return equity
    
    def _generate_report(self) -> Dict:
        """Generate comprehensive backtest report"""
        if not self.closed_trades:
            return {"error": "No trades executed"}
        
        # Basic metrics
        total_trades = len(self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        # PnL metrics
        total_pnl = sum(t.pnl for t in self.closed_trades)
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        avg_trade = total_pnl / total_trades if total_trades > 0 else 0
        
        # Return metrics
        final_equity = self.equity_curve[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # Annualized return (assuming 252 trading days)
        n_days = len(self.equity_curve)
        annualized_return = ((final_equity / self.initial_capital) ** (252 / n_days) - 1) * 100 if n_days > 0 else 0
        
        # Risk metrics
        if len(self.daily_returns) > 1:
            volatility = np.std(self.daily_returns) * np.sqrt(252)
            sharpe_ratio = np.mean(self.daily_returns) / (np.std(self.daily_returns) + 1e-6) * np.sqrt(252)
            
            # Sortino ratio
            negative_returns = [r for r in self.daily_returns if r < 0]
            downside_dev = np.std(negative_returns) * np.sqrt(252) if negative_returns else 0
            sortino_ratio = np.mean(self.daily_returns) / (downside_dev + 1e-6) * np.sqrt(252) if downside_dev > 0 else 0
            
            # Maximum drawdown
            peak = self.equity_curve[0]
            max_drawdown = 0
            for equity in self.equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Calmar ratio
            calmar_ratio = annualized_return / (max_drawdown * 100) if max_drawdown > 0 else 0
            
            # VaR and CVaR
            var_95 = np.percentile(self.daily_returns, 5)
            cvar_95 = np.mean([r for r in self.daily_returns if r <= var_95]) if any(r <= var_95 for r in self.daily_returns) else var_95
        else:
            volatility = sharpe_ratio = sortino_ratio = max_drawdown = calmar_ratio = var_95 = cvar_95 = 0
        
        # Holding period
        avg_holding_period = np.mean([t.holding_period for t in self.closed_trades]) if self.closed_trades else 0
        
        # Build report
        report = {
            "summary": {
                "initial_capital": self.initial_capital,
                "final_equity": final_equity,
                "total_pnl": total_pnl,
                "total_return_pct": total_return,
                "annualized_return_pct": annualized_return
            },
            "trade_statistics": {
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate_pct": win_rate,
                "avg_trade_pnl": avg_trade,
                "avg_winning_trade": avg_win,
                "avg_losing_trade": avg_loss,
                "profit_factor": profit_factor,
                "avg_holding_period_days": avg_holding_period
            },
            "risk_metrics": {
                "volatility_annual_pct": volatility * 100,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "max_drawdown_pct": max_drawdown * 100,
                "calmar_ratio": calmar_ratio,
                "var_95_pct": var_95 * 100,
                "cvar_95_pct": cvar_95 * 100
            },
            "costs": {
                "total_commissions": sum(t.commission for t in self.closed_trades),
                "total_slippage": sum(t.slippage for t in self.closed_trades)
            },
            "equity_curve": self.equity_curve,
            "daily_returns": self.daily_returns,
            "trades": [t.to_dict() for t in self.closed_trades]
        }
        
        # Print report
        self._print_report(report)
        
        return report
    
    def _print_report(self, report: Dict):
        """Print formatted backtest report"""
        print("\n" + "="*80)
        print("📊 BACKTEST RESULTS")
        print("="*80)
        
        summary = report['summary']
        print(f"\n💰 CAPITAL:")
        print(f"   Initial: ${summary['initial_capital']:,.2f}")
        print(f"   Final: ${summary['final_equity']:,.2f}")
        print(f"   Total P&L: ${summary['total_pnl']:,.2f}")
        print(f"   Total Return: {summary['total_return_pct']:+.2f}%")
        print(f"   Annualized Return: {summary['annualized_return_pct']:+.2f}%")
        
        stats = report['trade_statistics']
        print(f"\n📈 TRADE STATISTICS:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Winners: {stats['winning_trades']} | Losers: {stats['losing_trades']}")
        print(f"   Win Rate: {stats['win_rate_pct']:.1f}%")
        print(f"   Profit Factor: {stats['profit_factor']:.2f}")
        print(f"   Avg Trade: ${stats['avg_trade_pnl']:.2f}")
        print(f"   Avg Winner: ${stats['avg_winning_trade']:.2f}")
        print(f"   Avg Loser: ${stats['avg_losing_trade']:.2f}")
        print(f"   Avg Holding Period: {stats['avg_holding_period_days']:.1f} days")
        
        risk = report['risk_metrics']
        print(f"\n⚠️ RISK METRICS:")
        print(f"   Volatility: {risk['volatility_annual_pct']:.1f}%")
        print(f"   Sharpe Ratio: {risk['sharpe_ratio']:.2f}")
        print(f"   Sortino Ratio: {risk['sortino_ratio']:.2f}")
        print(f"   Max Drawdown: {risk['max_drawdown_pct']:.1f}%")
        print(f"   Calmar Ratio: {risk['calmar_ratio']:.2f}")
        print(f"   VaR (95%): {risk['var_95_pct']:.2f}%")
        print(f"   CVaR (95%): {risk['cvar_95_pct']:.2f}%")
        
        costs = report['costs']
        print(f"\n💸 COSTS:")
        print(f"   Total Commissions: ${costs['total_commissions']:.2f}")
        print(f"   Total Slippage: ${costs['total_slippage']:.2f}")
        
        print("\n" + "="*80)
        print("✅ BACKTEST COMPLETED")
        print("="*80 + "\n")


def demo_backtest():
    """Demonstrate backtesting engine"""
    print("\n🔬 RUNNING BACKTEST DEMO...\n")
    
    # Generate synthetic price data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252, freq='B')
    
    # Generate prices for multiple symbols
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA']
    price_data = {}
    
    for symbol in symbols:
        base_price = np.random.uniform(150, 500)
        returns = np.random.normal(0.0005, 0.02, 252)  # Positive drift
        prices = base_price * np.exp(np.cumsum(returns))
        price_data[symbol] = prices
    
    # Create DataFrame
    df = pd.DataFrame(price_data, index=dates)
    
    # Generate synthetic signals
    signals = []
    for i, date in enumerate(dates[:-10]):  # Leave room for holding period
        for symbol in symbols:
            # Random signals with slight bullish bias
            if np.random.random() < 0.1:  # 10% chance of signal
                action = np.random.choice(['BUY', 'SELL'], p=[0.7, 0.3])
                signals.append({
                    'date': date,
                    'symbol': symbol,
                    'action': action,
                    'confidence': np.random.uniform(0.6, 0.95)
                })
    
    # Configure and run backtest
    config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.001,
        slippage_rate=0.0005,
        position_size_pct=0.1,
        max_positions=5,
        stop_loss_pct=0.02,
        take_profit_pct=0.04
    )
    
    backtester = AdvancedBacktester(config)
    results = backtester.run_backtest(signals, df)
    
    return results


if __name__ == "__main__":
    demo_backtest()
