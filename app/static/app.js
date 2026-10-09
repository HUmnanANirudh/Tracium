const $ = id => document.getElementById(id);
// Log content is attacker-controlled: never inject it as HTML.
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const getJSON = url => fetch(url).then(r => r.ok ? r.json() : Promise.reject(`${url} -> ${r.status}`));

const STATUS = {
  running:          'bg-blue-100 text-blue-800 animate-pulse',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  completed:        'bg-green-100 text-green-800',
  failed:           'bg-red-100 text-red-800',
};
const VERDICT = {true_positive: 'text-red-700', false_positive: 'text-green-700', inconclusive: 'text-yellow-700'};

function incidentCard(i) {
  return `<div class="p-3 mb-2 border-l-4 ${i.severity === 'high' || i.severity === 'critical' ? 'border-red-500 bg-red-50' : 'border-gray-400 bg-gray-50'}">
    <b class="uppercase">${esc(i.type)}</b>
    <span class="text-xs text-gray-500">${esc(i.severity)} · ${esc(i.state)} · ${esc(i.event_count)} events</span><br>
    <span class="text-sm">${esc(i.message)}</span>
    <div class="text-xs text-gray-400">${esc(i.id)}</div>
  </div>`;
}

function runCard(r, events) {
  const s = r.state || {}, v = s.verdict, p = s.response_proposal;
  const verdict = v ? `
    <div class="mt-2"><b class="${VERDICT[v.classification] || ''}">${esc(v.classification)}</b>
      <span class="text-xs">confidence ${esc(v.confidence)}</span></div>
    <div class="text-sm">${esc(v.reasoning)}</div>
    ${v.evidence_ids?.length ? `<div class="text-xs text-gray-500">validated evidence: ${v.evidence_ids.map(esc).join(', ')}</div>` : ''}
    ${v.missing_evidence?.length ? `<div class="text-xs text-yellow-700">missing: ${v.missing_evidence.map(esc).join('; ')}</div>` : ''}` : '';
  const proposal = p ? `
    <div class="mt-2 p-2 bg-white border text-sm">
      <b>Proposed:</b> ${esc(p.action)} → <code>${esc(p.target)}</code>
      <span class="text-xs">(risk ${esc(p.risk_tier)}, ${p.requires_approval ? 'needs approval' : 'auto-allowed by policy'})</span>
      <div class="text-xs mt-1">${esc(p.justification)}</div>
      <div class="text-xs text-gray-500">rollback: ${esc(p.rollback_plan)}</div>
    </div>` : '';
  const errors = s.errors?.length ? `<div class="mt-2 text-xs text-red-700">${s.errors.map(esc).join('<br>')}</div>` : '';
  const buttons = r.status === 'pending_approval' ? `
    <div class="mt-2">
      <button onclick="decide('${esc(r.run_id)}','approve')" class="bg-green-600 text-white px-3 py-1 text-sm rounded font-bold">Approve</button>
      <button onclick="decide('${esc(r.run_id)}','reject')" class="bg-red-600 text-white px-3 py-1 text-sm rounded font-bold">Reject</button>
    </div>` : '';
  const trail = events.map(e =>
    `<div><span class="text-gray-400">${esc(e.timestamp?.slice(11, 19))}</span> <b>${esc(e.event_type)}</b> ${esc(JSON.stringify(e.details))}</div>`).join('');

  return `<div class="p-3 mb-3 border bg-blue-50">
    <div class="text-sm"><b>${esc(r.run_id)}</b>
      <span class="px-2 rounded text-xs ${STATUS[r.status] || ''}">${esc(r.status)}</span>
      <span class="text-xs text-gray-500">${esc(r.incident_id)}</span></div>
    ${verdict}${proposal}${errors}${buttons}
    <details class="mt-2 text-xs"><summary class="cursor-pointer">audit trail (${events.length})</summary>
      <div class="mt-1 max-h-48 overflow-auto bg-white p-2 break-all">${trail}</div></details>
  </div>`;
}

let last = '';
async function tick() {
  try {
    const [{incidents}, runs] = await Promise.all([getJSON('/incidents'), getJSON('/agents/runs')]);
    const events = await Promise.all(runs.map(r => getJSON(`/agents/runs/${r.run_id}/events`).then(d => d.events)));
    // Re-render only on change so open <details> panels stay open.
    const key = JSON.stringify([incidents, runs, events]);
    if (key === last) return;
    last = key;
    $('inc-list').innerHTML = incidents.map(incidentCard).join('') || 'No incidents yet. Run a scenario.';
    $('ai-list').innerHTML = runs.slice().reverse().map((r, i, a) => runCard(r, events[a.length - 1 - i])).join('') || 'No investigations yet.';
    $('err').textContent = '';
  } catch (e) {
    $('err').textContent = `API error: ${e}`;
  }
}

async function decide(id, action) {
  const body = action === 'approve' ? {actor: 'analyst'} : {actor: 'analyst', reason: 'Rejected from copilot UI'};
  await fetch(`/agents/runs/${id}/${action}`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  tick();
}

setInterval(tick, 2000);
tick();
