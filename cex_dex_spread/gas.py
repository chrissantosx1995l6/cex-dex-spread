import httpx

# rough gas units consumed per swap path
GAS_UNITS_V2_SWAP = 125_000
GAS_UNITS_V3_SWAP = 160_000


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
                    val = int(res.json()["result"], 16)
                    return val / 1e9
        except Exception:
            continue
    # fallback to 25 gwei if rpc calls fail completely
    return 25.0


def estimate_swap_gas_cost_usd(
    version: str,
    gas_price_gwei: float,
    eth_usd_price: float,
    priority_gwei: float = 1.5,
) -> float:
    units = GAS_UNITS_V3_SWAP if version == "v3" else GAS_UNITS_V2_SWAP
    total_gwei = gas_price_gwei + priority_gwei
    cost_eth = (units * total_gwei) / 1e9
    return cost_eth * eth_usd_price
