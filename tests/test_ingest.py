import sqlite3
import pytest
from touzi_agent.models import MarketConfig
from touzi_agent.data.db import init_db, get_bars
from touzi_agent.adapters.markets import USDataAdapter
from touzi_agent.ingestion.ingest import ingest_bars


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    init_db(c)
    yield c
    c.close()


def test_ingest_fetches_and_persists(conn, fake_client):
    cfg = MarketConfig(market="US", currency="USD", settlement="T+0",
                       short_selling="allowed", code_prefix="US",
                       daily_limit=None, costs={})
    adapter = USDataAdapter(cfg, fake_client)
    written = ingest_bars(adapter, conn, "AAPL", "2026-06-18", "2026-06-19")
    assert written == 2
    stored = get_bars(conn, "US.AAPL", "2026-06-18", "2026-06-19")
    assert [b.date for b in stored] == ["2026-06-18", "2026-06-19"]
    assert fake_client.calls == [("US.AAPL", "2026-06-18", "2026-06-19", "K_DAY")]


def test_ingest_is_idempotent(conn, fake_client):
    cfg = MarketConfig(market="US", currency="USD", settlement="T+0",
                       short_selling="allowed", code_prefix="US",
                       daily_limit=None, costs={})
    adapter = USDataAdapter(cfg, fake_client)
    ingest_bars(adapter, conn, "AAPL", "2026-06-18", "2026-06-19")
    ingest_bars(adapter, conn, "AAPL", "2026-06-18", "2026-06-19")
    stored = get_bars(conn, "US.AAPL", "2026-06-18", "2026-06-19")
    assert len(stored) == 2  # no duplicate rows
