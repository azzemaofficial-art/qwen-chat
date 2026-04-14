"""
Configuration Manager for Trading Advisor Pro v6.0
Centralized configuration management with environment support, validation, and hot-reloading.
"""

import os
import configparser
from pathlib import Path
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeneralConfig:
    app_name: str = "Trading Advisor Pro"
    version: str = "6.0.0"
    environment: str = "production"
    log_level: str = "INFO"
    max_workers: int = 4
    timeout_seconds: int = 30


@dataclass
class DataConfig:
    default_source: str = "yahoo"
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    max_history_days: int = 365
    default_currency: str = "USD"


@dataclass
class TradingConfig:
    default_capital: float = 10000.0
    max_position_size_pct: float = 0.25
    max_portfolio_risk: float = 0.02
    stop_loss_default_pct: float = 0.05
    take_profit_default_pct: float = 0.10
    min_confidence_threshold: float = 0.65


@dataclass
class RiskConfig:
    var_confidence_level: float = 0.95
    cvar_enabled: bool = True
    max_drawdown_limit: float = 0.15
    volatility_window: int = 20
    correlation_threshold: float = 0.7


@dataclass
class MLConfig:
    model_cache_enabled: bool = True
    retrain_frequency_days: int = 7
    feature_importance_threshold: float = 0.01
    cross_validation_folds: int = 5


@dataclass
class DLConfig:
    default_architecture: str = "hybrid_lstm_transformer"
    sequence_length: int = 60
    dropout_rate: float = 0.3
    learning_rate: float = 0.001
    batch_size: int = 32
    early_stopping_patience: int = 10


@dataclass
class QuantumConfig:
    optimization_iterations: int = 1000
    annealing_schedule: str = "linear"
    qubit_simulation: bool = True


@dataclass
class SentimentConfig:
    news_sources: list = field(default_factory=lambda: ["yahoo", "google", "reuters"])
    sentiment_model: str = "transformer"
    language: str = "en"
    min_articles_for_signal: int = 5


@dataclass
class DatabaseConfig:
    type: str = "sqlite"
    path: str = "./data/trading.db"
    backup_enabled: bool = True
    backup_frequency_hours: int = 24


@dataclass
class APIConfig:
    rate_limit_per_minute: int = 60
    retry_attempts: int = 3
    retry_delay_seconds: int = 2


@dataclass
class LoggingConfig:
    console_output: bool = True
    file_output: bool = True
    log_directory: str = "./logs"
    rotation_max_mb: int = 50
    backup_count: int = 10
    include_timestamps: bool = True
    include_caller_info: bool = True


@dataclass
class SecurityConfig:
    encrypt_sensitive_data: bool = True
    api_key_rotation_days: int = 30
    audit_logging_enabled: bool = True


@dataclass
class BacktestConfig:
    default_start_date: str = "2020-01-01"
    default_end_date: str = "2024-12-31"
    transaction_cost_pct: float = 0.001
    slippage_pct: float = 0.0005
    benchmark_symbol: str = "SPY"


@dataclass
class VisualizationConfig:
    chart_format: str = "png"
    dpi: int = 300
    interactive_plots: bool = True
    color_scheme: str = "professional"


class ConfigManager:
    """
    Centralized configuration manager with support for:
    - Multiple environment configurations
    - Configuration validation
    - Hot-reloading
    - Environment variable overrides
    - Type-safe access to configuration values
    """
    
    _instance: Optional['ConfigManager'] = None
    _config_path: Optional[Path] = None
    
    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return
            
        self.config_path = Path(config_path) if config_path else None
        self.config = configparser.ConfigParser()
        self._load_config()
        self._initialized = True
        
        # Initialize all config sections
        self.general = self._parse_general()
        self.data = self._parse_data()
        self.trading = self._parse_trading()
        self.risk = self._parse_risk()
        self.ml = self._parse_ml()
        self.dl = self._parse_dl()
        self.quantum = self._parse_quantum()
        self.sentiment = self._parse_sentiment()
        self.database = self._parse_database()
        self.api = self._parse_api()
        self.logging = self._parse_logging()
        self.security = self._parse_security()
        self.backtest = self._parse_backtest()
        self.visualization = self._parse_visualization()
    
    def _find_config_file(self) -> Path:
        """Search for configuration file in standard locations"""
        search_paths = [
            Path.cwd() / "config" / "settings.ini",
            Path.cwd() / "settings.ini",
            Path.home() / ".trading_advisor" / "settings.ini",
            Path("/etc/trading_advisor/settings.ini"),
        ]
        
        if self.config_path:
            search_paths.insert(0, self.config_path)
        
        for path in search_paths:
            if path.exists():
                logger.info(f"Loaded configuration from: {path}")
                return path
        
        logger.warning("No configuration file found, using defaults")
        return None
    
    def _load_config(self):
        """Load configuration from file"""
        config_file = self._find_config_file()
        if config_file:
            self.config.read(config_file)
    
    def reload(self):
        """Reload configuration from file (hot-reload)"""
        logger.info("Reloading configuration...")
        self.config.clear()
        self._load_config()
        self.__init__(str(self.config_path) if self.config_path else None)
        logger.info("Configuration reloaded successfully")
    
    def _get(self, section: str, option: str, fallback: Any, cast_type: type) -> Any:
        """Get configuration value with type casting and environment override"""
        # Check environment variable override first
        env_var = f"TAP_{section.upper()}_{option.upper()}"
        env_value = os.environ.get(env_var)
        
        if env_value is not None:
            logger.debug(f"Using environment override for {env_var}")
            try:
                if cast_type == bool:
                    return env_value.lower() in ('true', '1', 'yes', 'on')
                return cast_type(env_value)
            except ValueError as e:
                logger.warning(f"Invalid environment variable {env_var}: {e}")
        
        # Fall back to config file
        try:
            if cast_type == bool:
                return self.config.getboolean(section, option, fallback=fallback)
            elif cast_type == int:
                return self.config.getint(section, option, fallback=fallback)
            elif cast_type == float:
                return self.config.getfloat(section, option, fallback=fallback)
            elif cast_type == list:
                value = self.config.get(section, option, fallback=', '.join(fallback))
                return [item.strip() for item in value.split(',')]
            else:
                return self.config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def _parse_general(self) -> GeneralConfig:
        return GeneralConfig(
            app_name=self._get('general', 'app_name', 'Trading Advisor Pro', str),
            version=self._get('general', 'version', '6.0.0', str),
            environment=self._get('general', 'environment', 'production', str),
            log_level=self._get('general', 'log_level', 'INFO', str),
            max_workers=self._get('general', 'max_workers', 4, int),
            timeout_seconds=self._get('general', 'timeout_seconds', 30, int),
        )
    
    def _parse_data(self) -> DataConfig:
        return DataConfig(
            default_source=self._get('data', 'default_source', 'yahoo', str),
            cache_enabled=self._get('data', 'cache_enabled', True, bool),
            cache_ttl_hours=self._get('data', 'cache_ttl_hours', 24, int),
            max_history_days=self._get('data', 'max_history_days', 365, int),
            default_currency=self._get('data', 'default_currency', 'USD', str),
        )
    
    def _parse_trading(self) -> TradingConfig:
        return TradingConfig(
            default_capital=self._get('trading', 'default_capital', 10000.0, float),
            max_position_size_pct=self._get('trading', 'max_position_size_pct', 0.25, float),
            max_portfolio_risk=self._get('trading', 'max_portfolio_risk', 0.02, float),
            stop_loss_default_pct=self._get('trading', 'stop_loss_default_pct', 0.05, float),
            take_profit_default_pct=self._get('trading', 'take_profit_default_pct', 0.10, float),
            min_confidence_threshold=self._get('trading', 'min_confidence_threshold', 0.65, float),
        )
    
    def _parse_risk(self) -> RiskConfig:
        return RiskConfig(
            var_confidence_level=self._get('risk_management', 'var_confidence_level', 0.95, float),
            cvar_enabled=self._get('risk_management', 'cvar_enabled', True, bool),
            max_drawdown_limit=self._get('risk_management', 'max_drawdown_limit', 0.15, float),
            volatility_window=self._get('risk_management', 'volatility_window', 20, int),
            correlation_threshold=self._get('risk_management', 'correlation_threshold', 0.7, float),
        )
    
    def _parse_ml(self) -> MLConfig:
        return MLConfig(
            model_cache_enabled=self._get('machine_learning', 'model_cache_enabled', True, bool),
            retrain_frequency_days=self._get('machine_learning', 'retrain_frequency_days', 7, int),
            feature_importance_threshold=self._get('machine_learning', 'feature_importance_threshold', 0.01, float),
            cross_validation_folds=self._get('machine_learning', 'cross_validation_folds', 5, int),
        )
    
    def _parse_dl(self) -> DLConfig:
        return DLConfig(
            default_architecture=self._get('deep_learning', 'default_architecture', 'hybrid_lstm_transformer', str),
            sequence_length=self._get('deep_learning', 'sequence_length', 60, int),
            dropout_rate=self._get('deep_learning', 'dropout_rate', 0.3, float),
            learning_rate=self._get('deep_learning', 'learning_rate', 0.001, float),
            batch_size=self._get('deep_learning', 'batch_size', 32, int),
            early_stopping_patience=self._get('deep_learning', 'early_stopping_patience', 10, int),
        )
    
    def _parse_quantum(self) -> QuantumConfig:
        return QuantumConfig(
            optimization_iterations=self._get('quantum', 'optimization_iterations', 1000, int),
            annealing_schedule=self._get('quantum', 'annealing_schedule', 'linear', str),
            qubit_simulation=self._get('quantum', 'qubit_simulation', True, bool),
        )
    
    def _parse_sentiment(self) -> SentimentConfig:
        return SentimentConfig(
            news_sources=self._get('sentiment', 'news_sources', ['yahoo', 'google', 'reuters'], list),
            sentiment_model=self._get('sentiment', 'sentiment_model', 'transformer', str),
            language=self._get('sentiment', 'language', 'en', str),
            min_articles_for_signal=self._get('sentiment', 'min_articles_for_signal', 5, int),
        )
    
    def _parse_database(self) -> DatabaseConfig:
        return DatabaseConfig(
            type=self._get('database', 'type', 'sqlite', str),
            path=self._get('database', 'path', './data/trading.db', str),
            backup_enabled=self._get('database', 'backup_enabled', True, bool),
            backup_frequency_hours=self._get('database', 'backup_frequency_hours', 24, int),
        )
    
    def _parse_api(self) -> APIConfig:
        return APIConfig(
            rate_limit_per_minute=self._get('api', 'rate_limit_per_minute', 60, int),
            retry_attempts=self._get('api', 'retry_attempts', 3, int),
            retry_delay_seconds=self._get('api', 'retry_delay_seconds', 2, int),
        )
    
    def _parse_logging(self) -> LoggingConfig:
        return LoggingConfig(
            console_output=self._get('logging', 'console_output', True, bool),
            file_output=self._get('logging', 'file_output', True, bool),
            log_directory=self._get('logging', 'log_directory', './logs', str),
            rotation_max_mb=self._get('logging', 'rotation_max_mb', 50, int),
            backup_count=self._get('logging', 'backup_count', 10, int),
            include_timestamps=self._get('logging', 'include_timestamps', True, bool),
            include_caller_info=self._get('logging', 'include_caller_info', True, bool),
        )
    
    def _parse_security(self) -> SecurityConfig:
        return SecurityConfig(
            encrypt_sensitive_data=self._get('security', 'encrypt_sensitive_data', True, bool),
            api_key_rotation_days=self._get('security', 'api_key_rotation_days', 30, int),
            audit_logging_enabled=self._get('security', 'audit_logging_enabled', True, bool),
        )
    
    def _parse_backtest(self) -> BacktestConfig:
        return BacktestConfig(
            default_start_date=self._get('backtesting', 'default_start_date', '2020-01-01', str),
            default_end_date=self._get('backtesting', 'default_end_date', '2024-12-31', str),
            transaction_cost_pct=self._get('backtesting', 'transaction_cost_pct', 0.001, float),
            slippage_pct=self._get('backtesting', 'slippage_pct', 0.0005, float),
            benchmark_symbol=self._get('backtesting', 'benchmark_symbol', 'SPY', str),
        )
    
    def _parse_visualization(self) -> VisualizationConfig:
        return VisualizationConfig(
            chart_format=self._get('visualization', 'chart_format', 'png', str),
            dpi=self._get('visualization', 'dpi', 300, int),
            interactive_plots=self._get('visualization', 'interactive_plots', True, bool),
            color_scheme=self._get('visualization', 'color_scheme', 'professional', str),
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate trading constraints
        if not 0 < self.trading.max_position_size_pct <= 1:
            errors.append("max_position_size_pct must be between 0 and 1")
        
        if not 0 < self.trading.max_portfolio_risk <= 1:
            errors.append("max_portfolio_risk must be between 0 and 1")
        
        # Validate risk parameters
        if not 0.5 <= self.risk.var_confidence_level <= 1:
            errors.append("var_confidence_level must be between 0.5 and 1")
        
        # Validate ML/DL parameters
        if not 0 <= self.dl.dropout_rate <= 1:
            errors.append("dropout_rate must be between 0 and 1")
        
        if self.dl.learning_rate <= 0:
            errors.append("learning_rate must be positive")
        
        if self.dl.batch_size <= 0:
            errors.append("batch_size must be positive")
        
        # Validate backtesting
        if self.backtest.transaction_cost_pct < 0:
            errors.append("transaction_cost_pct cannot be negative")
        
        if self.backtest.slippage_pct < 0:
            errors.append("slippage_pct cannot be negative")
        
        if errors:
            logger.error(f"Configuration validation failed with {len(errors)} errors")
            for error in errors:
                logger.error(f"  - {error}")
        else:
            logger.info("Configuration validation passed")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return {
            'general': self.general.__dict__,
            'data': self.data.__dict__,
            'trading': self.trading.__dict__,
            'risk': self.risk.__dict__,
            'ml': self.ml.__dict__,
            'dl': self.dl.__dict__,
            'quantum': self.quantum.__dict__,
            'sentiment': self.sentiment.__dict__,
            'database': self.database.__dict__,
            'api': self.api.__dict__,
            'logging': self.logging.__dict__,
            'security': self.security.__dict__,
            'backtest': self.backtest.__dict__,
            'visualization': self.visualization.__dict__,
        }
    
    def __repr__(self) -> str:
        return f"ConfigManager(environment={self.general.environment}, version={self.general.version})"


# Global configuration instance
config = ConfigManager()


def get_config() -> ConfigManager:
    """Get global configuration instance"""
    return config


if __name__ == "__main__":
    # Test configuration loading
    cfg = ConfigManager()
    print(f"Configuration loaded: {cfg}")
    print(f"Validation errors: {cfg.validate()}")
    print(f"\nGeneral settings: {cfg.general}")
    print(f"Trading settings: {cfg.trading}")
