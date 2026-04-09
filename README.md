# Trading Advisor Pro

Applicazione avanzata di analisi di mercato che combina:
- Analisi tecnica (grafici, indicatori)
- Analisi fondamentale (notizie, sentiment)
- Raccomandazioni di trading con livelli di confidenza

## ⚠️ DISCLAIMER
Questa applicazione è solo a scopo educativo e informativo. 
NON costituisce consulenza finanziaria. Il trading comporta rischi significativi.

## Installazione

```bash
pip install -r requirements.txt
```

## Utilizzo

```bash
python main.py --symbol AAPL --action analyze
```

## Struttura

- `src/technical_analysis.py` - Analisi tecnica e indicatori
- `src/news_analyzer.py` - Analisi sentiment delle notizie
- `src/recommendation_engine.py` - Motore di raccomandazione
- `src/data_fetcher.py` - Recupero dati di mercato
- `main.py` - Punto di ingresso principale

## Requisiti

- Python 3.8+
- API keys per dati di mercato (opzionale per dati gratuiti)
