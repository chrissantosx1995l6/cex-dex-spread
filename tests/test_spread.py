from decimal import Decimal
from cex_dex_spread.models import CexTicker, DexPool, DexProtocol, TradeDirection
from cex_dex_spread.spread import calculate_gross_spread, compute_spread


def test_gross_spread_buy_cex():
    cex_p = Decimal("2000.0")
    dex_p = Decimal("2020.0")  # 1% higher on DEX
    spread, direction = calculate_gross_spread(cex_p, dex_p)
    assert spread == Decimal("1.0")
    assert direction == TradeDirection.BUY_CEX_SELL_DEX


def test_gross_spread_buy_dex():
    cex_p = Decimal("2000.0")
    dex_p = Decimal("1980.0")  # 1.01% cheaper on DEX
    spread, direction = calculate_gross_spread(cex_p, dex_p)
    assert direction == TradeDirection.BUY_DEX_SELL_CEX
    assert spread > Decimal("1.0")


def test_compute_spread_profitable():
    ticker = CexTicker(
        symbol="ETH/USDT",
        bid=Decimal("2000.0"),
        ask=Decimal("2000.0"),
        timestamp=1700000000.0,
    )
    pool = DexPool(
        address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        protocol=DexProtocol.UNISWAP_V3,
        token0="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        token1="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        price=Decimal("2050.0"),  # 2.5% premium
        fee_rate=Decimal("0.0005"),  # 5 bps
        reserve0=Decimal("100"),
        reserve1=Decimal("200000"),
    )

    res = compute_spread(
        ticker=ticker,
        pool=pool,
        gas_cost_usd=Decimal("5.0"),
        cex_fee_rate=Decimal("0.001"),  # 10 bps
        trade_size_usd=Decimal("2000.0"),
    )

    assert res is not None
    assert res.direction == TradeDirection.BUY_CEX_SELL_DEX
    assert res.gross_spread_pct == Decimal("2.5")
    # Gross pnl = 2.5% of 2000 = $50
    # cex fee = 2000 * 0.001 = $2
    # dex fee = 2000 * 0.0005 = $1
    # gas = $5
    # net = 50 - 8 = $42
    assert res.net_profit_usd == Decimal("42.0")
    assert res.net_spread_pct == Decimal("2.1")


def test_compute_spread_zero_price():
    ticker = CexTicker(symbol="ETH/USDT", bid=Decimal("0"), ask=Decimal("0"), timestamp=0.0)
    pool = DexPool(
        address="0x123",
        protocol=DexProtocol.UNISWAP_V2,
        token0="0x1",
        token1="0x2",
        price=Decimal("100"),
        fee_rate=Decimal("0.003"),
        reserve0=Decimal("10"),
        reserve1=Decimal("1000"),
    )
    assert compute_spread(ticker, pool) is None
