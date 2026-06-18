// ── State ────────────────────────────────────────────────────
let lastPhase     = null;
let lastStateHash = null;
let lastHandStr   = { dealer: null, my: null };
let resultsShown  = false;

// ── Rendering helpers ─────────────────────────────────────────
function makeCard(str, ghost = false) {
  if (str === '?') return `<div class="card-hidden"></div>`;
  const rank  = str.slice(0, -1);
  const suit  = str.slice(-1);
  const isRed = suit === '♥' || suit === '♦';
  const cls   = `card ${isRed ? 'red' : 'black'}${ghost ? ' card-ghost' : ''}`;
  return `<div class="${cls}">
    <span class="rank">${rank}</span>
    <span class="suit">${suit}</span>
    <span class="rank-bottom">${rank}</span>
  </div>`;
}

function renderHand(containerId, cards, ghost = false) {
  const el  = document.getElementById(containerId);
  if (!el) return;
  const key = containerId === 'dealer-hand' ? 'dealer' : 'my';
  if (!ghost) {
    const ser = cards.join(',');
    if (lastHandStr[key] === ser) return;
    lastHandStr[key] = ser;
  }
  el.innerHTML = cards.map(c => makeCard(c, ghost)).join('');
}

function setVisible(id, visible) {
  const el = document.getElementById(id);
  if (!el) return;
  visible ? el.classList.remove('hidden') : el.classList.add('hidden');
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el && el.textContent !== String(text)) el.textContent = text;
}

// ── Timer ──────────────────────────────────────────────────────
function updateTimer(secs) {
  const wrap = document.getElementById('timer-bar-wrap');
  const bar  = document.getElementById('timer-bar');
  const txt  = document.getElementById('timer-text');
  if (secs === null || secs === undefined) { wrap.classList.add('hidden'); return; }
  wrap.classList.remove('hidden');
  bar.style.width      = (secs / 15 * 100) + '%';
  bar.style.background = secs > 8 ? '#2d9e57' : secs > 4 ? '#f0c040' : '#e03030';
  txt.textContent = secs;
}

// ── Bannière joining ───────────────────────────────────────────
function updateJoinBanner(secs, myStatus) {
  let el = document.getElementById('join-timer-banner');
  if (secs === null || secs === undefined) { if (el) el.remove(); return; }
  if (!el) {
    el = document.createElement('div');
    el.id = 'join-timer-banner';
    el.className = 'join-timer-banner';
    document.getElementById('phase-banner').after(el);
  }
  const inGame = myStatus === 'idle';
  el.textContent = inGame
    ? `✅ Tu es inscrit — la partie commence dans ${secs}s`
    : `⏱️ La partie commence dans ${secs}s`;
  el.style.background = secs > 8
    ? 'rgba(45,158,87,0.15)' : secs > 4
    ? 'rgba(240,192,64,0.15)' : 'rgba(224,48,48,0.2)';
}

const PHASE_MSGS = {
  waiting: '⏳ En attente — Lance la partie !',
  joining: '🚪 Nouvelle manche — Rejoins ou attends !',
  betting: '💰 Mise — Combien tu risques ?',
  playing: '🎴 Jeu — Tirer ou rester ?',
  dealer:  '🎰 Le croupier joue...',
  results: '🏆 Résultats !',
};

// ── Poll ───────────────────────────────────────────────────────
async function fetchState() {
  try {
    const res = await fetch('/api/state');
    if (!res.ok) return;
    const s = await res.json();
    if (s.error) return;
    applyState(s);
  } catch(e) {}
}

function applyState(s) {
  setText('balance-display', `💰 ${s.my_balance.toLocaleString('fr-FR')}€`);
  renderHand('dealer-hand', s.dealer_hand);
  setText('dealer-value', s.dealer_value !== '?' ? s.dealer_value : '?');
  renderHand('my-hand', s.my_hand);
  setText('my-value', s.my_value || '');
  setText('phase-banner', PHASE_MSGS[s.phase] || s.phase);
  updateTimer(s.timer_left);
  updateJoinBanner(s.join_timer_left, s.my_status);

  if (s.state_hash !== lastStateHash) {
    renderPlayers(s.players, s.phase, s.is_master);
    lastStateHash = s.state_hash;
  }

  // ── Master : preview next card ──
  if (s.is_master) {
    setVisible('master-panel', true);
    // Mode label
    const modeLabel = s.jyss_mode === 'super' ? '⚡ Force Blackjack actif' : '✅ Mode normal';
    setText('master-mode-label', modeLabel);
    // Preview ma prochaine carte
    if (s.next_card && s.phase === 'playing' && s.my_status === 'playing') {
      setVisible('my-next-wrap', true);
      renderHand('my-next-hand', [s.next_card], true);
    } else {
      setVisible('my-next-wrap', false);
    }
    // Preview prochaine carte croupier
    if (s.dealer_next_card && ['playing', 'betting'].includes(s.phase)) {
      setVisible('dealer-next-wrap', true);
      renderHand('dealer-next-hand', [s.dealer_next_card], true);
    } else {
      setVisible('dealer-next-wrap', false);
    }
  } else {
    setVisible('master-panel', false);
    setVisible('my-next-wrap', false);
    setVisible('dealer-next-wrap', false);
  }

  // ── Zones d'action ──
  setVisible('start-zone',      false);
  setVisible('join-round-zone', false);
  setVisible('new-round-zone',  false);
  setVisible('actions',         false);
  setVisible('bet-actions',     false);
  setVisible('play-actions',    false);

  if (s.phase === 'waiting') {
    setVisible('start-zone', true);
  } else if (s.phase === 'joining') {
    if (s.my_status !== 'idle') setVisible('join-round-zone', true);
  } else if (s.phase === 'betting' && s.my_status === 'betting') {
    setVisible('actions',     true);
    setVisible('bet-actions', true);
  } else if (s.phase === 'playing' && s.my_status === 'playing') {
    setVisible('actions',      true);
    setVisible('play-actions', true);
  } else if (s.phase === 'results') {
    setVisible('new-round-zone', true);
    if (!resultsShown) { resultsShown = true; loadResults(); }
  }

  if (s.phase !== 'results') resultsShown = false;
  lastPhase = s.phase;
}

function renderPlayers(players, phase, isMaster) {
  const zone   = document.getElementById('players-zone');
  const labels = {
    idle: '😴 En attente', betting: '💭 Mise en cours...',
    playing: '🎴 Joue', stand: '✋ Reste',
    bust: '💥 Bust !', blackjack: '🌟 BLACKJACK !',
    done: '✓ Terminé', spectator: '👁️ Spectateur',
  };
  // En mode master on voit toutes les mains, sinon seulement en results
  const showHands = isMaster || phase === 'results';
  zone.innerHTML = Object.entries(players).map(([name, p]) => {
    const handHtml = showHands
      ? p.hand.map(c => makeCard(c)).join('')
      : `<small>${p.hand_size} carte(s)</small>`;
    const valStr = (isMaster && p.value !== '?') ? ` · <strong>${p.value}</strong>` : '';
    return `<div class="player-card">
      <div class="pname">${name}</div>
      <div class="hand" style="min-height:40px">${handHtml}</div>
      <div class="pbet">Mise : ${p.bet.toLocaleString('fr-FR')}€${valStr}</div>
      <div class="pstatus">${labels[p.status] || p.status}</div>
    </div>`;
  }).join('');
}

// ── Results ────────────────────────────────────────────────────
async function loadResults() {
  const res  = await fetch('/api/results');
  const data = await res.json();
  if (!Object.keys(data).length) return;
  const content = document.getElementById('results-content');
  const labels = {
    win:       ['🟢 Gagné',       'result-win'],
    lose:      ['🔴 Perdu',       'result-lose'],
    push:      ['⚪ Egalité',     'result-push'],
    blackjack: ['🌟 BLACKJACK !', 'result-bj'],
    bust:      ['💥 Bust',        'result-bust'],
  };
  content.innerHTML = Object.entries(data).map(([name, r]) => {
    const [label, cls] = labels[r.result] || [r.result, ''];
    const sign = r.delta > 0 ? '+' : '';
    return `<div class="result-row">
      <span>${name} — ${r.hand} (${r.value})</span>
      <span class="${cls}">${label} ${sign}${r.delta.toLocaleString('fr-FR')}€</span>
    </div>`;
  }).join('');
  document.getElementById('results-overlay').classList.remove('hidden');
  loadLeaderboard();
}

function closeResults() {
  document.getElementById('results-overlay').classList.add('hidden');
}

// ── Actions jeu ────────────────────────────────────────────────
async function joinAndStart() {
  await fetch('/api/join',  { method: 'POST' });
  await fetch('/api/start', { method: 'POST' });
  fetchState();
}

async function joinRound() {
  await fetch('/api/join_round', { method: 'POST' });
  fetchState();
}

async function placeBet(amount) {
  await fetch('/api/bet', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount }),
  });
  fetchState();
}

async function placeCustomBet() {
  const amount = parseInt(document.getElementById('custom-amount').value.trim());
  if (!amount || amount < 1) return;
  await placeBet(amount);
}

async function hit() {
  await fetch('/api/hit', { method: 'POST' });
  fetchState();
}

async function stand() {
  await fetch('/api/stand', { method: 'POST' });
  fetchState();
}

async function newRound() {
  closeResults();
  await fetch('/api/new_round', { method: 'POST' });
  fetchState();
}

async function leaveTable() {
  await fetch('/api/leave', { method: 'POST' });
  window.location.href = '/logout';
}

// ── Actions master ─────────────────────────────────────────────
async function masterForceBlackjack() {
  await fetch('/api/master/force_blackjack', { method: 'POST' });
  fetchState();
}

async function masterNormal() {
  await fetch('/api/master/normal', { method: 'POST' });
  fetchState();
}

async function masterReset() {
  if (!confirm('⚠️ Reset TOTAL : table + wallets. Confirmer ?')) return;
  await fetch('/api/master/reset', { method: 'POST' });
  fetchState();
}

// ── Leaderboard ────────────────────────────────────────────────
async function loadLeaderboard() {
  const res  = await fetch('/api/leaderboard');
  const data = await res.json();
  document.getElementById('leaderboard-list').innerHTML =
    data.slice(0, 8).map(([name, amount], i) =>
      `<div class="lb-row">
        <span class="lb-name">${i + 1}. ${name}</span>
        <span class="lb-amount">${amount.toLocaleString('fr-FR')}€</span>
      </div>`
    ).join('');
}

// ── Init ───────────────────────────────────────────────────────
async function init() {
  await fetch('/api/join', { method: 'POST' });
  fetchState();
  loadLeaderboard();
  setInterval(fetchState,      1000);
  setInterval(loadLeaderboard, 5000);
}

init();
