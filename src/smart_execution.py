"""
Smart Execution Engine - Institutional Grade Order Execution
Implements TWAP, VWAP, Implementation Shortfall, and Almgren-Chriss models
Minimizes market impact and transaction costs
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionAlgo(Enum):
    """Execution algorithm types"""
    TWAP = "twap"                    # Time-Weighted Average Price
    VWAP = "vwap"                    # Volume-Weighted Average Price
    IS = "implementation_shortfall"  # Implementation Shortfall
    AC = "almgren_chriss"           # Almgren-Chriss optimal execution
    POV = "participation_of_volume"  # Percentage of Volume
    SNAPSHOT = "snapshot"            # Snapshot execution (immediate)


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class ExecutionOrder:
    """Represents an execution order"""
    order_id: str
    symbol: str
    side: OrderSide
    total_quantity: float
    executed_quantity: float
    average_price: float
    start_time: datetime
    end_time: datetime
    algo: ExecutionAlgo
    status: str  # pending, active, completed, cancelled
    target_participation_rate: float = 0.1
    risk_aversion: float = 0.5
    urgency: float = 0.5  # 0 = patient, 1 = urgent
    
    # Performance metrics
    vwap_achieved: Optional[float] = None
    twap_achieved: Optional[float] = None
    implementation_shortfall: Optional[float] = None
    market_impact_cost: Optional[float] = None
    timing_cost: Optional[float] = None
    spread_cost: Optional[float] = None
    
    # Child orders
    child_orders: List[Dict] = field(default_factory=list)


@dataclass
class MarketImpactModel:
    """Market impact model parameters"""
    temporary_impact: float = 0.1  # Linear temporary impact coefficient
    permanent_impact: float = 0.05  # Linear permanent impact coefficient
    nonlinear_exponent: float = 0.6  # Nonlinear impact exponent
    daily_volume: float = 1e6  # Average daily volume
    volatility: float = 0.02  # Daily volatility
    

class AlmgrenChrissOptimizer:
    """
    Almgren-Chriss optimal execution model
    
    Minimizes expected cost + risk aversion * variance of cost
    
    Reference:
    Almgren, R., & Chriss, N. (2001). Optimal execution of portfolio transactions.
    Journal of Risk, 3, 5-40.
    """
    
    def __init__(self, impact_model: MarketImpactModel):
        self.impact_model = impact_model
        self.optimal_trajectory: Optional[np.ndarray] = None
        self.expected_cost: Optional[float] = None
        self.cost_variance: Optional[float] = None
        
    def optimize(self, total_quantity: float, total_time: int, 
                 risk_aversion: float = 0.5, n_periods: int = 10) -> Dict[str, Any]:
        """
        Calculate optimal execution trajectory using Almgren-Chriss model
        
        Parameters
        ----------
        total_quantity : float
            Total quantity to execute
        total_time : int
            Total time for execution (in minutes or periods)
        risk_aversion : float
            Risk aversion parameter (lambda)
        n_periods : int
            Number of trading periods
            
        Returns
        -------
        result : Dict[str, Any]
            Optimal trajectory and cost metrics
        """
        # Model parameters
        eta = self.impact_model.temporary_impact  # Temporary impact coefficient
        gamma = self.impact_model.permanent_impact  # Permanent impact coefficient
        sigma = self.impact_model.volatility  # Volatility
        V = self.impact_model.daily_volume  # Daily volume
        
        # Time step
        dt = total_time / n_periods
        
        # Calculate kappa (trading rate parameter)
        kappa = np.sqrt((risk_aversion * sigma**2) / (2 * eta))
        
        # Optimal trading trajectory (continuous approximation)
        t = np.linspace(0, total_time, n_periods + 1)
        
        # Remaining inventory at each time step
        q_optimal = total_quantity * np.sinh(kappa * (total_time - t)) / np.sinh(kappa * total_time)
        
        # Trading rate (quantity per period)
        trading_rates = -np.diff(q_optimal)
        
        # Ensure non-negative trading rates
        trading_rates = np.maximum(trading_rates, 0)
        
        # Normalize to ensure total quantity is executed
        if trading_rates.sum() > 0:
            trading_rates = trading_rates * (total_quantity / trading_rates.sum())
        
        self.optimal_trajectory = {
            'times': t[:-1],
            'remaining_inventory': q_optimal[:-1],
            'trading_rates': trading_rates,
            'quantities': trading_rates
        }
        
        # Calculate expected cost components
        # Market impact cost
        impact_cost = eta * np.sum(trading_rates**2) / V
        
        # Timing risk cost
        timing_risk = 0.5 * risk_aversion * sigma**2 * np.sum(q_optimal[:-1]**2) * dt
        
        # Permanent impact cost
        permanent_cost = 0.5 * gamma * total_quantity**2
        
        self.expected_cost = impact_cost + timing_risk + permanent_cost
        self.cost_variance = sigma**2 * np.sum(q_optimal[:-1]**2) * dt
        
        return {
            'trajectory': self.optimal_trajectory,
            'expected_cost': self.expected_cost,
            'cost_variance': self.cost_variance,
            'impact_cost': impact_cost,
            'timing_risk': timing_risk,
            'permanent_cost': permanent_cost,
            'total_cost_bps': (self.expected_cost / total_quantity) * 10000
        }


class TWAPExecutor:
    """
    Time-Weighted Average Price execution
    Splits order evenly across time intervals
    """
    
    def __init__(self):
        self.slices: List[Dict] = []
        
    def generate_slices(self, total_quantity: float, start_time: datetime,
                       end_time: datetime, n_slices: int = 10) -> List[Dict]:
        """
        Generate TWAP execution slices
        
        Parameters
        ----------
        total_quantity : float
            Total quantity to execute
        start_time : datetime
            Start time
        end_time : datetime
            End time
        n_slices : int
            Number of slices
            
        Returns
        -------
        slices : List[Dict]
            List of execution slices
        """
        time_delta = (end_time - start_time).total_seconds() / n_slices
        quantity_per_slice = total_quantity / n_slices
        
        self.slices = []
        for i in range(n_slices):
            slice_time = start_time + timedelta(seconds=time_delta * i)
            self.slices.append({
                'slice_id': i,
                'quantity': quantity_per_slice,
                'scheduled_time': slice_time,
                'status': 'pending'
            })
        
        return self.slices


class VWAPExecutor:
    """
    Volume-Weighted Average Price execution
    Slices order based on historical volume profile
    """
    
    def __init__(self, volume_profile: Optional[pd.Series] = None):
        self.volume_profile = volume_profile
        self.slices: List[Dict] = []
        
    def set_volume_profile(self, volume_profile: pd.Series):
        """Set historical volume profile"""
        self.volume_profile = volume_profile
        
    def generate_slices(self, total_quantity: float, start_time: datetime,
                       end_time: datetime) -> List[Dict]:
        """
        Generate VWAP execution slices based on volume profile
        
        Parameters
        ----------
        total_quantity : float
            Total quantity to execute
        start_time : datetime
            Start time
        end_time : datetime
            End time
            
        Returns
        -------
        slices : List[Dict]
            List of execution slices
        """
        if self.volume_profile is None:
            # Default to uniform profile if none provided
            n_slices = 10
            self.volume_profile = pd.Series([1.0] * n_slices)
        
        # Normalize volume profile
        volume_weights = self.volume_profile / self.volume_profile.sum()
        
        # Generate slices
        time_delta = (end_time - start_time).total_seconds() / len(volume_weights)
        
        self.slices = []
        for i, weight in enumerate(volume_weights):
            slice_time = start_time + timedelta(seconds=time_delta * i)
            self.slices.append({
                'slice_id': i,
                'quantity': total_quantity * weight,
                'scheduled_time': slice_time,
                'volume_weight': weight,
                'status': 'pending'
            })
        
        return self.slices


class ImplementationShortfallExecutor:
    """
    Implementation Shortfall minimization
    Balances market impact against timing risk
    Uses dynamic participation based on price movement
    """
    
    def __init__(self, risk_aversion: float = 0.5, urgency: float = 0.5):
        self.risk_aversion = risk_aversion
        self.urgency = urgency
        self.participation_rate: float = 0.1
        
    def calculate_participation_rate(self, price_deviation: float, 
                                    volume_available: float,
                                    time_remaining: float) -> float:
        """
        Calculate dynamic participation rate based on market conditions
        
        Parameters
        ----------
        price_deviation : float
            Deviation from decision price (adverse movement)
        volume_available : float
            Available market volume
        time_remaining : float
            Time remaining for execution
            
        Returns
        -------
        participation_rate : float
            Calculated participation rate
        """
        # Base participation rate
        base_rate = 0.1
        
        # Increase participation if price moves adversely
        if price_deviation > 0:  # Adverse movement
            urgency_adjustment = min(self.urgency * price_deviation * 10, 0.5)
        else:
            urgency_adjustment = 0
        
        # Decrease participation if time is abundant
        time_adjustment = max(0, 0.1 * (1 - time_remaining))
        
        # Risk aversion adjustment
        risk_adjustment = self.risk_aversion * 0.2
        
        participation_rate = base_rate + urgency_adjustment + time_adjustment + risk_adjustment
        
        # Cap participation rate
        participation_rate = min(participation_rate, 0.3)  # Max 30% of volume
        participation_rate = max(participation_rate, 0.05)  # Min 5% of volume
        
        self.participation_rate = participation_rate
        return participation_rate
    
    def generate_slices(self, total_quantity: float, start_time: datetime,
                       end_time: datetime, market_data: pd.DataFrame) -> List[Dict]:
        """
        Generate adaptive IS execution slices
        
        Parameters
        ----------
        total_quantity : float
            Total quantity to execute
        start_time : datetime
            Start time
        end_time : datetime
            End time
        market_data : pd.DataFrame
            Market data with prices and volumes
            
        Returns
        -------
        slices : List[Dict]
            List of execution slices with dynamic participation
        """
        n_slices = min(len(market_data), 20)
        time_delta = (end_time - start_time).total_seconds() / n_slices
        
        self.slices = []
        remaining_quantity = total_quantity
        
        for i in range(n_slices):
            slice_time = start_time + timedelta(seconds=time_delta * i)
            
            # Get market data for this slice
            if i < len(market_data):
                volume_available = market_data.iloc[i]['volume']
                current_price = market_data.iloc[i]['price']
            else:
                volume_available = 1e6
                current_price = 100.0
            
            # Calculate participation rate
            time_remaining = (n_slices - i) / n_slices
            price_deviation = 0.01 * (i / n_slices)  # Simulated adverse movement
            
            participation_rate = self.calculate_participation_rate(
                price_deviation, volume_available, time_remaining
            )
            
            # Calculate slice quantity
            slice_quantity = min(
                remaining_quantity / (n_slices - i),  # Equal split of remaining
                volume_available * participation_rate  # Volume limit
            )
            
            self.slices.append({
                'slice_id': i,
                'quantity': slice_quantity,
                'scheduled_time': slice_time,
                'participation_rate': participation_rate,
                'estimated_cost_bps': 5 + 10 * participation_rate,  # Estimated cost
                'status': 'pending'
            })
            
            remaining_quantity -= slice_quantity
        
        return self.slices


class SmartExecutionEngine:
    """
    Smart Execution Engine - Institutional Grade Order Routing
    
    Features:
    - Multiple execution algorithms (TWAP, VWAP, IS, Almgren-Chriss)
    - Real-time market impact estimation
    - Adaptive execution based on market conditions
    - Cost optimization and performance attribution
    - Multi-venue routing (future extension)
    """
    
    def __init__(self, impact_model: Optional[MarketImpactModel] = None):
        self.impact_model = impact_model or MarketImpactModel()
        self.ac_optimizer = AlmgrenChrissOptimizer(self.impact_model)
        self.twap_executor = TWAPExecutor()
        self.vwap_executor = VWAPExecutor()
        self.is_executor = ImplementationShortfallExecutor()
        
        self.active_orders: Dict[str, ExecutionOrder] = {}
        self.completed_orders: List[ExecutionOrder] = []
        self.execution_history: List[Dict] = []
        
        # Performance tracking
        self.total_cost_savings = 0.0
        self.average_slippage = 0.0
        
    def create_order(self, symbol: str, side: OrderSide, quantity: float,
                    algo: ExecutionAlgo, start_time: datetime, end_time: datetime,
                    risk_aversion: float = 0.5, urgency: float = 0.5,
                    participation_rate: float = 0.1) -> ExecutionOrder:
        """
        Create a new execution order
        
        Parameters
        ----------
        symbol : str
            Symbol to trade
        side : OrderSide
            Buy or sell
        quantity : float
            Quantity to execute
        algo : ExecutionAlgo
            Execution algorithm
        start_time : datetime
            Start time
        end_time : datetime
            End time
        risk_aversion : float
            Risk aversion parameter
        urgency : float
            Urgency parameter (0-1)
        participation_rate : float
            Target participation rate
            
        Returns
        -------
        order : ExecutionOrder
            Created order
        """
        order_id = f"{symbol}_{side.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        order = ExecutionOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            executed_quantity=0.0,
            average_price=0.0,
            start_time=start_time,
            end_time=end_time,
            algo=algo,
            status='pending',
            target_participation_rate=participation_rate,
            risk_aversion=risk_aversion,
            urgency=urgency
        )
        
        self.active_orders[order_id] = order
        
        logger.info(f"Created {algo.value} order: {order_id}")
        logger.info(f"  Symbol: {symbol}, Side: {side.value}, Quantity: {quantity}")
        logger.info(f"  Time window: {start_time} to {end_time}")
        
        return order
    
    def generate_execution_plan(self, order: ExecutionOrder, 
                               market_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Generate execution plan for an order
        
        Parameters
        ----------
        order : ExecutionOrder
            Order to plan
        market_data : pd.DataFrame, optional
            Historical market data for planning
            
        Returns
        -------
        plan : Dict[str, Any]
            Execution plan with slices and cost estimates
        """
        duration_minutes = (order.end_time - order.start_time).total_seconds() / 60
        
        if order.algo == ExecutionAlgo.TWAP:
            n_slices = max(10, int(duration_minutes / 5))  # One slice every 5 minutes
            slices = self.twap_executor.generate_slices(
                order.total_quantity,
                order.start_time,
                order.end_time,
                n_slices=n_slices
            )
            estimated_cost_bps = 2.0  # Low cost for TWAP
            
        elif order.algo == ExecutionAlgo.VWAP:
            if market_data is not None and 'volume' in market_data.columns:
                # Use intraday volume profile
                volume_profile = market_data.set_index('time')['volume']
                self.vwap_executor.set_volume_profile(volume_profile)
            slices = self.vwap_executor.generate_slices(
                order.total_quantity,
                order.start_time,
                order.end_time
            )
            estimated_cost_bps = 3.0
            
        elif order.algo == ExecutionAlgo.IS:
            if market_data is None:
                # Create dummy market data
                n_points = 20
                market_data = pd.DataFrame({
                    'price': np.linspace(100, 102, n_points),
                    'volume': np.random.exponential(1e5, n_points)
                })
            self.is_executor.risk_aversion = order.risk_aversion
            self.is_executor.urgency = order.urgency
            slices = self.is_executor.generate_slices(
                order.total_quantity,
                order.start_time,
                order.end_time,
                market_data
            )
            estimated_cost_bps = 4.0 + order.urgency * 5.0
            
        elif order.algo == ExecutionAlgo.AC:
            ac_result = self.ac_optimizer.optimize(
                order.total_quantity,
                int(duration_minutes),
                risk_aversion=order.risk_aversion,
                n_periods=max(10, int(duration_minutes / 5))
            )
            slices = [
                {
                    'slice_id': i,
                    'quantity': ac_result['trajectory']['quantities'][i],
                    'scheduled_time': order.start_time + timedelta(
                        seconds=(order.end_time - order.start_time).total_seconds() * i / len(ac_result['trajectory']['quantities'])
                    ),
                    'status': 'pending'
                }
                for i in range(len(ac_result['trajectory']['quantities']))
            ]
            estimated_cost_bps = ac_result['total_cost_bps']
            
        else:
            raise ValueError(f"Unknown execution algorithm: {order.algo}")
        
        # Store child orders
        order.child_orders = slices
        
        plan = {
            'order_id': order.order_id,
            'algo': order.algo.value,
            'total_quantity': order.total_quantity,
            'n_slices': len(slices),
            'slices': slices,
            'estimated_cost_bps': estimated_cost_bps,
            'duration_minutes': duration_minutes
        }
        
        logger.info(f"Generated execution plan for {order.order_id}")
        logger.info(f"  Algorithm: {order.algo.value}")
        logger.info(f"  Number of slices: {len(slices)}")
        logger.info(f"  Estimated cost: {estimated_cost_bps:.2f} bps")
        
        return plan
    
    def simulate_execution(self, order: ExecutionOrder, 
                          market_prices: np.ndarray) -> Dict[str, Any]:
        """
        Simulate order execution and calculate performance metrics
        
        Parameters
        ----------
        order : ExecutionOrder
            Order to simulate
        market_prices : np.ndarray
            Market price series during execution period
            
        Returns
        -------
        result : Dict[str, Any]
            Execution results with costs and slippage
        """
        if not order.child_orders:
            raise ValueError("No execution plan generated")
        
        # Decision price (price at order creation)
        decision_price = market_prices[0]
        
        # Execute slices
        total_proceeds = 0.0
        total_quantity = 0.0
        vwap_market = 0.0
        twap_market = 0.0
        
        for i, slice_info in enumerate(order.child_orders):
            if i >= len(market_prices):
                break
                
            slice_price = market_prices[i]
            slice_quantity = slice_info['quantity']
            
            # Apply market impact (simplified)
            impact_factor = 1.0
            if order.side == OrderSide.BUY:
                execution_price = slice_price * (1 + impact_factor * 0.0001)
            else:
                execution_price = slice_price * (1 - impact_factor * 0.0001)
            
            total_proceeds += execution_price * slice_quantity
            total_quantity += slice_quantity
            
            # Accumulate for VWAP calculation
            vwap_market += slice_price * slice_quantity
            twap_market += slice_price
        
        # Calculate metrics
        if total_quantity > 0:
            vwap_achieved = total_proceeds / total_quantity
            twap_market = twap_market / len(order.child_orders)
            vwap_market = vwap_market / total_quantity
        else:
            vwap_achieved = decision_price
            twap_market = decision_price
            vwap_market = decision_price
        
        # Implementation shortfall
        if order.side == OrderSide.BUY:
            shortfall_bps = (vwap_achieved - decision_price) / decision_price * 10000
        else:
            shortfall_bps = (decision_price - vwap_achieved) / decision_price * 10000
        
        # Update order
        order.executed_quantity = total_quantity
        order.average_price = vwap_achieved
        order.vwap_achieved = vwap_achieved
        order.twap_achieved = twap_market
        order.implementation_shortfall = shortfall_bps
        order.status = 'completed'
        
        # Cost attribution (simplified)
        order.market_impact_cost = shortfall_bps * 0.4  # 40% attributed to impact
        order.timing_cost = shortfall_bps * 0.4  # 40% attributed to timing
        order.spread_cost = shortfall_bps * 0.2  # 20% attributed to spread
        
        result = {
            'order_id': order.order_id,
            'status': 'completed',
            'executed_quantity': total_quantity,
            'average_price': vwap_achieved,
            'decision_price': decision_price,
            'vwap_market': vwap_market,
            'twap_market': twap_market,
            'implementation_shortfall_bps': shortfall_bps,
            'market_impact_cost_bps': order.market_impact_cost,
            'timing_cost_bps': order.timing_cost,
            'spread_cost_bps': order.spread_cost,
            'total_cost_bps': shortfall_bps
        }
        
        # Move to completed orders
        if order.order_id in self.active_orders:
            del self.active_orders[order.order_id]
        self.completed_orders.append(order)
        self.execution_history.append(result)
        
        logger.info(f"Executed order {order.order_id}")
        logger.info(f"  Avg price: {vwap_achieved:.4f}, Decision price: {decision_price:.4f}")
        logger.info(f"  Implementation shortfall: {shortfall_bps:.2f} bps")
        
        return result
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary of all executed orders
        
        Returns
        -------
        summary : Dict[str, Any]
            Performance metrics
        """
        if not self.execution_history:
            return {'error': 'No executed orders'}
        
        total_is = sum(r['implementation_shortfall_bps'] for r in self.execution_history)
        avg_is = total_is / len(self.execution_history)
        
        total_impact = sum(r['market_impact_cost_bps'] for r in self.execution_history)
        total_timing = sum(r['timing_cost_bps'] for r in self.execution_history)
        total_spread = sum(r['spread_cost_bps'] for r in self.execution_history)
        
        summary = {
            'total_orders': len(self.execution_history),
            'avg_implementation_shortfall_bps': avg_is,
            'total_implementation_shortfall_bps': total_is,
            'cost_breakdown': {
                'market_impact_bps': total_impact,
                'timing_cost_bps': total_timing,
                'spread_cost_bps': total_spread
            },
            'by_algorithm': {}
        }
        
        # Breakdown by algorithm
        algo_groups = {}
        for result in self.execution_history:
            order = next((o for o in self.completed_orders if o.order_id == result['order_id']), None)
            if order:
                algo = order.algo.value
                if algo not in algo_groups:
                    algo_groups[algo] = []
                algo_groups[algo].append(result['implementation_shortfall_bps'])
        
        for algo, costs in algo_groups.items():
            summary['by_algorithm'][algo] = {
                'count': len(costs),
                'avg_cost_bps': np.mean(costs),
                'total_cost_bps': sum(costs)
            }
        
        return summary


def demo_smart_execution():
    """Demonstrate smart execution engine"""
    np.random.seed(42)
    
    print("=" * 70)
    print("SMART EXECUTION ENGINE DEMO")
    print("=" * 70)
    
    # Create execution engine
    engine = SmartExecutionEngine()
    
    # Create sample market data (simulated price path)
    n_periods = 50
    base_price = 100.0
    returns = np.random.normal(0.0001, 0.001, n_periods)
    prices = base_price * np.cumprod(1 + returns)
    
    market_data = pd.DataFrame({
        'time': pd.date_range(start='2024-01-01 09:30', periods=n_periods, freq='T'),
        'price': prices,
        'volume': np.random.exponential(1e5, n_periods)
    })
    
    # Test different execution algorithms
    algorithms = [
        ExecutionAlgo.TWAP,
        ExecutionAlgo.VWAP,
        ExecutionAlgo.IS,
        ExecutionAlgo.AC
    ]
    
    results = []
    
    for algo in algorithms:
        print(f"\n{'='*70}")
        print(f"Testing {algo.value.upper()} Execution")
        print('='*70)
        
        # Create order
        start_time = datetime(2024, 1, 1, 9, 30)
        end_time = datetime(2024, 1, 1, 10, 30)
        
        order = engine.create_order(
            symbol='AAPL',
            side=OrderSide.BUY,
            quantity=10000,
            algo=algo,
            start_time=start_time,
            end_time=end_time,
            risk_aversion=0.5,
            urgency=0.5
        )
        
        # Generate execution plan
        plan = engine.generate_execution_plan(order, market_data)
        
        print(f"\nExecution Plan:")
        print(f"  Total quantity: {plan['total_quantity']}")
        print(f"  Number of slices: {plan['n_slices']}")
        print(f"  Estimated cost: {plan['estimated_cost_bps']:.2f} bps")
        print(f"  Duration: {plan['duration_minutes']:.0f} minutes")
        
        # Simulate execution
        result = engine.simulate_execution(order, prices[:plan['n_slices']])
        
        print(f"\nExecution Results:")
        print(f"  Average price: ${result['average_price']:.4f}")
        print(f"  Decision price: ${result['decision_price']:.4f}")
        print(f"  VWAP market: ${result['vwap_market']:.4f}")
        print(f"  Implementation shortfall: {result['implementation_shortfall_bps']:.2f} bps")
        print(f"  Market impact cost: {result['market_impact_cost_bps']:.2f} bps")
        print(f"  Timing cost: {result['timing_cost_bps']:.2f} bps")
        print(f"  Spread cost: {result['spread_cost_bps']:.2f} bps")
        
        results.append(result)
    
    # Performance summary
    print(f"\n{'='*70}")
    print("PERFORMANCE SUMMARY")
    print('='*70)
    
    summary = engine.get_performance_summary()
    print(f"\nTotal orders executed: {summary['total_orders']}")
    print(f"Average implementation shortfall: {summary['avg_implementation_shortfall_bps']:.2f} bps")
    print(f"Total implementation shortfall: {summary['total_implementation_shortfall_bps']:.2f} bps")
    
    print("\nCost Breakdown:")
    print(f"  Market impact: {summary['cost_breakdown']['market_impact_bps']:.2f} bps")
    print(f"  Timing cost: {summary['cost_breakdown']['timing_cost_bps']:.2f} bps")
    print(f"  Spread cost: {summary['cost_breakdown']['spread_cost_bps']:.2f} bps")
    
    print("\nBy Algorithm:")
    for algo, stats in summary['by_algorithm'].items():
        print(f"  {algo.upper()}: {stats['avg_cost_bps']:.2f} bps avg ({stats['count']} orders)")
    
    return engine


if __name__ == "__main__":
    engine = demo_smart_execution()
