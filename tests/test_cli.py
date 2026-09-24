"""Tests for command line interface."""

from pathlib import Path
import pytest

from src.main import main


def test_cli_help(capsys):
    """Test running CLI with --help returns 0."""
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_cli_list_stocks(capsys):
    """Test running CLI --list-stocks."""
    code = main(["--list-stocks", "--market", "US"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Discovered Stocks" in captured.out


def test_cli_search(capsys):
    """Test running CLI --search."""
    code = main(["--search", "Apple"])
    assert code == 0
    captured = capsys.readouterr()
    assert "AAPL" in captured.out


def test_cli_single_stock_no_charts(tmp_path, capsys):
    """Test running CLI single stock research without charts."""
    out_dir = str(tmp_path / "reports_test")
    code = main(["--stock", "AAPL", "--output-dir", out_dir, "--no-charts"])
    assert code == 0
    captured = capsys.readouterr()
    assert "STOCK RESEARCH REPORT: AAPL" in captured.out
    report_file = Path(out_dir) / "aapl_research_report.md"
    assert report_file.exists()


def test_cli_compare_stocks_no_charts(tmp_path, capsys):
    """Test running CLI multi-stock comparison without charts."""
    out_dir = str(tmp_path / "reports_test_comp")
    code = main(["--compare", "AAPL", "MSFT", "--output-dir", out_dir, "--no-charts"])
    assert code == 0
    captured = capsys.readouterr()
    assert "MULTI-STOCK COMPARISON: AAPL, MSFT" in captured.out
    report_file = Path(out_dir) / "comparison_aapl_vs_msft.md"
    assert report_file.exists()
