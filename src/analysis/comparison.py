"""Stock comparison and correlation analysis module.

Allows multi-stock comparative analysis, returns alignment, risk-return trade-offs,
and daily returns correlation matrices.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd

from src.analysis.returns import calculate_daily_returns, calculate_return_metrics, ReturnMetrics
from src.analysis.risk import calculate_risk_metrics, RiskMetrics


@dataclass(frozen=True)
class StockComparisonResult:
    """Consolidated comparative analysis result for multiple stocks."""

    symbols: List[str]
    common_start_date: str
    common_end_date: str
    common_trading_days: int
    comparison_table: pd.DataFrame
    correlation_matrix: pd.DataFrame
    cumulative_returns_df: pd.DataFrame


class StockComparator:
    """Compares multiple stocks over synchronized historical time horizons."""

    def __init__(self, stock_dfs: Dict[str, pd.DataFrame], price_col: str = "adjusted_close"):
        """Initialize comparator with a dictionary mapping symbol -> DataFrame.
        
        Args:
            stock_dfs: Dictionary of {symbol: price_df}.
            price_col: Column to use for calculations.
        """
        if len(stock_dfs) < 2:
            raise ValueError("At least 2 stock DataFrames are required for comparison.")

        self.price_col = price_col
        self.raw_dfs = stock_dfs
        self.symbols = list(stock_dfs.keys())

    def align_data(self) -> pd.DataFrame:
        """Extract prices for all stocks and align on common trading dates (inner join).
        
        Returns:
            DataFrame of adjusted close prices indexed by DatetimeIndex with columns as symbols.
        """
        price_series_dict = {}
        for sym, df in self.raw_dfs.items():
            col = self.price_col if self.price_col in df.columns else "close"
            price_series_dict[sym] = df[col].dropna()

        aligned_prices = pd.DataFrame(price_series_dict).dropna()
        if len(aligned_prices) < 2:
            raise ValueError(
                "Insufficient overlapping trading dates between selected stocks to perform comparison."
            )
        return aligned_prices

    def compare(self, risk_free_rate: float = 0.0) -> StockComparisonResult:
        """Run comprehensive multi-stock factual comparison.
        
        Args:
            risk_free_rate: Risk-free rate for Sharpe / Sortino calculations.
            
        Returns:
            StockComparisonResult dataclass.
        """
        aligned_prices = self.align_data()
        start_date = str(aligned_prices.index[0])[:10]
        end_date = str(aligned_prices.index[-1])[:10]
        n_days = len(aligned_prices)

        # Compute aligned daily returns
        daily_returns_df = aligned_prices.pct_change().dropna()
        correlation_matrix = daily_returns_df.corr()

        # Compute normalized cumulative returns (starting at 0.0)
        cum_returns_df = (aligned_prices / aligned_prices.iloc[0]) - 1.0

        records = []
        for sym in self.symbols:
            s_prices = aligned_prices[sym]
            ret_metrics: ReturnMetrics = calculate_return_metrics(s_prices)
            risk_metrics: RiskMetrics = calculate_risk_metrics(s_prices, risk_free_rate=risk_free_rate)

            # Retrieve optional sector/market info from attrs if available
            orig_df = self.raw_dfs.get(sym)
            market = orig_df.attrs.get("market", "") if orig_df is not None else ""
            sector = orig_df.attrs.get("sector", "") if orig_df is not None else ""
            currency = orig_df.attrs.get("currency", "") if orig_df is not None else ""

            records.append(
                {
                    "Symbol": sym,
                    "Market": market,
                    "Sector": sector,
                    "Currency": currency,
                    "Start Price": ret_metrics.start_price,
                    "End Price": ret_metrics.end_price,
                    "Cumulative Return (%)": ret_metrics.cumulative_return * 100.0,
                    "Annualized Return CAGR (%)": ret_metrics.cagr * 100.0,
                    "Annualized Volatility (%)": risk_metrics.annualized_volatility * 100.0,
                    "Sharpe Ratio": risk_metrics.sharpe_ratio,
                    "Sortino Ratio": risk_metrics.sortino_ratio,
                    "Max Drawdown (%)": risk_metrics.max_drawdown * 100.0,
                    "Max DD Peak Date": risk_metrics.max_drawdown_peak_date,
                    "Max DD Trough Date": risk_metrics.max_drawdown_trough_date,
                    "Positive Days (%)": ret_metrics.positive_days_ratio,
                }
            )

        comp_df = pd.DataFrame(records).set_index("Symbol")

        return StockComparisonResult(
            symbols=self.symbols,
            common_start_date=start_date,
            common_end_date=end_date,
            common_trading_days=n_days,
            comparison_table=comp_df,
            correlation_matrix=correlation_matrix,
            cumulative_returns_df=cum_returns_df,
        )
