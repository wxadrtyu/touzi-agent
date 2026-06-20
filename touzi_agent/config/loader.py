from pathlib import Path
import yaml

from touzi_agent.models import MarketConfig

DEFAULT_MARKETS_DIR = Path(__file__).parent / "markets"
_REQUIRED = ("market", "currency", "settlement", "short_selling",
             "code_prefix", "daily_limit", "costs")
_VALID_SETTLEMENT = {"T+0", "T+1", "T+2"}


def load_market_config(path: str | Path) -> MarketConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in _REQUIRED if k not in data]
    if missing:
        raise ValueError(f"{path}: missing required fields {missing}")
    if data["settlement"] not in _VALID_SETTLEMENT:
        raise ValueError(
            f"{path}: invalid settlement {data['settlement']!r}")
    return MarketConfig(
        market=data["market"],
        currency=data["currency"],
        settlement=data["settlement"],
        short_selling=data["short_selling"],
        code_prefix=data["code_prefix"],
        daily_limit=data["daily_limit"],
        costs=data["costs"],
    )


def load_all_markets(dir: str | Path) -> dict[str, MarketConfig]:
    result: dict[str, MarketConfig] = {}
    for path in sorted(Path(dir).glob("market-*.yaml")):
        cfg = load_market_config(path)
        result[cfg.market] = cfg
    return result
