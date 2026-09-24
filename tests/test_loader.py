"""Tests for stock data loading and validation module."""

from pathlib import Path
import pandas as pd
import pytest

from src.data.loader import StockDataLoader, REQUIRED_COLUMNS


def test_loader_load_valid_stock():
    """Test loading historical data for AAPL from upstream submodule."""
    loader = StockDataLoader()
    df = loader.load_stock_data("AAPL")
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert isinstance(df.index, pd.DatetimeIndex)
    assert "close" in df.columns
    assert "adjusted_close" in df.columns
    assert df.attrs.get("symbol") == "AAPL"


def test_loader_date_filtering():
    """Test start_date and end_date filtering."""
    loader = StockDataLoader()
    start = "2021-01-01"
    end = "2022-12-31"
    df = loader.load_stock_data("AAPL", start_date=start, end_date=end)
    
    assert str(df.index[0])[:10] >= start
    assert str(df.index[-1])[:10] <= end


def test_loader_missing_symbol_raises_keyerror():
    """Test requesting invalid symbol raises descriptive KeyError."""
    loader = StockDataLoader()
    with pytest.raises(KeyError, match="not found in catalog"):
        loader.load_stock_data("TOTALLY_UNKNOWN_SYMBOL_999")


def test_loader_missing_columns_validation(tmp_path):
    """Test that CSV missing required columns raises ValueError."""
    bad_csv = tmp_path / "bad.csv"
    bad_df = pd.DataFrame({"date": ["2020-01-01"], "some_column": [123]})
    bad_df.to_csv(bad_csv, index=False)

    loader = StockDataLoader()
    with pytest.raises(ValueError, match="missing required columns"):
        loader.load_from_file(bad_csv)


def test_loader_empty_csv_validation(tmp_path):
    """Test that empty CSV raises ValueError."""
    empty_csv = tmp_path / "empty.csv"
    pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(empty_csv, index=False)

    loader = StockDataLoader()
    with pytest.raises(ValueError, match="empty"):
        loader.load_from_file(empty_csv)


def test_loader_file_not_found():
    """Test non-existent file path raises FileNotFoundError."""
    loader = StockDataLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_from_file(Path("non_existent_file_path_xyz.csv"))
