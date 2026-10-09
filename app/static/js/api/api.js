export const getJSON = url => fetch(url).then(r => r.ok ? r.json() : Promise.reject(`${url} -> ${r.status}`));

export async function decide(id, action) {
  const body = action === 'approve' ? {actor: 'analyst'} : {actor: 'analyst', reason: 'Rejected from copilot UI'};
  await fetch(`/agents/runs/${id}/${action}`, {
    method: 'POST', 
    headers: {'Content-Type': 'application/json'}, 
    body: JSON.stringify(body)
  });
}

export async function triggerSimulation(type) {
  await fetch(`/simulate/${type}`, { method: 'POST' });
}
