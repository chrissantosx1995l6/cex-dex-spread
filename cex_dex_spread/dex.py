import httpx
from cex_dex_spread.models import DexPoolState

# function selectors
# getReserves() -> 0x0902f1ac
# slot0() -> 0x3850c7bd
SELECTOR_GET_RESERVES = "0x0902f1ac"
SELECTOR_SLOT0 = "0x3850c7bd"


async def rpc_eth_call(rpc_url: str, to_addr: str, call_data: str, timeout: float = 3.0) -> str:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": to_addr, "data": call_data}, "latest"],
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(rpc_url, json=payload)
        resp.raise_for_status()
        body = resp.json()
        if "error" in body:
            raise RuntimeError(f"RPC error: {body['error']}")
        return body["result"]


def decode_v2_reserves(raw_hex: str) -> tuple[int, int, int]:
    clean = raw_hex[2:] if raw_hex.startswith("0x") else raw_hex
    if len(clean) < 192:
        raise ValueError(f"unexpected getReserves output length: {len(clean)}")
    r0 = int(clean[0:64], 16)
    r1 = int(clean[64:128], 16)
    ts = int(clean[128:192], 16)
    return r0, r1, ts


def decode_v3_slot0(raw_hex: str) -> tuple[int, int]:
    clean = raw_hex[2:] if raw_hex.startswith("0x") else raw_hex
    if len(clean) < 128:
        raise ValueError(f"unexpected slot0 output length: {len(clean)}")
    sqrt_price_x96 = int(clean[0:64], 16)
    # tick is signed int24 packed in word 2
    raw_tick = int(clean[64:128], 16)
    if raw_tick >= (1 << 23):
        raw_tick -= 1 << 24
    return sqrt_price_x96, raw_tick


def v3_sqrt_price_to_human(sqrt_price_x96: int, dec0: int, dec1: int) -> float:
    # price = (sqrtPriceX96 / 2^96)^2 * 10^(dec0 - dec1)
    ratio = sqrt_price_x96 / (1 << 96)
    price_raw = ratio * ratio
    return price_raw * (10 ** (dec0 - dec1))


async def fetch_v2_pool(rpc_url: str, pool_address: str, dec0: int, dec1: int) -> DexPoolState:
    raw = await rpc_eth_call(rpc_url, pool_address, SELECTOR_GET_RESERVES)
    r0, r1, _ = decode_v2_reserves(raw)
    h0 = r0 / (10 ** dec0)
    h1 = r1 / (10 ** dec1)
    price = h1 / h0 if h0 > 0 else 0.0
    return DexPoolState(
        pool_address=pool_address,
        version="v2",
        token0_reserve=r0,
        token1_reserve=r1,
        price_token1_per_token0=price,
    )


async def fetch_v3_pool(rpc_url: str, pool_address: str, dec0: int, dec1: int) -> DexPoolState:
    raw = await rpc_eth_call(rpc_url, pool_address, SELECTOR_SLOT0)
    sqrt_px, tick = decode_v3_slot0(raw)
    price = v3_sqrt_price_to_human(sqrt_px, dec0, dec1)
    return DexPoolState(
        pool_address=pool_address,
        version="v3",
        sqrt_price_x96=sqrt_px,
        tick=tick,
        price_token1_per_token0=price,
    )
