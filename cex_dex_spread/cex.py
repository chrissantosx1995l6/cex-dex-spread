import json
import asyncio
import httpx
import websockets
from cex_dex_spread.models import TickerQuote


async def fetch_binance_rest(symbol: str) -> TickerQuote:
    url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol.upper()}"
    async with httpx.AsyncClient(timeout=3.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        return TickerQuote(
            venue="binance",
            symbol=symbol.upper(),
            bid=float(data["bidPrice"]),
            ask=float(data["askPrice"]),
            bid_size=float(data["bidQty"]),
            ask_size=float(data["askQty"]),
        )


async def fetch_bybit_rest(symbol: str) -> TickerQuote:
    url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol.upper()}"
    async with httpx.AsyncClient(timeout=3.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        res = data.get("result", {}).get("list", [])
        if not res:
            raise ValueError(f"no bybit ticker data for {symbol}")
        item = res[0]
        return TickerQuote(
            venue="bybit",
            symbol=symbol.upper(),
            bid=float(item["bid1Price"]),
            ask=float(item["ask1Price"]),
            bid_size=float(item["bid1Size"]),
            ask_size=float(item["ask1Size"]),
        )


async def stream_binance_book(symbol: str, queue: asyncio.Queue[TickerQuote], ws_url: str):
    stream_name = f"{symbol.lower()}@bookTicker"
    url = f"{ws_url.rstrip('/')}/{stream_name}"
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, close_timeout=5) as ws:
                async for msg in ws:
                    data = json.loads(msg)
                    if "b" not in data or "a" not in data:
                        continue
                    quote = TickerQuote(
                        venue="binance",
                        symbol=symbol.upper(),
                        bid=float(data["b"]),
                        ask=float(data["a"]),
                        bid_size=float(data["B"]),
                        ask_size=float(data["A"]),
                    )
                    await queue.put(quote)
        except (websockets.ConnectionClosed, OSError, asyncio.TimeoutError):
            await asyncio.sleep(1.0)


async def stream_bybit_book(symbol: str, queue: asyncio.Queue[TickerQuote], ws_url: str):
    sub_msg = json.dumps({
        "op": "subscribe",
        "args": [f"orderbook.1.{symbol.upper()}"]
    })
    while True:
        try:
            async with websockets.connect(ws_url, ping_interval=20, close_timeout=5) as ws:
                await ws.send(sub_msg)
                async for msg in ws:
                    data = json.loads(msg)
                    if data.get("op") == "ping":
                        await ws.send(json.dumps({"op": "pong"}))
                        continue
                    payload = data.get("data")
                    if not payload:
                        continue
                    bids = payload.get("b", [])
                    asks = payload.get("a", [])
                    if not bids or not asks:
                        continue
                    quote = TickerQuote(
                        venue="bybit",
                        symbol=symbol.upper(),
                        bid=float(bids[0][0]),
                        ask=float(asks[0][0]),
                        bid_size=float(bids[0][1]),
                        ask_size=float(asks[0][1]),
                    )
                    await queue.put(quote)
        except (websockets.ConnectionClosed, OSError, asyncio.TimeoutError):
            await asyncio.sleep(1.0)
