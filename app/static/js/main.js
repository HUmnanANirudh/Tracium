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
      
      document.getElementById('stats').textContent = `${incidents.length} THREATS · ${runs.length} RUNS`;

      const hash = JSON.stringify([incidents, runs, events, this.selectedIncidentId]);
      if (hash === this.lastHash && !force) return;
      this.lastHash = hash;
      
      const incList = document.getElementById('inc-list');
      if (incidents.length === 0) {
        incList.innerHTML = '<div class="text-xs font-mono text-gray-500 text-center mt-10 p-6 bg-white border border-dashed border-gray-300 rounded-xl">SYSTEM SECURE<br><br>Awaiting threats...</div>';
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
            <div class="absolute inset-0 flex items-center justify-center text-gray-500 font-mono text-sm">
              <div class="flex flex-col items-center gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                <div class="h-6 w-6 rounded-full border-2 border-brand-base border-t-transparent animate-spin"></div>
                <p class="tracking-widest uppercase text-xs font-bold text-gray-400">Initializing Context...</p>
              </div>
            </div>
          `;
        }
      } else {
        aiList.innerHTML = `
          <div class="absolute inset-0 flex items-center justify-center text-gray-500 font-mono text-sm">
            <p class="tracking-widest uppercase opacity-50">NO CONTEXT SELECTED</p>
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
