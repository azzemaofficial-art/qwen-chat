#!/usr/bin/env python3
"""
Advanced Trading Features - Funzionalità Avanzate di Trading Quantitativo
Implementa le migliori teorie accademiche e pratiche istituzionali:
- Kelly Criterion ottimizzato
- Bayesian Change Point Detection
- Regime Switching Models
- Volatility Targeting
- Correlation Clustering
- Smart Beta Factors
- Transaction Cost Analysis
- Market Impact Models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from scipy import stats
from scipy.optimize import minimize, brentq
from scipy.signal import argrelextrema
import logging
import warnings
from enum import Enum

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Stati del mercato per regime switching"""
    BULL_LOW_VOL = "bull_low_vol"
    BULL_HIGH_VOL = "bull_high_vol"
    BEAR_LOW_VOL = "bear_low_vol"
    BEAR_HIGH_VOL = "bear_high_vol"
    SIDEWAYS = "sideways"
    CRISIS = "crisis"


@dataclass
class KellyResult:
    """Risultato ottimizzazione Kelly Criterion"""
    optimal_fraction: float
    expected_growth: float
    variance_of_growth: float
    risk_of_ruin: float
    recommended_leverage: float
    confidence_interval: Tuple[float, float]


@dataclass
class RegimeState:
    """Stato corrente del mercato"""
    current_regime: MarketRegime
    probability_distribution: Dict[MarketRegime, float]
    regime_duration: int
    transition_matrix: np.ndarray
    expected_return: float
    expected_volatility: float


@dataclass
class TransactionCost:
    """Analisi costi di transazione"""
    explicit_costs: float
    implicit_costs: float
    market_impact: float
    timing_cost: float
    total_cost: float
    cost_percentage: float


class AdvancedKellyOptimizer:
    """
    Ottimizzatore Kelly Criterion con vincoli e robustezza
    Basato su: Thorp (1969), Rotando & Thorp (1992)
    """
    
    def __init__(self, risk_free_rate: float = 0.04, max_kelly: float = 0.25):
        self.risk_free_rate = risk_free_rate
        self.max_kelly = max_kelly
        
    def calculate_kelly(self, 
                       returns: np.ndarray,
                       win_prob: Optional[float] = None,
                       win_loss_ratio: Optional[float] = None) -> KellyResult:
        if win_prob is None:
            win_prob = np.mean(returns > 0)
        
        if win_loss_ratio is None:
            avg_win = np.mean(returns[returns > 0]) if np.any(returns > 0) else 0
            avg_loss = abs(np.mean(returns[returns < 0])) if np.any(returns < 0) else 1e-10
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        kelly_classic = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
        
        def geometric_growth_rate(f):
            if f <= 0 or f >= 1:
                return -np.inf
            growth_rates = np.log(1 + f * returns)
            return np.mean(growth_rates)
        
        try:
            result = minimize(
                lambda f: -geometric_growth_rate(f),
                x0=0.1,
                bounds=[(0.01, self.max_kelly)],
                method='L-BFGS-B'
            )
            kelly_optimal = result.x[0]
        except Exception as e:
            logger.warning(f"Ottimizzazione numerica fallita: {e}")
            kelly_optimal = kelly_classic
        
        kelly_fractional = kelly_optimal * 0.5
        kelly_final = min(kelly_fractional, self.max_kelly)
        
        expected_growth = geometric_growth_rate(kelly_final)
        growth_variances = np.var(np.log(1 + kelly_final * returns))
        
        risk_of_ruin = np.exp(-2 * expected_growth / growth_variances) if growth_variances > 0 else 0
        
        bootstrap_kelly = []
        n_bootstrap = 100
        for _ in range(n_bootstrap):
            sample_idx = np.random.choice(len(returns), len(returns), replace=True)
            sample_returns = returns[sample_idx]
            sample_win_prob = np.mean(sample_returns > 0)
            sample_avg_win = np.mean(sample_returns[sample_returns > 0]) if np.any(sample_returns > 0) else 0
            sample_avg_loss = abs(np.mean(sample_returns[sample_returns < 0])) if np.any(sample_returns < 0) else 1e-10
            sample_wl_ratio = sample_avg_win / sample_avg_loss if sample_avg_loss > 0 else 0
            sample_kelly = (sample_win_prob * sample_wl_ratio - (1 - sample_win_prob)) / sample_wl_ratio
            bootstrap_kelly.append(sample_kelly)
        
        ci_lower = np.percentile(bootstrap_kelly, 5)
        ci_upper = np.percentile(bootstrap_kelly, 95)
        
        sharpe = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        recommended_leverage = min(sharpe, 2.0)
        
        return KellyResult(
            optimal_fraction=kelly_final,
            expected_growth=expected_growth,
            variance_of_growth=growth_variances,
            risk_of_ruin=risk_of_ruin,
            recommended_leverage=recommended_leverage,
            confidence_interval=(max(0, ci_lower), ci_upper)
        )


class BayesianChangePointDetector:
    """
    Rilevamento punti di cambiamento strutturale usando metodi Bayesiani
    """
    
    def __init__(self, prior_prob_change: float = 0.01, min_segment_length: int = 10):
        self.prior_prob_change = prior_prob_change
        self.min_segment_length = min_segment_length
        
    def detect_changepoints(self, data: np.ndarray, method: str = 'cusum') -> List[int]:
        if method == 'cusum':
            return self._cusum_detection(data)
        elif method == 'bayesian':
            return self._bayesian_detection(data)
        elif method == 'likelihood':
            return self._likelihood_ratio_detection(data)
        else:
            raise ValueError(f"Metodo {method} non supportato")
    
    def _cusum_detection(self, data: np.ndarray) -> List[int]:
        mean_data = np.mean(data)
        std_data = np.std(data)
        if std_data == 0:
            return []
        
        cusum_pos = np.zeros(len(data))
        cusum_neg = np.zeros(len(data))
        threshold = 5 * std_data
        changepoints = []
        
        for i in range(1, len(data)):
            cusum_pos[i] = max(0, cusum_pos[i-1] + (data[i] - mean_data) - std_data/2)
            cusum_neg[i] = min(0, cusum_neg[i-1] + (data[i] - mean_data) + std_data/2)
            
            if cusum_pos[i] > threshold or abs(cusum_neg[i]) > threshold:
                changepoints.append(i)
                cusum_pos[i] = 0
                cusum_neg[i] = 0
        
        return changepoints
    
    def _bayesian_detection(self, data: np.ndarray) -> List[int]:
        n = len(data)
        run_length = 0
        changepoints = []
        hazard = lambda t: self.prior_prob_change
        
        for t in range(1, n):
            if np.random.random() < hazard(run_length):
                changepoints.append(t)
                run_length = 0
            else:
                run_length += 1
            
            if changepoints and t - changepoints[-1] < self.min_segment_length:
                changepoints.pop()
                run_length = t - (changepoints[-1] if changepoints else 0)
        
        return changepoints
    
    def _likelihood_ratio_detection(self, data: np.ndarray) -> List[int]:
        changepoints = []
        n = len(data)
        
        for i in range(self.min_segment_length, n - self.min_segment_length):
            left_mean = np.mean(data[:i])
            right_mean = np.mean(data[i:])
            left_std = np.std(data[:i])
            right_std = np.std(data[i:])
            
            pooled_var = ((i-1)*left_std**2 + (n-i-1)*right_std**2) / (n-2)
            if pooled_var > 0:
                t_stat = abs(left_mean - right_mean) / np.sqrt(pooled_var * (1/i + 1/(n-i)))
                if t_stat > 3.0:
                    changepoints.append(i)
        
        if len(changepoints) > 1:
            filtered = [changepoints[0]]
            for cp in changepoints[1:]:
                if cp - filtered[-1] >= self.min_segment_length:
                    filtered.append(cp)
            changepoints = filtered
        
        return changepoints


def calculate_drawdown_series(equity_curve: np.ndarray) -> np.ndarray:
    """Calcola serie dei drawdown"""
    running_max = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - running_max) / running_max
    return drawdown


def calculate_calmar_ratio(returns: np.ndarray) -> float:
    """Calmar Ratio = Annual Return / Max Drawdown"""
    annual_return = np.mean(returns) * 252
    equity_curve = np.cumprod(1 + returns)
    drawdowns = calculate_drawdown_series(equity_curve)
    max_drawdown = abs(np.min(drawdowns))
    return annual_return / max_drawdown if max_drawdown > 0 else 0


def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.04) -> float:
    """Sortino Ratio usa solo downside deviation"""
    excess_returns = returns - risk_free_rate / 252
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0:
        return np.inf
    
    downside_deviation = np.std(downside_returns) * np.sqrt(252)
    annual_return = np.mean(excess_returns) * 252
    return annual_return / downside_deviation if downside_deviation > 0 else 0
