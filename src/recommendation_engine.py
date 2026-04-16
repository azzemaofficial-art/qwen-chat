"""
Recommendation Engine - Motore di raccomandazione trading
Combina analisi tecnica, sentiment e fattori di rischio per generare consigli precisi
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import numpy as np
import json


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
    # Campi per il sistema di voto
    recommendation_id: str = field(default_factory=lambda: "")
    created_at: datetime = field(default_factory=datetime.now)
    user_rating: Optional[int] = None  # Voto utente 1-5 (5 = perfetto per imparare e fare trading)
    rating_criteria: Dict[str, int] = field(default_factory=dict)  # Criteri dettagliati
    rating_notes: str = ""
    actual_outcome: Optional[Dict] = None  # Risultato effettivo del trade
    is_speculative: bool = False  # Indica se il titolo è speculativo in questo momento
    speculation_reasons: List[str] = field(default_factory=list)  # Motivi della speculazione
    learning_points: List[str] = field(default_factory=list)  # Punti educativi da imparare


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
        self.recommendations_history: List[TradeRecommendation] = []
        self.rating_criteria_definitions = {
            "accuratezza_prezzo": "Accuratezza del prezzo di ingresso",
            "tempistica": "Tempistica dell'operazione",
            "gestione_rischio": "Qualità della gestione del rischio (stop loss/take profit)",
            "chiarezza": "Chiarezza delle motivazioni fornite",
            "performance": "Performance effettiva del trade"
        }
        # Criteri avanzati per voto complesso 6/5 (perfetto per trading e apprendimento)
        self.advanced_criteria = {
            "potenziale_profitto": "Potenziale di profitto dell'operazione",
            "qualita_setup": "Qualità del setup tecnico",
            "apprendimento": "Valore educativo dell'operazione",
            "gestione_emotiva": "Gestione dello stress emotivo richiesto",
            "timing_mercato": "Timing rispetto alle condizioni di mercato"
        }
    
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
        Genera una raccomandazione completa di trading con analisi speculativa e punti educativi
        
        Args:
            symbol: Simbolo del titolo
            technical_data: Risultati analisi tecnica
            news_data: Risultati analisi notizie
            current_price: Prezzo corrente
        
        Returns:
            TradeRecommendation completa con valutazione speculativa e apprendimento
        """
        print(f"\n🔍 Generazione raccomandazione per {symbol}...")
        
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
        
        # Analisi speculativa avanzata
        is_speculative, speculation_reasons = self._analyze_speculation_opportunity(
            symbol, technical_data, news_data, current_price
        )
        
        # Genera punti educativi basati sul setup
        learning_points = self._generate_learning_points(
            symbol, action, technical_data, news_data, is_speculative
        )
        
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
            overall_score=round(overall_score, 1),
            is_speculative=is_speculative,
            speculation_reasons=speculation_reasons,
            learning_points=learning_points
        )
        
        import uuid
        recommendation.recommendation_id = str(uuid.uuid4())[:8]
        self.recommendations_history.append(recommendation)
        
        return recommendation
    
    def _analyze_speculation_opportunity(
        self,
        symbol: str,
        technical_data: Dict,
        news_data: Dict,
        current_price: float
    ) -> Tuple[bool, List[str]]:
        """
        Analizza se un titolo è speculativo nel momento attuale
        
        Returns:
            Tuple con (è speculativo, lista di motivi)
        """
        speculation_reasons = []
        is_speculative = False
        
        # Controlla volatilità elevata
        volatility = technical_data.get('volatility', 0)
        if volatility > 0.4:  # >40% volatilità annuale
            is_speculative = True
            speculation_reasons.append(f"Alta volatilità ({volatility*100:.1f}%)")
        
        # Controlla RSI estremo
        rsi = technical_data.get('rsi', 50)
        if rsi < 25 or rsi > 75:
            is_speculative = True
            level = "ipervenduto" if rsi < 25 else "ipercomprato"
            speculation_reasons.append(f"RSI in zona estrema ({rsi:.1f} - {level})")
        
        # Controlla volume anomalo
        avg_volume = technical_data.get('avg_volume', 0)
        current_volume = technical_data.get('current_volume', 0)
        if avg_volume > 0 and current_volume > avg_volume * 2:
            is_speculative = True
            speculation_reasons.append(f"Volume esploso ({current_volume/avg_volume:.1f}x la media)")
        
        # Controlla notizie molto positive/negative
        very_positive = news_data.get('very_positive_count', 0)
        very_negative = news_data.get('very_negative_count', 0)
        total_articles = news_data.get('articles_count', 0)
        
        if total_articles > 0:
            extreme_ratio = (very_positive + very_negative) / total_articles
            if extreme_ratio > 0.6:
                is_speculative = True
                speculation_reasons.append(f"Alto impatto emotivo dalle notizie ({extreme_ratio*100:.0f}% articoli estremi)")
        
        # Controlla breakout/breakdown recenti
        ma_trend = technical_data.get('ma_trend', 'neutral')
        if ma_trend == 'bullish' and technical_data.get('recent_breakout', False):
            is_speculative = True
            speculation_reasons.append("Breakout rialzista recente - opportunità speculativa")
        elif ma_trend == 'bearish' and technical_data.get('recent_breakdown', False):
            is_speculative = True
            speculation_reasons.append("Breakdown ribassista recente - opportunità speculativa")
        
        # Controlla divergenze
        if technical_data.get('rsi_divergence', False):
            is_speculative = True
            speculation_reasons.append("Divergenza RSI rilevata - possibile inversione")
        
        # Controlla gap di prezzo
        if technical_data.get('price_gap', 0) > 0.05:  # Gap > 5%
            is_speculative = True
            speculation_reasons.append(f"Gap di prezzo significativo ({technical_data.get('price_gap', 0)*100:.1f}%)")
        
        return is_speculative, speculation_reasons
    
    def _generate_learning_points(
        self,
        symbol: str,
        action: ActionType,
        technical_data: Dict,
        news_data: Dict,
        is_speculative: bool
    ) -> List[str]:
        """
        Genera punti educativi basati sul setup di trading
        
        Returns:
            Lista di punti educativi da imparare
        """
        learning_points = []
        
        # Punti basati sull'azione
        if action in [ActionType.STRONG_BUY, ActionType.BUY]:
            learning_points.append("✅ Impara: Identificare setup rialzisti con conferme multiple")
            learning_points.append("📚 Lezione: Il timing di ingresso è cruciale - aspetta pullback su supporti")
        elif action in [ActionType.STRONG_SELL, ActionType.SELL]:
            learning_points.append("⚠️ Impara: Riconoscere segnali di debolezza prima che il trend si inverta")
            learning_points.append("📚 Lezione: Proteggi i profitti - usa trailing stop in trend ribassisti")
        else:
            learning_points.append("⏳ Impara: La pazienza è una virtù - non forzare trade quando i segnali sono confusi")
            learning_points.append("📚 Lezione: A volte la migliore operazione è non operare")
        
        # Punti basati sulla gestione del rischio
        rsi = technical_data.get('rsi', 50)
        if rsi < 30:
            learning_points.append("💡 Gestione rischio: In ipervenduto, scala gli ingressi per ridurre il rischio")
        elif rsi > 70:
            learning_points.append("💡 Gestione rischio: In ipercomprato, considera prese di profitto parziali")
        
        # Punti basati sulla speculazione
        if is_speculative:
            learning_points.append("🎯 Speculazione: Alta ricompensa = alto rischio - riduci la size della posizione")
            learning_points.append("🧠 Psicologia: Nelle trade speculative, gestisci le emozioni - non FOMO!")
            learning_points.append("⚡ Strategia: Usa stop loss stretti nelle operazioni speculative")
        else:
            learning_points.append("🛡️ Trading conservativo: Setup ad alta probabilità richiedono pazienza")
        
        # Punti basati sul sentiment
        sentiment = news_data.get('overall_sentiment', 0)
        if abs(sentiment) > 0.7:
            learning_points.append("📰 Sentiment: Quando il sentiment è estremo, preparati per possibili reversal")
        
        # Punti sulla diversificazione
        learning_points.append("🔄 Ricorda: Non mettere mai più del 2-5% del capitale in una singola trade rischiosa")
        
        return learning_points
    
    def rate_recommendation(
        self,
        recommendation_id: str,
        overall_rating: int,
        criteria_ratings: Optional[Dict[str, int]] = None,
        notes: str = "",
        actual_outcome: Optional[Dict] = None,
        advanced_criteria_ratings: Optional[Dict[str, int]] = None
    ) -> bool:
        """
        Assegna un voto complesso da 1 a 5 (con possibilità di 6/5 per performance eccezionali)
        Perfetto per trading e apprendimento simultaneo
        
        Args:
            recommendation_id: ID della raccomandazione da votare
            overall_rating: Voto complessivo da 1 a 5 (5 = perfetto, uso eccezionale può essere considerato 6/5)
            criteria_ratings: Voti per criteri specifici base (opzionale)
                - accuratezza_prezzo: Accuratezza del prezzo di ingresso (1-5)
                - tempistica: Tempistica dell'operazione (1-5)
                - gestione_rischio: Qualità stop loss/take profit (1-5)
                - chiarezza: Chiarezza delle motivazioni (1-5)
                - performance: Performance effettiva (1-5)
            notes: Note aggiuntive sul voto
            actual_outcome: Risultato effettivo del trade
                Esempio: {"exit_price": 180.0, "profit_loss_pct": 2.5, "exit_date": "2024-01-15"}
            advanced_criteria_ratings: Voti per criteri avanzati (opzionale)
                - potenziale_profitto: Potenziale di profitto (1-5)
                - qualita_setup: Qualità del setup tecnico (1-5)
                - apprendimento: Valore educativo (1-5)
                - gestione_emotiva: Gestione stress emotivo (1-5)
                - timing_mercato: Timing condizioni di mercato (1-5)
        
        Returns:
            True se il voto è stato assegnato con successo, False altrimenti
        """
        # Supporta voto 6 come "perfetto oltre l'eccellenza" ma lo memorizza come 5 con bonus flag
        display_rating = overall_rating
        is_perfect_plus = overall_rating >= 6
        
        if not 1 <= overall_rating <= 6:
            print(f"❌ Errore: Il voto deve essere tra 1 e 6 (6 = perfetto+), ricevuto {overall_rating}")
            return False
        
        # Trova la raccomandazione
        rec = self._find_recommendation(recommendation_id)
        if not rec:
            print(f"❌ Errore: Raccomandazione con ID {recommendation_id} non trovata")
            return False
        
        # Assegna voto complessivo (max 5 nel storage, ma tracciamo se era 6)
        rec.user_rating = min(5, overall_rating)
        rec.rating_notes = notes
        if is_perfect_plus:
            rec.rating_notes += " [VOTO 6/5 - PERFORMANCE ECCEZIONALE!]"
        
        # Assegna voti per criteri base (se forniti)
        if criteria_ratings:
            valid_criteria = set(self.rating_criteria_definitions.keys())
            for criterion, rating in criteria_ratings.items():
                if criterion in valid_criteria:
                    if 1 <= rating <= 5:
                        rec.rating_criteria[criterion] = rating
                    else:
                        print(f"⚠️  Avviso: Voto {rating} per '{criterion}' non valido (deve essere 1-5), ignorato")
                else:
                    print(f"⚠️  Avviso: Criterio '{criterion}' non riconosciuto, ignorato")
        
        # Assegna voti per criteri avanzati (se forniti)
        if advanced_criteria_ratings:
            valid_advanced = set(self.advanced_criteria.keys())
            for criterion, rating in advanced_criteria_ratings.items():
                if criterion in valid_advanced:
                    if 1 <= rating <= 5:
                        rec.rating_criteria[f"adv_{criterion}"] = rating
                    else:
                        print(f"⚠️  Avviso: Voto {rating} per '{criterion}' non valido (deve essere 1-5), ignorato")
                else:
                    print(f"⚠️  Avviso: Criterio avanzato '{criterion}' non riconosciuto, ignorato")
        
        # Registra risultato effettivo (se fornito)
        if actual_outcome:
            rec.actual_outcome = actual_outcome
        
        # Stampa feedback visivo avanzato
        print(f"\n{'🏆' if is_perfect_plus else '✅'} Voto assegnato con successo alla raccomandazione {recommendation_id}")
        stars = '⭐' * min(5, overall_rating)
        if is_perfect_plus:
            stars += ' 🌟'
        print(f"   Voto complessivo: {stars} ({display_rating}/5 {'- PERFETTO+!' if is_perfect_plus else ''})")
        
        if rec.rating_criteria:
            print(f"   📊 Voti per criterio:")
            # Criteri base
            for criterion, rating in rec.rating_criteria.items():
                if not criterion.startswith("adv_"):
                    criterion_label = self.rating_criteria_definitions.get(criterion, criterion)
                    print(f"     • {criterion_label}: {'⭐' * rating} ({rating}/5)")
            # Criteri avanzati
            for criterion, rating in rec.rating_criteria.items():
                if criterion.startswith("adv_"):
                    base_name = criterion.replace("adv_", "")
                    criterion_label = self.advanced_criteria.get(base_name, base_name)
                    print(f"     🔹 {criterion_label}: {'⭐' * rating} ({rating}/5)")
        
        if notes:
            print(f"   📝 Note: {notes}")
        
        # Mostra punti di apprendimento se presenti
        if rec.learning_points:
            print(f"\n   💡 Punti educativi da questa raccomandazione:")
            for point in rec.learning_points[:3]:  # Mostra primi 3
                print(f"     {point}")
        
        return True
    
    def _find_recommendation(self, recommendation_id: str) -> Optional[TradeRecommendation]:
        """Trova una raccomandazione per ID"""
        for rec in self.recommendations_history:
            if rec.recommendation_id == recommendation_id:
                return rec
        return None
    
    def get_rating_statistics(self) -> Dict:
        """
        Calcola statistiche dettagliate sui voti
        
        Returns:
            Dizionario con statistiche complete sui voti
        """
        rated_recs = [r for r in self.recommendations_history if r.user_rating is not None]
        
        if not rated_recs:
            return {"message": "Nessuna raccomandazione votata ancora"}
        
        total = len(rated_recs)
        avg_overall = sum(r.user_rating for r in rated_recs) / total
        
        # Distribuzione voti
        rating_distribution = {i: 0 for i in range(1, 6)}
        for r in rated_recs:
            rating_distribution[r.user_rating] += 1
        
        # Statistiche per criterio
        criteria_stats = {}
        for criterion in self.rating_criteria_definitions.keys():
            ratings = [r.rating_criteria.get(criterion) for r in rated_recs if r.rating_criteria.get(criterion) is not None]
            if ratings:
                criteria_stats[criterion] = {
                    "media": round(sum(ratings) / len(ratings), 2),
                    "conteggio": len(ratings),
                    "min": min(ratings),
                    "max": max(ratings)
                }
        
        # Top raccomandazioni
        top_rated = sorted(rated_recs, key=lambda x: x.user_rating, reverse=True)[:5]
        
        # Statistiche performance (se disponibili)
        performance_stats = None
        recs_with_outcome = [r for r in rated_recs if r.actual_outcome]
        if recs_with_outcome:
            profits = [r.actual_outcome.get('profit_loss_pct', 0) for r in recs_with_outcome]
            performance_stats = {
                "trades_conclusi": len(recs_with_outcome),
                "profit medio %": round(sum(profits) / len(profits), 2),
                "trade vincenti": sum(1 for p in profits if p > 0),
                "trade perdenti": sum(1 for p in profits if p < 0)
            }
        
        return {
            "totale_votati": total,
            "voto_medio": round(avg_overall, 2),
            "distribuzione": rating_distribution,
            "statistiche_criteri": criteria_stats,
            "top_rated": [
                {
                    "id": r.recommendation_id,
                    "symbol": r.symbol,
                    "voto": r.user_rating,
                    "azione": r.action.value
                }
                for r in top_rated
            ],
            "performance": performance_stats
        }
    
    def export_ratings_to_json(self, filename: str = "ratings_export.json") -> str:
        """
        Esporta tutti i voti e le raccomandazioni in un file JSON
        
        Args:
            filename: Nome del file di output
        
        Returns:
            Percorso del file creato
        """
        rated_recs = [r for r in self.recommendations_history if r.user_rating is not None]
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "totale_votati": len(rated_recs),
            "raccomandazioni": []
        }
        
        for rec in rated_recs:
            rec_data = {
                "id": rec.recommendation_id,
                "symbol": rec.symbol,
                "azione": rec.action.value,
                "data_creazione": rec.created_at.isoformat(),
                "voto_complessivo": rec.user_rating,
                "voti_criteri": rec.rating_criteria,
                "note": rec.rating_notes,
                "risultato_effettivo": rec.actual_outcome,
                "dettagli_originali": {
                    "confidence": rec.confidence,
                    "entry_price": rec.entry_price,
                    "stop_loss": rec.stop_loss,
                    "take_profit_1": rec.take_profit_1,
                    "technical_score": rec.technical_score,
                    "sentiment_score": rec.sentiment_score
                }
            }
            export_data["raccomandazioni"].append(rec_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Dati esportati con successo in {filename}")
        return filename
    
    def format_recommendation(self, rec: TradeRecommendation, show_rating_info: bool = True) -> str:
        """Formatta la raccomandazione per la visualizzazione con info speculative e educative"""
        output = f"""
{'='*60}
RACCOMANDAZIONE TRADING: {rec.symbol}
{'='*60}
ID: {rec.recommendation_id}
Data creazione: {rec.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Badge speculativo se applicabile
        if rec.is_speculative:
            output += f"""
🎯 OPPORTUNITÀ SPECULATIVA RILEVATA!
   Motivi: {', '.join(rec.speculation_reasons[:3])}
   ⚠️ Attenzione: Alto rischio/alto rendimento potenziale
"""
        
        output += f"""
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
        
        # Mostra punti educativi
        if rec.learning_points:
            output += "\n💡 PUNTI EDUCATIVI (IMPARA MENTRE FAI TRADING):\n"
            for point in rec.learning_points:
                output += f"   {point}\n"
        
        # Mostra informazioni sul voto se presente
        if show_rating_info and rec.user_rating is not None:
            is_perfect_plus = "[VOTO 6/5 - PERFORMANCE ECCEZIONALE!]" in rec.rating_notes
            trophy = "🏆" if is_perfect_plus else ""
            output += f"""
{trophy}⭐ VOTO UTENTE: {'⭐' * rec.user_rating}{' 🌟' if is_perfect_plus else ''} ({rec.user_rating}/5{'+ PERFETTO!' if is_perfect_plus else ''})
"""
            if rec.rating_criteria:
                output += "   📊 Dettagli voto:\n"
                # Criteri base
                for criterion, rating in rec.rating_criteria.items():
                    if not criterion.startswith("adv_"):
                        criterion_label = self.rating_criteria_definitions.get(criterion, criterion)
                        output += f"     • {criterion_label}: {'⭐' * rating} ({rating}/5)\n"
                # Criteri avanzati
                for criterion, rating in rec.rating_criteria.items():
                    if criterion.startswith("adv_"):
                        base_name = criterion.replace("adv_", "")
                        criterion_label = self.advanced_criteria.get(base_name, base_name)
                        output += f"     🔹 {criterion_label}: {'⭐' * rating} ({rating}/5)\n"
            
            if rec.rating_notes:
                output += f"   📝 Note: {rec.rating_notes}\n"
            
            if rec.actual_outcome:
                outcome = rec.actual_outcome
                output += f"   Risultato effettivo:\n"
                if 'exit_price' in outcome:
                    output += f"     - Prezzo di uscita: ${outcome['exit_price']}\n"
                if 'profit_loss_pct' in outcome:
                    pl = outcome['profit_loss_pct']
                    emoji = "📈" if pl > 0 else "📉" if pl < 0 else "➡️"
                    output += f"     {emoji} Profitto/Perdita: {pl:+.2f}%\n"
                if 'exit_date' in outcome:
                    output += f"     - Data chiusura: {outcome['exit_date']}\n"
        
        output += f"""
⚠️ DISCLAIMER: Questa è solo analisi tecnica/statistica.
   Il trading comporta rischi. Fai sempre le tue ricerche.
{'='*60}
"""
        return output
    
    def get_speculative_opportunities(self) -> List[TradeRecommendation]:
        """
        Restituisce tutte le raccomandazioni che sono opportunità speculative
        
        Returns:
            Lista di raccomandazioni speculative
        """
        return [r for r in self.recommendations_history if r.is_speculative]
    
    def print_speculative_alert(self, symbol: str) -> str:
        """
        Genera un alert per titoli speculativi nel momento attuale
        
        Args:
            symbol: Simbolo del titolo da controllare
        
        Returns:
            Stringa formattata con l'alert speculativo
        """
        rec = None
        for r in self.recommendations_history:
            if r.symbol == symbol and r.is_speculative:
                rec = r
                break
        
        if not rec:
            return f"❌ Nessuna opportunità speculativa trovata per {symbol}"
        
        output = f"""
{'='*60}
🎯 ALERT SPECULAZIONE: {symbol}
{'='*60}
⚡ OPPORTUNITÀ SPECULATIVA ATTIVA!

📋 MOTIVI DELLA SPECULAZIONE:
"""
        for i, reason in enumerate(rec.speculation_reasons, 1):
            output += f"   {i}. {reason}\n"
        
        output += f"""
💡 CONSIGLI PER QUESTA TRADE SPECULATIVA:
   • Riduci la dimensione della posizione (max 1-2% del capitale)
   • Usa stop loss stretti
   • Prendi profitti parziali rapidamente
   • Non farti prendere dal FOMO!

📊 DETTAGLI OPERATIVI:
   Azione: {rec.action.value}
   Prezzo ingresso: ${rec.entry_price}
   Stop Loss: ${rec.stop_loss}
   Take Profit 1: ${rec.take_profit_1}
   
🧠 RICORDA: Le trade speculative sono ad alto rischio!
{'='*60}
"""
        return output


if __name__ == "__main__":
    # Test completo del sistema di voto complesso
    print("=" * 60)
    print("TRADING ADVISOR PRO v5.0 - SISTEMA DI VOTO COMPLESSO")
    print("=" * 60)
    
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
    
    # Genera prima raccomandazione
    print("\n📌 Generazione prima raccomandazione (AAPL)...")
    rec1 = engine.generate_recommendation(
        symbol="AAPL",
        technical_data=technical_data,
        news_data=news_data,
        current_price=175.0
    )
    print(engine.format_recommendation(rec1))
    
    # Genera seconda raccomandazione
    print("\n📌 Generazione seconda raccomandazione (TSLA)...")
    technical_data['rsi'] = 25
    technical_data['overall_signal']['confidence'] = 85
    rec2 = engine.generate_recommendation(
        symbol="TSLA",
        technical_data=technical_data,
        news_data=news_data,
        current_price=250.0
    )
    print(engine.format_recommendation(rec2))
    
    # Test del sistema di voto complesso
    print("\n" + "=" * 60)
    print("TEST SISTEMA DI VOTO COMPLESSO")
    print("=" * 60)
    
    # Vota la prima raccomandazione con voti dettagliati
    print(f"\n⭐ Votazione raccomandazione {rec1.recommendation_id} (AAPL)...")
    engine.rate_recommendation(
        recommendation_id=rec1.recommendation_id,
        overall_rating=4,
        criteria_ratings={
            "accuratezza_prezzo": 5,
            "tempistica": 4,
            "gestione_rischio": 4,
            "chiarezza": 5,
            "performance": 3
        },
        notes="Buona analisi tecnica, prezzo di ingresso preciso",
        actual_outcome={
            "exit_price": 182.0,
            "profit_loss_pct": 4.0,
            "exit_date": "2024-01-15"
        }
    )
    
    # Vota la seconda raccomandazione
    print(f"\n⭐ Votazione raccomandazione {rec2.recommendation_id} (TSLA)...")
    engine.rate_recommendation(
        recommendation_id=rec2.recommendation_id,
        overall_rating=5,
        criteria_ratings={
            "accuratezza_prezza": 5,
            "tempistica": 5,
            "gestione_rischio": 5,
            "chiarezza": 4,
            "performance": 5
        },
        notes="Eccellente! Segnale perfetto con ottimo profitto",
        actual_outcome={
            "exit_price": 275.0,
            "profit_loss_pct": 10.0,
            "exit_date": "2024-01-20"
        }
    )
    
    # Mostra statistiche
    print("\n" + "=" * 60)
    print("STATISTICHE VOTI")
    print("=" * 60)
    stats = engine.get_rating_statistics()
    
    print(f"\n📊 Totale raccomandazioni votate: {stats['totale_votati']}")
    print(f"⭐ Voto medio: {stats['voto_medio']}/5")
    print(f"\n📈 Distribuzione voti:")
    for voto, conteggio in stats['distribuzione'].items():
        barre = "█" * conteggio
        print(f"   {voto} stelle: {barre} ({conteggio})")
    
    if stats['statistiche_criteri']:
        print(f"\n📋 Statistiche per criterio:")
        for criterio, dati in stats['statistiche_criteri'].items():
            criterio_label = engine.rating_criteria_definitions.get(criterio, criterio)
            print(f"   {criterio_label}:")
            print(f"     Media: {dati['media']}/5 | Min: {dati['min']} | Max: {dati['max']} | Campioni: {dati['conteggio']}")
    
    if stats['top_rated']:
        print(f"\n🏆 Top raccomandazioni:")
        for i, top in enumerate(stats['top_rated'], 1):
            print(f"   {i}. {top['symbol']} ({top['id']}): {'⭐' * top['voto']} ({top['voto']}/5) - {top['azione']}")
    
    if stats['performance']:
        perf = stats['performance']
        print(f"\n💰 Performance trades:")
        print(f"   Trades conclusi: {perf['trades_conclusi']}")
        print(f"   Profitto medio: {perf['profit medio %']:+.2f}%")
        print(f"   Trade vincenti: {perf['trade vincenti']}")
        print(f"   Trade perdenti: {perf['trade perdenti']}")
    
    # Mostra raccomandazioni con voti
    print("\n" + "=" * 60)
    print("RACCOMANDAZIONI AGGIORNATE CON VOTI")
    print("=" * 60)
    print("\n" + engine.format_recommendation(rec1))
    print("\n" + engine.format_recommendation(rec2))
    
    # Esporta dati
    print("\n" + "=" * 60)
    print("ESPORTAZIONE DATI")
    print("=" * 60)
    engine.export_ratings_to_json("ratings_export.json")
    
    print("\n✅ Test completato con successo!")
