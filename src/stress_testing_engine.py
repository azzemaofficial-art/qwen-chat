"""
Stress Testing Engine - Advanced Risk Simulation
Monte Carlo, Historical Stress Tests, Black Swan Analysis
Comprehensive scenario analysis for portfolio resilience
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from scipy import stats
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StressScenarioType(Enum):
    """Types of stress scenarios"""
    HISTORICAL = "historical"           # Historical crisis events
    HYPOTHETICAL = "hypothetical"       # Hypothetical scenarios
    MONTE_CARLO = "monte_carlo"         # Monte Carlo simulation
    SENSITIVITY = "sensitivity"         # Sensitivity analysis
    BLACK_SWAN = "black_swan"           # Extreme tail events
    REGULATORY = "regulatory"           # Regulatory stress tests


@dataclass
class HistoricalCrisis:
    """Historical crisis event"""
    name: str
    start_date: datetime
    end_date: datetime
    description: str
    market_impact: Dict[str, float]  # Asset class impacts
    duration_days: int
    
    @classmethod
    def get_predefined_crises(cls) -> List['HistoricalCrisis']:
        """Get list of predefined historical crises"""
        return [
            HistoricalCrisis(
                name="2008 Financial Crisis",
                start_date=datetime(2008, 1, 1),
                end_date=datetime(2009, 3, 9),
                description="Global financial crisis triggered by subprime mortgage collapse",
                market_impact={
                    'equities': -0.57,
                    'bonds': 0.05,
                    'commodities': -0.35,
                    'real_estate': -0.45,
                    'gold': 0.05
                },
                duration_days=433
            ),
            HistoricalCrisis(
                name="2020 COVID Crash",
                start_date=datetime(2020, 2, 19),
                end_date=datetime(2020, 3, 23),
                description="Market crash due to COVID-19 pandemic",
                market_impact={
                    'equities': -0.34,
                    'bonds': 0.03,
                    'commodities': -0.25,
                    'real_estate': -0.20,
                    'gold': 0.08
                },
                duration_days=33
            ),
            HistoricalCrisis(
                name="2000 Dot-com Bubble",
                start_date=datetime(2000, 3, 10),
                end_date=datetime(2002, 10, 9),
                description="Technology stock bubble burst",
                market_impact={
                    'equities': -0.49,
                    'bonds': 0.08,
                    'commodities': -0.10,
                    'real_estate': -0.15,
                    'gold': 0.15
                },
                duration_days=944
            ),
            HistoricalCrisis(
                name="1987 Black Monday",
                start_date=datetime(1987, 10, 19),
                end_date=datetime(1987, 12, 4),
                description="Largest one-day percentage decline in stock market history",
                market_impact={
                    'equities': -0.30,
                    'bonds': 0.02,
                    'commodities': -0.15,
                    'real_estate': -0.10,
                    'gold': -0.05
                },
                duration_days=46
            ),
            HistoricalCrisis(
                name="2015 China Slowdown",
                start_date=datetime(2015, 6, 12),
                end_date=datetime(2016, 1, 20),
                description="Chinese stock market crash and yuan devaluation",
                market_impact={
                    'equities': -0.18,
                    'bonds': 0.04,
                    'commodities': -0.25,
                    'real_estate': -0.08,
                    'gold': 0.10
                },
                duration_days=222
            )
        ]


@dataclass
class StressTestResult:
    """Results from a stress test"""
    scenario_name: str
    scenario_type: StressScenarioType
    portfolio_value_before: float
    portfolio_value_after: float
    loss_amount: float
    loss_percentage: float
    var_95: float
    var_99: float
    expected_shortfall: float
    max_drawdown: float
    recovery_time_days: int
    asset_class_losses: Dict[str, float]
    risk_metrics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_critical(self, threshold: float = 0.20) -> bool:
        """Check if loss exceeds critical threshold"""
        return abs(self.loss_percentage) > threshold


@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo simulation"""
    n_simulations: int = 10000
    time_horizon_days: int = 252
    confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99])
    distribution: str = "normal"  # normal, student_t, empirical
    include_jumps: bool = False
    jump_intensity: float = 0.01
    jump_mean: float = -0.05
    jump_std: float = 0.10
    correlation_matrix: Optional[np.ndarray] = None
    

class MonteCarloEngine:
    """
    Monte Carlo Simulation Engine for Portfolio Risk Analysis
    
    Supports:
    - Geometric Brownian Motion
    - Jump-Diffusion processes
    - Student-t distributions for fat tails
    - Correlated asset simulations
    """
    
    def __init__(self, config: MonteCarloConfig):
        self.config = config
        self.simulation_results: Optional[np.ndarray] = None
        self.portfolio_paths: Optional[np.ndarray] = None
        
    def simulate_gbm(self, initial_price: float, mu: float, sigma: float,
                    n_days: int) -> np.ndarray:
        """
        Simulate Geometric Brownian Motion
        
        Parameters
        ----------
        initial_price : float
            Starting price
        mu : float
            Expected return (annualized)
        sigma : float
            Volatility (annualized)
        n_days : int
            Number of days to simulate
            
        Returns
        -------
        prices : np.ndarray
            Simulated price path
        """
        dt = 1.0 / 252.0  # Daily time step
        
        # Generate random returns
        if self.config.distribution == "normal":
            returns = np.random.normal(mu * dt, sigma * np.sqrt(dt), n_days)
        elif self.config.distribution == "student_t":
            # Student-t with 4 degrees of freedom for fat tails
            df = 4
            returns = stats.t.rvs(df, loc=mu * dt, scale=sigma * np.sqrt(dt), size=n_days)
        else:
            raise ValueError(f"Unknown distribution: {self.config.distribution}")
        
        # Add jumps if configured
        if self.config.include_jumps:
            jump_indicator = np.random.poisson(self.config.jump_intensity, n_days)
            jump_sizes = np.random.normal(self.config.jump_mean, self.config.jump_std, n_days)
            returns += jump_indicator * jump_sizes
        
        # Calculate price path
        prices = initial_price * np.cumprod(1 + returns)
        
        return prices
    
    def simulate_portfolio(self, weights: np.ndarray, 
                          expected_returns: np.ndarray,
                          volatilities: np.ndarray,
                          correlation_matrix: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Simulate portfolio value paths using Monte Carlo
        
        Parameters
        ----------
        weights : np.ndarray
            Portfolio weights
        expected_returns : np.ndarray
            Expected annual returns for each asset
        volatilities : np.ndarray
            Annual volatilities for each asset
        correlation_matrix : np.ndarray, optional
            Correlation matrix between assets
            
        Returns
        -------
        portfolio_paths : np.ndarray
            Simulated portfolio value paths (n_simulations x n_days)
        """
        n_assets = len(weights)
        n_days = self.config.time_horizon_days
        n_sims = self.config.n_simulations
        
        # Build covariance matrix
        if correlation_matrix is None:
            correlation_matrix = np.eye(n_assets)
        
        cov_matrix = np.outer(volatilities, volatilities) * correlation_matrix
        
        # Cholesky decomposition for correlated random numbers
        try:
            L = np.linalg.cholesky(cov_matrix)
        except np.linalg.LinAlgError:
            # If not positive definite, use eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
            eigenvalues = np.maximum(eigenvalues, 0)
            L = eigenvectors @ np.diag(np.sqrt(eigenvalues))
        
        # Generate correlated returns
        dt = 1.0 / 252.0
        
        if self.config.distribution == "normal":
            uncorrelated_returns = np.random.normal(
                0, 1, (n_sims, n_days, n_assets)
            )
        elif self.config.distribution == "student_t":
            df = 4
            uncorrelated_returns = stats.t.rvs(
                df, 0, 1, (n_sims, n_days, n_assets)
            )
        else:
            raise ValueError(f"Unknown distribution: {self.config.distribution}")
        
        # Apply correlation structure
        correlated_returns = uncorrelated_returns @ L.T
        
        # Add drift and volatility
        for i in range(n_assets):
            correlated_returns[:, :, i] += (expected_returns[i] * dt)
            correlated_returns[:, :, i] *= volatilities[i] / np.sqrt(252 * dt)
        
        # Add jumps if configured
        if self.config.include_jumps:
            jump_indicator = np.random.poisson(
                self.config.jump_intensity, (n_sims, n_days, n_assets)
            )
            jump_sizes = np.random.normal(
                self.config.jump_mean, self.config.jump_std, (n_sims, n_days, n_assets)
            )
            correlated_returns += jump_indicator * jump_sizes
        
        # Calculate portfolio returns
        portfolio_returns = np.sum(correlated_returns * weights, axis=2)
        
        # Calculate cumulative returns (wealth indices)
        wealth_indices = np.cumprod(1 + portfolio_returns, axis=1)
        
        self.portfolio_paths = wealth_indices
        self.simulation_results = wealth_indices[:, -1]  # Final values
        
        return wealth_indices
    
    def calculate_var(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk from simulation results
        
        Parameters
        ----------
        confidence_level : float
            Confidence level (e.g., 0.95 for 95% VaR)
            
        Returns
        -------
        var : float
            Value at Risk (as a percentage loss)
        """
        if self.simulation_results is None:
            raise ValueError("No simulation results available")
        
        # VaR is the quantile of losses
        var = np.percentile(self.simulation_results, (1 - confidence_level) * 100)
        
        # Convert to loss percentage (assuming starting value of 1)
        var_loss = 1 - var
        
        return max(0, var_loss)
    
    def calculate_expected_shortfall(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Expected Shortfall (CVaR) from simulation results
        
        Parameters
        ----------
        confidence_level : float
            Confidence level
            
        Returns
        -------
        es : float
            Expected Shortfall (average loss beyond VaR)
        """
        if self.simulation_results is None:
            raise ValueError("No simulation results available")
        
        var = self.calculate_var(confidence_level)
        var_threshold = 1 - var
        
        # ES is the average of losses beyond VaR
        tail_losses = self.simulation_results[self.simulation_results <= var_threshold]
        
        if len(tail_losses) == 0:
            return var
        
        es = 1 - np.mean(tail_losses)
        
        return max(0, es)
    
    def get_statistics(self) -> Dict[str, float]:
        """Get comprehensive statistics from simulation"""
        if self.simulation_results is None:
            raise ValueError("No simulation results available")
        
        final_values = self.simulation_results
        
        stats_dict = {
            'mean_return': np.mean(final_values) - 1,
            'median_return': np.median(final_values) - 1,
            'std_return': np.std(final_values),
            'min_return': np.min(final_values) - 1,
            'max_return': np.max(final_values) - 1,
            'skewness': stats.skew(final_values),
            'kurtosis': stats.kurtosis(final_values),
            'var_95': self.calculate_var(0.95),
            'var_99': self.calculate_var(0.99),
            'es_95': self.calculate_expected_shortfall(0.95),
            'es_99': self.calculate_expected_shortfall(0.99),
            'probability_of_loss': np.mean(final_values < 1),
            'probability_of_ruin': np.mean(final_values < 0.5)
        }
        
        return stats_dict


class StressTestingEngine:
    """
    Comprehensive Stress Testing Engine
    
    Features:
    - Historical crisis replay
    - Monte Carlo simulation
    - Hypothetical scenario testing
    - Black swan analysis
    - Sensitivity analysis
    - Regulatory stress tests (Basel, CCAR)
    """
    
    def __init__(self):
        self.historical_crises = HistoricalCrisis.get_predefined_crises()
        self.stress_results: List[StressTestResult] = []
        self.current_portfolio: Optional[Dict[str, Any]] = None
        
    def set_portfolio(self, portfolio_value: float, 
                     asset_allocation: Dict[str, float],
                     asset_returns: Dict[str, float],
                     asset_volatilities: Dict[str, float],
                     correlation_matrix: Optional[np.ndarray] = None):
        """
        Set current portfolio configuration
        
        Parameters
        ----------
        portfolio_value : float
            Total portfolio value
        asset_allocation : Dict[str, float]
            Allocation weights by asset class
        asset_returns : Dict[str, float]
            Expected annual returns by asset class
        asset_volatilities : Dict[str, float]
            Annual volatilities by asset class
        correlation_matrix : np.ndarray, optional
            Correlation matrix between asset classes
        """
        self.current_portfolio = {
            'value': portfolio_value,
            'allocation': asset_allocation,
            'returns': asset_returns,
            'volatilities': asset_volatilities,
            'correlation_matrix': correlation_matrix
        }
        
        logger.info(f"Portfolio set: ${portfolio_value:,.2f}")
        logger.info(f"Asset classes: {list(asset_allocation.keys())}")
    
    def run_historical_stress_test(self, crisis: HistoricalCrisis) -> StressTestResult:
        """
        Run stress test using historical crisis scenario
        
        Parameters
        ----------
        crisis : HistoricalCrisis
            Historical crisis event
            
        Returns
        -------
        result : StressTestResult
            Stress test results
        """
        if self.current_portfolio is None:
            raise ValueError("Portfolio not set")
        
        portfolio_value = self.current_portfolio['value']
        allocation = self.current_portfolio['allocation']
        
        # Calculate portfolio impact
        total_loss = 0.0
        asset_losses = {}
        
        for asset_class, weight in allocation.items():
            # Get impact for this asset class (or use equity impact as proxy)
            impact = crisis.market_impact.get(asset_class, crisis.market_impact.get('equities', -0.3))
            loss = weight * impact
            total_loss += loss
            asset_losses[asset_class] = loss
        
        portfolio_value_after = portfolio_value * (1 + total_loss)
        loss_amount = portfolio_value_after - portfolio_value
        
        # Estimate VaR and ES based on historical volatility scaling
        base_var_95 = abs(total_loss) * 1.2
        base_var_99 = abs(total_loss) * 1.5
        es = abs(total_loss) * 1.8
        
        result = StressTestResult(
            scenario_name=crisis.name,
            scenario_type=StressScenarioType.HISTORICAL,
            portfolio_value_before=portfolio_value,
            portfolio_value_after=portfolio_value_after,
            loss_amount=loss_amount,
            loss_percentage=total_loss,
            var_95=base_var_95,
            var_99=base_var_99,
            expected_shortfall=es,
            max_drawdown=abs(total_loss),
            recovery_time_days=int(crisis.duration_days * 0.7),  # Estimate 70% of crisis duration
            asset_class_losses=asset_losses,
            risk_metrics={
                'crisis_duration': crisis.duration_days,
                'description': crisis.description
            }
        )
        
        self.stress_results.append(result)
        
        logger.info(f"Historical stress test: {crisis.name}")
        logger.info(f"  Loss: {total_loss:.2%} (${loss_amount:,.2f})")
        
        return result
    
    def run_monte_carlo_stress_test(self, config: MonteCarloConfig) -> StressTestResult:
        """
        Run Monte Carlo stress test
        
        Parameters
        ----------
        config : MonteCarloConfig
            Monte Carlo configuration
            
        Returns
        -------
        result : StressTestResult
            Stress test results
        """
        if self.current_portfolio is None:
            raise ValueError("Portfolio not set")
        
        portfolio_value = self.current_portfolio['value']
        allocation = self.current_portfolio['allocation']
        returns = self.current_portfolio['returns']
        volatilities = self.current_portfolio['volatilities']
        correlation_matrix = self.current_portfolio['correlation_matrix']
        
        # Prepare arrays
        asset_classes = list(allocation.keys())
        weights = np.array([allocation[ac] for ac in asset_classes])
        exp_returns = np.array([returns.get(ac, 0.05) for ac in asset_classes])
        vols = np.array([volatilities.get(ac, 0.15) for ac in asset_classes])
        
        # Run Monte Carlo simulation
        mc_engine = MonteCarloEngine(config)
        portfolio_paths = mc_engine.simulate_portfolio(
            weights, exp_returns, vols, correlation_matrix
        )
        
        # Calculate statistics
        final_values = mc_engine.simulation_results
        worst_case = np.percentile(final_values, 1)  # 1st percentile
        
        portfolio_value_after = portfolio_value * worst_case
        loss_amount = portfolio_value_after - portfolio_value
        loss_percentage = worst_case - 1
        
        var_95 = mc_engine.calculate_var(0.95)
        var_99 = mc_engine.calculate_var(0.99)
        es_95 = mc_engine.calculate_expected_shortfall(0.95)
        
        # Calculate max drawdown across all paths
        max_drawdowns = []
        for path in portfolio_paths:
            running_max = np.maximum.accumulate(path)
            drawdowns = (path - running_max) / running_max
            max_drawdowns.append(np.min(drawdowns))
        max_drawdown = np.mean(max_drawdowns)
        
        # Estimate recovery time
        stats_dict = mc_engine.get_statistics()
        recovery_time = int(config.time_horizon_days * (1 - stats_dict['probability_of_loss']))
        
        result = StressTestResult(
            scenario_name=f"Monte Carlo ({config.n_simulations} simulations)",
            scenario_type=StressScenarioType.MONTE_CARLO,
            portfolio_value_before=portfolio_value,
            portfolio_value_after=portfolio_value_after,
            loss_amount=loss_amount,
            loss_percentage=loss_percentage,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=es_95,
            max_drawdown=abs(max_drawdown),
            recovery_time_days=recovery_time,
            asset_class_losses={ac: loss_percentage * w for ac, w in allocation.items()},
            risk_metrics=stats_dict
        )
        
        self.stress_results.append(result)
        
        logger.info(f"Monte Carlo stress test completed")
        logger.info(f"  VaR 95%: {var_95:.2%}, VaR 99%: {var_99:.2%}")
        logger.info(f"  Expected Shortfall: {es_95:.2%}")
        
        return result
    
    def run_hypothetical_scenario(self, scenario_name: str, 
                                 shocks: Dict[str, float],
                                 description: str = "") -> StressTestResult:
        """
        Run hypothetical stress scenario
        
        Parameters
        ----------
        scenario_name : str
            Name of the scenario
        shocks : Dict[str, float]
            Shocks to apply to each asset class
        description : str
            Scenario description
            
        Returns
        -------
        result : StressTestResult
            Stress test results
        """
        if self.current_portfolio is None:
            raise ValueError("Portfolio not set")
        
        portfolio_value = self.current_portfolio['value']
        allocation = self.current_portfolio['allocation']
        
        # Calculate portfolio impact
        total_loss = 0.0
        asset_losses = {}
        
        for asset_class, weight in allocation.items():
            shock = shocks.get(asset_class, 0.0)
            loss = weight * shock
            total_loss += loss
            asset_losses[asset_class] = loss
        
        portfolio_value_after = portfolio_value * (1 + total_loss)
        loss_amount = portfolio_value_after - portfolio_value
        
        result = StressTestResult(
            scenario_name=scenario_name,
            scenario_type=StressScenarioType.HYPOTHETICAL,
            portfolio_value_before=portfolio_value,
            portfolio_value_after=portfolio_value_after,
            loss_amount=loss_amount,
            loss_percentage=total_loss,
            var_95=abs(total_loss) * 1.2,
            var_99=abs(total_loss) * 1.5,
            expected_shortfall=abs(total_loss) * 1.8,
            max_drawdown=abs(total_loss),
            recovery_time_days=60,  # Default estimate
            asset_class_losses=asset_losses,
            risk_metrics={'description': description, 'shocks': shocks}
        )
        
        self.stress_results.append(result)
        
        logger.info(f"Hypothetical scenario: {scenario_name}")
        logger.info(f"  Loss: {total_loss:.2%}")
        
        return result
    
    def run_black_swan_analysis(self, n_extreme_scenarios: int = 100) -> List[StressTestResult]:
        """
        Run black swan analysis with extreme tail scenarios
        
        Parameters
        ----------
        n_extreme_scenarios : int
            Number of extreme scenarios to simulate
            
        Returns
        -------
        results : List[StressTestResult]
            List of black swan scenario results
        """
        if self.current_portfolio is None:
            raise ValueError("Portfolio not set")
        
        results = []
        portfolio_value = self.current_portfolio['value']
        allocation = self.current_portfolio['allocation']
        
        logger.info(f"Running black swan analysis with {n_extreme_scenarios} scenarios...")
        
        for i in range(n_extreme_scenarios):
            # Generate extreme shocks (from tail of distribution)
            severity = np.random.exponential(0.3) + 0.2  # Minimum 20% shock
            shocks = {}
            
            for asset_class in allocation.keys():
                # Different asset classes have different tail risks
                if asset_class == 'equities':
                    shock = -severity * np.random.uniform(0.8, 1.2)
                elif asset_class == 'bonds':
                    shock = np.random.uniform(-0.1, 0.1)  # Bonds usually safer
                elif asset_class == 'commodities':
                    shock = -severity * np.random.uniform(0.5, 1.0)
                elif asset_class == 'gold':
                    shock = np.random.uniform(-0.1, 0.2)  # Gold often rises in crises
                else:
                    shock = -severity * 0.5
                
                shocks[asset_class] = shock
            
            # Create scenario
            scenario_name = f"Black Swan #{i+1}"
            result = self.run_hypothetical_scenario(
                scenario_name=scenario_name,
                shocks=shocks,
                description=f"Extreme tail event scenario #{i+1}"
            )
            result.scenario_type = StressScenarioType.BLACK_SWAN
            results.append(result)
        
        return results
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive stress testing report
        
        Returns
        -------
        report : Dict[str, Any]
            Comprehensive report with all results
        """
        if not self.stress_results:
            return {'error': 'No stress tests run'}
        
        # Group results by scenario type
        by_type = {}
        for result in self.stress_results:
            type_name = result.scenario_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(result)
        
        # Calculate summary statistics
        all_losses = [r.loss_percentage for r in self.stress_results]
        worst_case = min(all_losses)
        avg_loss = np.mean(all_losses)
        var_95_loss = np.percentile(all_losses, 5)
        
        # Find worst case per category
        worst_by_type = {}
        for type_name, results in by_type.items():
            worst = min(results, key=lambda r: r.loss_percentage)
            worst_by_type[type_name] = {
                'scenario': worst.scenario_name,
                'loss': worst.loss_percentage,
                'amount': worst.loss_amount
            }
        
        report = {
            'summary': {
                'total_scenarios_tested': len(self.stress_results),
                'worst_case_loss': worst_case,
                'average_loss': avg_loss,
                'var_95_of_scenarios': var_95_loss,
                'scenarios_exceeding_20pct': sum(1 for l in all_losses if l < -0.20),
                'scenarios_exceeding_30pct': sum(1 for l in all_losses if l < -0.30)
            },
            'by_scenario_type': worst_by_type,
            'detailed_results': [
                {
                    'scenario': r.scenario_name,
                    'type': r.scenario_type.value,
                    'loss_percentage': r.loss_percentage,
                    'loss_amount': r.loss_amount,
                    'var_95': r.var_95,
                    'var_99': r.var_99,
                    'expected_shortfall': r.expected_shortfall,
                    'recovery_days': r.recovery_time_days
                }
                for r in self.stress_results
            ],
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate risk management recommendations based on results"""
        recommendations = []
        
        if not self.stress_results:
            return recommendations
        
        # Analyze worst cases
        worst_loss = min(r.loss_percentage for r in self.stress_results)
        
        if worst_loss < -0.50:
            recommendations.append(
                "CRITICAL: Portfolio shows vulnerability to extreme losses (>50%). "
                "Consider immediate hedging or diversification."
            )
        elif worst_loss < -0.30:
            recommendations.append(
                "WARNING: Significant tail risk detected. Review hedging strategies "
                "and consider reducing exposure to high-risk assets."
            )
        
        # Check concentration risk
        if self.current_portfolio:
            max_weight = max(self.current_portfolio['allocation'].values())
            if max_weight > 0.5:
                recommendations.append(
                    f"CONCENTRATION RISK: Single asset class has {max_weight:.0%} allocation. "
                    "Consider diversifying to reduce concentration risk."
                )
        
        # General recommendations
        recommendations.append(
            "Regular stress testing should be performed monthly or when market conditions change significantly."
        )
        recommendations.append(
            "Maintain liquidity buffer to withstand stressed market conditions without forced selling."
        )
        
        return recommendations


def demo_stress_testing():
    """Demonstrate stress testing engine"""
    np.random.seed(42)
    
    print("=" * 70)
    print("STRESS TESTING ENGINE DEMO")
    print("=" * 70)
    
    # Create stress testing engine
    engine = StressTestingEngine()
    
    # Set up sample portfolio
    portfolio_value = 10_000_000  # $10M
    asset_allocation = {
        'equities': 0.60,
        'bonds': 0.25,
        'commodities': 0.10,
        'gold': 0.05
    }
    
    asset_returns = {
        'equities': 0.08,
        'bonds': 0.03,
        'commodities': 0.05,
        'gold': 0.04
    }
    
    asset_volatilities = {
        'equities': 0.18,
        'bonds': 0.05,
        'commodities': 0.20,
        'gold': 0.15
    }
    
    # Simple correlation matrix
    correlation_matrix = np.array([
        [1.00, 0.20, 0.30, 0.10],
        [0.20, 1.00, 0.10, 0.20],
        [0.30, 0.10, 1.00, 0.25],
        [0.10, 0.20, 0.25, 1.00]
    ])
    
    engine.set_portfolio(
        portfolio_value=portfolio_value,
        asset_allocation=asset_allocation,
        asset_returns=asset_returns,
        asset_volatilities=asset_volatilities,
        correlation_matrix=correlation_matrix
    )
    
    # Run historical stress tests
    print("\n" + "=" * 70)
    print("HISTORICAL STRESS TESTS")
    print("=" * 70)
    
    for crisis in HistoricalCrisis.get_predefined_crises()[:3]:  # Test first 3 crises
        result = engine.run_historical_stress_test(crisis)
        print(f"\n{crisis.name}:")
        print(f"  Portfolio Value: ${result.portfolio_value_before:,.0f} → ${result.portfolio_value_after:,.0f}")
        print(f"  Loss: {result.loss_percentage:.2%} (${result.loss_amount:,.0f})")
        print(f"  VaR 95%: {result.var_95:.2%}, VaR 99%: {result.var_99:.2%}")
    
    # Run Monte Carlo stress test
    print("\n" + "=" * 70)
    print("MONTE CARLO STRESS TEST")
    print("=" * 70)
    
    mc_config = MonteCarloConfig(
        n_simulations=5000,
        time_horizon_days=252,
        distribution='student_t',
        include_jumps=True
    )
    
    mc_result = engine.run_monte_carlo_stress_test(mc_config)
    print(f"\nMonte Carlo Results:")
    print(f"  Portfolio Value: ${mc_result.portfolio_value_before:,.0f} → ${mc_result.portfolio_value_after:,.0f}")
    print(f"  Loss: {mc_result.loss_percentage:.2%}")
    print(f"  VaR 95%: {mc_result.var_95:.2%}, VaR 99%: {mc_result.var_99:.2%}")
    print(f"  Expected Shortfall: {mc_result.expected_shortfall:.2%}")
    
    # Run hypothetical scenario
    print("\n" + "=" * 70)
    print("HYPOTHETICAL SCENARIO")
    print("=" * 70)
    
    hypothetical_shocks = {
        'equities': -0.25,
        'bonds': 0.05,
        'commodities': -0.15,
        'gold': 0.10
    }
    
    hyp_result = engine.run_hypothetical_scenario(
        scenario_name="Interest Rate Shock + Recession",
        shocks=hypothetical_shocks,
        description="Fed raises rates 300bps triggering recession"
    )
    print(f"\nScenario: {hyp_result.scenario_name}")
    print(f"  Loss: {hyp_result.loss_percentage:.2%} (${hyp_result.loss_amount:,.0f})")
    
    # Run black swan analysis
    print("\n" + "=" * 70)
    print("BLACK SWAN ANALYSIS")
    print("=" * 70)
    
    black_swan_results = engine.run_black_swan_analysis(n_extreme_scenarios=50)
    worst_black_swan = min(black_swan_results, key=lambda r: r.loss_percentage)
    print(f"\nWorst Black Swan Scenario:")
    print(f"  Loss: {worst_black_swan.loss_percentage:.2%} (${worst_black_swan.loss_amount:,.0f})")
    print(f"  Expected Shortfall: {worst_black_swan.expected_shortfall:.2%}")
    
    # Generate comprehensive report
    print("\n" + "=" * 70)
    print("COMPREHENSIVE REPORT")
    print("=" * 70)
    
    report = engine.get_comprehensive_report()
    
    print(f"\nSummary:")
    print(f"  Total scenarios tested: {report['summary']['total_scenarios_tested']}")
    print(f"  Worst case loss: {report['summary']['worst_case_loss']:.2%}")
    print(f"  Average loss: {report['summary']['average_loss']:.2%}")
    print(f"  Scenarios exceeding 20% loss: {report['summary']['scenarios_exceeding_20pct']}")
    print(f"  Scenarios exceeding 30% loss: {report['summary']['scenarios_exceeding_30pct']}")
    
    print(f"\nRecommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    return engine


if __name__ == "__main__":
    engine = demo_stress_testing()
