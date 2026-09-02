import httpx
from cex_dex_spread.models import DexPoolState

# Uniswap / Sushiswap method selectors
# getReserves() -> 0x0902f1ac
# slot0() -> 0x3850c7bd
# liquidity() -> 0x1a684256
SELECTOR_GET_RESERVES = "0x0902f1ac"
SELECTOR_SLOT0 = "0x3850c7bd"
SELECTOR_LIQUIDITY = "0x1a684256"


async def rpc_eth_call_with_failover(rpc_urls: list[str], to_addr: str, call_data: str, timeout: float = 3.5) -> str:
    """Execute raw eth_call trying each endpoint sequentially."""
    last_err = None
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": to_addr, "data": call_data}, "latest"],
    }
    for url in rpc_urls:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    continue
                body = resp.json()
                if "error" in body:
                    continue
                return body["result"]
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"all RPC endpoints failed for target {to_addr}: {last_err}")


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

    # tick is signed int24 sitting at word offset 32 bytes
    tick_word = int(clean[64:128], 16)
    if tick_word >= (1 << 255):
        # full 256-bit two's complement
        tick = tick_word - (1 << 256)
    else:
        # handles sign extension if only bottom 24 bits were populated
        tick = tick_word if tick_word < (1 << 23) else tick_word - (1 << 24)
    return sqrt_price_x96, tick


def v3_sqrt_price_to_human(sqrt_price_x96: int, dec0: int, dec1: int) -> float:
    # price = (sqrtPriceX96 / 2^96)^2 * 10^(dec0 - dec1)
    ratio = sqrt_price_x96 / float(1 << 96)
    price_raw = ratio * ratio
    return price_raw * (10 ** (dec0 - dec1))


async def fetch_v2_pool(rpc_urls: list[str], pool_address: str, dec0: int, dec1: int) -> DexPoolState:
    raw = await rpc_eth_call_with_failover(rpc_urls, pool_address, SELECTOR_GET_RESERVES)
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


async def fetch_v3_pool(rpc_urls: list[str], pool_address: str, dec0: int, dec1: int) -> DexPoolState:
    raw = await rpc_eth_call_with_failover(rpc_urls, pool_address, SELECTOR_SLOT0)
    sqrt_px, tick = decode_v3_slot0(raw)
    price = v3_sqrt_price_to_human(sqrt_px, dec0, dec1)

    # liquidity is optional for simple spread calculation, but useful for impact checks
    liq = 0
    try:
        liq_raw = await rpc_eth_call_with_failover(rpc_urls, pool_address, SELECTOR_LIQUIDITY)
        liq = int(liq_raw, 16)
    except Exception:
        # print(f"debug: failed to fetch liquidity for {pool_address}")
        pass

    return DexPoolState(
        pool_address=pool_address,
        version="v3",
        sqrt_price_x96=sqrt_px,
        tick=tick,
        liquidity=liq,
        price_token1_per_token0=price,
    )
