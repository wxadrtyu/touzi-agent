import pytest
from touzi_agent.config.loader import (
    load_market_config, load_all_markets, DEFAULT_MARKETS_DIR,
)


def test_loads_us_config():
    cfg = load_market_config(DEFAULT_MARKETS_DIR / "market-us.yaml")
    assert cfg.market == "US"
    assert cfg.settlement == "T+0"
    assert cfg.daily_limit is None
    assert cfg.currency == "USD"


def test_loads_cn_config_with_limits():
    cfg = load_market_config(DEFAULT_MARKETS_DIR / "market-cn.yaml")
    assert cfg.market == "CN"
    assert cfg.settlement == "T+1"
    assert cfg.limit_for("main_board") == 0.10
    assert cfg.limit_for("chinext") == 0.20


def test_load_all_markets_keyed_by_market():
    markets = load_all_markets(DEFAULT_MARKETS_DIR)
    assert set(markets) == {"US", "HK", "CN"}
    assert markets["HK"].settlement == "T+2"


def test_invalid_settlement_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "market: XX\ncurrency: USD\nsettlement: T+9\n"
        "short_selling: allowed\ncode_prefix: XX\n"
        "daily_limit: null\ncosts: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_market_config(bad)
