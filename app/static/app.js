const q = id => document.getElementById(id);

async function tick() {
  const [incRes, runRes] = await Promise.all([fetch('/incidents'), fetch('/agents/runs')]);
  if (!incRes.ok || !runRes.ok) return;
  
  const incs = await incRes.json();
  const runs = await runRes.json();
  
  q('inc-list').innerHTML = incs.map(i => 
    `<div class="p-3 mb-3 border-l-4 ${i.severity === 'high' ? 'border-red-500 bg-red-50' : 'border-gray-500 bg-gray-50'}">
      <b class="uppercase">${i.type}</b> <span class="text-xs text-gray-500">(${i.state})</span><br>
      <span class="text-sm">${i.message}</span>
    </div>`
  ).join('') || 'No incidents.';

  q('ai-list').innerHTML = runs.filter(r => r.status !== 'completed').map(r => 
    `<div class="p-3 mb-3 border bg-blue-50">
      <div class="font-bold text-sm mb-1">${r.run_id} <span class="text-blue-600 animate-pulse">${r.status}</span></div>
      <div class="text-sm italic mb-2">${r.state.approval_status || 'Gathering evidence...'}</div>
      ${r.status === 'pending_approval' ? 
        `<button onclick="approve('${r.run_id}')" class="bg-green-600 text-white px-3 py-1 text-sm rounded font-bold">Approve</button>` : ''}
    </div>`
  ).join('') || 'Idle.';
}

async function approve(id) {
  await fetch(`/agents/runs/${id}/approve`, {
    method: 'POST', 
    headers: {'Content-Type': 'application/json'}, 
    body: JSON.stringify({actor: 'human'})
  });
  tick();
}

setInterval(tick, 2000);
tick();
