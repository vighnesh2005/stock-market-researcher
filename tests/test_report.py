"""Tests for research report generation."""

from pathlib import Path
import pytest

from src.analysis.comparison import StockComparator
from src.summary.report import ResearchReportGenerator


def test_single_stock_markdown_report(sample_ohlcv_dataframe):
    """Test generating markdown report string."""
    report = ResearchReportGenerator.generate_single_stock_markdown(
        sample_ohlcv_dataframe, symbol="TEST"
    )
    assert "# Stock Research Summary: TEST" in report
    assert "Historical Price & Return Analysis" in report
    assert "Risk & Volatility Analysis" in report
    assert "Technical Indicator Status" in report
    assert "ankit02327/stock-price" in report
    assert "Disclaimer" in report


def test_single_stock_dict_report(sample_ohlcv_dataframe):
    """Test generating structured dictionary."""
    data = ResearchReportGenerator.generate_single_stock_dict(
        sample_ohlcv_dataframe, symbol="TEST"
    )
    assert data["metadata"]["symbol"] == "TEST"
    assert "cumulative_return" in data["returns"]
    assert "annualized_volatility" in data["risk"]
    assert "sma_20" in data["technical"]


def test_comparison_markdown_report(sample_ohlcv_dataframe):
    """Test generating comparison markdown report."""
    df2 = sample_ohlcv_dataframe.copy()
    df2["adjusted_close"] = df2["adjusted_close"] * 1.2
    comp = StockComparator({"STOCK1": sample_ohlcv_dataframe, "STOCK2": df2}).compare()

    report = ResearchReportGenerator.generate_comparison_markdown(comp)
    assert "# Multi-Stock Comparative Research Summary" in report
    assert "STOCK1" in report
    assert "STOCK2" in report
