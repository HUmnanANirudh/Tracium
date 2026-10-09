import { esc, VERDICT_COLORS, STATUS_COLORS } from '../utils/formatting.js';

export function createRunCard(r, events) {
  const s = r.state || {}, v = s.verdict, p = s.response_proposal;
  
  const statusStyle = STATUS_COLORS[r.status] || STATUS_COLORS.completed;
  
  const verdictSection = v ? `
    <div class="mb-6">
      <h3 class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
        <div class="h-px bg-white/10 flex-1"></div>
        Verdict Analysis
        <div class="h-px bg-white/10 flex-1"></div>
      </h3>
      <div class="glass-panel rounded-lg p-4">
        <div class="flex justify-between items-start mb-3">
          <span class="text-xs px-2 py-1 border rounded font-mono font-bold uppercase ${VERDICT_COLORS[v.classification] || 'text-gray-400 border-gray-600'}">
            ${esc(v.classification).replace(/_/g, ' ')}
          </span>
          <span class="text-xs font-mono text-gray-500">CONFIDENCE: ${(v.confidence * 100).toFixed(0)}%</span>
        </div>
        <p class="text-sm text-gray-300 leading-relaxed">${esc(v.reasoning)}</p>
      </div>
    </div>
  ` : '';

  const proposalSection = p ? `
    <div class="mb-6">
      <h3 class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
        <div class="h-px bg-white/10 flex-1"></div>
        Proposed Response
        <div class="h-px bg-white/10 flex-1"></div>
      </h3>
      <div class="glass-panel border-brand-base/20 rounded-lg p-4 relative overflow-hidden">
        <div class="absolute top-0 left-0 w-1 h-full bg-brand-base/50"></div>
        <div class="flex items-center space-x-3 font-mono text-sm mb-3">
          <span class="text-brand-glow font-bold">${esc(p.action)}</span>
          <span class="text-gray-600">→</span>
          <span class="text-gray-300 bg-surface-100 px-2 py-0.5 rounded border border-white/5">${esc(p.target)}</span>
        </div>
        <p class="text-sm text-gray-400 mb-4">${esc(p.justification)}</p>
        
        <div class="flex items-center justify-between text-xs font-mono text-gray-500 bg-surface-100 p-2 rounded border border-white/5">
          <span>ROLLBACK: ${esc(p.rollback_plan)}</span>
          <span>RISK: ${esc(p.risk_tier).toUpperCase()}</span>
        </div>

        ${r.status === 'pending_approval' ? `
          <div class="mt-4 flex space-x-3">
            <button onclick="window.appState.decide('${esc(r.run_id)}','approve')" class="flex-1 bg-brand-base hover:bg-brand-glow text-white text-xs font-bold py-2 px-4 rounded shadow-[0_0_15px_rgba(59,130,246,0.3)] transition-all">APPROVE EXECUTION</button>
            <button onclick="window.appState.decide('${esc(r.run_id)}','reject')" class="flex-1 bg-surface-100 hover:bg-surface-200 text-gray-300 border border-white/10 text-xs font-bold py-2 px-4 rounded transition-all">REJECT</button>
          </div>
        ` : ''}
      </div>
    </div>
  ` : '';

  const errorsSection = s.errors?.length ? `
    <div class="mb-6 bg-status-critical/10 border border-status-critical/30 rounded-lg p-4">
      <h3 class="text-xs font-bold text-status-critical uppercase tracking-widest mb-2">Execution Error</h3>
      <div class="text-sm text-red-200 font-mono whitespace-pre-wrap">${s.errors.map(esc).join('<br>')}</div>
    </div>
  ` : '';

  const trailSection = events.length ? `
    <div>
      <h3 class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
        <div class="h-px bg-white/10 flex-1"></div>
        Execution Trace
        <div class="h-px bg-white/10 flex-1"></div>
      </h3>
      <div class="font-mono text-xs glass-panel rounded-lg border border-white/5 overflow-hidden">
        ${events.map((e, idx) => `
          <div class="flex items-start p-3 ${idx !== events.length - 1 ? 'border-b border-white/5' : ''} hover:bg-white/5 transition-colors">
            <span class="text-gray-500 w-20 shrink-0 pt-0.5">${esc(e.timestamp?.slice(11, 19))}</span>
            <div class="flex-1 min-w-0">
              <span class="text-brand-glow block mb-1">${esc(e.event_type)}</span>
              <div class="text-gray-400 break-all">${esc(JSON.stringify(e.details))}</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  ` : '';

  return `
    <div class="animate-fade-in max-w-4xl mx-auto">
      <div class="flex items-center justify-between mb-8">
        <div class="flex items-center space-x-3">
          <span class="px-2 py-1 text-[10px] font-bold uppercase tracking-widest border rounded ${statusStyle}">
            ${esc(r.status)}
          </span>
          <span class="text-sm font-mono text-gray-400">${esc(r.run_id)}</span>
        </div>
      </div>
      
      ${errorsSection}
      ${verdictSection}
      ${proposalSection}
      ${trailSection}
    </div>
  `;
}
