import { esc, VERDICT_COLORS, STATUS_COLORS } from '../utils/formatting.js';

export function createRunCard(r, events) {
  const s = r.state || {}, v = s.verdict, p = s.response_proposal;
  
  const statusStyle = STATUS_COLORS[r.status] || STATUS_COLORS.completed;
  
  const verdictSection = v ? `
    <div class="mb-8 grid grid-cols-2 gap-6">
      <div class="glass-panel p-5 flex flex-col">
        <h4 class="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
          What I See (Observation)
        </h4>
        <ul class="text-sm text-gray-700 space-y-2 list-disc list-inside flex-1 leading-relaxed">
          ${(v.confirmed_facts || []).map(f => `<li>${esc(f)}</li>`).join('') || '<li class="text-gray-400 italic">No facts confirmed.</li>'}
        </ul>
      </div>
      
      <div class="glass-panel p-5 flex flex-col">
        <h4 class="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
          What It Means (Inference)
        </h4>
        <ul class="text-sm text-gray-700 space-y-2 list-disc list-inside flex-1 leading-relaxed">
          ${(v.inferred_relationships || []).map(i => `<li>${esc(i)}</li>`).join('') || '<li class="text-gray-400 italic">No inferences made.</li>'}
        </ul>
      </div>
    </div>

    <div class="mb-8 glass-panel p-6">
      <div class="flex justify-between items-start mb-4 border-b border-gray-100 pb-4">
        <div class="flex items-center gap-3">
          <span class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Thinking & Verdict</span>
          <span class="text-[11px] px-2.5 py-1 border rounded-full font-mono font-bold uppercase ${VERDICT_COLORS[v.classification] || 'text-gray-500 border-gray-300'}">
            ${esc(v.classification).replace(/_/g, ' ')}
          </span>
        </div>
        <span class="text-[11px] font-mono text-gray-400 font-semibold bg-gray-50 px-2 py-1 rounded">CONFIDENCE: ${(v.confidence * 100).toFixed(0)}%</span>
      </div>
      <p class="text-sm text-gray-700 leading-relaxed">${esc(v.reasoning)}</p>
    </div>
  ` : '';

  const proposalSection = p ? `
    <div class="mb-8">
      <h3 class="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-3">
        <div class="h-px bg-gray-200 flex-1"></div>
        Decided Action
        <div class="h-px bg-gray-200 flex-1"></div>
      </h3>
      <div class="glass-panel p-6 relative overflow-hidden border-l-4 border-l-brand-base">
        <div class="flex items-center space-x-3 font-mono text-sm mb-4">
          <span class="text-brand-base font-bold bg-brand-glow px-2 py-1 rounded">${esc(p.action)}</span>
          <span class="text-gray-400">→</span>
          <span class="text-gray-700 bg-gray-100 px-2 py-1 rounded border border-gray-200">${esc(p.target)}</span>
        </div>
        <p class="text-sm text-gray-600 mb-5 leading-relaxed">${esc(p.justification)}</p>
        
        <div class="flex items-center justify-between text-xs font-mono text-gray-500 bg-gray-50 p-3 rounded-lg border border-gray-100">
          <span>ROLLBACK: ${esc(p.rollback_plan)}</span>
          <span class="font-bold">RISK: ${esc(p.risk_tier).toUpperCase()}</span>
        </div>

        ${r.status === 'pending_approval' ? `
          <div class="mt-5 flex space-x-3">
            <button onclick="window.appState.decide('${esc(r.run_id)}','approve')" class="flex-1 bg-brand-base hover:bg-blue-700 text-white text-xs font-bold py-2.5 px-4 rounded-full shadow transition-all">APPROVE EXECUTION</button>
            <button onclick="window.appState.decide('${esc(r.run_id)}','reject')" class="flex-1 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 text-xs font-bold py-2.5 px-4 rounded-full transition-all">REJECT</button>
          </div>
        ` : ''}
      </div>
    </div>
  ` : '';

  const errorsSection = s.errors?.length ? `
    <div class="mb-8 bg-red-50 border border-red-200 rounded-xl p-5">
      <h3 class="text-xs font-bold text-red-600 uppercase tracking-wider mb-2">Execution Error</h3>
      <div class="text-sm text-red-800 font-mono whitespace-pre-wrap">${s.errors.map(esc).join('<br>')}</div>
    </div>
  ` : '';

  const trailSection = events.length ? `
    <div>
      <h3 class="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-3">
        <div class="h-px bg-gray-200 flex-1"></div>
        Execution Trace
        <div class="h-px bg-gray-200 flex-1"></div>
      </h3>
      <div class="font-mono text-xs glass-panel overflow-hidden">
        ${events.map((e, idx) => `
          <div class="flex items-start p-4 ${idx !== events.length - 1 ? 'border-b border-gray-100' : ''} hover:bg-gray-50 transition-colors">
            <span class="text-gray-400 font-semibold w-20 shrink-0 pt-0.5">${esc(e.timestamp?.slice(11, 19))}</span>
            <div class="flex-1 min-w-0">
              <span class="text-brand-base font-bold block mb-1.5">${esc(e.event_type)}</span>
              <div class="text-gray-500 break-all bg-white border border-gray-100 p-2 rounded">${esc(JSON.stringify(e.details))}</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  ` : '';

  return `
    <div class="animate-fade-in max-w-4xl mx-auto pb-10">
      <div class="flex items-center justify-between mb-8">
        <div class="flex items-center space-x-3">
          <span class="px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full ${statusStyle}">
            ${esc(r.status)}
          </span>
          <span class="text-xs font-mono text-gray-400 bg-white border border-gray-200 px-2 py-0.5 rounded-full shadow-sm">${esc(r.run_id)}</span>
        </div>
      </div>
      
      ${errorsSection}
      ${verdictSection}
      ${proposalSection}
      ${trailSection}
    </div>
  `;
}
