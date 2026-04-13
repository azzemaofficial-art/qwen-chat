"""
Advanced Order Execution Engine
High-frequency trading simulation with smart order routing
"""

import time
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Order:
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    trail_percent: Optional[float] = None
    time_in_force: str = "GTC"  # GTC, IOC, FOK, GTD
    expiry: Optional[datetime] = None
    iceberg_qty: Optional[float] = None
    twap_duration: Optional[int] = None  # seconds
    vwap_participation: Optional[float] = None  # 0.0-1.0
    
    order_id: str = field(default_factory=lambda: hashlib.md5(
        f"{time.time()}{random.random()}".encode()).hexdigest()[:16])
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: float = 0.0
    avg_fill_price: float = 0.0
    fills: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "stop_price": self.stop_price,
            "trail_percent": self.trail_percent,
            "time_in_force": self.time_in_force,
            "status": self.status.value,
            "filled_qty": self.filled_qty,
            "avg_fill_price": self.avg_fill_price,
            "fills": self.fills,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class MarketDepth:
    symbol: str
    bids: List[Tuple[float, float]]  # (price, quantity)
    asks: List[Tuple[float, float]]  # (price, quantity)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_vwap(self, side: OrderSide, quantity: float) -> Optional[float]:
        """Calculate VWAP for executing given quantity"""
        levels = self.bids if side == OrderSide.SELL else self.asks
        if not levels:
            return None
        
        remaining_qty = quantity
        total_value = 0.0
        total_qty = 0.0
        
        for price, qty in levels:
            exec_qty = min(remaining_qty, qty)
            total_value += price * exec_qty
            total_qty += exec_qty
            remaining_qty -= exec_qty
            
            if remaining_qty <= 0:
                break
        
        if total_qty == 0:
            return None
        return total_value / total_qty
    
    def get_spread(self) -> Optional[float]:
        if self.bids and self.asks:
            return self.asks[0][0] - self.bids[0][0]
        return None
    
    def get_mid_price(self) -> Optional[float]:
        if self.bids and self.asks:
            return (self.bids[0][0] + self.asks[0][0]) / 2
        return None


class SmartOrderRouter:
    """Routes orders to optimal execution venues"""
    
    def __init__(self):
        self.venues = ["NYSE", "NASDAQ", "ARCA", "BATS", "IEX"]
        self.venue_latencies = {v: random.uniform(1, 10) for v in self.venues}
        self.venue_fees = {v: random.uniform(0.0001, 0.0005) for v in self.venues}
        self.venue_liquidity = {v: random.uniform(0.7, 1.0) for v in self.venues}
    
    def find_best_venue(self, order: Order, market_depth: MarketDepth) -> str:
        """Select optimal venue based on price, latency, and liquidity"""
        scores = {}
        
        for venue in self.venues:
            # Score based on multiple factors
            liquidity_score = self.venue_liquidity[venue]
            latency_penalty = 1.0 / (1.0 + self.venue_latencies[venue] / 10)
            fee_penalty = 1.0 - self.venue_fees[venue]
            
            # Price improvement potential
            spread = market_depth.get_spread() or 0
            price_improvement = 1.0 if spread > 0.01 else 0.8
            
            scores[venue] = (
                liquidity_score * 0.4 +
                latency_penalty * 0.3 +
                fee_penalty * 0.2 +
                price_improvement * 0.1
            )
        
        return max(scores, key=scores.get)


class ExecutionEngine:
    """High-performance order execution engine"""
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.router = SmartOrderRouter()
        self.market_data: Dict[str, MarketDepth] = {}
        self.execution_log: List[Dict] = []
        self._simulate_market_data()
    
    def _simulate_market_data(self):
        """Generate realistic market depth data"""
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "AMD"]
        
        for symbol in symbols:
            base_price = random.uniform(100, 500)
            spread = base_price * random.uniform(0.0001, 0.001)
            
            bids = [
                (base_price - spread * (i + 1), random.uniform(100, 1000))
                for i in range(10)
            ]
            asks = [
                (base_price + spread * (i + 1), random.uniform(100, 1000))
                for i in range(10)
            ]
            
            self.market_data[symbol] = MarketDepth(
                symbol=symbol,
                bids=sorted(bids, reverse=True),
                asks=sorted(asks)
            )
    
    def submit_order(self, order: Order) -> Order:
        """Submit order to execution system"""
        if order.symbol not in self.market_data:
            order.status = OrderStatus.REJECTED
            order.updated_at = datetime.now()
            self.orders[order.order_id] = order
            return order
        
        # Route order
        venue = self.router.find_best_venue(order, self.market_data[order.symbol])
        
        # Execute based on order type
        if order.order_type == OrderType.MARKET:
            self._execute_market_order(order, venue)
        elif order.order_type == OrderType.LIMIT:
            self._execute_limit_order(order, venue)
        elif order.order_type == OrderType.ICEBERG:
            self._execute_iceberg_order(order, venue)
        elif order.order_type == OrderType.TWAP:
            self._execute_twap_order(order, venue)
        elif order.order_type == OrderType.VWAP:
            self._execute_vwap_order(order, venue)
        else:
            self._execute_standard_order(order, venue)
        
        self.orders[order.order_id] = order
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "order_id": order.order_id,
            "action": "submitted",
            "venue": venue
        })
        
        return order
    
    def _execute_market_order(self, order: Order, venue: str):
        """Execute market order immediately"""
        market = self.market_data[order.symbol]
        fill_price = market.get_vwap(order.side, order.quantity)
        
        if fill_price is None:
            order.status = OrderStatus.REJECTED
            return
        
        slippage = random.uniform(-0.001, 0.002)  # Small slippage
        final_price = fill_price * (1 + slippage)
        
        order.filled_qty = order.quantity
        order.avg_fill_price = final_price
        order.status = OrderStatus.FILLED
        order.fills.append({
            "price": final_price,
            "quantity": order.quantity,
            "timestamp": datetime.now().isoformat(),
            "venue": venue
        })
        order.updated_at = datetime.now()
    
    def _execute_limit_order(self, order: Order, venue: str):
        """Execute limit order if price conditions met"""
        market = self.market_data[order.symbol]
        mid_price = market.get_mid_price()
        
        if mid_price is None:
            order.status = OrderStatus.REJECTED
            return
        
        can_fill = False
        if order.side == OrderSide.BUY and order.price >= mid_price:
            can_fill = True
        elif order.side == OrderSide.SELL and order.price <= mid_price:
            can_fill = True
        
        if can_fill:
            fill_prob = random.random()
            if fill_prob > 0.3:  # 70% fill probability
                order.filled_qty = order.quantity
                order.avg_fill_price = order.price
                order.status = OrderStatus.FILLED
                order.fills.append({
                    "price": order.price,
                    "quantity": order.quantity,
                    "timestamp": datetime.now().isoformat(),
                    "venue": venue
                })
            else:
                order.status = OrderStatus.PENDING
        else:
            order.status = OrderStatus.PENDING
        
        order.updated_at = datetime.now()
    
    def _execute_iceberg_order(self, order: Order, venue: str):
        """Execute iceberg order in small chunks"""
        if order.iceberg_qty is None:
            order.iceberg_qty = order.quantity / 10
        
        market = self.market_data[order.symbol]
        remaining = order.quantity - order.filled_qty
        
        if remaining <= 0:
            order.status = OrderStatus.FILLED
            return
        
        chunk_size = min(order.iceberg_qty, remaining)
        fill_price = market.get_vwap(order.side, chunk_size)
        
        if fill_price:
            slippage = random.uniform(-0.0005, 0.001)
            final_price = fill_price * (1 + slippage)
            
            order.filled_qty += chunk_size
            weighted_avg = (
                (order.avg_fill_price * (order.filled_qty - chunk_size) + 
                 final_price * chunk_size) / order.filled_qty
            )
            order.avg_fill_price = weighted_avg
            
            order.fills.append({
                "price": final_price,
                "quantity": chunk_size,
                "timestamp": datetime.now().isoformat(),
                "venue": venue,
                "iceberg_chunk": True
            })
            
            if order.filled_qty >= order.quantity:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIALLY_FILLED
        
        order.updated_at = datetime.now()
    
    def _execute_twap_order(self, order: Order, venue: str):
        """Execute TWAP order over specified duration"""
        if order.twap_duration is None:
            order.twap_duration = 3600  # Default 1 hour
        
        intervals = max(10, order.twap_duration // 60)
        chunk_size = order.quantity / intervals
        
        market = self.market_data[order.symbol]
        fill_price = market.get_vwap(order.side, chunk_size)
        
        if fill_price:
            # Simulate partial execution (first interval)
            slippage = random.uniform(-0.001, 0.001)
            final_price = fill_price * (1 + slippage)
            
            executed_qty = min(chunk_size, order.quantity - order.filled_qty)
            order.filled_qty += executed_qty
            
            if order.filled_qty > 0:
                weighted_avg = (
                    (order.avg_fill_price * (order.filled_qty - executed_qty) + 
                     final_price * executed_qty) / order.filled_qty
                )
                order.avg_fill_price = weighted_avg
            
            order.fills.append({
                "price": final_price,
                "quantity": executed_qty,
                "timestamp": datetime.now().isoformat(),
                "venue": venue,
                "twap_interval": 1,
                "total_intervals": intervals
            })
            
            if order.filled_qty >= order.quantity:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIALLY_FILLED
        
        order.updated_at = datetime.now()
    
    def _execute_vwap_order(self, order: Order, venue: str):
        """Execute VWAP order targeting volume participation"""
        if order.vwap_participation is None:
            order.vwap_participation = 0.1  # 10% participation
        
        market = self.market_data[order.symbol]
        target_qty = order.quantity * order.vwap_participation
        
        fill_price = market.get_vwap(order.side, target_qty)
        
        if fill_price:
            slippage = random.uniform(-0.0005, 0.0005)
            final_price = fill_price * (1 + slippage)
            
            executed_qty = min(target_qty, order.quantity - order.filled_qty)
            order.filled_qty += executed_qty
            
            if order.filled_qty > 0:
                weighted_avg = (
                    (order.avg_fill_price * (order.filled_qty - executed_qty) + 
                     final_price * executed_qty) / order.filled_qty
                )
                order.avg_fill_price = weighted_avg
            
            order.fills.append({
                "price": final_price,
                "quantity": executed_qty,
                "timestamp": datetime.now().isoformat(),
                "venue": venue,
                "vwap_participation": order.vwap_participation
            })
            
            if order.filled_qty >= order.quantity:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIALLY_FILLED
        
        order.updated_at = datetime.now()
    
    def _execute_standard_order(self, order: Order, venue: str):
        """Generic order execution for other types"""
        self._execute_market_order(order, venue)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return False
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "order_id": order_id,
            "action": "cancelled"
        })
        
        return True
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get current order status"""
        if order_id not in self.orders:
            return None
        return self.orders[order_id].to_dict()
    
    def get_execution_metrics(self) -> Dict:
        """Calculate execution quality metrics"""
        if not self.execution_log:
            return {}
        
        total_orders = len(self.orders)
        filled_orders = sum(1 for o in self.orders.values() 
                          if o.status == OrderStatus.FILLED)
        rejected_orders = sum(1 for o in self.orders.values() 
                            if o.status == OrderStatus.REJECTED)
        
        total_slippage = 0.0
        fill_count = 0
        
        for order in self.orders.values():
            for fill in order.fills:
                if "slippage" in fill:
                    total_slippage += fill["slippage"]
                    fill_count += 1
        
        avg_slippage = total_slippage / fill_count if fill_count > 0 else 0
        
        return {
            "total_orders": total_orders,
            "filled_orders": filled_orders,
            "fill_rate": filled_orders / total_orders if total_orders > 0 else 0,
            "rejected_orders": rejected_orders,
            "avg_slippage_bps": avg_slippage * 10000,
            "total_fills": sum(len(o.fills) for o in self.orders.values())
        }


def demo():
    """Demonstrate execution engine capabilities"""
    print("=" * 70)
    print("🚀 ADVANCED ORDER EXECUTION ENGINE DEMO")
    print("=" * 70)
    
    engine = ExecutionEngine()
    
    # Demo 1: Market Order
    print("\n📊 Test 1: Market Order Execution")
    market_order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=500
    )
    result = engine.submit_order(market_order)
    print(f"   Order ID: {result.order_id}")
    print(f"   Status: {result.status.value}")
    print(f"   Filled: {result.filled_qty}/{result.quantity}")
    print(f"   Avg Price: ${result.avg_fill_price:.2f}")
    print(f"   Total Fills: {len(result.fills)}")
    
    # Demo 2: Limit Order
    print("\n📊 Test 2: Limit Order Execution")
    limit_order = Order(
        symbol="GOOGL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=300,
        price=140.0
    )
    result = engine.submit_order(limit_order)
    print(f"   Order ID: {result.order_id}")
    print(f"   Status: {result.status.value}")
    print(f"   Limit Price: ${limit_order.price:.2f}")
    
    # Demo 3: Iceberg Order
    print("\n📊 Test 3: Iceberg Order Execution")
    iceberg_order = Order(
        symbol="MSFT",
        side=OrderSide.SELL,
        order_type=OrderType.ICEBERG,
        quantity=5000,
        iceberg_qty=500
    )
    result = engine.submit_order(iceberg_order)
    print(f"   Order ID: {result.order_id}")
    print(f"   Status: {result.status.value}")
    print(f"   Hidden Qty: {result.quantity - (result.iceberg_qty or 0)}")
    print(f"   Visible Qty: {result.iceberg_qty}")
    print(f"   Filled: {result.filled_qty}/{result.quantity}")
    
    # Demo 4: TWAP Order
    print("\n📊 Test 4: TWAP Order Execution")
    twap_order = Order(
        symbol="TSLA",
        side=OrderSide.BUY,
        order_type=OrderType.TWAP,
        quantity=2000,
        twap_duration=1800  # 30 minutes
    )
    result = engine.submit_order(twap_order)
    print(f"   Order ID: {result.order_id}")
    print(f"   Status: {result.status.value}")
    print(f"   Duration: {twap_order.twap_duration}s")
    print(f"   Filled: {result.filled_qty}/{result.quantity}")
    
    # Demo 5: VWAP Order
    print("\n📊 Test 5: VWAP Order Execution")
    vwap_order = Order(
        symbol="NVDA",
        side=OrderSide.SELL,
        order_type=OrderType.VWAP,
        quantity=3000,
        vwap_participation=0.15
    )
    result = engine.submit_order(vwap_order)
    print(f"   Order ID: {result.order_id}")
    print(f"   Status: {result.status.value}")
    print(f"   Participation: {vwap_order.vwap_participation*100:.0f}%")
    print(f"   Filled: {result.filled_qty}/{result.quantity}")
    
    # Demo 6: Execution Metrics
    print("\n📊 Test 6: Execution Quality Metrics")
    metrics = engine.get_execution_metrics()
    print(f"   Total Orders: {metrics['total_orders']}")
    print(f"   Fill Rate: {metrics['fill_rate']*100:.1f}%")
    print(f"   Rejected: {metrics['rejected_orders']}")
    print(f"   Avg Slippage: {metrics['avg_slippage_bps']:.2f} bps")
    print(f"   Total Fills: {metrics['total_fills']}")
    
    # Demo 7: Order Cancellation
    print("\n📊 Test 7: Order Cancellation")
    pending_order = Order(
        symbol="AMD",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=1000,
        price=100.0
    )
    result = engine.submit_order(pending_order)
    print(f"   Submitted Order: {result.order_id}")
    cancelled = engine.cancel_order(result.order_id)
    print(f"   Cancelled: {cancelled}")
    print(f"   New Status: {engine.get_order_status(result.order_id)['status']}")
    
    print("\n" + "=" * 70)
    print("✅ EXECUTION ENGINE DEMO COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    demo()
