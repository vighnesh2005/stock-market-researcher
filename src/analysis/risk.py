"""Stock risk and drawdown analysis module.

Provides functions for calculating annualized volatility, maximum drawdown,
drawdown duration, peak/trough dates, downside risk, and risk-adjusted metrics.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.analysis.returns import TRADING_DAYS_PER_YEAR, calculate_daily_returns


@dataclass(frozen=True)
class RiskMetrics:
    """Summary of factual risk and volatility measurements."""

    annualized_volatility: float  # std(daily) * sqrt(252)
    daily_volatility: float
    downside_deviation: float  # semi-deviation below 0 or MAR
    max_drawdown: float  # Minimum drawdown (negative decimal, e.g. -0.25 for -25%)
    max_drawdown_peak_date: str
    max_drawdown_trough_date: str
    max_drawdown_recovery_date: Optional[str]
    max_drawdown_duration_days: int  # Calendar days between peak and trough/recovery
    sharpe_ratio: float  # (Annualized Return - rf) / Annualized Volatility
    sortino_ratio: float  # (Annualized Return - rf) / Downside Deviation
    var_95: float  # 95% 1-day Value at Risk (historical percentile)
    cvar_95: float  # 95% 1-day Conditional Value at Risk (Expected Shortfall)


def calculate_drawdown_series(
    prices_or_returns: Union[pd.Series, pd.DataFrame],
    price_col: str = "adjusted_close",
) -> Tuple[pd.Series, pd.Series]:
    """Calculate the cumulative peak (high-water mark) and drawdown series.
    
    Drawdown is defined as: (Price_t - Peak_t) / Peak_t.
    
    Args:
        prices_or_returns: Series or DataFrame of prices (or cumulative returns).
        price_col: Column name to use if a DataFrame is passed.
        
    Returns:
        Tuple of (running_peak_series, drawdown_series).
    """
    if isinstance(prices_or_returns, pd.DataFrame):
        target = price_col if price_col in prices_or_returns.columns else "close"
        prices = prices_or_returns[target].dropna()
    elif isinstance(prices_or_returns, pd.Series):
        prices = prices_or_returns.dropna()
    else:
        raise TypeError("Input must be a pandas Series or DataFrame.")

    if prices.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    running_peak = prices.cummax()
    drawdown = (prices - running_peak) / running_peak
    drawdown.name = "drawdown"
    running_peak.name = "running_peak"

    return running_peak, drawdown


def calculate_risk_metrics(
    df_or_prices: Union[pd.DataFrame, pd.Series],
    risk_free_rate: float = 0.0,
    price_col: str = "adjusted_close",
) -> RiskMetrics:
    """Calculate risk and drawdown metrics for the given price series.
    
    Args:
        df_or_prices: Price Series or DataFrame.
        risk_free_rate: Annualized risk-free rate (e.g. 0.04 for 4%, default 0.0).
        price_col: Column name to use for price data.
        
    Returns:
        RiskMetrics dataclass with computed metrics.
    """
    if isinstance(df_or_prices, pd.DataFrame):
        target_col = price_col if price_col in df_or_prices.columns else "close"
        prices = df_or_prices[target_col].dropna()
    elif isinstance(df_or_prices, pd.Series):
        prices = df_or_prices.dropna()
    else:
        raise TypeError("Input must be a pandas Series or DataFrame.")

    if len(prices) < 2:
        raise ValueError(f"At least 2 price observations required to compute risk, got {len(prices)}.")

    daily_returns = prices.pct_change().dropna()
    n_days = len(prices)

    # Volatility
    daily_vol = float(daily_returns.std(ddof=1)) if len(daily_returns) > 1 else 0.0
    annualized_vol = daily_vol * np.sqrt(TRADING_DAYS_PER_YEAR)

    # Downside deviation (semi-deviation for returns < 0)
    negative_returns = daily_returns[daily_returns < 0]
    if len(negative_returns) > 0:
        downside_std_daily = np.sqrt(np.mean(negative_returns ** 2))
        downside_deviation = float(downside_std_daily * np.sqrt(TRADING_DAYS_PER_YEAR))
    else:
        downside_deviation = 0.0

    # Drawdown calculations
    running_peak, drawdown = calculate_drawdown_series(prices)
    max_dd = float(drawdown.min())
    trough_date_idx = drawdown.idxmin()
    trough_date_str = str(trough_date_idx)[:10]

    # Find the peak prior to the trough
    prior_prices = prices.loc[:trough_date_idx]
    peak_date_idx = prior_prices.idxmax()
    peak_date_str = str(peak_date_idx)[:10]
    peak_price = prices.loc[peak_date_idx]

    # Find recovery date if any (first date after trough where price >= peak_price)
    post_trough_prices = prices.loc[trough_date_idx:]
    recovered_slice = post_trough_prices[post_trough_prices >= peak_price]
    if not recovered_slice.empty and len(recovered_slice) > 1:
        # First date strictly after trough that matches or exceeds peak
        rec_date_idx = recovered_slice.index[recovered_slice.index > trough_date_idx]
        if not rec_date_idx.empty:
            rec_date_str: Optional[str] = str(rec_date_idx[0])[:10]
            end_duration_dt = rec_date_idx[0]
        else:
            rec_date_str = None
            end_duration_dt = prices.index[-1]
    else:
        rec_date_str = None
        end_duration_dt = prices.index[-1]

    # Duration from peak to trough/recovery
    try:
        duration_days = int((pd.to_datetime(end_duration_dt) - pd.to_datetime(peak_date_idx)).days)
    except Exception:
        duration_days = 0

    # Annualized Return for Sharpe & Sortino calculation
    trading_years = (n_days - 1) / TRADING_DAYS_PER_YEAR
    start_price = float(prices.iloc[0])
    end_price = float(prices.iloc[-1])
    if trading_years > 0 and start_price > 0 and end_price > 0:
        cagr = (end_price / start_price) ** (1.0 / trading_years) - 1.0
    else:
        cagr = (end_price - start_price) / start_price if start_price > 0 else 0.0

    # Sharpe ratio
    sharpe = (cagr - risk_free_rate) / annualized_vol if annualized_vol > 0 else 0.0

    # Sortino ratio
    sortino = (cagr - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0.0

    # Value at Risk (Historical 95% 1-day)
    # 5th percentile of daily returns
    var_95 = float(np.percentile(daily_returns, 5))
    tail_returns = daily_returns[daily_returns <= var_95]
    cvar_95 = float(tail_returns.mean()) if not tail_returns.empty else var_95

    return RiskMetrics(
        annualized_volatility=annualized_vol,
        daily_volatility=daily_vol,
        downside_deviation=downside_deviation,
        max_drawdown=max_dd,
        max_drawdown_peak_date=peak_date_str,
        max_drawdown_trough_date=trough_date_str,
        max_drawdown_recovery_date=rec_date_str,
        max_drawdown_duration_days=duration_days,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        var_95=var_95,
        cvar_95=cvar_95,
    )
