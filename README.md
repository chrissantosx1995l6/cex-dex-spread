# cex-dex-spread

CLI scanner that watches price divergence between CEX orderbooks (Binance, Bybit) and on-chain DEX pools (Uniswap v2/v3, Pancake, Camelot) via raw JSON-RPC calls.

I built this to avoid running heavy Web3 SDKs or local indexing nodes just to see if a pool is lagging behind spot movement.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

Arbitrum Uniswap v3 WETH/USDC vs Binance ETHUSDT:

```bash
cex-dex-spread \
  --cex binance \
  --pair ETHUSDT \
  --rpc https://arb1.arbitrum.io/rpc \
  --pool 0xC6962004f452bE9203591991D15f6b388e09E8D0 \
  --dex-type v3 \
  --gas-price-gwei 0.1 \
  --trade-size 2500
```

Track a Uniswap v2 pair on Ethereum mainnet:

```bash
cex-dex-spread \
  --cex bybit \
  --pair ETHUSDT \
  --rpc $ETH_RPC_URL \
  --pool 0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc \
  --dex-type v2 \
  --threshold 0.35
```

## CLI Flags

- `--cex`: `binance` or `bybit` (uses public WS streams).
- `--rpc`: HTTP URL of an EVM node.
- `--pool`: Pair or Pool contract hex address.
- `--dex-type`: `v2` (reads `getReserves()`) or `v3` (reads `slot0()`).
- `--trade-size`: Nominal size in USD used to calculate estimated slippage.
- `--threshold`: Minimum net spread percentage to highlight in table (default: `0.20`).
- `--poll-ms`: Polling interval for RPC contract calls in milliseconds (default: `800`).

<!-- refreshed: 2026-09-09 -->
