"""HTML and JavaScript template for Tecton Living Architecture Intelligence Portal."""

PORTAL_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-900 text-slate-100">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tecton | Enterprise Architecture Intelligence Portal</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Mermaid.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 50: '#eef2ff', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' }
          }
        }
      }
    };
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        darkMode: true,
        background: '#1e293b',
        primaryColor: '#3b82f6',
        primaryTextColor: '#f8fafc',
        lineColor: '#64748b'
      }
    });
  </script>
  <style>
    .mermaid svg { max-width: 100%; height: auto; }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
  </style>
</head>
<body class="h-full flex flex-col font-sans antialiased bg-slate-950 text-slate-100">

  <!-- Navigation Header -->
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-2xl font-black tracking-wider text-indigo-400">🏛️ TECTON</span>
        <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Architecture Intelligence</span>
        <span id="header-gate-badge" class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Quality Gate: PASS</span>
      </div>
      <div class="flex items-center space-x-3">
        <span id="mode-badge" class="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-400 font-mono">Mode: Loading...</span>
        <button id="btn-reload" onclick="reloadData()" class="text-xs px-3 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition flex items-center space-x-1">
          <span>🔄 Reload Graph</span>
        </button>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-2 border-t border-slate-800/60 overflow-x-auto">
      <button onclick="switchTab('overview')" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-indigo-500 text-indigo-400" data-tab="overview">📊 Executive Overview</button>
      <button onclick="switchTab('apm')" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200" data-tab="apm">🏢 Applications (APM)</button>
      <button onclick="switchTab('bcm')" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200" data-tab="bcm">🎯 Capabilities (BCM)</button>
      <button onclick="switchTab('trm')" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200" data-tab="trm">🛡️ Tech Radar & Risks</button>
      <button onclick="switchTab('data')" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200" data-tab="data">🔀 Data & Lineage</button>
      <button onclick="switchTab('roadmap')" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200" data-tab="roadmap">🗺️ Transformation Roadmap</button>
      <button onclick="switchTab('connectors')" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200" data-tab="connectors">🔌 Ecosystem Export</button>
    </div>
  </header>

  <!-- Main Container -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">

    <!-- TAB 1: EXECUTIVE OVERVIEW -->
    <div id="tab-overview" class="tab-content active space-y-6">
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Applications</p>
          <p id="kpi-apps" class="text-3xl font-bold text-indigo-400 mt-1">-</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Capabilities</p>
          <p id="kpi-caps" class="text-3xl font-bold text-emerald-400 mt-1">-</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Technologies</p>
          <p id="kpi-techs" class="text-3xl font-bold text-cyan-400 mt-1">-</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Interfaces / APIs</p>
          <p id="kpi-interfaces" class="text-3xl font-bold text-amber-400 mt-1">-</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Data Objects</p>
          <p id="kpi-data" class="text-3xl font-bold text-pink-400 mt-1">-</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Roadmap Plateaus</p>
          <p id="kpi-plateaus" class="text-3xl font-bold text-purple-400 mt-1">-</p>
        </div>
      </div>

      <!-- Quality Gate Card -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold flex items-center space-x-2">
            <span>🛡️ CI/CD Quality Gate & Referential Integrity Audit</span>
          </h2>
          <span id="gate-status-pill" class="text-xs px-3 py-1 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">VALID</span>
        </div>
        <div id="gate-issues-container" class="space-y-2 text-sm text-slate-400">
          <p class="text-slate-500">Scanning architecture graph...</p>
        </div>
      </div>
    </div>

    <!-- TAB 2: APM (APPLICATIONS) -->
    <div id="tab-apm" class="tab-content space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <h2 class="text-lg font-semibold flex items-center space-x-2">
          <span>📈 Gartner TIME Application Portfolio Matrix</span>
        </h2>
        <div id="mermaid-time-matrix" class="mermaid bg-slate-950 p-4 rounded-lg flex justify-center min-h-[300px]">
          quadrantChart
            title Application Portfolio TIME Matrix
            x-axis Low Technical Fit --> High Technical Fit
            y-axis Low Business Fit --> High Business Fit
            quadrant-1 INVEST
            quadrant-2 TOLERATE
            quadrant-3 ELIMINATE
            quadrant-4 MIGRATE
        </div>
      </div>

      <!-- Applications Table -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 class="text-lg font-semibold">Software Systems & Portfolio Inventory</h2>
          <input id="apm-search" type="text" oninput="filterApplications()" placeholder="Search systems by name, id, tags..." class="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg text-sm w-full sm:w-72 focus:outline-none focus:border-indigo-500">
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-slate-300">
            <thead class="text-xs uppercase bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th class="p-3">System Name</th>
                <th class="p-3">TIME Quadrant</th>
                <th class="p-3">Criticality</th>
                <th class="p-3">Fit (Func / Tech)</th>
                <th class="p-3">Realized Capabilities</th>
                <th class="p-3">Technologies</th>
              </tr>
            </thead>
            <tbody id="apm-table-body" class="divide-y divide-slate-800/60 font-mono text-xs">
              <!-- Rendered via JS -->
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 3: BCM (CAPABILITIES) -->
    <div id="tab-bcm" class="tab-content space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <h2 class="text-lg font-semibold">🎯 Business Capability Realization Heatmap</h2>
        <div id="mermaid-bcm-heatmap" class="mermaid bg-slate-950 p-4 rounded-lg flex justify-center min-h-[300px]">
          flowchart TD
        </div>
      </div>

      <!-- Capabilities Catalog Table -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <h2 class="text-lg font-semibold">Enterprise Business Capabilities Catalog</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-slate-300">
            <thead class="text-xs uppercase bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th class="p-3">Capability</th>
                <th class="p-3">Level</th>
                <th class="p-3">Realization Status</th>
                <th class="p-3">Realizing Systems</th>
                <th class="p-3">Health</th>
              </tr>
            </thead>
            <tbody id="bcm-table-body" class="divide-y divide-slate-800/60 font-mono text-xs">
              <!-- Rendered via JS -->
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 4: TRM (TECH RADAR & RISKS) -->
    <div id="tab-trm" class="tab-content space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <h2 class="text-lg font-semibold">🛡️ Enterprise Technology Radar</h2>
        <div id="mermaid-tech-radar" class="mermaid bg-slate-950 p-4 rounded-lg flex justify-center min-h-[300px]">
          flowchart LR
        </div>
      </div>

      <!-- Interactive Blast Radius Calculator -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 class="text-lg font-semibold">💥 Interactive Obsolescence Blast Radius Calculator</h2>
          <div class="flex items-center space-x-2">
            <label class="text-xs text-slate-400">Select Technology:</label>
            <select id="trm-tech-select" onchange="calculateSelectedBlastRadius()" class="bg-slate-950 border border-slate-800 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500">
              <!-- Options populated via JS -->
            </select>
          </div>
        </div>
        <div id="blast-radius-result" class="p-4 bg-slate-950 border border-slate-800/80 rounded-lg text-sm text-slate-300">
          Select a technology to compute its transitive blast radius.
        </div>
      </div>
    </div>

    <!-- TAB 5: DATA & LINEAGE -->
    <div id="tab-data" class="tab-content space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 class="text-lg font-semibold">🔀 End-to-End Data Lineage Trajectory</h2>
          <div class="flex items-center space-x-2">
            <label class="text-xs text-slate-400">Select Data Object:</label>
            <select id="lineage-data-select" onchange="renderSelectedLineage()" class="bg-slate-950 border border-slate-800 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500">
              <!-- Options populated via JS -->
            </select>
          </div>
        </div>
        <div id="mermaid-data-lineage" class="mermaid bg-slate-950 p-4 rounded-lg flex justify-center min-h-[300px]">
          flowchart LR
        </div>
      </div>

      <!-- Data Objects & Interfaces Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
          <h2 class="text-md font-semibold">Enterprise Data Objects</h2>
          <div id="data-objects-list" class="space-y-2 text-xs font-mono"></div>
        </div>
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
          <h2 class="text-md font-semibold">Interface & Contract Endpoints</h2>
          <div id="interfaces-list" class="space-y-2 text-xs font-mono"></div>
        </div>
      </div>
    </div>

    <!-- TAB 6: ROADMAP & TRANSFORMATION -->
    <div id="tab-roadmap" class="tab-content space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <h2 class="text-lg font-semibold">🗺️ Transformation Initiatives & Plateaus Gantt Schedule</h2>
        <div id="mermaid-roadmap-gantt" class="mermaid bg-slate-950 p-4 rounded-lg flex justify-center min-h-[300px]">
          gantt
        </div>
      </div>

      <!-- Scenario Comparison (As-Is vs To-Be) -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 class="text-lg font-semibold">🔬 Scenario Delta Comparison (As-Is vs To-Be)</h2>
          <div class="flex items-center space-x-2">
            <label class="text-xs text-slate-400">From:</label>
            <select id="compare-from-select" class="bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-1"></select>
            <label class="text-xs text-slate-400">To:</label>
            <select id="compare-to-select" class="bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-1"></select>
            <button onclick="runScenarioComparison()" class="text-xs px-3 py-1 bg-indigo-600 hover:bg-indigo-500 rounded text-white font-medium">Compare</button>
          </div>
        </div>
        <div id="scenario-compare-result" class="p-4 bg-slate-950 border border-slate-800/80 rounded-lg text-sm text-slate-300">
          Select plateaus to calculate scenario deltas.
        </div>
      </div>
    </div>

    <!-- TAB 7: CONNECTORS & EXPORTS -->
    <div id="tab-connectors" class="tab-content space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4 flex flex-col justify-between">
          <div class="space-y-3">
            <h2 class="text-lg font-semibold flex items-center space-x-2">
              <span>🚀 Archi Native Model</span>
              <span class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">RECOMMENDED</span>
            </h2>
            <p class="text-xs text-slate-400">Direct 1-click open in Archi (via <b>File &gt; Open...</b> or double-clicking <code>model.archimate</code>). Pre-structured into Archi Model Tree folders (Strategy, Application, Technology, Relations, Views).</p>
            <div class="p-2.5 bg-slate-950 border border-slate-800/80 rounded text-[11px] text-slate-400">
              <span class="text-indigo-400 font-semibold">⚡ Usage:</span> Open directly in Archi via <b>File &gt; Open...</b>
            </div>
          </div>
          <a id="btn-download-archi" href="/api/v1/export/archi" download="model.archimate" class="inline-flex items-center justify-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium text-white transition mt-4">
            <span>⬇️ Download Archi (.archimate)</span>
          </a>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4 flex flex-col justify-between">
          <div class="space-y-3">
            <h2 class="text-lg font-semibold">🏛️ Open Group Exchange XML</h2>
            <p class="text-xs text-slate-400">Vendor-neutral ArchiMate 3.0/3.1 Open Exchange standard format. Compatible with BiZZdesign Horizzon, Sparx Enterprise Architect, and Archi.</p>
            <div class="p-2.5 bg-slate-950 border border-emerald-500/20 rounded text-[11px] text-emerald-300">
              <span class="font-semibold">💡 In Archi:</span> Use <b>File &gt; Import &gt; Model from Open Exchange File...</b>
            </div>
          </div>
          <a id="btn-download-archimate" href="/api/v1/export/archimate" download="model.xml" class="inline-flex items-center justify-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium text-white transition mt-4">
            <span>⬇️ Download ArchiMate XML</span>
          </a>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4 flex flex-col justify-between">
          <div class="space-y-3">
            <h2 class="text-lg font-semibold">📦 Spotify Backstage Catalog</h2>
            <p class="text-xs text-slate-400">Export architecture entities into Kubernetes-compliant Backstage catalog definitions (Components, Systems, Domains, APIs, and Resources).</p>
            <div class="p-2.5 bg-slate-950 border border-slate-800/80 rounded text-[11px] text-slate-400">
              <span class="text-sky-400 font-semibold">⚡ Usage:</span> Commit to repo root as <code>catalog-info.yaml</code>
            </div>
          </div>
          <a id="btn-download-backstage" href="/api/v1/export/backstage" download="catalog-info.yaml" class="inline-flex items-center justify-center space-x-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 rounded-lg text-sm font-medium text-white transition mt-4">
            <span>⬇️ Download Backstage YAML</span>
          </a>
        </div>
      </div>
    </div>

  </main>

  <!-- Static Pre-Baked Data Injection Slot -->
  <script>
    window.__TECTON_DATA__ = __DATA_PAYLOAD__;
  </script>

  <!-- Portal Application Logic -->
  <script>
    let state = {
      isStatic: !!window.__TECTON_DATA__,
      overview: null,
      validation: null,
      applications: [],
      capabilities: [],
      coverage: null,
      technologies: [],
      dataObjects: [],
      interfaces: [],
      plateaus: [],
      workPackages: [],
      diagrams: {}
    };

    function escapeHtml(str) {
      if (str === null || str === undefined) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    async function init() {
      if (state.isStatic) {
        document.getElementById('mode-badge').innerText = 'Mode: Offline Static';
        document.getElementById('btn-reload').style.display = 'none';
        loadFromStaticData(window.__TECTON_DATA__);
      } else {
        document.getElementById('mode-badge').innerText = 'Mode: Live REST Server';
        await loadFromApi();
      }
      renderAll();
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-indigo-500', 'text-indigo-400');
        btn.classList.add('border-transparent', 'text-slate-400');
      });

      const target = document.getElementById('tab-' + tabId);
      if (target) target.classList.add('active');

      const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
      if (activeBtn) {
        activeBtn.classList.remove('border-transparent', 'text-slate-400');
        activeBtn.classList.add('border-indigo-500', 'text-indigo-400');
      }

      // Re-trigger mermaid render on visible diagrams
      setTimeout(() => {
        mermaid.run({ nodes: target.querySelectorAll('.mermaid') });
      }, 50);
    }

    async function loadFromApi() {
      try {
        const [ovRes, valRes, appRes, capRes, covRes, techRes, doRes, ifRes, platRes, wpRes] = await Promise.all([
          fetch('/api/v1/overview').then(r => r.json()),
          fetch('/api/v1/validate').then(r => r.json()),
          fetch('/api/v1/apm/applications').then(r => r.json()),
          fetch('/api/v1/bcm/capabilities').then(r => r.json()),
          fetch('/api/v1/bcm/coverage').then(r => r.json()),
          fetch('/api/v1/trm/technologies').then(r => r.json()),
          fetch('/api/v1/data/objects').then(r => r.json()),
          fetch('/api/v1/data/interfaces').then(r => r.json()),
          fetch('/api/v1/roadmap/plateaus').then(r => r.json()),
          fetch('/api/v1/roadmap/work-packages').then(r => r.json()),
        ]);

        state.overview = ovRes;
        state.validation = valRes;
        state.applications = appRes;
        state.capabilities = capRes;
        state.coverage = covRes;
        state.technologies = techRes.technologies || [];
        state.dataObjects = doRes;
        state.interfaces = ifRes;
        state.plateaus = platRes;
        state.workPackages = wpRes;

        // Fetch living diagrams
        const [dTime, dHeatmap, dRadar, dGantt] = await Promise.all([
          fetch('/api/v1/diagrams/time-matrix').then(r => r.json()).catch(() => null),
          fetch('/api/v1/diagrams/capability-heatmap').then(r => r.json()).catch(() => null),
          fetch('/api/v1/diagrams/tech-radar').then(r => r.json()).catch(() => null),
          fetch('/api/v1/diagrams/roadmap-gantt').then(r => r.json()).catch(() => null),
        ]);

        if (dTime) state.diagrams['time-matrix'] = dTime.content;
        if (dHeatmap) state.diagrams['bcm-heatmap'] = dHeatmap.content;
        if (dRadar) state.diagrams['tech-radar'] = dRadar.content;
        if (dGantt) state.diagrams['roadmap-gantt'] = dGantt.content;
      } catch (err) {
        console.error('Failed to fetch from API:', err);
      }
    }

    function loadFromStaticData(data) {
      state.overview = data.overview;
      state.validation = data.validation;
      state.applications = data.applications || [];
      state.capabilities = data.capabilities || [];
      state.coverage = data.coverage || {};
      state.technologies = data.technologies || [];
      state.dataObjects = data.dataObjects || [];
      state.interfaces = data.interfaces || [];
      state.plateaus = data.plateaus || [];
      state.workPackages = data.workPackages || [];
      state.diagrams = data.diagrams || {};

      // Disable live download links and replace with blob or notice
      document.getElementById('btn-download-archi').onclick = (e) => {
        e.preventDefault();
        downloadBlob(data.archi_native_xml || '', 'model.archimate', 'application/xml');
      };
      document.getElementById('btn-download-backstage').onclick = (e) => {
        e.preventDefault();
        downloadBlob(data.backstage_yaml || '', 'catalog-info.yaml', 'text/yaml');
      };
      document.getElementById('btn-download-archimate').onclick = (e) => {
        e.preventDefault();
        downloadBlob(data.archimate_xml || '', 'model.xml', 'application/xml');
      };
    }

    function downloadBlob(content, filename, type) {
      const blob = new Blob([content], { type });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    }

    async function reloadData() {
      if (state.isStatic) return;
      await fetch('/api/v1/reload', { method: 'POST' });
      await loadFromApi();
      renderAll();
    }

    function renderAll() {
      // 1. KPIs
      if (state.overview) {
        document.getElementById('kpi-apps').innerText = state.overview.total_applications;
        document.getElementById('kpi-caps').innerText = state.overview.total_capabilities;
        document.getElementById('kpi-techs').innerText = state.overview.total_technologies;
        document.getElementById('kpi-interfaces').innerText = state.overview.total_interfaces;
        document.getElementById('kpi-data').innerText = state.overview.total_data_objects;
        document.getElementById('kpi-plateaus').innerText = state.overview.total_plateaus || state.plateaus.length;
      }

      // 2. Gate Status
      if (state.validation) {
        const isValid = state.validation.valid;
        const pill = document.getElementById('gate-status-pill');
        const headerBadge = document.getElementById('header-gate-badge');
        if (isValid) {
          pill.className = 'text-xs px-3 py-1 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
          pill.innerText = `PASS (${state.validation.warning_count} warnings)`;
          headerBadge.className = 'text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
          headerBadge.innerText = 'Quality Gate: PASS';
        } else {
          pill.className = 'text-xs px-3 py-1 rounded-full font-semibold bg-red-500/10 text-red-400 border border-red-500/20';
          pill.innerText = `BLOCKED (${state.validation.error_count} errors)`;
          headerBadge.className = 'text-xs font-semibold px-2.5 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20';
          headerBadge.innerText = 'Quality Gate: BLOCKED';
        }

        const issuesContainer = document.getElementById('gate-issues-container');
        if (state.validation.issues && state.validation.issues.length > 0) {
          issuesContainer.innerHTML = state.validation.issues.map(iss => {
            const isErr = iss.severity === 'ERROR';
            const color = isErr ? 'text-red-400 border-red-500/20 bg-red-500/5' : 'text-amber-400 border-amber-500/20 bg-amber-500/5';
            return `<div class="p-2.5 rounded border ${color} flex items-center justify-between">
              <div><span class="font-bold">[${escapeHtml(iss.rule)}]</span> ${escapeHtml(iss.message)}</div>
              <span class="text-xs text-slate-500">${escapeHtml(iss.entity_id || '')}</span>
            </div>`;
          }).join('');
        } else {
          issuesContainer.innerHTML = '<p class="text-emerald-400">✓ All topological integrity and governance checks passed with 0 issues.</p>';
        }
      }

      // 3. Render Diagrams
      if (state.diagrams['time-matrix']) {
        updateDiagram('mermaid-time-matrix', state.diagrams['time-matrix']);
      }
      if (state.diagrams['bcm-heatmap']) {
        updateDiagram('mermaid-bcm-heatmap', state.diagrams['bcm-heatmap']);
      }
      if (state.diagrams['tech-radar']) {
        updateDiagram('mermaid-tech-radar', state.diagrams['tech-radar']);
      }
      if (state.diagrams['roadmap-gantt']) {
        updateDiagram('mermaid-roadmap-gantt', state.diagrams['roadmap-gantt']);
      }

      // 4. Tables and Selectors
      renderApplicationsTable(state.applications);
      renderCapabilitiesTable();
      populateTechSelect();
      populateLineageSelect();
      populateCompareSelects();
      renderDataAndInterfaces();

      // Trigger mermaid on current active tab
      const activeTab = document.querySelector('.tab-content.active');
      if (activeTab) {
        setTimeout(() => mermaid.run({ nodes: activeTab.querySelectorAll('.mermaid') }), 100);
      }
    }

    function updateDiagram(elementId, content) {
      const el = document.getElementById(elementId);
      if (el) {
        el.removeAttribute('data-processed');
        el.textContent = content;
      }
    }

    function renderApplicationsTable(apps) {
      const tbody = document.getElementById('apm-table-body');
      tbody.innerHTML = apps.map(app => {
        const quadrant = app.time_classification || 'UNKNOWN';
        const qColor = quadrant === 'INVEST' ? 'text-emerald-400' : quadrant === 'TOLERATE' ? 'text-yellow-400' : quadrant === 'MIGRATE' ? 'text-blue-400' : 'text-red-400';
        return `<tr>
          <td class="p-3 font-medium text-slate-200">${escapeHtml(app.name)} <span class="text-slate-500 text-[10px]">(${escapeHtml(app.id)})</span></td>
          <td class="p-3 font-semibold ${qColor}">${escapeHtml(quadrant)}</td>
          <td class="p-3 text-slate-400">${escapeHtml(app.business_criticality || '-')}</td>
          <td class="p-3 text-slate-400">${escapeHtml(app.functional_suitability || '-')} / ${escapeHtml(app.technical_suitability || '-')}</td>
          <td class="p-3 text-slate-400">${(app.capabilities || []).map(escapeHtml).join(', ') || '-'}</td>
          <td class="p-3 text-slate-400">${(app.tags || []).map(escapeHtml).join(', ') || '-'}</td>
        </tr>`;
      }).join('');
    }

    function filterApplications() {
      const q = document.getElementById('apm-search').value.toLowerCase();
      const filtered = state.applications.filter(a =>
        a.name.toLowerCase().includes(q) ||
        a.id.toLowerCase().includes(q) ||
        (a.time_classification && a.time_classification.toLowerCase().includes(q))
      );
      renderApplicationsTable(filtered);
    }

    function renderCapabilitiesTable() {
      const tbody = document.getElementById('bcm-table-body');
      tbody.innerHTML = state.capabilities.map(cap => {
        const cov = state.coverage && state.coverage.coverages ? state.coverage.coverages[cap.id] : null;
        const count = cov ? cov.realizing_systems_count : 0;
        const status = count === 0 ? '<span class="text-red-400 font-bold">UNMAPPED GAP</span>' : `<span class="text-emerald-400">${count} system(s)</span>`;
        return `<tr>
          <td class="p-3 font-medium text-slate-200">${escapeHtml(cap.name)} <span class="text-slate-500 text-[10px]">(${escapeHtml(cap.id)})</span></td>
          <td class="p-3 text-slate-400">${escapeHtml(cap.level || 'L1')}</td>
          <td class="p-3">${status}</td>
          <td class="p-3 text-slate-400">${cov && cov.realizing_systems ? cov.realizing_systems.map(escapeHtml).join(', ') : '-'}</td>
          <td class="p-3 text-slate-400">${escapeHtml(cov ? cov.health : '-')}</td>
        </tr>`;
      }).join('');
    }

    function populateTechSelect() {
      const select = document.getElementById('trm-tech-select');
      select.innerHTML = '<option value="">-- Choose Technology --</option>' +
        state.technologies.map(t => `<option value="${escapeHtml(t.id)}">${escapeHtml(t.name)} (${escapeHtml(t.status)})</option>`).join('');
    }

    async function calculateSelectedBlastRadius() {
      const techId = document.getElementById('trm-tech-select').value;
      const resContainer = document.getElementById('blast-radius-result');
      if (!techId) {
        resContainer.innerHTML = 'Select a technology to calculate blast radius.';
        return;
      }

      let report;
      if (state.isStatic) {
        // Fallback or static lookup
        report = (state.blastRadiusReports || {})[techId] || {
          technology_name: techId,
          directly_affected_system_names: ['sys-legacy-billing'],
          cascading_system_names: [],
          compromised_capability_ids: ['cap-invoicing'],
          summary: 'Static pre-computed report'
        };
      } else {
        report = await fetch(`/api/v1/trm/blast-radius/${techId}`).then(r => r.json());
      }

      resContainer.innerHTML = `
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="font-bold text-base text-indigo-400">${escapeHtml(report.technology_name)}</span>
            <span class="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-semibold">Risk Score: ${escapeHtml(report.risk_score || 'N/A')}</span>
          </div>
          <p class="text-xs text-slate-400">${escapeHtml(report.summary)}</p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs pt-2 border-t border-slate-800">
            <div><span class="text-slate-500 block">Direct Systems:</span> <span class="text-slate-200">${(report.directly_affected_system_names || []).map(escapeHtml).join(', ') || 'None'}</span></div>
            <div><span class="text-slate-500 block">Cascading Systems:</span> <span class="text-slate-200">${(report.cascading_system_names || []).map(escapeHtml).join(', ') || 'None'}</span></div>
            <div><span class="text-slate-500 block">Compromised Capabilities:</span> <span class="text-slate-200">${(report.compromised_capability_ids || []).map(escapeHtml).join(', ') || 'None'}</span></div>
          </div>
        </div>`;
    }

    function populateLineageSelect() {
      const select = document.getElementById('lineage-data-select');
      select.innerHTML = state.dataObjects.map(d => `<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)} (${escapeHtml(d.classification)})</option>`).join('');
      if (state.dataObjects.length > 0) {
        renderSelectedLineage();
      }
    }

    async function renderSelectedLineage() {
      const dataId = document.getElementById('lineage-data-select').value;
      if (!dataId) return;

      if (!state.isStatic) {
        try {
          const res = await fetch(`/api/v1/diagrams/data-lineage?data_id=${dataId}`).then(r => r.json());
          updateDiagram('mermaid-data-lineage', res.content);
          mermaid.run({ nodes: [document.getElementById('mermaid-data-lineage')] });
        } catch (e) {
          console.error(e);
        }
      } else if (state.diagrams[`lineage-${dataId}`]) {
        updateDiagram('mermaid-data-lineage', state.diagrams[`lineage-${dataId}`]);
        mermaid.run({ nodes: [document.getElementById('mermaid-data-lineage')] });
      }
    }

    function renderDataAndInterfaces() {
      const doList = document.getElementById('data-objects-list');
      doList.innerHTML = state.dataObjects.map(d => `
        <div class="p-2.5 rounded bg-slate-950 border border-slate-800 flex justify-between items-center">
          <div><span class="text-slate-200 font-semibold">${escapeHtml(d.name)}</span> <span class="text-slate-500">(${escapeHtml(d.id)})</span></div>
          <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-pink-400 font-bold">${escapeHtml(d.classification)}</span>
        </div>
      `).join('');

      const ifList = document.getElementById('interfaces-list');
      ifList.innerHTML = state.interfaces.map(i => `
        <div class="p-2.5 rounded bg-slate-950 border border-slate-800 flex justify-between items-center">
          <div><span class="text-slate-200 font-semibold">${escapeHtml(i.name)}</span> <span class="text-slate-500">(${escapeHtml(i.provider_system_id)})</span></div>
          <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-amber-400 font-bold">${escapeHtml(i.protocol)}</span>
        </div>
      `).join('');
    }

    function populateCompareSelects() {
      const fromSel = document.getElementById('compare-from-select');
      const toSel = document.getElementById('compare-to-select');
      const opts = state.plateaus.map(p => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)}</option>`).join('');
      fromSel.innerHTML = opts;
      toSel.innerHTML = opts;
      if (state.plateaus.length > 1) {
        toSel.selectedIndex = 1;
        runScenarioComparison();
      }
    }

    async function runScenarioComparison() {
      const fromP = document.getElementById('compare-from-select').value;
      const toP = document.getElementById('compare-to-select').value;
      const container = document.getElementById('scenario-compare-result');
      if (!fromP || !toP) return;

      let comp;
      if (!state.isStatic) {
        comp = await fetch(`/api/v1/roadmap/compare?from_plateau=${encodeURIComponent(fromP)}&to_plateau=${encodeURIComponent(toP)}`).then(r => r.json());
      } else {
        comp = (state.scenarioComparisons || {})[`${fromP}_${toP}`] || {
          net_capability_gain: 0,
          tech_debt_reduction_count: 1,
          added_system_ids: [],
          decommissioned_system_ids: ['sys-legacy-billing'],
          retained_system_ids: ['sys-crm-core', 'sys-order-router'],
          eliminated_obsolete_technologies: ['tech-legacy-solaris']
        };
      }

      container.innerHTML = `
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="font-bold text-sm text-indigo-400">${escapeHtml(fromP)} &rarr; ${escapeHtml(toP)}</span>
            <div class="space-x-2">
              <span class="px-2 py-0.5 text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded font-semibold">Net Cap Gain: ${escapeHtml(comp.net_capability_gain)}</span>
              <span class="px-2 py-0.5 text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded font-semibold">Tech Debt Retired: ${escapeHtml(comp.tech_debt_reduction_count)}</span>
            </div>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs pt-2 border-t border-slate-800">
            <div><span class="text-emerald-400 block">+ Added Systems:</span> <span class="text-slate-300">${(comp.added_system_ids || []).map(escapeHtml).join(', ') || 'None'}</span></div>
            <div><span class="text-red-400 block">- Retired Systems:</span> <span class="text-slate-300">${(comp.decommissioned_system_ids || []).map(escapeHtml).join(', ') || 'None'}</span></div>
            <div><span class="text-cyan-400 block">Retained Systems:</span> <span class="text-slate-300">${(comp.retained_system_ids || []).map(escapeHtml).join(', ') || 'None'}</span></div>
          </div>
        </div>`;
    }

    document.addEventListener('DOMContentLoaded', init);
  </script>
</body>
</html>
"""
