"""
Trading Advisor Pro v7.0 - DeFi & Crypto Integration
Support for decentralized exchanges, liquidity pools, and yield farming
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import ccxt.async_support as ccxt
from web3 import Web3
from web3.exceptions import ContractLogicError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DexType(Enum):
    UNISWAP = "uniswap"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"
    BALANCER = "balancer"
    PANCAKESWAP = "pancakeswap"


class ChainType(Enum):
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    AVALANCHE = "avalanche"


@dataclass
class LiquidityPool:
    pool_address: str
    token0: str
    token1: str
    reserve0: float
    reserve1: float
    fee_tier: float
    apr: float
    tvl: float
    dex: DexType
    chain: ChainType


@dataclass
class ArbitrageOpportunity:
    buy_exchange: str
    sell_exchange: str
    symbol: str
    price_difference: float
    profit_potential: float
    volume_available: float
    timestamp: datetime


class DeFiAnalyzer:
    """Analyzer for DeFi protocols and opportunities"""
    
    def __init__(self, rpc_endpoints: Optional[Dict[str, str]] = None):
        self.rpc_endpoints = rpc_endpoints or {
            'ethereum': 'https://mainnet.infura.io/v3/YOUR_KEY',
            'bsc': 'https://bsc-dataseed.binance.org',
            'polygon': 'https://polygon-rpc.com'
        }
        
        # Initialize Web3 connections
        self.web3_connections: Dict[str, Web3] = {}
        for chain, rpc in self.rpc_endpoints.items():
            try:
                self.web3_connections[chain] = Web3(Web3.HTTPProvider(rpc))
            except Exception as e:
                logger.warning(f"Failed to connect to {chain}: {e}")
    
    def get_token_balance(self, token_address: str, wallet_address: str, chain: str = 'ethereum') -> float:
        """Get token balance for a wallet"""
        if chain not in self.web3_connections:
            raise ValueError(f"Unsupported chain: {chain}")
        
        web3 = self.web3_connections[chain]
        
        # ERC20 ABI (minimal)
        abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=abi)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
        
        # Get token decimals
        decimals_abi = [{
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }]
        
        decimals_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=decimals_abi)
        decimals = decimals_contract.functions.decimals().call()
        
        return balance / (10 ** decimals)
    
    async def scan_arbitrage_opportunities(
        self,
        symbols: List[str],
        exchanges: List[str] = ['binance', 'coinbase', 'kraken'],
        min_profit_pct: float = 0.5
    ) -> List[ArbitrageOpportunity]:
        """Scan for arbitrage opportunities across exchanges"""
        
        opportunities = []
        
        try:
            # Initialize exchanges
            exchange_instances = {}
            for ex_name in exchanges:
                exchange_class = getattr(ccxt, ex_name)
                exchange_instances[ex_name] = exchange_class()
            
            # Fetch prices for each symbol
            for symbol in symbols:
                prices = {}
                
                for ex_name, exchange in exchange_instances.items():
                    try:
                        ticker = await exchange.fetch_ticker(symbol)
                        prices[ex_name] = {
                            'bid': ticker['bid'],
                            'ask': ticker['ask'],
                            'volume': ticker.get('quoteVolume', 0)
                        }
                    except Exception as e:
                        logger.warning(f"Failed to fetch {symbol} from {ex_name}: {e}")
                
                # Find arbitrage opportunities
                if len(prices) >= 2:
                    exchanges_list = list(prices.keys())
                    
                    for i, ex1 in enumerate(exchanges_list):
                        for ex2 in exchanges_list[i+1:]:
                            # Buy on ex1, sell on ex2
                            buy_price = prices[ex1]['ask']
                            sell_price = prices[ex2]['bid']
                            
                            if sell_price > buy_price:
                                profit_pct = ((sell_price - buy_price) / buy_price) * 100
                                
                                if profit_pct >= min_profit_pct:
                                    opportunities.append(ArbitrageOpportunity(
                                        buy_exchange=ex1,
                                        sell_exchange=ex2,
                                        symbol=symbol,
                                        price_difference=sell_price - buy_price,
                                        profit_potential=profit_pct,
                                        volume_available=min(
                                            prices[ex1].get('volume', 0),
                                            prices[ex2].get('volume', 0)
                                        ),
                                        timestamp=datetime.now()
                                    ))
                            
                            # Buy on ex2, sell on ex1
                            buy_price = prices[ex2]['ask']
                            sell_price = prices[ex1]['bid']
                            
                            if sell_price > buy_price:
                                profit_pct = ((sell_price - buy_price) / buy_price) * 100
                                
                                if profit_pct >= min_profit_pct:
                                    opportunities.append(ArbitrageOpportunity(
                                        buy_exchange=ex2,
                                        sell_exchange=ex1,
                                        symbol=symbol,
                                        price_difference=sell_price - buy_price,
                                        profit_potential=profit_pct,
                                        volume_available=min(
                                            prices[ex2].get('volume', 0),
                                            prices[ex1].get('volume', 0)
                                        ),
                                        timestamp=datetime.now()
                                    ))
            
            # Close exchanges
            for exchange in exchange_instances.values():
                await exchange.close()
        
        except Exception as e:
            logger.error(f"Arbitrage scan error: {e}")
        
        return sorted(opportunities, key=lambda x: x.profit_potential, reverse=True)


class YieldFarmingOptimizer:
    """Optimizer for yield farming strategies"""
    
    def __init__(self):
        self.pool_database: List[LiquidityPool] = []
    
    def add_pool(self, pool: LiquidityPool):
        """Add a liquidity pool to database"""
        self.pool_database.append(pool)
    
    def calculate_impermanent_loss(self, price_ratio_change: float) -> float:
        """Calculate impermanent loss for a given price change"""
        # IL formula for constant product AMM
        if price_ratio_change <= 0:
            return 0
        
        r = price_ratio_change
        il = 2 * (r ** 0.5) / (1 + r) - 1
        return abs(il) * 100
    
    def find_best_pools(
        self,
        risk_tolerance: float = 0.5,
        min_tvl: float = 1e6,
        chains: Optional[List[ChainType]] = None
    ) -> List[LiquidityPool]:
        """Find best yield farming pools based on risk tolerance"""
        
        filtered_pools = [
            p for p in self.pool_database
            if p.tvl >= min_tvl and
            (chains is None or p.chain in chains)
        ]
        
        # Score pools based on APR/risk ratio
        scored_pools = []
        for pool in filtered_pools:
            # Simple risk score (lower fee = lower risk typically)
            risk_score = pool.fee_tier * 100
            
            # Adjust APR by risk
            if risk_tolerance < 0.3:  # Low risk tolerance
                adjusted_apr = pool.apr / (risk_score + 1)
            elif risk_tolerance < 0.7:  # Medium risk tolerance
                adjusted_apr = pool.apr
            else:  # High risk tolerance
                adjusted_apr = pool.apr * (1 + risk_score / 100)
            
            scored_pools.append((pool, adjusted_apr))
        
        # Sort by adjusted APR
        scored_pools.sort(key=lambda x: x[1], reverse=True)
        
        return [p[0] for p in scored_pools[:10]]
    
    def optimize_yield_strategy(
        self,
        capital: float,
        pools: List[LiquidityPool],
        auto_compound: bool = True
    ) -> Dict[str, Any]:
        """Optimize yield farming strategy across multiple pools"""
        
        if not pools:
            return {"error": "No pools provided"}
        
        # Diversify across top pools
        num_pools = min(5, len(pools))
        selected_pools = pools[:num_pools]
        
        # Equal weight allocation
        allocation_per_pool = capital / num_pools
        
        # Calculate expected returns
        total_expected_return = 0
        for pool in selected_pools:
            # Annual return
            annual_return = allocation_per_pool * (pool.apr / 100)
            
            # Compound frequency (daily compounding if enabled)
            if auto_compound:
                # Daily compounding
                daily_rate = pool.apr / 365 / 100
                compounded_return = allocation_per_pool * ((1 + daily_rate) ** 365 - 1)
                total_expected_return += compounded_return
            else:
                total_expected_return += annual_return
        
        # Estimate impermanent loss (simplified)
        avg_il = sum(self.calculate_impermanent_loss(0.5) for _ in selected_pools) / len(selected_pools)
        il_impact = capital * (avg_il / 100) * 0.5  # Assume 50% chance of IL
        
        net_return = total_expected_return - il_impact
        
        return {
            "total_capital": capital,
            "num_pools": num_pools,
            "allocations": [
                {
                    "pool": f"{pool.token0}/{pool.token1}",
                    "dex": pool.dex.value,
                    "chain": pool.chain.value,
                    "allocation": allocation_per_pool,
                    "apr": pool.apr
                }
                for pool in selected_pools
            ],
            "expected_annual_return": total_expected_return,
            "estimated_impermanent_loss": il_impact,
            "net_expected_return": net_return,
            "net_apr": (net_return / capital) * 100
        }


async def demo_defi_features():
    """Demo of DeFi features"""
    
    print("=" * 70)
    print("💰 DEFI & CRYPTO INTEGRATION DEMO")
    print("=" * 70)
    
    # Demo 1: Arbitrage Scanner
    print("\n🔍 SCANNING FOR ARBITRAGE OPPORTUNITIES...")
    
    analyzer = DeFiAnalyzer()
    opportunities = await analyzer.scan_arbitrage_opportunities(
        symbols=['BTC/USDT', 'ETH/USDT'],
        exchanges=['binance', 'coinbase'],
        min_profit_pct=0.1
    )
    
    if opportunities:
        print(f"\nFound {len(opportunities)} arbitrage opportunities:")
        for opp in opportunities[:3]:
            print(f"  • {opp.symbol}: Buy on {opp.buy_exchange}, Sell on {opp.sell_exchange}")
            print(f"    Profit: {opp.profit_potential:.2f}% | Volume: ${opp.volume_available:,.2f}")
    else:
        print("  No significant arbitrage opportunities found")
    
    # Demo 2: Yield Farming Optimization
    print("\n🌾 YIELD FARMING OPTIMIZATION...")
    
    optimizer = YieldFarmingOptimizer()
    
    # Add sample pools
    sample_pools = [
        LiquidityPool(
            pool_address="0x...",
            token0="USDC",
            token1="ETH",
            reserve0=100e6,
            reserve1=50e3,
            fee_tier=0.003,
            apr=15.5,
            tvl=200e6,
            dex=DexType.UNISWAP,
            chain=ChainType.ETHEREUM
        ),
        LiquidityPool(
            pool_address="0x...",
            token0="USDT",
            token1="BUSD",
            reserve0=500e6,
            reserve1=500e6,
            fee_tier=0.0005,
            apr=8.2,
            tvl=1e9,
            dex=DexType.CURVE,
            chain=ChainType.ETHEREUM
        ),
        LiquidityPool(
            pool_address="0x...",
            token0="BNB",
            token1="BUSD",
            reserve0=2e6,
            reserve1=600e6,
            fee_tier=0.0025,
            apr=22.3,
            tvl=500e6,
            dex=DexType.PANCAKESWAP,
            chain=ChainType.BSC
        )
    ]
    
    for pool in sample_pools:
        optimizer.add_pool(pool)
    
    # Find best pools for medium risk
    best_pools = optimizer.find_best_pools(risk_tolerance=0.5, min_tvl=100e6)
    
    print(f"\nTop {len(best_pools)} pools for medium risk:")
    for i, pool in enumerate(best_pools, 1):
        print(f"  {i}. {pool.token0}/{pool.token1} on {pool.dex.value} ({pool.chain.value})")
        print(f"     APR: {pool.apr:.2f}% | TVL: ${pool.tvl/1e6:.1f}M | Fee: {pool.fee_tier*100:.3f}%")
    
    # Optimize strategy
    print("\n💼 OPTIMIZED YIELD STRATEGY ($100,000 capital):")
    strategy = optimizer.optimize_yield_strategy(
        capital=100000,
        pools=best_pools,
        auto_compound=True
    )
    
    if "error" not in strategy:
        print(f"  Pools: {strategy['num_pools']}")
        print(f"  Expected Annual Return: ${strategy['expected_annual_return']:,.2f}")
        print(f"  Est. Impermanent Loss: ${strategy['estimated_impermanent_loss']:,.2f}")
        print(f"  Net Expected Return: ${strategy['net_expected_return']:,.2f}")
        print(f"  Net APR: {strategy['net_apr']:.2f}%")
        
        print("\n  Allocations:")
        for alloc in strategy['allocations']:
            print(f"    • {alloc['pool']}: ${alloc['allocation']:,.2f} @ {alloc['apr']:.2f}% APR")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_defi_features())
