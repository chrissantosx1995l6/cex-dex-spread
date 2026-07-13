# cex-dex-spread

CLI scanner that watches price divergence between CEX orderbooks (Binance, Bybit) and on-chain DEX pools (Uniswap v2/v3, Pancake, Camelot) via raw JSON-RPC calls.

I built this to avoid running heavy Web3 SDKs or local indexing nodes just to see if a pool is lagging behind spot movement.

## Quick start

```bash
pip install -e .
```

Run against an Arbitrum RPC for WETH/USDC:

```bash
cex-dex-spread \
  --cex binance \
  --pair ETH/USDT \
  --rpc https://arb1.arbitrum.io/rpc \
  --pool 0xC6962004f452bE9203591991D15f6b388e09E8D0 \
  --dex-type v3 \
  --interval 1.0
```
