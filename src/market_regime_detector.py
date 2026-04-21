"""
Market Regime Detector - Hidden Markov Models & GARCH for State Detection
Identifies market regimes: Bull, Bear, Sideways, High Volatility, Crisis
Adapts trading strategies based on detected regime
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import warnings
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime states"""
    BULL_LOW_VOL = "bull_low_vol"      # Strong uptrend, low volatility
    BULL_HIGH_VOL = "bull_high_vol"    # Uptrend, high volatility
    BEAR_LOW_VOL = "bear_low_vol"      # Downtrend, low volatility
    BEAR_HIGH_VOL = "bear_high_vol"    # Strong downtrend, high volatility
    SIDEWAYS_LOW = "sideways_low"      # Range-bound, low volatility
    SIDEWAYS_HIGH = "sideways_high"    # Range-bound, high volatility
    CRISIS = "crisis"                  # Extreme volatility, crash
    TRANSITION = "transition"          # Changing regime


@dataclass
class RegimeState:
    """Current market regime state"""
    regime: MarketRegime
    probability: float
    start_date: datetime
    duration_days: int
    confidence: float
    volatility_level: float
    trend_strength: float
    recommended_action: str
    risk_multiplier: float


@dataclass
class RegimeTransition:
    """Probability of transitioning between regimes"""
    from_regime: MarketRegime
    to_regime: MarketRegime
    probability: float
    expected_duration: int


class HiddenMarkovModel:
    """
    Hidden Markov Model implementation for regime detection
    Uses Baum-Welch algorithm for parameter estimation
    Viterbi algorithm for state decoding
    """
    
    def __init__(self, n_states: int = 8, max_iterations: int = 100, tol: float = 1e-6):
        self.n_states = n_states
        self.max_iterations = max_iterations
        self.tol = tol
        
        # Model parameters (to be estimated)
        self.transition_matrix: Optional[np.ndarray] = None  # A
        self.emission_means: Optional[np.ndarray] = None     # μ
        self.emission_stds: Optional[np.ndarray] = None      # σ
        self.initial_probs: Optional[np.ndarray] = None      # π
        
        self.states_converged = False
        self.log_likelihood_history: List[float] = []
        
    def _initialize_parameters(self, observations: np.ndarray):
        """Initialize HMM parameters using K-means style initialization"""
        n_features = observations.shape[1] if len(observations.shape) > 1 else 1
        
        # Initialize transition matrix (random but row-stochastic)
        self.transition_matrix = np.random.dirichlet(np.ones(self.n_states), size=self.n_states)
        
        # Ensure diagonal dominance (states tend to persist)
        self.transition_matrix *= 0.7
        self.transition_matrix += np.eye(self.n_states) * 0.3
        self.transition_matrix /= self.transition_matrix.sum(axis=1, keepdims=True)
        
        # Initialize emission parameters using quantiles
        obs_flat = observations.flatten()
        percentiles = np.linspace(5, 95, self.n_states)
        self.emission_means = np.percentile(obs_flat, percentiles).reshape(-1, 1)
        self.emission_stds = np.ones((self.n_states, 1)) * np.std(obs_flat)
        
        # Initialize initial state probabilities
        self.initial_probs = np.ones(self.n_states) / self.n_states
        
    def _gaussian_emission_prob(self, observations: np.ndarray, state: int) -> np.ndarray:
        """Calculate Gaussian emission probability for a state"""
        mean = self.emission_means[state]
        std = self.emission_stds[state]
        
        if std < 1e-10:
            std = 1e-10
            
        if len(observations.shape) == 1:
            observations = observations.reshape(-1, 1)
            
        prob = np.prod(
            (1.0 / (np.sqrt(2 * np.pi) * std)) * 
            np.exp(-0.5 * ((observations - mean) / std) ** 2),
            axis=1
        )
        return prob
    
    def _forward_algorithm(self, observations: np.ndarray) -> Tuple[np.ndarray, float]:
        """Forward algorithm for calculating likelihood"""
        T = len(observations)
        N = self.n_states
        
        alpha = np.zeros((T, N))
        
        # Initialization
        emission_prob = self._gaussian_emission_prob(observations[0].flatten(), 0)
        alpha[0] = self.initial_probs * np.array([
            self._gaussian_emission_prob(observations[0].flatten(), s)[0] 
            for s in range(N)
        ])
        
        # Recursion
        for t in range(1, T):
            for j in range(N):
                alpha[t, j] = np.sum(alpha[t-1] * self.transition_matrix[:, j]) * \
                             self._gaussian_emission_prob(observations[t].flatten(), j)[0]
        
        # Total likelihood
        likelihood = np.sum(alpha[T-1])
        
        return alpha, likelihood
    
    def _backward_algorithm(self, observations: np.ndarray) -> np.ndarray:
        """Backward algorithm for calculating posterior probabilities"""
        T = len(observations)
        N = self.n_states
        
        beta = np.zeros((T, N))
        beta[T-1] = 1.0
        
        # Recursion
        for t in range(T-2, -1, -1):
            for i in range(N):
                beta[t, i] = np.sum(
                    self.transition_matrix[i, :] * 
                    np.array([
                        self._gaussian_emission_prob(observations[t+1].flatten(), j)[0] 
                        for j in range(N)
                    ]) * 
                    beta[t+1]
                )
        
        return beta
    
    def _viterbi_algorithm(self, observations: np.ndarray) -> np.ndarray:
        """Viterbi algorithm for finding most likely state sequence"""
        T = len(observations)
        N = self.n_states
        
        delta = np.zeros((T, N))
        psi = np.zeros((T, N), dtype=int)
        
        # Initialization
        delta[0] = np.log(self.initial_probs + 1e-300) + np.log(np.array([
            self._gaussian_emission_prob(observations[0].flatten(), s)[0] + 1e-300
            for s in range(N)
        ]))
        
        # Recursion
        for t in range(1, T):
            for j in range(N):
                trans_probs = np.log(self.transition_matrix[:, j] + 1e-300)
                candidates = delta[t-1] + trans_probs
                psi[t, j] = np.argmax(candidates)
                delta[t, j] = candidates[psi[t, j]] + np.log(
                    self._gaussian_emission_prob(observations[t].flatten(), j)[0] + 1e-300
                )
        
        # Backtracking
        states = np.zeros(T, dtype=int)
        states[T-1] = np.argmax(delta[T-1])
        
        for t in range(T-2, -1, -1):
            states[t] = psi[t+1, states[t+1]]
        
        return states
    
    def fit(self, observations: np.ndarray, verbose: bool = False) -> 'HiddenMarkovModel':
        """
        Fit HMM using Baum-Welch (EM) algorithm
        
        Parameters
        ----------
        observations : np.ndarray
            Time series observations (returns, volatility, etc.)
        verbose : bool
            Print convergence information
            
        Returns
        -------
        self : HiddenMarkovModel
            Fitted model
        """
        if len(observations.shape) == 1:
            observations = observations.reshape(-1, 1)
        
        self._initialize_parameters(observations)
        
        prev_log_likelihood = -np.inf
        self.log_likelihood_history = []
        
        for iteration in range(self.max_iterations):
            # E-step: Calculate forward-backward probabilities
            alpha, likelihood = self._forward_algorithm(observations)
            beta = self._backward_algorithm(observations)
            
            log_likelihood = np.log(likelihood + 1e-300)
            self.log_likelihood_history.append(log_likelihood)
            
            # Check convergence
            if abs(log_likelihood - prev_log_likelihood) < self.tol:
                self.states_converged = True
                if verbose:
                    logger.info(f"Converged at iteration {iteration}")
                break
            
            prev_log_likelihood = log_likelihood
            
            # M-step: Update parameters (simplified version)
            T = len(observations)
            N = self.n_states
            
            # Calculate gamma (posterior state probabilities)
            gamma = (alpha * beta) / (np.sum(alpha * beta, axis=1, keepdims=True) + 1e-300)
            
            # Update initial probabilities
            self.initial_probs = gamma[0] + 1e-300
            self.initial_probs /= np.sum(self.initial_probs)
            
            # Update transition matrix
            xi = np.zeros((T-1, N, N))
            for t in range(T-1):
                denom = 0
                for i in range(N):
                    for j in range(N):
                        xi[t, i, j] = (alpha[t, i] * self.transition_matrix[i, j] * 
                                      self._gaussian_emission_prob(observations[t+1].flatten(), j)[0] * 
                                      beta[t+1, j])
                        denom += xi[t, i, j]
                
                if denom > 1e-300:
                    xi[t] /= denom
            
            self.transition_matrix = np.sum(xi, axis=0)
            self.transition_matrix /= (np.sum(self.transition_matrix, axis=1, keepdims=True) + 1e-300)
            
            # Update emission parameters
            for k in range(N):
                numerator = np.sum(gamma[:, k] * observations.flatten())
                denominator = np.sum(gamma[:, k])
                if denominator > 1e-300:
                    self.emission_means[k] = numerator / denominator
                    
                    variance_num = np.sum(gamma[:, k] * (observations.flatten() - self.emission_means[k])**2)
                    self.emission_stds[k] = np.sqrt(variance_num / denominator + 1e-10)
        
        return self
    
    def predict(self, observations: np.ndarray) -> np.ndarray:
        """Predict most likely state sequence"""
        if len(observations.shape) == 1:
            observations = observations.reshape(-1, 1)
        return self._viterbi_algorithm(observations)
    
    def predict_proba(self, observations: np.ndarray) -> np.ndarray:
        """Predict state probabilities"""
        if len(observations.shape) == 1:
            observations = observations.reshape(-1, 1)
        
        alpha, _ = self._forward_algorithm(observations)
        beta = self._backward_algorithm(observations)
        
        gamma = (alpha * beta) / (np.sum(alpha * beta, axis=1, keepdims=True) + 1e-300)
        return gamma


class GARCHModel:
    """
    GARCH(1,1) model for volatility forecasting
    Generalized Autoregressive Conditional Heteroskedasticity
    """
    
    def __init__(self, p: int = 1, q: int = 1):
        self.p = p
        self.q = q
        self.omega: Optional[float] = None  # Constant term
        self.alpha: Optional[np.ndarray] = None  # ARCH terms
        self.beta: Optional[np.ndarray] = None  # GARCH terms
        self.residuals: Optional[np.ndarray] = None
        self.volatility_forecast: Optional[np.ndarray] = None
        
    def fit(self, returns: np.ndarray, max_iterations: int = 1000, tol: float = 1e-8) -> 'GARCHModel':
        """
        Fit GARCH model using Maximum Likelihood Estimation
        
        Parameters
        ----------
        returns : np.ndarray
            Return series
        max_iterations : int
            Maximum iterations for optimization
        tol : float
            Convergence tolerance
            
        Returns
        -------
        self : GARCHModel
            Fitted model
        """
        n = len(returns)
        
        # Initial parameter estimates
        self.omega = np.var(returns) * 0.1
        self.alpha = np.array([0.1])
        self.beta = np.array([0.8])
        
        # Ensure stationarity: alpha + beta < 1
        if self.alpha[0] + self.beta[0] >= 0.99:
            self.alpha[0] = 0.1
            self.beta[0] = 0.8
        
        # Iterative optimization (simplified MLE)
        prev_params = [self.omega, self.alpha.copy(), self.beta.copy()]
        
        for iteration in range(max_iterations):
            # Calculate conditional variances
            sigma_squared = np.zeros(n)
            sigma_squared[0] = np.var(returns)
            
            for t in range(1, n):
                sigma_squared[t] = (self.omega + 
                                   self.alpha[0] * returns[t-1]**2 + 
                                   self.beta[0] * sigma_squared[t-1])
            
            # Calculate log-likelihood (assuming normal distribution)
            log_likelihood = -0.5 * np.sum(
                np.log(2 * np.pi) + np.log(sigma_squared + 1e-10) + 
                (returns**2 / (sigma_squared + 1e-10))
            )
            
            # Gradient-based update (simplified)
            lr = 0.01 / (1 + iteration * 0.01)  # Learning rate decay
            
            # Update omega
            grad_omega = -0.5 * np.sum(1/sigma_squared - returns**2/sigma_squared**2)
            self.omega -= lr * grad_omega
            self.omega = max(1e-10, self.omega)
            
            # Update alpha
            grad_alpha = -0.5 * np.sum((returns[:-1]**2)/sigma_squared[1:] - 
                                       (returns[1:]**2 * returns[:-1]**2)/sigma_squared[1:]**2)
            self.alpha[0] -= lr * grad_alpha
            self.alpha[0] = np.clip(self.alpha[0], 0, 0.5)
            
            # Update beta
            grad_beta = -0.5 * np.sum(sigma_squared[:-1]/sigma_squared[1:] - 
                                      (returns[1:]**2 * sigma_squared[:-1])/sigma_squared[1:]**2)
            self.beta[0] -= lr * grad_beta
            self.beta[0] = np.clip(self.beta[0], 0, 0.99 - self.alpha[0])
            
            # Check convergence
            params = [self.omega, self.alpha.copy(), self.beta.copy()]
            param_change = sum(abs(p1 - p2) for p1, p2 in zip(params, prev_params))
            
            if param_change < tol:
                logger.info(f"GARCH converged at iteration {iteration}")
                break
            
            prev_params = params
        
        # Store residuals and final volatility
        sigma_squared = np.zeros(n)
        sigma_squared[0] = np.var(returns)
        for t in range(1, n):
            sigma_squared[t] = (self.omega + 
                               self.alpha[0] * returns[t-1]**2 + 
                               self.beta[0] * sigma_squared[t-1])
        
        self.residuals = returns / np.sqrt(sigma_squared + 1e-10)
        self.volatility_forecast = np.sqrt(sigma_squared)
        
        return self
    
    def forecast(self, steps: int = 10) -> np.ndarray:
        """
        Forecast future volatility
        
        Parameters
        ----------
        steps : int
            Number of steps to forecast
            
        Returns
        -------
        forecast : np.ndarray
            Volatility forecast
        """
        if self.volatility_forecast is None:
            raise ValueError("Model not fitted")
        
        forecast = np.zeros(steps)
        last_sigma = self.volatility_forecast[-1]
        last_return = self.residuals[-1] * last_sigma if self.residuals is not None else 0
        
        for t in range(steps):
            if t == 0:
                forecast[t] = np.sqrt(
                    self.omega + 
                    self.alpha[0] * last_return**2 + 
                    self.beta[0] * last_sigma**2
                )
            else:
                forecast[t] = np.sqrt(
                    self.omega + 
                    (self.alpha[0] + self.beta[0]) * forecast[t-1]**2
                )
        
        return forecast


class MarketRegimeDetector:
    """
    Advanced Market Regime Detection System
    
    Combines:
    - Hidden Markov Models for state identification
    - GARCH for volatility modeling
    - Technical indicators for regime confirmation
    - Bayesian updating for probability refinement
    
    Detects regimes:
    - Bull/Bear markets with low/high volatility
    - Sideways/range-bound markets
    - Crisis/extreme events
    - Transition periods
    """
    
    def __init__(self, lookback_period: int = 252, hmm_states: int = 8):
        self.lookback_period = lookback_period
        self.hmm_states = hmm_states
        
        self.hmm_model: Optional[HiddenMarkovModel] = None
        self.garch_model: Optional[GARCHModel] = None
        
        self.current_regime: Optional[RegimeState] = None
        self.regime_history: List[RegimeState] = []
        self.transition_matrix: Optional[np.ndarray] = None
        
        # Regime characteristics
        self.regime_profiles = self._initialize_regime_profiles()
        
        # Performance metrics
        self.detection_accuracy: float = 0.0
        self.false_positive_rate: float = 0.0
        
    def _initialize_regime_profiles(self) -> Dict[MarketRegime, Dict[str, Any]]:
        """Initialize characteristic profiles for each regime"""
        return {
            MarketRegime.BULL_LOW_VOL: {
                'mean_return': 0.001, 'volatility': 0.01, 'skewness': 0.5,
                'action': 'aggressive_long', 'risk_mult': 1.2
            },
            MarketRegime.BULL_HIGH_VOL: {
                'mean_return': 0.0008, 'volatility': 0.025, 'skewness': 0.3,
                'action': 'moderate_long', 'risk_mult': 1.0
            },
            MarketRegime.BEAR_LOW_VOL: {
                'mean_return': -0.0005, 'volatility': 0.012, 'skewness': -0.3,
                'action': 'defensive_short', 'risk_mult': 0.8
            },
            MarketRegime.BEAR_HIGH_VOL: {
                'mean_return': -0.001, 'volatility': 0.03, 'skewness': -0.6,
                'action': 'strong_defensive', 'risk_mult': 0.5
            },
            MarketRegime.SIDEWAYS_LOW: {
                'mean_return': 0.0001, 'volatility': 0.008, 'skewness': 0.0,
                'action': 'mean_reversion', 'risk_mult': 0.9
            },
            MarketRegime.SIDEWAYS_HIGH: {
                'mean_return': 0.0, 'volatility': 0.02, 'skewness': 0.0,
                'action': 'reduced_exposure', 'risk_mult': 0.7
            },
            MarketRegime.CRISIS: {
                'mean_return': -0.002, 'volatility': 0.05, 'skewness': -1.0,
                'action': 'flight_to_safety', 'risk_mult': 0.2
            },
            MarketRegime.TRANSITION: {
                'mean_return': 0.0, 'volatility': 0.015, 'skewness': 0.0,
                'action': 'wait_and_see', 'risk_mult': 0.6
            }
        }
    
    def prepare_features(self, prices: pd.Series, volumes: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        Prepare features for regime detection
        
        Features include:
        - Returns (daily, weekly, monthly)
        - Volatility measures
        - Momentum indicators
        - Volume patterns
        - Skewness and kurtosis
        """
        df = pd.DataFrame(index=prices.index)
        df['price'] = prices
        
        # Returns
        df['return_1d'] = prices.pct_change()
        df['return_5d'] = prices.pct_change(5)
        df['return_21d'] = prices.pct_change(21)
        
        # Volatility
        df['volatility_21d'] = df['return_1d'].rolling(21).std()
        df['volatility_63d'] = df['return_1d'].rolling(63).std()
        df['volatility_ratio'] = df['volatility_21d'] / (df['volatility_63d'] + 1e-10)
        
        # Momentum
        df['momentum_21d'] = prices / prices.shift(21) - 1
        df['momentum_63d'] = prices / prices.shift(63) - 1
        
        # Trend strength (RSI-like)
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume analysis
        if volumes is not None:
            df['volume_ma_ratio'] = volumes / volumes.rolling(21).mean()
            df['volume_volatility'] = volumes.pct_change().rolling(21).std()
        else:
            df['volume_ma_ratio'] = 1.0
            df['volume_volatility'] = 0.0
        
        # Skewness and kurtosis (rolling)
        df['skewness_21d'] = df['return_1d'].rolling(21).skew()
        df['kurtosis_21d'] = df['return_1d'].rolling(21).kurt()
        
        # Drawdown
        running_max = prices.cummax()
        df['drawdown'] = (prices - running_max) / running_max
        
        # Fill NaN values
        df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)
        
        return df
    
    def detect_regime(self, prices: pd.Series, volumes: Optional[pd.Series] = None, 
                     verbose: bool = False) -> RegimeState:
        """
        Detect current market regime
        
        Parameters
        ----------
        prices : pd.Series
            Price time series
        volumes : pd.Series, optional
            Volume time series
        verbose : bool
            Print detailed information
            
        Returns
        -------
        regime_state : RegimeState
            Current regime state with probabilities and recommendations
        """
        # Prepare features
        features_df = self.prepare_features(prices, volumes)
        
        # Use recent data for regime detection
        recent_data = features_df.tail(self.lookback_period)
        
        # Select key features for HMM
        feature_columns = ['return_1d', 'volatility_21d', 'momentum_21d', 
                          'rsi', 'skewness_21d', 'drawdown']
        observations = recent_data[feature_columns].values
        
        # Normalize features
        obs_mean = observations.mean(axis=0)
        obs_std = observations.std(axis=0) + 1e-10
        observations_normalized = (observations - obs_mean) / obs_std
        
        # Fit HMM if not already fitted or if data changed significantly
        if self.hmm_model is None or not self.hmm_model.states_converged:
            if verbose:
                logger.info("Fitting HMM model...")
            self.hmm_model = HiddenMarkovModel(n_states=self.hmm_states)
            self.hmm_model.fit(observations_normalized[:, 0], verbose=verbose)
        
        # Predict current state
        state_sequence = self.hmm_model.predict(observations_normalized[:, 0])
        state_probabilities = self.hmm_model.predict_proba(observations_normalized[:, 0])
        
        current_state = state_sequence[-1]
        current_probs = state_probabilities[-1]
        
        # Fit GARCH for volatility forecast
        returns = recent_data['return_1d'].values
        self.garch_model = GARCHModel()
        try:
            self.garch_model.fit(returns)
            volatility_forecast = self.garch_model.forecast(5).mean()
        except Exception as e:
            logger.warning(f"GARCH fitting failed: {e}")
            volatility_forecast = recent_data['volatility_21d'].iloc[-1]
        
        # Map HMM state to market regime
        current_regime = self._map_state_to_regime(
            state=current_state,
            probs=current_probs,
            volatility=volatility_forecast,
            momentum=recent_data['momentum_21d'].iloc[-1],
            drawdown=recent_data['drawdown'].iloc[-1]
        )
        
        # Create regime state object
        regime_state = RegimeState(
            regime=current_regime,
            probability=float(current_probs[current_state]),
            start_date=recent_data.index[-1],
            duration_days=self._estimate_duration(state_sequence, current_state),
            confidence=self._calculate_confidence(current_probs),
            volatility_level=volatility_forecast,
            trend_strength=abs(recent_data['momentum_21d'].iloc[-1]),
            recommended_action=self.regime_profiles[current_regime]['action'],
            risk_multiplier=self.regime_profiles[current_regime]['risk_mult']
        )
        
        self.current_regime = regime_state
        self.regime_history.append(regime_state)
        
        # Update transition matrix
        self._update_transition_matrix(state_sequence)
        
        if verbose:
            logger.info(f"Current Regime: {current_regime.value}")
            logger.info(f"Confidence: {regime_state.confidence:.2%}")
            logger.info(f"Recommended Action: {regime_state.recommended_action}")
            logger.info(f"Risk Multiplier: {regime_state.risk_multiplier:.2f}")
        
        return regime_state
    
    def _map_state_to_regime(self, state: int, probs: np.ndarray, 
                            volatility: float, momentum: float, 
                            drawdown: float) -> MarketRegime:
        """Map HMM state to interpretable market regime"""
        
        # Crisis detection (extreme volatility and drawdown)
        if volatility > 0.04 or drawdown < -0.2:
            return MarketRegime.CRISIS
        
        # Determine trend direction
        if momentum > 0.05:
            trend = 'bull'
        elif momentum < -0.05:
            trend = 'bear'
        else:
            trend = 'sideways'
        
        # Determine volatility level
        if volatility > 0.025:
            vol_level = 'high'
        else:
            vol_level = 'low'
        
        # Map to specific regime
        regime_map = {
            ('bull', 'low'): MarketRegime.BULL_LOW_VOL,
            ('bull', 'high'): MarketRegime.BULL_HIGH_VOL,
            ('bear', 'low'): MarketRegime.BEAR_LOW_VOL,
            ('bear', 'high'): MarketRegime.BEAR_HIGH_VOL,
            ('sideways', 'low'): MarketRegime.SIDEWAYS_LOW,
            ('sideways', 'high'): MarketRegime.SIDEWAYS_HIGH,
        }
        
        return regime_map.get((trend, vol_level), MarketRegime.TRANSITION)
    
    def _estimate_duration(self, state_sequence: np.ndarray, current_state: int) -> int:
        """Estimate how long the current regime has persisted"""
        duration = 0
        for state in reversed(state_sequence):
            if state == current_state:
                duration += 1
            else:
                break
        return duration
    
    def _calculate_confidence(self, probs: np.ndarray) -> float:
        """Calculate confidence in regime detection"""
        max_prob = np.max(probs)
        entropy = -np.sum(probs * np.log(probs + 1e-300))
        max_entropy = np.log(len(probs))
        
        # Confidence based on probability concentration and low entropy
        confidence = max_prob * (1 - entropy / (max_entropy + 1e-10))
        return min(1.0, max(0.0, confidence))
    
    def _update_transition_matrix(self, state_sequence: np.ndarray):
        """Update empirical transition matrix from observed states"""
        n_states = self.hmm_states
        transition_counts = np.zeros((n_states, n_states))
        
        for t in range(len(state_sequence) - 1):
            from_state = state_sequence[t]
            to_state = state_sequence[t + 1]
            transition_counts[from_state, to_state] += 1
        
        # Convert to probabilities
        row_sums = transition_counts.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        self.transition_matrix = transition_counts / row_sums
    
    def get_regime_forecast(self, steps: int = 5) -> List[Tuple[MarketRegime, float]]:
        """
        Forecast future regime probabilities
        
        Parameters
        ----------
        steps : int
            Number of steps to forecast
            
        Returns
        -------
        forecast : List[Tuple[MarketRegime, float]]
            List of (regime, probability) tuples for each step
        """
        if self.transition_matrix is None or self.current_regime is None:
            raise ValueError("No regime detected yet")
        
        # Map current regime to state index (simplified)
        current_state_idx = list(self.regime_profiles.keys()).index(self.current_regime.regime)
        
        forecast = []
        current_probs = np.zeros(self.hmm_states)
        current_probs[current_state_idx] = 1.0
        
        for step in range(steps):
            current_probs = current_probs @ self.transition_matrix
            most_likely_state = np.argmax(current_probs)
            most_likely_regime = list(self.regime_profiles.keys())[most_likely_state % len(self.regime_profiles)]
            forecast.append((most_likely_regime, current_probs[most_likely_state]))
        
        return forecast
    
    def get_strategy_recommendation(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy recommendation based on current regime
        
        Returns
        -------
        recommendation : Dict[str, Any]
            Detailed strategy recommendation
        """
        if self.current_regime is None:
            return {'error': 'No regime detected'}
        
        regime = self.current_regime.regime
        profile = self.regime_profiles[regime]
        
        # Base recommendation
        recommendation = {
            'regime': regime.value,
            'confidence': self.current_regime.confidence,
            'primary_action': profile['action'],
            'risk_multiplier': profile['risk_mult'],
            'position_sizing': self._get_position_sizing(profile),
            'asset_allocation': self._get_asset_allocation(regime),
            'hedging_strategy': self._get_hedging_strategy(regime),
            'stop_loss_adjustment': self._get_stop_loss_adjustment(regime),
            'take_profit_adjustment': self._get_take_profit_adjustment(regime),
        }
        
        # Add regime-specific insights
        if regime == MarketRegime.CRISIS:
            recommendation['priority'] = 'capital_preservation'
            recommendation['avoid'] = ['leveraged_positions', 'illiquid_assets']
        elif regime in [MarketRegime.BULL_LOW_VOL, MarketRegime.BULL_HIGH_VOL]:
            recommendation['priority'] = 'capture_upside'
            recommendation['favor'] = ['growth_stocks', 'momentum_strategies']
        elif regime in [MarketRegime.BEAR_LOW_VOL, MarketRegime.BEAR_HIGH_VOL]:
            recommendation['priority'] = 'defensive_positioning'
            recommendation['favor'] = ['value_stocks', 'dividend_payers', 'bonds']
        else:
            recommendation['priority'] = 'range_trading'
            recommendation['favor'] = ['mean_reversion', 'options_selling']
        
        return recommendation
    
    def _get_position_sizing(self, profile: Dict[str, Any]) -> str:
        """Get position sizing recommendation"""
        risk_mult = profile['risk_mult']
        if risk_mult >= 1.0:
            return "full_size (100%)"
        elif risk_mult >= 0.8:
            return "reduced_size (80%)"
        elif risk_mult >= 0.5:
            return "half_size (50%)"
        else:
            return "minimal_size (20%)"
    
    def _get_asset_allocation(self, regime: MarketRegime) -> Dict[str, float]:
        """Get recommended asset allocation"""
        allocations = {
            MarketRegime.BULL_LOW_VOL: {'equities': 0.8, 'bonds': 0.1, 'cash': 0.05, 'alternatives': 0.05},
            MarketRegime.BULL_HIGH_VOL: {'equities': 0.6, 'bonds': 0.2, 'cash': 0.1, 'alternatives': 0.1},
            MarketRegime.BEAR_LOW_VOL: {'equities': 0.3, 'bonds': 0.4, 'cash': 0.2, 'alternatives': 0.1},
            MarketRegime.BEAR_HIGH_VOL: {'equities': 0.1, 'bonds': 0.3, 'cash': 0.5, 'alternatives': 0.1},
            MarketRegime.SIDEWAYS_LOW: {'equities': 0.5, 'bonds': 0.3, 'cash': 0.1, 'alternatives': 0.1},
            MarketRegime.SIDEWAYS_HIGH: {'equities': 0.3, 'bonds': 0.3, 'cash': 0.3, 'alternatives': 0.1},
            MarketRegime.CRISIS: {'equities': 0.0, 'bonds': 0.2, 'cash': 0.7, 'alternatives': 0.1},
            MarketRegime.TRANSITION: {'equities': 0.4, 'bonds': 0.3, 'cash': 0.2, 'alternatives': 0.1},
        }
        return allocations.get(regime, allocations[MarketRegime.TRANSITION])
    
    def _get_hedging_strategy(self, regime: MarketRegime) -> str:
        """Get hedging strategy recommendation"""
        strategies = {
            MarketRegime.BULL_LOW_VOL: "minimal_hedging",
            MarketRegime.BULL_HIGH_VOL: "protective_puts",
            MarketRegime.BEAR_LOW_VOL: "collar_strategy",
            MarketRegime.BEAR_HIGH_VOL: "aggressive_hedging",
            MarketRegime.SIDEWAYS_LOW: "iron_condors",
            MarketRegime.SIDEWAYS_HIGH: "straddle_selling",
            MarketRegime.CRISIS: "tail_risk_protection",
            MarketRegime.TRANSITION: "flexible_hedging",
        }
        return strategies.get(regime, "neutral")
    
    def _get_stop_loss_adjustment(self, regime: MarketRegime) -> str:
        """Get stop-loss adjustment recommendation"""
        adjustments = {
            MarketRegime.BULL_LOW_VOL: "wide_stops (3-5%)",
            MarketRegime.BULL_HIGH_VOL: "medium_stops (2-3%)",
            MarketRegime.BEAR_LOW_VOL: "tight_stops (1-2%)",
            MarketRegime.BEAR_HIGH_VOL: "very_tight_stops (0.5-1%)",
            MarketRegime.SIDEWAYS_LOW: "range_based_stops",
            MarketRegime.SIDEWAYS_HIGH: "volatility_adjusted_stops",
            MarketRegime.CRISIS: "immediate_exit",
            MarketRegime.TRANSITION: "cautious_stops",
        }
        return adjustments.get(regime, "standard")
    
    def _get_take_profit_adjustment(self, regime: MarketRegime) -> str:
        """Get take-profit adjustment recommendation"""
        adjustments = {
            MarketRegime.BULL_LOW_VOL: "let_runners",
            MarketRegime.BULL_HIGH_VOL: "scale_out_gradually",
            MarketRegime.BEAR_LOW_VOL: "quick_profits",
            MarketRegime.BEAR_HIGH_VOL: "minimal_targets",
            MarketRegime.SIDEWAYS_LOW: "range_boundaries",
            MarketRegime.SIDEWAYS_HIGH: "conservative_targets",
            MarketRegime.CRISIS: "preserve_capital",
            MarketRegime.TRANSITION: "flexible_targets",
        }
        return adjustments.get(regime, "standard")


def demo_regime_detection():
    """Demonstrate regime detection with synthetic data"""
    np.random.seed(42)
    
    # Generate synthetic price data with different regimes
    n_days = 500
    dates = pd.date_range(start='2020-01-01', periods=n_days, freq='D')
    
    # Create price series with regime changes
    prices = np.ones(n_days)
    
    # Regime 1: Bull market (days 0-150)
    for i in range(1, 150):
        prices[i] = prices[i-1] * (1 + np.random.normal(0.001, 0.01))
    
    # Regime 2: High volatility sideways (days 150-250)
    for i in range(150, 250):
        prices[i] = prices[i-1] * (1 + np.random.normal(0.0001, 0.025))
    
    # Regime 3: Bear market crash (days 250-350)
    for i in range(250, 350):
        prices[i] = prices[i-1] * (1 + np.random.normal(-0.0015, 0.03))
    
    # Regime 4: Recovery bull (days 350-500)
    for i in range(350, n_days):
        prices[i] = prices[i-1] * (1 + np.random.normal(0.0012, 0.015))
    
    prices_series = pd.Series(prices, index=dates)
    volumes_series = pd.Series(np.random.exponential(1e6, n_days), index=dates)
    
    # Run regime detection
    detector = MarketRegimeDetector(lookback_period=100, hmm_states=6)
    
    print("=" * 60)
    print("MARKET REGIME DETECTION DEMO")
    print("=" * 60)
    
    regime_state = detector.detect_regime(prices_series, volumes_series, verbose=True)
    
    print("\n" + "=" * 60)
    print("STRATEGY RECOMMENDATION")
    print("=" * 60)
    
    recommendation = detector.get_strategy_recommendation()
    for key, value in recommendation.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    print("REGIME FORECAST (Next 5 periods)")
    print("=" * 60)
    
    forecast = detector.get_regime_forecast(5)
    for i, (regime, prob) in enumerate(forecast, 1):
        print(f"Period {i}: {regime.value} ({prob:.2%})")
    
    return detector


if __name__ == "__main__":
    detector = demo_regime_detection()
