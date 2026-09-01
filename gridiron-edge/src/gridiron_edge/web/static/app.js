async function syncOdds() {
  const btn = document.getElementById('sync-btn');
  const msg = document.getElementById('status-msg');
  btn.disabled = true;
  msg.textContent = 'Syncing odds from OddsPapi...';

  try {
    const res = await fetch('/api/sync', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      msg.textContent = `Found ${data.pick_count} +EV picks. Reloading...`;
      setTimeout(() => window.location.reload(), 1000);
    } else {
      msg.textContent = `Error: ${data.error}`;
    }
  } catch (err) {
    msg.textContent = `Request failed: ${err.message}`;
  } finally {
    btn.disabled = false;
  }
}

async function runDemoBacktest() {
  const btn = document.getElementById('backtest-btn');
  const section = document.getElementById('backtest-results');
  const output = document.getElementById('backtest-output');
  const msg = document.getElementById('status-msg');

  btn.disabled = true;
  msg.textContent = 'Running demo backtest...';

  try {
    const res = await fetch('/api/backtest/demo');
    const data = await res.json();
    section.classList.remove('hidden');
    output.textContent = JSON.stringify(data, null, 2);
    msg.textContent = `Backtest: ${data.win_rate}% win rate, $${data.profit_usd} profit on ${data.total_bets} bets`;
  } catch (err) {
    msg.textContent = `Backtest failed: ${err.message}`;
  } finally {
    btn.disabled = false;
  }
}
