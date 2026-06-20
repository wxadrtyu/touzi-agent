import sqlite3

from touzi_agent.models import Bar, Instrument


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS instruments (
            code TEXT PRIMARY KEY, market TEXT NOT NULL, name TEXT,
            lot_size INTEGER NOT NULL, board TEXT NOT NULL)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS ohlcv (
            code TEXT NOT NULL, date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL,
            volume INTEGER, turnover REAL,
            PRIMARY KEY (code, date))"""
    )
    conn.commit()


def upsert_instrument(conn: sqlite3.Connection, inst: Instrument) -> None:
    conn.execute(
        """INSERT INTO instruments (code, market, name, lot_size, board)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(code) DO UPDATE SET
             market=excluded.market, name=excluded.name,
             lot_size=excluded.lot_size, board=excluded.board""",
        (inst.code, inst.market, inst.name, inst.lot_size, inst.board),
    )
    conn.commit()


def get_instrument(conn: sqlite3.Connection, code: str) -> Instrument | None:
    row = conn.execute(
        "SELECT code, market, name, lot_size, board FROM instruments "
        "WHERE code = ?", (code,)).fetchone()
    if row is None:
        return None
    return Instrument(*row)


def upsert_bars(conn: sqlite3.Connection, bars: list[Bar]) -> int:
    conn.executemany(
        """INSERT INTO ohlcv
             (code, date, open, high, low, close, volume, turnover)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(code, date) DO UPDATE SET
             open=excluded.open, high=excluded.high, low=excluded.low,
             close=excluded.close, volume=excluded.volume,
             turnover=excluded.turnover""",
        [(b.code, b.date, b.open, b.high, b.low, b.close,
          b.volume, b.turnover) for b in bars],
    )
    conn.commit()
    return len(bars)


def get_bars(conn: sqlite3.Connection, code: str,
             start: str, end: str) -> list[Bar]:
    rows = conn.execute(
        """SELECT code, date, open, high, low, close, volume, turnover
           FROM ohlcv WHERE code = ? AND date >= ? AND date <= ?
           ORDER BY date ASC""", (code, start, end)).fetchall()
    return [Bar(*row) for row in rows]
