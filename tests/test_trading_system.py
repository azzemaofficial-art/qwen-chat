"""
Comprehensive Test Suite for Trading Advisor Pro v6.0
Covers: Unit tests, Integration tests, Performance tests
Uses: pytest, unittest, pytest-cov for coverage reporting
"""

import pytest
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


# ============================================================================
# Configuration Manager Tests
# ============================================================================

class TestConfigManager(unittest.TestCase):
    """Test suite for configuration management"""
    
    def setUp(self):
        from src.config_manager import ConfigManager
        self.config = ConfigManager()
    
    def test_config_singleton(self):
        """Test that ConfigManager is a singleton"""
        from src.config_manager import ConfigManager
        config1 = ConfigManager()
        config2 = ConfigManager()
        self.assertIs(config1, config2)
    
    def test_default_values(self):
        """Test default configuration values"""
        self.assertEqual(self.config.general.app_name, "Trading Advisor Pro")
        self.assertEqual(self.config.trading.default_capital, 10000.0)
        self.assertGreater(self.config.risk.var_confidence_level, 0.5)
    
    def test_validation_passes(self):
        """Test that default config passes validation"""
        errors = self.config.validate()
        self.assertEqual(len(errors), 0)
    
    def test_trading_constraints(self):
        """Test trading parameter constraints"""
        self.assertGreater(self.config.trading.max_position_size_pct, 0)
        self.assertLessEqual(self.config.trading.max_position_size_pct, 1)
        self.assertGreater(self.config.trading.min_confidence_threshold, 0)
        self.assertLessEqual(self.config.trading.min_confidence_threshold, 1)


# ============================================================================
# Technical Analysis Tests
# ============================================================================

class TestTechnicalAnalysis(unittest.TestCase):
    """Test suite for technical analysis functions"""
    
    def setUp(self):
        # Create sample price data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 2)
        self.prices = pd.Series(prices, index=dates)
    
    def test_sma_calculation(self):
        """Test Simple Moving Average calculation"""
        from src.technical_analysis import TechnicalAnalyzer
        
        analyzer = TechnicalAnalyzer()
        sma = analyzer.calculate_sma(self.prices, window=10)
        
        self.assertEqual(len(sma), len(self.prices))
        self.assertTrue(pd.isna(sma.iloc[:9]).all())
        self.assertFalse(pd.isna(sma.iloc[9:]).any())
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        from src.technical_analysis import TechnicalAnalyzer
        
        analyzer = TechnicalAnalyzer()
        rsi = analyzer.calculate_rsi(self.prices, window=14)
        
        self.assertEqual(len(rsi), len(self.prices))
        self.assertTrue((rsi >= 0).all())
        self.assertTrue((rsi <= 100).all())
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        from src.technical_analysis import TechnicalAnalyzer
        
        analyzer = TechnicalAnalyzer()
        macd_data = analyzer.calculate_macd(self.prices)
        
        self.assertIn('macd_line', macd_data)
        self.assertIn('signal_line', macd_data)
        self.assertIn('histogram', macd_data)
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        from src.technical_analysis import TechnicalAnalyzer
        
        analyzer = TechnicalAnalyzer()
        bb = analyzer.calculate_bollinger_bands(self.prices, window=20)
        
        self.assertIn('upper', bb)
        self.assertIn('middle', bb)
        self.assertIn('lower', bb)
        
        # Upper band should be above middle, middle above lower
        self.assertTrue((bb['upper'] >= bb['middle']).all())
        self.assertTrue((bb['middle'] >= bb['lower']).all())


# ============================================================================
# Risk Management Tests
# ============================================================================

class TestRiskManagement(unittest.TestCase):
    """Test suite for risk management calculations"""
    
    def setUp(self):
        np.random.seed(42)
        self.returns = pd.Series(np.random.randn(252) * 0.02)
        self.positions = [
            {'symbol': 'AAPL', 'value': 10000, 'volatility': 0.2},
            {'symbol': 'GOOGL', 'value': 15000, 'volatility': 0.25},
            {'symbol': 'MSFT', 'value': 8000, 'volatility': 0.18},
        ]
    
    def test_var_calculation(self):
        """Test Value at Risk calculation"""
        from src.risk_management import AdvancedRiskManager
        
        risk_manager = AdvancedRiskManager()
        var_95 = risk_manager.calculate_var(self.returns, confidence_level=0.95)
        var_99 = risk_manager.calculate_var(self.returns, confidence_level=0.99)
        
        # VaR should be positive (representing loss)
        self.assertGreater(var_95, 0)
        self.assertGreater(var_99, 0)
        
        # 99% VaR should be greater than 95% VaR
        self.assertGreater(var_99, var_95)
    
    def test_cvar_calculation(self):
        """Test Conditional VaR calculation"""
        from src.risk_management import AdvancedRiskManager
        
        risk_manager = AdvancedRiskManager()
        cvar = risk_manager.calculate_cvar(self.returns, confidence_level=0.95)
        var = risk_manager.calculate_var(self.returns, confidence_level=0.95)
        
        # CVaR should be greater than VaR
        self.assertGreater(cvar, var)
    
    def test_portfolio_correlation(self):
        """Test portfolio correlation matrix"""
        from src.risk_management import AdvancedRiskManager
        
        risk_manager = AdvancedRiskManager()
        
        # Create correlated returns
        np.random.seed(42)
        n_assets = 3
        n_days = 252
        base_returns = np.random.randn(n_days)
        
        returns_data = {}
        for i in range(n_assets):
            noise = np.random.randn(n_days) * 0.5
            returns_data[f'asset_{i}'] = pd.Series(base_returns * 0.7 + noise * 0.3)
        
        returns_df = pd.DataFrame(returns_data)
        corr_matrix = risk_manager.calculate_correlation_matrix(returns_df)
        
        self.assertEqual(corr_matrix.shape, (n_assets, n_assets))
        # Diagonal should be 1
        for i in range(n_assets):
            self.assertAlmostEqual(corr_matrix.iloc[i, i], 1.0, places=5)


# ============================================================================
# Machine Learning Predictor Tests
# ============================================================================

class TestMLPredictor(unittest.TestCase):
    """Test suite for ML prediction models"""
    
    def setUp(self):
        np.random.seed(42)
        n_samples = 1000
        
        # Create synthetic features and target
        self.features = pd.DataFrame({
            'feature_1': np.random.randn(n_samples),
            'feature_2': np.random.randn(n_samples),
            'feature_3': np.random.randn(n_samples),
            'lag_1': np.random.randn(n_samples),
            'lag_2': np.random.randn(n_samples),
        })
        
        # Target with some signal
        self.target = pd.Series(
            0.5 * self.features['feature_1'] + 
            0.3 * self.features['feature_2'] + 
            np.random.randn(n_samples) * 0.1
        )
    
    def test_model_training(self):
        """Test model training process"""
        from src.ml_predictor import MLPredictor
        
        predictor = MLPredictor()
        predictor.train(self.features, self.target)
        
        # Model should be trained
        self.assertIsNotNone(predictor.model)
    
    def test_prediction(self):
        """Test prediction functionality"""
        from src.ml_predictor import MLPredictor
        
        predictor = MLPredictor()
        predictor.train(self.features, self.target)
        
        # Make predictions on subset
        test_features = self.features.iloc[-10:]
        predictions = predictor.predict(test_features)
        
        self.assertEqual(len(predictions), 10)
        self.assertIsInstance(predictions, np.ndarray)
    
    def test_feature_importance(self):
        """Test feature importance calculation"""
        from src.ml_predictor import MLPredictor
        
        predictor = MLPredictor()
        predictor.train(self.features, self.target)
        
        importance = predictor.get_feature_importance()
        
        self.assertIsNotNone(importance)
        self.assertEqual(len(importance), len(self.features.columns))


# ============================================================================
# Backtesting Tests
# ============================================================================

class TestBacktesting(unittest.TestCase):
    """Test suite for backtesting engine"""
    
    def setUp(self):
        # Create sample price data
        dates = pd.date_range(start='2023-01-01', periods=252, freq='B')
        np.random.seed(42)
        
        # Generate realistic price series
        returns = np.random.randn(252) * 0.02 + 0.0005
        prices = 100 * np.cumprod(1 + returns)
        
        self.prices = pd.Series(prices, index=dates)
        self.signals = pd.Series(
            np.random.choice([-1, 0, 1], size=252),
            index=dates
        )
    
    def test_backtest_execution(self):
        """Test backtest execution"""
        from src.backtesting import AdvancedBacktester
        
        backtester = AdvancedBacktester(
            initial_capital=10000,
            transaction_cost=0.001,
            slippage=0.0005
        )
        
        results = backtester.run(self.prices, self.signals)
        
        self.assertIn('final_value', results)
        self.assertIn('total_return', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('max_drawdown', results)
    
    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        from src.backtesting import AdvancedBacktester
        
        backtester = AdvancedBacktester(initial_capital=10000)
        results = backtester.run(self.prices, self.signals)
        
        # Check metrics are reasonable
        self.assertIsInstance(results['total_return'], float)
        self.assertIsInstance(results['sharpe_ratio'], float)
        self.assertIsInstance(results['max_drawdown'], float)
        
        # Max drawdown should be between 0 and 1
        self.assertGreaterEqual(results['max_drawdown'], 0)
        self.assertLessEqual(results['max_drawdown'], 1)


# ============================================================================
# Portfolio Optimizer Tests
# ============================================================================

class TestPortfolioOptimizer(unittest.TestCase):
    """Test suite for portfolio optimization"""
    
    def setUp(self):
        np.random.seed(42)
        n_assets = 5
        n_periods = 252
        
        # Generate correlated returns
        base = np.random.randn(n_periods)
        returns_data = {}
        for i in range(n_assets):
            noise = np.random.randn(n_periods) * 0.5
            returns_data[f'asset_{i}'] = pd.Series(base * 0.6 + noise * 0.4)
        
        self.returns = pd.DataFrame(returns_data)
    
    def test_mean_variance_optimization(self):
        """Test mean-variance optimization"""
        from src.portfolio_optimizer import PortfolioOptimizer
        
        optimizer = PortfolioOptimizer()
        weights = optimizer.optimize_mean_variance(self.returns)
        
        self.assertEqual(len(weights), len(self.returns.columns))
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=5)
        self.assertTrue(all(w >= 0 for w in weights.values()))
    
    def test_risk_parity_optimization(self):
        """Test risk parity optimization"""
        from src.portfolio_optimizer import PortfolioOptimizer
        
        optimizer = PortfolioOptimizer()
        weights = optimizer.optimize_risk_parity(self.returns)
        
        self.assertEqual(len(weights), len(self.returns.columns))
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=5)


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration(unittest.TestCase):
    """Integration tests for full workflow"""
    
    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline"""
        from src.data_fetcher import DataFetcher
        from src.technical_analysis import TechnicalAnalyzer
        from src.risk_management import AdvancedRiskManager
        from src.ml_predictor import MLPredictor
        
        # Generate synthetic data
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        prices = pd.Series(
            100 + np.cumsum(np.random.randn(200) * 2),
            index=dates
        )
        
        # Technical analysis
        tech_analyzer = TechnicalAnalyzer()
        sma = tech_analyzer.calculate_sma(prices, window=20)
        rsi = tech_analyzer.calculate_rsi(prices, window=14)
        
        self.assertFalse(pd.isna(sma.iloc[-1]))
        self.assertFalse(pd.isna(rsi.iloc[-1]))
        
        # Risk analysis
        returns = prices.pct_change().dropna()
        risk_manager = AdvancedRiskManager()
        var = risk_manager.calculate_var(returns, confidence_level=0.95)
        
        self.assertGreater(var, 0)
        
        # ML prediction
        features = pd.DataFrame({
            'returns': returns,
            'lag_1': returns.shift(1),
            'lag_2': returns.shift(2),
        }).dropna()
        
        target = returns.shift(-1).dropna()
        features = features.loc[target.index]
        
        ml_predictor = MLPredictor()
        ml_predictor.train(features, target)
        prediction = ml_predictor.predict(features.iloc[-1:])
        
        self.assertEqual(len(prediction), 1)


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.performance
class TestPerformance(unittest.TestCase):
    """Performance benchmarks"""
    
    def test_large_dataset_processing(self):
        """Test processing of large datasets"""
        from src.technical_analysis import TechnicalAnalyzer
        
        # Create large dataset
        np.random.seed(42)
        n_points = 100000
        dates = pd.date_range(start='2000-01-01', periods=n_points, freq='D')
        prices = pd.Series(
            100 + np.cumsum(np.random.randn(n_points) * 2),
            index=dates
        )
        
        analyzer = TechnicalAnalyzer()
        
        import time
        start = time.time()
        sma = analyzer.calculate_sma(prices, window=50)
        rsi = analyzer.calculate_rsi(prices, window=14)
        macd = analyzer.calculate_macd(prices)
        elapsed = time.time() - start
        
        # Should complete within 5 seconds
        self.assertLess(elapsed, 5.0)
        print(f"\nPerformance test completed in {elapsed:.2f}s for {n_points} data points")


# ============================================================================
# Test Runner
# ============================================================================

def run_tests():
    """Run all tests with coverage"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestConfigManager,
        TestTechnicalAnalysis,
        TestRiskManagement,
        TestMLPredictor,
        TestBacktesting,
        TestPortfolioOptimizer,
        TestIntegration,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
