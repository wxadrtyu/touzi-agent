from typing import Protocol


class FutuClient(Protocol):
    def get_history_kline(self, code: str, start: str, end: str,
                          ktype: str = "K_DAY") -> list[dict]:
        ...


class RealFutuClient:
    """Wraps 富途 OpenQuoteContext. Requires a running OpenD gateway.

    Not exercised by unit tests; used in production/integration only.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        from futu import OpenQuoteContext
        self._ctx = OpenQuoteContext(host=host, port=port)

    def get_history_kline(self, code: str, start: str, end: str,
                          ktype: str = "K_DAY") -> list[dict]:
        from futu import RET_OK, KLType
        ret, data = self._ctx.request_history_kline(
            code, start=start, end=end,
            ktype=getattr(KLType, ktype))
        if ret != RET_OK:
            raise RuntimeError(f"富途 history kline failed: {data}")
        return data.to_dict("records")

    def close(self) -> None:
        self._ctx.close()
