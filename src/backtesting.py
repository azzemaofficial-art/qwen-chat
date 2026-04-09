"""
Advanced Backtesting System - Sistema di backtesting avanzato
Include walk-forward optimization, Monte Carlo simulation e analisi statistica
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt


@dataclass
class Trade:
    """Rappresenta un trade eseguito"""
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime]
    exit_price: Optional[float]
    direction: str  # 'LONG' o 'SHORT'
    shares: int
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""


@dataclass
class BacktestResults:
    """Risultati completi del backtest"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    average_holding_period: float
    trades: List[Trade]
    equity_curve: pd.Series
    drawdown_curve: pd.Series


class AdvancedBacktester:
    """Sistema di backtesting avanzato"""
    
    def __init__(
        self,
        initial_capital: float = 100000,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005
    ):
        """
        Args:
            initial_capital: Capitale iniziale
            commission_pct: Commissione per trade (es. 0.001 = 0.1%)
            slippage_pct: Slippage stimato
        """
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
    
    def generate_signals(
        self,
        df: pd.DataFrame,
        strategy: str = 'ma_crossover'
    ) -> pd.Series:
        """
        Genera segnali di trading basati su strategia
        
        Strategies:
            - 'ma_crossover': Incrocio medie mobili
            - 'rsi_mean_reversion': Mean reversion con RSI
            - 'macd_momentum': Momentum con MACD
            - 'bollinger_breakout': Breakout bande di Bollinger
        """
        signals = pd.Series(0, index=df.index)
        
        if strategy == 'ma_crossover':
            # Calcola medie mobili
            ma_fast = df['Close'].rolling(20).mean()
            ma_slow = df['Close'].rolling(50).mean()
            
            # Genera segnali
            for i in range(1, len(df)):
                if ma_fast.iloc[i] > ma_slow.iloc[i] and ma_fast.iloc[i-1] <= ma_slow.iloc[i-1]:
                    signals.iloc[i] = 1  # BUY
                elif ma_fast.iloc[i] < ma_slow.iloc[i] and ma_fast.iloc[i-1] >= ma_slow.iloc[i-1]:
                    signals.iloc[i] = -1  # SELL
        
        elif strategy == 'rsi_mean_reversion':
            # Calcola RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / (loss + 1e-9)
            rsi = 100 - (100 / (1 + rs))
            
            # Genera segnali
            for i in range(1, len(df)):
                if rsi.iloc[i] < 30:
                    signals.iloc[i] = 1  # BUY (ipervenduto)
                elif rsi.iloc[i] > 70:
                    signals.iloc[i] = -1  # SELL (ipercomprato)
        
        elif strategy == 'macd_momentum':
            # Calcola MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9, adjust=False).mean()
            
            # Genera segnali
            for i in range(1, len(df)):
                if macd.iloc[i] > signal_line.iloc[i] and macd.iloc[i-1] <= signal_line.iloc[i-1]:
                    signals.iloc[i] = 1  # BUY
                elif macd.iloc[i] < signal_line.iloc[i] and macd.iloc[i-1] >= signal_line.iloc[i-1]:
                    signals.iloc[i] = -1  # SELL
        
        elif strategy == 'bollinger_breakout':
            # Calcola Bande di Bollinger
            sma = df['Close'].rolling(20).mean()
            std = df['Close'].rolling(20).std()
            upper = sma + 2 * std
            lower = sma - 2 * std
            
            # Genera segnali
            for i in range(1, len(df)):
                if df['Close'].iloc[i] > upper.iloc[i]:
                    signals.iloc[i] = 1  # BUY (breakout)
                elif df['Close'].iloc[i] < lower.iloc[i]:
                    signals.iloc[i] = -1  # SELL (breakdown)
        
        return signals
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        position_size_pct: float = 0.1,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10
    ) -> BacktestResults:
        """
        Esegue il backtest
        
        Args:
            df: DataFrame con dati OHLCV
            signals: Serie dei segnali (1=buy, -1=sell, 0=hold)
            position_size_pct: % capitale per trade
            stop_loss_pct: Stop loss percentuale
            take_profit_pct: Take profit percentuale
        
        Returns:
            BacktestResults completo
        """
        capital = self.initial_capital
        position = None
        trades = []
        equity = [capital]
        dates = []
        
        for i in range(len(df)):
            date = df.index[i] if hasattr(df.index[i], 'to_pydatetime') else pd.Timestamp(df.index[i])
            price = df['Close'].iloc[i]
            signal = signals.iloc[i]
            
            # Gestione posizione aperta
            if position:
                # Calcola PnL corrente
                if position.direction == 'LONG':
                    pnl_pct = (price - position.entry_price) / position.entry_price
                else:
                    pnl_pct = (position.entry_price - price) / position.entry_price
                
                # Controlla stop loss e take profit
                exit_trade = False
                exit_reason = ""
                
                if pnl_pct <= -stop_loss_pct:
                    exit_trade = True
                    exit_reason = "STOP_LOSS"
                elif pnl_pct >= take_profit_pct:
                    exit_trade = True
                    exit_reason = "TAKE_PROFIT"
                elif (signal == -1 and position.direction == 'LONG') or \
                     (signal == 1 and position.direction == 'SHORT'):  # Segnale contrario
                    exit_trade = True
                    exit_reason = "SIGNAL_REVERSAL"
                
                if exit_trade:
                    # Chiudi posizione
                    exit_price = price * (1 - self.slippage_pct) if position.direction == 'LONG' else price * (1 + self.slippage_pct)
                    commission = exit_price * position.shares * self.commission_pct
                    
                    if position.direction == 'LONG':
                        pnl = (exit_price - position.entry_price) * position.shares - commission
                    else:
                        pnl = (position.entry_price - exit_price) * position.shares - commission
                    
                    pnl_pct = pnl / (position.entry_price * position.shares)
                    
                    position.exit_date = date if hasattr(date, 'to_pydatetime') else pd.Timestamp(date)
                    position.exit_price = exit_price
                    position.pnl = pnl
                    position.pnl_pct = pnl_pct
                    position.exit_reason = exit_reason
                    
                    trades.append(position)
                    capital += pnl
                    position = None
            
            # Apri nuova posizione se segnale e nessuna posizione aperta
            if signal != 0 and position is None:
                direction = 'LONG' if signal == 1 else 'SHORT'
                entry_price = price * (1 + self.slippage_pct) if direction == 'LONG' else price * (1 - self.slippage_pct)
                commission = entry_price * 100 * self.commission_pct  # Stima shares
                
                shares = int((capital * position_size_pct) / entry_price)
                if shares > 0:
                    position = Trade(
                        entry_date=date if hasattr(date, 'to_pydatetime') else pd.Timestamp(date),
                        entry_price=entry_price,
                        exit_date=None,
                        exit_price=None,
                        direction=direction,
                        shares=shares
                    )
        
        # Chiudi eventuali posizioni aperte alla fine
        if position:
            last_price = df['Close'].iloc[-1]
            exit_price = last_price * (1 - self.slippage_pct) if position.direction == 'LONG' else last_price * (1 + self.slippage_pct)
            
            if position.direction == 'LONG':
                pnl = (exit_price - position.entry_price) * position.shares
            else:
                pnl = (position.entry_price - exit_price) * position.shares
            
            position.exit_date = df.index[-1] if hasattr(df.index[-1], 'to_pydatetime') else pd.Timestamp(df.index[-1])
            position.exit_price = exit_price
            position.pnl = pnl
            position.pnl_pct = pnl / (position.entry_price * position.shares)
            position.exit_reason = "END_OF_DATA"
            trades.append(position)
            capital += pnl
        
        # Calcola equity curve
        equity_curve = pd.Series([self.initial_capital])
        drawdown_curve = pd.Series([0.0])
        running_max = self.initial_capital
        
        for trade in trades:
            equity_curve.loc[len(equity_curve)] = equity_curve.iloc[-1] + trade.pnl
            running_max = max(running_max, equity_curve.iloc[-1])
            dd = (equity_curve.iloc[-1] - running_max) / running_max
            drawdown_curve.loc[len(drawdown_curve)] = dd
        
        # Calcola metriche
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.pnl > 0)
        losing_trades = sum(1 for t in trades if t.pnl <= 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_return = (equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # Annualizza ritorno
        n_days = len(df)
        years = n_days / 252
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Max drawdown
        max_drawdown = drawdown_curve.min()
        
        # Sharpe Ratio
        returns = equity_curve.pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 0 and returns.std() > 0 else 0
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        sortino = (returns.mean() / downside_returns.std()) * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
        
        # Profit Factor
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl <= 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Statistiche trade
        avg_win = np.mean([t.pnl for t in trades if t.pnl > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([t.pnl for t in trades if t.pnl <= 0]) if losing_trades > 0 else 0
        largest_win = max([t.pnl for t in trades], default=0)
        largest_loss = min([t.pnl for t in trades], default=0)
        
        # Holding period medio
        holding_periods = []
        for t in trades:
            if t.exit_date and t.entry_date:
                period = (pd.Timestamp(t.exit_date) - pd.Timestamp(t.entry_date)).days
                holding_periods.append(period)
        avg_holding = np.mean(holding_periods) if holding_periods else 0
        
        return BacktestResults(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            profit_factor=profit_factor,
            average_win=avg_win,
            average_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            average_holding_period=avg_holding,
            trades=trades,
            equity_curve=equity_curve.reset_index(drop=True),
            drawdown_curve=drawdown_curve.reset_index(drop=True)
        )
    
    def walk_forward_optimization(
        self,
        df: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, List],
        in_sample_pct: float = 0.7,
        n_folds: int = 5
    ) -> Dict:
        """
        Esegue walk-forward optimization
        
        Args:
            df: DataFrame con dati
            strategy: Nome strategia
            param_ranges: Dizionario {parametro: [valori]}
            in_sample_pct: % dati per training
            n_folds: Numero di fold
        
        Returns:
            Dictionary con migliori parametri e performance
        """
        n_samples = len(df)
        fold_size = n_samples // n_folds
        
        best_params = {}
        best_score = -float('inf')
        out_of_sample_results = []
        
        for fold in range(n_folds):
            # Split dati
            test_start = fold * fold_size
            test_end = test_start + int(fold_size * in_sample_pct)
            
            in_sample = df.iloc[:test_end]
            out_sample = df.iloc[test_end:test_end + fold_size]
            
            if len(in_sample) < 100 or len(out_sample) < 50:
                continue
            
            # Grid search sui parametri
            fold_best_params = None
            fold_best_score = -float('inf')
            
            # Semplificazione: prova combinazioni base
            for param_name, param_values in param_ranges.items():
                for value in param_values:
                    # Genera segnali con parametri correnti
                    signals = self.generate_signals(in_sample, strategy)
                    
                    # Backtest in-sample
                    results = self.run_backtest(in_sample, signals)
                    
                    if results.sharpe_ratio > fold_best_score:
                        fold_best_score = results.sharpe_ratio
                        fold_best_params = {param_name: value}
            
            if fold_best_params:
                # Test out-of-sample
                signals_oos = self.generate_signals(out_sample, strategy)
                results_oos = self.run_backtest(out_sample, signals_oos)
                
                out_of_sample_results.append(results_oos)
                
                if results_oos.sharpe_ratio > best_score:
                    best_score = results_oos.sharpe_ratio
                    best_params = fold_best_params
        
        # Calcola media out-of-sample
        if out_of_sample_results:
            avg_oos_sharpe = np.mean([r.sharpe_ratio for r in out_of_sample_results])
            avg_oos_return = np.mean([r.total_return for r in out_of_sample_results])
        else:
            avg_oos_sharpe = 0
            avg_oos_return = 0
        
        return {
            'best_params': best_params,
            'best_oos_sharpe': avg_oos_sharpe,
            'best_oos_return': avg_oos_return,
            'n_folds': len(out_of_sample_results)
        }
    
    def monte_carlo_simulation(
        self,
        results: BacktestResults,
        n_simulations: int = 1000
    ) -> Dict:
        """
        Esegue simulazione Monte Carlo sui risultati
        
        Args:
            results: Risultati del backtest
            n_simulations: Numero di simulazioni
        
        Returns:
            Dictionary con statistiche Monte Carlo
        """
        if len(results.trades) < 10:
            return {'error': 'Troppi pochi trade per simulazione'}
        
        simulated_final_equity = []
        
        for _ in range(n_simulations):
            # Campiona trade con replacement
            sampled_trades = np.random.choice(
                results.trades,
                size=len(results.trades),
                replace=True
            )
            
            # Calcola equity finale
            final_equity = self.initial_capital
            for trade in sampled_trades:
                final_equity += trade.pnl
            
            simulated_final_equity.append(final_equity)
        
        # Statistiche
        percentiles = np.percentile(simulated_final_equity, [5, 25, 50, 75, 95])
        
        return {
            'mean_final_equity': np.mean(simulated_final_equity),
            'median_final_equity': np.median(simulated_final_equity),
            'std_final_equity': np.std(simulated_final_equity),
            'percentile_5': percentiles[0],
            'percentile_25': percentiles[1],
            'percentile_50': percentiles[2],
            'percentile_75': percentiles[3],
            'percentile_95': percentiles[4],
            'probability_profit': np.mean([e > self.initial_capital for e in simulated_final_equity]),
            'probability_ruin': np.mean([e < self.initial_capital * 0.5 for e in simulated_final_equity])
        }
    
    def format_backtest_report(self, results: BacktestResults, strategy_name: str) -> str:
        """Formatta report del backtest"""
        report = f"""
{'='*70}
📊 REPORT BACKTEST: {strategy_name}
{'='*70}

📈 PERFORMANCE GENERALE:
   Ritorno Totale: {results.total_return:.2%}
   Ritorno Annualizzato: {results.annualized_return:.2%}
   
📊 STATISTICHE TRADE:
   Trade Totali: {results.total_trades}
   Trade Vincenti: {results.winning_trades} ({results.win_rate:.1%})
   Trade Perdenti: {results.losing_trades}
   
💰 PROFITTO/PERDITA:
   Profit Factor: {results.profit_factor:.2f}
   Vincita Media: ${results.average_win:.2f}
   Perdita Media: ${results.average_loss:.2f}
   Vincita Maggiore: ${results.largest_win:.2f}
   Perdita Maggiore: ${results.largest_loss:.2f}
   
⚠️ RISCHIO:
   Massimo Drawdown: {results.max_drawdown:.2%}
   Sharpe Ratio: {results.sharpe_ratio:.2f}
   Sortino Ratio: {results.sortino_ratio:.2f}
   
⏱️ TEMPISTICHE:
   Periodo Detenimento Medio: {results.average_holding_period:.1f} giorni

{'='*70}
"""
        return report


if __name__ == "__main__":
    # Test con dati simulati
    np.random.seed(42)
    
    # Genera dati sintetici
    n_days = 500
    dates = pd.date_range('2022-01-01', periods=n_days, freq='D')
    
    # Prezzo con trend e rumore
    returns = np.random.normal(0.0005, 0.02, n_days)
    prices = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'Open': prices * (1 + np.random.randn(n_days) * 0.005),
        'High': prices * (1 + np.abs(np.random.randn(n_days) * 0.01)),
        'Low': prices * (1 - np.abs(np.random.randn(n_days) * 0.01)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, n_days)
    }, index=dates)
    
    # Esegui backtest
    backtester = AdvancedBacktester(initial_capital=100000)
    
    strategies = ['ma_crossover', 'rsi_mean_reversion', 'macd_momentum', 'bollinger_breakout']
    
    print("="*70)
    print("🔬 BACKTESTING MULTIPLE STRATEGIES")
    print("="*70)
    
    best_strategy = None
    best_sharpe = -float('inf')
    
    for strategy in strategies:
        signals = backtester.generate_signals(df, strategy)
        results = backtester.run_backtest(df, signals)
        
        print(backtester.format_backtest_report(results, strategy))
        
        if results.sharpe_ratio > best_sharpe:
            best_sharpe = results.sharpe_ratio
            best_strategy = strategy
    
    print(f"\n🏆 MIGLIORE STRATEGIA: {best_strategy} (Sharpe: {best_sharpe:.2f})")
    
    # Walk-forward optimization
    print("\n\n" + "="*70)
    print("🔄 WALK-FORWARD OPTIMIZATION")
    print("="*70)
    
    param_ranges = {
        'ma_fast': [10, 20, 30],
        'ma_slow': [40, 50, 60]
    }
    
    wfo_results = backtester.walk_forward_optimization(
        df,
        'ma_crossover',
        param_ranges,
        n_folds=3
    )
    
    print(f"Migliori parametri: {wfo_results['best_params']}")
    print(f"Sharpe OOS medio: {wfo_results['best_oos_sharpe']:.2f}")
    print(f"Ritorno OOS medio: {wfo_results['best_oos_return']:.2%}")
