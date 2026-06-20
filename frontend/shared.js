function formatDate(updatedAt) {
  if (!updatedAt) return '';
  const date = new Date(updatedAt.replace(' ', 'T'));
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterdayStart = new Date(todayStart);
  yesterdayStart.setDate(yesterdayStart.getDate() - 1);

  if (date >= todayStart) {
    const h = String(date.getHours()).padStart(2, '0');
    const m = String(date.getMinutes()).padStart(2, '0');
    return `Aujourd'hui ${h}:${m}`;
  }
  if (date >= yesterdayStart) {
    return 'Hier';
  }
  const months = ['jan.', 'fév.', 'mars', 'avr.', 'mai', 'juin',
                  'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
  return `${date.getDate()} ${months[date.getMonth()]}`;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderMarkdown(text) {
  if (!text) return '';
  const lines = text.split('\n');
  const result = [];
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    if (/^### /.test(line)) {
      if (inList) { result.push('</ul>'); inList = false; }
      result.push(`<h3>${escapeHtml(line.slice(4))}</h3>`);
      continue;
    }
    if (/^## /.test(line)) {
      if (inList) { result.push('</ul>'); inList = false; }
      result.push(`<h2>${escapeHtml(line.slice(3))}</h2>`);
      continue;
    }
    if (/^# /.test(line)) {
      if (inList) { result.push('</ul>'); inList = false; }
      result.push(`<h1>${escapeHtml(line.slice(2))}</h1>`);
      continue;
    }
    if (/^- /.test(line)) {
      if (!inList) { result.push('<ul>'); inList = true; }
      result.push(`<li>${inlineMarkdown(escapeHtml(line.slice(2)))}</li>`);
      continue;
    }

    if (inList) { result.push('</ul>'); inList = false; }

    if (line.trim() === '') {
      result.push('<br>');
    } else {
      result.push(`<p>${inlineMarkdown(escapeHtml(line))}</p>`);
    }
  }

  if (inList) result.push('</ul>');
  return result.join('');
}

function inlineMarkdown(escaped) {
  return escaped
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

function getAgentLabel(agentCode) {
  if (agentCode === 'ANALYSTE') return 'Analyste';
  if (agentCode === 'REDACTEUR') return 'Rédacteur';
  return 'Boss';
}
