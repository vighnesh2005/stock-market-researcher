"""Tests for risk, volatility, and drawdown calculations."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.returns import TRADING_DAYS_PER_YEAR
from src.analysis.risk import (
    RiskMetrics,
    calculate_drawdown_series,
    calculate_risk_metrics,
)


def test_drawdown_calculation(sample_drawdown_series):
    """Test drawdown calculation and peak/trough identification.
    
    Prices: [100.0, 120.0, 90.0, 110.0, 125.0]
    Peaks:  [100.0, 120.0, 120.0, 120.0, 125.0]
    DD:     [0.0,   0.0,   (90-120)/120 = -0.25, (110-120)/120 = -0.0833, 0.0]
    """
    peaks, dd = calculate_drawdown_series(sample_drawdown_series)
    
    assert pytest.approx(peaks.iloc[1]) == 120.0
    assert pytest.approx(dd.iloc[2]) == -0.25
    assert pytest.approx(dd.min()) == -0.25
    assert pytest.approx(dd.iloc[4]) == 0.0


def test_risk_metrics_computation(sample_drawdown_series):
    """Test RiskMetrics dataclass calculation with exact numbers."""
    risk: RiskMetrics = calculate_risk_metrics(sample_drawdown_series, risk_free_rate=0.0)
    
    assert pytest.approx(risk.max_drawdown) == -0.25
    assert risk.max_drawdown_peak_date == "2024-01-02"  # 120.0 date
    assert risk.max_drawdown_trough_date == "2024-01-03"  # 90.0 date
    assert risk.max_drawdown_recovery_date == "2024-01-05"  # 125.0 date
    assert risk.annualized_volatility > 0.0
    assert risk.downside_deviation > 0.0
    assert risk.sharpe_ratio != 0.0


def test_volatility_annualization(sample_price_series):
    """Test that annualized volatility equals daily vol * sqrt(252)."""
    risk: RiskMetrics = calculate_risk_metrics(sample_price_series)
    expected_annual_vol = risk.daily_volatility * np.sqrt(TRADING_DAYS_PER_YEAR)
    assert pytest.approx(risk.annualized_volatility) == expected_annual_vol


def test_risk_metrics_too_few_points():
    """Test calculating risk on < 2 points raises ValueError."""
    s = pd.Series([100.0], index=[pd.Timestamp("2024-01-01")])
    with pytest.raises(ValueError, match="At least 2 price observations"):
        calculate_risk_metrics(s)
