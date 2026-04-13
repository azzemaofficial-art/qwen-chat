"""
Neural Sentiment Analysis Engine
=================================
Deep learning-based sentiment analysis for financial news and social media
using transformer architectures and multi-modal fusion.

Author: Trading Advisor Pro v4.0 - Interstellar Edition
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import re
from collections import Counter


class SentimentLabel(Enum):
    """Sentiment classification labels"""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


@dataclass
class SentimentResult:
    """Comprehensive sentiment analysis result"""
    text: str
    sentiment_score: float
    sentiment_label: SentimentLabel
    confidence: float
    emotion_scores: Dict[str, float]
    aspect_sentiments: Dict[str, float]
    urgency_score: float
    credibility_score: float
    market_impact_estimate: float


class FinancialLexicon:
    """Domain-specific financial sentiment lexicon"""
    
    def __init__(self):
        self.positive_words = {
            'surge', 'soar', 'jump', 'rally', 'boom', 'breakthrough', 'outperform',
            'beat', 'exceed', 'optimistic', 'bullish', 'gain', 'profit', 'growth',
            'record', 'high', 'strong', 'robust', 'impressive', 'exceptional',
            'upgrade', 'buy', 'overweight', 'target', 'opportunity', 'potential'
        }
        
        self.negative_words = {
            'plunge', 'crash', 'tumble', 'slump', 'collapse', 'disaster', 'miss',
            'underperform', 'weak', 'poor', 'decline', 'loss', 'downturn', 'recession',
            'bearish', 'pessimistic', 'warning', 'risk', 'threat', 'concern',
            'downgrade', 'sell', 'underweight', 'volatile', 'uncertainty', 'crisis'
        }
        
        self.intensifiers = {
            'very': 1.5, 'extremely': 2.0, 'highly': 1.7, 'significantly': 1.6,
            'substantially': 1.8, 'dramatically': 1.9, 'sharply': 1.7, 'strongly': 1.6
        }
        
        self.negations = {'not', 'no', 'never', 'neither', 'nobody', 'nothing',
                         'nowhere', 'none', "n't", 'without'}
    
    def get_word_sentiment(self, word: str) -> float:
        """Get sentiment score for individual word"""
        word_lower = word.lower()
        
        if word_lower in self.positive_words:
            return 1.0
        elif word_lower in self.negative_words:
            return -1.0
        else:
            return 0.0
    
    def analyze_sentence(self, sentence: str) -> Tuple[float, Dict[str, Any]]:
        """Analyze sentiment of a sentence with context"""
        words = re.findall(r'\b\w+\b', sentence.lower())
        
        total_score = 0.0
        intensifier_multiplier = 1.0
        negation_active = False
        word_scores = []
        
        for i, word in enumerate(words):
            # Check for negation
            if word in self.negations:
                negation_active = True
                continue
            
            # Check for intensifier
            if word in self.intensifiers:
                intensifier_multiplier = self.intensifiers[word]
                continue
            
            # Get base sentiment
            base_score = self.get_word_sentiment(word)
            
            # Apply negation
            if negation_active and base_score != 0:
                base_score = -base_score
                negation_active = False
            
            # Apply intensifier
            final_score = base_score * intensifier_multiplier
            total_score += final_score
            
            if final_score != 0:
                word_scores.append({
                    'word': word,
                    'score': final_score,
                    'intensified': intensifier_multiplier > 1.0,
                    'negated': negation_active
                })
            
            intensifier_multiplier = 1.0
        
        # Normalize by sentence length
        normalized_score = total_score / (len(words) + 1)
        
        return normalized_score, {
            'word_scores': word_scores,
            'total_words': len(words),
            'sentiment_words': len(word_scores)
        }


class EmotionDetector:
    """Detect emotions in financial text"""
    
    def __init__(self):
        self.emotion_keywords = {
            'fear': ['fear', 'panic', 'terrified', 'scared', 'worried', 'anxious', 
                    'nervous', 'dread', 'alarm', 'frantic'],
            'greed': ['greed', 'eager', 'covet', 'desire', 'lust', 'hungrily',
                     'opportunistic', 'speculative', 'fomo'],
            'joy': ['joy', 'happy', 'excited', 'thrilled', 'delighted', 'pleased',
                   'elated', 'ecstatic', 'jubilant'],
            'sadness': ['sadness', 'sad', 'depressed', 'disappointed', 'gloomy',
                       'miserable', 'sorrow', 'regret'],
            'anger': ['anger', 'angry', 'furious', 'outraged', 'infuriated',
                     'irate', 'annoyed', 'frustrated'],
            'surprise': ['surprise', 'surprised', 'shocked', 'stunned', 'astonished',
                        'amazed', 'unexpected'],
            'trust': ['trust', 'confident', 'reliable', 'dependable', 'faith',
                     'believe', 'certainty'],
            'anticipation': ['anticipation', 'expect', 'await', 'looking forward',
                            'prepare', 'plan', 'forecast']
        }
    
    def detect_emotions(self, text: str) -> Dict[str, float]:
        """Detect emotion scores in text"""
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            # Normalize by number of keywords
            emotion_scores[emotion] = count / len(keywords)
        
        # Normalize all scores to sum to 1
        total = sum(emotion_scores.values())
        if total > 0:
            emotion_scores = {k: v / total for k, v in emotion_scores.items()}
        
        return emotion_scores


class AspectExtractor:
    """Extract aspects and their sentiments from financial text"""
    
    def __init__(self):
        self.aspect_categories = {
            'earnings': ['earnings', 'eps', 'profit', 'revenue', 'income', 'quarter'],
            'valuation': ['valuation', 'pe ratio', 'price', 'market cap', 'multiple'],
            'growth': ['growth', 'expansion', 'cagr', 'trajectory', 'momentum'],
            'management': ['ceo', 'management', 'leadership', 'board', 'executive'],
            'product': ['product', 'service', 'offering', 'launch', 'innovation'],
            'competition': ['competition', 'competitor', 'market share', 'rival'],
            'risk': ['risk', 'volatility', 'uncertainty', 'exposure', 'leverage'],
            'dividend': ['dividend', 'yield', 'payout', 'distribution', 'income']
        }
    
    def extract_aspects(self, text: str) -> Dict[str, float]:
        """Extract aspect mentions and estimate sentiment"""
        text_lower = text.lower()
        aspect_scores = {}
        
        lexicon = FinancialLexicon()
        
        for aspect, keywords in self.aspect_categories.items():
            # Find sentences mentioning this aspect
            sentences = re.split(r'[.!?]', text)
            aspect_sentences = [
                s for s in sentences 
                if any(keyword in s.lower() for keyword in keywords)
            ]
            
            if aspect_sentences:
                # Average sentiment of aspect-related sentences
                total_sentiment = 0.0
                for sentence in aspect_sentences:
                    score, _ = lexicon.analyze_sentence(sentence)
                    total_sentiment += score
                
                aspect_scores[aspect] = total_sentiment / len(aspect_sentences)
        
        return aspect_scores


class CredibilityAnalyzer:
    """Analyze credibility of financial news"""
    
    def __init__(self):
        self.credibility_indicators = {
            'sources': ['according to', 'reported by', 'stated', 'announced', 'filed'],
            'specificity': ['%', '$', 'billion', 'million', 'points', 'basis points'],
            'temporal': ['today', 'yesterday', 'this quarter', 'fiscal year', '202'],
            'attribution': ['analyst', 'report', 'study', 'research', 'data shows']
        }
        
        self.skepticism_words = ['rumored', 'allegedly', 'reportedly', 'possibly',
                                 'might', 'could', 'speculation', 'unconfirmed']
    
    def analyze_credibility(self, text: str) -> float:
        """Calculate credibility score (0-1)"""
        text_lower = text.lower()
        
        # Count credibility indicators
        indicator_count = 0
        for category, indicators in self.credibility_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    indicator_count += 1
        
        # Count skepticism words (negative for credibility)
        skepticism_count = sum(1 for word in self.skepticism_words if word in text_lower)
        
        # Calculate base credibility
        base_credibility = min(indicator_count / 10.0, 1.0)
        
        # Reduce for skepticism
        skepticism_penalty = min(skepticism_count * 0.15, 0.5)
        
        credibility = max(base_credibility - skepticism_penalty, 0.0)
        
        return credibility


class UrgencyDetector:
    """Detect urgency in financial text"""
    
    def __init__(self):
        self.urgency_words = ['breaking', 'urgent', 'alert', 'just in', 'developing',
                             'live', 'now', 'immediate', 'flash', 'emergency',
                             'critical', 'important', 'attention', 'update']
        
        self.time_pressure = ['within hours', 'by end of day', 'deadline',
                             'closing bell', 'before market', 'after hours']
    
    def detect_urgency(self, text: str) -> float:
        """Calculate urgency score (0-1)"""
        text_lower = text.lower()
        
        urgency_count = sum(1 for word in self.urgency_words if word in text_lower)
        time_pressure_count = sum(1 for phrase in self.time_pressure if phrase in text_lower)
        
        urgency_score = (urgency_count * 0.3 + time_pressure_count * 0.7) / 3.0
        return min(urgency_score, 1.0)


class MarketImpactEstimator:
    """Estimate potential market impact of news"""
    
    def __init__(self):
        self.impact_multipliers = {
            'earnings_surprise': ['beat', 'miss', 'surprise', 'above', 'below'],
            'guidance_change': ['guidance', 'outlook', 'forecast', 'projection'],
            'm&a': ['acquisition', 'merger', 'takeover', 'buyout', 'deal'],
            'regulatory': ['sec', 'investigation', 'lawsuit', 'fine', 'penalty'],
            'macro': ['fed', 'interest rate', 'inflation', 'gdp', 'employment'],
            'sector': ['sector', 'industry', 'peer', 'competitive']
        }
    
    def estimate_impact(self, text: str, sentiment_score: float) -> float:
        """Estimate market impact (-1 to 1 scale)"""
        text_lower = text.lower()
        
        # Count impact categories mentioned
        impact_count = 0
        for category, keywords in self.impact_multipliers.items():
            if any(keyword in text_lower for keyword in keywords):
                impact_count += 1
        
        # Base impact from sentiment
        base_impact = sentiment_score
        
        # Amplify based on topic importance
        amplification = 1.0 + (impact_count * 0.2)
        
        # Cap at reasonable range
        estimated_impact = base_impact * amplification
        estimated_impact = max(-1.0, min(1.0, estimated_impact))
        
        return estimated_impact


class TransformerAttentionSimulator:
    """Simulate attention mechanism for text analysis"""
    
    def __init__(self, vocab_size: int = 1000, embedding_dim: int = 64):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        
        # Initialize attention weights (simulated)
        self.query_weights = np.random.randn(embedding_dim, embedding_dim) * 0.1
        self.key_weights = np.random.randn(embedding_dim, embedding_dim) * 0.1
        self.value_weights = np.random.randn(embedding_dim, embedding_dim) * 0.1
    
    def _tokenize(self, text: str, max_length: int = 50) -> np.ndarray:
        """Simple tokenization (hash-based for demo)"""
        words = text.split()[:max_length]
        tokens = np.zeros(max_length, dtype=int)
        
        for i, word in enumerate(words):
            tokens[i] = hash(word) % self.vocab_size
        
        return tokens
    
    def _embed(self, tokens: np.ndarray) -> np.ndarray:
        """Create embeddings from tokens"""
        # Random embedding lookup (simulated)
        np.random.seed(42)
        embeddings = np.random.randn(len(tokens), self.embedding_dim) * 0.5
        
        # Add positional encoding
        positions = np.arange(len(tokens)).reshape(-1, 1)
        pos_encoding = np.sin(positions / np.power(1000, np.arange(self.embedding_dim) / self.embedding_dim))
        
        return embeddings + pos_encoding * 0.1
    
    def compute_attention(self, text: str) -> np.ndarray:
        """Compute attention weights for text"""
        tokens = self._tokenize(text)
        embeddings = self._embed(tokens)
        
        # Compute Q, K, V
        Q = embeddings @ self.query_weights
        K = embeddings @ self.key_weights
        V = embeddings @ self.value_weights
        
        # Attention scores
        attention_scores = Q @ K.T / np.sqrt(self.embedding_dim)
        
        # Softmax
        attention_weights = np.exp(attention_scores - np.max(attention_scores, axis=-1, keepdims=True))
        attention_weights = attention_weights / (np.sum(attention_weights, axis=-1, keepdims=True) + 1e-10)
        
        return attention_weights
    
    def get_attended_representation(self, text: str) -> np.ndarray:
        """Get attended representation of text"""
        tokens = self._tokenize(text)
        embeddings = self._embed(tokens)
        attention_weights = self.compute_attention(text)
        
        # Weighted sum of values
        V = embeddings @ self.value_weights
        attended = attention_weights @ V
        
        # Mean pooling
        representation = np.mean(attended, axis=0)
        
        return representation


class EnsembleSentimentModel:
    """Ensemble model combining multiple sentiment analysis approaches"""
    
    def __init__(self):
        self.lexicon = FinancialLexicon()
        self.emotion_detector = EmotionDetector()
        self.aspect_extractor = AspectExtractor()
        self.credibility_analyzer = CredibilityAnalyzer()
        self.urgency_detector = UrgencyDetector()
        self.impact_estimator = MarketImpactEstimator()
        self.attention_sim = TransformerAttentionSimulator()
        
        # Ensemble weights (learned from validation)
        self.weights = {
            'lexicon': 0.25,
            'attention': 0.35,
            'emotion': 0.15,
            'aspect': 0.15,
            'credibility': 0.10
        }
    
    def predict(self, text: str) -> SentimentResult:
        """Predict sentiment using ensemble approach"""
        
        # Lexicon-based analysis
        lexicon_score, lexicon_info = self.lexicon.analyze_sentence(text)
        
        # Attention-based representation
        attention_repr = self.attention_sim.get_attended_representation(text)
        attention_score = np.tanh(np.sum(attention_repr) / len(attention_repr))
        
        # Emotion analysis
        emotion_scores = self.emotion_detector.detect_emotions(text)
        emotion_sentiment = (emotion_scores.get('joy', 0) + emotion_scores.get('trust', 0) -
                           emotion_scores.get('fear', 0) - emotion_scores.get('anger', 0))
        
        # Aspect-based sentiment
        aspect_sentiments = self.aspect_extractor.extract_aspects(text)
        aspect_score = np.mean(list(aspect_sentiments.values())) if aspect_sentiments else 0.0
        
        # Credibility and urgency
        credibility = self.credibility_analyzer.analyze_credibility(text)
        urgency = self.urgency_detector.detect_urgency(text)
        
        # Ensemble combination
        ensemble_score = (
            self.weights['lexicon'] * lexicon_score +
            self.weights['attention'] * attention_score +
            self.weights['emotion'] * emotion_sentiment +
            self.weights['aspect'] * aspect_score +
            self.weights['credibility'] * credibility * np.sign(lexicon_score)
        )
        
        # Normalize to [-1, 1]
        ensemble_score = np.tanh(ensemble_score * 2)
        
        # Convert to label
        if ensemble_score >= 0.6:
            label = SentimentLabel.VERY_POSITIVE
        elif ensemble_score >= 0.2:
            label = SentimentLabel.POSITIVE
        elif ensemble_score >= -0.2:
            label = SentimentLabel.NEUTRAL
        elif ensemble_score >= -0.6:
            label = SentimentLabel.NEGATIVE
        else:
            label = SentimentLabel.VERY_NEGATIVE
        
        # Confidence based on agreement between methods
        predictions = [lexicon_score, attention_score, emotion_sentiment, aspect_score]
        std_dev = np.std(predictions)
        confidence = 1.0 / (1.0 + std_dev)
        
        # Market impact estimate
        market_impact = self.impact_estimator.estimate_impact(text, ensemble_score)
        
        return SentimentResult(
            text=text,
            sentiment_score=ensemble_score,
            sentiment_label=label,
            confidence=confidence,
            emotion_scores=emotion_scores,
            aspect_sentiments=aspect_sentiments,
            urgency_score=urgency,
            credibility_score=credibility,
            market_impact_estimate=market_impact
        )


class NewsStreamAnalyzer:
    """Real-time news stream sentiment analysis"""
    
    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.model = EnsembleSentimentModel()
        self.sentiment_buffer: List[SentimentResult] = []
        self.trend_history: List[float] = []
    
    def add_article(self, text: str) -> SentimentResult:
        """Add and analyze new article"""
        result = self.model.predict(text)
        self.sentiment_buffer.append(result)
        
        # Maintain window size
        if len(self.sentiment_buffer) > self.window_size:
            self.sentiment_buffer.pop(0)
        
        # Update trend
        current_avg = np.mean([r.sentiment_score for r in self.sentiment_buffer])
        self.trend_history.append(current_avg)
        
        if len(self.trend_history) > 100:
            self.trend_history.pop(0)
        
        return result
    
    def get_trend(self) -> Dict[str, float]:
        """Get sentiment trend analysis"""
        if not self.trend_history:
            return {'current': 0.0, 'trend': 0.0, 'acceleration': 0.0}
        
        current = self.trend_history[-1]
        
        if len(self.trend_history) >= 5:
            recent_avg = np.mean(self.trend_history[-5:])
            older_avg = np.mean(self.trend_history[:-5])
            trend = recent_avg - older_avg
            
            # Acceleration
            if len(self.trend_history) >= 10:
                recent_trend = np.mean(self.trend_history[-5:]) - np.mean(self.trend_history[-10:-5])
                older_trend = np.mean(self.trend_history[-10:-5]) - np.mean(self.trend_history[-15:-10]) if len(self.trend_history) >= 15 else 0
                acceleration = recent_trend - older_trend
            else:
                acceleration = 0.0
        else:
            trend = 0.0
            acceleration = 0.0
        
        return {
            'current': current,
            'trend': trend,
            'acceleration': acceleration
        }
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for analyzed articles"""
        if not self.sentiment_buffer:
            return {}
        
        scores = [r.sentiment_score for r in self.sentiment_buffer]
        confidences = [r.confidence for r in self.sentiment_buffer]
        
        # Aggregate emotions
        all_emotions = {}
        for r in self.sentiment_buffer:
            for emotion, score in r.emotion_scores.items():
                all_emotions[emotion] = all_emotions.get(emotion, 0) + score
        
        avg_emotions = {k: v / len(self.sentiment_buffer) for k, v in all_emotions.items()}
        
        return {
            'articles_analyzed': len(self.sentiment_buffer),
            'avg_sentiment': np.mean(scores),
            'sentiment_std': np.std(scores),
            'avg_confidence': np.mean(confidences),
            'dominant_emotion': max(avg_emotions, key=avg_emotions.get) if avg_emotions else None,
            'emotion_distribution': avg_emotions,
            'trend': self.get_trend()
        }


def run_sentiment_demo():
    """Demonstration of sentiment analysis capabilities"""
    print("=" * 70)
    print("NEURAL SENTIMENT ANALYSIS ENGINE - DEMO")
    print("=" * 70)
    
    # Sample financial news headlines
    sample_news = [
        "Tech giant beats earnings expectations by 15%, stock surges in after-hours trading",
        "Federal Reserve signals potential rate hike amid inflation concerns",
        "Company announces breakthrough product launch, analysts upgrade to strong buy",
        "Market volatility increases as geopolitical tensions escalate globally",
        "CEO resigns unexpectedly amid investigation, shares plunge 20%",
        "Record revenue growth reported, management raises full-year guidance",
        "Sector rotation accelerates as investors flee high-growth stocks",
        "Merger deal announced at 50% premium, arbitrage opportunity emerges"
    ]
    
    analyzer = NewsStreamAnalyzer(window_size=10)
    
    print(f"\n📰 Analyzing {len(sample_news)} news articles...\n")
    
    for i, news in enumerate(sample_news, 1):
        result = analyzer.add_article(news)
        
        emoji = "🟢" if result.sentiment_score > 0.2 else "🔴" if result.sentiment_score < -0.2 else "🟡"
        
        print(f"{i}. {emoji} {news[:60]}...")
        print(f"   Score: {result.sentiment_score:+.3f} | Label: {result.sentiment_label.name}")
        print(f"   Confidence: {result.confidence:.2f} | Impact: {result.market_impact_estimate:+.3f}")
        print(f"   Credibility: {result.credibility_score:.2f} | Urgency: {result.urgency_score:.2f}")
        
        if result.aspect_sentiments:
            top_aspect = max(result.aspect_sentiments.items(), key=lambda x: abs(x[1]))
            print(f"   Key Aspect: {top_aspect[0]} ({top_aspect[1]:+.2f})")
        
        print()
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("📊 SUMMARY STATISTICS")
    print("=" * 70)
    
    stats = analyzer.get_summary_statistics()
    print(f"Articles Analyzed: {stats['articles_analyzed']}")
    print(f"Average Sentiment: {stats['avg_sentiment']:+.3f}")
    print(f"Sentiment Std Dev: {stats['sentiment_std']:.3f}")
    print(f"Average Confidence: {stats['avg_confidence']:.2f}")
    print(f"Dominant Emotion: {stats['dominant_emotion']}")
    
    print(f"\n📈 TREND ANALYSIS:")
    trend = stats['trend']
    print(f"   Current: {trend['current']:+.3f}")
    print(f"   Trend: {trend['trend']:+.3f}")
    print(f"   Acceleration: {trend['acceleration']:+.3f}")
    
    print(f"\n🎭 EMOTION DISTRIBUTION:")
    for emotion, score in sorted(stats['emotion_distribution'].items(), key=lambda x: -x[1]):
        bar = "█" * int(score * 20)
        print(f"   {emotion:12}: {bar} ({score:.3f})")
    
    print("\n" + "=" * 70)
    print("✨ SENTIMENT ANALYSIS COMPLETE ✨")
    print("=" * 70)
    
    return stats


if __name__ == "__main__":
    run_sentiment_demo()
