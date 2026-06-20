const BASE = '';

async function apiFetch(path, options = {}) {
  const res = await fetch(BASE + path, options);
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

function json(method, body) {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
}

function getConversations() {
  return apiFetch('/api/conversations');
}

function createConversation() {
  return apiFetch('/api/conversations', json('POST', {}));
}

function deleteConversation(id) {
  return apiFetch(`/api/conversations/${id}`, { method: 'DELETE' });
}

function patchConversation(id, title) {
  return apiFetch(`/api/conversations/${id}`, json('PATCH', { title }));
}

function getMessages(conversationId) {
  return apiFetch(`/api/conversations/${conversationId}/messages`);
}

function postMessage(conversationId, content) {
  return apiFetch(`/api/conversations/${conversationId}/messages`, json('POST', { content }));
}

function getJobStatus(jobId) {
  return apiFetch(`/api/jobs/${jobId}`);
}

function getPinned(conversationId) {
  return apiFetch(`/api/conversations/${conversationId}/pinned`);
}

function createPinned(conversationId, content) {
  return apiFetch(`/api/conversations/${conversationId}/pinned`, json('POST', { content }));
}

function deletePinned(pinnedId) {
  return apiFetch(`/api/pinned/${pinnedId}`, { method: 'DELETE' });
}

function getCompanyProfile() {
  return apiFetch('/api/company-profile');
}

function putCompanyProfile(data) {
  return apiFetch('/api/company-profile', json('PUT', data));
}

function getConfig() {
  return apiFetch('/api/config');
}

function putConfig(data) {
  return apiFetch('/api/config', json('PUT', data));
}

function getAgents() {
  return apiFetch('/api/agents');
}

function getLogs() {
  return apiFetch('/api/logs');
}
