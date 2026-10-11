# ADR 0004: Mermaid diagrams and Markdown reports

- **Status:** Accepted
- **Date:** 2026-10-10

## Context

Architecture outputs should be inspectable text that can be versioned and shared
without a proprietary image-rendering API.

## Decision

Generate Mermaid diagram source and Markdown reports, including portfolio
quadrants, capability/technology diagrams, lineage and roadmaps. Provide an HTML
portal for browsing an embedded or API-supplied model snapshot.

## Consequences and limits

Text generation works locally and produces reviewable changes. Graphical
rendering requires a Mermaid-capable viewer; support varies across hosts.
The current HTML portal loads Tailwind and Mermaid from CDNs, so full visual
rendering is not an air-gapped capability. Bundled offline assets remain future work.
