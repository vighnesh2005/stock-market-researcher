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

__all__ = [
    "ReturnMetrics",
    "calculate_daily_returns",
    "calculate_cumulative_returns",
    "calculate_return_metrics",
    "RiskMetrics",
    "calculate_drawdown_series",
    "calculate_risk_metrics",
]
