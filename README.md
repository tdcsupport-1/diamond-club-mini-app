# Get a free/paid API key from Twelve Data or use your broker/feed provider.
# Vantage Markets API is usually FIX/partner connectivity, not a simple retail REST feed.
MARKET_PROVIDER=twelvedata
TWELVE_DATA_API_KEY=put_your_key_here

# Optional: if Vantage or another provider gives you a JSON tick endpoint, set this URL.
# Expected JSON can be customized in market_data.py.
VANTAGE_TICK_FEED_URL=

# Flask settings
PORT=8000
FLASK_DEBUG=false
