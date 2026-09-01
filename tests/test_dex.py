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


