"""
Deep Learning Neural Network Suite for Financial Time Series
=============================================================
Implementa LSTM, GRU, Transformer e CNN-LSTM ibridi per previsione finanziaria
con attenzione multi-head, meccanismi di attention e ensemble stacking
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Model, Sequential
    from tensorflow.keras.layers import (
        Dense, LSTM, GRU, Dropout, BatchNormalization,
        Conv1D, MaxPooling1D, Flatten, Input, Concatenate,
        MultiHeadAttention, LayerNormalization, GlobalAveragePooling1D,
        Attention, Add, Activation
    )
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    Model = type('Model', (), {})  # Dummy per type hinting
    print("⚠️ TensorFlow non disponibile, uso fallback scikit-learn")


@dataclass
class DLArchitecture:
    """Configurazione architettura deep learning"""
    model_type: str  # 'lstm', 'gru', 'transformer', 'cnn_lstm', 'hybrid'
    sequence_length: int = 60
    n_layers: int = 3
    hidden_units: int = 128
    dropout_rate: float = 0.3
    attention_heads: int = 8
    use_batch_norm: bool = True
    use_residual_connections: bool = True


class TimeSeriesFeatureExtractor:
    """Estrae feature avanzate per deep learning"""
    
    def __init__(self, sequence_length: int = 60):
        self.sequence_length = sequence_length
        self.feature_columns = []
        
    def create_multimodal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crea feature multimodali per il modello"""
        features = df.copy()
        
        # Feature tecniche avanzate
        features['returns_1d'] = df['Close'].pct_change(1)
        features['returns_5d'] = df['Close'].pct_change(5)
        features['volatility_rolling'] = df['Close'].rolling(20).std()
        features['volume_price_trend'] = (df['Volume'] * df['returns_1d']).rolling(20).sum()
        
        # Medie mobili multiple
        for period in [5, 10, 20, 50, 200]:
            features[f'sma_{period}'] = df['Close'].rolling(period).mean()
            features[f'ema_{period}'] = df['Close'].ewm(span=period).mean()
        
        # Bandee di Bollinger
        sma_20 = features['sma_20']
        std_20 = df['Close'].rolling(20).std()
        features['bb_upper'] = sma_20 + 2 * std_20
        features['bb_lower'] = sma_20 - 2 * std_20
        features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / sma_20
        features['bb_position'] = (df['Close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'] + 1e-9)
        
        # RSI e MACD
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta).where(delta < 0, 0).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        features['rsi'] = 100 - (100 / (1 + rs))
        
        exp12 = df['Close'].ewm(span=12).mean()
        exp26 = df['Close'].ewm(span=26).mean()
        features['macd'] = exp12 - exp26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        # Feature cicliche (per catturare stagionalità)
        if isinstance(df.index, pd.DatetimeIndex):
            features['day_sin'] = np.sin(2 * np.pi * df.index.dayofweek / 7)
            features['day_cos'] = np.cos(2 * np.pi * df.index.dayofweek / 7)
            features['month_sin'] = np.sin(2 * np.pi * df.index.month / 12)
            features['month_cos'] = np.cos(2 * np.pi * df.index.month / 12)
        else:
            features['day_sin'] = np.sin(2 * np.pi * np.arange(len(df)) / 7)
            features['day_cos'] = np.cos(2 * np.pi * np.arange(len(df)) / 7)
            features['month_sin'] = np.sin(2 * np.pi * np.arange(len(df)) / 12)
            features['month_cos'] = np.cos(2 * np.pi * np.arange(len(df)) / 12)
        
        # Lag features
        for lag in [1, 2, 3, 5, 10]:
            features[f'returns_lag_{lag}'] = features['returns_1d'].shift(lag)
            features[f'volume_lag_{lag}'] = features['Volume'].pct_change().shift(lag)
        
        # Target variable
        features['target_next'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        features['target_return'] = df['Close'].shift(-1) / df['Close'] - 1
        
        return features
    
    def get_feature_columns(self) -> List[str]:
        """Restituisce lista colonne feature"""
        return [
            'returns_1d', 'returns_5d', 'volatility_rolling', 'volume_price_trend',
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_200',
            'bb_upper', 'bb_lower', 'bb_width', 'bb_position',
            'rsi', 'macd', 'macd_signal', 'macd_hist',
            'day_sin', 'day_cos', 'month_sin', 'month_cos',
            'returns_lag_1', 'returns_lag_2', 'returns_lag_3', 'returns_lag_5', 'returns_lag_10',
            'volume_lag_1', 'volume_lag_2', 'volume_lag_3', 'volume_lag_5', 'volume_lag_10'
        ]
    
    def create_sequences(
        self,
        data: np.ndarray,
        targets: np.ndarray,
        sequence_length: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Crea sequenze per training"""
        X, y = [], []
        
        for i in range(len(data) - sequence_length):
            X.append(data[i:i+sequence_length])
            y.append(targets[i+sequence_length])
        
        return np.array(X), np.array(y)


class DeepLearningPredictor:
    """Predittore basato su deep learning con multiple architetture"""
    
    def __init__(
        self,
        architecture: DLArchitecture = None,
        horizon: str = '1d'
    ):
        self.architecture = architecture or DLArchitecture(model_type='lstm')
        self.horizon = horizon
        self.model = None
        self.feature_extractor = TimeSeriesFeatureExtractor(
            self.architecture.sequence_length
        )
        self.is_fitted = False
        self.training_history = None
        
    def _build_lstm_model(self, input_shape: Tuple, n_classes: int = 2) -> Model:
        """Costruisce modello LSTM con attention"""
        inputs = Input(shape=input_shape)
        
        x = LSTM(
            self.architecture.hidden_units,
            return_sequences=True,
            recurrent_dropout=0.2
        )(inputs)
        x = BatchNormalization()(x) if self.architecture.use_batch_norm else x
        x = Dropout(self.architecture.dropout_rate)(x)
        
        x = LSTM(
            self.architecture.hidden_units // 2,
            return_sequences=True
        )(x)
        x = BatchNormalization()(x) if self.architecture.use_batch_norm else x
        x = Dropout(self.architecture.dropout_rate)(x)
        
        # Attention mechanism
        attention = Attention()([x, x])
        x = Add()([x, attention])
        x = LayerNormalization()(x)
        
        x = GlobalAveragePooling1D()(x)
        x = Dense(self.architecture.hidden_units // 4, activation='relu')(x)
        x = Dropout(self.architecture.dropout_rate)(x)
        
        outputs = Dense(n_classes, activation='softmax')(x)
        
        model = Model(inputs, outputs)
        return model
    
    def _build_gru_model(self, input_shape: Tuple, n_classes: int = 2) -> Model:
        """Costruisce modello GRU con residual connections"""
        inputs = Input(shape=input_shape)
        
        x = GRU(
            self.architecture.hidden_units,
            return_sequences=True
        )(inputs)
        x = BatchNormalization()(x) if self.architecture.use_batch_norm else x
        
        # Residual block
        residual = x
        x = GRU(
            self.architecture.hidden_units // 2,
            return_sequences=True
        )(x)
        x = GRU(
            self.architecture.hidden_units // 2,
            return_sequences=False
        )(x)
        
        if self.architecture.use_residual_connections:
            x = Concatenate()([x, GlobalAveragePooling1D()(residual)])
        
        x = Dropout(self.architecture.dropout_rate)(x)
        x = Dense(self.architecture.hidden_units // 4, activation='relu')(x)
        outputs = Dense(n_classes, activation='softmax')(x)
        
        model = Model(inputs, outputs)
        return model
    
    def _build_transformer_model(self, input_shape: Tuple, n_classes: int = 2) -> Model:
        """Costruisce modello Transformer encoder"""
        inputs = Input(shape=input_shape)
        
        # Embedding layer
        x = Dense(self.architecture.hidden_units)(inputs)
        
        # Multi-head attention layers
        for _ in range(self.architecture.n_layers):
            attention_output = MultiHeadAttention(
                num_heads=self.architecture.attention_heads,
                key_dim=self.architecture.hidden_units // self.architecture.attention_heads
            )(x, x)
            
            x = Add()([x, attention_output])
            x = LayerNormalization()(x)
            
            # Feed-forward network
            ffn_output = Dense(self.architecture.hidden_units * 4, activation='relu')(x)
            ffn_output = Dense(self.architecture.hidden_units)(ffn_output)
            
            x = Add()([x, ffn_output])
            x = LayerNormalization()(x)
        
        # Global pooling
        x = GlobalAveragePooling1D()(x)
        x = Dropout(self.architecture.dropout_rate)(x)
        x = Dense(self.architecture.hidden_units // 4, activation='relu')(x)
        outputs = Dense(n_classes, activation='softmax')(x)
        
        model = Model(inputs, outputs)
        return model
    
    def _build_cnn_lstm_model(self, input_shape: Tuple, n_classes: int = 2) -> Model:
        """Costruisce modello ibrido CNN-LSTM"""
        inputs = Input(shape=input_shape)
        
        # CNN layers per feature extraction
        x = Conv1D(
            filters=64,
            kernel_size=3,
            activation='relu',
            padding='same'
        )(inputs)
        x = BatchNormalization()(x) if self.architecture.use_batch_norm else x
        x = MaxPooling1D(pool_size=2)(x)
        x = Dropout(self.architecture.dropout_rate)(x)
        
        x = Conv1D(
            filters=128,
            kernel_size=3,
            activation='relu',
            padding='same'
        )(x)
        x = BatchNormalization()(x) if self.architecture.use_batch_norm else x
        x = MaxPooling1D(pool_size=2)(x)
        x = Dropout(self.architecture.dropout_rate)(x)
        
        # LSTM layers
        x = LSTM(self.architecture.hidden_units, return_sequences=False)(x)
        x = Dropout(self.architecture.dropout_rate)(x)
        
        x = Dense(self.architecture.hidden_units // 2, activation='relu')(x)
        x = Dropout(self.architecture.dropout_rate)(x)
        
        outputs = Dense(n_classes, activation='softmax')(x)
        
        model = Model(inputs, outputs)
        return model
    
    def _build_hybrid_ensemble_model(self, input_shape: Tuple, n_classes: int = 2) -> Model:
        """Costruisce modello ensemble ibrido che combina tutte le architetture"""
        inputs = Input(shape=input_shape)
        
        # LSTM branch
        lstm_x = LSTM(64, return_sequences=False)(inputs)
        lstm_x = Dropout(0.3)(lstm_x)
        
        # GRU branch
        gru_x = GRU(64, return_sequences=False)(inputs)
        gru_x = Dropout(0.3)(gru_x)
        
        # CNN branch
        cnn_x = Conv1D(64, 3, activation='relu', padding='same')(inputs)
        cnn_x = GlobalAveragePooling1D()(cnn_x)
        cnn_x = Dropout(0.3)(cnn_x)
        
        # Concatenate all branches
        combined = Concatenate()([lstm_x, gru_x, cnn_x])
        combined = Dense(128, activation='relu')(combined)
        combined = Dropout(0.3)(combined)
        combined = Dense(64, activation='relu')(combined)
        combined = Dropout(0.3)(combined)
        
        outputs = Dense(n_classes, activation='softmax')(combined)
        
        model = Model(inputs, outputs)
        return model
    
    def build_model(self, input_shape: Tuple, n_classes: int = 2) -> Model:
        """Costruisce il modello basato sull'architettura specificata"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow required for deep learning models")
        
        model_map = {
            'lstm': self._build_lstm_model,
            'gru': self._build_gru_model,
            'transformer': self._build_transformer_model,
            'cnn_lstm': self._build_cnn_lstm_model,
            'hybrid': self._build_hybrid_ensemble_model
        }
        
        builder = model_map.get(self.architecture.model_type, self._build_lstm_model)
        model = builder(input_shape, n_classes)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy', 'Precision', 'Recall']
        )
        
        return model
    
    def train(
        self,
        df: pd.DataFrame,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> Dict:
        """Addestra il modello deep learning"""
        if not TENSORFLOW_AVAILABLE:
            return self._sklearn_fallback(df)
        
        print(f"\n🧠 Training Deep Learning ({self.architecture.model_type.upper()})...")
        
        # Estrai feature
        features = self.feature_extractor.create_multimodal_features(df)
        feature_cols = self.feature_extractor.get_feature_columns()
        
        # Prepara dati
        features = features.dropna(subset=feature_cols + ['target_next'])
        
        X_raw = features[feature_cols].values
        y = features['target_next'].values
        
        # Crea sequenze
        X, y = self.feature_extractor.create_sequences(
            X_raw, y, self.architecture.sequence_length
        )
        
        # Normalizza
        mean = X.reshape(-1, X.shape[-1]).mean(axis=0)
        std = X.reshape(-1, X.shape[-1]).std(axis=0) + 1e-9
        X = (X - mean) / std
        
        print(f"   Dataset: {X.shape[0]} sequenze, {X.shape[1]} timestep, {X.shape[2]} feature")
        
        # Split train/validation
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Costruisci modello
        input_shape = (X_train.shape[1], X_train.shape[2])
        self.model = self.build_model(input_shape)
        
        print(f"   Parametri modello: {self.model.count_params():,}")
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6,
                verbose=1
            )
        ]
        
        # Training
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.training_history = history.history
        self.is_fitted = True
        
        # Metriche finali
        train_metrics = self.model.evaluate(X_train, y_train, verbose=0)
        val_metrics = self.model.evaluate(X_val, y_val, verbose=0)
        
        results = {
            'train_accuracy': train_metrics[1],
            'val_accuracy': val_metrics[1],
            'train_loss': train_metrics[0],
            'val_loss': val_metrics[0],
            'history': history.history,
            'epochs_trained': len(history.history['loss'])
        }
        
        print(f"\n✅ Training completato!")
        print(f"   Accuracy Train: {results['train_accuracy']:.2%}")
        print(f"   Accuracy Val: {results['val_accuracy']:.2%}")
        print(f"   Epochs: {results['epochs_trained']}")
        
        return results
    
    def predict(self, df: pd.DataFrame) -> Dict:
        """Effettua predizione"""
        if not self.is_fitted:
            return {'error': 'Modello non addestrato'}
        
        if not TENSORFLOW_AVAILABLE:
            return self._sklearn_predict_fallback(df)
        
        features = self.feature_extractor.create_multimodal_features(df)
        feature_cols = self.feature_extractor.get_feature_columns()
        
        features = features.dropna(subset=feature_cols)
        X_raw = features[feature_cols].values
        
        # Crea ultima sequenza
        X_latest = X_raw[-self.architecture.sequence_length:].reshape(1, self.architecture.sequence_length, -1)
        
        # Normalizza
        mean = X_latest.reshape(-1, X_latest.shape[-1]).mean(axis=0)
        std = X_latest.reshape(-1, X_latest.shape[-1]).std(axis=0) + 1e-9
        X_latest = (X_latest - mean) / std
        
        # Predizione
        prediction_proba = self.model.predict(X_latest, verbose=0)[0]
        prediction = int(np.argmax(prediction_proba))
        confidence = prediction_proba[prediction]
        
        return {
            'prediction': 'UP' if prediction == 1 else 'DOWN',
            'probability': float(prediction_proba[1]),
            'confidence': float(confidence * 100),
            'model_type': self.architecture.model_type,
            'horizon': self.horizon
        }
    
    def _sklearn_fallback(self, df: pd.DataFrame) -> Dict:
        """Fallback a modello sklearn se TensorFlow non disponibile"""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        
        print("   📊 Fallback a Random Forest (TensorFlow non disponibile)")
        
        features = self.feature_extractor.create_multimodal_features(df)
        feature_cols = self.feature_extractor.get_feature_columns()
        
        features = features.dropna(subset=feature_cols + ['target_next'])
        
        X = features[feature_cols].values
        y = features['target_next'].values
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_scaled, y)
        
        self.model = model
        self.scaler = scaler
        self.is_fitted = True
        
        train_pred = model.predict(X_scaled)
        accuracy = (train_pred == y).mean()
        
        return {
            'train_accuracy': accuracy,
            'model_type': 'random_forest_fallback',
            'epochs_trained': 1
        }
    
    def _sklearn_predict_fallback(self, df: pd.DataFrame) -> Dict:
        """Predizione con fallback sklearn"""
        features = self.feature_extractor.create_multimodal_features(df)
        feature_cols = self.feature_extractor.get_feature_columns()
        
        features = features.dropna(subset=feature_cols)
        X_latest = features[feature_cols].values[-1:].reshape(1, -1)
        
        X_scaled = self.scaler.transform(X_latest)
        prediction_proba = self.model.predict_proba(X_latest)[0]
        prediction = int(np.argmax(prediction_proba))
        
        return {
            'prediction': 'UP' if prediction == 1 else 'DOWN',
            'probability': float(prediction_proba[1]),
            'confidence': float(max(prediction_proba) * 100),
            'model_type': 'random_forest_fallback',
            'horizon': self.horizon
        }


if __name__ == "__main__":
    # Test del modello deep learning
    np.random.seed(42)
    
    # Genera dati sintetici
    dates = pd.date_range('2022-01-01', periods=500, freq='D')
    close_prices = 100 + np.cumsum(np.random.randn(500) * 2)
    high_prices = close_prices + np.abs(np.random.randn(500))
    low_prices = close_prices - np.abs(np.random.randn(500))
    open_prices = low_prices + np.random.rand(500) * (high_prices - low_prices)
    volumes = np.random.randint(1000000, 10000000, 500)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volumes
    })
    df.set_index('Date', inplace=True)
    
    # Test con diverse architetture
    architectures = ['lstm', 'gru', 'cnn_lstm', 'hybrid']
    
    for arch_type in architectures:
        print(f"\n{'='*70}")
        print(f"Testing {arch_type.upper()} Architecture")
        print(f"{'='*70}")
        
        arch = DLArchitecture(
            model_type=arch_type,
            sequence_length=30,
            hidden_units=64,
            n_layers=2,
            dropout_rate=0.3
        )
        
        predictor = DeepLearningPredictor(architecture=arch)
        metrics = predictor.train(df, epochs=10, batch_size=32)
        
        if 'error' not in metrics:
            prediction = predictor.predict(df)
            print(f"\n📊 Predizione:")
            print(f"   Direzione: {prediction['prediction']}")
            print(f"   Probabilità: {prediction['probability']:.1%}")
            print(f"   Confidenza: {prediction['confidence']:.1f}%")
