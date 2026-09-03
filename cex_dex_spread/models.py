from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time


class TradeDirection(str, Enum):
    BUY_CEX_SELL_DEX = "BUY_CEX_SELL_DEX"
    BUY_DEX_SELL_CEX = "BUY_DEX_SELL_CEX"
    NONE = "NONE"


class DexProtocol(str, Enum):
    V2 = "v2"
    V3 = "v3"


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

    @property
    def mid_price(self) -> float:
        return (self.bid_price + self.ask_price) / 2.0


@dataclass(slots=True)
class DexPoolState:
    """Snapshot of an on-chain liquidity pool state retrieved via eth_call."""
    pool_address: str
    dex_type: DexProtocol
    token0_symbol: str
    token1_symbol: str
    token0_decimals: int
    token1_decimals: int
    raw_price: float
    block_number: int
    fee_bps: int = 30
    # V2 reserves
    reserve0: Optional[int] = None
    reserve1: Optional[int] = None
    # V3 specifics
    sqrt_price_x96: Optional[int] = None
    tick: Optional[int] = None
    liquidity: Optional[int] = None
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    # print(f"DEBUG: raw tick {self.tick} price {self.raw_price}")

    def get_effective_price(self, trade_size_usd: float, is_buying_token0: bool) -> float:
        # TODO: integrate full tick-math walk for large V3 swaps instead of constant slip estimate
        base_price = self.raw_price
        fee_multiplier = 1.0 - (self.fee_bps / 10000.0)

        if self.dex_type == DexProtocol.V2 and self.reserve0 and self.reserve1:
            # quick constant product slippage approximation
            token0_price = base_price if is_buying_token0 else (1.0 / base_price if base_price > 0 else 0)
            reserve_val = (self.reserve0 / (10 ** self.token0_decimals)) * base_price
            if reserve_val > 0:
                impact = trade_size_usd / reserve_val
                return base_price * (1.0 + impact) if is_buying_token0 else base_price * (1.0 - impact)

        return base_price * fee_multiplier


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
    trade_size_usd: float = 0.0
    block_number: int = 0
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()
