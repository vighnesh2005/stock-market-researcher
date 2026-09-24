"""Chart generation module for stock research analysis.

Generates clean publication-ready charts saved to the filesystem:
- Price history with Moving Averages & Bollinger Bands
- Cumulative Returns
- Drawdown Underwater Chart
- Daily Return Distribution Histogram
- Multi-stock Comparative Returns & Risk/Return Scatter
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import matplotlib
# Use headless backend for non-interactive server/CLI chart generation
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analysis.comparison import StockComparisonResult
from src.analysis.returns import calculate_cumulative_returns, calculate_daily_returns
from src.analysis.risk import calculate_drawdown_series
from src.analysis.technical import add_technical_indicators


# Styling constants
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
PRIMARY_COLOR = "#1f77b4"
SECONDARY_COLOR = "#ff7f0e"
ACCENT_GREEN = "#2ca02c"
ACCENT_RED = "#d62728"
ACCENT_PURPLE = "#9467bd"


def plot_price_and_indicators(
    df: pd.DataFrame,
    symbol: str,
    output_path: Union[str, Path],
    price_col: str = "adjusted_close",
) -> Path:
    """Plot price history with SMA 20, 50, 200, Bollinger Bands and Volume.
    
    Args:
        df: Price history DataFrame.
        symbol: Ticker symbol for title.
        output_path: Target PNG file path.
        price_col: Price column.
        
    Returns:
        Path to generated image.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    enriched = add_technical_indicators(df, price_col=price_col)
    target = price_col if price_col in enriched.columns else "close"

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )

    # Price and Moving Averages
    ax1.plot(enriched.index, enriched[target], label="Adjusted Close", color="#111827", linewidth=1.5)
    if "SMA_20" in enriched.columns and not enriched["SMA_20"].isna().all():
        ax1.plot(enriched.index, enriched["SMA_20"], label="SMA 20", color="#f59e0b", linestyle="--", linewidth=1.2)
    if "SMA_50" in enriched.columns and not enriched["SMA_50"].isna().all():
        ax1.plot(enriched.index, enriched["SMA_50"], label="SMA 50", color="#3b82f6", linestyle="--", linewidth=1.2)
    if "SMA_200" in enriched.columns and not enriched["SMA_200"].isna().all():
        ax1.plot(enriched.index, enriched["SMA_200"], label="SMA 200", color="#ef4444", linewidth=1.4)

    # Bollinger Bands shading
    if "BB_Upper" in enriched.columns and "BB_Lower" in enriched.columns:
        ax1.fill_between(
            enriched.index,
            enriched["BB_Upper"],
            enriched["BB_Lower"],
            color="#94a3b8",
            alpha=0.15,
            label="Bollinger Bands (20, 2σ)",
        )

    currency = df.attrs.get("currency", "USD")
    company = df.attrs.get("company_name", symbol)
    ax1.set_title(f"{symbol} ({company}) - Price History & Technical Indicators", fontsize=14, fontweight="bold")
    ax1.set_ylabel(f"Price ({currency})", fontsize=11)
    ax1.legend(loc="upper left", frameon=True)
    ax1.grid(True, alpha=0.3)

    # Volume Subplot
    if "volume" in enriched.columns:
        ax2.bar(enriched.index, enriched["volume"], color="#64748b", alpha=0.6, width=1.0)
        ax2.set_ylabel("Volume", fontsize=10)
        ax2.grid(True, alpha=0.3)

    ax2.set_xlabel("Date", fontsize=11)
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_cumulative_returns(
    df_or_prices: Union[pd.DataFrame, pd.Series],
    symbol: str,
    output_path: Union[str, Path],
    price_col: str = "adjusted_close",
) -> Path:
    """Plot cumulative percentage returns with 0% baseline.
    
    Args:
        df_or_prices: Price DataFrame or Series.
        symbol: Ticker symbol.
        output_path: Target PNG file path.
        price_col: Column name.
        
    Returns:
        Path to generated image.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cum_ret = calculate_cumulative_returns(df_or_prices, price_col=price_col) * 100.0

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(cum_ret.index, cum_ret.values, color="#2563eb", linewidth=1.8, label=f"{symbol} Cumulative Return")
    ax.axhline(0, color="#6b7280", linestyle=":", linewidth=1.2, label="Base Return (0%)")

    # Highlight peak and trough
    max_idx = cum_ret.idxmax()
    min_idx = cum_ret.idxmin()
    ax.scatter([max_idx], [cum_ret.loc[max_idx]], color="#16a34a", s=60, zorder=5, label=f"Max ({cum_ret.loc[max_idx]:.1f}%)")
    ax.scatter([min_idx], [cum_ret.loc[min_idx]], color="#dc2626", s=60, zorder=5, label=f"Min ({cum_ret.loc[min_idx]:.1f}%)")

    ax.set_title(f"{symbol} - Cumulative Historical Returns", fontsize=13, fontweight="bold")
    ax.set_ylabel("Cumulative Return (%)", fontsize=11)
    ax.set_xlabel("Date", fontsize=11)
    ax.legend(loc="best", frameon=True)
    ax.grid(True, alpha=0.3)

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_drawdown(
    df_or_prices: Union[pd.DataFrame, pd.Series],
    symbol: str,
    output_path: Union[str, Path],
    price_col: str = "adjusted_close",
) -> Path:
    """Plot historical underwater drawdown series with shaded area.
    
    Args:
        df_or_prices: Price DataFrame or Series.
        symbol: Ticker symbol.
        output_path: Target PNG file path.
        price_col: Column name.
        
    Returns:
        Path to generated image.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    _, drawdown = calculate_drawdown_series(df_or_prices, price_col=price_col)
    dd_pct = drawdown * 100.0

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(dd_pct.index, dd_pct.values, color="#dc2626", linewidth=1.4)
    ax.fill_between(dd_pct.index, dd_pct.values, 0, color="#ef4444", alpha=0.3, label="Drawdown (%)")
    ax.axhline(0, color="#111827", linewidth=1.0)

    # Highlight Maximum Drawdown
    min_dd_idx = dd_pct.idxmin()
    min_dd_val = dd_pct.loc[min_dd_idx]
    ax.scatter([min_dd_idx], [min_dd_val], color="#7f1d1d", s=70, zorder=5, label=f"Max Drawdown ({min_dd_val:.1f}%)")

    ax.set_title(f"{symbol} - Historical Drawdown (Underwater Chart)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Drawdown from Peak (%)", fontsize=11)
    ax.set_xlabel("Date", fontsize=11)
    ax.legend(loc="lower left", frameon=True)
    ax.grid(True, alpha=0.3)

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_returns_distribution(
    df_or_prices: Union[pd.DataFrame, pd.Series],
    symbol: str,
    output_path: Union[str, Path],
    price_col: str = "adjusted_close",
) -> Path:
    """Plot histogram and statistical distribution of daily returns.
    
    Args:
        df_or_prices: Price DataFrame or Series.
        symbol: Ticker symbol.
        output_path: Target PNG file path.
        price_col: Column name.
        
    Returns:
        Path to generated image.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    daily_ret = calculate_daily_returns(df_or_prices, price_col=price_col) * 100.0

    fig, ax = plt.subplots(figsize=(10, 5))
    count, bins, _ = ax.hist(
        daily_ret.values, bins=50, color="#3b82f6", edgecolor="#1e40af", alpha=0.7, density=True, label="Daily Returns"
    )

    mean_val = float(daily_ret.mean())
    std_val = float(daily_ret.std(ddof=1))
    var95_val = float(np.percentile(daily_ret, 5))

    # Overlay normal distribution curve for comparison
    x = np.linspace(daily_ret.min(), daily_ret.max(), 200)
    if std_val > 0:
        p = (1 / (std_val * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean_val) / std_val) ** 2)
        ax.plot(x, p, color="#111827", linewidth=1.8, linestyle="--", label="Normal Fit")

    ax.axvline(mean_val, color="#16a34a", linestyle="-", linewidth=1.5, label=f"Mean ({mean_val:+.2f}%)")
    ax.axvline(var95_val, color="#dc2626", linestyle=":", linewidth=1.8, label=f"95% VaR ({var95_val:.2f}%)")

    ax.set_title(f"{symbol} - Daily Return Distribution", fontsize=13, fontweight="bold")
    ax.set_xlabel("Daily Return (%)", fontsize=11)
    ax.set_ylabel("Probability Density", fontsize=11)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_stock_comparison(
    comp_result: StockComparisonResult,
    output_path: Union[str, Path],
) -> Path:
    """Plot normalized cumulative return comparison across multiple stocks.
    
    Args:
        comp_result: Output from StockComparator.compare().
        output_path: Target PNG file path.
        
    Returns:
        Path to generated image.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [2.5, 1.5]}
    )

    # 1. Cumulative returns line chart
    cum_df = comp_result.cumulative_returns_df * 100.0
    for col in cum_df.columns:
        ax1.plot(cum_df.index, cum_df[col], linewidth=1.8, label=col)

    ax1.axhline(0, color="#6b7280", linestyle=":", linewidth=1.0)
    ax1.set_title(f"Comparative Cumulative Performance ({comp_result.common_start_date} to {comp_result.common_end_date})", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Cumulative Return (%)", fontsize=11)
    ax1.set_xlabel("Date", fontsize=11)
    ax1.legend(loc="best", frameon=True)
    ax1.grid(True, alpha=0.3)
    fig.autofmt_xdate()

    # 2. Risk vs Return scatter plot
    table = comp_result.comparison_table
    x_vols = table["Annualized Volatility (%)"]
    y_rets = table["Annualized Return CAGR (%)"]

    ax2.scatter(x_vols, y_rets, color="#2563eb", s=90, edgecolors="#1e40af", zorder=5)
    for sym in table.index:
        ax2.annotate(
            sym,
            (x_vols.loc[sym], y_rets.loc[sym]),
            textcoords="offset points",
            xytext=(6, 6),
            fontweight="bold",
            fontsize=10,
        )

    ax2.set_title("Annualized Risk vs Return Trade-off", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Annualized Volatility (%)", fontsize=11)
    ax2.set_ylabel("Annualized Return CAGR (%)", fontsize=11)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def generate_full_research_charts(
    df: pd.DataFrame,
    symbol: str,
    output_dir: Union[str, Path] = "reports",
    price_col: str = "adjusted_close",
) -> List[Path]:
    """Generate all 4 standard research charts for a single stock.
    
    Args:
        df: Price DataFrame.
        symbol: Ticker symbol.
        output_dir: Directory where PNG files will be stored.
        price_col: Price column.
        
    Returns:
        List of generated image paths.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"{symbol.lower()}"
    p1 = plot_price_and_indicators(df, symbol, out_dir / f"{prefix}_price_indicators.png", price_col=price_col)
    p2 = plot_cumulative_returns(df, symbol, out_dir / f"{prefix}_cumulative_returns.png", price_col=price_col)
    p3 = plot_drawdown(df, symbol, out_dir / f"{prefix}_drawdown.png", price_col=price_col)
    p4 = plot_returns_distribution(df, symbol, out_dir / f"{prefix}_return_distribution.png", price_col=price_col)

    return [p1, p2, p3, p4]
