// ── Références DOM ────────────────────────────────────────────────
const profileNotice   = document.getElementById('profile-notice');
const profileName     = document.getElementById('profile-name');
const profileSector   = document.getElementById('profile-sector');
const profileTone     = document.getElementById('profile-tone');
const profileRules    = document.getElementById('profile-rules');
const profileNameErr  = document.getElementById('profile-name-error');
const btnSaveProfile  = document.getElementById('btn-save-profile');
const profileSuccess  = document.getElementById('profile-success');

const configModel     = document.getElementById('config-model');
const configHost      = document.getElementById('config-host');
const configPort      = document.getElementById('config-port');
const configKey       = document.getElementById('config-key');
const btnToggleKey    = document.getElementById('btn-toggle-key');
const btnSaveConfig   = document.getElementById('btn-save-config');
const configSuccess   = document.getElementById('config-success');

const agentsGrid      = document.getElementById('agents-grid');
const logsContent     = document.getElementById('logs-content');
const btnRefreshLogs  = document.getElementById('btn-refresh-logs');

// Tracker des valeurs initiales de config pour détecter les modifications
let configInitial = {};

// ── Initialisation ────────────────────────────────────────────────
async function init() {
  await Promise.allSettled([
    loadProfile(),
    loadConfig(),
    loadAgents(),
    loadLogs(),
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
    configModel.value = config.model_id || '';
    configHost.value  = config.host || '';
    configPort.value  = config.port || '';
    // La clé reste toujours vide
    configInitial = {
      model_id: config.model_id || '',
      host:     config.host || '',
      port:     config.port || '',
    };
  } catch (e) { /* silencieux */ }
}

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

  const model = configModel.value.trim();
  const host  = configHost.value.trim();
  const port  = configPort.value.trim();
  const key   = configKey.value.trim();

  if (model !== configInitial.model_id) updates.model_id = model;
  if (host  !== configInitial.host)     updates.host = host;
  if (port  !== configInitial.port)     updates.port = port;
  if (key)                              updates.openrouter_api_key = key;

  if (Object.keys(updates).length === 0) {
    showSuccess(configSuccess, 'Aucune modification.');
    btnSaveConfig.disabled = false;
    return;
  }

  try {
    await putConfig(updates);
    // Mettre à jour les valeurs initiales
    if (updates.model_id !== undefined) configInitial.model_id = updates.model_id;
    if (updates.host     !== undefined) configInitial.host     = updates.host;
    if (updates.port     !== undefined) configInitial.port     = updates.port;
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

// ── Utilitaire ────────────────────────────────────────────────────
function showSuccess(el, msg) {
  el.textContent = msg;
  el.style.color = '';
  setTimeout(() => { el.textContent = ''; }, 3000);
}

// ── Démarrage ─────────────────────────────────────────────────────
init();
