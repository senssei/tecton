"""HTML and JavaScript template for Tecton Living Architecture Intelligence Portal."""

PORTAL_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-900 text-slate-100">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tecton | Enterprise Architecture Intelligence Portal</title>
  <style>__RADAR_STYLE__</style>
  <script>__RADAR_SCRIPT__</script>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Mermaid.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    if (typeof tailwind !== 'undefined') {
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
    }
    if (typeof mermaid !== 'undefined' && mermaid && mermaid.initialize) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        gantt: {
          useMaxWidth: false,
          useWidth: 1120,
          leftPadding: 360,
          rightPadding: 100,
          topPadding: 64,
          barHeight: 30,
          barGap: 16,
          fontSize: 16,
          sectionFontSize: 16,
          tickInterval: '3month'
        },
        quadrantChart: {
          chartWidth: 960,
          chartHeight: 640,
          titleFontSize: 24,
          titlePadding: 20,
          quadrantLabelFontSize: 20,
          quadrantTextTopPadding: 14,
          xAxisLabelFontSize: 18,
          yAxisLabelFontSize: 18,
          pointLabelFontSize: 16,
          pointRadius: 7,
          pointTextPadding: 10
        },
        themeVariables: {
          darkMode: true,
          background: '#1e293b',
          primaryColor: '#3b82f6',
          primaryTextColor: '#f8fafc',
          lineColor: '#64748b',
          fontSize: '17px',
          quadrant1Fill: '#064e3b',
          quadrant2Fill: '#422006',
          quadrant3Fill: '#4c0519',
          quadrant4Fill: '#172554',
          quadrant1TextFill: '#a7f3d0',
          quadrant2TextFill: '#fde68a',
          quadrant3TextFill: '#fecdd3',
          quadrant4TextFill: '#bfdbfe',
          quadrantPointFill: '#ffffff',
          quadrantPointTextFill: '#f8fafc',
          quadrantInternalBorderStrokeFill: '#64748b',
          quadrantExternalBorderStrokeFill: '#94a3b8'
        }
      });
    }
    function safeRenderMermaid(container) {
      if (!container) return;
      // Only render visible diagrams: hidden tabs have no measurable width.
      const nodes = Array.from(container.matches && container.matches('.mermaid')
        ? [container] : container.querySelectorAll('.mermaid'))
        .filter(el => el.getClientRects().length > 0);
      if (typeof mermaid !== 'undefined' && mermaid && mermaid.run) {
        try {
          if (nodes && nodes.length > 0) {
            mermaid.run({ nodes: nodes }).catch(e => console.warn('Mermaid render notice:', e));
          }
        } catch (e) {
          console.warn("Mermaid render notice:", e);
        }
      } else {
        nodes.forEach(el => {
          if (!el.classList.contains('offline-rendered')) {
            el.classList.add('offline-rendered');
            el.style.fontFamily = 'ui-monospace, SFMono-Regular, Menlo, monospace';
            el.style.whiteSpace = 'pre-wrap';
            el.style.fontSize = '12px';
            el.style.color = '#94a3b8';
            el.style.overflowX = 'auto';
            el.style.padding = '12px';
          }
        });
      }
    }
  </script>
  <style>
    /* Standalone Offline CSS Fallback for Air-Gapped Environments */
    :root { color-scheme: dark; }
    body { margin: 0; background-color: #020617; color: #f8fafc; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .mermaid svg { max-width: 100%; height: auto; }
    .readable-chart { display: block; overflow-x: auto; padding: 24px; }
    #mermaid-time-matrix svg { width: 960px; min-width: 960px; max-width: none; height: auto; margin: 0 auto; display: block; }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .offline-rendered { border: 1px dashed #334155; border-radius: 8px; background: #090d16; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 10px 12px; }
    .inventory-table { min-width: 1280px; font-size: 14px; line-height: 1.6; }
    .inventory-table th, .inventory-table td { vertical-align: top; padding: 16px; }
    .inventory-table td:first-child { min-width: 320px; max-width: 380px; }
    .inventory-table td:nth-child(7), .inventory-table td:nth-child(8) { min-width: 180px; }
    .inventory-name { font-size: 16px; font-weight: 600; }
    .inventory-id { display: block; font-size: 12px; color: #94a3b8; overflow-wrap: anywhere; }
    .inventory-description { margin: 8px 0 12px; color: #cbd5e1; font-weight: 400; }
    .inventory-table details { margin-top: 8px; }
    .inventory-table summary { cursor: pointer; color: #a5b4fc; }
    .inventory-components { list-style: none; padding: 0; max-height: 360px; overflow-y: auto; }
    .inventory-components li { padding: 10px 0; border-bottom: 1px solid #334155; }
    .inventory-items { list-style: none; margin: 0; padding: 0; }
    .inventory-items li { margin-bottom: 6px; overflow-wrap: anywhere; }
    .empty-state { min-height: 0 !important; padding: 28px !important; color: #cbd5e1; font: 15px/1.7 ui-sans-serif, system-ui, sans-serif !important; }
    .empty-state strong { display: block; color: #f8fafc; font-size: 17px; margin-bottom: 6px; }
    .overview-card { text-align: left; cursor: pointer; font-family: inherit; }
    .overview-card:hover { border-color: #818cf8; background: #172036; }
    .overview-card:focus-visible { outline: 2px solid #a5b4fc; outline-offset: 3px; }
    .overview-card-description { color: #cbd5e1; font-size: 13px; line-height: 1.5; margin-top: 8px; }
    .issue-card { padding: 20px; border: 1px solid; border-radius: 10px; font-size: 15px; line-height: 1.6; }
    .issue-card h3 { color: #f8fafc; font-size: 17px; margin: 8px 0; }
    .issue-card p { color: #cbd5e1; margin: 8px 0; }
    .issue-card summary { cursor: pointer; font-size: 13px; color: #cbd5e1; margin-top: 12px; }
    .issue-card code { overflow-wrap: anywhere; }
    .capability-heatmap { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
    .capability-tile { border: 1px solid; border-radius: 10px; padding: 20px; font-size: 14px; line-height: 1.6; }
    .capability-tile h3 { margin: 0 0 12px; font-size: 16px; color: #fff; }
    .capability-tile p { margin: 6px 0 0; }
    .heat-healthy { background: #064e3b; border-color: #34d399; color: #d1fae5; }
    .heat-tolerable { background: #713f12; border-color: #facc15; color: #fef3c7; }
    .heat-at-risk { background: #7f1d1d; border-color: #f87171; color: #fee2e2; }
    .heat-unmapped { background: #1e293b; border-color: #94a3b8; color: #e2e8f0; }
    .heat-unknown { background: #312e81; border-color: #a5b4fc; color: #e0e7ff; }
    .chart-legend { display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0; font-size: 14px; }
    .chart-legend span { border-radius: 6px; padding: 6px 12px; border: 1px solid; }
    .technology-radar { display: grid; grid-template-columns: minmax(0, 2fr) minmax(240px, 1fr); gap: 24px; align-items: start; }
    .technology-radar svg { width: 100%; height: auto; display: block; }
    .radar-key { list-style: none; margin: 0; padding: 0; font-size: 14px; line-height: 1.6; }
    .radar-key li { padding: 12px 0; border-bottom: 1px solid #334155; }
    .radar-key small { display: block; color: #cbd5e1; }
    @media (max-width: 800px) { .technology-radar { grid-template-columns: 1fr; } }
    button:disabled, select:disabled { opacity: .5; cursor: not-allowed; }
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
      <div><h1 class="text-2xl font-semibold">Architecture at a glance</h1><p class="text-sm text-slate-300 mt-2">What is in this catalog, and which architecture issues need attention.</p></div>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <button type="button" onclick="switchTab('apm')" class="overview-card bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Software systems</p>
          <p id="kpi-apps" class="text-3xl font-bold text-indigo-400 mt-1">-</p>
          <p class="overview-card-description">Products and services</p>
        </button>
        <button type="button" onclick="switchTab('bcm')" class="overview-card bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Business capabilities</p>
          <p id="kpi-caps" class="text-3xl font-bold text-emerald-400 mt-1">-</p>
          <p class="overview-card-description">What the business can do</p>
        </button>
        <button type="button" onclick="switchTab('trm')" class="overview-card bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Technologies</p>
          <p id="kpi-techs" class="text-3xl font-bold text-cyan-400 mt-1">-</p>
          <p class="overview-card-description">Platforms, tools and libraries</p>
        </button>
        <button type="button" onclick="switchTab('data')" class="overview-card bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Interfaces & APIs</p>
          <p id="kpi-interfaces" class="text-3xl font-bold text-amber-400 mt-1">-</p>
          <p class="overview-card-description">Connections between systems</p>
        </button>
        <button type="button" onclick="switchTab('data')" class="overview-card bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Data objects</p>
          <p id="kpi-data" class="text-3xl font-bold text-pink-400 mt-1">-</p>
          <p class="overview-card-description">Information used or exchanged</p>
        </button>
        <button type="button" onclick="switchTab('roadmap')" class="overview-card bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-wider">Architecture milestones</p>
          <p id="kpi-plateaus" class="text-3xl font-bold text-purple-400 mt-1">-</p>
          <p class="overview-card-description">Planned architecture states</p>
        </button>
      </div>

      <!-- Quality Gate Card -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold flex items-center space-x-2">
            <span>🛡️ Architecture health & issues</span>
          </h2>
          <span id="gate-status-pill" class="text-xs px-3 py-1 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">VALID</span>
        </div>
        <p id="gate-summary" class="text-sm text-slate-300"></p>
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
        <div id="mermaid-time-matrix" class="mermaid readable-chart bg-slate-950 rounded-lg">
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
          <table class="inventory-table w-full text-left text-sm text-slate-300">
            <thead class="text-xs uppercase bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th class="p-3">System Name</th>
                <th class="p-3">Owner</th>
                <th class="p-3">Lifecycle</th>
                <th class="p-3">TIME Quadrant</th>
                <th class="p-3">Criticality</th>
                <th class="p-3">Fit (Func / Tech)</th>
                <th class="p-3">Realized Capabilities</th>
                <th class="p-3">Technologies</th>
              </tr>
            </thead>
            <tbody id="apm-table-body" class="divide-y divide-slate-800/60">
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
        <p class="text-sm text-slate-300">Capabilities are grouped by business area. Color shows direct system health; parent areas do not inherit coverage from their children.</p>
        <div class="chart-legend" aria-label="Capability health legend"><span class="heat-healthy">Healthy</span><span class="heat-tolerable">Tolerable</span><span class="heat-at-risk">At risk</span><span class="heat-unmapped">Unmapped</span><span class="heat-unknown">Unknown</span></div>
        <div id="capability-heatmap" class="capability-heatmap"></div>
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
        <p class="text-sm text-slate-300">Sectors group technology categories. Rings show approval status, from approved at the center to prohibited at the edge.</p>
        <div id="technology-radar" class="technology-radar"></div>
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
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 class="text-lg font-semibold">Data flow diagrams</h2>
        <div id="dfd-view" class="dfd-view"></div>
      </div>
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 class="text-lg font-semibold">🔀 System-level lineage</h2>
          <div class="flex items-center space-x-2">
            <label class="text-xs text-slate-400">Select Data Object:</label>
            <select id="lineage-data-select" onchange="renderSelectedLineage()" class="bg-slate-950 border border-slate-800 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500">
              <!-- Options populated via JS -->
            </select>
          </div>
        </div>
        <p id="lineage-summary" class="text-sm text-slate-300">Choose a data object to see the systems that send and receive it.</p>
        <div id="mermaid-data-lineage" class="lineage-transfers"></div>
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
        <h2 class="text-lg font-semibold">🗺️ Transformation schedule</h2>
        <div id="roadmap-schedule"></div>
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
            <button id="compare-button" onclick="runScenarioComparison()" class="text-xs px-3 py-1 bg-indigo-600 hover:bg-indigo-500 rounded text-white font-medium">Compare</button>
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

  <dialog id="components-dialog" class="components-dialog" aria-labelledby="components-title"><header><h2 id="components-title"></h2><button type="button" onclick="this.closest('dialog').close()">Close</button></header><div class="component-cards"></div></dialog>
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
        safeRenderMermaid(target);
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
        state.dataFlowDiagrams = await fetch('/api/v1/data/flow-diagrams').then(r => {if (!r.ok) throw Error('DFD unavailable'); return r.json();});
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
      state.dataFlowDiagrams = data.dataFlowDiagrams || [];
      state.diagrams = data.diagrams || {};
      state.blastRadiusReports = data.blastRadiusReports || {};
      state.scenarioComparisons = data.scenarioComparisons || {};
      state.lineageReports = data.lineageReports || {};

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
        const warnings = state.validation.warning_count || 0;
        document.getElementById('gate-summary').textContent = isValid
          ? (warnings ? `No blocking errors. ${warnings} warning${warnings === 1 ? '' : 's'} need review. The catalog passes validation, but these risks remain.` : 'No blocking errors or warnings. The catalog passes validation.')
          : `${state.validation.error_count} blocking error${state.validation.error_count === 1 ? '' : 's'} must be resolved before the catalog passes validation.`;
        const pill = document.getElementById('gate-status-pill');
        const headerBadge = document.getElementById('header-gate-badge');
        if (isValid) {
          pill.className = 'text-xs px-3 py-1 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
          pill.innerText = warnings ? 'Needs review' : 'Checks passed';
          if (warnings) pill.className = 'text-sm px-3 py-1 rounded-full font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20';
          headerBadge.className = 'text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
          headerBadge.innerText = warnings ? `Valid catalog · ${warnings} warnings` : 'Valid catalog';
          if (warnings) headerBadge.className = 'text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20';
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
            const titles = {
              TECHNOLOGY_EOL_EXPIRED: 'Technology has reached end of life',
              GOVERNANCE_DEPRECATED_TECH_USAGE: 'A system uses deprecated technology',
              GOVERNANCE_PROHIBITED_TECH_USAGE: 'A system uses prohibited technology',
              MISSING_SYSTEM_OWNER: 'A system has no accountable owner'
            };
            const actions = {
              TECHNOLOGY_EOL_EXPIRED: 'Review an upgrade or replacement plan and confirm who owns the migration.',
              GOVERNANCE_DEPRECATED_TECH_USAGE: 'Review the affected system and plan migration to an approved technology.',
              GOVERNANCE_PROHIBITED_TECH_USAGE: 'Replace the prohibited technology or resolve the architecture policy violation.',
              MISSING_SYSTEM_OWNER: 'Assign a team or person responsible for this system.'
            };
            const entity = [...state.applications, ...state.technologies, ...state.capabilities].find(item => item.id === iss.entity_id);
            const title = titles[iss.rule] || iss.rule.toLowerCase().replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
            return `<article class="issue-card ${color}">
              <strong>${isErr ? 'Blocking error' : 'Warning'}</strong>
              <h3>${escapeHtml(title)}</h3>
              ${entity ? `<p><strong>Affected:</strong> ${escapeHtml(entity.name)}</p>` : ''}
              <p>${escapeHtml(iss.message)}</p>
              ${actions[iss.rule] ? `<p><strong>Next step:</strong> ${escapeHtml(actions[iss.rule])}</p>` : ''}
              <details><summary>Validation details</summary><p>Rule: <code>${escapeHtml(iss.rule)}</code><br>Entity: <code>${escapeHtml(iss.entity_id || 'Catalog')}</code>${iss.file_origin ? `<br>Source: <code>${escapeHtml(iss.file_origin)}</code>` : ''}</p></details>
            </article>`;
          }).join('');
        } else {
          issuesContainer.innerHTML = '<p class="text-emerald-400">✓ All topological integrity and governance checks passed with 0 issues.</p>';
        }
      }

      // 3. Render Diagrams
      if (state.diagrams['time-matrix']) {
        updateDiagram('mermaid-time-matrix', state.diagrams['time-matrix']);
      }
      renderCapabilityHeatmap();
      renderTechnologyRadar();
      window.TectonRoadmap.render(document.getElementById('roadmap-schedule'), state);

      window.TectonDFD.render(document.getElementById('dfd-view'), state);

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
        setTimeout(() => safeRenderMermaid(activeTab), 100);
      }
    }

    function updateDiagram(elementId, content) {
      const el = document.getElementById(elementId);
      if (el) {
        el.classList.add('mermaid');
        el.classList.remove('empty-state', 'offline-rendered');
        el.removeAttribute('data-processed');
        el.textContent = elementId === 'mermaid-data-lineage' ? content.replace(/^flowchart LR/m, 'flowchart TB') : content;
      }
    }

    function showDiagramEmpty(elementId, title, message) {
      const el = document.getElementById(elementId);
      el.classList.remove('mermaid', 'offline-rendered');
      el.classList.add('empty-state');
      el.removeAttribute('data-processed');
      el.innerHTML = `<div><strong>${escapeHtml(title)}</strong>${escapeHtml(message)}</div>`;
    }

    function inventoryItems(ids, catalog) {
      if (!ids || !ids.length) return '<span class="text-slate-400">—</span>';
      const names = new Map(catalog.map(item => [item.id, item.name]));
      const list = entries => `<ul class="inventory-items">${entries.map(id =>
        `<li title="${escapeHtml(id)}">${escapeHtml(names.get(id) || id)}</li>`).join('')}</ul>`;
      return list(ids.slice(0, 3)) + (ids.length > 3
        ? `<details><summary>${ids.length - 3} more</summary>${list(ids.slice(3))}</details>` : '');
    }

    function renderApplicationsTable(apps) {
      const tbody = document.getElementById('apm-table-body');
      tbody.innerHTML = apps.map(app => {
        const quadrant = app.time_classification || 'UNKNOWN';
        const qColor = quadrant === 'INVEST' ? 'text-emerald-400' : quadrant === 'TOLERATE' ? 'text-yellow-400' : quadrant === 'MIGRATE' ? 'text-blue-400' : 'text-red-400';
        return `<tr>
          <td class="p-3 text-slate-200"><div class="inventory-name">${escapeHtml(app.name)}</div><span class="inventory-id">${escapeHtml(app.id)}</span><p class="inventory-description">${escapeHtml(app.description || "")}</p>${(app.components || []).length ? `<button type="button" class="text-indigo-300" data-components="${escapeHtml(app.id)}">View ${app.components.length} components →</button>` : ''}</td>
          <td class="p-3">${escapeHtml(app.owner || '-')}</td>
          <td class="p-3">${escapeHtml(app.current_phase || '-')}</td>
          <td class="p-3 font-semibold ${qColor}">${escapeHtml(quadrant)}</td>
          <td class="p-3 text-slate-400">${escapeHtml(app.business_criticality || '-')}</td>
          <td class="p-3 text-slate-400">${escapeHtml(app.functional_suitability || '-')} / ${escapeHtml(app.technical_suitability || '-')}</td>
          <td class="p-3">${inventoryItems(app.capabilities, state.capabilities)}</td>
          <td class="p-3">${inventoryItems(app.technologies, state.technologies)}</td>
        </tr>`;
      }).join('');
      tbody.querySelectorAll('[data-components]').forEach(button => button.addEventListener('click', () => {
        const application = state.applications.find(item => item.id === button.dataset.components);
        const dialog = document.getElementById('components-dialog');
        dialog.querySelector('h2').textContent = `${application.name} — ${application.components.length} components`;
        dialog.querySelector('.component-cards').innerHTML = application.components.map(c => `<article class="component-card"><h3>${escapeHtml(c.name)}</h3><p>${escapeHtml(c.description || 'No description provided.')}</p><details><summary>Technical ID</summary><code>${escapeHtml(c.id)}</code></details></article>`).join('');
        dialog.showModal();
      }));
    }

    function filterApplications() {
      const q = document.getElementById('apm-search').value.toLowerCase();
      const filtered = state.applications.filter(a =>
        a.name.toLowerCase().includes(q) ||
        a.id.toLowerCase().includes(q) ||
        (a.owner && a.owner.toLowerCase().includes(q)) ||
        (a.tags || []).some(tag => tag.toLowerCase().includes(q)) ||
        (a.time_classification && a.time_classification.toLowerCase().includes(q))
      );
      renderApplicationsTable(filtered);
    }

    function renderCapabilitiesTable() {
      const tbody = document.getElementById('bcm-table-body');
      tbody.innerHTML = state.capabilities.map(cap => {
        const cov = state.coverage && state.coverage.coverages ? state.coverage.coverages[cap.id] : null;
        const count = cov ? (cov.realizing_systems_count ?? (cov.realizing_system_ids || []).length) : 0;
        const status = count === 0 ? '<span class="text-red-400 font-bold">UNMAPPED GAP</span>' : `<span class="text-emerald-400">${count} system(s)</span>`;
        return `<tr>
          <td class="p-3 font-medium text-slate-200">${escapeHtml(cap.name)} <span class="text-slate-500 text-[10px]">(${escapeHtml(cap.id)})</span></td>
          <td class="p-3 text-slate-400">${escapeHtml(cap.level || 'L1')}</td>
          <td class="p-3">${status}</td>
          <td class="p-3 text-slate-400">${cov ? (cov.realizing_systems || cov.realizing_system_names || []).map(escapeHtml).join(', ') || '-' : '-'}</td>
          <td class="p-3 text-slate-400">${escapeHtml(cov ? cov.health : '-')}</td>
        </tr>`;
      }).join('');
    }


    function renderCapabilityHeatmap() {
      const host = document.getElementById('capability-heatmap');
      const classes = { HEALTHY: 'heat-healthy', TOLERABLE: 'heat-tolerable', AT_RISK: 'heat-at-risk', UNMAPPED: 'heat-unmapped', UNKNOWN: 'heat-unknown' };
      const names = new Map(state.capabilities.map(cap => [cap.id, cap.name]));
      const capabilities = [...state.capabilities].sort((a,b) => a.name.localeCompare(b.name));
      const ids = new Set(capabilities.map(c => c.id));
      const seen = new Set();
      const tile = cap => {
        const cov = state.coverage?.coverages?.[cap.id];
        const health = cov && classes[cov.health] ? cov.health : 'UNKNOWN';
        const count = cov ? (cov.realizing_systems_count ?? (cov.realizing_system_ids || []).length) : null;
        const systems = cov ? (cov.realizing_systems || cov.realizing_system_names || []) : [];
        const label = health === 'UNMAPPED' ? 'No direct systems' : health.replace(/_/g, ' ').toLowerCase();
        return `<details class="capability-cell ${classes[health]}"><summary><span class="capability-cell-level">${escapeHtml(cap.level || '')}</span><strong>${escapeHtml(cap.name)}</strong><span class="capability-cell-footer"><span>${escapeHtml(label)}</span><span>${count === null ? '?' : count} systems</span></span></summary><div class="capability-cell-detail"><p>${escapeHtml(cap.description || 'No description provided.')}</p><p>${systems.length ? systems.map(escapeHtml).join('<br>') : 'No directly mapped systems.'}</p></div></details>`;
      };
      const branch = cap => {
        if (seen.has(cap.id)) return '';
        seen.add(cap.id);
        const children = capabilities.filter(c => c.parent_id === cap.id);
        return `<div class="capability-branch">${tile(cap)}${children.length ? `<div class="capability-children">${children.map(branch).join('')}</div>` : ''}</div>`;
      };
      const roots = capabilities.filter(c => !c.parent_id || !ids.has(c.parent_id));
      host.innerHTML = roots.map(cap => `<section class="capability-area" aria-label="${escapeHtml(cap.name)}">${branch(cap)}</section>`).join('');
      host.innerHTML += capabilities.filter(c => !seen.has(c.id)).map(cap => `<section class="capability-area">${branch(cap)}</section>`).join('');
      if (!capabilities.length) host.innerHTML = '<p class="empty-state">No business capabilities defined in this catalog.</p>';
    }

    function renderTechnologyRadar() {
      window.TectonRadar.render(document.getElementById('technology-radar'), state);
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
        report = (state.blastRadiusReports || {})[techId];
        if (!report) {
          resContainer.textContent = 'Impact analysis unavailable.';
          return;
        }
      } else {
        report = await fetch(`/api/v1/trm/blast-radius/${techId}`).then(r => r.json());
      }

      resContainer.innerHTML = `
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="font-bold text-base text-indigo-400">${escapeHtml(report.technology_name)}</span>
            <span class="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-semibold">Risk Score: ${escapeHtml(report.risk_score ?? 'N/A')}</span>
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
      select.disabled = !state.dataObjects.length;
      select.innerHTML = state.dataObjects.map(d => `<option value="${escapeHtml(d.id)}">${escapeHtml(d.name)} (${escapeHtml(d.classification)})</option>`).join('') || '<option>No data objects</option>';
      if (state.dataObjects.length > 0) {
        renderSelectedLineage();
      } else {
        showDiagramEmpty('mermaid-data-lineage', 'No data lineage to display',
          'This catalog has no data objects. Data flows will appear here when objects and their relationships are defined.');
      }
    }

    async function renderSelectedLineage() {
      const dataId = document.getElementById('lineage-data-select').value;
      if (!dataId) return;
      const dataObject = state.dataObjects.find(item => item.id === dataId);
      document.getElementById('lineage-summary').textContent = dataObject
        ? `${dataObject.name} · ${dataObject.classification}. Arrows show declared transfers between systems; labels identify the channels. This catalog describes system-level lineage.`
        : 'Arrows show declared data transfers between systems.';

      const host = document.getElementById('mermaid-data-lineage');
      host.textContent = 'Loading data transfers…';
      try {
        const report = state.isStatic ? state.lineageReports?.[dataId] : await fetch(`/api/v1/data/lineage/${encodeURIComponent(dataId)}`).then(r => {if (!r.ok) throw new Error('Lineage unavailable'); return r.json();});
        if (document.getElementById('lineage-data-select').value !== dataId) return;
        const groups = new Map();
        for (const edge of report?.flow_edges || []) {
          const key = JSON.stringify([edge.source_system_id,edge.target_system_id]);
          if (!groups.has(key)) groups.set(key,{...edge,channels:new Map()});
          const channel = edge.channel_name || 'Declared relationship';
          const technical = /^(depends_on|integrates_with|uses|calls) [(]/.test(channel);
          const name = technical ? channel.split(' (')[0].replaceAll('_',' ') : channel;
          groups.get(key).channels.set(JSON.stringify([name,edge.protocol]),{name,protocol:edge.protocol});
        }
        window.TectonLineage.render(host, [...groups.values()]);
      } catch (error) { host.textContent = 'Data lineage unavailable. Reload to try again.'; }

    }

    function renderDataAndInterfaces() {
      const doList = document.getElementById('data-objects-list');
      doList.innerHTML = state.dataObjects.map(d => `
        <div class="p-2.5 rounded bg-slate-950 border border-slate-800 flex justify-between items-center">
          <div><span class="text-slate-200 font-semibold">${escapeHtml(d.name)}</span> <span class="text-slate-500">(${escapeHtml(d.id)})</span></div>
          <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-pink-400 font-bold">${escapeHtml(d.classification)}</span>
        </div>
      `).join('') || '<p class="empty-state">No data objects defined in this catalog.</p>';

      const ifList = document.getElementById('interfaces-list');
      ifList.innerHTML = state.interfaces.map(i => `
        <div class="p-2.5 rounded bg-slate-950 border border-slate-800 flex justify-between items-center">
          <div><span class="text-slate-200 font-semibold">${escapeHtml(i.name)}</span> <span class="text-slate-500">(${escapeHtml(i.provider_system_id)})</span></div>
          <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-amber-400 font-bold">${escapeHtml(i.protocol)}</span>
        </div>
      `).join('') || '<p class="empty-state">No interfaces defined in this catalog.</p>';
    }

    function populateCompareSelects() {
      const fromSel = document.getElementById('compare-from-select');
      const toSel = document.getElementById('compare-to-select');
      const opts = state.plateaus.map(p => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)}</option>`).join('');
      fromSel.innerHTML = opts || '<option>No plateaus</option>';
      toSel.innerHTML = opts || '<option>No plateaus</option>';
      fromSel.disabled = toSel.disabled = state.plateaus.length < 2;
      document.getElementById('compare-button').disabled = state.plateaus.length < 2;
      if (state.plateaus.length < 2) {
        document.getElementById('scenario-compare-result').textContent =
          'Define at least two architecture plateaus to compare scenarios.';
      }
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

      if (fromP === toP) { container.textContent = 'Choose two different architecture stages to compare.'; return; }
      container.textContent = 'Comparing architecture stages…';
      let comp;
      try {
        comp = state.isStatic ? state.scenarioComparisons?.[`${fromP}_${toP}`]
          : await fetch(`/api/v1/roadmap/compare?from_plateau=${encodeURIComponent(fromP)}&to_plateau=${encodeURIComponent(toP)}`).then(r => {if (!r.ok) throw new Error('Comparison unavailable'); return r.json();});
      } catch (error) { container.textContent = 'Comparison unavailable. Reload to try again.'; return; }
      if (document.getElementById('compare-from-select').value !== fromP || document.getElementById('compare-to-select').value !== toP) return;
      if (!comp) {container.textContent = 'No comparison available for these architecture stages.'; return;}
      const systems = new Map(state.applications.map(s => [s.id,s.name]));
      const capabilities = new Map(state.capabilities.map(c => [c.id,c.name]));
      const technologies = new Map(state.technologies.map(t => [t.id,t.name]));
      const list = (ids,names) => ids?.length ? `<ul>${ids.map(id => `<li>${escapeHtml(names.get(id) || id)}</li>`).join('')}</ul>` : '<p class="scenario-none">None</p>';
      const gained = comp.gained_capability_ids || [], lost = comp.lost_capability_ids || [];
      const net = comp.net_capability_gain;
      container.innerHTML = `
        <div class="scenario-stages"><div><small>FROM</small><strong>${escapeHtml(comp.from_plateau_name || fromP)}</strong></div><span aria-hidden="true">→</span><div><small>TO</small><strong>${escapeHtml(comp.to_plateau_name || toP)}</strong></div></div>
        <div class="scenario-metrics"><article class="${net < 0 ? 'scenario-loss' : ''}"><strong>${net > 0 ? '+' : ''}${escapeHtml(net)}</strong><h3>Change in capability coverage</h3><p>${gained.length} gained · ${lost.length} lost</p></article><article><strong>${escapeHtml(comp.tech_debt_reduction_count)}</strong><h3>Obsolete technologies removed</h3><p>No longer used by systems in the target stage.</p></article></div>
        ${lost.length ? `<div class="scenario-warning"><strong>Capability coverage is lost in the target stage</strong>${list(lost,capabilities)}<p>The target catalog has no active system mapped to these capabilities.</p></div>` : ''}
        <div class="scenario-columns"><section><h3>Added systems <span>${(comp.added_system_ids || []).length}</span></h3>${list(comp.added_system_ids,systems)}</section><section><h3>Retired systems <span>${(comp.decommissioned_system_ids || []).length}</span></h3>${list(comp.decommissioned_system_ids,systems)}</section><section><h3>Retained systems <span>${(comp.retained_system_ids || []).length}</span></h3>${list(comp.retained_system_ids,systems)}</section></div>
        <details class="scenario-details"><summary>Capability and technology changes</summary><div class="scenario-columns"><section><h3>Capabilities gained</h3>${list(gained,capabilities)}</section><section><h3>Obsolete technologies removed</h3>${list(comp.eliminated_obsolete_technologies,technologies)}</section><section><h3>Technologies introduced</h3>${list(comp.introduced_technologies,technologies)}</section></div></details>`;

    }

    document.addEventListener('DOMContentLoaded', init);
  </script>
</body>
</html>
"""
