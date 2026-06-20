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

function getKnowledgeStats() {
  return apiFetch('/api/knowledge/stats');
}

function getKnowledgeDocuments(sessionId) {
  const q = sessionId != null ? `?session_id=${sessionId}` : '';
  return apiFetch(`/api/knowledge/documents${q}`);
}

async function importKnowledgeDocuments(files) {
  const fd = new FormData();
  for (const f of files) fd.append('files', f);
  const res = await fetch('/api/knowledge/import', { method: 'POST', body: fd });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

function deleteKnowledgeDocument(id) {
  return apiFetch(`/api/knowledge/documents/${id}`, { method: 'DELETE' });
}

function runSentinelAnalysis() {
  return apiFetch('/api/sentinel/analyze', { method: 'POST' });
}

function getSentinelReports() {
  return apiFetch('/api/sentinel/reports');
}

function getProposals(status = 'PENDING') {
  return apiFetch(`/api/learning-proposals?status=${encodeURIComponent(status)}`);
}

function patchProposal(id, action) {
  return apiFetch(`/api/learning-proposals/${id}`, json('PATCH', { action }));
}

function getActiveTestSession() {
  return apiFetch('/api/test-sessions/active');
}

function getTestSessions() {
  return apiFetch('/api/test-sessions');
}

function createTestSession(name) {
  return apiFetch('/api/test-sessions', json('POST', { name }));
}

function activateTestSession(id) {
  return apiFetch(`/api/test-sessions/${id}/activate`, { method: 'POST' });
}

function resetTestSession(id) {
  return apiFetch(`/api/test-sessions/${id}/reset`, { method: 'POST' });
}
