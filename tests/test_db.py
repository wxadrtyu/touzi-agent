import sqlite3
import pytest
from touzi_agent.models import Bar, Instrument
from touzi_agent.data.db import (
    init_db, upsert_instrument, get_instrument, upsert_bars, get_bars,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    init_db(c)
    yield c
    c.close()


def test_instrument_roundtrip(conn):
    inst = Instrument(code="US.AAPL", market="US", name="Apple",
                      lot_size=1, board="main_board")
    upsert_instrument(conn, inst)
    assert get_instrument(conn, "US.AAPL") == inst
    assert get_instrument(conn, "US.MISSING") is None


def test_bars_insert_and_range_query(conn):
    bars = [
        Bar("US.AAPL", "2026-06-17", 1, 2, 0.5, 1.5, 10, 15.0),
        Bar("US.AAPL", "2026-06-18", 1.5, 2.5, 1, 2.0, 20, 40.0),
        Bar("US.AAPL", "2026-06-19", 2.0, 3, 1.8, 2.8, 30, 84.0),
    ]
    assert upsert_bars(conn, bars) == 3
    got = get_bars(conn, "US.AAPL", "2026-06-18", "2026-06-19")
    assert [b.date for b in got] == ["2026-06-18", "2026-06-19"]
    assert got[0].close == 2.0


def test_bars_upsert_overwrites(conn):
    upsert_bars(conn, [Bar("US.AAPL", "2026-06-19", 1, 1, 1, 1, 1, 1.0)])
    upsert_bars(conn, [Bar("US.AAPL", "2026-06-19", 2, 2, 2, 2, 2, 2.0)])
    got = get_bars(conn, "US.AAPL", "2026-06-19", "2026-06-19")
    assert len(got) == 1
    assert got[0].close == 2.0
