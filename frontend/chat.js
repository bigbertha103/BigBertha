// État interne
let currentConvId = null;
let conversations = [];
const activeJobPollers = new Map();
let currentUserMsgCount = 0;
const HANDOFF_WARNING_THRESHOLD = 14; // Avertir à 14 messages (seuil handoff = 15)

// ── Éléments DOM ──────────────────────────────────────────────────
const convList      = document.getElementById('conv-list');
const msgContainer  = document.getElementById('messages');
const msgInput      = document.getElementById('msg-input');
const btnSend       = document.getElementById('btn-send');
const convTitleEl   = document.getElementById('conv-title');
const convTitleBar  = document.getElementById('conv-title-bar');
const pinnedList    = document.getElementById('pinned-list');
const btnAddPin     = document.getElementById('btn-add-pin');
const pinForm       = document.getElementById('pin-form');
const pinTextarea   = document.getElementById('pin-textarea');
const btnPinSubmit  = document.getElementById('btn-pin-submit');
const btnPinCancel  = document.getElementById('btn-pin-cancel');
const btnNewConv       = document.getElementById('btn-new-conv');
const btnArchiveConv   = document.getElementById('btn-archive-conv');
const testModeBanner   = document.getElementById('test-mode-banner');

// ── Initialisation ────────────────────────────────────────────────
async function init() {
  convList.innerHTML = '<div class="sidebar-state">Chargement...</div>';
  try {
    const [convsResult, sessionResult] = await Promise.allSettled([
      getConversations(),
      getActiveTestSession(),
    ]);

    conversations = convsResult.status === 'fulfilled' ? convsResult.value : [];
    renderConvList();
    if (conversations.length > 0) {
      await loadConversation(conversations[0].id);
    } else {
      showEmptyState();
    }

    if (sessionResult.status === 'fulfilled' && sessionResult.value) {
      showTestModeBanner(sessionResult.value.name);
    }
  } catch (e) {
    convList.innerHTML = `
      <div class="sidebar-state">
        Impossible de charger les conversations.
        <button class="btn-retry" id="btn-retry-load">Réessayer</button>
      </div>`;
    document.getElementById('btn-retry-load').addEventListener('click', init);
  }
}

function showTestModeBanner(name) {
  testModeBanner.style.display = 'flex';
  testModeBanner.innerHTML =
    `⚠️ Mode test actif — <strong>${escapeHtml(name)}</strong>&nbsp;&nbsp;<a href="settings.html" class="test-banner-link">Gérer</a>`;
}

// ── Sidebar : liste des conversations (sessions) ─────────────────
function renderConvList() {
  if (conversations.length === 0) {
    convList.innerHTML = '<div class="sidebar-state">Aucune conversation. Cliquez sur Nouvelle conversation pour commencer.</div>';
    return;
  }

  const byId = {};
  const successorOf = new Set();
  for (const conv of conversations) {
    byId[conv.id] = conv;
    if (conv.previous_conversation_id != null) {
      successorOf.add(conv.previous_conversation_id);
    }
  }

  const heads = conversations
    .filter(c => !successorOf.has(c.id))
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

  convList.innerHTML = '';
  for (const head of heads) {
    const ancestors = [];
    let cur = head;
    while (cur.previous_conversation_id != null && byId[cur.previous_conversation_id]) {
      cur = byId[cur.previous_conversation_id];
      ancestors.push(cur);
    }
    convList.appendChild(buildSessionItem(head, ancestors));
  }
}

function buildConvItem() {
  renderConvList();
  return null;
}

function buildSessionItem(head, ancestors) {
  const wrapper = document.createElement('div');
  wrapper.className = 'session-wrapper';
  wrapper.dataset.headId = head.id;

  const headEl = document.createElement('div');
  headEl.className = 'conv-item' + (head.id === currentConvId ? ' active' : '');
  headEl.dataset.id = head.id;

  const titleText = head.title || 'Sans titre';
  const titleClass = head.title ? 'conv-item-title' : 'conv-item-title no-title';
  const hasAncestors = ancestors.length > 0;

  headEl.innerHTML = `
    <div class="conv-item-body">
      ${hasAncestors ? '<button class="btn-session-toggle" title="Voir l\'historique de session">▶</button>' : ''}
      <div class="${titleClass}">${escapeHtmlSafe(titleText)}</div>
      <div class="conv-item-date">${formatDate(head.updated_at)}</div>
    </div>
    <button class="btn-delete-conv" title="Supprimer">🗑</button>`;

  headEl.querySelector('.conv-item-body').addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-session-toggle')) {
      toggleSessionHistory(wrapper);
      return;
    }
    loadConversation(head.id);
  });
  headEl.querySelector('.btn-delete-conv').addEventListener('click', (e) => {
    e.stopPropagation();
    confirmDeleteConversation(head.id);
  });

  wrapper.appendChild(headEl);

  if (hasAncestors) {
    const historyEl = document.createElement('div');
    historyEl.className = 'session-history';
    const isAncestorActive = ancestors.some(a => a.id === currentConvId);
    if (!isAncestorActive) {
      historyEl.style.display = 'none';
    } else {
      const toggle = headEl.querySelector('.btn-session-toggle');
      if (toggle) toggle.textContent = '▼';
    }

    for (const anc of ancestors) {
      const ancEl = document.createElement('div');
      ancEl.className = 'conv-item conv-item-ancestor' + (anc.id === currentConvId ? ' active' : '');
      ancEl.dataset.id = anc.id;
      const ancTitle = anc.title || 'Sans titre';
      ancEl.innerHTML = `
        <div class="conv-item-body">
          <div class="conv-item-title archived-label">${escapeHtmlSafe(ancTitle)}</div>
          <div class="conv-item-date">${formatDate(anc.updated_at)}</div>
        </div>`;
      ancEl.addEventListener('click', () => loadConversation(anc.id));
      historyEl.appendChild(ancEl);
    }
    wrapper.appendChild(historyEl);
  }

  return wrapper;
}

function toggleSessionHistory(wrapper) {
  const history = wrapper.querySelector('.session-history');
  const toggle = wrapper.querySelector('.btn-session-toggle');
  if (!history) return;
  const isHidden = history.style.display === 'none';
  history.style.display = isHidden ? 'block' : 'none';
  if (toggle) toggle.textContent = isHidden ? '▼' : '▶';
}

function updateSidebarItem() {
  renderConvList();
  setActiveConvInSidebar(currentConvId);
}

function setActiveConvInSidebar(id) {
  convList.querySelectorAll('.conv-item').forEach(el => {
    el.classList.toggle('active', Number(el.dataset.id) === id);
  });
}

function escapeHtmlSafe(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

async function fetchSessionSummary(convId) {
  try {
    const resp = await fetch(`/api/conversations/${convId}/session-summary`);
    if (!resp.ok) return null;
    return await resp.json();
  } catch (e) {
    return null;
  }
}

// ── Charger une conversation ──────────────────────────────────────
async function loadConversation(id) {
  currentConvId = id;
  setActiveConvInSidebar(id);

  // Titre
  const conv = conversations.find(c => c.id === id);
  renderTitle(conv ? conv.title : null);

  // Masquer le bouton Archiver si la conversation est déjà archivée
  if (conv && conv.status === 'archived') {
    btnArchiveConv.style.display = 'none';
  } else {
    btnArchiveConv.style.display = '';
  }

  // Messages
  msgContainer.innerHTML = '';

  // Bilan ARCHIVISTE pour les conversations archivées
  if (conv && conv.status === 'archived') {
    const summary = await fetchSessionSummary(id);
    if (summary) {
      appendSessionSummaryCard(summary);
    }
  }

  try {
    const messages = await getMessages(id);
    if (messages.length === 0) {
      showConvEmptyState();
    } else {
      for (const msg of messages) {
        appendMessage(msg.role, msg.content);
      }
      currentUserMsgCount = messages.filter(m => m.role === 'user').length;
      checkHandoffWarning();
      scrollToBottom();
    }
  } catch (e) {
    // Silencieux — la conversation existe
  }

  // Pinned
  renderPinnedList([]);
  try {
    const pinned = await getPinned(id);
    renderPinnedList(pinned);
  } catch (e) { /* silencieux */ }

  // Réactiver champ si pas de job en cours sur cette conv
  const poller = activeJobPollers.get(id);
  if (poller) {
    disableInput();
    showProgressIndicator('En cours...');
  } else {
    enableInput();
  }
}

// ── Titre éditab ──────────────────────────────────────────────────
function renderTitle(title) {
  convTitleEl.textContent = title || 'Sans titre';
  convTitleEl.style.display = 'inline-block';
}

convTitleEl.addEventListener('click', startTitleEdit);

function startTitleEdit() {
  const conv = conversations.find(c => c.id === currentConvId);
  if (!conv) return;

  const input = document.createElement('input');
  input.id = 'conv-title-input';
  input.type = 'text';
  input.value = conv.title || '';
  input.placeholder = 'Sans titre';

  convTitleEl.style.display = 'none';
  convTitleBar.appendChild(input);
  input.focus();
  input.select();

  async function commitEdit() {
    const newTitle = input.value.trim() || null;
    input.remove();
    convTitleEl.style.display = 'inline-block';
    if (newTitle === conv.title) return;
    try {
      const updated = await patchConversation(currentConvId, newTitle);
      conv.title = updated.title;
      conv.updated_at = updated.updated_at;
      renderTitle(updated.title);
      updateSidebarItem(conv);
    } catch (e) { /* silencieux */ }
  }

  input.addEventListener('blur', commitEdit);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
    if (e.key === 'Escape') { input.value = conv.title || ''; input.blur(); }
  });
}

// ── Messages ──────────────────────────────────────────────────────
function appendSessionSummaryCard(summary) {
  const card = document.createElement('div');
  card.className = 'session-summary-card';

  let html = '<div class="session-summary-header">📋 Bilan de cette session archivée</div>';

  if (summary.summary_json) {
    let data;
    try { data = JSON.parse(summary.summary_json); } catch(e) { data = null; }
    if (data) {
      if (data.sujet_principal) {
        html += `<div class="session-summary-subject">${escapeHtmlSafe(data.sujet_principal)}</div>`;
      }
      if (data.decisions_prises && data.decisions_prises.length > 0) {
        html += '<div class="session-summary-section"><strong>Décisions</strong><ul>';
        data.decisions_prises.forEach(d => {
          html += `<li>${escapeHtmlSafe(d)}</li>`;
        });
        html += '</ul></div>';
      }
      if (data.prochaine_etape) {
        html += `<div class="session-summary-section"><strong>Prochaine étape</strong><p>${escapeHtmlSafe(data.prochaine_etape)}</p></div>`;
      }
    }
  } else if (summary.summary_text) {
    html += `<div class="session-summary-section">${escapeHtmlSafe(summary.summary_text)}</div>`;
  }

  card.innerHTML = html;
  msgContainer.appendChild(card);
}

function appendMessage(role, content) {
  const row = document.createElement('div');
  row.className = `msg-row ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  if (role === 'boss') {
    bubble.innerHTML = renderMarkdown(content);
  } else {
    bubble.textContent = content;
  }
  row.appendChild(bubble);
  msgContainer.appendChild(row);
}

function showConvEmptyState() {
  const div = document.createElement('div');
  div.className = 'msg-empty';
  div.textContent = 'Posez votre première question à Big Bertha.';
  msgContainer.appendChild(div);
}

function showEmptyState() {
  msgContainer.innerHTML = '';
  const warn = document.getElementById('handoff-warning');
  if (warn) warn.remove();
  currentUserMsgCount = 0;
  convTitleEl.textContent = '';
  renderPinnedList([]);
  disableInput();
  btnArchiveConv.style.display = 'none';
}

function scrollToBottom() {
  msgContainer.scrollTop = msgContainer.scrollHeight;
}

// ── Indicateur de progression ─────────────────────────────────────
let progressEl = null;

function showProgressIndicator(text) {
  removeProgressIndicator();
  const row = document.createElement('div');
  row.className = 'msg-progress';
  row.id = 'progress-indicator';
  const bubble = document.createElement('div');
  bubble.className = 'msg-progress-bubble';
  bubble.textContent = text;
  row.appendChild(bubble);
  msgContainer.appendChild(row);
  progressEl = row;
  scrollToBottom();
}

function updateProgressIndicator(text) {
  const el = document.getElementById('progress-indicator');
  if (el) el.querySelector('.msg-progress-bubble').textContent = text;
}

function removeProgressIndicator() {
  const el = document.getElementById('progress-indicator');
  if (el) el.remove();
  progressEl = null;
}

function showErrorIndicator(message) {
  removeProgressIndicator();
  const row = document.createElement('div');
  row.className = 'msg-error';
  const bubble = document.createElement('div');
  bubble.className = 'msg-error-bubble';
  bubble.textContent = message;
  row.appendChild(bubble);
  msgContainer.appendChild(row);
  scrollToBottom();
}

function checkHandoffWarning() {
  const existing = document.getElementById('handoff-warning');
  if (existing) existing.remove();

  if (currentUserMsgCount >= HANDOFF_WARNING_THRESHOLD) {
    const banner = document.createElement('div');
    banner.id = 'handoff-warning';
    banner.className = 'handoff-warning-banner';
    banner.textContent =
      '⚠️ Cette conversation approche de sa limite. Le prochain échange déclenchera l\'archivage automatique et ouvrira une nouvelle session.';
    const inputZone = document.getElementById('input-zone');
    inputZone.parentNode.insertBefore(banner, inputZone);
  }
}

// ── Envoi de message ──────────────────────────────────────────────
async function sendMessage() {
  const content = msgInput.value.trim();
  if (!content || !currentConvId) return;

  // Retirer état vide
  const empty = msgContainer.querySelector('.msg-empty');
  if (empty) empty.remove();

  disableInput();
  msgInput.value = '';
  appendMessage('user', content);
  currentUserMsgCount++;
  scrollToBottom();

  try {
    const result = await postMessage(currentConvId, content);
    const jobId = result.job_id;

    // Handoff : conversation archivée → nouvelle créée automatiquement
    if (result.new_conversation_id) {
      const warn = document.getElementById('handoff-warning');
      if (warn) warn.remove();
      currentUserMsgCount = 0;
      const newId = result.new_conversation_id;
      conversations.unshift({
        id: newId,
        title: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      currentConvId = newId;
      renderConvList();
      setActiveConvInSidebar(newId);
    }

    showProgressIndicator('Le Boss analyse votre demande...');
    startJobPoller(currentConvId, jobId);
  } catch (e) {
    showErrorIndicator('Une erreur est survenue lors de l\'envoi. Merci de réessayer.');
    enableInput();
  }
}

// ── Poller de job ─────────────────────────────────────────────────
function startJobPoller(convId, jobId) {
  if (activeJobPollers.has(convId)) {
    clearInterval(activeJobPollers.get(convId).intervalId);
  }

  const intervalId = setInterval(async () => {
    try {
      const job = await getJobStatus(jobId);
      const isCurrentConv = convId === currentConvId;

      if (job.status === 'PENDING' || job.status === 'ROUTING') {
        if (isCurrentConv) updateProgressIndicator('Le Boss analyse votre demande...');
      } else if (job.status === 'AGENT_RUNNING') {
        const label = getAgentLabel(job.agent_code);
        if (isCurrentConv) updateProgressIndicator(`${label} au travail...`);
      } else if (job.status === 'SYNTHESIZING') {
        if (isCurrentConv) updateProgressIndicator('Synthèse en cours...');
      } else if (job.status === 'DONE') {
        clearInterval(intervalId);
        activeJobPollers.delete(convId);

        if (isCurrentConv) {
          removeProgressIndicator();
          if (job.final_response) appendMessage('boss', job.final_response);
          scrollToBottom();
          enableInput();
          checkHandoffWarning();
          // Rafraîchir pinned
          try {
            const pinned = await getPinned(convId);
            renderPinnedList(pinned);
          } catch (e) { /* silencieux */ }
        }
        // Mettre à jour le titre dans la sidebar
        try {
          conversations = await getConversations();
          renderConvList();
          setActiveConvInSidebar(currentConvId);
          const conv = conversations.find(c => c.id === convId);
          if (conv && convId === currentConvId) renderTitle(conv.title);
        } catch (e) { /* silencieux */ }

      } else if (job.status === 'ERROR') {
        clearInterval(intervalId);
        activeJobPollers.delete(convId);

        if (isCurrentConv) {
          const msg = job.error_message
            ? `Une erreur est survenue : ${job.error_message}`
            : 'Une erreur est survenue lors du traitement de votre demande. Merci de réessayer.';
          showErrorIndicator(msg);
          enableInput();
        }
      }
    } catch (e) {
      // Erreur réseau transitoire — on continue à poller
    }
  }, 1000);

  activeJobPollers.set(convId, { intervalId, jobId });
}

// ── Input enable/disable ──────────────────────────────────────────
function enableInput() {
  msgInput.disabled = false;
  btnSend.disabled = !msgInput.value.trim();
  msgInput.focus();
}

function disableInput() {
  msgInput.disabled = true;
  btnSend.disabled = true;
}

// ── Nouvelle conversation ─────────────────────────────────────────
async function newConversation() {
  try {
    const conv = await createConversation();
    conversations.unshift(conv);
    renderConvList();
    await loadConversation(conv.id);
    enableInput();
  } catch (e) {
    // silencieux
  }
}

// ── Suppression conversation ──────────────────────────────────────
async function confirmDeleteConversation(id) {
  if (!window.confirm('Supprimer cette conversation ? Cette action est irréversible.')) return;
  try {
    await deleteConversation(id);
    // Arrêter le poller si actif
    if (activeJobPollers.has(id)) {
      clearInterval(activeJobPollers.get(id).intervalId);
      activeJobPollers.delete(id);
    }
    conversations = conversations.filter(c => c.id !== id);
    renderConvList();
    if (currentConvId === id) {
      currentConvId = null;
      if (conversations.length > 0) {
        await loadConversation(conversations[0].id);
      } else {
        showEmptyState();
        convList.innerHTML = '<div class="sidebar-state">Aucune conversation pour l\'instant. Cliquez sur Nouvelle conversation pour commencer.</div>';
      }
    }
  } catch (e) { /* silencieux */ }
}

// ── Pinned ────────────────────────────────────────────────────────
function renderPinnedList(items) {
  pinnedList.innerHTML = '';
  if (!items || items.length === 0) {
    pinnedList.innerHTML = '<div class="pinned-empty">Aucun élément épinglé pour l\'instant.</div>';
    return;
  }
  for (const item of items) {
    pinnedList.appendChild(buildPinnedItem(item));
  }
}

function buildPinnedItem(item) {
  const div = document.createElement('div');
  div.className = 'pinned-item';
  div.dataset.id = item.id;

  const sourceIcon = item.source === 'boss' ? '🤖' : '👤';
  div.innerHTML = `
    <span class="pinned-source" title="${item.source}">${sourceIcon}</span>
    <span class="pinned-content">${escapeHtmlSafe(item.content)}</span>
    <button class="btn-unpin" title="Désépingler">✕</button>`;

  div.querySelector('.btn-unpin').addEventListener('click', () => unpinItem(item, div));
  return div;
}

async function unpinItem(item, el) {
  // Suppression optimiste
  el.remove();
  if (pinnedList.children.length === 0) {
    pinnedList.innerHTML = '<div class="pinned-empty">Aucun élément épinglé pour l\'instant.</div>';
  }
  try {
    await deletePinned(item.id);
  } catch (e) {
    // Réafficher l'item
    const empty = pinnedList.querySelector('.pinned-empty');
    if (empty) empty.remove();
    pinnedList.appendChild(buildPinnedItem(item));
    // Afficher erreur
    const errDiv = document.createElement('div');
    errDiv.className = 'pinned-error';
    errDiv.textContent = 'Échec de la suppression, réessayez.';
    pinnedList.appendChild(errDiv);
    setTimeout(() => errDiv.remove(), 3000);
  }
}

// ── Formulaire d'épinglage ────────────────────────────────────────
btnAddPin.addEventListener('click', () => {
  btnAddPin.style.display = 'none';
  pinForm.classList.add('visible');
  pinTextarea.value = '';
  btnPinSubmit.disabled = true;
  pinTextarea.focus();
});

btnPinCancel.addEventListener('click', closePinForm);

pinTextarea.addEventListener('input', () => {
  btnPinSubmit.disabled = !pinTextarea.value.trim();
});

btnPinSubmit.addEventListener('click', async () => {
  const content = pinTextarea.value.trim();
  if (!content || !currentConvId) return;
  btnPinSubmit.disabled = true;
  try {
    const newPin = await createPinned(currentConvId, content);
    closePinForm();
    const empty = pinnedList.querySelector('.pinned-empty');
    if (empty) empty.remove();
    pinnedList.appendChild(buildPinnedItem(newPin));
  } catch (e) {
    btnPinSubmit.disabled = false;
  }
});

function closePinForm() {
  pinForm.classList.remove('visible');
  btnAddPin.style.display = '';
  pinTextarea.value = '';
}

// ── Envoi clavier ─────────────────────────────────────────────────
msgInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!btnSend.disabled) sendMessage();
  }
});

msgInput.addEventListener('input', () => {
  btnSend.disabled = !msgInput.value.trim() || msgInput.disabled;
});

btnSend.addEventListener('click', sendMessage);
btnNewConv.addEventListener('click', newConversation);

// ── Archivage manuel ──────────────────────────────────────────────
async function archiveCurrentConversation() {
  if (!currentConvId) return;
  if (!window.confirm('Archiver cette conversation ? Elle ne pourra plus recevoir de nouveaux messages directement.')) return;
  try {
    btnArchiveConv.disabled = true;
    await fetch(`/api/conversations/${currentConvId}/archive`, { method: 'POST' });
    // Mettre à jour l'état local
    const conv = conversations.find(c => c.id === currentConvId);
    if (conv) conv.status = 'archived';
    btnArchiveConv.style.display = 'none';
    disableInput();
    // Raffraîchir la liste
    conversations = await getConversations();
    renderConvList();
    setActiveConvInSidebar(currentConvId);
  } catch (e) {
    alert('Erreur lors de l\'archivage. Réessayez.');
  } finally {
    btnArchiveConv.disabled = false;
  }
}

btnArchiveConv.addEventListener('click', archiveCurrentConversation);

// ── Démarrage ─────────────────────────────────────────────────────
init();
