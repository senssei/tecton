# Portal visualizations

The technology radar uses bundled D3 7.9.0. Its scripts, styles and license are
embedded into both static and REST portal HTML. The radar and explicit DFD view
work without network access; the other Mermaid diagrams and Tailwind styling
still use CDNs.

## Technology radar

Categories define sectors. Approval status defines four fixed rings: approved,
under evaluation, deprecated and prohibited. Unknown statuses appear in the list.
Point size reflects the number of directly using systems. A pink outer border
marks a technology whose declared end-of-life date has passed.

Search or filter by category, status, system and owner. Select a marker or list
entry to inspect its description, EOL date, system ownership and actual blast
radius analysis. The controls support zoom, reset and clearing filters. The list
is keyboard accessible and remains available when the chart is too dense.

REST and snapshots include `description`, `eol_date`, `is_eol`,
`days_to_eol`, `realizing_systems_count` and `realizing_system_details` for every
technology. Each system detail contains `id`, `name` and nullable `owner`.
Missing owners and dates are shown explicitly; missing impact reports are never
replaced with sample results.

## Explicit data flow diagrams

System-level lineage describes transfers between software systems. A DFD requires
separate definitions of processes, stores, external entities and named data flows.
Tecton never infers those roles from the system integration graph.

Define diagrams in the optional `data_flow_diagrams` collection. Diagram IDs are
catalog-wide; node and flow IDs are local to their diagram. Node kinds are
`process`, `data_store` and `external_entity`. Optional `system_id` associates a
node with an existing system. Every flow must reference existing local nodes,
connect to a process, and name at least one existing data object. Self-flows and
duplicate local IDs fail validation. Processes without both an input and an output
produce a warning.

```yaml
data_objects:
  - id: order
    name: Sales order
    classification: INTERNAL
data_flow_diagrams:
  - id: dfd-orders
    name: Order intake
    nodes:
      - {id: customer, name: Customer, kind: external_entity}
      - {id: capture, name: Capture order, kind: process}
      - {id: orders, name: Orders, kind: data_store}
    flows:
      - id: submit
        name: Submitted order
        source_id: customer
        target_id: capture
        data_objects: [order]
      - id: save
        name: Validated order
        source_id: capture
        target_id: orders
        data_objects: [order]
```

The portal draws processes as rounded boxes, stores with an open end and external
entities as rectangles. Arrows carry flow names; numbered flow definitions show
full names, endpoints and data objects. Existing system lineage remains below the
DFD. A catalog without explicit definitions shows an empty state.

`GET /api/v1/data/flow-diagrams` returns the models as JSON. Static snapshots carry
identical models in `dataFlowDiagrams`. The
[example catalog](../examples/c4_eam_workspace/data_objects.yaml) contains an
illustrative level-1 order-processing DFD, not an inferred production design.

## Browser verification

```bash
python -m pip install -e '.[dev]' playwright
python -m playwright install chromium
python -m pytest tests/browser
```

Browser checks block external network requests and exercise static catalogs,
REST data, filtering, keyboard selection, zoom, dense deterministic layouts, DFD
shapes and the component detail panel. General CI also runs these browser checks.

## Transformation schedule

The portal uses a bundled D3 timeline with a separate column for initiative names,
dates and status. Diamonds represent plateau target dates; bars use declared work
package start and target dates. Missing dates remain explicitly unspecified.
Descriptions, owners and prerequisites appear under Details. On smaller screens,
the timeline scrolls horizontally while the name column remains visible.

System-level lineage uses a connected graph with one node per system and grouped
channels on directed arrows. Desktop layouts run left to right; narrow screens
use a vertical layout. The graph retains declared branches and cycles.
