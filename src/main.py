"""Main CLI entrypoint for Stock Market Researcher application.

Provides interactive stock discovery, single-stock historical research,
multi-stock comparative analytics, and automated report/chart generation.
"""

import argparse
from pathlib import Path
import sys
from typing import List, Optional
import json

from src.analysis.comparison import StockComparator
from src.analysis.returns import calculate_return_metrics
from src.analysis.risk import calculate_risk_metrics
from src.analysis.technical import calculate_technical_summary
from src.data.discovery import StockCatalog, StockMetadata
from src.data.loader import StockDataLoader
from src.summary.report import ResearchReportGenerator
from src.visualization.charts import generate_full_research_charts, plot_stock_comparison


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="stock-market-researcher",
        description="Quantitative stock market research and comparative analysis tool.",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--list-stocks",
        "-l",
        action="store_true",
        help="List available stocks discovered in the upstream dataset.",
    )
    group.add_argument(
        "--search",
        "-q",
        type=str,
        help="Search discovered stocks by ticker, company name, or sector.",
    )
    group.add_argument(
        "--stock",
        "-s",
        type=str,
        help="Run comprehensive research analysis on a single stock symbol (e.g. AAPL, ABB).",
    )
    group.add_argument(
        "--compare",
        "-c",
        nargs="+",
        help="Compare multiple stocks (e.g. --compare AAPL MSFT GOOGL).",
    )

    parser.add_argument(
        "--market",
        "-m",
        type=str,
        choices=["US", "IND", "all"],
        default="all",
        help="Filter by market region: 'US' (S&P 500 / NASDAQ) or 'IND' (NSE). Default: all.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date filter in 'YYYY-MM-DD' format.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date filter in 'YYYY-MM-DD' format.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="reports",
        help="Directory to save generated markdown reports and PNG charts (default: 'reports').",
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Disable chart rendering and only generate text/data reports.",
    )
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        default=0.0,
        help="Annualized risk-free rate for Sharpe/Sortino ratios (default: 0.0).",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "text", "json"],
        default="markdown",
        help="Output format for generated reports (default: markdown).",
    )

    return parser


def handle_list_stocks(catalog: StockCatalog, market_filter: Optional[str]) -> int:
    """Print tabular list of discovered stocks."""
    stocks = catalog.list_stocks(market=market_filter)
    market_str = market_filter or "ALL"
    print(f"\n=======================================================")
    print(f"Discovered Stocks ({len(stocks)} stocks available in {market_str} dataset)")
    print(f"=======================================================")
    print(f"{'Symbol':<12} {'Market':<8} {'Exchange':<10} {'Sector':<24} {'Company Name'}")
    print("-" * 80)
    for s in stocks[:40]:  # Show top 40 in terminal
        comp = s.company_name[:24] if len(s.company_name) > 24 else s.company_name
        print(f"{s.symbol:<12} {s.market:<8} {s.exchange:<10} {s.sector:<24} {comp}")

    if len(stocks) > 40:
        print(f"... and {len(stocks) - 40} more stocks. Use --search <query> to filter.")
    print("=======================================================\n")
    return 0


def handle_search_stocks(catalog: StockCatalog, query: str, market_filter: Optional[str]) -> int:
    """Search and display matching stocks."""
    results = catalog.search_stocks(query, market=market_filter)
    print(f"\n=======================================================")
    print(f"Search Results for '{query}' ({len(results)} matches found)")
    print(f"=======================================================")
    if not results:
        print("No matching stocks found. Try searching by ticker (e.g. 'AAPL') or sector.")
        return 0

    print(f"{'Symbol':<12} {'Market':<8} {'Exchange':<10} {'Sector':<24} {'Company Name'}")
    print("-" * 80)
    for s in results:
        comp = s.company_name[:30] if len(s.company_name) > 30 else s.company_name
        print(f"{s.symbol:<12} {s.market:<8} {s.exchange:<10} {s.sector:<24} {comp}")
    print("=======================================================\n")
    return 0


def handle_single_stock(
    loader: StockDataLoader,
    symbol: str,
    start_date: Optional[str],
    end_date: Optional[str],
    market: Optional[str],
    output_dir: Path,
    save_charts: bool,
    risk_free_rate: float,
    report_format: str,
) -> int:
    """Run research workflow for a single stock."""
    sym = symbol.strip().upper()
    try:
        df = loader.load_stock_data(sym, start_date=start_date, end_date=end_date, market=market)
    except Exception as e:
        print(f"[Error] Failed to load data for '{sym}': {e}", file=sys.stderr)
        return 1

    meta = loader.catalog.get_stock_metadata(sym, market=market)
    ret_m = calculate_return_metrics(df)
    risk_m = calculate_risk_metrics(df, risk_free_rate=risk_free_rate)
    tech_m = calculate_technical_summary(df)

    cur = df.attrs.get("currency", "USD")
    company = meta.company_name if meta else sym

    # Terminal summary printout
    print("\n" + "=" * 65)
    print(f" STOCK RESEARCH REPORT: {sym} ({company})")
    print("=" * 65)
    print(f" Market / Exchange : {meta.market if meta else 'N/A'} ({meta.exchange if meta else 'N/A'})")
    print(f" Sector            : {meta.sector if meta else 'N/A'}")
    print(f" Analyzed Period   : {ret_m.start_date} -> {ret_m.end_date} ({ret_m.total_trading_days} trading days)")
    print(f" Starting Price    : {cur} {ret_m.start_price:,.2f}")
    print(f" Ending Price      : {cur} {ret_m.end_price:,.2f}")
    print("-" * 65)
    print(" RETURN PROFILE:")
    print(f"   Cumulative Return  : {ret_m.cumulative_return * 100:+.2f}%")
    print(f"   Annualized (CAGR)  : {ret_m.cagr * 100:+.2f}%")
    print(f"   Daily Mean Return  : {ret_m.mean_daily_return * 100:+.4f}%")
    print(f"   Best Single Day    : {ret_m.best_day_return * 100:+.2f}% ({ret_m.best_day_date})")
    print(f"   Worst Single Day   : {ret_m.worst_day_return * 100:+.2f}% ({ret_m.worst_day_date})")
    print(f"   Positive Days      : {ret_m.positive_days_ratio:.1f}% ({ret_m.positive_days_count} of {ret_m.total_trading_days - 1} sessions)")
    print("-" * 65)
    print(" RISK & DRAWDOWN:")
    print(f"   Annualized Vol     : {risk_m.annualized_volatility * 100:.2f}%")
    print(f"   Maximum Drawdown   : {risk_m.max_drawdown * 100:.2f}%")
    print(f"   MDD Peak Date      : {risk_m.max_drawdown_peak_date}")
    print(f"   MDD Trough Date    : {risk_m.max_drawdown_trough_date}")
    print(f"   MDD Recovery Date  : {risk_m.max_drawdown_recovery_date or 'In Drawdown / Unrecovered'}")
    print(f"   Sharpe Ratio (rf=0): {risk_m.sharpe_ratio:.2f}")
    print(f"   Sortino Ratio (rf=0): {risk_m.sortino_ratio:.2f}")
    print(f"   1-Day 95% VaR      : {risk_m.var_95 * 100:.2f}%")
    print("-" * 65)
    print(" TECHNICAL INDICATORS (Latest):")
    sma20_str = f"{cur} {tech_m.sma_20:,.2f}" if tech_m.sma_20 else "N/A"
    sma50_str = f"{cur} {tech_m.sma_50:,.2f}" if tech_m.sma_50 else "N/A"
    sma200_str = f"{cur} {tech_m.sma_200:,.2f}" if tech_m.sma_200 else "N/A"
    print(f"   SMA 20             : {sma20_str} ({tech_m.price_to_sma20_pct:+.2f}%)" if tech_m.price_to_sma20_pct is not None else f"   SMA 20             : {sma20_str}")
    print(f"   SMA 50             : {sma50_str} ({tech_m.price_to_sma50_pct:+.2f}%)" if tech_m.price_to_sma50_pct is not None else f"   SMA 50             : {sma50_str}")
    print(f"   SMA 200            : {sma200_str} ({tech_m.price_to_sma200_pct:+.2f}%)" if tech_m.price_to_sma200_pct is not None else f"   SMA 200            : {sma200_str}")
    print(f"   SMA 50/200 Status  : {tech_m.sma50_vs_sma200 or 'N/A'}")
    print("=" * 65)

    output_dir.mkdir(parents=True, exist_ok=True)
    clean_sym = sym.lower()

    if report_format == "markdown":
        report_text = ResearchReportGenerator.generate_single_stock_markdown(
            df=df, symbol=sym, metadata=meta, risk_free_rate=risk_free_rate
        )
        report_file = output_dir / f"{clean_sym}_research_report.md"
        report_file.write_text(report_text, encoding="utf-8")
        print(f"\n[Report Saved] -> {report_file}")
    elif report_format == "json":
        data_dict = ResearchReportGenerator.generate_single_stock_dict(
            df=df, symbol=sym, metadata=meta, risk_free_rate=risk_free_rate
        )
        report_file = output_dir / f"{clean_sym}_research_report.json"
        report_file.write_text(json.dumps(data_dict, indent=2, default=str), encoding="utf-8")
        print(f"\n[Report Saved] -> {report_file}")

    if save_charts:
        print(f"[Rendering Charts] -> {output_dir}")
        chart_paths = generate_full_research_charts(df, sym, output_dir=output_dir)
        for cp in chart_paths:
            print(f"  + {cp.name}")

    print("\nResearch complete.\n")
    return 0


def handle_compare_stocks(
    loader: StockDataLoader,
    symbols: List[str],
    start_date: Optional[str],
    end_date: Optional[str],
    market: Optional[str],
    output_dir: Path,
    save_charts: bool,
    risk_free_rate: float,
) -> int:
    """Run comparative analysis across multiple stocks."""
    clean_symbols = [s.strip().upper() for s in symbols]
    dfs = {}

    for sym in clean_symbols:
        try:
            df = loader.load_stock_data(sym, start_date=start_date, end_date=end_date, market=market)
            dfs[sym] = df
        except Exception as e:
            print(f"[Error] Failed to load data for '{sym}': {e}", file=sys.stderr)
            return 1

    try:
        comparator = StockComparator(dfs)
        result = comparator.compare(risk_free_rate=risk_free_rate)
    except Exception as e:
        print(f"[Error] Comparison failed: {e}", file=sys.stderr)
        return 1

    print("\n" + "=" * 80)
    print(f" MULTI-STOCK COMPARISON: {', '.join(clean_symbols)}")
    print("=" * 80)
    print(f" Common Period: {result.common_start_date} to {result.common_end_date} ({result.common_trading_days} sessions)")
    print("-" * 80)
    print(result.comparison_table.to_string())
    print("-" * 80)
    print(" Daily Returns Correlation Matrix:")
    print(result.correlation_matrix.to_string())
    print("=" * 80)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_text = ResearchReportGenerator.generate_comparison_markdown(result)
    tag = "_vs_".join(s.lower() for s in clean_symbols[:3])
    report_file = output_dir / f"comparison_{tag}.md"
    report_file.write_text(report_text, encoding="utf-8")
    print(f"\n[Report Saved] -> {report_file}")

    if save_charts:
        chart_file = output_dir / f"comparison_{tag}_chart.png"
        plot_stock_comparison(result, chart_file)
        print(f"[Chart Saved]  -> {chart_file}")

    print("\nComparison complete.\n")
    return 0


def main(args: Optional[List[str]] = None) -> int:
    """Main program entrypoint."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    # Initialize catalog and data loader
    catalog = StockCatalog()
    loader = StockDataLoader(catalog)

    market_filter = None if parsed.market == "all" else parsed.market
    output_path = Path(parsed.output_dir)

    if parsed.list_stocks:
        return handle_list_stocks(catalog, market_filter)

    if parsed.search:
        return handle_search_stocks(catalog, parsed.search, market_filter)

    if parsed.stock:
        return handle_single_stock(
            loader=loader,
            symbol=parsed.stock,
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            market=market_filter,
            output_dir=output_path,
            save_charts=not parsed.no_charts,
            risk_free_rate=parsed.risk_free_rate,
            report_format=parsed.format,
        )

    if parsed.compare:
        return handle_compare_stocks(
            loader=loader,
            symbols=parsed.compare,
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            market=market_filter,
            output_dir=output_path,
            save_charts=not parsed.no_charts,
            risk_free_rate=parsed.risk_free_rate,
        )

    # If no specific action is provided, print help and show interactive default prompt
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
