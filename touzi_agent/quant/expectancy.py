from dataclasses import dataclass
from statistics import mean, stdev
from math import sqrt

_Z = 1.96


@dataclass(frozen=True)
class ExpectancyStats:
    n: int
    win_rate: float
    avg_win_r: float
    avg_loss_r: float
    expectancy_r: float
    ci_low: float
    ci_high: float


def expectancy(r_multiples: list[float]) -> ExpectancyStats:
    if not r_multiples:
        raise ValueError("need at least one R-multiple")
    n = len(r_multiples)
    wins = [r for r in r_multiples if r > 0]
    losses = [r for r in r_multiples if r <= 0]
    exp_r = mean(r_multiples)
    if n > 1:
        margin = _Z * stdev(r_multiples) / sqrt(n)
    else:
        margin = 0.0
    return ExpectancyStats(
        n=n,
        win_rate=len(wins) / n,
        avg_win_r=mean(wins) if wins else 0.0,
        avg_loss_r=mean(losses) if losses else 0.0,
        expectancy_r=exp_r,
        ci_low=exp_r - margin,
        ci_high=exp_r + margin,
    )
