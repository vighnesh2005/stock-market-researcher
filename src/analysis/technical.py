"""Technical indicator calculations and moving-average relationship analysis."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TechnicalSummary:
    """Factual summary of technical indicators and moving averages at latest date."""

    latest_date: str
    latest_price: float
    sma_20: Optional[float]
    sma_50: Optional[float]
    sma_200: Optional[float]
    ema_20: Optional[float]
    ema_50: Optional[float]
    price_to_sma20_pct: Optional[float]  # (Price - SMA20) / SMA20 * 100
    price_to_sma50_pct: Optional[float]  # (Price - SMA50) / SMA50 * 100
    price_to_sma200_pct: Optional[float]  # (Price - SMA200) / SMA200 * 100
    sma50_vs_sma200: Optional[str]  # 'ABOVE' (Bullish alignment) or 'BELOW' (Bearish alignment) or None
    bb_upper: Optional[float]  # Bollinger Upper (20-period, 2 std)
    bb_lower: Optional[float]  # Bollinger Lower (20-period, 2 std)
    bb_position_pct: Optional[float]  # % within Bollinger Band width: (Price - Lower) / (Upper - Lower) * 100


def calculate_sma(
    series_or_df: Union[pd.Series, pd.DataFrame],
    window: int,
    column: str = "adjusted_close",
) -> pd.Series:
    """Calculate Simple Moving Average (SMA) over a rolling window.
    
    Args:
        series_or_df: Price Series or DataFrame.
        window: Number of periods for moving window.
        column: Target column name if DataFrame.
        
    Returns:
        pd.Series with SMA values.
    """
    if isinstance(series_or_df, pd.DataFrame):
        target = column if column in series_or_df.columns else "close"
        series = series_or_df[target]
    else:
        series = series_or_df

    sma = series.rolling(window=window, min_periods=window).mean()
    sma.name = f"SMA_{window}"
    return sma


def calculate_ema(
    series_or_df: Union[pd.Series, pd.DataFrame],
    span: int,
    column: str = "adjusted_close",
) -> pd.Series:
    """Calculate Exponential Moving Average (EMA) with a specified span.
    
    Args:
        series_or_df: Price Series or DataFrame.
        span: Span for decay calculation: alpha = 2 / (span + 1).
        column: Target column name if DataFrame.
        
    Returns:
        pd.Series with EMA values.
    """
    if isinstance(series_or_df, pd.DataFrame):
        target = column if column in series_or_df.columns else "close"
        series = series_or_df[target]
    else:
        series = series_or_df

    ema = series.ewm(span=span, adjust=False, min_periods=span).mean()
    ema.name = f"EMA_{span}"
    return ema


def calculate_bollinger_bands(
    series_or_df: Union[pd.Series, pd.DataFrame],
    window: int = 20,
    num_std: float = 2.0,
    column: str = "adjusted_close",
) -> pd.DataFrame:
    """Calculate Bollinger Bands (Middle SMA, Upper Band, Lower Band).
    
    Args:
        series_or_df: Price Series or DataFrame.
        window: Rolling window period (default 20).
        num_std: Number of standard deviations (default 2.0).
        column: Target column name if DataFrame.
        
    Returns:
        DataFrame with columns ['bb_middle', 'bb_upper', 'bb_lower', 'bb_bandwidth'].
    """
    if isinstance(series_or_df, pd.DataFrame):
        target = column if column in series_or_df.columns else "close"
        series = series_or_df[target]
    else:
        series = series_or_df

    middle = series.rolling(window=window, min_periods=window).mean()
    rolling_std = series.rolling(window=window, min_periods=window).std(ddof=1)
    upper = middle + (rolling_std * num_std)
    lower = middle - (rolling_std * num_std)
    bandwidth = (upper - lower) / middle

    bb_df = pd.DataFrame(
        {
            "bb_middle": middle,
            "bb_upper": upper,
            "bb_lower": lower,
            "bb_bandwidth": bandwidth,
        },
        index=series.index,
    )
    return bb_df


def add_technical_indicators(
    df: pd.DataFrame,
    price_col: str = "adjusted_close",
) -> pd.DataFrame:
    """Enrich a price DataFrame with standard technical indicators.
    
    Adds: SMA_20, SMA_50, SMA_200, EMA_20, EMA_50, BB_Upper, BB_Lower.
    
    Args:
        df: Input price DataFrame.
        price_col: Column to use for calculations.
        
    Returns:
        New DataFrame with appended indicator columns.
    """
    out = df.copy()
    target = price_col if price_col in out.columns else "close"

    out["SMA_20"] = calculate_sma(out[target], window=20)
    out["SMA_50"] = calculate_sma(out[target], window=50)
    if len(out) >= 200:
        out["SMA_200"] = calculate_sma(out[target], window=200)
    else:
        out["SMA_200"] = np.nan

    out["EMA_20"] = calculate_ema(out[target], span=20)
    out["EMA_50"] = calculate_ema(out[target], span=50)

    bb = calculate_bollinger_bands(out[target], window=20, num_std=2.0)
    out["BB_Middle"] = bb["bb_middle"]
    out["BB_Upper"] = bb["bb_upper"]
    out["BB_Lower"] = bb["bb_lower"]

    return out


def calculate_technical_summary(
    df_or_prices: Union[pd.DataFrame, pd.Series],
    price_col: str = "adjusted_close",
) -> TechnicalSummary:
    """Generate a factual summary of technical indicators for the latest available date.
    
    Args:
        df_or_prices: DataFrame with price data or Series.
        price_col: Target price column.
        
    Returns:
        TechnicalSummary dataclass with latest indicator levels.
    """
    if isinstance(df_or_prices, pd.DataFrame):
        target = price_col if price_col in df_or_prices.columns else "close"
        df_work = df_or_prices.copy()
    else:
        target = "adjusted_close"
        df_work = pd.DataFrame({target: df_or_prices})

    enriched = add_technical_indicators(df_work, price_col=target)
    latest_row = enriched.iloc[-1]
    latest_date_str = str(enriched.index[-1])[:10]
    price = float(latest_row[target])

    sma20 = float(latest_row["SMA_20"]) if pd.notna(latest_row["SMA_20"]) else None
    sma50 = float(latest_row["SMA_50"]) if pd.notna(latest_row["SMA_50"]) else None
    sma200 = float(latest_row["SMA_200"]) if pd.notna(latest_row["SMA_200"]) else None

    ema20 = float(latest_row["EMA_20"]) if pd.notna(latest_row["EMA_20"]) else None
    ema50 = float(latest_row["EMA_50"]) if pd.notna(latest_row["EMA_50"]) else None

    bb_upper = float(latest_row["BB_Upper"]) if pd.notna(latest_row["BB_Upper"]) else None
    bb_lower = float(latest_row["BB_Lower"]) if pd.notna(latest_row["BB_Lower"]) else None

    # Percent distances
    pct_to_sma20 = ((price - sma20) / sma20 * 100.0) if sma20 else None
    pct_to_sma50 = ((price - sma50) / sma50 * 100.0) if sma50 else None
    pct_to_sma200 = ((price - sma200) / sma200 * 100.0) if sma200 else None

    # SMA 50 vs 200 relationship
    if sma50 is not None and sma200 is not None:
        sma50_vs_200 = "ABOVE" if sma50 >= sma200 else "BELOW"
    else:
        sma50_vs_200 = None

    # Bollinger Band position %
    if bb_upper is not None and bb_lower is not None and (bb_upper - bb_lower) > 0:
        bb_pos = (price - bb_lower) / (bb_upper - bb_lower) * 100.0
    else:
        bb_pos = None

    return TechnicalSummary(
        latest_date=latest_date_str,
        latest_price=price,
        sma_20=sma20,
        sma_50=sma50,
        sma_200=sma200,
        ema_20=ema20,
        ema_50=ema50,
        price_to_sma20_pct=pct_to_sma20,
        price_to_sma50_pct=pct_to_sma50,
        price_to_sma200_pct=pct_to_sma200,
        sma50_vs_sma200=sma50_vs_200,
        bb_upper=bb_upper,
        bb_lower=bb_lower,
        bb_position_pct=bb_pos,
    )
