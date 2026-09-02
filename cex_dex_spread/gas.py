import httpx

# typical gas units for standard ERC20 pool interactions
GAS_UNITS_V2_SWAP = 110_000
GAS_UNITS_V3_SWAP = 145_000
GAS_TRANSFER_OVERHEAD = 28_000


async def fetch_base_fee_gwei(rpc_urls: list[str], timeout: float = 3.0) -> float:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_gasPrice",
        "params": [],
    }
    for url in rpc_urls:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    body = res.json()
                    if "result" in body:
                        val = int(body["result"], 16)
                        return val / 1e9
        except Exception:
            continue
    # FIXME: fall back to a dynamic cache instead of hardcoded 25.0
    return 25.0


def estimate_swap_gas_cost_usd(
    version: str,
    gas_price_gwei: float,
    eth_usd_price: float,
    priority_gwei: float = 1.5,
    is_multihop: bool = False,
) -> float:
    base_units = GAS_UNITS_V3_SWAP if version == "v3" else GAS_UNITS_V2_SWAP
    if is_multihop:
        base_units += GAS_TRANSFER_OVERHEAD

    total_gwei = gas_price_gwei + priority_gwei
    cost_eth = (base_units * total_gwei) / 1e9
    return cost_eth * eth_usd_price
