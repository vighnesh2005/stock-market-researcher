"""Stock data discovery module.

Discovers available stock datasets and metadata from the upstream
`vendor/stock-price/permanent` repository resources.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


@dataclass(frozen=True)
class StockMetadata:
    """Metadata for a discovered stock."""

    symbol: str
    company_name: str
    sector: str
    market_cap: Optional[str]
    headquarters: Optional[str]
    exchange: str
    market: str  # e.g., 'US' or 'IND'
    file_path: Path


class StockCatalog:
    """Catalog for discovering and querying available stock datasets.
    
    Reads metadata from upstream index files and matches them against
    available individual CSV time series in the submodule.
    """

    def __init__(self, vendor_root: Optional[Path] = None):
        """Initialize the stock catalog.
        
        Args:
            vendor_root: Path to vendor directory. If None, resolves relative to project root.
        """
        if vendor_root is None:
            # Default to repo root / vendor / stock-price
            self.vendor_root = Path(__file__).resolve().parent.parent.parent / "vendor" / "stock-price"
        else:
            self.vendor_root = Path(vendor_root)

        self.permanent_dir = self.vendor_root / "permanent"
        self._stocks: Dict[str, StockMetadata] = {}
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Scan permanent stock directories and index CSVs."""
        self._stocks.clear()
        
        market_configs = [
            {
                "market": "US",
                "index_file": self.permanent_dir / "us_stocks" / "index_us_stocks.csv",
                "files_dir": self.permanent_dir / "us_stocks" / "individual_files",
            },
            {
                "market": "IND",
                "index_file": self.permanent_dir / "ind_stocks" / "index_ind_stocks.csv",
                "files_dir": self.permanent_dir / "ind_stocks" / "individual_files",
            },
        ]

        for config in market_configs:
            market = config["market"]
            index_path: Path = config["index_file"]
            files_dir: Path = config["files_dir"]

            if not index_path.exists():
                continue

            try:
                df = pd.read_csv(index_path)
            except Exception:
                continue

            for _, row in df.iterrows():
                symbol = str(row.get("symbol", "")).strip().upper()
                if not symbol:
                    continue

                csv_file = files_dir / f"{symbol}.csv"
                if not csv_file.exists():
                    # Check case-insensitive if file exists
                    found = list(files_dir.glob(f"{symbol}.[cC][sS][vV]"))
                    if found:
                        csv_file = found[0]
                    else:
                        continue

                company_name = str(row.get("company_name", symbol))
                sector = str(row.get("sector", "Unknown"))
                market_cap = str(row.get("market_cap", "")) if pd.notna(row.get("market_cap")) else None
                headquarters = str(row.get("headquarters", "")) if pd.notna(row.get("headquarters")) else None
                exchange = str(row.get("exchange", "Unknown"))

                metadata = StockMetadata(
                    symbol=symbol,
                    company_name=company_name,
                    sector=sector,
                    market_cap=market_cap,
                    headquarters=headquarters,
                    exchange=exchange,
                    market=market,
                    file_path=csv_file,
                )
                
                # Store with market prefix if collision, or standard key
                key = f"{market}:{symbol}"
                self._stocks[key] = metadata
                # Also store by pure symbol if not already present
                if symbol not in self._stocks:
                    self._stocks[symbol] = metadata

    def list_stocks(self, market: Optional[str] = None) -> List[StockMetadata]:
        """List all discovered unique stocks, optionally filtered by market.
        
        Args:
            market: 'US' or 'IND' (case-insensitive). If None, returns all stocks.
            
        Returns:
            List of StockMetadata objects sorted by symbol.
        """
        seen_paths = set()
        result: List[StockMetadata] = []
        
        for meta in self._stocks.values():
            if meta.file_path in seen_paths:
                continue
            if market and meta.market.upper() != market.upper():
                continue
            seen_paths.add(meta.file_path)
            result.append(meta)

        return sorted(result, key=lambda s: s.symbol)

    def search_stocks(self, query: str, market: Optional[str] = None) -> List[StockMetadata]:
        """Search stocks by symbol, company name, or sector.
        
        Args:
            query: Substring to search for.
            market: Optional market filter ('US' or 'IND').
            
        Returns:
            List of matching StockMetadata objects.
        """
        q = query.strip().lower()
        if not q:
            return self.list_stocks(market=market)

        stocks = self.list_stocks(market=market)
        matches = []
        for stock in stocks:
            if (
                q in stock.symbol.lower()
                or q in stock.company_name.lower()
                or q in stock.sector.lower()
                or q in stock.exchange.lower()
            ):
                matches.append(stock)

        return matches

    def get_stock_metadata(self, symbol: str, market: Optional[str] = None) -> Optional[StockMetadata]:
        """Retrieve metadata for a specific stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'ABB', 'US:AAPL').
            market: Optional market filter ('US' or 'IND').
            
        Returns:
            StockMetadata if found, else None.
        """
        sym = symbol.strip().upper()
        if market:
            key = f"{market.upper()}:{sym}"
            if key in self._stocks:
                return self._stocks[key]

        if sym in self._stocks:
            return self._stocks[sym]

        # Look up by symbol across unique items
        for meta in self.list_stocks(market=market):
            if meta.symbol == sym:
                return meta
        return None

    def list_sectors(self, market: Optional[str] = None) -> List[str]:
        """List all unique sectors available in the catalog."""
        sectors = {s.sector for s in self.list_stocks(market=market) if s.sector and s.sector != "Unknown"}
        return sorted(sectors)
