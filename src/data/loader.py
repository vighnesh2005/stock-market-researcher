"""Stock data loader module.

Loads, validates, and cleans historical time-series datasets
for downstream market analysis.
"""

from pathlib import Path
from typing import List, Optional, Union
import pandas as pd

from src.data.discovery import StockCatalog, StockMetadata


REQUIRED_COLUMNS: List[str] = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "adjusted_close",
    "currency",
]


class StockDataLoader:
    """Loads and preprocesses historical stock price datasets."""

    def __init__(self, catalog: Optional[StockCatalog] = None):
        """Initialize loader with a stock catalog.
        
        Args:
            catalog: Instance of StockCatalog. If None, initializes a default catalog.
        """
        self.catalog = catalog or StockCatalog()

    def load_from_file(
        self,
        file_path: Union[str, Path],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Load and validate stock data directly from a CSV file path.
        
        Args:
            file_path: Absolute or relative path to the stock CSV.
            start_date: Optional start date filter (inclusive, format 'YYYY-MM-DD').
            end_date: Optional end date filter (inclusive, format 'YYYY-MM-DD').
            
        Returns:
            Cleaned pandas DataFrame indexed by DatetimeIndex.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If required columns are missing or data is invalid.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Stock data file not found at: {path}")

        try:
            df = pd.read_csv(path)
        except Exception as e:
            raise ValueError(f"Failed to read CSV at {path}: {e}") from e

        # Validate required columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Dataset at {path} is missing required columns: {missing_cols}. "
                f"Expected columns: {REQUIRED_COLUMNS}"
            )

        if df.empty:
            raise ValueError(f"Dataset at {path} is empty.")

        # Standardize date column and handle timezones
        try:
            df["date"] = pd.to_datetime(df["date"], utc=True)
            # Normalize to date level tz-naive
            df["date"] = df["date"].dt.tz_localize(None).dt.floor("D")
        except Exception as e:
            raise ValueError(f"Failed to parse 'date' column in {path}: {e}") from e

        # Sort chronologically and drop duplicate dates if any
        df = df.sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)

        # Set DatetimeIndex
        df = df.set_index("date")

        # Validate numeric price/volume columns
        numeric_cols = ["open", "high", "low", "close", "adjusted_close", "volume"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop rows where essential prices are NaN
        df = df.dropna(subset=["close", "adjusted_close"])

        if df.empty:
            raise ValueError(f"Dataset at {path} contains no valid numeric price data.")

        # Date range filtering
        if start_date:
            try:
                start_dt = pd.to_datetime(start_date)
                df = df[df.index >= start_dt]
            except Exception as e:
                raise ValueError(f"Invalid start_date '{start_date}': {e}") from e

        if end_date:
            try:
                end_dt = pd.to_datetime(end_date)
                df = df[df.index <= end_dt]
            except Exception as e:
                raise ValueError(f"Invalid end_date '{end_date}': {e}") from e

        if df.empty:
            raise ValueError(
                f"No data available for {path.name} in the specified date range "
                f"({start_date} to {end_date})."
            )

        return df

    def load_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        market: Optional[str] = None,
    ) -> pd.DataFrame:
        """Load stock price history by symbol from discovered catalog.
        
        Args:
            symbol: Ticker symbol (e.g. 'AAPL', 'INFY', 'TCS').
            start_date: Optional 'YYYY-MM-DD' filter.
            end_date: Optional 'YYYY-MM-DD' filter.
            market: Optional 'US' or 'IND' market filter.
            
        Returns:
            Cleaned pandas DataFrame indexed by DatetimeIndex.
            
        Raises:
            KeyError: If the stock symbol is not found in the catalog.
            ValueError: If parameters or loaded data are invalid.
        """
        meta: Optional[StockMetadata] = self.catalog.get_stock_metadata(symbol, market=market)
        if meta is None:
            available_examples = [s.symbol for s in self.catalog.list_stocks(market=market)[:10]]
            raise KeyError(
                f"Stock symbol '{symbol}' not found in catalog (market={market or 'all'}). "
                f"Examples of available symbols: {', '.join(available_examples)}..."
            )

        df = self.load_from_file(meta.file_path, start_date=start_date, end_date=end_date)
        # Store metadata attributes in df.attrs for convenient reference
        df.attrs["symbol"] = meta.symbol
        df.attrs["company_name"] = meta.company_name
        df.attrs["sector"] = meta.sector
        df.attrs["exchange"] = meta.exchange
        df.attrs["market"] = meta.market
        df.attrs["currency"] = df["currency"].iloc[0] if "currency" in df.columns else "USD"

        return df
