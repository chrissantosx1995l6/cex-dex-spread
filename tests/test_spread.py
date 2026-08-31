from decimal import Decimal
from cex_dex_spread.models import CexTicker, DexPool, DexProtocol, TradeDirection
from cex_dex_spread.spread import calculate_gross_spread, compute_spread


def test_gross_spread_buy_cex():
    cex_p = Decimal("2000.0")
    dex_p = Decimal("2020.0")  # 1% higher on DEX
    spread, direction = calculate_gross_spread(cex_p, dex_p)
    assert spread == Decimal("1.0")
    assert direction == TradeDirection.BUY_CEX_SELL_DEX


