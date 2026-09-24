"""Tests for multi-stock comparison and correlation."""

import pandas as pd
import pytest

from src.analysis.comparison import StockComparator, StockComparisonResult


def test_stock_comparator_basic(sample_ohlcv_dataframe):
    """Test comparing two stocks with known returns."""
    df1 = sample_ohlcv_dataframe.copy()
    # Create second dataframe with 2x returns
    df2 = sample_ohlcv_dataframe.copy()
    df2["adjusted_close"] = df2["adjusted_close"] * 1.5

    comparator = StockComparator({"STOCK1": df1, "STOCK2": df2})
    result: StockComparisonResult = comparator.compare()

    assert len(result.symbols) == 2
    assert "STOCK1" in result.symbols
    assert "STOCK2" in result.symbols
    assert result.common_trading_days == 5
    assert not result.comparison_table.empty
    assert result.correlation_matrix.shape == (2, 2)
    assert pytest.approx(result.correlation_matrix.loc["STOCK1", "STOCK2"]) == 1.0


def test_stock_comparator_fewer_than_two_raises():
    """Test that providing less than 2 stocks raises ValueError."""
    with pytest.raises(ValueError, match="At least 2 stock DataFrames"):
        StockComparator({"ONLY_ONE": pd.DataFrame({"adjusted_close": [10, 20]})})
