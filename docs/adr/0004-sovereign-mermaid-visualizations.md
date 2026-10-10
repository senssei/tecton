# ADR 0004: Native Mermaid Visualizations and Living Markdown Reports

* **Status:** Accepted
* **Date:** 2026-10-10
* **Deciders:** Solution Architecture Team
* **Consulted:** Tecton Core Contributors

---

## Context
Architectural decision-makers require clear visual reports (such as 2D portfolio quadrant charts and capability landscape matrices). However, EAM repositories do not expose image rendering APIs (PNG/SVG/PDF export endpoints are nonexistent in public APIs).

Traditional workarounds involve either manual screenshots taken from web portals or heavyweight headless browser automation (e.g., Puppeteer, Playwright), which introduces substantial deployment overhead, brittle dependencies, and security concerns in CI/CD environments.

## Decision
We adopt **Mermaid.js** and **GitHub Flavored Markdown** as the primary visual output formats:
1. `MermaidExporter`: Generates native `quadrantChart` Mermaid code, normalizing 1.0–5.0 suitability scores into 0.0–1.0 2D coordinates.
2. `MarkdownExporter`: Generates living, version-controllable architectural documentation combining executive summaries, distribution tables, redundancy findings, and embedded Mermaid diagrams.
3. Visualization generation operates completely offline without headless browsers or image rendering dependencies.

## Consequences

### Positive
* **Lightweight & Fast:** Generates visual diagram source code in microseconds with zero binary or browser dependencies.
* **GitOps Ready:** Markdown and Mermaid render natively in GitHub, GitLab, Notion, Azure DevOps, and documentation sites (Astro, MkDocs, Docusaurus).
* **Diffable:** Changes in architecture diagrams produce clean text git diffs rather than binary image conflicts.

### Negative / Trade-offs
* Requires a markdown viewer or browser with Mermaid support for graphical rendering.
* Mermaid's `quadrantChart` feature set is currently more constrained than full-featured commercial BI charting libraries.
