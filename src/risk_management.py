"""
Advanced Risk Management - Gestione avanzata del rischio
Include VaR, Expected Shortfall, correlazioni e stress testing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
from dataclasses import dataclass


@dataclass
class RiskMetrics:
    """Metriche di rischio complete"""
    var_95: float  # Value at Risk al 95%
    var_99: float  # Value at Risk al 99%
    expected_shortfall_95: float  # CVaR al 95%
    expected_shortfall_99: float  # CVaR al 99%
    max_drawdown: float  # Massimo drawdown storico
    current_drawdown: float  # Drawdown corrente
    volatility_annual: float  # Volatilità annualizzata
    skewness: float  # Asimmetria dei rendimenti
    kurtosis: float  # Curtosi dei rendimenti
    sharpe_ratio: float  # Sharpe Ratio
    sortino_ratio: float  # Sortino Ratio
    beta: Optional[float]  # Beta rispetto al mercato (se disponibile)


class AdvancedRiskManager:
    """Gestione avanzata del rischio per trading"""
    
    def __init__(self, risk_free_rate: float = 0.04):
        """
        Args:
            risk_free_rate: Tasso privo di rischio annuale (default 4%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_var(
        self, 
        returns: pd.Series, 
        confidence_level: float = 0.95,
        method: str = 'historical'
    ) -> float:
        """
        Calcola Value at Risk
        
        Args:
            returns: Serie dei rendimenti
            confidence_level: Livello di confidenza (es. 0.95 per 95%)
            method: Metodo di calcolo ('historical', 'parametric', 'monte_carlo')
        
        Returns:
            VaR come valore positivo (perdita potenziale)
        """
        if method == 'historical':
            var = self.calculate_var_historical(returns, confidence_level)
        elif method == 'parametric':
            var = self.calculate_var_parametric(returns, confidence_level)
        elif method == 'monte_carlo':
            var = self.calculate_var_monte_carlo(returns, confidence_level)
        else:
            var = self.calculate_var_historical(returns, confidence_level)
        
        # Ritorna il valore assoluto (positivo) per rappresentare la perdita
        return abs(var)
    
    def calculate_cvar(
        self, 
        returns: pd.Series, 
        confidence_level: float = 0.95
    ) -> float:
        """
        Calcola Conditional Value at Risk (Expected Shortfall)
        
        Args:
            returns: Serie dei rendimenti
            confidence_level: Livello di confidenza
        
        Returns:
            CVaR/Expected Shortfall come valore positivo
        """
        var = self.calculate_var(returns, confidence_level, method='historical')
        # Recalcola il VaR storico negativo per trovare i valori sotto la soglia
        var_neg = self.calculate_var_historical(returns, confidence_level)
        cvar = returns[returns <= var_neg].mean()
        # Ritorna il valore assoluto (positivo) - CVaR è sempre maggiore di VaR
        return abs(cvar) if not np.isnan(cvar) else var
    
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """Calcola i rendimenti logaritmici"""
        return np.log(prices / prices.shift(1)).dropna()
    
    def calculate_var_historical(
        self, 
        returns: pd.Series, 
        confidence_level: float = 0.95
    ) -> float:
        """
        Calcola Value at Risk usando metodo storico
        
        Args:
            returns: Serie dei rendimenti
            confidence_level: Livello di confidenza (es. 0.95 per 95%)
        
        Returns:
            VaR come percentuale negativa (es. -0.02 = -2%)
        """
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(returns.dropna(), var_percentile)
        return var
    
    def calculate_var_parametric(
        self, 
        returns: pd.Series, 
        confidence_level: float = 0.95
    ) -> float:
        """
        Calcola VaR parametrico assumendo distribuzione normale
        
        Args:
            returns: Serie dei rendimenti
            confidence_level: Livello di confidenza
        
        Returns:
            VaR parametrico
        """
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Z-score per il livello di confidenza
        z_score = stats.norm.ppf(1 - confidence_level)
        
        var = mean_return + z_score * std_return
        return var
    
    def calculate_var_monte_carlo(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        n_simulations: int = 10000,
        horizon_days: int = 1
    ) -> float:
        """
        Calcola VaR usando simulazione Monte Carlo
        
        Args:
            returns: Serie dei rendimenti
            confidence_level: Livello di confidenza
            n_simulations: Numero di simulazioni
            horizon_days: Orizzonte temporale in giorni
        
        Returns:
            VaR Monte Carlo
        """
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Simula rendimenti futuri
        simulated_returns = np.random.normal(
            mean_return * horizon_days,
            std_return * np.sqrt(horizon_days),
            n_simulations
        )
        
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(simulated_returns, var_percentile)
        
        return var
    
    def calculate_expected_shortfall(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calcola Expected Shortfall (CVaR) - perdita media oltre il VaR
        
        Args:
            returns: Serie dei rendimenti
            confidence_level: Livello di confidenza
        
        Returns:
            Expected Shortfall
        """
        var = self.calculate_var_historical(returns, confidence_level)
        es = returns[returns <= var].mean()
        return es if not np.isnan(es) else var
    
    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        """
        Calcola il massimo drawdown storico
        
        Args:
            prices: Serie dei prezzi
        
        Returns:
            Massimo drawdown come percentuale negativa
        """
        # Running maximum
        running_max = prices.cummax()
        drawdown = (prices - running_max) / running_max
        
        return drawdown.min()
    
    def calculate_current_drawdown(self, prices: pd.Series) -> float:
        """
        Calcola il drawdown corrente
        
        Args:
            prices: Serie dei prezzi
        
        Returns:
            Drawdown corrente come percentuale negativa
        """
        running_max = prices.cummax()
        current_dd = (prices.iloc[-1] - running_max.iloc[-1]) / running_max.iloc[-1]
        return current_dd
    
    def calculate_volatility_annual(self, returns: pd.Series) -> float:
        """
        Calcola la volatilità annualizzata
        
        Args:
            returns: Rendimenti giornalieri
        
        Returns:
            Volatilità annualizzata
        """
        daily_vol = returns.std()
        annual_vol = daily_vol * np.sqrt(252)  # 252 giorni di trading
        return annual_vol
    
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        benchmark_return: float = 0.0
    ) -> float:
        """
        Calcola lo Sharpe Ratio
        
        Args:
            returns: Rendimenti del titolo/portafoglio
            benchmark_return: Rendimento benchmark (o risk-free rate)
        
        Returns:
            Sharpe Ratio annualizzato
        """
        excess_returns = returns - benchmark_return
        
        if returns.std() == 0:
            return 0.0
        
        sharpe = excess_returns.mean() / returns.std()
        # Annualizza
        sharpe_annual = sharpe * np.sqrt(252)
        
        return sharpe_annual
    
    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        target_return: float = 0.0
    ) -> float:
        """
        Calcola lo Sortino Ratio (usa solo downside deviation)
        
        Args:
            returns: Rendimenti del titolo/portafoglio
            target_return: Rendimento target
        
        Returns:
            Sortino Ratio annualizzato
        """
        excess_returns = returns - target_return
        
        # Downside deviation (solo rendimenti negativi)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        downside_dev = downside_returns.std()
        sortino = excess_returns.mean() / downside_dev
        sortino_annual = sortino * np.sqrt(252)
        
        return sortino_annual
    
    def calculate_skewness_kurtosis(self, returns: pd.Series) -> Tuple[float, float]:
        """
        Calcola asimmetria e curtosi dei rendimenti
        
        Returns:
            Tuple con (skewness, kurtosis)
        """
        skewness = stats.skew(returns.dropna())
        kurtosis = stats.kurtosis(returns.dropna())  # Excess kurtosis
        return skewness, kurtosis
    
    def calculate_correlation_matrix(self, returns_dict: Dict[str, pd.Series]) -> pd.DataFrame:
        """
        Calcola matrice di correlazione tra più asset
        
        Args:
            returns_dict: Dizionario {symbol: returns_series}
        
        Returns:
            Matrice di correlazione
        """
        df = pd.DataFrame(returns_dict)
        return df.corr()
    
    def calculate_portfolio_var(
        self,
        weights: np.ndarray,
        returns_matrix: pd.DataFrame,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calcola VaR di portafoglio
        
        Args:
            weights: Pesi degli asset nel portafoglio
            returns_matrix: Matrice dei rendimenti
            confidence_level: Livello di confidenza
        
        Returns:
            VaR del portafoglio
        """
        # Rendimento del portafoglio
        portfolio_returns = (returns_matrix * weights).sum(axis=1)
        
        var = self.calculate_var_historical(portfolio_returns, confidence_level)
        return var
    
    def stress_test(
        self,
        returns: pd.Series,
        scenarios: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Esegue stress test con scenari predefiniti
        
        Args:
            returns: Rendimenti storici
            scenarios: Dizionario {scenario_name: shock_percentage}
        
        Returns:
            Dizionario con impatti degli scenari
        """
        results = {}
        
        for scenario_name, shock in scenarios.items():
            # Simula impatto dello shock
            impacted_returns = returns * (1 + shock)
            var_impact = self.calculate_var_historical(impacted_returns, 0.95)
            results[scenario_name] = var_impact
        
        return results
    
    def calculate_risk_metrics(self, prices: pd.Series) -> RiskMetrics:
        """
        Calcola tutte le metriche di rischio
        
        Args:
            prices: Serie dei prezzi
        
        Returns:
            RiskMetrics completo
        """
        returns = self.calculate_returns(prices)
        
        # VaR
        var_95 = self.calculate_var_historical(returns, 0.95)
        var_99 = self.calculate_var_historical(returns, 0.99)
        
        # Expected Shortfall
        es_95 = self.calculate_expected_shortfall(returns, 0.95)
        es_99 = self.calculate_expected_shortfall(returns, 0.99)
        
        # Drawdown
        max_dd = self.calculate_max_drawdown(prices)
        current_dd = self.calculate_current_drawdown(prices)
        
        # Volatilità
        vol_annual = self.calculate_volatility_annual(returns)
        
        # Skewness e Kurtosis
        skewness, kurtosis = self.calculate_skewness_kurtosis(returns)
        
        # Sharpe e Sortino
        daily_rf = self.risk_free_rate / 252
        sharpe = self.calculate_sharpe_ratio(returns, daily_rf)
        sortino = self.calculate_sortino_ratio(returns, daily_rf)
        
        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            expected_shortfall_95=es_95,
            expected_shortfall_99=es_99,
            max_drawdown=max_dd,
            current_drawdown=current_dd,
            volatility_annual=vol_annual,
            skewness=skewness,
            kurtosis=kurtosis,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            beta=None  # Da calcolare se disponibile benchmark
        )
    
    def get_risk_rating(self, risk_metrics: RiskMetrics) -> str:
        """
        Assegna un rating di rischio basato sulle metriche
        
        Returns:
            Rating: "BASSO", "MEDIO", "ALTO", "MOLTO_ALTO"
        """
        score = 0
        
        # Volatilità
        if risk_metrics.volatility_annual > 0.5:
            score += 3
        elif risk_metrics.volatility_annual > 0.3:
            score += 2
        elif risk_metrics.volatility_annual > 0.15:
            score += 1
        
        # Max Drawdown
        if abs(risk_metrics.max_drawdown) > 0.3:
            score += 3
        elif abs(risk_metrics.max_drawdown) > 0.2:
            score += 2
        elif abs(risk_metrics.max_drawdown) > 0.1:
            score += 1
        
        # VaR
        if abs(risk_metrics.var_95) > 0.03:
            score += 2
        elif abs(risk_metrics.var_95) > 0.02:
            score += 1
        
        # Kurtosis (fat tails)
        if risk_metrics.kurtosis > 3:
            score += 2
        elif risk_metrics.kurtosis > 1:
            score += 1
        
        if score >= 8:
            return "MOLTO_ALTO"
        elif score >= 5:
            return "ALTO"
        elif score >= 3:
            return "MEDIO"
        else:
            return "BASSO"
    
    def format_risk_report(self, risk_metrics: RiskMetrics, symbol: str) -> str:
        """
        Formatta report di rischio
        
        Args:
            risk_metrics: Metriche di rischio
            symbol: Simbolo del titolo
        
        Returns:
            Report formattato
        """
        risk_rating = self.get_risk_rating(risk_metrics)
        
        report = f"""
{'='*60}
📊 REPORT RISCHIO: {symbol}
{'='*60}

⚠️ RATING DI RISCHIO: {risk_rating}

📉 VALUE AT RISK (VaR):
   VaR 95% (1 giorno): {risk_metrics.var_95:.2%}
   VaR 99% (1 giorno): {risk_metrics.var_99:.2%}

💸 EXPECTED SHORTFALL (CVaR):
   ES 95%: {risk_metrics.expected_shortfall_95:.2%}
   ES 99%: {risk_metrics.expected_shortfall_99:.2%}

📊 DRAWDOWN:
   Massimo Drawdown Storico: {risk_metrics.max_drawdown:.2%}
   Drawdown Corrente: {risk_metrics.current_drawdown:.2%}

📈 VOLATILITÀ E RENDIMENTO:
   Volatilità Annualizzata: {risk_metrics.volatility_annual:.2%}
   Sharpe Ratio: {risk_metrics.sharpe_ratio:.2f}
   Sortino Ratio: {risk_metrics.sortino_ratio:.2f}

📊 DISTRIBUZIONE RENDIMENTI:
   Skewness: {risk_metrics.skewness:.2f}
   Kurtosis: {risk_metrics.kurtosis:.2f}
   {'⚠️ Code grasse (fat tails) rilevate!' if risk_metrics.kurtosis > 1 else '✓ Distribuzione quasi normale'}

{'='*60}
"""
        return report


if __name__ == "__main__":
    # Test con dati simulati
    np.random.seed(42)
    
    # Genera prezzi sintetici
    n_days = 500
    returns = np.random.normal(0.0005, 0.02, n_days)  # Mean 0.05%, daily vol 2%
    prices = 100 * np.exp(np.cumsum(returns))
    
    prices_series = pd.Series(prices)
    
    # Calcola metriche
    risk_manager = AdvancedRiskManager()
    metrics = risk_manager.calculate_risk_metrics(prices_series)
    
    print(risk_manager.format_risk_report(metrics, "TEST"))
    
    # Stress test
    scenarios = {
        "Crollo 2008": -0.30,
        "COVID Crash": -0.35,
        "Flash Crash": -0.10,
        "Correzione moderata": -0.15
    }
    
    stress_results = risk_manager.stress_test(
        risk_manager.calculate_returns(prices_series),
        scenarios
    )
    
    print("\n🔬 STRESS TEST RESULTS:")
    for scenario, impact in stress_results.items():
        print(f"   {scenario}: VaR = {impact:.2%}")
