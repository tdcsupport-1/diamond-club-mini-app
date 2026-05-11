<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <meta name="theme-color" content="#06111f" />
    <title>Diamond Club Session Dashboard</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <main class="app-shell">
      <section class="hero glass-card">
        <div class="hero-glow"></div>
        <img class="club-logo" src="/static/diamond-club-logo.png?v=3" alt="The Diamond Club logo" />
        <div class="hero-copy compact">
          <p class="eyebrow">Premium Trading Dashboard</p>
          <p class="subtitle">Session clocks · UK/NY time · live market movement</p>
        </div>
      </section>

      <section class="clock-grid glass-card">
        <div class="section-title">
          <span>◷</span>
          <h2>Session Clocks</h2>
        </div>
        <div id="session-cards" class="session-cards"></div>
      </section>

      <section class="time-panel glass-card">
        <div>
          <p class="panel-label">UK Time</p>
          <strong id="uk-time">--:--:--</strong>
          <span id="uk-date">Loading…</span>
          <em id="uk-zone">UK</em>
        </div>
        <div>
          <p class="panel-label">New York Time</p>
          <strong id="ny-time">--:--:--</strong>
          <span id="ny-date">Loading…</span>
          <em id="ny-zone">ET</em>
        </div>
      </section>

      <section class="market-panel glass-card">
        <div class="market-header">
          <div class="section-title no-margin">
            <span>▥</span>
            <h2>Market Update</h2>
          </div>
          <div class="live-dot"><span></span> Live</div>
        </div>
        <p id="data-warning" class="data-warning hidden"></p>
        <div id="market-list" class="market-list"></div>
        <footer id="data-footer">Powered by Vantage Markets data or similar</footer>
      </section>
    </main>

    <script src="/static/app.js"></script>
  </body>
</html>
