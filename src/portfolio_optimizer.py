#!/usr/bin/env python3
"""
Portfolio Optimization Engine - Motore di ottimizzazione portafoglio
Include Modern Portfolio Theory, Black-Litterman, Risk Parity e Monte Carlo
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy.optimize import minimize
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class PortfolioMetrics:
    """Metriche complete del portafoglio ottimizzato"""
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float
    diversification_ratio: float
    turnover: float
    risk_contribution: Dict[str, float]


@dataclass
class EfficientFrontier:
    """Frontiera efficiente completa"""
    portfolios: List[Dict]
    min_variance_portfolio: Dict
    max_sharpe_portfolio: Dict
    target_return_portfolios: List[Dict]


class PortfolioOptimizer:
    """Motore di ottimizzazione portafoglio istituzionale"""
    
    def __init__(self, risk_free_rate: float = 0.04):
        """
        Args:
            risk_free_rate: Tasso privo di rischio annuale
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days = 252
    
    def calculate_expected_returns(self, returns_df: pd.DataFrame, method: str = 'historical') -> pd.Series:
        """
        Calcola i rendimenti attesi
        
        Methods:
            - 'historical': Media storica annualizzata
            - 'capm': CAPM model (se disponibile benchmark)
            - 'black_litterman': Black-Litterman con views
        """
        if method == 'historical':
            # Media storica annualizzata
            expected_returns = returns_df.mean() * self.trading_days
        elif method == 'equilibrium':
            # Rendimenti di equilibrio (market-implied)
            cov_matrix = returns_df.cov() * self.trading_days
            n_assets = len(returns_df.columns)
            # Assumi pesi di mercato uguali come proxy
            market_weights = np.ones(n_assets) / n_assets
            risk_aversion = 2.5  # Coefficiente di avversione al rischio
            expected_returns = risk_aversion * cov_matrix @ market_weights
        else:
            expected_returns = returns_df.mean() * self.trading_days
        
        return expected_returns
    
    def calculate_covariance_matrix(self, returns_df: pd.DataFrame, method: str = 'sample') -> pd.DataFrame:
        """
        Calcola matrice di covarianza
        
        Methods:
            - 'sample': Covarianza campionaria
            - 'exponential': Covarianza esponenziale (più peso ai dati recenti)
            - 'ledoit_wolf': Ledoit-Wolf shrinkage estimator
        """
        if method == 'sample':
            cov_matrix = returns_df.cov() * self.trading_days
        elif method == 'exponential':
            # Pesi esponenziali
            n_obs = len(returns_df)
            halflife = 63  # ~3 mesi
            weights = np.exp(-np.log(2) * np.arange(n_obs)[::-1] / halflife)
            weights /= weights.sum()
            
            centered = returns_df - returns_df.mean()
            cov_matrix = pd.DataFrame(
                np.cov(centered.T, aweights=weights) * self.trading_days,
                index=returns_df.columns,
                columns=returns_df.columns
            )
        elif method == 'ledoit_wolf':
            # Ledoit-Wolf shrinkage verso la matrice identità
            sample_cov = returns_df.cov() * self.trading_days
            n_assets = len(returns_df.columns)
            
            # Shrinkage intensity (semplificata)
            mu = np.trace(sample_cov) / n_assets
            target = mu * np.eye(n_assets)
            
            # Calcola shrinkage intensity
            X = returns_df.values
            n = len(X)
            delta = sample_cov.values
            
            # Stima shrinkage (formula semplificata)
            gamma = np.sum((sample_cov - target) ** 2) / n
            kappa = (np.sum(sample_cov ** 2)) / n
            shrinkage = min(1, gamma / kappa) if kappa > 0 else 0.5
            
            cov_matrix = pd.DataFrame(
                shrinkage * target + (1 - shrinkage) * delta,
                index=returns_df.columns,
                columns=returns_df.columns
            )
        else:
            cov_matrix = returns_df.cov() * self.trading_days
        
        return cov_matrix
    
    def portfolio_performance(self, weights: np.ndarray, expected_returns: pd.Series, 
                             cov_matrix: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Calcola performance del portafoglio
        
        Returns:
            Tuple con (rendimento atteso, volatilità, sharpe ratio)
        """
        port_return = np.dot(weights, expected_returns)
        port_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = (port_return - self.risk_free_rate) / port_volatility if port_volatility > 0 else 0
        
        return port_return, port_volatility, sharpe
    
    def negative_sharpe_ratio(self, weights: np.ndarray, expected_returns: pd.Series, 
                              cov_matrix: pd.DataFrame) -> float:
        """Funzione obiettivo per minimizzare (negative Sharpe Ratio)"""
        _, _, sharpe = self.portfolio_performance(weights, expected_returns, cov_matrix)
        return -sharpe
    
    def optimize_max_sharpe(self, expected_returns: pd.Series, cov_matrix: pd.DataFrame,
                           constraints: Optional[List] = None) -> Dict:
        """
        Ottimizza portafoglio Maximum Sharpe Ratio
        
        Args:
            expected_returns: Rendimenti attesi
            cov_matrix: Matrice di covarianza
            constraints: Vincoli aggiuntivi
        
        Returns:
            Dictionary con pesi ottimali e metriche
        """
        n_assets = len(expected_returns)
        
        # Vincoli base
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # I pesi sommano a 1
        ]
        
        if constraints:
            constraints_list.extend(constraints)
        
        # Limiti sui pesi (nessuna vendita allo scoperto di default)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Peso iniziale uniforme
        initial_weights = np.ones(n_assets) / n_assets
        
        # Ottimizzazione
        result = minimize(
            self.negative_sharpe_ratio,
            initial_weights,
            args=(expected_returns, cov_matrix),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': 1000, 'ftol': 1e-10}
        )
        
        if result.success:
            optimal_weights = result.x
        else:
            # Fallback a pesi uniformi
            optimal_weights = initial_weights
        
        # Normalizza pesi
        optimal_weights = optimal_weights / np.sum(optimal_weights)
        
        # Calcola metriche
        port_return, port_vol, sharpe = self.portfolio_performance(
            optimal_weights, expected_returns, cov_matrix
        )
        
        # Calcola contributo al rischio per asset
        marginal_contrib = np.dot(cov_matrix, optimal_weights)
        risk_contrib = optimal_weights * marginal_contrib
        total_risk = np.sum(risk_contrib)
        risk_contrib_pct = risk_contrib / total_risk if total_risk > 0 else np.zeros(n_assets)
        
        return {
            'weights': dict(zip(expected_returns.index, optimal_weights)),
            'expected_return': port_return,
            'volatility': port_vol,
            'sharpe_ratio': sharpe,
            'risk_contribution': dict(zip(expected_returns.index, risk_contrib_pct))
        }
    
    def optimize_min_variance(self, expected_returns: pd.Series, cov_matrix: pd.DataFrame,
                             constraints: Optional[List] = None) -> Dict:
        """
        Ottimizza portafoglio Minimum Variance
        
        Returns:
            Dictionary con pesi ottimali e metriche
        """
        n_assets = len(expected_returns)
        
        # Funzione obiettivo: minimizzare varianza
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))
        
        # Vincoli
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        if constraints:
            constraints_list.extend(constraints)
        
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_weights = np.ones(n_assets) / n_assets
        
        result = minimize(
            portfolio_variance,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': 1000, 'ftol': 1e-10}
        )
        
        if result.success:
            optimal_weights = result.x
        else:
            optimal_weights = initial_weights
        
        optimal_weights = optimal_weights / np.sum(optimal_weights)
        
        port_return, port_vol, sharpe = self.portfolio_performance(
            optimal_weights, expected_returns, cov_matrix
        )
        
        return {
            'weights': dict(zip(expected_returns.index, optimal_weights)),
            'expected_return': port_return,
            'volatility': port_vol,
            'sharpe_ratio': sharpe
        }
    
    def optimize_risk_parity(self, expected_returns: pd.Series, cov_matrix: pd.DataFrame,
                            target_risk: Optional[float] = None) -> Dict:
        """
        Ottimizza portafoglio Risk Parity (uguale contributo al rischio)
        
        Args:
            expected_returns: Rendimenti attesi
            cov_matrix: Matrice di covarianza
            target_risk: Volatilità target (opzionale)
        
        Returns:
            Dictionary con pesi ottimali
        """
        n_assets = len(expected_returns)
        
        def risk_parity_objective(weights):
            # Calcola contributo al rischio
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            if port_vol == 0:
                return 1e10
            
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / port_vol
            
            # Target: uguale contributo per tutti gli asset
            target_contrib = np.ones(n_assets) / n_assets
            
            # Minimizza differenza quadratica
            return np.sum((risk_contrib - target_contrib) ** 2)
        
        # Vincoli
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds = tuple((0.01, 1) for _ in range(n_assets))  # Minimo 1% per asset
        initial_weights = np.ones(n_assets) / n_assets
        
        result = minimize(
            risk_parity_objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000, 'ftol': 1e-12}
        )
        
        if result.success:
            optimal_weights = result.x
        else:
            optimal_weights = initial_weights
        
        optimal_weights = optimal_weights / np.sum(optimal_weights)
        
        port_return, port_vol, sharpe = self.portfolio_performance(
            optimal_weights, expected_returns, cov_matrix
        )
        
        # Calcola contributo al rischio effettivo
        marginal_contrib = np.dot(cov_matrix, optimal_weights)
        risk_contrib = optimal_weights * marginal_contrib
        total_risk = np.sum(risk_contrib)
        risk_contrib_pct = risk_contrib / total_risk if total_risk > 0 else np.zeros(n_assets)
        
        return {
            'weights': dict(zip(expected_returns.index, optimal_weights)),
            'expected_return': port_return,
            'volatility': port_vol,
            'sharpe_ratio': sharpe,
            'risk_contribution': dict(zip(expected_returns.index, risk_contrib_pct)),
            'method': 'Risk Parity'
        }
    
    def efficient_frontier(self, expected_returns: pd.Series, cov_matrix: pd.DataFrame,
                          n_portfolios: int = 100) -> EfficientFrontier:
        """
        Calcola la frontiera efficiente
        
        Args:
            expected_returns: Rendimenti attesi
            cov_matrix: Matrice di covarianza
            n_portfolios: Numero di portafogli sulla frontiera
        
        Returns:
            EfficientFrontier object
        """
        min_var_result = self.optimize_min_variance(expected_returns, cov_matrix)
        max_sharpe_result = self.optimize_max_sharpe(expected_returns, cov_matrix)
        
        # Genera portafogli target return
        min_return = min(expected_returns)
        max_return = max(expected_returns)
        target_returns = np.linspace(min_return * 1.1, max_return * 0.9, n_portfolios)
        
        target_portfolios = []
        
        for target_ret in target_returns:
            # Vincolo di rendimento target
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.dot(x, expected_returns) - target_ret}
            ]
            
            try:
                result = self.optimize_min_variance(expected_returns, cov_matrix, constraints)
                if result['volatility'] > 0:
                    result['target_return'] = target_ret
                    target_portfolios.append(result)
            except:
                continue
        
        return EfficientFrontier(
            portfolios=target_portfolios,
            min_variance_portfolio=min_var_result,
            max_sharpe_portfolio=max_sharpe_result,
            target_return_portfolios=target_portfolios
        )
    
    def black_litterman_optimization(
        self,
        market_caps: pd.Series,
        returns_df: pd.DataFrame,
        views: Dict[str, float],
        view_confidences: Dict[str, float],
        tau: float = 0.05
    ) -> Dict:
        """
        Implementa modello Black-Litterman con views dell'investitore
        
        Args:
            market_caps: Capitalizzazioni di mercato
            returns_df: Rendimenti storici
            views: Dictionary {asset: expected_return_view}
            view_confidences: Confidence per ogni view (0-1)
            tau: Scaling factor per incertezza
        
        Returns:
            Portafoglio ottimizzato Black-Litterman
        """
        assets = list(views.keys())
        n_assets = len(assets)
        
        if n_assets == 0:
            return self.optimize_max_sharpe(
                self.calculate_expected_returns(returns_df, 'equilibrium'),
                self.calculate_covariance_matrix(returns_df)
            )
        
        # Rendimenti di equilibrio
        cov_matrix = self.calculate_covariance_matrix(returns_df[assets])
        
        # Pesi di mercato
        total_market_cap = market_caps[assets].sum()
        market_weights = market_caps[assets] / total_market_cap
        
        # Rendimenti implied dal mercato
        risk_aversion = 2.5
        equilibrium_returns = risk_aversion * np.dot(cov_matrix, market_weights)
        
        # Incorpora views
        # Matrice P (identifica quali asset sono coinvolti nelle views)
        P = np.zeros((n_assets, n_assets))
        Q = np.zeros(n_assets)
        Omega_diag = []
        
        for i, asset in enumerate(assets):
            if asset in views:
                P[i, i] = 1
                Q[i] = views[asset]
                confidence = view_confidences.get(asset, 0.5)
                # Incertezza inversamente proporzionale alla confidence
                omega = (1 - confidence) / confidence * tau * cov_matrix.iloc[i, i]
                Omega_diag.append(max(omega, 1e-6))
        
        if len(Omega_diag) == 0:
            return self.optimize_max_sharpe(
                pd.Series(equilibrium_returns, index=assets),
                cov_matrix
            )
        
        Omega = np.diag(Omega_diag)
        
        # Formula Black-Litterman
        tau_cov = tau * cov_matrix
        
        # Posterior expected returns
        M1 = np.linalg.inv(np.linalg.inv(tau_cov) + P.T @ np.linalg.inv(Omega) @ P)
        M2 = np.linalg.inv(tau_cov) @ equilibrium_returns + P.T @ np.linalg.inv(Omega) @ Q
        
        bl_expected_returns = M1 @ M2
        
        # Ottimizza con nuovi rendimenti
        result = self.optimize_max_sharpe(
            pd.Series(bl_expected_returns, index=assets),
            cov_matrix
        )
        
        result['method'] = 'Black-Litterman'
        result['views_applied'] = views
        
        return result
    
    def monte_carlo_simulation(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        n_simulations: int = 10000,
        horizon_days: int = 252
    ) -> Dict:
        """
        Simulazione Monte Carlo per distribuzione dei rendimenti del portafoglio
        
        Args:
            expected_returns: Rendimenti attesi giornalieri
            cov_matrix: Matrice di covarianza giornaliera
            n_simulations: Numero di simulazioni
            horizon_days: Orizzonte temporale
        
        Returns:
            Dictionary con statistiche della simulazione
        """
        daily_returns = expected_returns / self.trading_days
        daily_cov = cov_matrix / self.trading_days
        
        n_assets = len(expected_returns)
        
        # Ottieni pesi optimal
        optimal = self.optimize_max_sharpe(expected_returns * self.trading_days, cov_matrix)
        weights = np.array([optimal['weights'][asset] for asset in expected_returns.index])
        
        # Simula percorsi
        simulated_final_values = []
        
        for _ in range(n_simulations):
            # Genera rendimenti casuali correlati
            random_returns = np.random.multivariate_normal(
                daily_returns,
                daily_cov,
                horizon_days
            )
            
            # Calcola valore finale del portafoglio
            portfolio_returns = np.dot(random_returns, weights)
            final_value = np.prod(1 + portfolio_returns)
            simulated_final_values.append(final_value)
        
        simulated_final_values = np.array(simulated_final_values)
        
        # Statistiche
        mean_return = np.mean(simulated_final_values) - 1
        median_return = np.median(simulated_final_values) - 1
        std_return = np.std(simulated_final_values)
        
        var_95 = np.percentile(simulated_final_values, 5) - 1
        var_99 = np.percentile(simulated_final_values, 1) - 1
        
        prob_positive = np.mean(simulated_final_values > 1)
        prob_double = np.mean(simulated_final_values > 2)
        prob_half = np.mean(simulated_final_values < 0.5)
        
        return {
            'mean_return': mean_return,
            'median_return': median_return,
            'std_deviation': std_return,
            'var_95': var_95,
            'var_99': var_99,
            'probability_positive': prob_positive,
            'probability_double': prob_double,
            'probability_loss_50pct': prob_half,
            'n_simulations': n_simulations,
            'horizon_days': horizon_days
        }
    
    def format_portfolio_report(self, metrics: PortfolioMetrics, strategy_name: str = "") -> str:
        """Formatta report del portafoglio"""
        report = f"""
{'='*70}
📊 PORTAFOGLIO OTTIMIZZATO{f' - {strategy_name}' if strategy_name else ''}
{'='*70}

📈 COMPOSIZIONE:
"""
        sorted_weights = sorted(metrics.weights.items(), key=lambda x: x[1], reverse=True)
        for asset, weight in sorted_weights:
            risk_contrib = metrics.risk_contribution.get(asset, 0)
            report += f"   {asset}: {weight*100:5.1f}% (contributo rischio: {risk_contrib*100:5.1f}%)\n"
        
        report += f"""
📊 METRICHE DI PERFORMANCE:
   Rendimento Atteso: {metrics.expected_return*100:.2f}% annuo
   Volatilità: {metrics.volatility*100:.2f}% annua
   Sharpe Ratio: {metrics.sharpe_ratio:.2f}
   Sortino Ratio: {metrics.sortino_ratio:.2f}

⚠️ METRICHE DI RISCHIO:
   VaR 95% (1 giorno): {metrics.var_95*100:.2f}%
   Max Drawdown Stimato: {metrics.max_drawdown*100:.2f}%
   Diversification Ratio: {metrics.diversification_ratio:.2f}

🔄 TURNOVER: {metrics.turnover*100:.1f}% (rispetto a portafoglio precedente)

{'='*70}
"""
        return report


def create_portfolio_from_recommendations(recommendations: List[Dict], capital: float = 100000) -> PortfolioMetrics:
    """
    Crea un portafoglio ottimizzato da una lista di raccomandazioni
    
    Args:
        recommendations: Lista di raccomandazioni con symbol, confidence, etc.
        capital: Capitale disponibile
    
    Returns:
        PortfolioMetrics ottimizzato
    """
    # Estrai simboli e score
    symbols = [rec['symbol'] for rec in recommendations]
    scores = np.array([rec['confidence'] for rec in recommendations])
    
    # Normalizza score come pesi iniziali
    initial_weights = scores / scores.sum()
    
    # Per una vera ottimizzazione servirebbero i rendimenti storici
    # Qui usiamo un approccio semplificato basato sulla confidence
    
    weights_dict = {sym: w for sym, w in zip(symbols, initial_weights)}
    
    return PortfolioMetrics(
        weights=weights_dict,
        expected_return=0.0,  # Da calcolare con dati storici
        volatility=0.0,
        sharpe_ratio=0.0,
        sortino_ratio=0.0,
        max_drawdown=0.0,
        var_95=0.0,
        diversification_ratio=1.0,
        turnover=0.0,
        risk_contribution=weights_dict.copy()
    )


if __name__ == "__main__":
    # Test con dati simulati
    np.random.seed(42)
    
    # Genera rendimenti sintetici per 5 asset
    n_days = 500
    assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    
    # Matrice di correlazione realistica
    corr_matrix = np.array([
        [1.00, 0.65, 0.70, 0.60, 0.45],
        [0.65, 1.00, 0.75, 0.65, 0.50],
        [0.70, 0.75, 1.00, 0.70, 0.55],
        [0.60, 0.65, 0.70, 1.00, 0.50],
        [0.45, 0.50, 0.55, 0.50, 1.00]
    ])
    
    # Volatilità giornaliere
    vols = np.array([0.02, 0.018, 0.017, 0.022, 0.035])
    
    # Genera rendimenti correlati
    L = np.linalg.cholesky(corr_matrix)
    uncorrelated = np.random.randn(n_days, len(assets))
    correlated = uncorrelated @ L.T
    
    # Applica volatilità e drift
    drifts = np.array([0.0008, 0.0006, 0.0007, 0.0005, 0.001])
    returns_data = correlated * vols + drifts
    
    returns_df = pd.DataFrame(returns_data, columns=assets)
    
    # Crea optimizer
    optimizer = PortfolioOptimizer()
    
    print("="*70)
    print("🚀 PORTFOLIO OPTIMIZATION ENGINE - TEST")
    print("="*70)
    
    # Calcola rendimenti attesi e covarianza
    expected_returns = optimizer.calculate_expected_returns(returns_df, 'historical')
    cov_matrix = optimizer.calculate_covariance_matrix(returns_df, 'sample')
    
    print("\n📊 RENDIMENTI ATTESI (annualizzati):")
    for asset, ret in expected_returns.items():
        print(f"   {asset}: {ret*100:.1f}%")
    
    # 1. Maximum Sharpe Ratio
    print("\n\n" + "="*70)
    print("1️⃣ MASSIMO SHARPE RATIO")
    print("="*70)
    
    max_sharpe = optimizer.optimize_max_sharpe(expected_returns, cov_matrix)
    print("\nPesi ottimali:")
    for asset, weight in max_sharpe['weights'].items():
        print(f"   {asset}: {weight*100:.1f}%")
    print(f"\nSharpe Ratio: {max_sharpe['sharpe_ratio']:.2f}")
    print(f"Rendimento: {max_sharpe['expected_return']*100:.1f}%")
    print(f"Volatilità: {max_sharpe['volatility']*100:.1f}%")
    
    # 2. Minimum Variance
    print("\n\n" + "="*70)
    print("2️⃣ MINIMA VARIANZA")
    print("="*70)
    
    min_var = optimizer.optimize_min_variance(expected_returns, cov_matrix)
    print("\nPesi ottimali:")
    for asset, weight in min_var['weights'].items():
        print(f"   {asset}: {weight*100:.1f}%")
    print(f"\nSharpe Ratio: {min_var['sharpe_ratio']:.2f}")
    print(f"Rendimento: {min_var['expected_return']*100:.1f}%")
    print(f"Volatilità: {min_var['volatility']*100:.1f}%")
    
    # 3. Risk Parity
    print("\n\n" + "="*70)
    print("3️⃣ RISK PARITY")
    print("="*70)
    
    risk_parity = optimizer.optimize_risk_parity(expected_returns, cov_matrix)
    print("\nPesi ottimali:")
    for asset, weight in risk_parity['weights'].items():
        risk_contrib = risk_parity['risk_contribution'].get(asset, 0)
        print(f"   {asset}: {weight*100:5.1f}% (rischio: {risk_contrib*100:5.1f}%)")
    print(f"\nSharpe Ratio: {risk_parity['sharpe_ratio']:.2f}")
    
    # 4. Black-Litterman
    print("\n\n" + "="*70)
    print("4️⃣ BLACK-LITTERMAN (con views)")
    print("="*70)
    
    market_caps = pd.Series({
        'AAPL': 3000e9,
        'GOOGL': 1800e9,
        'MSFT': 2800e9,
        'AMZN': 1500e9,
        'TSLA': 800e9
    })
    
    views = {
        'AAPL': 0.25,  # View: AAPL renderà il 25%
        'TSLA': 0.40,  # View: TSLA renderà il 40%
        'MSFT': 0.15   # View: MSFT renderà il 15%
    }
    
    confidences = {
        'AAPL': 0.7,
        'TSLA': 0.5,
        'MSFT': 0.8
    }
    
    bl_result = optimizer.black_litterman_optimization(
        market_caps, returns_df, views, confidences
    )
    
    print("\nViews applicate:")
    for asset, view in views.items():
        conf = confidences.get(asset, 0)
        print(f"   {asset}: {view*100:.0f}% (confidence: {conf*100:.0f}%)")
    
    print("\nPesi ottimizzati:")
    for asset, weight in bl_result['weights'].items():
        print(f"   {asset}: {weight*100:.1f}%")
    
    # 5. Monte Carlo Simulation
    print("\n\n" + "="*70)
    print("5️⃣ SIMULAZIONE MONTE CARLO (1 anno)")
    print("="*70)
    
    mc_results = optimizer.monte_carlo_simulation(
        expected_returns, cov_matrix, n_simulations=5000, horizon_days=252
    )
    
    print(f"""
Risultati su {mc_results['n_simulations']} simulazioni:
   Rendimento Medio: {mc_results['mean_return']*100:.1f}%
   Rendimento Mediano: {mc_results['median_return']*100:.1f}%
   
   Probabilità rendimento positivo: {mc_results['probability_positive']*100:.1f}%
   Probabilità raddoppiare capitale: {mc_results['probability_double']*100:.1f}%
   Probabilità perdere >50%: {mc_results['probability_loss_50pct']*100:.1f}%
   
   VaR 95%: {mc_results['var_95']*100:.1f}%
   VaR 99%: {mc_results['var_99']*100:.1f}%
""")
    
    print("\n✅ Portfolio Optimization Engine completato!")
