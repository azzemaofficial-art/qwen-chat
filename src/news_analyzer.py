"""
News Analyzer - Analisi sentiment delle notizie finanziarie
Recupera e analizza notizie dal web per valutare il sentiment di mercato
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re


@dataclass
class NewsArticle:
    """Rappresenta un articolo di notizia"""
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str
    sentiment_score: float  # -1 (negativo) a +1 (positivo)
    relevance_score: float  # 0 a 1


class SentimentAnalyzer:
    """Analizzatore di sentiment basato su parole chiave"""
    
    def __init__(self):
        # Parole chiave positive
        self.positive_words = {
            'crescita', 'profitto', 'guadagno', 'successo', 'record',
            'ottimo', 'eccellente', 'superiore', 'batte', 'supera',
            'rialzo', 'aumento', 'boom', 'espansione', 'innovazione',
            'partnership', 'accordo', 'approvazione', 'lancio', 'breakthrough',
            'outperform', 'upgrade', 'buy', 'strong', 'positive', 'bullish',
            'revenue', 'earnings beat', 'guidance', 'dividend', 'growth'
        }
        
        # Parole chiave negative
        self.negative_words = {
            'perdita', 'calo', 'diminuzione', 'crisi', 'fallimento',
            'peggio', 'terribile', 'inferiore', 'manca', 'sotto',
            'ribasso', 'crollo', 'crash', 'contrazione', 'problema',
            'controversia', 'scandalo', 'indagine', 'ritardo', 'warning',
            'underperform', 'downgrade', 'sell', 'weak', 'negative', 'bearish',
            'loss', 'miss', 'cut', 'layoff', 'lawsuit', 'fraud'
        }
        
        # Parole ad alta intensità
        self.intensifiers = {
            'forte': 1.5, 'significativo': 1.4, 'notevole': 1.3,
            'sorprendente': 1.5, 'storico': 1.6, 'eccezionale': 1.7,
            'drammatico': 1.5, 'pesante': 1.4, 'massiccio': 1.5,
            'strong': 1.5, 'significant': 1.4, 'major': 1.4,
            'sharp': 1.3, 'huge': 1.5, 'massive': 1.6
        }
    
    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Analizza il sentiment di un testo
        
        Returns:
            Tuple con (score da -1 a +1, valutazione testuale)
        """
        if not text:
            return 0.0, "NEUTRALE"
        
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        positive_count = 0
        negative_count = 0
        intensity_multiplier = 1.0
        
        for word in words:
            if word in self.positive_words:
                positive_count += 1
            elif word in self.negative_words:
                negative_count += 1
            
            # Controlla intensificatori
            if word in self.intensifiers:
                intensity_multiplier = max(intensity_multiplier, self.intensifiers[word])
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0, "NEUTRALE"
        
        # Calcola score normalizzato
        raw_score = (positive_count - negative_count) / total
        score = raw_score * intensity_multiplier
        
        # Normalizza tra -1 e 1
        score = max(-1.0, min(1.0, score))
        
        # Determina valutazione testuale
        if score >= 0.5:
            sentiment = "MOLTO POSITIVO"
        elif score >= 0.2:
            sentiment = "POSITIVO"
        elif score >= -0.2:
            sentiment = "NEUTRALE"
        elif score >= -0.5:
            sentiment = "NEGATIVO"
        else:
            sentiment = "MOLTO NEGATIVO"
        
        return score, sentiment
    
    def calculate_relevance(self, text: str, symbol: str, company_name: str = "") -> float:
        """
        Calcola la rilevanza di un articolo rispetto a un titolo
        
        Args:
            text: Testo dell'articolo
            symbol: Simbolo del titolo (es. AAPL)
            company_name: Nome della compagnia (opzionale)
        
        Returns:
            Score di rilevanza da 0 a 1
        """
        text_lower = text.lower()
        symbol_lower = symbol.lower()
        
        relevance = 0.0
        
        # Presenza del simbolo
        if symbol_lower in text_lower:
            relevance += 0.4
        
        # Presenza del nome azienda
        if company_name and company_name.lower() in text_lower:
            relevance += 0.3
        
        # Parole chiave finanziarie
        financial_keywords = [
            'stock', 'action', 'titolo', 'trading', 'mercato',
            'price', 'prezzo', 'value', 'valore', 'market cap',
            'investor', 'investitore', 'share', 'azione'
        ]
        
        for keyword in financial_keywords:
            if keyword in text_lower:
                relevance += 0.02
        
        return min(1.0, relevance)


class NewsFetcher:
    """Classe per il recupero di notizie finanziarie"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def fetch_news_yahoo(self, symbol: str, limit: int = 10) -> List[NewsArticle]:
        """
        Recupera notizie da Yahoo Finance
        
        Args:
            symbol: Simbolo del titolo
            limit: Numero massimo di articoli
        
        Returns:
            Lista di NewsArticle
        """
        articles = []
        
        try:
            # Yahoo Finance news endpoint
            url = f"https://finance.yahoo.com/quote/{symbol}/news/"
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Errore nel recupero notizie: {response.status_code}")
                return articles
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Estrai articoli (selector può cambiare nel tempo)
            article_elements = soup.find_all('article', limit=limit)
            
            for elem in article_elements[:limit]:
                try:
                    title_elem = elem.find('h3') or elem.find('h4')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    link_elem = elem.find('a')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = f"https://finance.yahoo.com{url}"
                    
                    # Estrai sommario
                    summary_elem = elem.find('p')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    # Analizza sentiment
                    full_text = f"{title} {summary}"
                    sentiment_score, _ = self.sentiment_analyzer.analyze_sentiment(full_text)
                    relevance_score = self.sentiment_analyzer.calculate_relevance(full_text, symbol)
                    
                    article = NewsArticle(
                        title=title,
                        source="Yahoo Finance",
                        url=url,
                        published_at=datetime.now(),
                        summary=summary,
                        sentiment_score=sentiment_score,
                        relevance_score=relevance_score
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    continue
            
            print(f"Recuperati {len(articles)} articoli da Yahoo Finance")
            
        except Exception as e:
            print(f"Errore nel fetch news: {str(e)}")
        
        return articles
    
    def fetch_news_google(self, symbol: str, limit: int = 10) -> List[NewsArticle]:
        """
        Recupera notizie da Google News (simulato per demo)
        
        Nota: Per un uso production, usare API ufficiali
        """
        articles = []
        
        try:
            # Simulazione per demo - in produzione usare Google News API
            print(f"[Demo] Notizie Google per {symbol} - usare API ufficiale in produzione")
            
        except Exception as e:
            print(f"Errore nel fetch news Google: {str(e)}")
        
        return articles
    
    def get_combined_news(self, symbol: str, limit: int = 20) -> List[NewsArticle]:
        """
        Combina notizie da multiple fonti
        
        Args:
            symbol: Simbolo del titolo
            limit: Numero totale massimo di articoli
        
        Returns:
            Lista combinata di NewsArticle ordinata per rilevanza
        """
        all_articles = []
        
        # Yahoo Finance
        yahoo_news = self.fetch_news_yahoo(symbol, limit // 2)
        all_articles.extend(yahoo_news)
        
        # Ordina per rilevanza e sentiment
        all_articles.sort(key=lambda x: (x.relevance_score, x.sentiment_score), reverse=True)
        
        return all_articles[:limit]


class NewsAnalyzer:
    """Analizzatore principale delle notizie"""
    
    def __init__(self):
        self.fetcher = NewsFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def analyze_symbol_news(self, symbol: str, limit: int = 20) -> Dict:
        """
        Analizza tutte le notizie relative a un simbolo
        
        Returns:
            Dict con analisi completa
        """
        print(f"Analisi notizie per {symbol}...")
        
        articles = self.fetcher.get_combined_news(symbol, limit)
        
        if not articles:
            return {
                'symbol': symbol,
                'articles_count': 0,
                'overall_sentiment': 0.0,
                'sentiment_label': 'NEUTRALE',
                'recommendation': 'NESSUN DATO',
                'articles': []
            }
        
        # Calcola metriche aggregate
        relevant_articles = [a for a in articles if a.relevance_score > 0.3]
        
        if not relevant_articles:
            relevant_articles = articles[:5]  # Prendi i primi 5 se nessuno rilevante
        
        # Sentiment medio ponderato
        total_weight = sum(a.relevance_score for a in relevant_articles)
        if total_weight > 0:
            weighted_sentiment = sum(
                a.sentiment_score * a.relevance_score 
                for a in relevant_articles
            ) / total_weight
        else:
            weighted_sentiment = 0.0
        
        # Determina label
        if weighted_sentiment >= 0.5:
            sentiment_label = "MOLTO POSITIVO"
            recommendation = "ACQUISTO (sentiment forte)"
        elif weighted_sentiment >= 0.2:
            sentiment_label = "POSITIVO"
            recommendation = "ACQUISTO (sentiment moderato)"
        elif weighted_sentiment >= -0.2:
            sentiment_label = "NEUTRALE"
            recommendation = "ATTESA"
        elif weighted_sentiment >= -0.5:
            sentiment_label = "NEGATIVO"
            recommendation = "VENDITA (sentiment moderato)"
        else:
            sentiment_label = "MOLTO NEGATIVO"
            recommendation = "VENDITA (sentiment forte)"
        
        # Articoli recenti molto positivi/negativi
        very_positive = [a for a in articles if a.sentiment_score >= 0.5][:3]
        very_negative = [a for a in articles if a.sentiment_score <= -0.5][:3]
        
        return {
            'symbol': symbol,
            'articles_count': len(articles),
            'relevant_articles_count': len(relevant_articles),
            'overall_sentiment': weighted_sentiment,
            'sentiment_label': sentiment_label,
            'recommendation': recommendation,
            'very_positive_count': len(very_positive),
            'very_negative_count': len(very_negative),
            'top_positive_articles': very_positive,
            'top_negative_articles': very_negative,
            'articles': articles
        }
    
    def get_sentiment_summary(self, analysis_result: Dict) -> str:
        """Genera un riassunto testuale dell'analisi sentiment"""
        summary = f"""
=== ANALISI SENTIMENT NOTIZIE ===
Simbolo: {analysis_result['symbol']}
Articoli analizzati: {analysis_result['articles_count']}
Articoli rilevanti: {analysis_result['relevant_articles_count']}

Sentiment complessivo: {analysis_result['sentiment_label']}
Score: {analysis_result['overall_sentiment']:.2f}

Raccomandazione basata su news: {analysis_result['recommendation']}

Notizie molto positive: {analysis_result['very_positive_count']}
Notizie molto negative: {analysis_result['very_negative_count']}
"""
        return summary


if __name__ == "__main__":
    # Test
    analyzer = NewsAnalyzer()
    result = analyzer.analyze_symbol_news("AAPL", limit=10)
    
    print(analyzer.get_sentiment_summary(result))
    
    if result['top_positive_articles']:
        print("\n=== TOP NOTIZIE POSITIVE ===")
        for art in result['top_positive_articles']:
            print(f"- {art.title} (score: {art.sentiment_score:.2f})")
    
    if result['top_negative_articles']:
        print("\n=== TOP NOTIZIE NEGATIVE ===")
        for art in result['top_negative_articles']:
            print(f"- {art.title} (score: {art.sentiment_score:.2f})")
