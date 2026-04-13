"""
Advanced Financial Visualization Engine
========================================
Multi-dimensional visualization suite for financial data analysis
including interactive charts, heatmaps, and 3D surface plots.

Author: Trading Advisor Pro v4.0 - Interstellar Edition
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ChartType(Enum):
    """Supported chart types"""
    LINE = "line"
    CANDLESTICK = "candlestick"
    HEATMAP = "heatmap"
    SURFACE_3D = "surface_3d"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    PIE = "pie"
    TREEMAP = "treemap"
    RADAR = "radar"
    EFFICIENT_FRONTIER = "efficient_frontier"


@dataclass
class ChartConfig:
    """Configuration for chart rendering"""
    width: int = 1200
    height: int = 800
    title: str = ""
    show_legend: bool = True
    show_grid: bool = True
    color_scheme: str = "professional"
    interactive: bool = True


class ColorPalette:
    """Professional color palettes for financial charts"""
    
    PROFESSIONAL = {
        'primary': '#1f77b4',
        'secondary': '#ff7f0e',
        'success': '#2ca02c',
        'danger': '#d62728',
        'warning': '#ff9800',
        'info': '#17becf',
        'neutral': '#7f7f7f',
        'background': '#ffffff',
        'grid': '#e0e0e0'
    }
    
    DARK = {
        'primary': '#5dade2',
        'secondary': '#f5b041',
        'success': '#58d68d',
        'danger': '#ec7063',
        'warning': '#f9e79f',
        'info': '#48c9b0',
        'neutral': '#aab7b8',
        'background': '#1a1a2e',
        'grid': '#2d2d44'
    }
    
    TRADING = {
        'bull': '#00c853',
        'bear': '#ff3d00',
        'neutral': '#9e9e9e',
        'volume_up': '#66bb6a',
        'volume_down': '#ef5350',
        'background': '#0d1117',
        'grid': '#30363d'
    }
    
    @classmethod
    def get_palette(cls, scheme: str) -> Dict[str, str]:
        """Get color palette by name"""
        return getattr(cls, scheme.upper(), cls.PROFESSIONAL)


class AsciiChartRenderer:
    """Render charts in ASCII format for terminal display"""
    
    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
    
    def render_line_chart(self, data: np.ndarray, title: str = "", 
                         labels: List[str] = None) -> str:
        """Render line chart in ASCII"""
        if len(data) == 0:
            return "No data to display"
        
        # Normalize data to chart dimensions
        min_val = np.min(data)
        max_val = np.max(data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        # Create chart grid
        chart = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Draw axes
        for i in range(self.height):
            chart[i][0] = '│'
        for j in range(self.width):
            chart[self.height - 1][j] = '─'
        chart[self.height - 1][0] = '└'
        
        # Plot data points
        n_points = min(len(data), self.width - 2)
        step = len(data) / n_points
        
        for i in range(n_points):
            x = i + 1
            data_idx = int(i * step)
            y_normalized = (data[data_idx] - min_val) / range_val
            y = int(y_normalized * (self.height - 2))
            
            chart[self.height - 2 - y][x] = '●'
        
        # Add title
        output_lines = []
        if title:
            output_lines.append(f"  {title}")
            output_lines.append("")
        
        # Add Y-axis labels
        for i in range(self.height):
            if i == 0:
                label = f"{max_val:8.2f}"
            elif i == self.height - 1:
                label = f"{min_val:8.2f}"
            elif i == self.height // 2:
                label = f"{(max_val + min_val) / 2:8.2f}"
            else:
                label = " " * 8
            
            row = label + ' ' + ''.join(chart[i])
            output_lines.append(row)
        
        # Add X-axis labels
        if labels:
            output_lines.append(' ' * 9 + ' '.join(labels[:min(len(labels), n_points)]))
        
        return '\n'.join(output_lines)
    
    def render_candlestick(self, open_prices: np.ndarray, high_prices: np.ndarray,
                          low_prices: np.ndarray, close_prices: np.ndarray,
                          title: str = "") -> str:
        """Render candlestick chart in ASCII"""
        if len(open_prices) == 0:
            return "No data to display"
        
        all_prices = np.concatenate([open_prices, high_prices, low_prices, close_prices])
        min_val = np.min(all_prices)
        max_val = np.max(all_prices)
        range_val = max_val - min_val if max_val != min_val else 1
        
        chart_height = self.height - 4
        chart_width = min(len(open_prices) * 2, self.width - 4)
        
        chart = [[' ' for _ in range(chart_width + 4)] for _ in range(chart_height + 2)]
        
        # Draw candles
        n_candles = min(len(open_prices), chart_width // 2)
        
        for i in range(n_candles):
            x = i * 2 + 2
            
            # Calculate positions
            high_y = int((high_prices[i] - min_val) / range_val * (chart_height - 1))
            low_y = int((low_prices[i] - min_val) / range_val * (chart_height - 1))
            open_y = int((open_prices[i] - min_val) / range_val * (chart_height - 1))
            close_y = int((close_prices[i] - min_val) / range_val * (chart_height - 1))
            
            is_bullish = close_prices[i] >= open_prices[i]
            
            # Draw wick
            for y in range(min(high_y, low_y), max(high_y, low_y) + 1):
                chart[chart_height - y][x] = '│'
            
            # Draw body
            body_top = min(open_y, close_y)
            body_bottom = max(open_y, close_y)
            
            for y in range(body_top, body_bottom + 1):
                chart[chart_height - y][x] = '█'
                if x + 1 < chart_width + 4:
                    chart[chart_height - y][x + 1] = '█'
        
        # Build output
        output_lines = []
        if title:
            output_lines.append(f"  {title}")
            output_lines.append("")
        
        for row in chart:
            output_lines.append(''.join(row))
        
        return '\n'.join(output_lines)
    
    def render_heatmap(self, data: np.ndarray, title: str = "",
                      row_labels: List[str] = None, 
                      col_labels: List[str] = None) -> str:
        """Render heatmap in ASCII"""
        if data.size == 0:
            return "No data to display"
        
        rows, cols = data.shape
        max_rows = self.height - 4
        max_cols = self.width - 12
        
        # Subsample if necessary
        row_step = max(1, rows // max_rows)
        col_step = max(1, cols // max_cols)
        
        sampled_rows = range(0, rows, row_step)
        sampled_cols = range(0, cols, col_step)
        
        min_val = np.min(data)
        max_val = np.max(data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        # Characters for different intensity levels
        chars = ' ░▒▓█'
        
        output_lines = []
        if title:
            output_lines.append(f"  {title}")
            output_lines.append("")
        
        # Column headers
        header = ' ' * 10
        for j in sampled_cols:
            if col_labels:
                header += col_labels[j][:4].ljust(5)
            else:
                header += f'{j:5}'
        output_lines.append(header)
        
        # Rows
        for i in sampled_rows:
            if row_labels:
                row_label = row_labels[i][:8].ljust(9)
            else:
                row_label = f'{i:8}'
            
            row_str = row_label + ' '
            for j in sampled_cols:
                normalized = (data[i, j] - min_val) / range_val
                char_idx = min(int(normalized * (len(chars) - 1)), len(chars) - 1)
                row_str += chars[char_idx] * 4 + ' '
            
            output_lines.append(row_str)
        
        return '\n'.join(output_lines)
    
    def render_histogram(self, data: np.ndarray, bins: int = 20,
                        title: str = "") -> str:
        """Render histogram in ASCII"""
        if len(data) == 0:
            return "No data to display"
        
        # Calculate histogram
        hist, bin_edges = np.histogram(data, bins=bins)
        max_count = np.max(hist)
        
        chart_height = self.height - 6
        bar_width = max(1, (self.width - 12) // bins)
        
        output_lines = []
        if title:
            output_lines.append(f"  {title}")
            output_lines.append("")
        
        # Draw histogram from top to bottom
        for row in range(chart_height, -1, -1):
            threshold = max_count * row / chart_height
            line = f"{threshold:8.0f} │"
            
            for count in hist:
                if count >= threshold:
                    line += '█' * bar_width
                else:
                    line += ' ' * bar_width
                line += ' '
            
            output_lines.append(line)
        
        # X-axis
        output_lines.append(' ' * 9 + '└' + '─' * (bar_width + 1) * bins)
        
        # Bin labels
        label_line = ' ' * 9 + ' '
        step = max(1, bins // 10)
        for i in range(0, bins, step):
            label_line += f"{bin_edges[i]:{bar_width}.1f}" + ' '
        output_lines.append(label_line)
        
        return '\n'.join(output_lines)
    
    def render_pie_chart(self, values: np.ndarray, labels: List[str] = None,
                        title: str = "") -> str:
        """Render pie chart approximation in ASCII"""
        if len(values) == 0:
            return "No data to display"
        
        total = np.sum(values)
        angles = [(v / total) * 360 for v in values]
        
        # Use block characters to approximate pie
        radius = min(self.height // 2 - 2, self.width // 4 - 2)
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Create canvas
        canvas = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Draw circle with sectors
        symbols = ['░', '▒', '▓', '█', '●', '○', '■', '□']
        current_angle = 0
        
        for sector_idx, angle in enumerate(angles):
            symbol = symbols[sector_idx % len(symbols)]
            end_angle = current_angle + angle
            
            # Draw sector
            for y in range(-radius, radius + 1):
                for x in range(-radius * 2, radius * 2 + 1):
                    # Adjust for aspect ratio
                    dist = np.sqrt((x / 2) ** 2 + y ** 2)
                    if dist <= radius:
                        point_angle = np.degrees(np.arctan2(y, x / 2))
                        if point_angle < 0:
                            point_angle += 360
                        
                        if current_angle <= point_angle < end_angle:
                            canvas_y = center_y - y
                            canvas_x = center_x + x
                            
                            if 0 <= canvas_y < self.height and 0 <= canvas_x < self.width:
                                canvas[canvas_y][canvas_x] = symbol
            
            current_angle = end_angle
        
        # Build output
        output_lines = []
        if title:
            output_lines.append(f"  {title}")
            output_lines.append("")
        
        for row in canvas:
            output_lines.append(''.join(row))
        
        # Legend
        if labels:
            output_lines.append("")
            output_lines.append("  Legend:")
            for i, label in enumerate(labels[:len(values)]):
                symbol = symbols[i % len(symbols)]
                pct = (values[i] / total) * 100
                output_lines.append(f"    {symbol} {label}: {pct:.1f}%")
        
        return '\n'.join(output_lines)


class PortfolioVisualizer:
    """Specialized visualizations for portfolio analysis"""
    
    def __init__(self, renderer: AsciiChartRenderer = None):
        self.renderer = renderer or AsciiChartRenderer()
    
    def render_efficient_frontier(self, returns: np.ndarray, volatilities: np.ndarray,
                                 sharpe_ratios: np.ndarray,
                                 optimal_point: Tuple[float, float] = None,
                                 title: str = "Efficient Frontier") -> str:
        """Render efficient frontier scatter plot"""
        if len(returns) == 0:
            return "No data to display"
        
        # Create scatter data
        data_points = list(zip(volatilities, returns))
        
        # Use scatter plot approximation
        output_lines = []
        output_lines.append(f"  {title}")
        output_lines.append("")
        
        # Find ranges
        min_vol = np.min(volatilities)
        max_vol = np.max(volatilities)
        min_ret = np.min(returns)
        max_ret = np.max(returns)
        
        vol_range = max_vol - min_vol if max_vol != min_vol else 1
        ret_range = max_ret - min_ret if max_ret != min_ret else 1
        
        chart_height = self.renderer.height - 8
        chart_width = self.renderer.width - 12
        
        # Create grid
        grid = [[' ' for _ in range(chart_width)] for _ in range(chart_height)]
        
        # Plot points
        for vol, ret in zip(volatilities, returns):
            x = int((vol - min_vol) / vol_range * (chart_width - 1))
            y = int((ret - min_ret) / ret_range * (chart_height - 1))
            
            if 0 <= x < chart_width and 0 <= y < chart_height:
                grid[chart_height - 1 - y][x] = '●'
        
        # Mark optimal point
        if optimal_point:
            opt_vol, opt_ret = optimal_point
            x = int((opt_vol - min_vol) / vol_range * (chart_width - 1))
            y = int((opt_ret - min_ret) / ret_range * (chart_height - 1))
            
            if 0 <= x < chart_width and 0 <= y < chart_height:
                grid[chart_height - 1 - y][x] = '★'
        
        # Draw axes
        for i in range(chart_height):
            grid[i][0] = '│'
        for j in range(chart_width):
            grid[chart_height - 1][j] = '─'
        grid[chart_height - 1][0] = '└'
        
        # Add labels
        output_lines.append(f"  Return ↑")
        
        for i in range(chart_height):
            if i == 0:
                label = f"{max_ret:7.2%}"
            elif i == chart_height - 1:
                label = f"{min_ret:7.2%}"
            else:
                label = " " * 8
            
            output_lines.append(label + ' │' + ''.join(grid[i]))
        
        output_lines.append(' ' * 9 + '└' + '─' * chart_width)
        output_lines.append(' ' * 9 + f"{min_vol:.2%}".ljust(10) + 
                          f"{(min_vol + max_vol) / 2:.2%}".center(chart_width // 2) +
                          f"{max_vol:.2%}".rjust(chart_width // 2 - 10))
        output_lines.append(' ' * 9 + "Volatility →")
        
        if optimal_point:
            output_lines.append(f"\n  ★ Optimal Portfolio: Vol={optimal_point[0]:.2%}, Ret={optimal_point[1]:.2%}")
        
        return '\n'.join(output_lines)
    
    def render_allocation(self, weights: np.ndarray, asset_names: List[str],
                         title: str = "Portfolio Allocation") -> str:
        """Render portfolio allocation as horizontal bar chart"""
        if len(weights) == 0:
            return "No data to display"
        
        total = np.sum(weights)
        weights_pct = weights / total * 100
        
        bar_width = self.renderer.width - 30
        
        output_lines = []
        output_lines.append(f"  {title}")
        output_lines.append("")
        
        # Sort by weight
        sorted_indices = np.argsort(weights)[::-1]
        
        for idx in sorted_indices:
            name = asset_names[idx] if idx < len(asset_names) else f"Asset {idx}"
            pct = weights_pct[idx]
            filled = int(bar_width * pct / 100)
            
            bar = '█' * filled + '░' * (bar_width - filled)
            output_lines.append(f"  {name:15} │{bar}│ {pct:5.1f}%")
        
        output_lines.append("")
        output_lines.append(f"  Total: {total * 100:.1f}%")
        
        return '\n'.join(output_lines)
    
    def render_drawdown(self, cumulative_returns: np.ndarray,
                       title: str = "Drawdown Analysis") -> str:
        """Render drawdown chart"""
        if len(cumulative_returns) == 0:
            return "No data to display"
        
        # Calculate drawdown
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        
        return self.renderer.render_line_chart(
            drawdown,
            title=title,
            labels=['Start', 'Mid', 'End']
        )


def run_visualization_demo():
    """Demonstration of visualization capabilities"""
    print("=" * 70)
    print("ADVANCED VISUALIZATION ENGINE - DEMO")
    print("=" * 70)
    
    renderer = AsciiChartRenderer(width=80, height=24)
    
    # Demo 1: Line Chart
    print("\n📈 LINE CHART DEMO")
    print("-" * 70)
    np.random.seed(42)
    price_data = np.cumsum(np.random.randn(50)) + 100
    print(renderer.render_line_chart(price_data, "Stock Price Simulation"))
    
    # Demo 2: Candlestick
    print("\n\n🕯️  CANDLESTICK CHART DEMO")
    print("-" * 70)
    n_candles = 20
    open_p = np.random.randn(n_candles).cumsum() + 100
    close_p = open_p + np.random.randn(n_candles) * 2
    high_p = np.maximum(open_p, close_p) + np.abs(np.random.randn(n_candles))
    low_p = np.minimum(open_p, close_p) - np.abs(np.random.randn(n_candles))
    print(renderer.render_candlestick(open_p, high_p, low_p, close_p, "Price Action"))
    
    # Demo 3: Heatmap
    print("\n\n🔥 HEATMAP DEMO")
    print("-" * 70)
    correlation_matrix = np.random.randn(8, 8)
    correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
    np.fill_diagonal(correlation_matrix, 1.0)
    asset_names = [f"A{i}" for i in range(8)]
    print(renderer.render_heatmap(correlation_matrix, "Correlation Matrix", 
                                  asset_names, asset_names))
    
    # Demo 4: Histogram
    print("\n\n📊 HISTOGRAM DEMO")
    print("-" * 70)
    returns_data = np.random.randn(1000) * 0.05
    print(renderer.render_histogram(returns_data, bins=25, title="Return Distribution"))
    
    # Demo 5: Pie Chart
    print("\n\n🥧 PIE CHART DEMO")
    print("-" * 70)
    allocation = np.array([30, 25, 20, 15, 10])
    labels = ["Stocks", "Bonds", "Real Estate", "Commodities", "Cash"]
    print(renderer.render_pie_chart(allocation, labels, "Asset Allocation"))
    
    # Demo 6: Efficient Frontier
    print("\n\n🎯 EFFICIENT FRONTIER DEMO")
    print("-" * 70)
    port_visualizer = PortfolioVisualizer(renderer)
    
    np.random.seed(42)
    n_portfolios = 200
    vols = np.random.uniform(0.05, 0.25, n_portfolios)
    rets = vols * 0.5 + np.random.randn(n_portfolios) * 0.02
    sharpe = rets / vols
    
    optimal_idx = np.argmax(sharpe)
    optimal = (vols[optimal_idx], rets[optimal_idx])
    
    print(port_visualizer.render_efficient_frontier(rets, vols, sharpe, optimal))
    
    # Demo 7: Portfolio Allocation
    print("\n\n📦 PORTFOLIO ALLOCATION DEMO")
    print("-" * 70)
    weights = np.array([0.25, 0.20, 0.18, 0.15, 0.12, 0.10])
    names = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA"]
    print(port_visualizer.render_allocation(weights, names))
    
    print("\n" + "=" * 70)
    print("✨ VISUALIZATION DEMO COMPLETE ✨")
    print("=" * 70)


if __name__ == "__main__":
    run_visualization_demo()
