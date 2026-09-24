"""Tests for technical indicators and moving averages."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.technical import (
    TechnicalSummary,
    add_technical_indicators,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_sma,
    calculate_technical_summary,
)


def test_calculate_sma():
    """Test Simple Moving Average calculation."""
    s = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    sma3 = calculate_sma(s, window=3)
    
    assert pd.isna(sma3.iloc[0])
    assert pd.isna(sma3.iloc[1])
    assert pytest.approx(sma3.iloc[2]) == 20.0  # (10 + 20 + 30) / 3
    assert pytest.approx(sma3.iloc[3]) == 30.0  # (20 + 30 + 40) / 3
    assert pytest.approx(sma3.iloc[4]) == 40.0  # (30 + 40 + 50) / 3


def test_calculate_ema():
    """Test Exponential Moving Average calculation."""
    s = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    ema = calculate_ema(s, span=3)
    assert not ema.empty
    assert pd.notna(ema.iloc[-1])


def test_calculate_bollinger_bands(long_price_dataframe):
    """Test Bollinger Bands bandwidth and bounds."""
    bb = calculate_bollinger_bands(long_price_dataframe["close"], window=20, num_std=2.0)
    
    assert "bb_middle" in bb.columns
    assert "bb_upper" in bb.columns
    assert "bb_lower" in bb.columns
    
    valid_bb = bb.dropna()
    assert (valid_bb["bb_upper"] >= valid_bb["bb_middle"]).all()
    assert (valid_bb["bb_middle"] >= valid_bb["bb_lower"]).all()


def test_technical_summary(long_price_dataframe):
    """Test TechnicalSummary generation on 250-day dataset."""
    ts: TechnicalSummary = calculate_technical_summary(long_price_dataframe)
    
    assert ts.sma_20 is not None
    assert ts.sma_50 is not None
    assert ts.sma_200 is not None
    assert ts.sma50_vs_sma200 in ["ABOVE", "BELOW"]
    assert ts.bb_position_pct is not None
