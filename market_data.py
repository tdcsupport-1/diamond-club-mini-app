import os
import random
import time
from datetime import datetime

import requests

SYMBOLS = [
    {"symbol": "EUR/USD", "display": "EURUSD", "name": "Euro / U.S. Dollar", "decimals": 5},
    {"symbol": "GBP/USD", "display": "GBPUSD", "name": "British Pound / U.S. Dollar", "decimals": 5},
    {"symbol": "USD/JPY", "display": "USDJPY", "name": "U.S. Dollar / Japanese Yen", "decimals": 3},
    {"symbol": "AUD/USD", "display": "AUDUSD", "name": "Australian Dollar / U.S. Dollar", "decimals": 5},
    {"symbol": "USD/CAD", "display": "USDCAD", "name": "U.S. Dollar / Canadian Dollar", "decimals": 5},
    {"symbol": "NZD/USD", "display": "NZDUSD", "name": "New Zealand Dollar / U.S. Dollar", "decimals": 5},
    {"symbol": "BTC/USD", "display": "BTCUSD", "name": "Bitcoin / U.S. Dollar", "decimals": 2},
    {"symbol": "XAU/USD", "display": "XAUUSD", "name": "Gold / U.S. Dollar", "decimals": 2},
]

_CACHE = {"expires": 0, "snapshot": None}
CACHE_SECONDS = int(os.getenv("MARKET_CACHE_SECONDS", "120"))


def _safe_float(value, default=0.0):
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _direction_and_emoji(pct):
    return ("bullish", "📈") if pct >= 0 else ("bearish", "📉")


def _row(item, price, pct, provider_symbol=None, is_demo=False):
    direction, emoji = _direction_and_emoji(pct)
    return {
        "symbol": item["display"],
        "providerSymbol": provider_symbol or item["symbol"],
        "name": item["name"],
        "price": round(_safe_float(price), item["decimals"]),
        "percentChange": round(_safe_float(pct), 2),
        "direction": direction,
        "emoji": emoji,
        "isDemo": is_demo,
    }


def _demo_snapshot():
    base_prices = {
        "EURUSD": 1.08642,
        "GBPUSD": 1.27280,
        "USDJPY": 155.240,
        "AUDUSD": 0.66210,
        "USDCAD": 1.36720,
        "NZDUSD": 0.60120,
        "BTCUSD": 67420.50,
        "XAUUSD": 2338.75,
    }
    rows = []
    for item in SYMBOLS:
        display = item["display"]
        pct = round(random.uniform(-0.65, 0.85), 2)
        price = base_prices[display] * (1 + random.uniform(-0.002, 0.002))
        rows.append(_row(item, price, pct, is_demo=True))
    return {
        "provider": "demo",
        "updatedAt": datetime.utcnow().isoformat() + "Z",
        "markets": rows,
        "warning": "Demo prices are showing because no valid market data API key is configured.",
    }


def _extract_quote_from_payload(payload, item):
    """Handle both Twelve Data batch and single-symbol response shapes."""
    if not isinstance(payload, dict):
        return {}

    symbol = item["symbol"]
    display = item["display"]

    # Single quote response: {"symbol":"EUR/USD", "close":"...", ...}
    if payload.get("symbol") in (symbol, display):
        return payload

    # Batch response usually: {"EUR/USD": {...}, "GBP/USD": {...}}
    for key in (symbol, display, symbol.replace("/", "")):
        if isinstance(payload.get(key), dict):
            return payload[key]

    # Some providers append exchange/type into the key.
    for key, value in payload.items():
        if not isinstance(value, dict):
            continue
        compact_key = str(key).replace("/", "").upper()
        compact_symbol = symbol.replace("/", "").upper()
        if compact_symbol in compact_key or compact_key in compact_symbol:
            return value
        if value.get("symbol") in (symbol, display):
            return value

    # Some endpoints return {"data":[{...}, {...}]}
    data_list = payload.get("data")
    if isinstance(data_list, list):
        for value in data_list:
            if not isinstance(value, dict):
                continue
            if value.get("symbol") in (symbol, display):
                return value

    return {}


def _price_and_percent_from_quote(data):
    # Twelve Data quote fields commonly include close, previous_close, change, percent_change.
    price = _safe_float(
        data.get("close")
        or data.get("price")
        or data.get("last")
        or data.get("last_price")
    )

    pct = _safe_float(data.get("percent_change"), None)
    if pct is None:
        change = _safe_float(data.get("change"), None)
        previous_close = _safe_float(data.get("previous_close") or data.get("prev_close"), None)
        if change is not None and previous_close not in (None, 0):
            pct = (change / previous_close) * 100
        else:
            pct = 0.0

    return price, pct


def _twelvedata_price_only(symbol, api_key):
    response = requests.get(
        "https://api.twelvedata.com/price",
        params={"symbol": symbol, "apikey": api_key},
        timeout=12,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and payload.get("status") == "error":
        raise RuntimeError(payload.get("message", "Twelve Data price error"))
    return _safe_float(payload.get("price"))


def _twelvedata_single_quote(item, api_key):
    response = requests.get(
        "https://api.twelvedata.com/quote",
        params={"symbol": item["symbol"], "apikey": api_key},
        timeout=12,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and payload.get("status") == "error":
        raise RuntimeError(payload.get("message", "Twelve Data quote error"))
    data = _extract_quote_from_payload(payload, item) or payload
    price, pct = _price_and_percent_from_quote(data)
    if price == 0:
        price = _twelvedata_price_only(item["symbol"], api_key)
    return price, pct


def _twelvedata_snapshot_uncached():
    api_key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if not api_key or api_key == "put_your_key_here":
        return _demo_snapshot()

    symbol_string = ",".join([item["symbol"] for item in SYMBOLS])
    errors = []

    # First try one efficient batch quote request.
    batch_payload = None
    try:
        response = requests.get(
            "https://api.twelvedata.com/quote",
            params={"symbol": symbol_string, "apikey": api_key},
            timeout=12,
        )
        response.raise_for_status()
        batch_payload = response.json()
        if isinstance(batch_payload, dict) and batch_payload.get("status") == "error":
            errors.append(batch_payload.get("message", "Twelve Data batch error"))
            batch_payload = None
    except Exception as exc:
        errors.append("Batch quote failed: %s" % exc)
        batch_payload = None

    rows = []
    for item in SYMBOLS:
        price = 0.0
        pct = 0.0
        source = item["symbol"]

        if batch_payload:
            data = _extract_quote_from_payload(batch_payload, item)
            if data:
                price, pct = _price_and_percent_from_quote(data)

        # If batch did not include usable data, fall back to a single symbol quote.
        if price == 0:
            try:
                price, pct = _twelvedata_single_quote(item, api_key)
            except Exception as exc:
                errors.append("%s failed: %s" % (item["symbol"], exc))

        rows.append(_row(item, price, pct, provider_symbol=source, is_demo=False))

    snapshot = {
        "provider": "twelvedata",
        "updatedAt": datetime.utcnow().isoformat() + "Z",
        "markets": rows,
    }

    if errors:
        snapshot["warning"] = "Some symbols could not be loaded: " + " | ".join(errors[:4])

    if all(row["price"] == 0 for row in rows):
        snapshot["warning"] = snapshot.get("warning", "") + " No live prices returned. Check API key, plan permissions, and symbol access."

    return snapshot


def _twelvedata_snapshot():
    now = time.time()
    if _CACHE["snapshot"] is not None and now < _CACHE["expires"]:
        return _CACHE["snapshot"]

    snapshot = _twelvedata_snapshot_uncached()
    _CACHE["snapshot"] = snapshot
    _CACHE["expires"] = now + CACHE_SECONDS
    return snapshot


def _vantage_or_custom_snapshot():
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
        rows.append(_row(item, price, pct, provider_symbol=display, is_demo=False))

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
