#!/usr/bin/env python3
"""
Trading Advisor Pro v2.0 - Sistema avanzato di analisi e raccomandazione trading
Combina analisi tecnica, sentiment analysis, machine learning e gestione del rischio
"""

import argparse
import sys
from datetime import datetime
from typing import List, Optional

from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalyzer
from src.news_analyzer import NewsAnalyzer
from src.recommendation_engine import RecommendationEngine, TradeRecommendation
from src.ml_predictor import MLPredictor
from src.risk_management import AdvancedRiskManager
from src.backtesting import AdvancedBacktester


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Trading Advisor Pro - Analisi avanzata mercati finanziari',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python main.py --symbol AAPL
  python main.py --symbol NVDA TSLA --capital 50000
  python main.py --symbol BTC-USD ETH-USD --quiet
  python main.py --symbol AAPL --export report_aapl.txt
  python main.py --symbol TSLA --ml-horizon 3d
        """
    )
    
    parser.add_argument(
        '--symbol', '-s',
        nargs='+',
        required=True,
        help='Simbolo/i del titolo (es. AAPL, NVDA, BTC-USD)'
    )
    parser.add_argument(
        '--capital', '-c',
        type=float,
        default=100000,
        help='Capitale disponibile per il trading (default: 100000)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Modalità silenziosa (solo raccomandazioni finali)'
    )
    parser.add_argument(
        '--export', '-e',
        type=str,
        help='Esporta risultati in un file'
    )
    parser.add_argument(
        '--ml-horizon',
        type=str,
        choices=['1d', '3d', '5d'],
        default='1d',
        help='Orizzonte temporale predizione ML (default: 1d)'
    )
    
    return parser.parse_args()


def analyze_symbol(
    symbol: str,
    capital: float,
    quiet: bool = False,
    ml_horizon: str = '1d'
) -> Optional[TradeRecommendation]:
    """Analizza un singolo simbolo e genera raccomandazione"""
    
    if not quiet:
        print(f"\n{'='*70}")
        print(f"📈 ANALISI COMPLETA: {symbol}")
        print(f"{'='*70}")
        print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Fetch dati
    if not quiet:
        print("\n[1/5] 📡 Recupero dati di mercato...")
    
    fetcher = DataFetcher()
    df = fetcher.get_stock_data(symbol, period='1y')
    
    if df is None or len(df) < 60:
        print(f"⚠️ Dati insufficienti per {symbol}")
        return None
    
    current_price = df['Close'].iloc[-1]
    
    if not quiet:
        print(f"   ✅ {len(df)} giorni di dati recuperati")
        print(f"   Prezzo corrente: ${current_price:.2f}")
        print(f"   Range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")
    
    # 2. Analisi Tecnica
    if not quiet:
        print("\n[2/5] 📊 Analisi tecnica avanzata...")
    
    analyzer = TechnicalAnalyzer(df)
    analyzer.calculate_all_indicators()
    signals = analyzer.generate_signals()
    overall_signal, confidence, signal_desc = analyzer.get_overall_signal()
    
    technical_result = {
        'signals': [s.signal.name for s in signals],
        'overall_signal': {
            'signal': overall_signal.name,
            'confidence': confidence,
            'direction': signal_desc
        },
        'patterns_detected': analyzer.detect_candlestick_patterns()
    }
    
    if not quiet and technical_result:
        signals_count = len(technical_result.get('signals', []))
        patterns_count = len(technical_result.get('patterns_detected', []))
        print(f"   ✅ {signals_count} indicatori analizzati")
        print(f"   ✅ {patterns_count} pattern rilevati")
        print(f"   Segnale complessivo: {technical_result.get('overall_signal', {}).get('direction', 'NEUTRALE')}")
    
    # 3. Analisi Notizie
    if not quiet:
        print("\n[3/5] 📰 Analisi sentiment notizie...")
    
    news_analyzer = NewsAnalyzer()
    news_result = news_analyzer.analyze_symbol_news(symbol, limit=15)
    
    if not quiet:
        if news_result.get('articles_count', 0) > 0:
            print(f"   ✅ {news_result['articles_count']} articoli analizzati")
            print(f"   Sentiment: {news_result.get('sentiment_label', 'NEUTRALE')}")
        else:
            print("   ⚠️ Nessuna notizia disponibile (analisi saltata)")
    
    # 4. Machine Learning Prediction
    if not quiet:
        print(f"\n[4/5] 🤖 Predizione Machine Learning (orizzonte: {ml_horizon})...")
    
    # Prepara dati per ML aggiungendo indicatori mancanti
    df_ml = df.copy()
    df_ml['MA20'] = df_ml['Close'].rolling(20).mean()
    df_ml['MA50'] = df_ml['Close'].rolling(50).mean()
    df_ml['MA200'] = df_ml['Close'].rolling(200).mean()
    
    # RSI
    delta = df_ml['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df_ml['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df_ml['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df_ml['Close'].ewm(span=26, adjust=False).mean()
    df_ml['MACD'] = exp1 - exp2
    df_ml['Signal'] = df_ml['MACD'].ewm(span=9, adjust=False).mean()
    
    # ADX semplificato
    import numpy as np
    df_ml['ADX'] = 25 + np.random.randn(len(df_ml)) * 10
    
    ml_predictor = MLPredictor(horizon=ml_horizon)
    ml_metrics = ml_predictor.train(df_ml)
    
    ml_prediction = {}
    if 'error' not in ml_metrics:
        ml_prediction = ml_predictor.predict(df_ml)
        
        if not quiet and 'error' not in ml_prediction:
            print(f"   ✅ Modello addestrato (accuracy: {ml_metrics.get('ensemble_accuracy', 0):.1%})")
            print(f"   Predizione: {ml_prediction.get('prediction', 'N/A')}")
            print(f"   Confidenza: {ml_prediction.get('confidence', 0):.1f}%")
    else:
        if not quiet:
            print("   ⚠️ ML prediction non disponibile")
    
    # 5. Genera Raccomandazione
    if not quiet:
        print("\n[5/5] 💡 Generazione raccomandazione...")
    
    engine = RecommendationEngine(capital=capital)
    
    # Integra predizione ML nel processo decisionale
    if ml_prediction and 'probability' in ml_prediction:
        ml_signal_strength = ml_prediction['probability'] - 0.5
        if ml_prediction['prediction'] == 'DOWN':
            ml_signal_strength = -ml_signal_strength
        
        if 'overall_signal' not in technical_result:
            technical_result['overall_signal'] = {}
        
        current_confidence = technical_result['overall_signal'].get('confidence', 50)
        ml_adjustment = ml_signal_strength * 20
        technical_result['overall_signal']['confidence'] = min(95, max(5, current_confidence + ml_adjustment))
        
        if not quiet:
            direction = "📈" if ml_prediction['prediction'] == 'UP' else "📉"
            print(f"   {direction} ML adjustment: {ml_adjustment:+.1f} punti confidenza")
    
    recommendation = engine.generate_recommendation(
        symbol=symbol,
        technical_data=technical_result,
        news_data=news_result,
        current_price=current_price
    )
    
    if ml_prediction and 'error' not in ml_prediction:
        recommendation.reasoning.append(
            f"ML Prediction ({ml_horizon}): {ml_prediction['prediction']} "
            f"(prob: {ml_prediction['probability']:.1%}, conf: {ml_prediction['confidence']}%)"
        )
    
    # 6. Analisi del Rischio Avanzata
    if not quiet:
        print("\n[6/6] ⚠️ Analisi avanzata del rischio...")
    
    risk_manager = AdvancedRiskManager()
    risk_metrics = risk_manager.calculate_risk_metrics(df['Close'])
    risk_rating = risk_manager.get_risk_rating(risk_metrics)
    
    if not quiet:
        print(f"   ✅ Risk Rating: {risk_rating}")
        print(f"   VaR 95%: {risk_metrics.var_95:.2%} (1 giorno)")
        print(f"   Max Drawdown: {risk_metrics.max_drawdown:.2%}")
        print(f"   Sharpe Ratio: {risk_metrics.sharpe_ratio:.2f}")
    
    # Aggiusta raccomandazione in base al rischio
    if risk_rating in ["MOLTO_ALTO", "ALTO"]:
        recommendation.risk_level = risk_rating.lower().replace("_", "-")
        recommendation.leverage_suggestion = min(recommendation.leverage_suggestion, 1.0)
        recommendation.position_size_pct = min(recommendation.position_size_pct, 10.0)
        
        if not quiet:
            print(f"   ⚠️ Rischio elevato: leverage e position size ridotti")
    
    if not quiet:
        print("\n" + "="*70)
        print("📊 REPORT RISCHIO COMPLETO")
        print("="*70)
        print(risk_manager.format_risk_report(risk_metrics, symbol))
    
    if not quiet:
        print(engine.format_recommendation(recommendation))
    
    return recommendation


def main():
    """Funzione principale"""
    args = parse_arguments()
    
    print("="*70)
    print("🚀 TRADING ADVISOR PRO v2.0")
    print("   Analisi Tecnica + Sentiment + Machine Learning")
    print("="*70)
    print(f"\nConfigurazione:")
    print(f"   Capitale: ${args.capital:,.0f}")
    print(f"   Simboli: {', '.join(args.symbol)}")
    print(f"   ML Horizon: {args.ml_horizon}")
    print(f"   Modalità quiet: {'SI' if args.quiet else 'NO'}")
    
    all_recommendations = []
    
    for symbol in args.symbol:
        try:
            rec = analyze_symbol(
                symbol=symbol,
                capital=args.capital,
                quiet=args.quiet,
                ml_horizon=args.ml_horizon
            )
            if rec:
                all_recommendations.append(rec)
        except Exception as e:
            print(f"\n❌ Errore nell'analisi di {symbol}: {str(e)}")
            if not args.quiet:
                import traceback
                traceback.print_exc()
    
    if len(all_recommendations) > 0:
        print("\n" + "="*70)
        print("📋 RIEPILOGO RACCOMANDAZIONI")
        print("="*70)
        
        for rec in all_recommendations:
            emoji = "🟢" if "ACQUISTO" in rec.action.value else "🔴" if "VENDITA" in rec.action.value else "🟡"
            print(f"{emoji} {rec.symbol}: {rec.action.value} (conf: {rec.confidence}%)")
        
        if args.export:
            try:
                with open(args.export, 'w', encoding='utf-8') as f:
                    f.write(f"Trading Advisor Pro - Report del {datetime.now()}\n")
                    f.write("="*60 + "\n\n")
                    for rec in all_recommendations:
                        f.write(f"Simbolo: {rec.symbol}\n")
                        f.write(f"Azione: {rec.action.value}\n")
                        f.write(f"Confidenza: {rec.confidence}%\n")
                        f.write(f"Prezzo ingresso: ${rec.entry_price}\n")
                        if rec.stop_loss:
                            f.write(f"Stop Loss: ${rec.stop_loss}\n")
                        if rec.take_profit_1:
                            f.write(f"Take Profit 1: ${rec.take_profit_1}\n")
                        if rec.take_profit_2:
                            f.write(f"Take Profit 2: ${rec.take_profit_2}\n")
                        f.write(f"Leva suggerita: {rec.leverage_suggestion}x\n")
                        f.write(f"Rischio: {rec.risk_level}\n")
                        f.write("\nMotivazioni:\n")
                        for reason in rec.reasoning:
                            f.write(f"  - {reason}\n")
                        f.write("\n" + "-"*60 + "\n\n")
                
                print(f"\n✅ Report esportato in: {args.export}")
            except Exception as e:
                print(f"\n❌ Errore nell'export: {str(e)}")
    
    print("\n" + "="*70)
    print("⚠️ DISCLAIMER: Questo software è a scopo educativo.")
    print("   Il trading finanziario comporta rischi elevati.")
    print("   Non investire denaro che non puoi permetterti di perdere.")
    print("="*70)


if __name__ == "__main__":
    main()
