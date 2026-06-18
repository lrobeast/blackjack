// ── Jyss Panel JS ─────────────────────────────────────────────

let currentMode = 'normal';

function makeCard(str) {
  const rank = str.slice(0, -1);
  const suit = str.slice(-1);
  const isRed = suit === '♥' || suit === '♦';
  return `
    <div class="card ${isRed ? 'red' : 'black'}">
      <span class="rank">${rank}</span>
      <span class="suit">${suit}</span>
      <span class="rank-bottom">${rank}</span>
    </div>`;
}

async function fetchJyssState() {
  try {
    const res = await fetch('/api/jyss/state');
    if (!res.ok) return;
    const s = await res.json();
    renderJyssState(s);
  } catch(e) {}
}

function renderJyssState(s) {
  // Dealer hand
  document.getElementById('jyss-dealer-hand').innerHTML =
    s.dealer_hand.length ? s.dealer_hand.map(makeCard).join('') : '<em style="color:#666">Pas encore distribuée</em>';
  document.getElementById('jyss-dealer-value').textContent =
    s.dealer_hand.length ? `Valeur : ${s.dealer_value}` : '';

  // Advice
  const advEl = document.getElementById('jyss-advice');
  if (s.dealer_hand.length) {
    advEl.textContent = `💡 Le croupier devrait : ${s.dealer_advice}`;
    advEl.style.background = s.dealer_advice_color + '22';
    advEl.style.color = s.dealer_advice_color;
    advEl.style.border = `1px solid ${s.dealer_advice_color}55`;
  } else {
    advEl.textContent = '';
  }

  // Players
  const statusLabels = {
    idle: '😴 En attente', betting: '💭 Mise en cours',
    playing: '🎴 Joue', stand: '✋ Reste',
    bust: '💥 Bust', blackjack: '🌟 Blackjack', done: '✓ Terminé',
  };
  document.getElementById('jyss-players').innerHTML =
    Object.entries(s.players).map(([name, p]) => `
      <div class="jyss-player">
        <div class="jp-name">${name}</div>
        <div class="hand">${p.hand.length ? p.hand.map(makeCard).join('') : '<em style="color:#666">Pas de cartes</em>'}</div>
        <div class="jp-info">
          Valeur : ${p.value} | Mise : ${p.bet.toLocaleString('fr-FR')}€ |
          Solde : ${p.balance.toLocaleString('fr-FR')}€ |
          Statut : ${statusLabels[p.status] || p.status}
        </div>
      </div>`).join('') || '<em style="color:#666">Aucun joueur à table</em>';

  // Mode status
  const modeNames = { normal: '✅ Mode normal', jyss: '👁️ JyssMode actif — tu vois la main du croupier', super: '⚡ SuperJyssMode — prochain deal = Blackjack garanti' };
  document.getElementById('mode-status').textContent = modeNames[s.jyss_mode || 'normal'] || '';

  // Logs
  document.getElementById('jyss-logs').innerHTML =
    s.logs.length
      ? [...s.logs].reverse().map(l => `<div class="log-entry">${new Date(l.time * 1000).toLocaleTimeString('fr-FR')} — ${l.msg}</div>`).join('')
      : '<em>Aucun log pour l\'instant</em>';
}

async function activateMode(mode) {
  currentMode = mode;
  await fetch('/api/jyss/activate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  });
  fetchJyssState();
}

async function clearLogs() {
  await fetch('/api/jyss/clear', { method: 'POST' });
  document.getElementById('jyss-logs').innerHTML = '<em>✓ Traces effacées</em>';
  document.getElementById('mode-status').textContent = '';
}

// Poll toutes les secondes
fetchJyssState();
setInterval(fetchJyssState, 1000);

async function resetAll() {
  if (!confirm('⚠️ Reset TOTAL : table + wallets de tous les joueurs. Confirmer ?')) return;
  const res  = await fetch('/api/jyss/reset', { method: 'POST' });
  const data = await res.json();
  document.getElementById('mode-status').textContent = data.message || '✓ Reset effectué';
  fetchJyssState();
}
