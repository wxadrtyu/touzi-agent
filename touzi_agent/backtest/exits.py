from touzi_agent.models import Bar
from touzi_agent.quant.trade import Side


def resolve_exit(side: str, stop: float, target: float | None,
                 bar: Bar) -> tuple[float, str] | None:
    if side == Side.LONG:
        if bar.low <= stop:
            return (stop, "stop")
        if target is not None and bar.high >= target:
            return (target, "target")
    else:
        if bar.high >= stop:
            return (stop, "stop")
        if target is not None and bar.low <= target:
            return (target, "target")
    return None
