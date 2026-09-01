from decimal import Decimal
from cex_dex_spread.dex import sqrt_price_x96_to_price, v2_reserves_to_price


def test_v2_reserves_to_price():
    # WETH (18 dec) / USDT (6 dec)
    # reserve0: 100 WETH = 100 * 10^18
    # reserve1: 300,000 USDT = 300_000 * 10^6
    r0 = 100 * 10**18
    r1 = 300_000 * 10**6
    price = v2_reserves_to_price(r0, r1, decimals0=18, decimals1=6)
    assert price == Decimal("3000.0")


def test_v2_zero_reserves():
    price = v2_reserves_to_price(0, 1000, 18, 6)
    assert price == Decimal("0")


def test_sqrt_price_x96_decoding():
    # Uni v3 ETH/USDC pool where ETH is token0 (18 dec), USDC is token1 (6 dec)
    # sqrtPriceX96 for ETH = 2500 USDC:
    # price = (sqrtPriceX96 / 2^96)^2 * 10^(18 - 6)
    # sqrt(2500 / 10^12) * 2^96
    # Let's test standard 1:1 price with same decimals
    # sqrtPrice = 2^96 => price = 1.0
    q96 = 2**96
    p1 = sqrt_price_x96_to_price(q96, decimals0=18, decimals1=18)
    assert round(p1, 4) == Decimal("1.0000")

    # 2x price token1/token0
    # sqrt(2) * 2^96 ~ 1.41421356 * 2^96
    sqrt_2 = int(Decimal("1.414213562373095048801688724") * Decimal(2**96))
    p2 = sqrt_price_x96_to_price(sqrt_2, decimals0=18, decimals1=18)
    assert round(p2, 3) == Decimal("2.000")
