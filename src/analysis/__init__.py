"""Analysis modules for returns, risk, technical indicators, and stock comparison."""

from src.analysis.returns import (
    ReturnMetrics,
    calculate_daily_returns,
    calculate_cumulative_returns,
    calculate_return_metrics,
)
from src.analysis.risk import (
    RiskMetrics,
    calculate_drawdown_series,
    calculate_risk_metrics,
)
from src.analysis.technical import (
    TechnicalSummary,
    add_technical_indicators,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_sma,
    calculate_technical_summary,
)

__all__ = [
    "ReturnMetrics",
    "calculate_daily_returns",
    "calculate_cumulative_returns",
    "calculate_return_metrics",
    "RiskMetrics",
    "calculate_drawdown_series",
    "calculate_risk_metrics",
    "TechnicalSummary",
    "add_technical_indicators",
    "calculate_bollinger_bands",
    "calculate_ema",
    "calculate_sma",
    "calculate_technical_summary",
]
