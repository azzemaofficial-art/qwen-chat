"""
Advanced Machine Learning Predictor - Predittore ML per trading
Utilizza Random Forest e Gradient Boosting per prevedere direzioni future
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')


class FeatureEngineer:
    """Crea feature avanzate per il modello ML"""
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crea feature tecniche avanzate per il training
        """
        features = df.copy()
        
        # Feature di momentum
        features['returns_1d'] = df['Close'].pct_change(1)
        features['returns_5d'] = df['Close'].pct_change(5)
        features['returns_10d'] = df['Close'].pct_change(10)
        features['returns_20d'] = df['Close'].pct_change(20)
        
        # Volatilità rolling
        features['volatility_5d'] = df['Close'].rolling(5).std()
        features['volatility_10d'] = df['Close'].rolling(10).std()
        features['volatility_ratio'] = features['volatility_5d'] / (features['volatility_10d'] + 1e-9)
        
        # Volume analysis
        features['volume_ma_ratio'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-9)
        features['volume_spike'] = (df['Volume'] > df['Volume'].rolling(20).mean() * 2).astype(int)
        
        # Price position
        features['price_vs_ma20'] = df['Close'] / df['MA20'] - 1
        features['price_vs_ma50'] = df['Close'] / df['MA50'] - 1
        features['price_vs_ma200'] = df['Close'] / df['MA200'] - 1
        
        # Range position
        rolling_high = df['High'].rolling(20).max()
        rolling_low = df['Low'].rolling(20).min()
        features['price_position_20d'] = (df['Close'] - rolling_low) / (rolling_high - rolling_low + 1e-9)
        
        # RSI derivatives
        if 'RSI' in df.columns:
            features['rsi_divergence'] = df['RSI'] - df['RSI'].shift(5)
            features['rsi_extreme'] = ((df['RSI'] < 30) | (df['RSI'] > 70)).astype(int)
        
        # MACD derivatives
        if 'MACD' in df.columns and 'Signal' in df.columns:
            features['macd_histogram'] = df['MACD'] - df['Signal']
            features['macd_cross'] = (features['macd_histogram'] * features['macd_histogram'].shift(1) < 0).astype(int)
        
        # Trend strength
        features['adx_trend'] = df.get('ADX', pd.Series([25]*len(df)))
        features['trend_strength'] = features['adx_trend'] / 100
        
        # Gap analysis
        features['gap'] = df['Open'] - df['Close'].shift(1)
        features['gap_pct'] = features['gap'] / df['Close'].shift(1)
        
        # Candlestick patterns
        features['body_size'] = abs(df['Close'] - df['Open'])
        features['upper_shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)
        features['lower_shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']
        features['doji_pattern'] = (features['body_size'] < (df['High'] - df['Low']) * 0.1).astype(int)
        
        # Lag features
        for lag in [1, 2, 3, 5]:
            features[f'returns_lag_{lag}'] = features['returns_1d'].shift(lag)
            features[f'volume_lag_{lag}'] = features['volume_ma_ratio'].shift(lag)
        
        # Target variable: direzione futura (1 = sale, 0 = scende)
        features['target_next_1d'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        features['target_next_3d'] = (df['Close'].shift(-3) > df['Close']).astype(int)
        features['target_next_5d'] = (df['Close'].shift(-5) > df['Close']).astype(int)
        
        return features
    
    def get_feature_columns(self) -> List[str]:
        """Restituisce la lista delle feature da usare nel modello"""
        return [
            'returns_1d', 'returns_5d', 'returns_10d', 'returns_20d',
            'volatility_5d', 'volatility_10d', 'volatility_ratio',
            'volume_ma_ratio', 'volume_spike',
            'price_vs_ma20', 'price_vs_ma50', 'price_vs_ma200',
            'price_position_20d',
            'rsi_divergence', 'rsi_extreme',
            'macd_histogram', 'macd_cross',
            'trend_strength',
            'gap_pct',
            'body_size', 'upper_shadow', 'lower_shadow', 'doji_pattern',
            'returns_lag_1', 'returns_lag_2', 'returns_lag_3', 'returns_lag_5',
            'volume_lag_1', 'volume_lag_2', 'volume_lag_3', 'volume_lag_5'
        ]


class MLPredictor:
    """Predittore basato su Machine Learning"""
    
    def __init__(self, horizon: str = '1d'):
        """
        Args:
            horizon: Orizzonte temporale ('1d', '3d', '5d')
        """
        self.horizon = horizon
        self.target_col = f'target_next_{horizon}'
        self.feature_engineer = FeatureEngineer()
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        self.gb_model = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            random_state=42
        )
        self.is_fitted = False
        self.feature_columns = []
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepara i dati per il training"""
        features = self.feature_engineer.create_features(df)
        self.feature_columns = self.feature_engineer.get_feature_columns()
        
        # Rimuovi NaN
        features = features.dropna(subset=self.feature_columns + [self.target_col])
        
        X = features[self.feature_columns]
        y = features[self.target_col]
        
        return X, y
    
    def train(self, df: pd.DataFrame, test_size: float = 0.2) -> Dict:
        """
        Addestra i modelli
        Returns:
            Dictionary con metriche di performance
        """
        print(f"\n🤖 Training ML Predictor (orizzonte: {self.horizon})...")
        
        X, y = self.prepare_data(df)
        
        if len(X) < 50:
            print("⚠️ Dati insufficienti per ML completo, uso modello statistico avanzato")
            return self._statistical_fallback(df)
        
        # Riduci test_size se abbiamo pochi dati
        if len(X) < 150:
            test_size = 0.15
            print(f"   ℹ️ Dataset ridotto: uso {test_size:.0%} per test")
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )
        
        # Scaling
        X_train_scaled = self.feature_engineer.scaler.fit_transform(X_train)
        X_test_scaled = self.feature_engineer.scaler.transform(X_test)
        
        # Train Random Forest
        self.rf_model.fit(X_train_scaled, y_train)
        rf_pred = self.rf_model.predict(X_test_scaled)
        rf_proba = self.rf_model.predict_proba(X_test_scaled)[:, 1]
        
        # Train Gradient Boosting
        self.gb_model.fit(X_train_scaled, y_train)
        gb_pred = self.gb_model.predict(X_test_scaled)
        gb_proba = self.gb_model.predict_proba(X_test_scaled)[:, 1]
        
        # Ensemble predictions (media pesata)
        ensemble_proba = 0.6 * rf_proba + 0.4 * gb_proba
        ensemble_pred = (ensemble_proba > 0.5).astype(int)
        
        # Calcola metriche
        metrics = {
            'rf_accuracy': accuracy_score(y_test, rf_pred),
            'rf_precision': precision_score(y_test, rf_pred, zero_division=0),
            'rf_recall': recall_score(y_test, rf_pred, zero_division=0),
            'rf_f1': f1_score(y_test, rf_pred, zero_division=0),
            
            'gb_accuracy': accuracy_score(y_test, gb_pred),
            'gb_precision': precision_score(y_test, gb_pred, zero_division=0),
            'gb_recall': recall_score(y_test, gb_pred, zero_division=0),
            'gb_f1': f1_score(y_test, gb_pred, zero_division=0),
            
            'ensemble_accuracy': accuracy_score(y_test, ensemble_pred),
            'ensemble_precision': precision_score(y_test, ensemble_pred, zero_division=0),
            'ensemble_recall': recall_score(y_test, ensemble_pred, zero_division=0),
            'ensemble_f1': f1_score(y_test, ensemble_pred, zero_division=0),
            
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_importance': dict(zip(
                self.feature_columns,
                self.rf_model.feature_importances_
            ))
        }
        
        self.is_fitted = True
        
        print(f"✅ Training completato!")
        print(f"   Samples: {metrics['train_samples']} train, {metrics['test_samples']} test")
        print(f"   RF Accuracy: {metrics['rf_accuracy']:.2%}")
        print(f"   GB Accuracy: {metrics['gb_accuracy']:.2%}")
        print(f"   Ensemble Accuracy: {metrics['ensemble_accuracy']:.2%}")
        print(f"   Ensemble Precision: {metrics['ensemble_precision']:.2%}")
        
        return metrics
    
    def predict(self, df: pd.DataFrame) -> Dict:
        """
        Effettua una predizione sull'ultimo dato disponibile
        Returns:
            Dictionary con predizione e confidenza
        """
        if not self.is_fitted:
            return {'error': 'Modello non addestrato'}
        
        features = self.feature_engineer.create_features(df)
        X_latest = features[self.feature_columns].iloc[-1:].dropna(axis=1)
        
        if len(X_latest.columns) < len(self.feature_columns) * 0.8:
            return {'error': 'Feature insufficienti'}
        
        # Allinea le colonne
        X_latest = X_latest.reindex(columns=self.feature_columns, fill_value=0)
        X_latest_scaled = self.feature_engineer.scaler.transform(X_latest)
        
        # Predizioni
        rf_proba = self.rf_model.predict_proba(X_latest_scaled)[0, 1]
        gb_proba = self.gb_model.predict_proba(X_latest_scaled)[0, 1]
        
        # Ensemble
        ensemble_proba = 0.6 * rf_proba + 0.4 * gb_proba
        prediction = int(ensemble_proba > 0.5)
        
        # Feature importance per questa predizione
        top_features = sorted(
            zip(self.feature_columns, self.rf_model.feature_importances_),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'prediction': 'UP' if prediction == 1 else 'DOWN',
            'probability': round(ensemble_proba, 3),
            'confidence': round(max(ensemble_proba, 1 - ensemble_proba) * 100, 1),
            'rf_probability': round(rf_proba, 3),
            'gb_probability': round(gb_proba, 3),
            'top_features': top_features,
            'horizon': self.horizon
        }
    
    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Restituisce le feature più importanti"""
        if not self.is_fitted:
            return []
        
        importance = sorted(
            zip(self.feature_columns, self.rf_model.feature_importances_),
            key=lambda x: x[1],
            reverse=True
        )
        return importance[:top_n]
    
    def _statistical_fallback(self, df: pd.DataFrame) -> Dict:
        """
        Modello statistico avanzato quando i dati sono insufficienti per ML completo
        Usa un ensemble di regole statistiche e pattern recognition
        """
        print("   📊 Attivazione modello statistico avanzato...")
        
        # Calcola momentum su diversi orizzonti
        returns_1d = df['Close'].pct_change(1).dropna()
        returns_5d = df['Close'].pct_change(5).dropna()
        returns_10d = df['Close'].pct_change(10).dropna()
        
        # Trend analysis
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        current_price = df['Close'].iloc[-1]
        
        # Score basato su multiple condizioni
        score = 0
        weights = 0
        
        # Momentum score (30%)
        if len(returns_1d) > 0 and returns_1d.iloc[-1] > 0:
            score += 0.3
        weights += 0.3
        
        # Trend score (40%)
        trend_score = 0
        if current_price > ma20:
            trend_score += 1
        if current_price > ma50:
            trend_score += 1
        if current_price > ma200:
            trend_score += 1
        score += (trend_score / 3) * 0.4
        weights += 0.4
        
        # Mean reversion score (30%)
        z_score = (current_price - ma50) / (df['Close'].rolling(50).std().iloc[-1] + 1e-9)
        if abs(z_score) > 2:
            # Prezzo estremo, probabile reversal
            if z_score > 0:
                score += 0.1  # Probabilità di discesa
            else:
                score += 0.5  # Probabilità di salita
        else:
            score += 0.3  # Neutrale
        weights += 0.3
        
        # Volatility adjustment
        volatility = df['Close'].rolling(20).std().iloc[-1] / current_price
        if volatility > 0.03:
            confidence_multiplier = 0.7  # Alta volatilità riduce confidenza
        else:
            confidence_multiplier = 1.0
        
        # Calcola probabilità finale
        final_probability = min(max(score / weights, 0.1), 0.9)
        prediction = 'UP' if final_probability > 0.5 else 'DOWN'
        confidence = max(final_probability, 1 - final_probability) * confidence_multiplier * 100
        
        print(f"   ✅ Modello statistico: {prediction} (confidenza: {confidence:.1f}%)")
        
        return {
            'prediction': prediction,
            'probability': round(final_probability, 3),
            'confidence': round(confidence, 1),
            'model_type': 'statistical_fallback',
            'z_score': round(z_score, 2),
            'trend_score': trend_score,
            'volatility': round(volatility * 100, 2)
        }


if __name__ == "__main__":
    # Test con dati simulati
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    np.random.seed(42)
    
    # Genera dati sintetici realistici
    close_prices = 100 + np.cumsum(np.random.randn(300) * 2)
    high_prices = close_prices + np.abs(np.random.randn(300))
    low_prices = close_prices - np.abs(np.random.randn(300))
    open_prices = low_prices + np.random.rand(300) * (high_prices - low_prices)
    volumes = np.random.randint(1000000, 10000000, 300)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volumes
    })
    
    # Aggiungi indicatori tecnici base
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # ADX (semplificato)
    df['ADX'] = 25 + np.random.randn(300) * 10
    
    # Training
    predictor = MLPredictor(horizon='1d')
    metrics = predictor.train(df)
    
    # Predizione
    prediction = predictor.predict(df)
    print(f"\n📊 Predizione per domani:")
    print(f"   Direzione: {prediction['prediction']}")
    print(f"   Probabilità: {prediction['probability']:.1%}")
    print(f"   Confidenza: {prediction['confidence']}%")
    
    print(f"\n🔝 Top 5 Feature Importanti:")
    for feature, importance in prediction['top_features']:
        print(f"   {feature}: {importance:.4f}")
