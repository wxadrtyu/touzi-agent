import pytest
from touzi_agent.quant.expectancy import expectancy, ExpectancyStats


def test_basic_expectancy():
    # 2 wins (+3R each), 3 losses (-1R each): mean = (6-3)/5 = 0.6
    stats = expectancy([3.0, 3.0, -1.0, -1.0, -1.0])
    assert stats.n == 5
    assert stats.win_rate == pytest.approx(0.4)
    assert stats.avg_win_r == pytest.approx(3.0)
    assert stats.avg_loss_r == pytest.approx(-1.0)
    assert stats.expectancy_r == pytest.approx(0.6)


def test_all_wins_no_losers():
    stats = expectancy([1.0, 2.0])
    assert stats.win_rate == 1.0
    assert stats.avg_loss_r == 0.0
    assert stats.expectancy_r == pytest.approx(1.5)


def test_confidence_interval_brackets_mean():
    stats = expectancy([3.0, 3.0, -1.0, -1.0, -1.0])
    assert stats.ci_low < stats.expectancy_r < stats.ci_high


def test_single_trade_ci_collapses():
    stats = expectancy([2.0])
    assert stats.ci_low == stats.ci_high == 2.0


def test_empty_rejected():
    with pytest.raises(ValueError):
        expectancy([])
