import { getJSON, decide, triggerSimulation } from './api/api.js';
import { createIncidentCard } from './components/incidentCard.js';
import { createRunCard } from './components/runCard.js';

class AppState {
  constructor() {
    this.selectedIncidentId = null;
    this.lastHash = '';
    
    // Expose to window for inline onclick handlers
    window.appState = this;
    window.simulate = async (type, event) => {
      let btn = null;
      let origText = '';
      try {
        if (event && event.currentTarget) {
          btn = event.currentTarget;
          origText = btn.innerHTML;
          btn.innerHTML = '<span class="animate-pulse">WAIT...</span>';
          btn.disabled = true;
        }
        await triggerSimulation(type);
        if (btn) {
          setTimeout(() => {
            btn.innerHTML = origText;
            btn.disabled = false;
          }, 1500);
        }
        this.tick(true);
      } catch (e) {
        this.showError(`Simulation failed: ${e}`);
        if (btn) {
          btn.innerHTML = origText;
          btn.disabled = false;
        }
      }
    };
  }

  selectIncident(id) {
    this.selectedIncidentId = id;
    document.getElementById('selected-incident-id').textContent = id;
    this.tick(true);
  }

  async decide(id, action) {
    try {
      await decide(id, action);
      this.tick(true);
    } catch (e) {
      this.showError(`Decision failed: ${e}`);
    }
  }

  showError(msg) {
    const errEl = document.getElementById('err');
    errEl.textContent = msg;
    errEl.classList.remove('translate-y-full');
    errEl.classList.add('bg-red-600');
    setTimeout(() => {
      errEl.classList.add('translate-y-full');
    }, 5000);
  }

  async tick(force = false) {
    try {
      const [{incidents}, runs] = await Promise.all([
        getJSON('/incidents'), 
        getJSON('/agents/runs')
      ]);
      const events = await Promise.all(
        runs.map(r => getJSON(`/agents/runs/${r.run_id}/events`).then(d => d.events))
      );
      
      document.getElementById('stats').textContent = `${incidents.length} threats · ${runs.length} runs`;

      const hash = JSON.stringify([incidents, runs, events, this.selectedIncidentId]);
      if (hash === this.lastHash && !force) return;
      this.lastHash = hash;
      
      const incList = document.getElementById('inc-list');
      if (incidents.length === 0) {
        incList.innerHTML = `
          <div class="text-center py-12 px-4">
            <div class="w-8 h-8 mx-auto mb-3 text-gray-300 flex items-center justify-center rounded-full bg-gray-100">
              <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            </div>
            <p class="text-xs font-medium text-gray-700">No active threats</p>
            <p class="text-[11px] text-gray-400 mt-1">Simulate an attack above to start investigation.</p>
          </div>
        `;
      } else {
        incList.innerHTML = incidents.map(i => createIncidentCard(i, i.id === this.selectedIncidentId)).join('');
      }
      
      const aiList = document.getElementById('ai-list');
      if (this.selectedIncidentId) {
        const runIndex = runs.findIndex(r => r.incident_id === this.selectedIncidentId);
        if (runIndex !== -1) {
          aiList.innerHTML = createRunCard(runs[runIndex], events[runIndex]);
        } else {
          aiList.innerHTML = `
            <div class="absolute inset-0 flex items-center justify-center text-gray-500">
              <div class="flex items-center gap-3 bg-white px-5 py-3 rounded-lg border border-gray-200 shadow-xs">
                <div class="h-4 w-4 rounded-full border-2 border-blue-600 border-t-transparent animate-spin"></div>
                <span class="text-xs text-gray-600 font-medium">Initializing investigation...</span>
              </div>
            </div>
          `;
        }
      } else {
        aiList.innerHTML = `
          <div class="absolute inset-0 flex items-center justify-center text-gray-400">
            <p class="text-xs font-normal">Select an alert from the queue to view investigation details.</p>
          </div>
        `;
      }
    } catch (e) {
      this.showError(`API Sync Error: ${e}`);
    }
  }

  start() {
    this.tick();
    setInterval(() => this.tick(), 2000);
  }
}

const app = new AppState();
app.start();
