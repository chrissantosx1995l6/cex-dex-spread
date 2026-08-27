from dataclasses import dataclass
from enum import Enum
import time


class TradeDirection(str, Enum):
    BUY_CEX_SELL_DEX = "BUY_CEX_SELL_DEX"
    BUY_DEX_SELL_CEX = "BUY_DEX_SELL_CEX"
    NONE = "NONE"


@dataclass(slots=True)
class CexQuote:
    exchange: str
    symbol: str
    bid_price: float
    ask_price: float
    bid_qty: float
    ask_qty: float
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass(slots=True)
class DexPoolState:
    pool_address: str
    dex_type: str
    token0_symbol: str
    token1_symbol: str
    token0_decimals: int
    token1_decimals: int
    raw_price: float
    block_number: int
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass(slots=True)
class SpreadOpportunity:
    direction: TradeDirection
    cex_price: float
    dex_price: float
    gross_spread_pct: float
    net_spread_pct: float
    est_profit_usd: float
    gas_cost_usd: float
    cex_exchange: str
    dex_pool: str
    timestamp: float = 0.0
