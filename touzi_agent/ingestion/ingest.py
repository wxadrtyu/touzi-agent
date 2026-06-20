import sqlite3

from touzi_agent.adapters.base import BaseDataAdapter
from touzi_agent.data.db import upsert_bars


def ingest_bars(adapter: BaseDataAdapter, conn: sqlite3.Connection,
                symbol: str, start: str, end: str) -> int:
    bars = adapter.fetch_bars(symbol, start, end)
    return upsert_bars(conn, bars)
