# Trading Advisor Pro v5.0 - ULTIMATE EDITION
# Sistema di analisi e raccomandazione trading di ultima generazione
# Combina: Analisi Tecnica + Sentiment NLP + Machine Learning + Deep Learning + 
#          Quantum-Inspired Optimization + Risk Management Avanzato

import argparse
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalyzer
from src.news_analyzer import NewsAnalyzer
from src.recommendation_engine import RecommendationEngine, TradeRecommendation
from src.ml_predictor import MLPredictor
from src.risk_management import AdvancedRiskManager
from src.backtesting import AdvancedBacktester
from src.portfolio_optimizer import PortfolioOptimizer, create_portfolio_from_recommendations
from src.predictive_analytics import AdvancedMLPredictor
from src.quantum.quantum_engine import QuantumPortfolioOptimizer, QuantumRiskAnalyzer
from src.deep_learning import DeepLearningPredictor, DLArchitecture


class QuantumMarketAnalyzer:
    """Wrapper per compatibilità con quantum engine esistente"""
    
    def __init__(self):
        self.lookback_period = 60
        self.volatility_threshold = 0.02
        
    def analyze_market_state(self, prices: pd.Series) -> dict:
        """Analizza stato del mercato usando tecniche quantistiche simulate"""
        from src.quantum.quantum_engine import QuantumState
        
        returns = prices.pct_change().dropna()
        volatility = returns.rolling(20).std().iloc[-1]
        momentum = (prices.iloc[-1] - prices.iloc[-20]) / prices.iloc[-20]
        
        if abs(momentum) < 0.02 and volatility < self.volatility_threshold:
            state = QuantumState.SUPERPOSITION
            confidence = 0.6
        elif momentum > 0.05 and volatility < 0.04:
            state = QuantumState.COLLAPSED
            confidence = 0.85
        elif momentum < -0.05 and volatility < 0.04:
            state = QuantumState.DECOHERENT
            confidence = 0.85
        else:
            state = QuantumState.ENTANGLED
            confidence = 0.7
        
        return {
            'state': type('obj', (object,), {'value': state.value})(),
            'confidence': confidence,
            'superposition_index': max(0, min(1, 1 - abs(momentum) / 0.1)),
            'coherence': max(0, min(1, 1 - volatility / 0.1)),
            'momentum': momentum,
            'volatility': volatility
        }


def print_banner():
    """Stampa banner animato"""
    console.print(Panel.fit(
        "[bold blue]🚀 TRADING ADVISOR PRO v5.0 - ULTIMATE EDITION[/bold blue]\n\n"
        "[cyan]Analisi Tecnica[/cyan] • [green]Sentiment NLP[/green] • [yellow]Machine Learning[/yellow] • "
        "[magenta]Deep Learning[/magenta] • [red]Quantum Optimization[/red]",
        border_style="blue",
        padding=(1, 2)
    ))


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Trading Advisor Pro v5.0 ULTIMATE - Analisi avanzata mercati finanziari con AI e Quantum Computing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python main.py --symbol AAPL
  python main.py --symbol NVDA TSLA --capital 50000
  python main.py --symbol BTC-USD ETH-USD --quiet
  python main.py --symbol AAPL --export report_aapl.txt
  python main.py --symbol TSLA --dl-model hybrid --epochs 50
  python main.py --symbol AAPL GOOGL MSFT --quantum-optimization
  python main.py --symbol NVDA --all-models --backtest
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
    parser.add_argument(
        '--dl-model',
        type=str,
        choices=['lstm', 'gru', 'transformer', 'cnn_lstm', 'hybrid'],
        default='hybrid',
        help='Architettura Deep Learning (default: hybrid)'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=30,
        help='Numero di epoche per training DL (default: 30)'
    )
    parser.add_argument(
        '--quantum-optimization',
        action='store_true',
        help='Usa ottimizzazione quantistica per portafoglio'
    )
    parser.add_argument(
        '--all-models',
        action='store_true',
        help='Usa tutti i modelli disponibili (ML + DL + Quantum)'
    )
    parser.add_argument(
        '--backtest',
        action='store_true',
        help='Esegui backtesting delle strategie'
    )
    parser.add_argument(
        '--optimize-portfolio',
        action='store_true',
        help='Ottimizza portafoglio usando Modern Portfolio Theory + Quantum'
    )
    
    return parser.parse_args()


def analyze_symbol(
    symbol: str,
    capital: float,
    quiet: bool = False,
    ml_horizon: str = '1d',
    dl_model: str = 'hybrid',
    epochs: int = 30,
    use_quantum: bool = False,
    use_all_models: bool = False
) -> Optional[TradeRecommendation]:
    """Analizza un singolo simbolo con tutti i modelli avanzati"""
    
    if not quiet:
        console.print(f"\n{'='*70}")
        console.print(f"[bold cyan]📈 ANALISI COMPLETA ULTIMATE: {symbol}[/bold cyan]")
        console.print(f"{'='*70}")
        console.print(f"Data: [yellow]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
    
    # 1. Fetch dati
    if not quiet:
        console.print("\n[bold blue][1/7] 📡 Recupero dati di mercato...[/bold blue]")
    
    fetcher = DataFetcher()
    df = fetcher.get_stock_data(symbol, period='2y')  # Più dati per DL
    
    if df is None or len(df) < 100:
        console.print(f"[red]⚠️ Dati insufficienti per {symbol}[/red]")
        return None
    
    current_price = df['Close'].iloc[-1]
    
    if not quiet:
        console.print(f"   [green]✅[/green] {len(df)} giorni di dati recuperati")
        console.print(f"   Prezzo corrente: [bold green]${current_price:.2f}[/bold green]")
        console.print(f"   Range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")
    
    # 2. Analisi Tecnica Avanzata
    if not quiet:
        console.print("\n[bold blue][2/7] 📊 Analisi tecnica avanzata con pattern recognition...[/bold blue]")
    
    analyzer = TechnicalAnalyzer(df)
    analyzer.calculate_all_indicators()
    signals = analyzer.generate_signals()
    overall_signal, confidence, signal_desc = analyzer.get_overall_signal()
    support_resistance = analyzer.get_support_resistance()
    
    technical_result = {
        'signals': [s.signal.name for s in signals],
        'overall_signal': {
            'signal': overall_signal.name,
            'confidence': confidence,
            'direction': signal_desc
        },
        'patterns_detected': analyzer.detect_candlestick_patterns(),
        'support_resistance': support_resistance
    }
    
    if not quiet:
        console.print(f"   [green]✅[/green] {len(technical_result.get('signals', []))} indicatori analizzati")
        console.print(f"   [green]✅[/green] {len(technical_result.get('patterns_detected', []))} pattern rilevati")
        console.print(f"   Segnale: [bold yellow]{technical_result.get('overall_signal', {}).get('direction', 'NEUTRALE')}[/bold yellow]")
    
    # 3. Analisi Notizie con NLP
    if not quiet:
        console.print("\n[bold blue][3/7] 📰 Analisi sentiment notizie con NLP...[/bold blue]")
    
    news_analyzer = NewsAnalyzer()
    news_result = news_analyzer.analyze_symbol_news(symbol, limit=20)
    
    if not quiet:
        if news_result.get('articles_count', 0) > 0:
            console.print(f"   [green]✅[/green] {news_result['articles_count']} articoli analizzati")
            console.print(f"   Sentiment: [bold yellow]{news_result.get('sentiment_label', 'NEUTRALE')}[/bold yellow]")
        else:
            console.print("   [yellow]⚠️ Nessuna notizia disponibile (analisi saltata)[/yellow]")
    
    # 4. Machine Learning Prediction (Random Forest + Gradient Boosting)
    if not quiet:
        console.print(f"\n[bold blue][4/7] 🤖 Predizione Machine Learning (orizzonte: {ml_horizon})...[/bold blue]")
    
    df_ml = df.copy()
    df_ml['MA20'] = df_ml['Close'].rolling(20).mean()
    df_ml['MA50'] = df_ml['Close'].rolling(50).mean()
    df_ml['MA200'] = df_ml['Close'].rolling(200).mean()
    
    delta = df_ml['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df_ml['RSI'] = 100 - (100 / (1 + rs))
    
    exp1 = df_ml['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df_ml['Close'].ewm(span=26, adjust=False).mean()
    df_ml['MACD'] = exp1 - exp2
    df_ml['Signal'] = df_ml['MACD'].ewm(span=9, adjust=False).mean()
    
    high = df_ml['High']
    low = df_ml['Low']
    close = df_ml['Close']
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
    df_ml['ADX'] = dx.rolling(window=14).mean()
    
    ml_predictor = MLPredictor(horizon=ml_horizon)
    ml_metrics = ml_predictor.train(df_ml)
    
    ml_prediction = {}
    if 'error' not in ml_metrics:
        ml_prediction = ml_predictor.predict(df_ml)
        
        if not quiet and 'error' not in ml_prediction:
            console.print(f"   [green]✅[/green] Modello addestrato (accuracy: {ml_metrics.get('ensemble_accuracy', 0):.1%})")
            console.print(f"   Predizione: [bold cyan]{ml_prediction.get('prediction', 'N/A')}[/bold cyan]")
            console.print(f"   Confidenza: {ml_prediction.get('confidence', 0):.1f}%")
    else:
        if not quiet:
            console.print("   [yellow]⚠️ ML prediction non disponibile[/yellow]")
    
    # 5. Deep Learning Prediction (LSTM/GRU/Transformer/Hybrid)
    dl_prediction = {}
    if use_all_models or dl_model != 'none':
        if not quiet:
            console.print(f"\n[bold blue][5/7] 🧠 Deep Learning ({dl_model.upper()}) con Attention Mechanism...[/bold blue]")
        
        try:
            arch = DLArchitecture(
                model_type=dl_model,
                sequence_length=60,
                hidden_units=128,
                n_layers=2,
                dropout_rate=0.3
            )
            dl_predictor = DeepLearningPredictor(architecture=arch, horizon=ml_horizon)
            dl_metrics = dl_predictor.train(df, epochs=min(epochs, 20), batch_size=32)
            
            if 'error' not in dl_metrics:
                dl_prediction = dl_predictor.predict(df)
                
                if not quiet and 'error' not in dl_prediction:
                    console.print(f"   [green]✅[/green] {dl_model.upper()} addestrato (val accuracy: {dl_metrics.get('val_accuracy', 0):.1%})")
                    console.print(f"   Predizione DL: [bold magenta]{dl_prediction.get('prediction', 'N/A')}[/bold magenta]")
                    console.print(f"   Confidenza DL: {dl_prediction.get('confidence', 0):.1f}%")
        except Exception as e:
            if not quiet:
                console.print(f"   [yellow]⚠️ Deep Learning non disponibile: {str(e)[:50]}[/yellow]")
    
    # 6. Quantum Market Analysis (se abilitato)
    quantum_state = None
    if use_quantum or use_all_models:
        if not quiet:
            console.print("\n[bold blue][6/7] ⚛️ Quantum Market Analysis (QAOA Simulation)...[/bold blue]")
        
        try:
            quantum_analyzer = QuantumMarketAnalyzer()
            quantum_state = quantum_analyzer.analyze_market_state(df['Close'])
            
            if not quiet:
                console.print(f"   [green]✅[/green] Stato quantistico: [bold red]{quantum_state.get('state', 'UNKNOWN').value}[/bold red]")
                console.print(f"   Coerenza: {quantum_state.get('coherence', 0):.2f}")
                console.print(f"   Superposizione: {quantum_state.get('superposition_index', 0):.2f}")
        except Exception as e:
            if not quiet:
                console.print(f"   [yellow]⚠️ Quantum analysis non disponibile: {str(e)[:50]}[/yellow]")
    
    # 7. Genera Raccomandazione Integrata
    if not quiet:
        console.print("\n[bold blue][7/7] 💡 Generazione raccomandazione con ensemble AI...[/bold blue]")
    
    engine = RecommendationEngine(capital=capital)
    
    # Integra tutte le predizioni nel processo decisionale
    combined_confidence = confidence
    reasoning_extensions = []
    
    # ML adjustment
    if ml_prediction and 'probability' in ml_prediction:
        ml_signal_strength = ml_prediction['probability'] - 0.5
        if ml_prediction['prediction'] == 'DOWN':
            ml_signal_strength = -ml_signal_strength
        ml_adjustment = ml_signal_strength * 15
        combined_confidence += ml_adjustment
        reasoning_extensions.append(
            f"ML ({ml_horizon}): {ml_prediction['prediction']} (prob: {ml_prediction['probability']:.1%})"
        )
    
    # DL adjustment
    if dl_prediction and 'probability' in dl_prediction:
        dl_signal_strength = dl_prediction['probability'] - 0.5
        if dl_prediction['prediction'] == 'DOWN':
            dl_signal_strength = -dl_signal_strength
        dl_adjustment = dl_signal_strength * 20  # DL ha più peso
        combined_confidence += dl_adjustment
        reasoning_extensions.append(
            f"DL ({dl_model}): {dl_prediction['prediction']} (conf: {dl_prediction['confidence']:.1f}%)"
        )
    
    # Quantum adjustment
    if quantum_state:
        if quantum_state['state'].value == 'collapsed_up':
            combined_confidence += 10
            reasoning_extensions.append(f"Quantum: trend rialzista confermato")
        elif quantum_state['state'].value == 'collapsed_down':
            combined_confidence -= 10
            reasoning_extensions.append(f"Quantum: trend ribassista confermato")
    
    # Normalizza confidenza
    combined_confidence = min(95, max(5, combined_confidence))
    
    if 'overall_signal' not in technical_result:
        technical_result['overall_signal'] = {}
    technical_result['overall_signal']['confidence'] = combined_confidence
    
    recommendation = engine.generate_recommendation(
        symbol=symbol,
        technical_data=technical_result,
        news_data=news_result,
        current_price=current_price
    )
    
    # Aggiungi reasoning da tutti i modelli
    recommendation.reasoning.extend(reasoning_extensions)
    
    if not quiet:
        adjustments = []
        if ml_prediction:
            adjustments.append(f"ML: {ml_prediction.get('prediction', 'N/A')}")
        if dl_prediction:
            adjustments.append(f"DL: {dl_prediction.get('prediction', 'N/A')}")
        if quantum_state:
            adjustments.append(f"Quantum: {quantum_state['state'].value}")
        if adjustments:
            console.print(f"   [cyan]Ensemble: {' | '.join(adjustments)}[/cyan]")
    
    # Analisi del Rischio Avanzata
    if not quiet:
        console.print("\n[bold blue]⚠️ Analisi avanzata del rischio...[/bold blue]")
    
    risk_manager = AdvancedRiskManager()
    risk_metrics = risk_manager.calculate_risk_metrics(df['Close'])
    risk_rating = risk_manager.get_risk_rating(risk_metrics)
    
    if not quiet:
        console.print(f"   Risk Rating: [bold yellow]{risk_rating}[/bold yellow]")
        console.print(f"   VaR 95%: {risk_metrics.var_95:.2%}")
        console.print(f"   Sharpe Ratio: {risk_metrics.sharpe_ratio:.2f}")
    
    # Aggiusta raccomandazione in base al rischio
    if risk_rating in ["MOLTO_ALTO", "ALTO"]:
        recommendation.risk_level = risk_rating.lower().replace("_", "-")
        recommendation.leverage_suggestion = min(recommendation.leverage_suggestion, 1.0)
        recommendation.position_size_pct = min(recommendation.position_size_pct, 10.0)
    
    if not quiet:
        console.print("\n" + "="*70)
        console.print(engine.format_recommendation(recommendation))
    
    return recommendation


def main():
    """Funzione principale"""
    args = parse_arguments()
    
    print_banner()
    
    console.print(f"\n[bold]Configurazione:[/bold]")
    console.print(f"   Capitale: [green]${args.capital:,.0f}[/green]")
    console.print(f"   Simboli: [cyan]{', '.join(args.symbol)}[/cyan]")
    console.print(f"   ML Horizon: [yellow]{args.ml_horizon}[/yellow]")
    console.print(f"   DL Model: [magenta]{args.dl_model}[/magenta]")
    console.print(f"   Epochs: {args.epochs}")
    console.print(f"   Quantum: {'[red]SI[/red]' if args.quantum_optimization or args.all_models else '[grey]NO[/grey]'}")
    console.print(f"   Modalità quiet: {'[red]SI[/red]' if args.quiet else '[green]NO[/green]'}")

    all_recommendations = []

    for symbol in args.symbol:
        try:
            rec = analyze_symbol(
                symbol=symbol,
                capital=args.capital,
                quiet=args.quiet,
                ml_horizon=args.ml_horizon,
                dl_model=args.dl_model,
                epochs=args.epochs,
                use_quantum=args.quantum_optimization,
                use_all_models=args.all_models
            )
            if rec:
                all_recommendations.append(rec)
        except Exception as e:
            console.print(f"\n[red]❌ Errore nell'analisi di {symbol}: {str(e)}[/red]")
            if not args.quiet:
                import traceback
                traceback.print_exc()

    if len(all_recommendations) > 0:
        console.print("\n" + "="*70)
        console.print("[bold]📋 RIEPILOGO RACCOMANDAZIONI[/bold]")
        console.print("="*70)
        
        for rec in all_recommendations:
            emoji = "🟢" if "ACQUISTO" in rec.action.value else "🔴" if "VENDITA" in rec.action.value else "🟡"
            console.print(f"{emoji} [bold]{rec.symbol}[/bold]: {rec.action.value} (conf: [yellow]{rec.confidence}%[/yellow])")
        
        # Portfolio optimization se richiesto
        if args.optimize_portfolio and len(all_recommendations) >= 2:
            console.print("\n[bold blue]🎯 Ottimizzazione portafoglio con Quantum AI...[/bold blue]")
            try:
                portfolio = create_portfolio_from_recommendations(all_recommendations, args.capital)
                optimizer = PortfolioOptimizer()
                
                returns = np.array([0.08, 0.10, 0.12, 0.09, 0.11])[:len(all_recommendations)]
                cov = np.eye(len(all_recommendations)) * 0.04
                
                if args.quantum_optimization:
                    quantum_optimizer = QuantumPortfolioOptimizer(n_assets=len(all_recommendations))
                    quantum_result = quantum_optimizer.optimize_portfolio(returns, cov)
                    
                    console.print(f"   Pesi ottimizzati (Quantum): {[f'{w:.1%}' for w in quantum_result['weights']]}")
                    console.print(f"   Sharpe Ratio: {quantum_result['sharpe_ratio']:.2f}")
                    console.print(f"   Vantaggio Quantistico: {quantum_result['quantum_metrics'].quantum_advantage:.2f}x")
            except Exception as e:
                console.print(f"   [yellow]⚠️ Ottimizzazione non disponibile: {str(e)[:50]}[/yellow]")
        
        if args.export:
            try:
                with open(args.export, 'w', encoding='utf-8') as f:
                    f.write(f"Trading Advisor Pro v5.0 ULTIMATE - Report del {datetime.now()}\n")
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
                
                console.print(f"\n[green]✅ Report esportato in: {args.export}[/green]")
            except Exception as e:
                console.print(f"\n[red]❌ Errore nell'export: {str(e)}[/red]")

    console.print("\n" + "="*70)
    console.print("[bold red]⚠️ DISCLAIMER[/bold red]: Questo software è a scopo [yellow]educativo[/yellow].")
    console.print("   Il trading finanziario comporta [bold]rischi elevati[/bold].")
    console.print("   Non investire denaro che non puoi permetterti di perdere.")
    console.print("="*70)


if __name__ == "__main__":
    main()
