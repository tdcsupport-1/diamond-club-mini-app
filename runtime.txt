import os
from datetime import datetime, time

import pytz
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from market_data import get_market_snapshot

load_dotenv()

app = Flask(__name__)

SESSION_CONFIG = [
    {
        "name": "Sydney",
        "tz": "Australia/Sydney",
        "open": "08:00",
        "close": "17:00",
        "city": "Sydney",
    },
    {
        "name": "Tokyo",
        "tz": "Asia/Tokyo",
        "open": "09:00",
        "close": "18:00",
        "city": "Tokyo",
    },
    {
        "name": "London",
        "tz": "Europe/London",
        "open": "08:00",
        "close": "17:00",
        "city": "London",
    },
    {
        "name": "New York",
        "tz": "America/New_York",
        "open": "08:00",
        "close": "17:00",
        "city": "New York",
    },
]


def parse_hhmm(value):
    h, m = value.split(":")
    return time(int(h), int(m))


def is_session_open(local_now, open_str, close_str):
    open_t = parse_hhmm(open_str)
    close_t = parse_hhmm(close_str)
    current = local_now.time()

    # Weekends: market sessions should display closed.
    if local_now.weekday() >= 5:
        return False

    if open_t <= close_t:
        return open_t <= current < close_t
    return current >= open_t or current < close_t


def session_payload():
    now_utc = datetime.now(pytz.utc)
    sessions = []

    for item in SESSION_CONFIG:
        zone = pytz.timezone(item["tz"])
        local_now = now_utc.astimezone(zone)
        sessions.append(
            {
                "name": item["name"],
                "city": item["city"],
                "timezone": item["tz"],
                "abbr": local_now.tzname(),
                "openTime": item["open"],
                "closeTime": item["close"],
                "isOpen": is_session_open(local_now, item["open"], item["close"]),
                "localTime": local_now.strftime("%H:%M:%S"),
            }
        )

    london = now_utc.astimezone(pytz.timezone("Europe/London"))
    new_york = now_utc.astimezone(pytz.timezone("America/New_York"))

    return {
        "generatedAtUtc": now_utc.isoformat(),
        "uk": {
            "time": london.strftime("%H:%M:%S"),
            "date": london.strftime("%A, %d %B %Y"),
            "abbr": london.tzname(),
            "offset": london.strftime("UTC%z"),
        },
        "newYork": {
            "time": new_york.strftime("%H:%M:%S"),
            "date": new_york.strftime("%A, %d %B %Y"),
            "abbr": new_york.tzname(),
            "offset": new_york.strftime("UTC%z"),
        },
        "sessions": sessions,
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/sessions")
def api_sessions():
    return jsonify(session_payload())


@app.route("/api/markets")
def api_markets():
    return jsonify(get_market_snapshot())


@app.route("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
