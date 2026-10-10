import { esc, SEVERITY_COLORS } from '../utils/formatting.js';

export function createIncidentCard(i, isSelected) {
  const sevStyle = SEVERITY_COLORS[i.severity] || SEVERITY_COLORS.low;
  
  const baseClasses = 'cursor-pointer p-4 rounded-xl border transition-all duration-200 select-none bg-white';
  const stateClasses = isSelected 
    ? 'border-brand-base shadow-[0_0_0_1px_rgba(26,115,232,1)] bg-brand-glow/20' 
    : 'border-transparent hover:border-gray-300 hover:shadow-sm shadow-[0_1px_2px_rgba(0,0,0,0.05)]';

  return `
    <div onclick="window.appState.selectIncident('${esc(i.id)}')" class="${baseClasses} ${stateClasses}">
      <div class="flex justify-between items-start mb-2">
        <b class="text-sm font-semibold text-gray-900 tracking-tight">${esc(i.type).replace(/_/g, ' ')}</b>
        <span class="text-[10px] px-2 py-0.5 rounded-full border uppercase font-bold tracking-wider ${sevStyle}">
          ${esc(i.severity)}
        </span>
      </div>
      <div class="text-xs text-gray-600 mb-3 line-clamp-2 leading-relaxed">
        ${esc(i.message)}
      </div>
      <div class="flex justify-between items-center text-[10px] text-gray-400 font-mono">
        <span class="uppercase tracking-wider font-semibold text-gray-500">${esc(i.state)} · ${esc(i.event_count)} EVT</span>
        <span class="opacity-70" title="${esc(i.id)}">${esc(i.id).split('-')[0] + '-...'}</span>
      </div>
    </div>
  `;
}
