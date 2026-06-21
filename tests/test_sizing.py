import pytest
from touzi_agent.quant.expectancy import expectancy
from touzi_agent.quant.sizing import kelly_risk_fraction, size_position


def test_positive_edge_fraction_capped():
    # W=0.4, avg_win=3, avg_loss=-1 -> b=3, f=0.4-0.6/3=0.2
    # kelly_cap*f = 0.25*0.2 = 0.05 -> capped at max_risk_pct=0.01
    stats = expectancy([3.0, 3.0, -1.0, -1.0, -1.0])
    assert kelly_risk_fraction(stats) == pytest.approx(0.01)


def test_positive_edge_below_cap():
    stats = expectancy([3.0, 3.0, -1.0, -1.0, -1.0])
    # raise the ceiling so the clamp doesn't bite: 0.25*0.2 = 0.05
    frac = kelly_risk_fraction(stats, max_risk_pct=0.10)
    assert frac == pytest.approx(0.05)


def test_negative_edge_returns_floor():
    # all losers -> f negative -> floor
    stats = expectancy([-1.0, -1.0, -1.0])
    assert kelly_risk_fraction(stats, floor=0.0) == 0.0


def test_no_losers_returns_max():
    stats = expectancy([1.0, 2.0])
    assert kelly_risk_fraction(stats, max_risk_pct=0.02) == 0.02


def test_size_position_rounds_to_lot():
    # equity 100000, risk_fraction 0.01 -> risk $1000; per-share risk $2
    # raw = 500 shares; lot 100 -> 500
    assert size_position(100000, 0.01, entry=100, stop=98, lot_size=100) == 500


def test_size_position_rounds_down_partial_lot():
    # risk $1000, per-share risk $3 -> raw 333.3; lot 100 -> 300
    assert size_position(100000, 0.01, entry=100, stop=97, lot_size=100) == 300


def test_size_position_zero_risk_rejected():
    with pytest.raises(ValueError):
        size_position(100000, 0.01, entry=100, stop=100)
