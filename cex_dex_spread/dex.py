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


