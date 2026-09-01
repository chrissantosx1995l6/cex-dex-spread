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


async def run_once(args, cfg):
    rpc_url = args.rpc or cfg.get("rpc_url")
    pool_address = args.pool or cfg.get("default_pool")
    if not rpc_url or not pool_address:
        sys.exit("Error: both rpc_url and pool address are required")

    ticker_task = fetch_cex_ticker(args.cex, args.pair)
    pool_task = fetch_dex_pool(rpc_url, pool_address)
    gas_task = estimate_swap_gas_usd(rpc_url, args.chain)

    ticker, pool, gas_usd = await asyncio.gather(ticker_task, pool_task, gas_task)
    res = compute_spread(ticker, pool, gas_cost_usd=gas_usd, trade_size_usd=Decimal(str(args.size)))

    if not res:
        print("Failed to compute spread - invalid ticker or pool data")
        return

    print(f"[{res.pair}] {args.cex.upper()}={res.cex_price:.4f} | DEX={res.dex_price:.4f}")
    print(f"Direction: {res.direction.value}")
    print(f"Gross spread: {res.gross_spread_pct:+.2f}%")
    print(f"Net spread:   {res.net_spread_pct:+.2f}% (net pnl: ${res.net_profit_usd:+.2f})")
    print(f"Gas estimate: ${res.gas_cost_usd:.2f}")


def main():
    args = parse_args()
    cfg = load_config(args.config)
    asyncio.run(run_once(args, cfg))


if __name__ == "__main__":
    main()
