const sessionCards = document.getElementById("session-cards");
const marketList = document.getElementById("market-list");
const warning = document.getElementById("data-warning");
const footer = document.getElementById("data-footer");

function initTelegram() {
  if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    tg.setHeaderColor("#06111f");
    tg.setBackgroundColor("#030812");
  }
}

function renderSessions(data) {
  document.getElementById("uk-time").textContent = data.uk.time;
  document.getElementById("uk-date").textContent = data.uk.date;
  document.getElementById("uk-zone").textContent = `${data.uk.abbr} (${formatOffset(data.uk.offset)})`;

  document.getElementById("ny-time").textContent = data.newYork.time;
  document.getElementById("ny-date").textContent = data.newYork.date;
  document.getElementById("ny-zone").textContent = `${data.newYork.abbr} (${formatOffset(data.newYork.offset)})`;

  sessionCards.innerHTML = data.sessions.map((session) => `
    <article class="session-card ${session.isOpen ? "open" : ""}">
      <h3>${session.name}</h3>
      <span class="status">${session.isOpen ? "OPEN" : "CLOSED"}</span>
      <span class="session-time">${session.openTime} - ${session.closeTime}</span>
      <span class="session-zone">${session.abbr}</span>
      <span class="local-time">${session.localTime}</span>
    </article>
  `).join("");
}

function formatOffset(offset) {
  if (!offset || offset.length < 8) return offset;
  const compact = offset.replace("UTC", "");
  return `UTC${compact.slice(0, 3)}:${compact.slice(3)}`;
}

function renderMarkets(data) {
  if (data.warning) {
    warning.textContent = data.warning;
    warning.classList.remove("hidden");
  } else {
    warning.classList.add("hidden");
  }

  const providerName = data.provider === "twelvedata"
    ? "Twelve Data market feed"
    : data.provider === "demo"
      ? "Demo data"
      : "Vantage/custom market feed";

  footer.textContent = `Powered by ${providerName} • Updated ${new Date(data.updatedAt).toLocaleTimeString()}`;

  marketList.innerHTML = data.markets.map((row) => {
    const cls = row.direction === "bullish" ? "bullish" : "bearish";
    const sign = row.percentChange >= 0 ? "+" : "";
    return `
      <article class="market-row">
        <div>
          <span class="symbol">${row.symbol}</span>
          <span class="name">${row.name}</span>
        </div>
        <strong class="price">${formatPrice(row.price)}</strong>
        <span class="change ${cls}">${sign}${row.percentChange.toFixed(2)}% ${row.emoji}</span>
      </article>
    `;
  }).join("");
}

function formatPrice(price) {
  if (Number(price) >= 1000) {
    return Number(price).toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  return Number(price).toLocaleString(undefined, { maximumFractionDigits: 5 });
}

async function refreshSessions() {
  const response = await fetch("/api/sessions", { cache: "no-store" });
  renderSessions(await response.json());
}

async function refreshMarkets() {
  const response = await fetch("/api/markets", { cache: "no-store" });
  renderMarkets(await response.json());
}

async function boot() {
  initTelegram();
  await Promise.all([refreshSessions(), refreshMarkets()]);
  setInterval(refreshSessions, 1000);
  setInterval(refreshMarkets, 60000);
}

boot().catch((error) => {
  console.error(error);
  warning.textContent = "Unable to load dashboard data. Check the server logs.";
  warning.classList.remove("hidden");
});
