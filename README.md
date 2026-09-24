# Stock Market Researcher

A quantitative stock market research and historical analysis platform built in Python. This project provides exploratory data analysis, return analytics, risk and drawdown evaluation, moving average indicators, multi-stock comparative benchmarking, and automated factual research report generation.

---

## 1. Project Overview

**Stock Market Researcher** is an independent downstream research tool designed to discover and analyze historical equities across both US markets (S&P 500 / NASDAQ / NYSE) and Indian markets (NSE).

The application processes daily price and volume time series to compute factual mathematical metrics—including geometric CAGR, annualized volatility, underwater drawdowns, peak-to-recovery durations, and Sharpe/Sortino ratios—rendering both publication-ready charts and markdown research summaries.

---

## 2. Why the Project Exists

Analyzing historical equities often requires assembling disparate data sources, writing repetitive statistical routines, and generating manual charts. This project serves as an educational and portfolio tool that:
- Standardizes data ingestion across global equities datasets.
- Implements mathematically rigorous quantitative metrics without external heavy dependencies.
- Generates reproducible, factual research artifacts for portfolio review and market study without making subjective predictions or investment recommendations.

---

## 3. Core Features

- **Data Discovery & Search**: Catalog over 1,000 stocks across US and Indian exchanges with sector, exchange, and company metadata filtering.
- **Robust Ingestion Layer**: Automatic timezone standardization, chronological sorting, missing value handling, and schema validation.
- **Return Analytics**:
  - Daily percentage returns & cumulative returns.
  - Compound Annual Growth Rate (CAGR) and arithmetic mean returns.
  - Best and worst trading sessions with exact dates.
  - Positive vs. negative trading days distribution.
- **Risk & Drawdown Profiling**:
  - Annualized volatility ($\sigma_{\text{daily}} \times \sqrt{252}$).
  - Semi-deviation downside risk.
  - Historical Maximum Drawdown (MDD), peak-to-trough tracking, and recovery duration.
  - Risk-adjusted performance metrics: Sharpe Ratio and Sortino Ratio.
  - 1-Day 95% Value at Risk (VaR) and Conditional Value at Risk (CVaR / Expected Shortfall).
- **Technical Indicators**:
  - Simple Moving Averages: SMA 20, SMA 50, SMA 200.
  - Exponential Moving Averages: EMA 20, EMA 50.
  - Bollinger Bands (20 periods, 2 standard deviations).
  - Moving average crossover analysis (Golden Cross / Death Cross alignment).
- **Multi-Stock Comparative Analysis**:
  - Inner-joined synchronized date alignment.
  - Normalized comparative performance tracking.
  - Return correlation matrices.
  - Annualized risk-return scatter plots.
- **Automated Research Reports & Visualizations**:
  - Markdown, JSON, and terminal report outputs.
  - High-resolution charts saved to `reports/`:
    - Price history with SMA & Bollinger Bands
    - Cumulative returns underwater
    - Historical drawdown
    - Daily return distribution histogram

---

## 4. Relationship with Upstream `ankit02327/stock-price`

This repository has a real upstream dependency on [**ankit02327/stock-price**](https://github.com/ankit02327/stock-price).

### What Part of `stock-price` is Used
This project directly consumes the verified historical permanent stock price datasets and metadata indices provided in the submodule under:
- `vendor/stock-price/permanent/us_stocks/` (S&P 500 / US equities indices and historical CSVs)
- `vendor/stock-price/permanent/ind_stocks/` (NSE / Indian equities indices and historical CSVs)

### Why It Is Useful
The upstream repository curates structured OHLCV time series and exchange metadata across over 1,000 equities. Rather than querying live rate-limited external APIs, this project uses the permanent dataset as an authoritative offline historical foundation for reproducible quantitative research and backtesting.

### Upstream Integration Details
- **Integration Mechanism**: Git Submodule under `vendor/stock-price`
- **Tracked Upstream Version**: `v0.1.9` (Commit `224325c09ae5a0e86cb25c4ed881a7a21020ab54`)
- **Upstream Repository**: https://github.com/ankit02327/stock-price

*Note: Stock Market Researcher is an independent downstream research application and is not an official component of `ankit02327/stock-price`.*

---

## 5. Architecture

```
stock-market-researcher/
├── src/
│   ├── data/
│   │   ├── discovery.py       # StockCatalog: index scanning & search across markets
│   │   └── loader.py          # StockDataLoader: validation, timezone normalization, range filtering
│   ├── analysis/
│   │   ├── returns.py         # Daily & cumulative returns, CAGR, periodic stats
│   │   ├── risk.py            # Annualized volatility, drawdown series, Sharpe/Sortino, VaR
│   │   ├── technical.py       # SMA 20/50/200, EMA, Bollinger Bands, trend alignment
│   │   └── comparison.py      # Multi-stock alignment, comparative tables, correlation
│   ├── visualization/
│   │   └── charts.py          # Matplotlib charting engine (headless rendering to PNG)
│   ├── summary/
│   │   └── report.py          # Factual markdown/JSON research summary report generator
│   └── main.py                # Command-line interface
├── tests/
│   ├── conftest.py            # Deterministic fixtures for mathematical testing
│   ├── test_discovery.py      # Tests for stock catalog discovery
│   ├── test_loader.py         # Tests for data loading and schema validation
│   ├── test_returns.py        # Mathematical tests for returns & CAGR
│   ├── test_risk.py           # Mathematical tests for volatility & drawdowns
│   ├── test_technical.py      # Tests for moving averages & indicators
│   ├── test_comparison.py     # Tests for multi-stock synchronization & correlation
│   ├── test_report.py         # Tests for report generator
│   └── test_cli.py            # End-to-end CLI integration tests
├── reports/                   # Output directory for generated reports & charts
├── vendor/
│   └── stock-price/           # Git submodule pinned to ankit02327/stock-price
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Minimal Python dependencies
└── .gitmodules                # Git submodule configuration
```

---

## 6. Installation

### Prerequisites
- Python 3.9+
- Git

### Setup
1. Clone the repository with submodules:
```bash
git clone --recurse-submodules https://github.com/vighnesh2005/stock-market-researcher.git
cd stock-market-researcher
```

If already cloned without submodules, initialize the submodule:
```bash
git submodule update --init --recursive
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 7. Usage

The tool is executed via `src/main.py`:

### Discover & Search Stocks
```bash
# List all available stocks (shows first 40 with sector & exchange)
python -m src.main --list-stocks

# Filter discovery by US or Indian markets
python -m src.main --list-stocks --market US
python -m src.main --list-stocks --market IND

# Search by ticker or keyword
python -m src.main --search "Apple"
python -m src.main --search "Healthcare" --market US
```

### Research a Single Stock
```bash
# Analyze Apple (AAPL) over full available history
python -m src.main --stock AAPL

# Specify a custom historical date range
python -m src.main --stock AAPL --start-date 2021-01-01 --end-date 2023-12-31

# Save reports and charts to a custom folder
python -m src.main --stock MSFT --output-dir reports/msft_study

# Generate JSON structured data instead of Markdown
python -m src.main --stock GOOGL --format json
```

### Multi-Stock Comparative Analysis
```bash
# Compare tech stocks across common trading dates
python -m src.main --compare AAPL MSFT GOOGL

# Compare Indian equities
python -m src.main --compare ABB TCS INFY --market IND
```

---

## 8. Example Output

### Terminal Summary (AAPL)
```text
=================================================================
 STOCK RESEARCH REPORT: AAPL (Apple)
=================================================================
 Market / Exchange : US (NASDAQ)
 Sector            : Technology
 Analyzed Period   : 2020-01-02 -> 2024-12-30 (1257 trading days)
 Starting Price    : USD 72.54
 Ending Price      : USD 251.31
-----------------------------------------------------------------
 RETURN PROFILE:
   Cumulative Return  : +246.45%
   Annualized (CAGR)  : +28.31%
   Daily Mean Return  : +0.1189%
   Best Single Day    : +11.98% (2020-03-13)
   Worst Single Day   : -12.86% (2020-03-16)
   Positive Days      : 53.3% (670 of 1256 sessions)
-----------------------------------------------------------------
 RISK & DRAWDOWN:
   Annualized Vol     : 31.69%
   Maximum Drawdown   : -31.43%
   MDD Peak Date      : 2020-02-12
   MDD Trough Date    : 2020-03-23
   MDD Recovery Date  : 2020-06-05
   Sharpe Ratio (rf=0): 0.89
   Sortino Ratio (rf=0): 0.90
   1-Day 95% VaR      : -3.01%
-----------------------------------------------------------------
 TECHNICAL INDICATORS (Latest):
   SMA 20             : USD 248.39 (+1.18%)
   SMA 50             : USD 236.38 (+6.32%)
   SMA 200            : USD 211.92 (+18.59%)
   SMA 50/200 Status  : ABOVE
=================================================================
```

### Generated Artifacts
When executing research commands, the application automatically outputs:
- `reports/<symbol>_research_report.md`: Markdown summary table
- `reports/<symbol>_price_indicators.png`: Price history, SMA 20/50/200, Bollinger Bands, and Volume
- `reports/<symbol>_cumulative_returns.png`: Historical cumulative return series
- `reports/<symbol>_drawdown.png`: Underwater drawdown chart
- `reports/<symbol>_return_distribution.png`: Daily return histogram with fitted normal curve and VaR threshold
- `reports/comparison_<symbols>_chart.png`: Normalized comparative return lines and risk/return scatter plot

---

## 9. Testing

The project includes an automated test suite with deterministic mathematical test fixtures.

Run all tests:
```bash
pytest
```

Run tests with verbose output and coverage:
```bash
pytest -v
```

---

## 10. Limitations

- **Historical Scope**: Data depends on the dates populated in the upstream permanent dataset (primarily 2020 through 2024/2025).
- **Offline / Static Ingestion**: Real-time intraday tick streaming is not implemented; analysis operates on end-of-day daily bars.
- **Cross-Market Synchronicity**: When comparing stocks from different international exchanges (e.g. US vs. Indian markets), comparisons are restricted to calendar dates where both markets operated simultaneously.

---

## 11. Disclaimer

*This application is developed strictly for academic, research, and portfolio demonstration purposes. All statistics and generated reports represent factual historical measurements. Nothing in this software constitutes investment advice, financial analysis, a recommendation to buy or sell securities, or a guarantee of future market performance.*
