from math import floor

from touzi_agent.quant.expectancy import ExpectancyStats


def kelly_risk_fraction(stats: ExpectancyStats, kelly_cap: float = 0.25,
                        max_risk_pct: float = 0.01,
                        floor: float = 0.0) -> float:
    if stats.avg_loss_r == 0:
        return max_risk_pct
    b = stats.avg_win_r / abs(stats.avg_loss_r)
    if b <= 0:
        return floor
    f = stats.win_rate - (1 - stats.win_rate) / b
    frac = kelly_cap * f
    if frac < floor:
        return floor
    if frac > max_risk_pct:
        return max_risk_pct
    return frac


def size_position(equity: float, risk_fraction: float, entry: float,
                  stop: float, lot_size: int = 1) -> int:
    per_share_risk = abs(entry - stop)
    if per_share_risk == 0:
        raise ValueError("entry and stop must differ")
    risk_amount = equity * risk_fraction
    raw_qty = risk_amount / per_share_risk
    return int(floor(raw_qty / lot_size) * lot_size)
