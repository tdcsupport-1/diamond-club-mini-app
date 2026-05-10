import os
import random
from datetime import datetime

import requests

SYMBOLS = [
    {"symbol": "EUR/USD", "display": "EURUSD", "name": "Euro / U.S. Dollar", "decimals": 5},
    {"symbol": "GBP/USD", "display": "GBPUSD", "name": "British Pound / U.S. Dollar", "decimals": 5},
    {"symbol": "USD/JPY", "display": "USDJPY", "name": "U.S. Dollar / Japanese Yen", "decimals": 3},
    {"symbol": "AUD/USD", "display": "AUDUSD", "name": "Australian Dollar / U.S. Dollar", "decimals": 5},
    {"symbol": "USD/CAD", "display": "USDCAD", "name": "U.S. Dollar / Canadian Dollar", "decimals": 5},
    {"symbol": "USD/CHF", "display": "USDCHF", "name": "U.S. Dollar / Swiss Franc", "decimals": 5},
    {"symbol": "NZD/USD", "display": "NZDUSD", "name": "New Zealand Dollar / U.S. Dollar", "decimals": 5},
    {"symbol": "BTC/USD", "display": "BTCUSD", "name": "Bitcoin / U.S. Dollar", "decimals": 2},
    {"symbol": "XAU/USD", "display": "XAUUSD", "name": "Gold / U.S. Dollar", "decimals": 2},
]


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _demo_snapshot():
    base_prices = {
        "EURUSD": 1.08642,
        "GBPUSD": 1.27280,
        "USDJPY": 155.240,
        "AUDUSD": 0.66210,
        "USDCAD": 1.36720,
        "USDCHF": 0.90510,
        "NZDUSD": 0.60120,
        "BTCUSD": 67420.50,
        "XAUUSD": 2338.75,
    }
    rows = []
    for item in SYMBOLS:
        display = item["display"]
        pct = round(random.uniform(-0.65, 0.85), 2)
        price = base_prices[display] * (1 + random.uniform(-0.002, 0.002))
        rows.append(
            {
                "symbol": display,
                "providerSymbol": item["symbol"],
                "name": item["name"],
                "price": round(price, item["decimals"]),
                "percentChange": pct,
                "direction": "bullish" if pct >= 0 else "bearish",
                "emoji": "📈" if pct >= 0 else "📉",
                "isDemo": True,
            }
        )
    return {
        "provider": "demo",
        "updatedAt": datetime.utcnow().isoformat() + "Z",
        "markets": rows,
        "warning": "Demo prices are showing because no valid market data API key is configured.",
    }


def _twelvedata_snapshot():
    api_key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if not api_key or api_key == "put_your_key_here":
        return _demo_snapshot()

    symbol_string = ",".join([item["symbol"] for item in SYMBOLS])
    url = "https://api.twelvedata.com/quote"
    params = {"symbol": symbol_string, "apikey": api_key}
    response = requests.get(url, params=params, timeout=12)
    response.raise_for_status()
    payload = response.json()

    rows = []
    for item in SYMBOLS:
        symbol = item["symbol"]
        data = payload.get(symbol, {}) if isinstance(payload, dict) else {}

        # Twelve Data returns 'close' and 'percent_change' on quote responses.
        price = _safe_float(data.get("close") or data.get("price"))
        pct = _safe_float(data.get("percent_change"))

        rows.append(
            {
                "symbol": item["display"],
                "providerSymbol": symbol,
                "name": item["name"],
                "price": round(price, item["decimals"]),
                "percentChange": round(pct, 2),
                "direction": "bullish" if pct >= 0 else "bearish",
                "emoji": "📈" if pct >= 0 else "📉",
                "isDemo": False,
            }
        )

    return {
        "provider": "twelvedata",
        "updatedAt": datetime.utcnow().isoformat() + "Z",
        "markets": rows,
    }


def _vantage_or_custom_snapshot():
    """
    Placeholder adapter for Vantage Markets / broker tick feed.

    Many broker feeds are delivered through FIX, MT4/MT5 bridges, or a private partner
    endpoint rather than a simple public REST API. If your provider gives you a JSON
    endpoint, adapt this function to match their response shape.

    Expected sample JSON:
    {
      "EURUSD": {"price": 1.08642, "percent_change": 0.12},
      "XAUUSD": {"price": 2338.75, "percent_change": -0.21}
    }
    """
    feed_url = os.getenv("VANTAGE_TICK_FEED_URL", "").strip()
    if not feed_url:
        return _demo_snapshot()

    response = requests.get(feed_url, timeout=12)
    response.raise_for_status()
    data = response.json()

    rows = []
    for item in SYMBOLS:
        display = item["display"]
        raw = data.get(display, {})
        price = _safe_float(raw.get("price"))
        pct = _safe_float(raw.get("percent_change"))
        rows.append(
            {
                "symbol": display,
                "providerSymbol": display,
                "name": item["name"],
                "price": round(price, item["decimals"]),
                "percentChange": round(pct, 2),
                "direction": "bullish" if pct >= 0 else "bearish",
                "emoji": "📈" if pct >= 0 else "📉",
                "isDemo": False,
            }
        )

    return {
        "provider": "custom-vantage-compatible",
        "updatedAt": datetime.utcnow().isoformat() + "Z",
        "markets": rows,
    }


def get_market_snapshot():
    provider = os.getenv("MARKET_PROVIDER", "twelvedata").strip().lower()
    try:
        if provider in ("vantage", "custom"):
            return _vantage_or_custom_snapshot()
        return _twelvedata_snapshot()
    except Exception as exc:
        fallback = _demo_snapshot()
        fallback["provider"] = provider + ":error"
        fallback["warning"] = "Live data failed, showing demo fallback: %s" % exc
        return fallback
