from dataclasses import dataclass

from touzi_agent.quant.portfolio import Position, Portfolio


@dataclass(frozen=True)
class RiskLimits:
    max_total_heat: float = 0.06
    max_position_pct: float = 0.20
    max_market_pct: float = 0.40
    max_cluster_pct: float = 0.30
    drawdown_derisk: float = 0.20


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reasons: list[str]


class RiskModel:
    def __init__(self, limits: RiskLimits):
        self.limits = limits

    def check(self, portfolio: Portfolio, candidate: Position) -> RiskDecision:
        lim = self.limits
        eq = portfolio.equity
        reasons: list[str] = []

        if portfolio.drawdown() >= lim.drawdown_derisk:
            reasons.append(
                f"drawdown {portfolio.drawdown():.2%} >= de-risk "
                f"threshold {lim.drawdown_derisk:.2%}; new entries paused")

        prospective = Portfolio(
            equity=eq,
            positions=list(portfolio.positions) + [candidate],
            peak_equity=portfolio.peak_equity,
        )

        if prospective.total_heat() > lim.max_total_heat:
            reasons.append(
                f"total heat {prospective.total_heat():.2%} > cap "
                f"{lim.max_total_heat:.2%}")

        pos_pct = candidate.notional / eq
        if pos_pct > lim.max_position_pct:
            reasons.append(
                f"position size {pos_pct:.2%} > cap "
                f"{lim.max_position_pct:.2%}")

        mkt_pct = prospective.market_exposure(candidate.market)
        if mkt_pct > lim.max_market_pct:
            reasons.append(
                f"market {candidate.market} exposure {mkt_pct:.2%} > cap "
                f"{lim.max_market_pct:.2%}")

        if candidate.cluster:
            cl_pct = prospective.cluster_exposure(candidate.cluster)
            if cl_pct > lim.max_cluster_pct:
                reasons.append(
                    f"cluster {candidate.cluster} exposure {cl_pct:.2%} > "
                    f"cap {lim.max_cluster_pct:.2%}")

        return RiskDecision(allowed=(reasons == []), reasons=reasons)
