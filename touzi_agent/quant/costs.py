from touzi_agent.models import MarketConfig


def compute_cost(config: MarketConfig, side: str,
                 price: float, qty: int) -> float:
    c = config.costs
    notional = price * qty
    commission = max(notional * c.get("commission_rate", 0.0),
                     c.get("min_commission", 0.0))
    stamp_rate = c.get("stamp_duty", 0.0)
    if side == "SELL" or config.market == "HK":
        stamp = notional * stamp_rate
    else:
        stamp = 0.0
    transfer = notional * c.get("transfer_fee", 0.0)
    platform = c.get("platform_fee", 0.0)
    return commission + stamp + transfer + platform
