#!/usr/bin/env python3
"""Live web dashboard + REST API over the pickup monitor's SQLite history.

Reads the same pickup_history.db that monitor.py writes. Meant to run 24/7
alongside the monitor (e.g. via launchd). The page auto-refreshes every 15s,
shows a live pulse, relative "checked N ago" times, and a running feed of the
most recent checks so you can see the 3-minute cadence happening.

    pip3 install flask
    python3 dashboard.py                 # http://localhost:5001  (debug/reloader)
    python3 dashboard.py --production     # no reloader (use this under launchd)

REST API (all JSON):
    GET /api/current                       latest state per store + per colour
    GET /api/history?store=R744&hours=24   raw per-store checks
    GET /api/changes?days=7&became=1       colour buyability change events
    GET /api/stats?days=7                  per-store totals / verified rate
"""
import os
from flask import Flask, jsonify, request, render_template_string

import db

DB_PATH = os.environ.get("DB_PATH", "pickup_history.db")
POLL_SECONDS = int(os.environ.get("DASHBOARD_POLL_SECONDS", "15"))
app = Flask(__name__)


def _no_cache(resp):
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/api/current")
def api_current():
    return _no_cache(jsonify(db.current_status(DB_PATH)))


@app.route("/api/history")
def api_history():
    store = request.args.get("store")
    hours = request.args.get("hours", 24, type=int)
    limit = request.args.get("limit", 30, type=int)
    return _no_cache(jsonify(db.history(store, hours, limit, DB_PATH)))


@app.route("/api/changes")
def api_changes():
    days = request.args.get("days", 7, type=int)
    became = request.args.get("became", 0, type=int) == 1
    return _no_cache(jsonify(db.changes(days, became, db_path=DB_PATH)))


@app.route("/api/stats")
def api_stats():
    days = request.args.get("days", 7, type=int)
    return _no_cache(jsonify(db.stats(days, DB_PATH)))


@app.route("/api/test_telegram", methods=["POST", "GET"])
def api_test_telegram():
    try:
        import monitor
        monitor.send_telegram("🔔 Test alert: Telegram connection is active and working!")
        return _no_cache(jsonify({"ok": True, "message": "Test alert sent to Telegram!"}))
    except Exception as e:
        return _no_cache(jsonify({"ok": False, "error": str(e)})), 500



PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>iPhone 17 Pickup Monitor</title>
<style>
  :root { --bg:#f5f5f7; --card:#fff; --ink:#1d1d1f; --muted:#86868b;
          --ok:#1a7f37; --bad:#b42318; --warn:#9a6700; --line:#e3e3e6; --brand:#0071e3; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#000; --card:#1c1c1e; --ink:#f5f5f7; --muted:#8e8e93;
            --line:#2c2c2e; }
  }
  * { box-sizing:border-box; }
  body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
         background:var(--bg); color:var(--ink); }
  header { padding:22px 20px 6px; }
  .wrap { max-width:960px; margin:0 auto; }
  h1 { font-size:22px; margin:0 0 4px; }
  .sub { color:var(--muted); font-size:13px; }
  main { max-width:960px; margin:0 auto; padding:12px 16px 48px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; }
  .card h2 { font-size:16px; margin:0; }
  .pill { display:inline-block; padding:3px 11px; border-radius:999px; font-size:12px; font-weight:700; letter-spacing:.02em; }
  .pill.ok { background:rgba(26,127,55,.15); color:var(--ok); }
  .pill.bad { background:rgba(180,35,24,.13); color:var(--bad); }
  .pill.warn { background:rgba(154,103,0,.15); color:var(--warn); }
  .colours { margin-top:12px; display:flex; flex-wrap:wrap; gap:6px; }
  .swatch { font-size:12px; padding:3px 9px; border-radius:8px; border:1px solid var(--line); color:var(--muted); }
  .swatch.ok { border-color:var(--ok); color:var(--ok); font-weight:600; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { text-align:left; padding:7px 8px; border-bottom:1px solid var(--line); }
  th { color:var(--muted); font-weight:600; }
  tr:last-child td { border-bottom:none; }
  .muted { color:var(--muted); }
  .section { margin-top:26px; }
  .section h3 { font-size:15px; margin:0 0 8px; }
  .row { display:flex; justify-content:space-between; align-items:center; gap:12px; }
  .foot { color:var(--muted); font-size:12px; margin-top:10px; }
  .empty { color:var(--muted); font-size:13px; padding:8px 0; }
  /* live indicator */
  .live { display:inline-flex; align-items:center; gap:7px; font-size:12px; color:var(--muted); }
  .dot { width:9px; height:9px; border-radius:50%; background:var(--ok);
         box-shadow:0 0 0 0 rgba(26,127,55,.5); animation:pulse 2s infinite; }
  .dot.stale { background:var(--warn); animation:none; }
  .dot.dead { background:var(--bad); animation:none; }
  @keyframes pulse {
    0%   { box-shadow:0 0 0 0 rgba(26,127,55,.5); }
    70%  { box-shadow:0 0 0 8px rgba(26,127,55,0); }
    100% { box-shadow:0 0 0 0 rgba(26,127,55,0); }
  }
  .feed td.state-available { color:var(--ok); font-weight:600; }
  .feed td.state-nostock { color:var(--muted); }
  .feed td.state-unverified { color:var(--warn); }
  button { font:inherit; border:1px solid var(--line); background:var(--card); color:var(--ink);
           border-radius:10px; padding:6px 12px; cursor:pointer; }
  button:active { transform:scale(.97); }
  .tg-btn { display:inline-flex; align-items:center; gap:6px; background:#0088cc; color:#fff; font-weight:600;
            padding:6px 14px; border-radius:10px; text-decoration:none; font-size:13px; margin-top:8px; }
  .tg-btn:hover { background:#0077b5; }
</style>
</head>
<body>
<header>
  <div class="wrap row">
    <div>
      <h1>iPhone 17 256GB · Pickup Monitor</h1>
      <div class="sub">Apple BKC, Apple Borivali &amp; Apple Saket</div>
    </div>
    <div style="text-align:right">
      <div class="live"><span class="dot" id="dot"></span><span id="liveText">connecting…</span></div>
      <div style="margin-top:8px; display:flex; gap:8px; justify-content:flex-end; align-items:center;">
        <a href="https://t.me/Fortune_feedbackbot" target="_blank" class="tg-btn">✈️ Connect Telegram Bot</a>
        <button onclick="testTelegram()">🔔 Test Alert</button>
        <button onclick="tick(true)">Refresh</button>
      </div>
    </div>
  </div>
</header>
<main>
  <div class="card" style="margin-bottom:18px; background:linear-gradient(135deg, rgba(0,136,204,0.08), rgba(0,113,227,0.05)); border-color:rgba(0,136,204,0.3);">
    <div class="row">
      <div>
        <h3 style="margin:0 0 4px; color:#0088cc; font-size:15px;">✈️ Live Telegram Notifications Active</h3>
        <div class="sub">Click <strong>Connect Telegram Bot</strong> to subscribe to instant iPhone 17 stock alerts (@Fortune_feedbackbot).</div>
      </div>
      <div>
        <a href="https://t.me/Fortune_feedbackbot" target="_blank" class="tg-btn">Open @Fortune_feedbackbot</a>
      </div>
    </div>
  </div>

  <div class="grid" id="stores"></div>

  <div class="section">
    <h3>Live check feed</h3>
    <div class="card"><div id="feed"></div></div>
  </div>

  <div class="section">
    <h3>Recent changes (7d)</h3>
    <div class="card"><div id="changes"></div></div>
  </div>

  <div class="section">
    <h3>Reliability (7d)</h3>
    <div class="card"><div id="stats"></div></div>
  </div>

  <div class="foot" id="foot"></div>
</main>

<script>
const POLL = %POLL% * 1000;
const esc = s => String(s ?? "").replace(/[&<>]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));

function statePill(s){
  if(s==='available') return '<span class="pill ok">AVAILABLE</span>';
  if(s==='nostock')   return '<span class="pill bad">NO STOCK</span>';
  return '<span class="pill warn">UNVERIFIED</span>';
}

// SQLite CURRENT_TIMESTAMP is UTC "YYYY-MM-DD HH:MM:SS". Parse as UTC.
function parseUTC(s){ return s ? new Date(s.replace(' ','T') + 'Z') : null; }
function ago(s){
  const d = parseUTC(s); if(!d) return 'never';
  let sec = Math.max(0, (Date.now() - d.getTime())/1000);
  if(sec < 60) return Math.floor(sec) + 's ago';
  if(sec < 3600) return Math.floor(sec/60) + 'm ago';
  if(sec < 86400) return Math.floor(sec/3600) + 'h ago';
  return Math.floor(sec/86400) + 'd ago';
}
// Format a UTC db timestamp as IST wall-clock, e.g. "24 Jul, 03:41:20 PM IST"
function istTime(s){
  const d = parseUTC(s); if(!d) return '—';
  return d.toLocaleString('en-IN', {timeZone:'Asia/Kolkata', day:'2-digit', month:'short',
    hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:true}) + ' IST';
}

async function j(u){ const r = await fetch(u, {cache:'no-store'}); return r.json(); }

function setLive(lastCheckedISO){
  const dot = document.getElementById('dot');
  const txt = document.getElementById('liveText');
  const d = parseUTC(lastCheckedISO);
  if(!d){ dot.className='dot dead'; txt.textContent='no data yet'; return; }
  const mins = (Date.now() - d.getTime())/60000;
  // monitor runs every 3 min; healthy if a check landed within ~7 min.
  if(mins <= 7) dot.className='dot';
  else if(mins <= 20) dot.className='dot stale';
  else dot.className='dot dead';
  txt.textContent = 'last check ' + istTime(lastCheckedISO);
}

async function tick(manual){
  try {
    const [cur, feed, ch, st] = await Promise.all([
      j('api/current'), j('api/history?limit=24'), j('api/changes?days=7'), j('api/stats?days=7')
    ]);

    const byStore = {};
    (cur.colours||[]).forEach(c => { (byStore[c.store_id] ??= []).push(c); });

    document.getElementById('stores').innerHTML = (cur.stores||[]).map(s => {
      const cols = (byStore[s.store_id]||[]).map(c =>
        `<span class="swatch ${c.is_buyable? 'ok':''}">${esc(c.colour)}${c.is_buyable?' ✓':''}</span>`
      ).join('') || '<span class="empty">no verified colour data yet</span>';
      return `<div class="card">
        <div class="row"><h2>${esc(s.store_name)}</h2>${statePill(s.state)}</div>
        <div class="muted" style="font-size:12px;margin-top:6px">${esc(s.detail||'')}</div>
        <div class="colours">${cols}</div>
        <div class="foot">checked ${istTime(s.checked_at)}</div>
      </div>`;
    }).join('') || '<div class="empty">No checks recorded yet. Start the monitor.</div>';

    // freshest check timestamp drives the live dot
    const newest = (cur.stores||[]).map(s => s.checked_at).filter(Boolean).sort().pop();
    setLive(newest);

    document.getElementById('feed').innerHTML = (feed && feed.length) ? `<table class="feed">
      <tr><th>When (IST)</th><th>Store</th><th>Result</th></tr>
      ${feed.map(x => `<tr>
        <td class="muted">${istTime(x.checked_at)}</td>
        <td>${esc(x.store_name)}</td>
        <td class="state-${esc(x.state)}">${esc(x.state)}</td>
      </tr>`).join('')}</table>` : '<div class="empty">No checks yet.</div>';

    document.getElementById('changes').innerHTML = (ch && ch.length) ? `<table>
      <tr><th>When (IST)</th><th>Store</th><th>Colour</th><th>Change</th></tr>
      ${ch.map(x => `<tr>
        <td class="muted">${istTime(x.changed_at)}</td><td>${esc(x.store_name)}</td><td>${esc(x.colour)}</td>
        <td>${x.new_buyable? '<span class="pill ok">became buyable</span>':'<span class="pill bad">went unbuyable</span>'}</td>
      </tr>`).join('')}</table>` : '<div class="empty">No changes in the last 7 days.</div>';

    document.getElementById('stats').innerHTML = (st && st.length) ? `<table>
      <tr><th>Store</th><th>Checks</th><th>Verified</th><th>Available</th><th>Became avail.</th></tr>
      ${st.map(x => `<tr>
        <td>${esc(x.store_name)}</td><td>${x.total_checks}</td>
        <td>${x.verified_rate}%</td><td>${x.available_checks}</td><td>${x.times_became_available}</td>
      </tr>`).join('')}</table>` : '<div class="empty">No stats yet.</div>';

    document.getElementById('foot').textContent =
      'Auto-refreshing every ' + (POLL/1000) + 's · updated ' + istTime(
        new Date().toISOString().slice(0,19).replace('T',' '));
  } catch (e) {
    document.getElementById('dot').className = 'dot dead';
    document.getElementById('liveText').textContent = 'dashboard offline';
    document.getElementById('foot').textContent = 'Error: ' + e;
  }
}

async function testTelegram() {
  try {
    const r = await fetch('/api/test_telegram', {method: 'POST'});
    const data = await r.json();
    if(data.ok) {
      alert('✅ Test alert sent to Telegram bot!');
    } else {
      alert('❌ Failed to send Telegram alert: ' + (data.error || 'Unknown error'));
    }
  } catch(e) {
    alert('❌ Request error: ' + e);
  }
}

tick();
setInterval(tick, POLL);
// keep the "N ago" labels ticking between polls
setInterval(() => {
  const s = document.querySelectorAll('.foot');
}, 1000);
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE.replace("%POLL%", str(POLL_SECONDS)))


if __name__ == "__main__":
    db.init_db(DB_PATH)
    import sys
    debug = "--production" not in sys.argv
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5001")), debug=debug)
