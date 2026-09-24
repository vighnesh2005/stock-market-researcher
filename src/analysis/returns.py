"""Stock return calculation and analysis module.

Provides functions and data structures for calculating daily returns,
cumulative returns, annualized returns (CAGR), and periodic performance statistics.
"""

from dataclasses import dataclass
from typing import Optional, Union
import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class ReturnMetrics:
    """Summary of factual return measurements over a time horizon."""

    start_date: str
    end_date: str
    total_trading_days: int
    start_price: float
    end_price: float
    cumulative_return: float  # Total return over period: (P_end - P_start) / P_start
    cagr: float  # Compound Annual Growth Rate
    mean_daily_return: float
    annualized_mean_return: float
    daily_volatility: float
    best_day_return: float
    best_day_date: str
    worst_day_return: float
    worst_day_date: str
    positive_days_count: int
    negative_days_count: int
    positive_days_ratio: float  # Percentage of days with positive return


def calculate_daily_returns(
    prices: Union[pd.Series, pd.DataFrame],
    price_col: str = "adjusted_close",
) -> pd.Series:
    """Calculate simple percentage daily returns: (P_t - P_{t-1}) / P_{t-1}.
    
    Args:
        prices: Price Series or DataFrame containing price history.
        price_col: Column name to use if a DataFrame is provided.
        
    Returns:
        pd.Series of daily percentage returns, with the first NaN dropped.
    """
    if isinstance(prices, pd.DataFrame):
        if price_col not in prices.columns:
            if "close" in prices.columns:
                series = prices["close"]
            else:
                raise ValueError(f"Column '{price_col}' not found in DataFrame.")
        else:
            series = prices[price_col]
    elif isinstance(prices, pd.Series):
        series = prices
    else:
        raise TypeError("Input must be a pandas Series or DataFrame.")

    if len(series) < 2:
        return pd.Series(dtype=float, index=series.index)

    returns = series.pct_change().dropna()
    returns.name = "daily_return"
    return returns


def calculate_cumulative_returns(
    daily_returns_or_prices: Union[pd.Series, pd.DataFrame],
    price_col: str = "adjusted_close",
) -> pd.Series:
    """Calculate cumulative returns series: (1 + r).cumprod() - 1 or (P_t - P_0) / P_0.
    
    Args:
        daily_returns_or_prices: Daily return series OR raw price DataFrame/Series.
        price_col: Column name if a DataFrame is passed.
        
    Returns:
        pd.Series of cumulative return (starts at 0.0 on base date).
    """
    if isinstance(daily_returns_or_prices, pd.DataFrame):
        price_series = daily_returns_or_prices[price_col] if price_col in daily_returns_or_prices.columns else daily_returns_or_prices["close"]
        if price_series.empty:
            return pd.Series(dtype=float)
        base_price = price_series.iloc[0]
        if base_price == 0:
            raise ValueError("Starting price is zero, cannot compute cumulative returns.")
        cum_ret = (price_series - base_price) / base_price
        cum_ret.name = "cumulative_return"
        return cum_ret

    series = daily_returns_or_prices
    if series.empty:
        return pd.Series(dtype=float)

    # Check if the series represents returns (mean around 0) or prices
    if (series < 0).any() or (series.max() < 2.0 and series.mean() < 0.1):
        # Likely daily returns
        cum_ret = (1.0 + series).cumprod() - 1.0
        cum_ret.name = "cumulative_return"
        return cum_ret
    else:
        # Price series
        base_price = series.iloc[0]
        if base_price == 0:
            raise ValueError("Starting price is zero, cannot compute cumulative returns.")
        cum_ret = (series - base_price) / base_price
        cum_ret.name = "cumulative_return"
        return cum_ret


def calculate_return_metrics(
    df_or_prices: Union[pd.DataFrame, pd.Series],
    price_col: str = "adjusted_close",
) -> ReturnMetrics:
    """Compute comprehensive factual return statistics over the provided history.
    
    Args:
        df_or_prices: DataFrame with price columns or price Series.
        price_col: Column name to use for price data (default 'adjusted_close').
        
    Returns:
        ReturnMetrics dataclass with computed metrics.
    """
    if isinstance(df_or_prices, pd.DataFrame):
        target_col = price_col if price_col in df_or_prices.columns else "close"
        if target_col not in df_or_prices.columns:
            raise ValueError(f"Neither '{price_col}' nor 'close' found in DataFrame.")
        prices = df_or_prices[target_col].dropna()
    elif isinstance(df_or_prices, pd.Series):
        prices = df_or_prices.dropna()
    else:
        raise TypeError("Input must be a pandas DataFrame or Series.")

    if len(prices) < 2:
        raise ValueError(f"At least 2 price observations required to compute returns, got {len(prices)}.")

    start_date_str = str(prices.index[0])[:10]
    end_date_str = str(prices.index[-1])[:10]
    n_days = len(prices)
    start_price = float(prices.iloc[0])
    end_price = float(prices.iloc[-1])

    if start_price <= 0:
        raise ValueError("Starting price must be positive.")

    daily_returns = prices.pct_change().dropna()
    cum_return = (end_price - start_price) / start_price

    # Compound Annual Growth Rate (CAGR)
    # Total trading years = (n_days - 1) / TRADING_DAYS_PER_YEAR
    trading_years = (n_days - 1) / TRADING_DAYS_PER_YEAR
    if trading_years > 0 and end_price > 0:
        cagr = (end_price / start_price) ** (1.0 / trading_years) - 1.0
    else:
        cagr = cum_return

    mean_daily = float(daily_returns.mean())
    annualized_mean = mean_daily * TRADING_DAYS_PER_YEAR
    daily_vol = float(daily_returns.std(ddof=1)) if len(daily_returns) > 1 else 0.0

    best_idx = daily_returns.idxmax()
    worst_idx = daily_returns.idxmin()
    best_return = float(daily_returns.loc[best_idx])
    worst_return = float(daily_returns.loc[worst_idx])
    best_date = str(best_idx)[:10]
    worst_date = str(worst_idx)[:10]

    pos_count = int((daily_returns > 0).sum())
    neg_count = int((daily_returns < 0).sum())
    pos_ratio = (pos_count / len(daily_returns)) * 100.0 if len(daily_returns) > 0 else 0.0

    return ReturnMetrics(
        start_date=start_date_str,
        end_date=end_date_str,
        total_trading_days=n_days,
        start_price=start_price,
        end_price=end_price,
        cumulative_return=cum_return,
        cagr=cagr,
        mean_daily_return=mean_daily,
        annualized_mean_return=annualized_mean,
        daily_volatility=daily_vol,
        best_day_return=best_return,
        best_day_date=best_date,
        worst_day_return=worst_return,
        worst_day_date=worst_date,
        positive_days_count=pos_count,
        negative_days_count=neg_count,
        positive_days_ratio=pos_ratio,
    )
