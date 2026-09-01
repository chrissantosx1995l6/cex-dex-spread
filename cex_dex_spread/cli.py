import argparse
import asyncio
import sys
from decimal import Decimal
from cex_dex_spread.config import load_config
from cex_dex_spread.cex import fetch_cex_ticker
from cex_dex_spread.dex import fetch_dex_pool
from cex_dex_spread.gas import estimate_swap_gas_usd
from cex_dex_spread.spread import compute_spread


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Track real-time spreads between CEX spot and EVM DEX pools")
    p.add_argument("--config", "-c", help="Path to config TOML file", default="config.toml")
    p.add_argument("--cex", choices=["binance", "bybit"], default="binance", help="CEX venue")
    p.add_argument("--pair", default="ETH/USDT", help="Trading pair")
    p.add_argument("--pool", help="DEX pool contract address")
    p.add_argument("--rpc", help="EVM JSON-RPC URL")
    p.add_argument("--chain", default="ethereum", help="Chain name for gas estimation")
    p.add_argument("--size", type=float, default=1000.0, help="Trade notional in USD for net calc")
    p.add_argument("--watch", "-w", action="store_true", help="Stream updates")
    p.add_argument("--interval", type=float, default=2.0, help="Poll interval in seconds")
    return p.parse_args()


