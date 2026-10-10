import { esc, VERDICT_BADGES, STATUS_BADGES } from '../utils/formatting.js';

export function createRunCard(r, events) {
  const s = r.state || {}, v = s.verdict, p = s.response_proposal;
  
  const statusBadge = STATUS_BADGES[r.status] || STATUS_BADGES.completed;
  const statusLabel = r.status ? r.status.replace(/_/g, ' ') : 'Unknown';
  
  const statusDot = r.status === 'running' 
    ? 'bg-blue-500 animate-pulse' 
    : r.status === 'failed' 
    ? 'bg-red-500' 
    : r.status === 'pending_approval' 
    ? 'bg-amber-500' 
    : 'bg-emerald-500';

  const verdictSection = v ? `
    <div class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <h4 class="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-3">
          Observations
        </h4>
        <ul class="text-xs text-gray-600 space-y-2 list-disc list-inside leading-relaxed">
          ${(v.confirmed_facts || []).map(f => `<li>${esc(f)}</li>`).join('') || '<li class="text-gray-400 italic">No confirmed observations.</li>'}
        </ul>
      </div>
      
      <div class="bg-white border border-gray-200 rounded-lg p-5">
        <h4 class="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-3">
          Inferences & Context
        </h4>
        <ul class="text-xs text-gray-600 space-y-2 list-disc list-inside leading-relaxed">
          ${(v.inferred_relationships || []).map(i => `<li>${esc(i)}</li>`).join('') || '<li class="text-gray-400 italic">No inferences made.</li>'}
        </ul>
      </div>
    </div>

    <div class="mb-6 bg-white border border-gray-200 rounded-lg p-5">
      <div class="flex items-center justify-between pb-3 mb-3 border-b border-gray-100">
        <div class="flex items-center gap-3">
          <span class="text-xs font-semibold text-gray-900">Verdict</span>
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border capitalize ${VERDICT_BADGES[v.classification] || 'bg-gray-100 text-gray-700 border-gray-200'}">
            ${esc(v.classification).replace(/_/g, ' ')}
          </span>
        </div>
        <span class="text-xs text-gray-500 font-medium">${(v.confidence * 100).toFixed(0)}% confidence</span>
      </div>
      <p class="text-xs text-gray-700 leading-relaxed">${esc(v.reasoning)}</p>
    </div>
  ` : '';

  const proposalSection = p ? `
    <div class="mb-6">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Response Plan</h3>
      <div class="bg-white border border-gray-200 border-l-4 border-l-blue-600 rounded-lg p-5">
        <div class="flex items-center gap-2 mb-3">
          <span class="font-mono text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">${esc(p.action)}</span>
          <span class="text-gray-400">→</span>
          <span class="font-mono text-xs text-gray-700 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded">${esc(p.target)}</span>
        </div>
        <p class="text-xs text-gray-600 mb-4 leading-relaxed">${esc(p.justification)}</p>
        
        <div class="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500 bg-gray-50 p-3 rounded border border-gray-100 font-mono">
          <span>Rollback: ${esc(p.rollback_plan)}</span>
          <span class="font-medium text-gray-700">Risk: ${esc(p.risk_tier).toUpperCase()}</span>
        </div>

        ${r.status === 'pending_approval' ? `
          <div class="mt-4 flex gap-3">
            <button onclick="window.appState.decide('${esc(r.run_id)}','approve')" class="bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium py-2 px-4 rounded-md shadow-xs transition-colors">Approve Execution</button>
            <button onclick="window.appState.decide('${esc(r.run_id)}','reject')" class="bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 text-xs font-medium py-2 px-4 rounded-md transition-colors">Reject</button>
          </div>
        ` : ''}
      </div>
    </div>
  ` : '';

  const errorsSection = s.errors?.length ? `
    <div class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 class="text-xs font-semibold text-red-800 uppercase tracking-wider mb-1.5">Execution Error</h3>
      <div class="text-xs text-red-700 font-mono whitespace-pre-wrap">${s.errors.map(esc).join('<br>')}</div>
    </div>
  ` : '';

  const trailSection = events.length ? `
    <div class="mb-6">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Audit Trail</h3>
      <div class="bg-white border border-gray-200 rounded-lg divide-y divide-gray-100 overflow-hidden font-mono text-xs">
        ${events.map(e => `
          <div class="flex items-start gap-4 p-3.5 hover:bg-gray-50/50 transition-colors">
            <span class="text-gray-400 font-normal shrink-0 pt-0.5">${esc(e.timestamp?.slice(11, 19))}</span>
            <div class="flex-1 min-w-0">
              <span class="text-gray-900 font-medium block mb-1">${esc(e.event_type)}</span>
              <div class="text-gray-500 break-all bg-gray-50 border border-gray-100 p-2 rounded text-[11px]">${esc(JSON.stringify(e.details))}</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  ` : '';

  return `
    <div class="max-w-4xl mx-auto pb-10">
      <div class="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
        <div class="flex items-center gap-3">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium border capitalize ${statusBadge}">
            <span class="w-1.5 h-1.5 rounded-full ${statusDot}"></span>
            ${esc(statusLabel)}
          </span>
          <span class="text-xs font-mono text-gray-500">${esc(r.run_id)}</span>
        </div>
      </div>
      
      ${errorsSection}
      ${verdictSection}
      ${proposalSection}
      ${trailSection}
    </div>
  `;
}
