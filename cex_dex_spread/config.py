import os
from dataclasses import dataclass


@dataclass
class Config:
    rpc_url: str
    binance_ws_url: str = "wss://stream.binance.com:9443/ws"
    bybit_ws_url: str = "wss://stream.bybit.com/v5/public/spot"
    poll_interval: float = 1.0
    min_spread_pct: float = 0.3
    gas_price_gwei_override: float | None = None

    @classmethod
    def from_env(cls) -> "Config":
        rpc = os.getenv("RPC_URL", "https://cloudflare-eth.com")
        binance_ws = os.getenv("BINANCE_WS_URL", "wss://stream.binance.com:9443/ws")
        bybit_ws = os.getenv("BYBIT_WS_URL", "wss://stream.bybit.com/v5/public/spot")
        poll_str = os.getenv("POLL_INTERVAL", "1.0")
        spread_str = os.getenv("MIN_SPREAD_PCT", "0.3")
        gas_str = os.getenv("GAS_PRICE_GWEI")

        return cls(
            rpc_url=rpc,
            binance_ws_url=binance_ws,
            bybit_ws_url=bybit_ws,
            poll_interval=float(poll_str),
            min_spread_pct=float(spread_str),
            gas_price_gwei_override=float(gas_str) if gas_str else None,
        )
