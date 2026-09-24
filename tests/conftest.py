"""Deterministic test fixtures for Stock Market Researcher test suite."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_price_series() -> pd.Series:
    """Deterministic price series for mathematical verification.
    
    Prices: [100.0, 105.0, 99.75, 104.7375, 115.21125]
    Daily Returns:
      Day 1: +5.0% (+0.05)
      Day 2: -5.0% (-0.05)
      Day 3: +5.0% (+0.05)
      Day 4: +10.0% (+0.10)
    """
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    prices = [100.0, 105.0, 99.75, 104.7375, 115.21125]
    return pd.Series(prices, index=dates, name="adjusted_close")


@pytest.fixture
def sample_ohlcv_dataframe(sample_price_series) -> pd.DataFrame:
    """Deterministic DataFrame matching standard OHLCV schema."""
    dates = sample_price_series.index
    df = pd.DataFrame(
        {
            "open": sample_price_series.values * 0.99,
            "high": sample_price_series.values * 1.02,
            "low": sample_price_series.values * 0.98,
            "close": sample_price_series.values,
            "adjusted_close": sample_price_series.values,
            "volume": [10000, 12000, 15000, 11000, 14000],
            "currency": ["USD"] * len(dates),
        },
        index=dates,
    )
    df.attrs["symbol"] = "TEST"
    df.attrs["company_name"] = "Test Corp"
    df.attrs["sector"] = "Technology"
    df.attrs["exchange"] = "TEST-EX"
    df.attrs["market"] = "US"
    df.attrs["currency"] = "USD"
    return df


@pytest.fixture
def sample_drawdown_series() -> pd.Series:
    """Deterministic series with clear peak, trough, and recovery.
    
    Day 0: 100.0 (initial)
    Day 1: 120.0 (peak)
    Day 2: 90.0 (trough, DD = (90-120)/120 = -25%)
    Day 3: 110.0 (rebound)
    Day 4: 125.0 (recovery, price > peak)
    """
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    prices = [100.0, 120.0, 90.0, 110.0, 125.0]
    return pd.Series(prices, index=dates, name="adjusted_close")


@pytest.fixture
def long_price_dataframe() -> pd.DataFrame:
    """Deterministic 250-day price history for moving average tests."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=250, freq="B")
    # Generate geometric Brownian motion
    returns = np.random.normal(0.0005, 0.015, size=250)
    prices = 100.0 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame(
        {
            "open": prices * 0.995,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "adjusted_close": prices,
            "volume": np.random.randint(100000, 500000, size=250),
            "currency": ["USD"] * 250,
        },
        index=dates,
    )
    df.attrs["symbol"] = "LONGSYM"
    df.attrs["company_name"] = "Long History Corp"
    df.attrs["sector"] = "Finance"
    df.attrs["exchange"] = "NYSE"
    df.attrs["market"] = "US"
    return df
