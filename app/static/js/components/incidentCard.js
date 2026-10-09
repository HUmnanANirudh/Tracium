import { esc, SEVERITY_COLORS } from '../utils/formatting.js';

export function createIncidentCard(i, isSelected) {
  const sevStyle = SEVERITY_COLORS[i.severity] || SEVERITY_COLORS.low;
  
  const baseClasses = 'cursor-pointer p-3 rounded border transition-all duration-200 select-none';
  const stateClasses = isSelected 
    ? 'bg-surface-100 border-brand-base/50 shadow-[0_0_15px_rgba(59,130,246,0.15)]' 
    : 'bg-transparent border-transparent hover:bg-white/5 hover:border-white/10';

  return `
    <div onclick="window.appState.selectIncident('${esc(i.id)}')" class="${baseClasses} ${stateClasses}">
      <div class="flex justify-between items-start mb-1.5">
        <b class="text-xs font-semibold text-gray-200 tracking-wide">${esc(i.type).replace(/_/g, ' ')}</b>
        <span class="text-[10px] px-1.5 py-0.5 rounded border uppercase font-bold tracking-wider ${sevStyle}">
          ${esc(i.severity)}
        </span>
      </div>
      <div class="text-xs text-gray-400 mb-2 line-clamp-2 leading-relaxed">
        ${esc(i.message)}
      </div>
      <div class="flex justify-between items-center text-[10px] text-gray-500 font-mono">
        <span class="uppercase tracking-wider">${esc(i.state)} · ${esc(i.event_count)} EVT</span>
        <span class="opacity-50" title="${esc(i.id)}">${esc(i.id).split('-')[0] + '-...'}</span>
      </div>
    </div>
  `;
}
