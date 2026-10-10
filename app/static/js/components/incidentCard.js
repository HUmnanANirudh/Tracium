import { esc, SEVERITY_STYLES } from '../utils/formatting.js';

export function createIncidentCard(i, isSelected) {
  const sev = SEVERITY_STYLES[i.severity] || SEVERITY_STYLES.low;
  const sevLabel = i.severity ? i.severity.charAt(0).toUpperCase() + i.severity.slice(1) : 'Low';
  const typeLabel = (i.type || 'Incident').replace(/_/g, ' ');
  
  const baseClasses = 'cursor-pointer p-4 rounded-lg border transition-all duration-150 select-none';
  const stateClasses = isSelected 
    ? 'border-blue-600 ring-1 ring-blue-600 bg-blue-50/20 shadow-sm' 
    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50/50 bg-white';

  return `
    <div onclick="window.appState.selectIncident('${esc(i.id)}')" class="${baseClasses} ${stateClasses}">
      <div class="flex items-center justify-between gap-2 mb-2">
        <h3 class="text-xs font-semibold text-gray-900 truncate tracking-tight capitalize">${esc(typeLabel)}</h3>
        <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border shrink-0 ${sev.badge}">
          <span class="w-1.5 h-1.5 rounded-full ${sev.dot}"></span>
          ${esc(sevLabel)}
        </span>
      </div>
      <p class="text-xs text-gray-600 mb-3 line-clamp-2 leading-relaxed">
        ${esc(i.message)}
      </p>
      <div class="flex items-center justify-between text-[11px] text-gray-400 font-mono pt-1">
        <span class="text-gray-500 font-medium">${esc(i.state)} · ${esc(i.event_count)} evt</span>
        <span class="text-gray-400 truncate max-w-[110px]" title="${esc(i.id)}">${esc(i.id)}</span>
      </div>
    </div>
  `;
}
