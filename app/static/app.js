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

let selectedIncidentId = null;

function selectIncident(id) {
  selectedIncidentId = id;
  $('selected-incident-id').textContent = id;
  tick(true); // force re-render
}

function incidentCard(i) {
  const isSelected = i.id === selectedIncidentId;
  let borderColors = 'border-gray-300 hover:border-gray-500';
  let bgColors = 'bg-white hover:bg-gray-50';
  let badgeColor = 'bg-gray-200 text-gray-700';

  if (i.severity === 'critical') { borderColors = 'border-purple-500'; bgColors = 'bg-purple-50'; badgeColor = 'bg-purple-200 text-purple-800'; }
  else if (i.severity === 'high') { borderColors = 'border-red-500'; bgColors = 'bg-red-50'; badgeColor = 'bg-red-200 text-red-800'; }

  if (isSelected) {
    bgColors = 'bg-blue-100 ring-2 ring-blue-500';
  }

  return `<div onclick="selectIncident('${esc(i.id)}')" class="cursor-pointer p-4 border rounded-lg transition-all ${borderColors} ${bgColors}">
    <div class="flex justify-between items-start mb-2">
      <b class="uppercase text-sm tracking-wider font-bold text-gray-800">${esc(i.type).replace('_', ' ')}</b>
      <span class="text-xs px-2 py-1 rounded font-bold uppercase ${badgeColor}">${esc(i.severity)}</span>
    </div>
    <div class="text-sm text-gray-700 font-medium mb-2">${esc(i.message)}</div>
    <div class="flex justify-between items-center text-xs text-gray-500">
      <span>${esc(i.state)} · ${esc(i.event_count)} events</span>
      <span class="truncate ml-2" title="${esc(i.id)}">${esc(i.id).split('-')[0] + '-...'}</span>
    </div>
  </div>`;
}

function runCard(r, events) {
  const s = r.state || {}, v = s.verdict, p = s.response_proposal;
  
  const verdict = v ? `
    <div class="bg-white p-4 rounded border shadow-sm mb-4">
      <h3 class="text-sm font-bold text-gray-500 uppercase tracking-wider mb-2">AI Verdict</h3>
      <div class="flex items-center space-x-3 mb-3">
        <span class="px-3 py-1 rounded font-bold text-sm ${VERDICT[v.classification] || 'bg-gray-200 text-gray-800'}">${esc(v.classification).replace('_', ' ')}</span>
        <span class="text-sm text-gray-600">Confidence: ${(v.confidence * 100).toFixed(0)}%</span>
      </div>
      <p class="text-sm text-gray-800 leading-relaxed">${esc(v.reasoning)}</p>
    </div>` : '';

  const proposal = p ? `
    <div class="bg-white p-4 rounded border border-blue-200 shadow-sm mb-4">
      <h3 class="text-sm font-bold text-blue-600 uppercase tracking-wider mb-2">Action Taken</h3>
      <div class="flex items-center space-x-2 text-lg mb-2">
        <span class="font-bold text-gray-800">${esc(p.action)}</span>
        <span class="text-gray-400">→</span>
        <code class="bg-gray-100 px-2 py-1 rounded text-pink-600 font-bold">${esc(p.target)}</code>
      </div>
      <p class="text-sm text-gray-700 mb-2">${esc(p.justification)}</p>
      <div class="text-xs text-gray-500 bg-gray-50 p-2 rounded">Rollback: ${esc(p.rollback_plan)}</div>
      ${r.status === 'pending_approval' ? `
      <div class="mt-4 flex space-x-3">
        <button onclick="decide('${esc(r.run_id)}','approve')" class="flex-1 bg-green-500 hover:bg-green-600 text-white py-2 rounded font-bold shadow transition">✅ Approve Execution</button>
        <button onclick="decide('${esc(r.run_id)}','reject')" class="flex-1 bg-red-500 hover:bg-red-600 text-white py-2 rounded font-bold shadow transition">❌ Reject</button>
      </div>` : ''}
    </div>` : '';

  const errors = s.errors?.length ? `<div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded mb-4 text-sm font-bold">${s.errors.map(esc).join('<br>')}</div>` : '';

  const trail = events.map(e =>
    `<div class="py-1 border-b border-gray-100 last:border-0 hover:bg-gray-50 flex items-start space-x-3">
      <span class="text-gray-400 text-xs w-20 shrink-0 pt-0.5">${esc(e.timestamp?.slice(11, 19))}</span>
      <div>
        <b class="text-blue-700 text-xs uppercase">${esc(e.event_type)}</b>
        <div class="text-xs text-gray-600 font-mono mt-0.5 break-all">${esc(JSON.stringify(e.details))}</div>
      </div>
    </div>`).join('');

  return `<div class="animate-fade-in">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-3">
        <div class="h-3 w-3 rounded-full ${r.status === 'running' ? 'bg-blue-500 animate-ping' : r.status === 'completed' ? 'bg-green-500' : 'bg-gray-400'}"></div>
        <span class="font-bold text-gray-700 uppercase tracking-widest text-sm">${esc(r.status)}</span>
      </div>
      <span class="text-xs text-gray-400 font-mono">Run: ${esc(r.run_id)}</span>
    </div>
    ${errors}
    ${verdict}
    ${proposal}
    <div class="bg-white rounded border shadow-sm mt-6">
      <div class="bg-gray-50 border-b p-3 text-xs font-bold text-gray-600 uppercase tracking-wider">AI Audit Trail (${events.length} steps)</div>
      <div class="p-3 max-h-64 overflow-auto">${trail}</div>
    </div>
  </div>`;
}

let last = '';
async function tick(force = false) {
  try {
    const [{incidents}, runs] = await Promise.all([getJSON('/incidents'), getJSON('/agents/runs')]);
    const events = await Promise.all(runs.map(r => getJSON(`/agents/runs/${r.run_id}/events`).then(d => d.events)));
    
    $('stats').textContent = `Tracking ${incidents.length} threats · ${runs.length} AI investigations`;

    const key = JSON.stringify([incidents, runs, events, selectedIncidentId]);
    if (key === last && !force) return;
    last = key;
    
    $('inc-list').innerHTML = incidents.map(incidentCard).join('') || '<div class="text-gray-400 text-center mt-10">No incidents yet. Run a scenario.</div>';
    
    if (selectedIncidentId) {
      const runIndex = runs.findIndex(r => r.incident_id === selectedIncidentId);
      if (runIndex !== -1) {
        $('ai-list').innerHTML = runCard(runs[runIndex], events[runIndex]);
      } else {
        $('ai-list').innerHTML = `<div class="flex h-full items-center justify-center text-gray-400">
          <div class="text-center">
            <svg class="animate-spin h-8 w-8 text-blue-500 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p>AI is investigating this threat...</p>
          </div>
        </div>`;
      }
    }
    
    $('err').textContent = '';
  } catch (e) {
    $('err').textContent = `API error: ${e}`;
  }
}

async function decide(id, action) {
  const body = action === 'approve' ? {actor: 'analyst'} : {actor: 'analyst', reason: 'Rejected from copilot UI'};
  await fetch(`/agents/runs/${id}/${action}`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  tick(true);
}

setInterval(tick, 2000);
tick();
