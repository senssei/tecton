# Tecton (Enterprise Architecture Intelligence Engine)

> **Deterministic Enterprise Architecture Intelligence & Architecture-as-Code Toolkit**
> Enforce architectural quality gates, automate portfolio scoring (Gartner TIME framework), detect functional redundancy, and generate living documentation directly from code repositories and CI/CD pipelines without vendor lock-in.

---

## 📁 Repository Structure

```
tecton/
├── docs/                                    # 📚 Comprehensive architectural & analytical documentation
│   ├── 01_product_vision.md                 # Product vision, mission, and five strategic pillars
│   ├── 02_adversarial_analysis.md           # Adversarial analysis: EAM repository APIs vs. domain logic
│   ├── 03_baseline_architecture.md          # Baseline hexagonal architecture & APM module design
│   ├── 04_eam_capabilities_catalog.md       # Standard metamodel & EAM capability taxonomy
│   ├── 05_attribute_driven_design.md        # SEI Attribute-Driven Design (ADD 3.0) specification
│   ├── 06_git_eam_graph_adversarial_analysis.md # Adversarial analysis: Git-backed EAM graph & C4 DSL
│   └── adr/                                 # 🏛️ Architecture Decision Records (ADRs)
│       ├── 0001-hexagonal-architecture.md
│       ├── 0002-deterministic-offline-engines.md
│       ├── 0003-safety-first-mutation-policy.md
│       ├── 0004-sovereign-mermaid-visualizations.md
│       ├── 0005-attribute-driven-design-methodology.md
│       └── 0006-git-backed-eam-graph-and-c4-extended-dsl.md
├── src/                                     # 💻 Production source code (Clean Architecture)
│   └── tecton/
│       ├── core/                            # Pure domain models (Application, Lifecycle, TIME, Config)
│       ├── dsl/                             # C4-Extended EAM DSL (schema, parser, compiler, linter)
│       ├── engines/                         # Deterministic analytic engines (TIME, Redundancy, Lifecycle)
│       ├── adapters/                        # Ports & Adapters (Git Workspace, GraphQL, In-Memory, File)
│       ├── exporters/                       # Visual exporters (Mermaid quadrantChart, Living Markdown)
│       ├── services/                        # Orchestration services (APMService)
│       └── cli/                             # Terminal interface (Typer + Rich: validate, apm)
├── tests/                                   # 🧪 Automated test suite (100% offline, unit & integration)
│   ├── unit/                                # Unit tests for analytic engines, adapters, and DSL linter
│   ├── integration/                         # Integration tests for CLI, Git adapter, and dogfooding
│   └── fixtures/                            # Test fixtures and enterprise application samples
├── examples/                                # 📋 Declarative manifests & dogfooding models
│   ├── c4_eam_workspace/                    # Sample Git-backed C4-Extended Architecture-as-Code repository
│   ├── config/                              # Sample tecton.yaml configurations
│   └── dogfood/                             # Tecton's self-describing architecture models (JSON & C4 DSL)
├── .gitignore                               # 🛡️ Python, virtual environment, and credential exclusions
└── README.md                                # 📌 Project entry point
```

---

## 🚀 Quick Start

### Installation
```bash
# Clone and set up virtual environment
git clone <repo-url> tecton
cd tecton
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Architecture Quality Gate & Linting (CI/CD Enforcement)
Prevent dangling pointers, cycles, and schema corruption before merging Pull Requests:
```bash
# Validate Git-backed architecture repository (checks referential integrity & DAG invariants)
tecton validate examples/c4_eam_workspace

# Enforce strict zero-warning policy (exits with code 1 on any warning)
tecton validate --strict examples/c4_eam_workspace

# Emit machine-readable JSON report for CI/CD pipelines
tecton validate --format json examples/c4_eam_workspace

# Using 'lint' alias
tecton lint examples/c4_eam_workspace
```

### Application Portfolio Management (APM)
Analyze portfolio health directly from a Git-backed workspace or local file:
```bash
# Inspect application portfolio directly from Git repository manifests
tecton apm list --source examples/c4_eam_workspace

# Run full deterministic APM evaluation (TIME, Redundancy, Lifecycle validation)
tecton apm analyze --source examples/c4_eam_workspace

# Export living Mermaid quadrant chart directly from Git repository
tecton apm export-matrix --source examples/c4_eam_workspace --format mermaid

# Export executive Markdown living report
tecton apm export-matrix --source examples/c4_eam_workspace --format markdown -o report.md

# Safely simulate TIME quadrant patch updates (Dry-Run by default)
tecton apm patch-time --source examples/c4_eam_workspace
```

### Business Capability Management (BCM) & Heatmaps
Audit capability realization, uncover unmapped blind spots, and export living heatmaps:
```bash
# Render interactive hierarchical capability tree in the terminal
tecton bcm tree --source examples/c4_eam_workspace

# Run full realization coverage, gap analysis, and capability health scoring
tecton bcm analyze --source examples/c4_eam_workspace

# Export color-coded Mermaid capability realization heatmap
tecton bcm heatmap --source examples/c4_eam_workspace
```

### Technology Risk & Obsolescence Management (TRM) & Blast Radius
Manage tech radar standards and compute cascading blast radius of EOL components:
```bash
# List technology catalog with radar status, EOL milestones, and adoption count
tecton trm list --source examples/c4_eam_workspace

# Trace direct & cascading transitive dependency blast radius of an obsolete technology
tecton trm blast-radius tech-legacy-solaris --source examples/c4_eam_workspace

# Export living Mermaid Technology Radar flowchart
tecton trm export-radar --source examples/c4_eam_workspace
```

### Semantic Architecture Diff & GitOps Review Gate
Compare architecture states between Git branches, commit revisions, or directories:
```bash
# Compare two architecture workspaces or folders
tecton diff examples/c4_eam_workspace examples/dogfood/tecton_c4_workspace

# Compare Git revisions (e.g. main vs current HEAD or feature branch)
tecton diff main HEAD

# Generate an executive GitHub / GitLab Pull Request review comment
tecton diff main HEAD --format pr-comment -o pr_review.md

# Enforce pre-merge gate (exit code 1 if breaking regressions or unmapped capability gaps are introduced)
tecton diff main HEAD --fail-on-risk
```

---

## 🐶 Dogfooding Tecton
Tecton evaluates and audits its own internal architecture using its own analytic engines and quality gates:
```bash
# 1. Enforce Quality Gate on Tecton's own C4 Architecture-as-Code workspace
tecton validate examples/dogfood/tecton_c4_workspace

# 2. Run APM portfolio analysis on Tecton's own components
tecton apm analyze --source examples/dogfood/tecton_c4_workspace

# 3. Export living Mermaid quadrant matrix of Tecton's architecture
tecton apm export-matrix --source examples/dogfood/tecton_c4_workspace --format mermaid
```

---

## 🏛️ Architecture Documentation Index
1. 📄 **[Product Vision (01_product_vision.md)](docs/01_product_vision.md)** – Mission, problem statement, business value, and Architecture-as-Code pillars.
2. 📄 **[Adversarial Analysis: Repository APIs (02_adversarial_analysis.md)](docs/02_adversarial_analysis.md)** – Critical gap assessment comparing EAM repository APIs to required domain intelligence.
3. 📄 **[Baseline Architecture (03_baseline_architecture.md)](docs/03_baseline_architecture.md)** – Hexagonal architecture specification, domain contracts, and APM engine design.
4. 📄 **[EAM Capability Catalog (04_eam_capabilities_catalog.md)](docs/04_eam_capabilities_catalog.md)** – Industry metamodel, entity definitions, and standard capability layers.
5. 📄 **[Attribute-Driven Design (05_attribute_driven_design.md)](docs/05_attribute_driven_design.md)** – SEI ADD 3.0 architectural drivers, tactics, and quality attribute scenarios.
6. 📄 **[Adversarial Analysis: Git-Backed EAM Graph (06_git_eam_graph_adversarial_analysis.md)](docs/06_git_eam_graph_adversarial_analysis.md)** – Deep gap analysis of Git as an EAM Graph database via C4-extended DSL (dangling edges, merge anomalies, indexing).
7. 📁 **[Architecture Decision Records (docs/adr/)](docs/adr/)** – Formal ADR log capturing design rationale and trade-offs.
