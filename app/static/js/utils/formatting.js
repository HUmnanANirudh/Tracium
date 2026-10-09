export const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export const SEVERITY_COLORS = {
  critical: 'text-status-critical border-status-critical/30 bg-status-critical/10',
  high: 'text-status-high border-status-high/30 bg-status-high/10',
  medium: 'text-status-medium border-status-medium/30 bg-status-medium/10',
  low: 'text-status-low border-status-low/30 bg-status-low/10'
};

export const VERDICT_COLORS = {
  true_positive: 'text-status-critical border-status-critical',
  false_positive: 'text-status-success border-status-success',
  inconclusive: 'text-status-medium border-status-medium'
};

export const STATUS_COLORS = {
  running: 'text-brand-base bg-brand-base/10 border-brand-base/30 animate-pulse',
  pending_approval: 'text-status-medium bg-status-medium/10 border-status-medium/30',
  completed: 'text-gray-300 bg-white/5 border-white/10',
  failed: 'text-status-critical bg-status-critical/10 border-status-critical/30'
};
