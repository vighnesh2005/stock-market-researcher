"""Tests for return analysis calculations."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.returns import (
    ReturnMetrics,
    calculate_cumulative_returns,
    calculate_daily_returns,
    calculate_return_metrics,
)


def test_calculate_daily_returns(sample_price_series):
    """Test daily percentage returns calculation."""
    daily_ret = calculate_daily_returns(sample_price_series)
    
    assert len(daily_ret) == len(sample_price_series) - 1
    # Day 1: (105 - 100) / 100 = +0.05
    assert pytest.approx(daily_ret.iloc[0], rel=1e-5) == 0.05
    # Day 2: (99.75 - 105) / 105 = -0.05
    assert pytest.approx(daily_ret.iloc[1], rel=1e-5) == -0.05
    # Day 3: (104.7375 - 99.75) / 99.75 = +0.05
    assert pytest.approx(daily_ret.iloc[2], rel=1e-5) == 0.05
    # Day 4: (115.21125 - 104.7375) / 104.7375 = +0.10
    assert pytest.approx(daily_ret.iloc[3], rel=1e-5) == 0.10


def test_calculate_cumulative_returns(sample_price_series):
    """Test cumulative return series calculation."""
    cum_ret = calculate_cumulative_returns(sample_price_series)
    
    # Base date cumulative return should be 0.0
    assert pytest.approx(cum_ret.iloc[0]) == 0.0
    # Day 1: 105 / 100 - 1 = +0.05
    assert pytest.approx(cum_ret.iloc[1]) == 0.05
    # Day 2: 99.75 / 100 - 1 = -0.0025
    assert pytest.approx(cum_ret.iloc[2]) == -0.0025
    # Final Day: 115.21125 / 100 - 1 = +0.1521125
    assert pytest.approx(cum_ret.iloc[-1]) == 0.1521125


def test_calculate_return_metrics(sample_ohlcv_dataframe):
    """Test complete ReturnMetrics computation."""
    metrics: ReturnMetrics = calculate_return_metrics(sample_ohlcv_dataframe)
    
    assert metrics.total_trading_days == 5
    assert metrics.start_price == 100.0
    assert pytest.approx(metrics.end_price) == 115.21125
    assert pytest.approx(metrics.cumulative_return) == 0.1521125
    assert pytest.approx(metrics.best_day_return) == 0.10
    assert pytest.approx(metrics.worst_day_return) == -0.05
    assert metrics.positive_days_count == 3
    assert metrics.negative_days_count == 1
    assert pytest.approx(metrics.positive_days_ratio) == 75.0  # 3 of 4 return days


def test_returns_single_observation_raises_error():
    """Test that calculating returns on < 2 observations raises ValueError."""
    single_series = pd.Series([100.0], index=[pd.Timestamp("2024-01-01")])
    with pytest.raises(ValueError, match="At least 2 price observations"):
        calculate_return_metrics(single_series)
