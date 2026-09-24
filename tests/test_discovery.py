"""Tests for stock data discovery module."""

from pathlib import Path
import pytest
from src.data.discovery import StockCatalog, StockMetadata


def test_stock_catalog_loads_upstream():
    """Test that default StockCatalog successfully discovers stocks from vendor submodule."""
    catalog = StockCatalog()
    stocks = catalog.list_stocks()
    assert len(stocks) > 0, "Stock catalog should discover stocks from vendor submodule"

    # Test US stocks exist
    us_stocks = catalog.list_stocks(market="US")
    assert len(us_stocks) >= 500

    # Test Indian stocks exist
    ind_stocks = catalog.list_stocks(market="IND")
    assert len(ind_stocks) >= 500


def test_catalog_metadata_retrieval():
    """Test retrieving metadata by ticker symbol."""
    catalog = StockCatalog()
    
    aapl = catalog.get_stock_metadata("AAPL")
    assert aapl is not None
    assert aapl.symbol == "AAPL"
    assert aapl.company_name == "Apple"
    assert aapl.market == "US"
    assert aapl.exchange in ["NASDAQ", "NYSE"]
    assert Path(aapl.file_path).exists()

    abb = catalog.get_stock_metadata("ABB", market="IND")
    assert abb is not None
    assert abb.symbol == "ABB"
    assert abb.market == "IND"
    assert Path(abb.file_path).exists()


def test_catalog_search():
    """Test searching stocks by substring."""
    catalog = StockCatalog()
    
    results = catalog.search_stocks("Apple")
    symbols = [s.symbol for s in results]
    assert "AAPL" in symbols

    # Search by sector
    tech_stocks = catalog.search_stocks("Technology", market="US")
    assert len(tech_stocks) > 0
    assert all(
        "technology" in (s.sector.lower() + " " + s.company_name.lower() + " " + s.symbol.lower())
        for s in tech_stocks
    )


def test_catalog_unknown_symbol():
    """Test querying non-existent ticker returns None."""
    catalog = StockCatalog()
    assert catalog.get_stock_metadata("NON_EXISTENT_XYZ_123") is None
