"""Automated factual research report generator.

Produces structured Markdown and Plain Text research summaries summarizing
returns, volatility, drawdowns, moving averages, and multi-stock comparisons.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Union
import json
import pandas as pd

from src.analysis.comparison import StockComparisonResult
from src.analysis.returns import ReturnMetrics, calculate_return_metrics
from src.analysis.risk import RiskMetrics, calculate_risk_metrics
from src.analysis.technical import TechnicalSummary, calculate_technical_summary
from src.data.discovery import StockMetadata


class ResearchReportGenerator:
    """Generates factual, objective stock market research reports."""

    @staticmethod
    def generate_single_stock_dict(
        df: pd.DataFrame,
        symbol: str,
        metadata: Optional[StockMetadata] = None,
        risk_free_rate: float = 0.0,
        price_col: str = "adjusted_close",
    ) -> Dict[str, Any]:
        """Compile complete factual measurements dictionary for a single stock."""
        target_col = price_col if price_col in df.columns else "close"
        ret_metrics: ReturnMetrics = calculate_return_metrics(df, price_col=target_col)
        risk_metrics: RiskMetrics = calculate_risk_metrics(df, risk_free_rate=risk_free_rate, price_col=target_col)
        tech_summary: TechnicalSummary = calculate_technical_summary(df, price_col=target_col)

        company_name = metadata.company_name if metadata else df.attrs.get("company_name", symbol)
        sector = metadata.sector if metadata else df.attrs.get("sector", "N/A")
        market = metadata.market if metadata else df.attrs.get("market", "N/A")
        exchange = metadata.exchange if metadata else df.attrs.get("exchange", "N/A")
        currency = df.attrs.get("currency", df["currency"].iloc[0] if "currency" in df.columns else "USD")

        # Period high and low
        high_price = float(df["high"].max()) if "high" in df.columns else float(df[target_col].max())
        low_price = float(df["low"].min()) if "low" in df.columns else float(df[target_col].min())

        return {
            "metadata": {
                "symbol": symbol,
                "company_name": company_name,
                "sector": sector,
                "market": market,
                "exchange": exchange,
                "currency": currency,
                "data_source": "ankit02327/stock-price (permanent dataset)",
            },
            "period": {
                "start_date": ret_metrics.start_date,
                "end_date": ret_metrics.end_date,
                "total_trading_days": ret_metrics.total_trading_days,
                "start_price": ret_metrics.start_price,
                "end_price": ret_metrics.end_price,
                "period_high": high_price,
                "period_low": low_price,
            },
            "returns": asdict(ret_metrics),
            "risk": asdict(risk_metrics),
            "technical": asdict(tech_summary),
        }

    @classmethod
    def generate_single_stock_markdown(
        cls,
        df: pd.DataFrame,
        symbol: str,
        metadata: Optional[StockMetadata] = None,
        risk_free_rate: float = 0.0,
        price_col: str = "adjusted_close",
    ) -> str:
        """Generate a structured Markdown research summary report."""
        data = cls.generate_single_stock_dict(
            df=df,
            symbol=symbol,
            metadata=metadata,
            risk_free_rate=risk_free_rate,
            price_col=price_col,
        )

        meta = data["metadata"]
        period = data["period"]
        ret = data["returns"]
        risk = data["risk"]
        tech = data["technical"]
        cur = meta["currency"]

        sma20_str = f"{cur} {tech['sma_20']:,.2f}" if tech["sma_20"] is not None else "N/A"
        sma50_str = f"{cur} {tech['sma_50']:,.2f}" if tech["sma_50"] is not None else "N/A"
        sma200_str = f"{cur} {tech['sma_200']:,.2f}" if tech["sma_200"] is not None else "N/A"
        ema20_str = f"{cur} {tech['ema_20']:,.2f}" if tech["ema_20"] is not None else "N/A"
        ema50_str = f"{cur} {tech['ema_50']:,.2f}" if tech["ema_50"] is not None else "N/A"

        p_sma20_str = f"{tech['price_to_sma20_pct']:+.2f}%" if tech["price_to_sma20_pct"] is not None else "N/A"
        p_sma50_str = f"{tech['price_to_sma50_pct']:+.2f}%" if tech["price_to_sma50_pct"] is not None else "N/A"
        p_sma200_str = f"{tech['price_to_sma200_pct']:+.2f}%" if tech["price_to_sma200_pct"] is not None else "N/A"

        bb_range_str = f"[{cur} {tech['bb_lower']:,.2f} to {cur} {tech['bb_upper']:,.2f}]" if tech["bb_upper"] is not None else "N/A"
        bb_pos_str = f"{tech['bb_position_pct']:.1f}% bandwidth position" if tech["bb_position_pct"] is not None else "N/A"

        align_desc = "N/A"
        if tech["sma50_vs_sma200"] == "ABOVE":
            align_desc = "Bullish alignment (SMA 50 >= SMA 200)"
        elif tech["sma50_vs_sma200"] == "BELOW":
            align_desc = "Bearish alignment (SMA 50 < SMA 200)"

        md_lines = [
            f"# Stock Research Summary: {meta['symbol']} ({meta['company_name']})",
            "",
            f"> **Data Source**: Historical permanent dataset from [`ankit02327/stock-price`](https://github.com/ankit02327/stock-price)",
            f"> **Generated Report Date**: {tech['latest_date']}",
            "",
            "## 1. Asset Profile",
            "",
            "| Property | Value |",
            "| :--- | :--- |",
            f"| **Symbol** | {meta['symbol']} |",
            f"| **Company** | {meta['company_name']} |",
            f"| **Sector** | {meta['sector']} |",
            f"| **Market / Exchange** | {meta['market']} ({meta['exchange']}) |",
            f"| **Currency** | {cur} |",
            f"| **Observed Period** | {period['start_date']} to {period['end_date']} ({period['total_trading_days']} trading days) |",
            "",
            "## 2. Historical Price & Return Analysis",
            "",
            "| Return Metric | Measurement | Description |",
            "| :--- | :--- | :--- |",
            f"| **Starting Price** | {cur} {period['start_price']:,.2f} | Price on {period['start_date']} |",
            f"| **Ending Price** | {cur} {period['end_price']:,.2f} | Price on {period['end_date']} |",
            f"| **Period Range (Low - High)** | {cur} {period['period_low']:,.2f} - {cur} {period['period_high']:,.2f} | Range of price observations |",
            f"| **Cumulative Return** | **{ret['cumulative_return'] * 100:+.2f}%** | Total return over entire period |",
            f"| **Annualized Return (CAGR)** | **{ret['cagr'] * 100:+.2f}%** | Geometric compound annual growth rate |",
            f"| **Average Daily Return** | {ret['mean_daily_return'] * 100:+.4f}% | Arithmetic daily average |",
            f"| **Best Day** | {ret['best_day_return'] * 100:+.2f}% | Recorded on {ret['best_day_date']} |",
            f"| **Worst Day** | {ret['worst_day_return'] * 100:+.2f}% | Recorded on {ret['worst_day_date']} |",
            f"| **Positive Trading Days** | {ret['positive_days_ratio']:.1f}% ({ret['positive_days_count']} of {ret['total_trading_days'] - 1} days) | Ratio of positive close-to-close days |",
            "",
            "## 3. Risk & Volatility Analysis",
            "",
            "| Risk Metric | Measurement | Description |",
            "| :--- | :--- | :--- |",
            f"| **Annualized Volatility** | **{risk['annualized_volatility'] * 100:.2f}%** | Daily standard deviation scaled by sqrt(252) |",
            f"| **Daily Volatility** | {risk['daily_volatility'] * 100:.2f}% | Standard deviation of daily percentage returns |",
            f"| **Downside Deviation** | {risk['downside_deviation'] * 100:.2f}% | Semi-deviation of negative returns below 0 |",
            f"| **Maximum Drawdown (MDD)** | **{risk['max_drawdown'] * 100:.2f}%** | Deepest trough from historical high-water mark |",
            f"| **MDD Peak Date** | {risk['max_drawdown_peak_date']} | Date peak was reached before drawdown |",
            f"| **MDD Trough Date** | {risk['max_drawdown_trough_date']} | Date maximum decline was recorded |",
            f"| **MDD Recovery Date** | {risk['max_drawdown_recovery_date'] or 'Unrecovered / In Drawdown'} | Date price restored to prior peak |",
            f"| **MDD Total Duration** | {risk['max_drawdown_duration_days']} calendar days | Peak-to-recovery (or current date) |",
            f"| **Sharpe Ratio (rf=0)** | **{risk['sharpe_ratio']:.2f}** | Risk-adjusted return per unit of total volatility |",
            f"| **Sortino Ratio (rf=0)** | **{risk['sortino_ratio']:.2f}** | Risk-adjusted return per unit of downside risk |",
            f"| **1-Day 95% Value at Risk (VaR)** | {risk['var_95'] * 100:.2f}% | Historical 5th percentile daily return |",
            f"| **1-Day 95% Expected Shortfall (CVaR)** | {risk['cvar_95'] * 100:.2f}% | Average loss in worst 5% tail days |",
            "",
            "## 4. Technical Indicator Status (Latest Date: " + str(tech['latest_date']) + ")",
            "",
            "| Indicator | Level | Current Position vs Price |",
            "| :--- | :--- | :--- |",
            f"| **Latest Price** | {cur} {tech['latest_price']:,.2f} | Reference baseline |",
            f"| **SMA 20** | {sma20_str} | {p_sma20_str} |",
            f"| **SMA 50** | {sma50_str} | {p_sma50_str} |",
            f"| **SMA 200** | {sma200_str} | {p_sma200_str} |",
            f"| **EMA 20** | {ema20_str} | Exponential short-term trend |",
            f"| **EMA 50** | {ema50_str} | Exponential medium-term trend |",
            f"| **SMA 50 vs 200 Alignment** | **{tech['sma50_vs_sma200'] or 'N/A'}** | {align_desc} |",
            f"| **Bollinger Bands (20, 2σ)** | {bb_range_str} | {bb_pos_str} |",
            "",
            "---",
            "*Disclaimer: This document is an automated quantitative research report generated strictly for educational and portfolio demonstration purposes. It presents objective historical calculations and contains no financial, legal, or investment advice or predictive guarantees.*",
        ]
        return "\n".join(md_lines)

    @classmethod
    def generate_comparison_markdown(cls, comp_result: StockComparisonResult) -> str:
        """Generate a structured Markdown report comparing multiple stocks."""
        table_md = comp_result.comparison_table.to_markdown()
        corr_md = comp_result.correlation_matrix.to_markdown()

        md_lines = [
            f"# Multi-Stock Comparative Research Summary",
            "",
            f"> **Analyzed Stocks**: {', '.join(comp_result.symbols)}",
            f"> **Synchronized Period**: {comp_result.common_start_date} to {comp_result.common_end_date} ({comp_result.common_trading_days} common trading days)",
            f"> **Data Source**: Historical permanent datasets from [`ankit02327/stock-price`](https://github.com/ankit02327/stock-price)",
            "",
            "## 1. Performance & Risk Comparison Table",
            "",
            table_md,
            "",
            "## 2. Daily Returns Correlation Matrix",
            "",
            corr_md,
            "",
            "---",
            "*Disclaimer: This report presents factual historical measurements across selected assets for educational research purposes and does not constitute financial advice.*",
        ]
        return "\n".join(md_lines)

    @classmethod
    def save_report(cls, content: str, output_path: Union[str, Path]) -> Path:
        """Save report string to file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
