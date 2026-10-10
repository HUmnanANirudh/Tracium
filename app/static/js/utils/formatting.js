export const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export const SEVERITY_STYLES = {
  critical: {
    dot: 'bg-red-500',
    text: 'text-red-700',
    badge: 'bg-red-50 text-red-700 border-red-200'
  },
  high: {
    dot: 'bg-orange-500',
    text: 'text-orange-700',
    badge: 'bg-orange-50 text-orange-700 border-orange-200'
  },
  medium: {
    dot: 'bg-amber-500',
    text: 'text-amber-800',
    badge: 'bg-amber-50 text-amber-800 border-amber-200'
  },
  low: {
    dot: 'bg-blue-500',
    text: 'text-blue-700',
    badge: 'bg-blue-50 text-blue-700 border-blue-200'
  }
};

export const VERDICT_BADGES = {
  true_positive: 'bg-red-50 text-red-700 border-red-200',
  false_positive: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  inconclusive: 'bg-amber-50 text-amber-800 border-amber-200'
};

export const STATUS_BADGES = {
  running: 'bg-blue-50 text-blue-700 border-blue-200',
  pending_approval: 'bg-amber-50 text-amber-800 border-amber-200',
  completed: 'bg-gray-100 text-gray-700 border-gray-200',
  failed: 'bg-red-50 text-red-700 border-red-200'
};
