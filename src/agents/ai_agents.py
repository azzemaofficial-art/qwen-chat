"""
Trading Advisor Pro v7.0 - AI Trading Agents with LLM Integration
Autonomous trading agents powered by large language models
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import openai
from pydantic import BaseModel, Field

from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalyzer
from src.risk_management import AdvancedRiskManager
from src.ml_predictor import MLPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentRole(Enum):
    ANALYST = "analyst"
    RISK_MANAGER = "risk_manager"
    TRADER = "trader"
    PORTFOLIO_MANAGER = "portfolio_manager"
    SENTIMENT_ANALYST = "sentiment_analyst"


class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"


@dataclass
class AgentDecision:
    agent_role: str
    action: str
    confidence: float
    reasoning: str
    timestamp: datetime
    metadata: Dict[str, Any] = None


@dataclass
class TradingSignal:
    symbol: str
    action: str  # BUY, SELL, HOLD
    quantity: int
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    reasoning: List[str]
    agents_consensus: Dict[str, str]
    timestamp: datetime


class BaseTradingAgent:
    """Base class for all trading agents"""
    
    def __init__(self, role: AgentRole, llm_api_key: Optional[str] = None):
        self.role = role
        self.llm_api_key = llm_api_key
        self.decision_history: List[AgentDecision] = []
        
        if llm_api_key:
            openai.api_key = llm_api_key
    
    async def analyze(self, market_data: Dict) -> AgentDecision:
        """Analyze market data and make decision"""
        raise NotImplementedError
    
    def _build_prompt(self, context: str, data: Dict) -> str:
        """Build prompt for LLM"""
        return f"""
You are an expert {self.role.value} for a professional trading system.

Market Context:
{context}

Data:
{json.dumps(data, indent=2)}

Provide your analysis and recommendation in JSON format:
{{
    "action": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation",
    "key_factors": ["factor1", "factor2"]
}}
"""
    
    async def _query_llm(self, prompt: str) -> Dict:
        """Query LLM for analysis"""
        if not self.llm_api_key:
            return {"action": "HOLD", "confidence": 0.5, "reasoning": "LLM not configured"}
        
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        
        except Exception as e:
            logger.error(f"LLM query error: {e}")
            return {"action": "HOLD", "confidence": 0.5, "reasoning": f"Error: {str(e)}"}


class TechnicalAnalystAgent(BaseTradingAgent):
    """Agent specialized in technical analysis"""
    
    def __init__(self, llm_api_key: Optional[str] = None):
        super().__init__(AgentRole.ANALYST, llm_api_key)
    
    async def analyze(self, market_data: Dict) -> AgentDecision:
        df = market_data.get('price_data')
        
        if df is None:
            return AgentDecision(
                agent_role=self.role.value,
                action="HOLD",
                confidence=0.0,
                reasoning="No price data available",
                timestamp=datetime.now()
            )
        
        # Perform technical analysis
        analyzer = TechnicalAnalyzer(df)
        analyzer.calculate_all_indicators()
        signals = analyzer.generate_signals()
        overall_signal, confidence, direction = analyzer.get_overall_signal()
        patterns = analyzer.detect_candlestick_patterns()
        
        # Build context for LLM
        context = f"""
Technical Analysis Summary:
- Overall Signal: {overall_signal.name}
- Confidence: {confidence:.2f}
- Direction: {direction}
- Indicators Analyzed: {len(signals)}
- Patterns Detected: {len(patterns)}

Key Levels:
- Support: {analyzer.get_support_resistance().get('support', 'N/A')}
- Resistance: {analyzer.get_support_resistance().get('resistance', 'N/A')}
"""
        
        data = {
            "signal_counts": {
                "bullish": len([s for s in signals if s.signal.name == "BUY"]),
                "bearish": len([s for s in signals if s.signal.name == "SELL"]),
                "neutral": len([s for s in signals if s.signal.name == "HOLD"])
            },
            "patterns": patterns[:5],  # Top 5 patterns
            "current_price": float(df['Close'].iloc[-1])
        }
        
        # Get LLM analysis
        prompt = self._build_prompt(context, data)
        llm_result = await self._query_llm(prompt)
        
        decision = AgentDecision(
            agent_role=self.role.value,
            action=llm_result.get("action", overall_signal.name),
            confidence=float(llm_result.get("confidence", confidence)),
            reasoning=llm_result.get("reasoning", direction),
            timestamp=datetime.now(),
            metadata={"technical_signals": len(signals), "patterns": len(patterns)}
        )
        
        self.decision_history.append(decision)
        return decision


class RiskManagerAgent(BaseTradingAgent):
    """Agent specialized in risk assessment"""
    
    def __init__(self, llm_api_key: Optional[str] = None):
        super().__init__(AgentRole.RISK_MANAGER, llm_api_key)
    
    async def analyze(self, market_data: Dict) -> AgentDecision:
        df = market_data.get('price_data')
        
        if df is None:
            return AgentDecision(
                agent_role=self.role.value,
                action="HOLD",
                confidence=0.0,
                reasoning="No price data for risk analysis",
                timestamp=datetime.now()
            )
        
        risk_manager = AdvancedRiskManager()
        returns = df['Close'].pct_change().dropna()
        
        # Calculate risk metrics
        var_95 = risk_manager.calculate_var(returns, confidence_level=0.95)
        cvar_95 = risk_manager.calculate_cvar(returns, confidence_level=0.95)
        volatility = returns.std()
        max_drawdown = risk_manager.calculate_max_drawdown(df['Close'])
        
        context = f"""
Risk Metrics:
- VaR (95%): {var_95:.4f} ({var_95*100:.2f}%)
- CVaR (95%): {cvar_95:.4f} ({cvar_95*100:.2f}%)
- Volatility: {volatility:.4f} ({volatility*100:.2f}%)
- Max Drawdown: {max_drawdown:.4f} ({max_drawdown*100:.2f}%)

Risk Assessment:
- Low Risk: VaR < 2%
- Medium Risk: VaR 2-5%
- High Risk: VaR > 5%
"""
        
        data = {
            "var_95": float(var_95),
            "cvar_95": float(cvar_95),
            "volatility": float(volatility),
            "max_drawdown": float(max_drawdown),
            "risk_level": "HIGH" if var_95 > 0.05 else "MEDIUM" if var_95 > 0.02 else "LOW"
        }
        
        prompt = self._build_prompt(context, data)
        llm_result = await self._query_llm(prompt)
        
        # Risk manager can veto trades
        action = "HOLD" if data["risk_level"] == "HIGH" else llm_result.get("action", "HOLD")
        
        decision = AgentDecision(
            agent_role=self.role.value,
            action=action,
            confidence=float(llm_result.get("confidence", 0.5)),
            reasoning=f"Risk Level: {data['risk_level']}. {llm_result.get('reasoning', '')}",
            timestamp=datetime.now(),
            metadata=data
        )
        
        self.decision_history.append(decision)
        return decision


class SentimentAnalystAgent(BaseTradingAgent):
    """Agent specialized in sentiment analysis"""
    
    def __init__(self, llm_api_key: Optional[str] = None):
        super().__init__(AgentRole.SENTIMENT_ANALYST, llm_api_key)
    
    async def analyze(self, market_data: Dict) -> AgentDecision:
        news_data = market_data.get('news', [])
        social_sentiment = market_data.get('social_sentiment', {})
        
        context = f"""
Sentiment Analysis:
- News Articles: {len(news_data)}
- Social Media Sentiment: {social_sentiment.get('score', 'N/A')}
- Twitter Mentions: {social_sentiment.get('twitter_mentions', 'N/A')}
- Reddit Sentiment: {social_sentiment.get('reddit_sentiment', 'N/A')}
"""
        
        data = {
            "news_count": len(news_data),
            "social_score": social_sentiment.get('score', 0),
            "trending": social_sentiment.get('trending', False)
        }
        
        prompt = self._build_prompt(context, data)
        llm_result = await self._query_llm(prompt)
        
        decision = AgentDecision(
            agent_role=self.role.value,
            action=llm_result.get("action", "HOLD"),
            confidence=float(llm_result.get("confidence", 0.5)),
            reasoning=llm_result.get("reasoning", "No significant sentiment signal"),
            timestamp=datetime.now(),
            metadata=data
        )
        
        self.decision_history.append(decision)
        return decision


class MultiAgentOrchestrator:
    """Orchestrates multiple trading agents for consensus decisions"""
    
    def __init__(self, llm_api_key: Optional[str] = None):
        self.agents = {
            'technical': TechnicalAnalystAgent(llm_api_key),
            'risk': RiskManagerAgent(llm_api_key),
            'sentiment': SentimentAnalystAgent(llm_api_key)
        }
        self.consensus_history: List[TradingSignal] = []
    
    async def analyze_symbol(self, symbol: str, capital: float = 100000) -> TradingSignal:
        """Get consensus decision from all agents"""
        
        # Fetch market data
        fetcher = DataFetcher()
        df = fetcher.get_stock_data(symbol, period='2y')
        
        if df is None or len(df) < 100:
            raise ValueError(f"Insufficient data for {symbol}")
        
        current_price = float(df['Close'].iloc[-1])
        
        # Prepare market data for agents
        market_data = {
            'price_data': df,
            'symbol': symbol,
            'current_price': current_price
        }
        
        # Run all agents in parallel
        tasks = [agent.analyze(market_data) for agent in self.agents.values()]
        decisions = await asyncio.gather(*tasks)
        
        # Build consensus
        actions = [d.action for d in decisions]
        confidences = [d.confidence for d in decisions]
        
        # Weighted voting (risk manager has veto power)
        weights = {'technical': 0.4, 'risk': 0.4, 'sentiment': 0.2}
        
        weighted_scores = {
            'BUY': 0,
            'SELL': 0,
            'HOLD': 0
        }
        
        for agent_name, decision in zip(self.agents.keys(), decisions):
            weight = weights.get(agent_name, 0.33)
            if decision.action == "HOLD" and agent_name == 'risk':
                # Risk manager veto
                weighted_scores['HOLD'] += weight * 2
            else:
                weighted_scores[decision.action] += weight * decision.confidence
        
        # Determine consensus action
        consensus_action = max(weighted_scores, key=weighted_scores.get)
        consensus_confidence = max(weighted_scores.values())
        
        # Calculate position size based on confidence and risk
        base_position = capital * 0.1  # 10% base allocation
        position_size = base_position * consensus_confidence
        
        # Set stop loss and take profit
        volatility = df['Close'].pct_change().std()
        stop_loss = current_price * (1 - 2 * volatility) if consensus_action == "BUY" else current_price * (1 + 2 * volatility)
        take_profit = current_price * (1 + 3 * volatility) if consensus_action == "BUY" else current_price * (1 - 3 * volatility)
        
        signal = TradingSignal(
            symbol=symbol,
            action=consensus_action,
            quantity=int(position_size / current_price),
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=consensus_confidence,
            reasoning=[d.reasoning for d in decisions],
            agents_consensus={
                agent_name: decision.action 
                for agent_name, decision in zip(self.agents.keys(), decisions)
            },
            timestamp=datetime.now()
        )
        
        self.consensus_history.append(signal)
        return signal
    
    def get_agent_performance(self) -> Dict:
        """Get performance metrics for each agent"""
        performance = {}
        
        for agent_name, agent in self.agents.items():
            decisions = agent.decision_history
            if decisions:
                performance[agent_name] = {
                    "total_decisions": len(decisions),
                    "avg_confidence": sum(d.confidence for d in decisions) / len(decisions),
                    "last_decision": asdict(decisions[-1]) if decisions else None
                }
        
        return performance


async def demo_multi_agent_trading():
    """Demo of multi-agent trading system"""
    
    print("=" * 70)
    print("🤖 MULTI-AGENT AI TRADING SYSTEM DEMO")
    print("=" * 70)
    
    # Initialize orchestrator (without LLM for demo)
    orchestrator = MultiAgentOrchestrator(llm_api_key=None)
    
    # Analyze a symbol
    symbol = "AAPL"
    print(f"\n📊 Analyzing {symbol}...\n")
    
    signal = await orchestrator.analyze_symbol(symbol, capital=100000)
    
    print(f"🎯 CONSENSUS SIGNAL for {symbol}")
    print(f"   Action: {signal.action}")
    print(f"   Confidence: {signal.confidence:.2f}")
    print(f"   Quantity: {signal.quantity}")
    print(f"   Entry: ${signal.entry_price:.2f}")
    print(f"   Stop Loss: ${signal.stop_loss:.2f}")
    print(f"   Take Profit: ${signal.take_profit:.2f}")
    print(f"\n📝 Agent Consensus:")
    for agent, action in signal.agents_consensus.items():
        print(f"   {agent}: {action}")
    print(f"\n💡 Reasoning:")
    for i, reason in enumerate(signal.reasoning, 1):
        print(f"   {i}. {reason[:100]}...")
    
    # Show agent performance
    print(f"\n📈 Agent Performance:")
    performance = orchestrator.get_agent_performance()
    for agent_name, metrics in performance.items():
        print(f"   {agent_name}: {metrics['total_decisions']} decisions, avg confidence: {metrics['avg_confidence']:.2f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_multi_agent_trading())
