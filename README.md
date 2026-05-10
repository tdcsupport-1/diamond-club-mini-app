# Diamond Club Telegram Mini App

This is a fresh Telegram Mini App for The Diamond Club.

It includes:

- Session clocks for Sydney, Tokyo, London and New York
- UK Time with automatic GMT/BST handling
- New York Time with automatic EST/EDT handling
- Market updates for major FX pairs, BTCUSD and XAUUSD
- Bullish/bearish percentage movement with 📈 / 📉
- Diamond Club themed UI using your supplied logo
- A Twelve Data adapter and a custom/Vantage-compatible adapter

## Important note on Vantage Markets data

Vantage Markets API connectivity is normally provided through FIX / partner API solutions rather than a simple public retail REST endpoint. If Vantage gives you a private feed endpoint, put it in `VANTAGE_TICK_FEED_URL` and set `MARKET_PROVIDER=vantage`.

For a quick working setup, use Twelve Data or another market data API.

## Install on Windows/VPS

Open CMD inside this folder and run:

```cmd
python -m pip install -r requirements.txt
```

Then create your env file:

```cmd
copy .env.example .env
notepad .env
```

Add your API key:

```env
MARKET_PROVIDER=twelvedata
TWELVE_DATA_API_KEY=your_key_here
PORT=8000
```

Run locally:

```cmd
python app.py
```

Open:

```text
http://127.0.0.1:8000
```

From outside your VPS, open:

```text
http://YOUR_SERVER_IP:8000
```

You may need to allow port 8000 in Windows Firewall:

```cmd
netsh advfirewall firewall add rule name="Diamond Club Mini App Port 8000" dir=in action=allow protocol=TCP localport=8000
```

## Telegram Mini App setup

Telegram Mini Apps need HTTPS. For production, put this behind a domain with SSL, or deploy it to Render/Railway/Fly.io.

In BotFather:

1. `/mybots`
2. Choose your bot
3. Bot Settings
4. Menu Button
5. Configure menu button
6. Paste your HTTPS URL
7. Name it: `Diamond Club`

## Deploy command examples

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

For simple VPS testing only:

```bash
python app.py
```
