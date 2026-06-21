// ── Références DOM ────────────────────────────────────────────────
const profileNotice   = document.getElementById('profile-notice');
const profileName     = document.getElementById('profile-name');
const profileSector   = document.getElementById('profile-sector');
const profileTone     = document.getElementById('profile-tone');
const profileRules    = document.getElementById('profile-rules');
const profileNameErr  = document.getElementById('profile-name-error');
const btnSaveProfile  = document.getElementById('btn-save-profile');
const profileSuccess  = document.getElementById('profile-success');

const configHost      = document.getElementById('config-host');
const configPort      = document.getElementById('config-port');
const configKey       = document.getElementById('config-key');
const btnToggleKey    = document.getElementById('btn-toggle-key');
const btnSaveConfig   = document.getElementById('btn-save-config');
const configSuccess   = document.getElementById('config-success');

const configPerfMode       = document.getElementById('config-perf-mode');
const configPerfLabel      = document.getElementById('config-perf-label');
const configRoutingModel   = document.getElementById('config-routing-model');
const configAgentModel     = document.getElementById('config-agent-model');
const configSynthesisModel = document.getElementById('config-synthesis-model');
const configSentinelModel  = document.getElementById('config-sentinel-model');
const configArchivisteModel= document.getElementById('config-archiviste-model');

const agentsGrid      = document.getElementById('agents-grid');
const logsContent     = document.getElementById('logs-content');
const btnRefreshLogs  = document.getElementById('btn-refresh-logs');

const kbBadge         = document.getElementById('kb-badge');
const kbFileInput     = document.getElementById('kb-file-input');
const btnKbImport     = document.getElementById('btn-kb-import');
const kbImportStatus  = document.getElementById('kb-import-status');
const kbImportResults = document.getElementById('kb-import-results');
const kbTableBody     = document.getElementById('kb-table-body');

const btnSentinel         = document.getElementById('btn-sentinel');
const sentinelSpinner     = document.getElementById('sentinel-spinner');
const sentinelError       = document.getElementById('sentinel-error');
const sentinelReport      = document.getElementById('sentinel-report');
const sentinelScore       = document.getElementById('sentinel-score');
const sentinelBaselineBadge = document.getElementById('sentinel-baseline-badge');
const sentinelObservations  = document.getElementById('sentinel-observations');
const sentinelMetricsBody   = document.getElementById('sentinel-metrics-body');
const sentinelDeltaWrap     = document.getElementById('sentinel-delta-wrap');
const sentinelDeltaContent  = document.getElementById('sentinel-delta-content');
const sentinelProposalsCount = document.getElementById('sentinel-proposals-count');
const sentinelHistory       = document.getElementById('sentinel-history');

const proposalsBadge       = document.getElementById('proposals-badge');
const proposalsPendingList = document.getElementById('proposals-pending-list');
const proposalsHistoryList = document.getElementById('proposals-history-list');

const tsNameInput      = document.getElementById('ts-name-input');
const btnCreateSession = document.getElementById('btn-create-session');
const tsCreateError    = document.getElementById('ts-create-error');
const testSessionsList = document.getElementById('test-sessions-list');

// Tracker des valeurs initiales de config pour détecter les modifications
let configInitial = {};

// ── Initialisation ────────────────────────────────────────────────
async function init() {
  await Promise.allSettled([
    loadProfile(),
    loadConfig(),
    loadAgents(),
    loadLogs(),
    loadKnowledgeStats(),
    loadKnowledgeDocuments(),
    loadSentinelReports(),
    loadProposals(),
    loadProposalHistory(),
    loadTestSessions(),
  ]);
}

// ── Section 1 : Profil entreprise ────────────────────────────────
async function loadProfile() {
  try {
    const profile = await getCompanyProfile();
    profileName.value   = profile.name || '';
    profileSector.value = profile.sector || '';
    profileTone.value   = profile.tone || '';
    profileRules.value  = profile.business_rules || '';
    profileNotice.textContent = '';
  } catch (e) {
    if (e.message && e.message.includes('404')) {
      profileNotice.textContent = 'Aucun profil configuré, complétez les champs ci-dessous.';
    }
  }
}

btnSaveProfile.addEventListener('click', async () => {
  profileNameErr.textContent = '';
  profileName.classList.remove('error');

  const name = profileName.value.trim();
  if (!name) {
    profileName.classList.add('error');
    profileNameErr.textContent = 'Le nom est obligatoire.';
    profileName.focus();
    return;
  }

  btnSaveProfile.disabled = true;
  try {
    await putCompanyProfile({
      name,
      sector:         profileSector.value.trim() || null,
      tone:           profileTone.value.trim() || null,
      business_rules: profileRules.value.trim() || null,
    });
    profileNotice.textContent = '';
    showSuccess(profileSuccess, 'Profil enregistré.');
  } catch (e) {
    profileNameErr.textContent = 'Erreur lors de l\'enregistrement.';
  } finally {
    btnSaveProfile.disabled = false;
  }
});

// ── Section 2 : Configuration modèle ─────────────────────────────
async function loadConfig() {
  try {
    const config = await getConfig();
    const perf = config.perf_mode === '1';
    configPerfMode.checked = perf;
    configPerfLabel.textContent = perf
      ? 'PERFORMANCE — Claude (Haiku / Sonnet)'
      : 'COST — modèles open source';
    const suffix = perf ? 'perf' : 'cost';
    configRoutingModel.value    = config[`routing_model_${suffix}`]    || '';
    configAgentModel.value      = config[`agent_model_${suffix}`]      || '';
    configSynthesisModel.value  = config[`synthesis_model_${suffix}`]  || '';
    configSentinelModel.value   = config[`sentinel_model_${suffix}`]   || '';
    configArchivisteModel.value = config[`archiviste_model_${suffix}`] || '';
    configHost.value = config.host || '';
    configPort.value = config.port || '';
    if (config['handoff_token_threshold']) document.getElementById('config-handoff-tokens').value = config['handoff_token_threshold'];
    if (config['handoff_message_fallback']) document.getElementById('config-handoff-messages').value = config['handoff_message_fallback'];
    configInitial = {
      perf_mode:              config.perf_mode || '0',
      routing_model_cost:     config.routing_model_cost    || '',
      routing_model_perf:     config.routing_model_perf    || '',
      agent_model_cost:       config.agent_model_cost      || '',
      agent_model_perf:       config.agent_model_perf      || '',
      synthesis_model_cost:   config.synthesis_model_cost  || '',
      synthesis_model_perf:   config.synthesis_model_perf  || '',
      sentinel_model_cost:    config.sentinel_model_cost   || '',
      sentinel_model_perf:    config.sentinel_model_perf   || '',
      archiviste_model_cost:  config.archiviste_model_cost || '',
      archiviste_model_perf:  config.archiviste_model_perf || '',
      host: config.host || '',
      port: config.port || '',
    };
  } catch (e) { /* silencieux */ }
}

configPerfMode.addEventListener('change', () => {
  const perf = configPerfMode.checked;
  configPerfLabel.textContent = perf
    ? 'PERFORMANCE — Claude (Haiku / Sonnet)'
    : 'COST — modèles open source';
  const suffix = perf ? 'perf' : 'cost';
  const cfg = configInitial;
  configRoutingModel.value    = cfg[`routing_model_${suffix}`]    || '';
  configAgentModel.value      = cfg[`agent_model_${suffix}`]      || '';
  configSynthesisModel.value  = cfg[`synthesis_model_${suffix}`]  || '';
  configSentinelModel.value   = cfg[`sentinel_model_${suffix}`]   || '';
  configArchivisteModel.value = cfg[`archiviste_model_${suffix}`] || '';
});

btnToggleKey.addEventListener('click', () => {
  if (configKey.type === 'password') {
    configKey.type = 'text';
    btnToggleKey.textContent = '🙈';
  } else {
    configKey.type = 'password';
    btnToggleKey.textContent = '👁';
  }
});

btnSaveConfig.addEventListener('click', async () => {
  btnSaveConfig.disabled = true;
  const updates = {};
  const perf = configPerfMode.checked;
  const suffix = perf ? 'perf' : 'cost';

  const newPerfMode = perf ? '1' : '0';
  if (newPerfMode !== configInitial.perf_mode)
    updates.perf_mode = newPerfMode;

  const routingVal = configRoutingModel.value.trim();
  const agentVal   = configAgentModel.value.trim();
  const synthVal   = configSynthesisModel.value.trim();
  const sentVal    = configSentinelModel.value.trim();
  const archVal    = configArchivisteModel.value.trim();
  const hostVal    = configHost.value.trim();
  const portVal    = configPort.value.trim();
  const keyVal     = configKey.value.trim();

  const rKey = `routing_model_${suffix}`;
  const aKey = `agent_model_${suffix}`;
  const sKey = `synthesis_model_${suffix}`;
  const seKey= `sentinel_model_${suffix}`;
  const arKey= `archiviste_model_${suffix}`;

  if (routingVal !== configInitial[rKey])  updates[rKey]  = routingVal;
  if (agentVal   !== configInitial[aKey])  updates[aKey]  = agentVal;
  if (synthVal   !== configInitial[sKey])  updates[sKey]  = synthVal;
  if (sentVal    !== configInitial[seKey]) updates[seKey] = sentVal;
  if (archVal    !== configInitial[arKey]) updates[arKey] = archVal;
  if (hostVal    !== configInitial.host)   updates.host   = hostVal;
  if (portVal    !== configInitial.port)   updates.port   = portVal;
  if (keyVal)                              updates.openrouter_api_key = keyVal;

  const tokensVal = document.getElementById('config-handoff-tokens').value.trim();
  const msgsVal = document.getElementById('config-handoff-messages').value.trim();
  if (tokensVal) updates['handoff_token_threshold'] = tokensVal;
  if (msgsVal) updates['handoff_message_fallback'] = msgsVal;

  if (Object.keys(updates).length === 0) {
    showSuccess(configSuccess, 'Aucune modification.');
    btnSaveConfig.disabled = false;
    return;
  }

  try {
    await putConfig(updates);
    if (updates.perf_mode !== undefined)   configInitial.perf_mode  = updates.perf_mode;
    if (updates[rKey]  !== undefined) configInitial[rKey]  = updates[rKey];
    if (updates[aKey]  !== undefined) configInitial[aKey]  = updates[aKey];
    if (updates[sKey]  !== undefined) configInitial[sKey]  = updates[sKey];
    if (updates[seKey] !== undefined) configInitial[seKey] = updates[seKey];
    if (updates[arKey] !== undefined) configInitial[arKey] = updates[arKey];
    if (updates.host   !== undefined) configInitial.host   = updates.host;
    if (updates.port   !== undefined) configInitial.port   = updates.port;
    configKey.value = '';
    showSuccess(configSuccess, 'Configuration enregistrée.');
  } catch (e) {
    configSuccess.textContent = 'Erreur lors de l\'enregistrement.';
    configSuccess.style.color = 'var(--color-error-text)';
    setTimeout(() => { configSuccess.textContent = ''; configSuccess.style.color = ''; }, 3000);
  } finally {
    btnSaveConfig.disabled = false;
  }
});

// ── Section 3 : Agents actifs ─────────────────────────────────────
async function loadAgents() {
  try {
    const agents = await getAgents();
    agentsGrid.innerHTML = '';
    for (const agent of agents) {
      const card = document.createElement('div');
      card.className = 'agent-card';
      card.innerHTML = `
        <div class="agent-card-name">${escapeHtml(agent.name)}</div>
        <div class="agent-card-desc">${escapeHtml(agent.description || '')}</div>`;
      agentsGrid.appendChild(card);
    }
    if (agents.length === 0) {
      agentsGrid.innerHTML = '<div class="profile-notice">Aucun agent actif.</div>';
    }
  } catch (e) {
    agentsGrid.innerHTML = '<div class="profile-notice">Impossible de charger les agents.</div>';
  }
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Section 4 : Logs ──────────────────────────────────────────────
async function loadLogs() {
  try {
    const lines = await getLogs();
    if (!lines || lines.length === 0) {
      logsContent.innerHTML = '<span class="logs-empty">Aucun log disponible.</span>';
    } else {
      logsContent.textContent = lines.join('\n');
      logsContent.scrollTop = logsContent.scrollHeight;
    }
  } catch (e) {
    logsContent.innerHTML = '<span class="logs-empty">Aucun log disponible.</span>';
  }
}

btnRefreshLogs.addEventListener('click', loadLogs);

// ── Section KB : Base de connaissance ───────────────────────────
async function loadKnowledgeStats() {
  try {
    const stats = await getKnowledgeStats();
    kbBadge.textContent = stats.doc_count + ' doc' + (stats.doc_count !== 1 ? 's' : '');
  } catch (e) {
    kbBadge.textContent = '';
  }
}

async function loadKnowledgeDocuments() {
  try {
    const docs = await getKnowledgeDocuments();
    kbTableBody.innerHTML = '';
    if (docs.length === 0) {
      kbTableBody.innerHTML = '<tr><td colspan="6" class="kb-empty">Aucun document importé.</td></tr>';
      return;
    }
    for (const doc of docs) {
      const tr = document.createElement('tr');
      const statusClass = doc.status.toLowerCase();
      const date = doc.created_at ? doc.created_at.slice(0, 10) : '—';
      tr.innerHTML = `
        <td>${escapeHtml(doc.filename)}</td>
        <td>${escapeHtml(doc.file_type)}</td>
        <td>${doc.chunk_count}</td>
        <td>${date}</td>
        <td><span class="kb-status ${statusClass}">${escapeHtml(doc.status)}</span></td>
        <td><button class="btn-kb-delete" data-id="${doc.id}">Supprimer</button></td>`;
      kbTableBody.appendChild(tr);
    }
    kbTableBody.querySelectorAll('.btn-kb-delete').forEach(btn => {
      btn.addEventListener('click', () => deleteDocument(Number(btn.dataset.id)));
    });
  } catch (e) {
    kbTableBody.innerHTML = '<tr><td colspan="6" class="kb-empty">Impossible de charger les documents.</td></tr>';
  }
}

async function importDocuments(files) {
  kbImportStatus.textContent = 'Import en cours…';
  kbImportStatus.style.color = 'var(--color-text-muted)';
  btnKbImport.disabled = true;
  kbImportResults.innerHTML = '';

  try {
    const results = await importKnowledgeDocuments(files);
    kbImportResults.innerHTML = '';
    for (const r of results) {
      const row = document.createElement('div');
      row.className = 'kb-result-row ' + (r.status === 'INDEXED' ? 'ok' : 'err');
      const icon = r.status === 'INDEXED' ? '✓' : '✗';
      const msg = r.status === 'INDEXED'
        ? `${icon} ${escapeHtml(r.filename)} — ${r.chunk_count} chunks indexés`
        : `${icon} ${escapeHtml(r.filename)} — ${escapeHtml(r.error || 'Erreur')}`;
      row.textContent = msg;
      kbImportResults.appendChild(row);
    }
    kbImportStatus.textContent = 'Import terminé.';
    kbImportStatus.style.color = '#16a34a';
    setTimeout(() => { kbImportStatus.textContent = ''; kbImportStatus.style.color = ''; }, 4000);
    kbFileInput.value = '';
    await Promise.all([loadKnowledgeStats(), loadKnowledgeDocuments()]);
  } catch (e) {
    kbImportStatus.textContent = 'Erreur : ' + (e.message || 'Échec de l\'import');
    kbImportStatus.style.color = 'var(--color-error-text)';
    setTimeout(() => { kbImportStatus.textContent = ''; kbImportStatus.style.color = ''; }, 5000);
  } finally {
    btnKbImport.disabled = false;
  }
}

async function deleteDocument(id) {
  if (!confirm('Supprimer ce document de la base de connaissance ?')) return;
  try {
    await deleteKnowledgeDocument(id);
    await Promise.all([loadKnowledgeStats(), loadKnowledgeDocuments()]);
  } catch (e) {
    alert('Erreur lors de la suppression : ' + (e.message || 'Échec'));
  }
}

// ── Section SENTINEL ──────────────────────────────────────────────
function _renderSentinelReport(r) {
  sentinelReport.style.display = 'block';
  sentinelError.style.display = 'none';

  const score = r.score;
  sentinelScore.textContent = score;
  sentinelScore.className = 'sentinel-score ' + (score < 40 ? 'low' : score <= 70 ? 'medium' : 'high');

  sentinelBaselineBadge.style.display = r.is_baseline ? 'inline-block' : 'none';

  sentinelObservations.innerHTML = '';
  for (const obs of (r.observations || [])) {
    const li = document.createElement('li');
    li.textContent = obs;
    sentinelObservations.appendChild(li);
  }

  sentinelMetricsBody.innerHTML = '';
  const metrics = r.metrics || {};
  for (const [k, v] of Object.entries(metrics)) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${escapeHtml(k)}</td><td>${typeof v === 'number' ? v.toFixed(2) : escapeHtml(String(v))}</td>`;
    sentinelMetricsBody.appendChild(tr);
  }

  const delta = r.delta_vs_baseline;
  if (delta) {
    sentinelDeltaWrap.style.display = 'block';
    sentinelDeltaContent.innerHTML = `<div class="sentinel-delta">`
      + (delta.summary ? escapeHtml(delta.summary) + '<br>' : '')
      + (delta.score_delta !== undefined ? `Score : ${delta.score_delta >= 0 ? '+' : ''}${delta.score_delta}` : '')
      + `</div>`;
  } else {
    sentinelDeltaWrap.style.display = 'none';
  }

  sentinelProposalsCount.textContent = (r.proposals || []).length + ' proposal' + ((r.proposals || []).length !== 1 ? 's' : '');
}

async function loadSentinelReports() {
  try {
    const reports = await getSentinelReports();
    if (!reports || reports.length === 0) {
      sentinelHistory.innerHTML = '<div class="profile-notice">Aucun rapport disponible.</div>';
      return;
    }
    sentinelHistory.innerHTML = '';
    for (const r of reports) {
      const div = document.createElement('div');
      div.className = 'sentinel-history-item';
      const date = r.created_at ? r.created_at.slice(0, 16).replace('T', ' ') : '—';
      const scoreClass = r.score < 40 ? 'low' : r.score <= 70 ? 'medium' : 'high';
      div.innerHTML = `
        <span class="sentinel-history-date">${date}</span>
        <span class="sentinel-history-score sentinel-score ${scoreClass}" style="font-size:16px">${r.score}</span>
        ${r.is_baseline ? '<span class="kb-badge">BASELINE</span>' : ''}
        <span style="color:var(--color-text-muted);font-size:11px">${r.pending_proposals} proposal${r.pending_proposals !== 1 ? 's' : ''} en attente</span>`;
      sentinelHistory.appendChild(div);
    }
  } catch (e) {
    sentinelHistory.innerHTML = '<div class="profile-notice">Impossible de charger l\'historique.</div>';
  }
}

btnSentinel.addEventListener('click', async () => {
  btnSentinel.disabled = true;
  sentinelSpinner.style.display = 'block';
  sentinelError.style.display = 'none';
  sentinelReport.style.display = 'none';

  try {
    const report = await runSentinelAnalysis();
    _renderSentinelReport(report);
    await loadSentinelReports();
  } catch (e) {
    sentinelError.textContent = 'Erreur : ' + (e.message || 'Échec de l\'analyse SENTINEL');
    sentinelError.style.display = 'block';
  } finally {
    sentinelSpinner.style.display = 'none';
    btnSentinel.disabled = false;
  }
});

// ── Section Proposals ────────────────────────────────────────────
function _proposalTypeBadge(ptype) {
  const map = {
    'UPDATE_AGENT_PROMPT': ['agent', 'Agent prompt'],
    'UPDATE_COMPANY_RULE': ['rule', 'Règle métier'],
    'ARCHIVE_DOCUMENT':   ['archive', 'Archivage doc'],
  };
  const [cls, label] = map[ptype] || ['agent', ptype];
  return `<span class="proposal-type-badge ${cls}">${label}</span>`;
}

async function loadProposals() {
  try {
    const proposals = await getProposals('PENDING');
    proposalsBadge.textContent = proposals.length > 0
      ? proposals.length + ' en attente'
      : '';
    proposalsPendingList.innerHTML = '';
    if (proposals.length === 0) {
      proposalsPendingList.innerHTML = '<div class="profile-notice">Aucune proposition en attente.</div>';
      return;
    }
    for (const p of proposals) {
      const preview = p.content.length > 200 ? p.content.slice(0, 200) + '…' : p.content;
      const card = document.createElement('div');
      card.className = 'proposal-card';
      card.dataset.id = p.id;
      card.innerHTML = `
        <div class="proposal-card-header">
          ${_proposalTypeBadge(p.proposal_type)}
          <span class="proposal-target">${escapeHtml(p.target)}</span>
        </div>
        <div class="proposal-rationale">${escapeHtml(p.rationale || '')}</div>
        <div class="proposal-preview">${escapeHtml(preview)}</div>
        <div class="proposal-actions">
          <button class="btn-approve" data-id="${p.id}">Approuver</button>
          <button class="btn-reject"  data-id="${p.id}">Rejeter</button>
        </div>`;
      proposalsPendingList.appendChild(card);
    }
    proposalsPendingList.querySelectorAll('.btn-approve').forEach(btn => {
      btn.addEventListener('click', () => approveProposal(Number(btn.dataset.id), btn));
    });
    proposalsPendingList.querySelectorAll('.btn-reject').forEach(btn => {
      btn.addEventListener('click', () => rejectProposal(Number(btn.dataset.id), btn));
    });
  } catch (e) {
    proposalsPendingList.innerHTML = '<div class="profile-notice">Impossible de charger les propositions.</div>';
  }
}

async function loadProposalHistory() {
  try {
    const [approved, rejected] = await Promise.all([
      getProposals('APPROVED'),
      getProposals('REJECTED'),
    ]);
    const all = [...approved, ...rejected]
      .sort((a, b) => (b.reviewed_at || b.created_at).localeCompare(a.reviewed_at || a.created_at))
      .slice(0, 10);
    proposalsHistoryList.innerHTML = '';
    if (all.length === 0) {
      proposalsHistoryList.innerHTML = '<div class="profile-notice">Aucun historique.</div>';
      return;
    }
    for (const p of all) {
      const div = document.createElement('div');
      div.className = 'proposal-history-item';
      const date = (p.reviewed_at || p.created_at || '').slice(0, 16).replace('T', ' ');
      const stCls = p.status === 'APPROVED' ? 'approved' : 'rejected';
      const stLabel = p.status === 'APPROVED' ? 'Approuvée' : 'Rejetée';
      div.innerHTML = `
        <span class="proposal-history-status ${stCls}">${stLabel}</span>
        ${_proposalTypeBadge(p.proposal_type)}
        <span class="proposal-target">${escapeHtml(p.target)}</span>
        <span style="color:var(--color-text-muted);font-size:11px;margin-left:auto">${date}</span>`;
      proposalsHistoryList.appendChild(div);
    }
  } catch (e) {
    proposalsHistoryList.innerHTML = '<div class="profile-notice">Impossible de charger l\'historique.</div>';
  }
}

async function approveProposal(id, btn) {
  if (btn) { btn.disabled = true; const sib = btn.nextElementSibling; if (sib) sib.disabled = true; }
  try {
    await patchProposal(id, 'approve');
    await Promise.all([loadProposals(), loadProposalHistory()]);
  } catch (e) {
    alert('Erreur approbation : ' + (e.message || 'Impossible d\'approuver'));
    if (btn) { btn.disabled = false; const sib = btn.nextElementSibling; if (sib) sib.disabled = false; }
  }
}

async function rejectProposal(id, btn) {
  if (!confirm('Rejeter cette proposition ?')) return;
  if (btn) { btn.disabled = true; const prev = btn.previousElementSibling; if (prev) prev.disabled = true; }
  try {
    await patchProposal(id, 'reject');
    await Promise.all([loadProposals(), loadProposalHistory()]);
  } catch (e) {
    alert('Erreur rejet : ' + (e.message || 'Impossible de rejeter'));
    if (btn) { btn.disabled = false; const prev = btn.previousElementSibling; if (prev) prev.disabled = false; }
  }
}

// ── Section Test Sessions ────────────────────────────────────
async function loadTestSessions() {
  try {
    const sessions = await getTestSessions();
    testSessionsList.innerHTML = '';
    if (!sessions || sessions.length === 0) {
      testSessionsList.innerHTML = '<div class="profile-notice">Aucune session de test créée.</div>';
      return;
    }
    const list = document.createElement('div');
    list.className = 'test-session-list';
    for (const s of sessions) {
      const item = document.createElement('div');
      item.className = 'test-session-item';
      const date = (s.created_at || '').slice(0, 10);
      item.innerHTML = `
        <span class="test-session-name">${escapeHtml(s.name)}
          ${s.is_active ? '<span class="kb-badge" style="margin-left:6px">ACTIVE</span>' : ''}
        </span>
        <span class="test-session-meta">${s.doc_count} doc${s.doc_count !== 1 ? 's' : ''} &middot; créée le ${date}</span>
        <button class="btn-save" data-id="${s.id}" ${s.is_active ? 'disabled' : ''}
          onclick="activateSession(${s.id})" style="font-size:11px;padding:4px 10px">Activer</button>
        <button class="btn-kb-delete" data-id="${s.id}"
          onclick="resetSession(${s.id})" style="font-size:11px;padding:4px 10px;color:#dc2626;border-color:#dc2626">Reset</button>`;
      list.appendChild(item);
    }
    testSessionsList.appendChild(list);
  } catch (e) {
    testSessionsList.innerHTML = '<div class="profile-notice">Impossible de charger les sessions.</div>';
  }
}

async function createSession() {
  const name = tsNameInput.value.trim();
  if (!name) {
    tsCreateError.textContent = 'Le nom de session ne peut pas être vide.';
    tsCreateError.style.display = 'block';
    return;
  }
  tsCreateError.style.display = 'none';
  btnCreateSession.disabled = true;
  try {
    await createTestSession(name);
    tsNameInput.value = '';
    await loadTestSessions();
  } catch (e) {
    tsCreateError.textContent = 'Erreur : ' + (e.message || 'Impossible de créer la session');
    tsCreateError.style.display = 'block';
  } finally {
    btnCreateSession.disabled = false;
  }
}

async function activateSession(id) {
  try {
    await activateTestSession(id);
    await loadTestSessions();
  } catch (e) {
    alert('Erreur activation : ' + (e.message || 'Impossible d\'activer'));
  }
}

async function resetSession(id) {
  if (!confirm('Réinitialiser cette session ? Les documents de test seront supprimés définitivement.')) return;
  try {
    const result = await resetTestSession(id);
    await loadTestSessions();
    alert(`Session réinitialisée. ${result.docs_deleted} doc(s) supprimé(s).`);
  } catch (e) {
    alert('Erreur reset : ' + (e.message || 'Impossible de réinitialiser'));
  }
}

btnCreateSession.addEventListener('click', createSession);
tsNameInput.addEventListener('keydown', e => { if (e.key === 'Enter') createSession(); });

btnKbImport.addEventListener('click', () => {
  const files = kbFileInput.files;
  if (!files || files.length === 0) {
    kbImportStatus.textContent = 'Sélectionnez au moins un fichier.';
    kbImportStatus.style.color = 'var(--color-error-text)';
    setTimeout(() => { kbImportStatus.textContent = ''; kbImportStatus.style.color = ''; }, 3000);
    return;
  }
  importDocuments(files);
});

// ── Utilitaire ────────────────────────────────────────────────────
function showSuccess(el, msg) {
  el.textContent = msg;
  el.style.color = '';
  setTimeout(() => { el.textContent = ''; }, 3000);
}

// ── Démarrage ─────────────────────────────────────────────────────
init();
