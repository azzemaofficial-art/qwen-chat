"""
Trading Advisor Pro v7.0 - API Gateway & WebSocket Server
Enterprise-grade REST API and real-time WebSocket interface
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import json
import logging
from enum import Enum
import jwt
from datetime import timedelta

# Import existing modules
from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalyzer
from src.ml_predictor import MLPredictor
from src.risk_management import AdvancedRiskManager
from src.portfolio_optimizer import PortfolioOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Advisor Pro API",
    description="Enterprise Trading System API with Real-time Data",
    version="7.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


class AnalysisRequest(BaseModel):
    symbol: str
    include_ml: bool = True
    include_technical: bool = True
    include_risk: bool = True
    horizon: str = "1d"


class PortfolioRequest(BaseModel):
    symbols: List[str]
    capital: float = 100000.0
    risk_tolerance: float = 0.5
    optimization_method: str = "quantum"


class TradeSignal(BaseModel):
    symbol: str
    action: str
    confidence: float
    price: float
    timestamp: datetime
    reasoning: List[str]


class MarketData(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime


# Active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}

# JWT Configuration
JWT_SECRET_KEY = "your-secret-key-change-in-production"  # Cambiare in produzione
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30


class TokenPayload(BaseModel):
    """JWT token payload structure"""
    user_id: str
    role: str
    exp: datetime
    iat: datetime


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token scaduto")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Token invalido: {e}")
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Validate JWT token and return user info"""
    token = credentials.credentials
    
    payload = verify_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Token non valido o scaduto",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": payload.get("user_id"),
        "role": payload.get("role"),
        "exp": payload.get("exp")
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "7.0.0"
    }


@app.get("/api/v1/market/{symbol}", response_model=MarketData)
async def get_market_data(symbol: str, user: dict = Depends(get_current_user)):
    """Get real-time market data for a symbol"""
    try:
        fetcher = DataFetcher()
        df = fetcher.get_stock_data(symbol, period='1d')
        
        if df is None or len(df) == 0:
            raise HTTPException(status_code=404, detail="Symbol not found")
        
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current
        
        return MarketData(
            symbol=symbol,
            price=float(current['Close']),
            change=float(current['Close'] - prev['Close']),
            change_percent=float((current['Close'] - prev['Close']) / prev['Close'] * 100),
            volume=int(current.get('Volume', 0)),
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze", response_model=Dict[str, Any])
async def analyze_symbol(request: AnalysisRequest, user: dict = Depends(get_current_user)):
    """Comprehensive symbol analysis"""
    try:
        fetcher = DataFetcher()
        df = fetcher.get_stock_data(request.symbol, period='2y')
        
        if df is None:
            raise HTTPException(status_code=404, detail="Insufficient data")
        
        result = {
            "symbol": request.symbol,
            "timestamp": datetime.now().isoformat(),
            "analysis": {}
        }
        
        # Technical Analysis
        if request.include_technical:
            analyzer = TechnicalAnalyzer(df)
            analyzer.calculate_all_indicators()
            signals = analyzer.generate_signals()
            overall_signal, confidence, direction = analyzer.get_overall_signal()
            
            result["analysis"]["technical"] = {
                "signal": overall_signal.name,
                "confidence": confidence,
                "direction": direction,
                "indicators_count": len(signals)
            }
        
        # ML Prediction
        if request.include_ml:
            df_ml = df.copy()
            df_ml['MA20'] = df_ml['Close'].rolling(20).mean()
            df_ml['RSI'] = 14  # Simplified
            
            ml_predictor = MLPredictor(horizon=request.horizon)
            ml_metrics = ml_predictor.train(df_ml)
            
            if 'error' not in ml_metrics:
                prediction = ml_predictor.predict(df_ml)
                result["analysis"]["ml"] = prediction
        
        # Risk Metrics
        if request.include_risk:
            risk_manager = AdvancedRiskManager()
            returns = df['Close'].pct_change().dropna()
            var_95 = risk_manager.calculate_var(returns, confidence_level=0.95)
            cvar = risk_manager.calculate_cvar(returns, confidence_level=0.95)
            
            result["analysis"]["risk"] = {
                "var_95": float(var_95),
                "cvar_95": float(cvar),
                "volatility": float(returns.std())
            }
        
        return result
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/portfolio/optimize", response_model=Dict[str, Any])
async def optimize_portfolio(request: PortfolioRequest, user: dict = Depends(get_current_user)):
    """Optimize portfolio allocation"""
    try:
        optimizer = PortfolioOptimizer(capital=request.capital)
        
        # Fetch data for all symbols
        prices_data = {}
        fetcher = DataFetcher()
        
        for symbol in request.symbols:
            df = fetcher.get_stock_data(symbol, period='2y')
            if df is not None:
                prices_data[symbol] = df['Close']
        
        if len(prices_data) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 valid symbols")
        
        # Optimize
        optimal_weights = optimizer.optimize_modern_portfolioTheory(
            list(prices_data.keys()),
            prices_data
        )
        
        return {
            "portfolio": {
                "symbols": request.symbols,
                "capital": request.capital,
                "optimal_weights": optimal_weights,
                "optimization_method": request.optimization_method,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        logger.error(f"Portfolio optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/market/{symbol}")
async def websocket_market_data(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for real-time market data"""
    await websocket.accept()
    
    if symbol not in active_connections:
        active_connections[symbol] = []
    active_connections[symbol].append(websocket)
    
    try:
        fetcher = DataFetcher()
        
        while True:
            try:
                # Fetch latest data
                df = fetcher.get_stock_data(symbol, period='1d')
                
                if df is not None and len(df) > 0:
                    current = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else current
                    
                    data = {
                        "type": "market_update",
                        "symbol": symbol,
                        "price": float(current['Close']),
                        "change": float(current['Close'] - prev['Close']),
                        "change_percent": float((current['Close'] - prev['Close']) / prev['Close'] * 100),
                        "volume": int(current.get('Volume', 0)),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send_json(data)
                
                # Wait before next update
                await asyncio.sleep(5)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)
    
    finally:
        active_connections[symbol].remove(websocket)
        if not active_connections[symbol]:
            del active_connections[symbol]


@app.websocket("/ws/signals")
async def websocket_trading_signals(websocket: WebSocket):
    """WebSocket endpoint for trading signals"""
    await websocket.accept()
    
    connection_id = f"signals_{id(websocket)}"
    if connection_id not in active_connections:
        active_connections[connection_id] = []
    active_connections[connection_id].append(websocket)
    
    try:
        while True:
            # Listen for subscription requests
            data = await websocket.receive_text()
            request = json.loads(data)
            
            if request.get("type") == "subscribe":
                symbols = request.get("symbols", [])
                
                # Send acknowledgment
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": symbols
                })
                
                # Start sending signals (simplified)
                for symbol in symbols:
                    signal = TradeSignal(
                        symbol=symbol,
                        action="HOLD",
                        confidence=0.5,
                        price=0.0,
                        timestamp=datetime.now(),
                        reasoning=["Demo signal"]
                    )
                    await websocket.send_json({
                        "type": "signal",
                        "data": signal.dict()
                    })
    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    finally:
        if connection_id in active_connections:
            active_connections[connection_id].remove(websocket)


@app.get("/api/v1/screener")
async def stock_screener(
    min_market_cap: float = 1e9,
    max_pe_ratio: float = 50,
    min_volume: int = 1000000,
    sector: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Stock screener with filters"""
    # Simplified implementation
    return {
        "results": [],
        "filters": {
            "min_market_cap": min_market_cap,
            "max_pe_ratio": max_pe_ratio,
            "min_volume": min_volume,
            "sector": sector
        },
        "count": 0
    }


@app.get("/api/v1/news/{symbol}")
async def get_news(symbol: str, limit: int = 10, user: dict = Depends(get_current_user)):
    """Get news for a symbol"""
    from src.news_analyzer import NewsAnalyzer
    
    analyzer = NewsAnalyzer()
    result = analyzer.analyze_symbol_news(symbol, limit=limit)
    
    return {
        "symbol": symbol,
        "articles": result.get("articles", []),
        "sentiment": result.get("sentiment_label", "NEUTRAL"),
        "sentiment_score": result.get("sentiment_score", 0)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
