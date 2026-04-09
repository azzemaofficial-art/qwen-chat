#!/usr/bin/env python3
"""
Trading Advisor Pro - Applicazione principale
Analisi completa di mercato con raccomandazioni di trading

Utilizzo:
    python main.py --symbol AAPL --capital 50000
    python main.py --symbol TSLA --analyze-all
"""

import argparse
import sys
from datetime import datetime
from typing import Optional

# Import moduli
try:
    from src.data_fetcher import DataFetcher
    from src.technical_analysis import TechnicalAnalyzer, Signal
    from src.news_analyzer import NewsAnalyzer
    from src.recommendation_engine import RecommendationEngine, TradeRecommendation
except ImportError as e:
    print(f"Errore nell'importazione dei moduli: {e}")
    print("Assicurati di aver installato i requisiti: pip install -r requirements.txt")
    sys.exit(1)


class TradingAdvisor:
    """Classe principale che coordina tutte le analisi"""
    
    def __init__(self, capital: float = 100000):
        """
        Args:
            capital: Capitale disponibile per il trading
        """
        self.capital = capital
        self.data_fetcher = DataFetcher()
        self.news_analyzer = NewsAnalyzer()
        self.recommendation_engine = RecommendationEngine(capital=capital)
        
        print(f"=" * 60)
        print(f"TRADING ADVISOR PRO v1.0")
        print(f"Capitale configurato: ${capital:,.2f}")
        print(f"=" * 60)
    
    def analyze_symbol(self, symbol: str, verbose: bool = True) -> Optional[TradeRecommendation]:
        """
        Esegue un'analisi completa su un simbolo
        
        Args:
            symbol: Simbolo del titolo da analizzare
            verbose: Se True, stampa output dettagliato
        
        Returns:
            TradeRecommendation o None se errore
        """
        print(f"\n{'='*60}")
        print(f"ANALISI COMPLETA PER: {symbol}")
        print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}\n")
        
        # 1. Recupero dati di mercato
        print("📊 [1/4] Recupero dati di mercato...")
        df = self.data_fetcher.get_stock_data(symbol, period="6mo")
        
        if df is None or df.empty:
            print(f"❌ Impossibile recuperare dati per {symbol}")
            return None
        
        current_price = self.data_fetcher.get_current_price(symbol)
        stock_info = self.data_fetcher.get_stock_info(symbol)
        
        if current_price:
            print(f"   Prezzo corrente: ${current_price:.2f}")
        
        # 2. Analisi tecnica
        print("\n📈 [2/4] Analisi tecnica...")
        try:
            tech_analyzer = TechnicalAnalyzer(df)
            tech_analyzer.calculate_all_indicators()
            signals = tech_analyzer.generate_signals()
            
            overall_signal, confidence, signal_desc = tech_analyzer.get_overall_signal()
            support_resistance = tech_analyzer.get_support_resistance()
            
            print(f"   Segnale complessivo: {signal_desc}")
            
            if verbose:
                print(f"\n   Indicatori principali:")
                for sig in signals[:5]:
                    print(f"   - {sig.name}: {sig.signal.value}")
            
            # Prepara dati tecnici per il motore
            technical_data = {
                'signals': [s.signal.name for s in signals],
                'overall_signal': {
                    'signal': overall_signal.name,
                    'confidence': confidence
                },
                'rsi': tech_analyzer.indicators.get('RSI', {}).iloc[-1] if 'RSI' in tech_analyzer.indicators else 50,
                'macd_signal': self._get_macd_signal(tech_analyzer),
                'ma_trend': self._get_ma_trend(tech_analyzer),
                'atr': tech_analyzer.indicators.get('ATR', {}).iloc[-1] if 'ATR' in tech_analyzer.indicators else current_price * 0.02,
                'volatility': self._calculate_volatility(df),
                'support_resistance': support_resistance
            }
            
        except Exception as e:
            print(f"   ⚠️ Errore nell'analisi tecnica: {str(e)}")
            technical_data = {}
        
        # 3. Analisi notizie/sentiment
        print("\n📰 [3/4] Analisi notizie e sentiment...")
        try:
            news_result = self.news_analyzer.analyze_symbol_news(symbol, limit=15)
            
            print(f"   Articoli analizzati: {news_result['articles_count']}")
            print(f"   Sentiment: {news_result['sentiment_label']} (score: {news_result['overall_sentiment']:.2f})")
            
            if verbose and news_result.get('top_positive_articles'):
                print(f"\n   Top news positiva:")
                for art in news_result['top_positive_articles'][:2]:
                    print(f"   + {art.title[:80]}")
            
            if verbose and news_result.get('top_negative_articles'):
                print(f"\n   Top news negativa:")
                for art in news_result['top_negative_articles'][:2]:
                    print(f"   - {art.title[:80]}")
            
        except Exception as e:
            print(f"   ⚠️ Errore nell'analisi news: {str(e)}")
            news_result = {
                'overall_sentiment': 0,
                'sentiment_label': 'NEUTRALE',
                'articles_count': 0,
                'very_positive_count': 0,
                'very_negative_count': 0
            }
        
        # 4. Genera raccomandazione
        print("\n💡 [4/4] Generazione raccomandazione...")
        
        recommendation = self.recommendation_engine.generate_recommendation(
            symbol=symbol,
            technical_data=technical_data,
            news_data=news_result,
            current_price=current_price or 0
        )
        
        # Stampa raccomandazione finale
        if verbose:
            print(self.recommendation_engine.format_recommendation(recommendation))
        
        return recommendation
    
    def _get_macd_signal(self, analyzer: TechnicalAnalyzer) -> str:
        """Determina il segnale MACD"""
        try:
            macd = analyzer.indicators.get('MACD', {})
            if macd:
                macd_line = macd['macd'].iloc[-1]
                signal_line = macd['signal'].iloc[-1]
                
                if macd_line > signal_line:
                    return 'bullish'
                elif macd_line < signal_line:
                    return 'bearish'
        except:
            pass
        return 'neutral'
    
    def _get_ma_trend(self, analyzer: TechnicalAnalyzer) -> str:
        """Determina il trend delle medie mobili"""
        try:
            sma_20 = analyzer.indicators.get('SMA_20', pd.Series([0])).iloc[-1]
            sma_50 = analyzer.indicators.get('SMA_50', pd.Series([0])).iloc[-1]
            sma_200 = analyzer.indicators.get('SMA_200', pd.Series([0])).iloc[-1]
            
            if sma_20 > sma_50 > sma_200:
                return 'bullish'
            elif sma_20 < sma_50 < sma_200:
                return 'bearish'
        except:
            pass
        return 'neutral'
    
    def _calculate_volatility(self, df) -> float:
        """Calcola la volatilità annualizzata"""
        try:
            returns = df['Close'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)
            return volatility
        except:
            return 0.3


def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(
        description="Trading Advisor Pro - Analisi di mercato e raccomandazioni",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python main.py --symbol AAPL
  python main.py --symbol TSLA --capital 25000
  python main.py --symbol GOOGL MSFT AAPL --capital 100000
        """
    )
    
    parser.add_argument(
        '--symbol', '-s',
        nargs='+',
        required=True,
        help='Simbolo/i del titolo da analizzare (es. AAPL, TSLA)'
    )
    
    parser.add_argument(
        '--capital', '-c',
        type=float,
        default=50000,
        help='Capitale disponibile per il trading (default: 50000)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Output minimale (solo raccomandazione finale)'
    )
    
    parser.add_argument(
        '--export', '-e',
        type=str,
        help='Esporta risultati in file JSON'
    )
    
    args = parser.parse_args()
    
    # Crea advisor
    advisor = TradingAdvisor(capital=args.capital)
    
    results = []
    
    # Analizza ogni simbolo
    for symbol in args.symbol:
        result = advisor.analyze_symbol(
            symbol=symbol.upper(),
            verbose=not args.quiet
        )
        
        if result:
            results.append({
                'symbol': result.symbol,
                'action': result.action.value,
                'confidence': result.confidence,
                'entry_price': result.entry_price,
                'stop_loss': result.stop_loss,
                'take_profit_1': result.take_profit_1,
                'leverage': result.leverage_suggestion,
                'position_size_pct': result.position_size_pct
            })
    
    # Riepilogo finale
    if len(args.symbol) > 1:
        print("\n" + "="*60)
        print("RIEPILOGO RACCOMANDAZIONI")
        print("="*60)
        
        for res in results:
            emoji = "🟢" if "ACQUISTO" in res['action'] else "🔴" if "VENDITA" in res['action'] else "🟡"
            print(f"{emoji} {res['symbol']}: {res['action']} ({res['confidence']}% confidenza)")
    
    print("\n" + "="*60)
    print("⚠️  DISCLAIMER IMPORTANTE")
    print("="*60)
    print("""
Questa applicazione fornisce solo analisi tecniche e statistiche.
NON costituisce consulenza finanziaria, raccomandazione di investimento,
o sollecitazione all'investimento.

Il trading di strumenti finanziari comporta rischi significativi di perdita.
Prima di effettuare qualsiasi operazione:
- Fai sempre le tue ricerche (DYOR)
- Considera la tua situazione finanziaria personale
- Consulta un consulente finanziario professionista se necessario
- Investi solo capitale che puoi permetterti di perdere

Performance passate non garantiscono risultati futuri.
    """)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
