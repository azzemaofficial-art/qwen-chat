"""
Recommendation Engine - Motore di raccomandazione trading
Combina analisi tecnica, sentiment e fattori di rischio per generare consigli precisi
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


class ActionType(Enum):
    STRONG_BUY = "FORTE_ACQUISTO"
    BUY = "ACQUISTO"
    HOLD = "ATTESA/MANTIENI"
    SELL = "VENDITA"
    STRONG_SELL = "FORTE_VENDITA"


@dataclass
class TradeRecommendation:
    """Raccomandazione di trading completa"""
    symbol: str
    action: ActionType
    confidence: float  # 0-100%
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit_1: Optional[float]  # Target conservativo
    take_profit_2: Optional[float]  # Target aggressivo
    leverage_suggestion: float  # 1x = nessun leverage
    position_size_pct: float  # % del portafoglio
    time_horizon: str  # Breve/Medio/Lungo termine
    risk_level: str  # Basso/Medio/Alto
    reasoning: List[str]
    technical_score: float
    sentiment_score: float
    overall_score: float


class RiskManager:
    """Gestione del rischio e calcolo position sizing"""
    
    def __init__(self, max_risk_per_trade: float = 0.02):
        """
        Args:
            max_risk_per_trade: Rischio massimo per trade (default 2%)
        """
        self.max_risk_per_trade = max_risk_per_trade
    
    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        risk_tolerance: str = "medio"
    ) -> Tuple[float, float]:
        """
        Calcola la dimensione della posizione basata sul rischio
        
        Returns:
            Tuple con (numero di azioni, percentuale del capitale)
        """
        if entry_price <= 0 or stop_loss <= 0:
            return 0, 0.0
        
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            return 0, 0.0
        
        # Adegua rischio in base alla tolleranza
        risk_multipliers = {
            "basso": 0.5,
            "medio": 1.0,
            "alto": 1.5
        }
        
        adjusted_risk = self.max_risk_per_trade * risk_multipliers.get(risk_tolerance, 1.0)
        max_loss_amount = capital * adjusted_risk
        
        num_shares = int(max_loss_amount / risk_per_share)
        position_value = num_shares * entry_price
        position_pct = (position_value / capital) * 100 if capital > 0 else 0
        
        return num_shares, min(position_pct, 25.0)  # Max 25% per trade
    
    def calculate_leverage_suggestion(
        self,
        confidence: float,
        volatility: float,
        risk_level: str
    ) -> float:
        """
        Suggerisce il leverage appropriato
        
        Args:
            confidence: Confidenza del segnale (0-100)
            volatility: Volatilità del titolo
            risk_level: Livello di rischio
        
        Returns:
            Leverage suggerito (1.0 = nessun leverage)
        """
        # Base leverage
        base_leverage = 1.0
        
        # Aumenta con alta confidenza
        if confidence >= 80:
            base_leverage = 1.5
        elif confidence >= 60:
            base_leverage = 1.2
        
        # Riduci con alta volatilità
        if volatility > 0.5:  # >50% annual volatility
            base_leverage *= 0.7
        elif volatility > 0.3:
            base_leverage *= 0.85
        
        # Riduci per alto rischio
        risk_reduction = {"basso": 1.0, "medio": 0.85, "alto": 0.7}
        base_leverage *= risk_reduction.get(risk_level, 0.85)
        
        return round(min(base_leverage, 3.0), 2)  # Max 3x


class RecommendationEngine:
    """Motore principale di raccomandazione"""
    
    def __init__(self, capital: float = 100000):
        """
        Args:
            capital: Capitale disponibile per il trading
        """
        self.capital = capital
        self.risk_manager = RiskManager()
    
    def analyze_technical_signals(
        self,
        technical_analysis_result: Dict
    ) -> Tuple[float, List[str]]:
        """
        Analizza i segnali tecnici e genera un score
        
        Returns:
            Tuple con (score tecnico, lista di ragioni)
        """
        score = 0.0
        reasons = []
        
        # Estrai segnali
        signals = technical_analysis_result.get('signals', [])
        overall_signal = technical_analysis_result.get('overall_signal', {})
        
        # Score dal segnale complessivo
        signal_confidence = overall_signal.get('confidence', 50)
        score += (signal_confidence / 100) * 40  # Max 40 punti
        
        if signal_confidence >= 70:
            reasons.append(f"Segnale tecnico forte ({signal_confidence:.0f}% confidenza)")
        elif signal_confidence >= 50:
            reasons.append(f"Segnale tecnico moderato ({signal_confidence:.0f}% confidenza)")
        
        # Analisi individuale indicatori
        rsi = technical_analysis_result.get('rsi', 50)
        if rsi < 30:
            score += 15
            reasons.append("RSI in ipervenduto (<30)")
        elif rsi > 70:
            score -= 15
            reasons.append("RSI in ipercomprato (>70)")
        
        macd_signal = technical_analysis_result.get('macd_signal', 'neutral')
        if macd_signal == 'bullish':
            score += 10
            reasons.append("MACD rialzista")
        elif macd_signal == 'bearish':
            score -= 10
            reasons.append("MACD ribassista")
        
        # Trend delle medie mobili
        ma_trend = technical_analysis_result.get('ma_trend', 'neutral')
        if ma_trend == 'bullish':
            score += 15
            reasons.append("Medie mobili allineate al rialzo")
        elif ma_trend == 'bearish':
            score -= 15
            reasons.append("Medie mobili allineate al ribasso")
        
        # Supporti/resistenze
        sr = technical_analysis_result.get('support_resistance', {})
        current_price = sr.get('current_price', 0)
        supports = sr.get('supports', [])
        resistances = sr.get('resistances', [])
        
        if supports and current_price > 0:
            nearest_support = max(s for s in supports if s < current_price) if any(s < current_price for s in supports) else None
            if nearest_support:
                distance_to_support = (current_price - nearest_support) / current_price * 100
                if distance_to_support < 3:
                    score += 5
                    reasons.append(f"Prezzo vicino a supporto ({distance_to_support:.1f}%)")
        
        if resistances and current_price > 0:
            nearest_resistance = min(r for r in resistances if r > current_price) if any(r > current_price for r in resistances) else None
            if nearest_resistance:
                distance_to_resistance = (nearest_resistance - current_price) / current_price * 100
                if distance_to_resistance < 3:
                    score -= 5
                    reasons.append(f"Prezzo vicino a resistenza ({distance_to_resistance:.1f}%)")
        
        # Normalizza score (0-100)
        final_score = max(0, min(100, 50 + score))
        
        return final_score, reasons
    
    def analyze_sentiment_signals(
        self,
        news_analysis_result: Dict
    ) -> Tuple[float, List[str]]:
        """
        Analizza il sentiment delle notizie
        
        Returns:
            Tuple con (score sentiment, lista di ragioni)
        """
        score = 50.0  # Base neutrale
        reasons = []
        
        overall_sentiment = news_analysis_result.get('overall_sentiment', 0)
        sentiment_label = news_analysis_result.get('sentiment_label', 'NEUTRALE')
        
        # Converti sentiment (-1 a +1) in score (0-100)
        normalized_score = 50 + (overall_sentiment * 50)
        score = normalized_score
        
        if overall_sentiment >= 0.5:
            reasons.append(f"Sentiment molto positivo ({sentiment_label})")
        elif overall_sentiment >= 0.2:
            reasons.append(f"Sentiment positivo ({sentiment_label})")
        elif overall_sentiment <= -0.5:
            reasons.append(f"Sentiment molto negativo ({sentiment_label})")
        elif overall_sentiment <= -0.2:
            reasons.append(f"Sentiment negativo ({sentiment_label})")
        else:
            reasons.append(f"Sentiment neutrale ({sentiment_label})")
        
        # Considera volume notizie
        articles_count = news_analysis_result.get('articles_count', 0)
        very_positive = news_analysis_result.get('very_positive_count', 0)
        very_negative = news_analysis_result.get('very_negative_count', 0)
        
        if articles_count > 0:
            if very_positive > very_negative * 2:
                score += 10
                reasons.append(f"Prevalenza notizie positive ({very_positive} vs {very_negative})")
            elif very_negative > very_positive * 2:
                score -= 10
                reasons.append(f"Prevalenza notizie negative ({very_negative} vs {very_positive})")
        
        final_score = max(0, min(100, score))
        
        return final_score, reasons
    
    def generate_recommendation(
        self,
        symbol: str,
        technical_data: Dict,
        news_data: Dict,
        current_price: float
    ) -> TradeRecommendation:
        """
        Genera una raccomandazione completa di trading
        
        Args:
            symbol: Simbolo del titolo
            technical_data: Risultati analisi tecnica
            news_data: Risultati analisi notizie
            current_price: Prezzo corrente
        
        Returns:
            TradeRecommendation completa
        """
        print(f"\nGenerazione raccomandazione per {symbol}...")
        
        # Analizza segnali
        tech_score, tech_reasons = self.analyze_technical_signals(technical_data)
        sent_score, sent_reasons = self.analyze_sentiment_signals(news_data)
        
        # Calcola score complessivo (70% tecnica, 30% sentiment)
        overall_score = (tech_score * 0.7) + (sent_score * 0.3)
        
        # Determina azione
        if overall_score >= 75:
            action = ActionType.STRONG_BUY
            time_horizon = "Medio termine (1-3 mesi)"
        elif overall_score >= 60:
            action = ActionType.BUY
            time_horizon = "Breve-Medio termine (2-6 settimane)"
        elif overall_score >= 40:
            action = ActionType.HOLD
            time_horizon = "In attesa di segnali più chiari"
        elif overall_score >= 25:
            action = ActionType.SELL
            time_horizon = "Breve termine (uscire gradualmente)"
        else:
            action = ActionType.STRONG_SELL
            time_horizon = "Immediato"
        
        # Calcola livelli di prezzo
        atr = technical_data.get('atr', current_price * 0.02)
        
        if action in [ActionType.STRONG_BUY, ActionType.BUY]:
            entry_price = current_price
            stop_loss = current_price - (atr * 2)
            take_profit_1 = current_price + (atr * 2)
            take_profit_2 = current_price + (atr * 4)
            risk_level = "medio" if overall_score < 70 else "basso"
        elif action in [ActionType.STRONG_SELL, ActionType.SELL]:
            entry_price = current_price
            stop_loss = current_price + (atr * 2)
            take_profit_1 = current_price - (atr * 2)
            take_profit_2 = current_price - (atr * 4)
            risk_level = "alto"
        else:
            entry_price = current_price
            stop_loss = None
            take_profit_1 = None
            take_profit_2 = None
            risk_level = "medio"
        
        # Calcola position sizing e leverage
        confidence = overall_score
        volatility = technical_data.get('volatility', 0.3)
        
        if stop_loss:
            num_shares, position_pct = self.risk_manager.calculate_position_size(
                self.capital, entry_price, stop_loss, risk_level
            )
        else:
            num_shares, position_pct = 0, 0
        
        leverage = self.risk_manager.calculate_leverage_suggestion(
            confidence, volatility, risk_level
        )
        
        # Unisci tutte le ragioni
        all_reasons = tech_reasons + sent_reasons
        
        recommendation = TradeRecommendation(
            symbol=symbol,
            action=action,
            confidence=round(overall_score, 1),
            entry_price=round(entry_price, 2) if entry_price else None,
            stop_loss=round(stop_loss, 2) if stop_loss else None,
            take_profit_1=round(take_profit_1, 2) if take_profit_1 else None,
            take_profit_2=round(take_profit_2, 2) if take_profit_2 else None,
            leverage_suggestion=leverage,
            position_size_pct=round(position_pct, 1),
            time_horizon=time_horizon,
            risk_level=risk_level,
            reasoning=all_reasons,
            technical_score=round(tech_score, 1),
            sentiment_score=round(sent_score, 1),
            overall_score=round(overall_score, 1)
        )
        
        return recommendation
    
    def format_recommendation(self, rec: TradeRecommendation) -> str:
        """Formatta la raccomandazione per la visualizzazione"""
        output = f"""
{'='*60}
RACCOMANDAZIONE TRADING: {rec.symbol}
{'='*60}

📊 AZIONE CONSIGLIATA: {rec.action.value}
   Confidenza: {rec.confidence}%

💰 DETTAGLI OPERATIVI:
   Prezzo ingresso: ${rec.entry_price}
   Stop Loss: ${rec.stop_loss if rec.stop_loss else 'N/A'}
   Take Profit 1: ${rec.take_profit_1 if rec.take_profit_1 else 'N/A'}
   Take Profit 2: ${rec.take_profit_2 if rec.take_profit_2 else 'N/A'}

📈 GESTIONE POSIZIONE:
   Dimensione posizione: {rec.position_size_pct}% del capitale
   Leverage suggerito: {rec.leverage_suggestion}x
   Livello di rischio: {rec.risk_level.upper()}
   Orizzonte temporale: {rec.time_horizon}

🔍 PUNTEGGI:
   Analisi Tecnica: {rec.technical_score}/100
   Sentiment News: {rec.sentiment_score}/100
   Score Complessivo: {rec.overall_score}/100

📝 MOTIVAZIONI:
"""
        for i, reason in enumerate(rec.reasoning, 1):
            output += f"   {i}. {reason}\n"
        
        output += f"""
⚠️ DISCLAIMER: Questa è solo analisi tecnica/statistica.
   Il trading comporta rischi. Fai sempre le tue ricerche.
{'='*60}
"""
        return output


if __name__ == "__main__":
    # Test con dati simulati
    engine = RecommendationEngine(capital=50000)
    
    technical_data = {
        'signals': ['buy', 'buy', 'neutral'],
        'overall_signal': {'confidence': 72},
        'rsi': 35,
        'macd_signal': 'bullish',
        'ma_trend': 'bullish',
        'atr': 3.5,
        'volatility': 0.25,
        'support_resistance': {
            'current_price': 175.0,
            'supports': [170, 165],
            'resistances': [180, 185]
        }
    }
    
    news_data = {
        'overall_sentiment': 0.3,
        'sentiment_label': 'POSITIVO',
        'articles_count': 15,
        'very_positive_count': 3,
        'very_negative_count': 1
    }
    
    rec = engine.generate_recommendation(
        symbol="AAPL",
        technical_data=technical_data,
        news_data=news_data,
        current_price=175.0
    )
    
    print(engine.format_recommendation(rec))
