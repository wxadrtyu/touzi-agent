from touzi_agent.adapters.base import BaseDataAdapter


def test_full_code_prefixes(us_config, fake_client):
    adapter = BaseDataAdapter(us_config, fake_client)
    assert adapter.full_code("AAPL") == "US.AAPL"


def test_fetch_bars_normalizes_kline(us_config, fake_client):
    adapter = BaseDataAdapter(us_config, fake_client)
    bars = adapter.fetch_bars("AAPL", "2026-06-18", "2026-06-19")
    assert [b.date for b in bars] == ["2026-06-18", "2026-06-19"]
    assert bars[0].code == "US.AAPL"
    assert bars[0].close == 2.0
    assert bars[1].volume == 30
