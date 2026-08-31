from decimal import Decimal
from typing import Optional
from cex_dex_spread.models import DexPool, CexTicker, SpreadResult, TradeDirection


def calculate_gross_spread(cex_price: Decimal, dex_price: Decimal) -> tuple[Decimal, TradeDirection]:
    if cex_price <= Decimal("0") or dex_price <= Decimal("0"):
        return Decimal("0"), TradeDirection.BUY_CEX_SELL_DEX

    if dex_price > cex_price:
        # Buy cheap on CEX, dump into DEX pool
        spread_pct = ((dex_price - cex_price) / cex_price) * Decimal("100")
        return spread_pct, TradeDirection.BUY_CEX_SELL_DEX
    else:
        # Buy cheap on DEX, sell on CEX
        spread_pct = ((cex_price - dex_price) / dex_price) * Decimal("100")
        return spread_pct, TradeDirection.BUY_DEX_SELL_CEX


def compute_spread(
    ticker: CexTicker,
    pool: DexPool,
    gas_cost_usd: Decimal = Decimal("0"),
    cex_fee_rate: Decimal = Decimal("0.001"),  # 10 bps default taker
    trade_size_usd: Decimal = Decimal("1000"),
) -> Optional[SpreadResult]:
    """Compute gross and net profit margin between CEX orderbook and DEX spot."""
    if ticker.ask <= Decimal("0") or ticker.bid <= Decimal("0") or pool.price <= Decimal("0"):
        return None

    # Pick relevant CEX leg
    # If DEX price > CEX ask -> buy on CEX at ask, sell on DEX
    # If DEX price < CEX bid -> buy on DEX, sell on CEX at bid
    if pool.price > ticker.ask:
        direction = TradeDirection.BUY_CEX_SELL_DEX
        cex_exec_price = ticker.ask
        dex_exec_price = pool.price
        gross_spread = ((dex_exec_price - cex_exec_price) / cex_exec_price) * Decimal("100")
    else:
        direction = TradeDirection.BUY_DEX_SELL_CEX
        cex_exec_price = ticker.bid
        dex_exec_price = pool.price
        gross_spread = ((cex_exec_price - dex_exec_price) / dex_exec_price) * Decimal("100")

    # Fee deductions
    cex_fee_usd = trade_size_usd * cex_fee_rate
    dex_fee_usd = trade_size_usd * pool.fee_rate

    gross_profit_usd = (gross_spread / Decimal("100")) * trade_size_usd
    total_costs_usd = cex_fee_usd + dex_fee_usd + gas_cost_usd
    net_profit_usd = gross_profit_usd - total_costs_usd
    net_spread_pct = (net_profit_usd / trade_size_usd) * Decimal("100") if trade_size_usd > Decimal("0") else Decimal("0")

    return SpreadResult(
        pair=ticker.symbol,
        direction=direction,
        cex_price=cex_exec_price,
        dex_price=dex_exec_price,
        gross_spread_pct=gross_spread,
        net_spread_pct=net_spread_pct,
        gross_profit_usd=gross_profit_usd,
        net_profit_usd=net_profit_usd,
        gas_cost_usd=gas_cost_usd,
        cex_fee_usd=cex_fee_usd,
        dex_fee_usd=dex_fee_usd,
        timestamp=ticker.timestamp,
    )
