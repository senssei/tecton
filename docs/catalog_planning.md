# Catalog review and transformation planning

Tecton evaluates declared architecture data. Git remains the source of truth;
reviews are recorded by editing manifests and approving pull requests. The portal
is read-only. The example workspace at `examples/planning` includes a migration,
costs, review metadata and deliberately exceeded capacity and budget limits.

## Complete change review

```bash
tecton diff main HEAD --workspace-path examples/planning --as-of-date 2026-06-01 --format pr-comment -o dist/review.md
tecton catalog freshness --source examples/planning --as-of-date 2026-07-01 --format json
```

Semantic diff includes all entity collections and declared fields, nested DFD
nodes/flows, reviews, costs and metadata. References/tags are order-independent;
lifecycle phase order and arbitrary metadata lists remain significant.
Relationships have no IDs: changing any field appears as removal and addition,
and repeated relationships are preserved. Added/removed entities include snapshots.

Base and head use one date and the head workspace's configuration. Use `--config`
to select a shared configuration explicitly. Configuration changes appear
separately; credentials are excluded from reports and fingerprints. Git diff
supports a relative `--workspace-path`, including `WORKTREE` as head.
`--fail-on-risk` blocks new validation errors or capability gaps; it does not
mean every detected change is prohibited.

## Reviews and policies

Every global entity and relationship supports optional `review` metadata.
DFD nodes and flows inherit their diagram's review.

```yaml
systems:
  - id: reviewed-system
    name: Reviewed system
    owner: platform
    current_phase: active
    review:
      reviewed_on: 2026-06-01
      reviewed_by: platform
      next_review_on: 2026-12-01
```

`reviewed_on` and nonblank `reviewed_by` must be supplied together. A review is
current through its due date; overdue begins the following day. Without an
explicit next review, validity is 180 days. Future-dated reviews are flagged.
A missing review is unknown freshness, not proof that an entity was reviewed.

Configure `tecton.yaml`:

```yaml
owners:
  platform: {name: Platform team, active: true}
quality:
  review_valid_days: 180
  rules:
    REVIEW_MISSING: warning
    REVIEW_OVERDUE: error
    REVIEW_FUTURE_DATED: error
    OWNER_UNKNOWN: error
    OWNER_INACTIVE: error
    DESCRIPTION_MISSING: warning
    LIFECYCLE_MISSING: warning
    SUITABILITY_MISSING: warning
```

New optional completeness checks are off until enabled. Existing rule severities
remain unchanged. Levels are `error`, `warning`, `off`; unknown rule names fail
configuration validation. Parsing, duplicate-ID and dangling-reference errors
cannot be downgraded or disabled. `--strict` blocks active warnings;
`--require-owner` requires a nonblank system owner even if its rule is disabled.
Legacy owner labels remain accepted unless directory validation is enabled.
An explicitly supplied missing or unreadable configuration fails rather than
silently selecting another file.

## Safe ID refactoring

```bash
tecton catalog rename old replacement --source examples/planning --format json
tecton catalog rename old replacement --source examples/planning --output dist/refactored-catalog
```

The first command previews. The second writes a normalized `catalog.yaml` and
`tecton.yaml` into a new directory outside the source workspace, after strict
schema and reference validation. The destination must not exist. Source files
are untouched; review and bring the generated changes into Git yourself.
YAML comments, original file boundaries and formatting are not preserved.

All typed global references are updated, including DFD system/data references.
Local DFD node/flow IDs are separate namespaces and remain unchanged. Text in
metadata and descriptions is not rewritten; metadata occurrences are reported
for manual review. Unknown IDs, collisions and invalid resulting graphs fail.

## Portfolio and capability decisions

```bash
tecton apm costs --source examples/planning --format json
tecton bcm analyze --source examples/planning --as-of-date 2026-06-01
```

APM, BCM and lineage use evaluated TIME classifications from the same thresholds.
Reports retain the declared classification and identify mismatches, scores,
thresholds and missing inputs. Analysis never writes classification changes;
`apm patch-time` remains the explicit persistence operation.

Capabilities support `importance` from 1 to 5 (default 1). Direct realization
remains separate from aggregated realization across a subtree. Leaf coverage
counts supported leaves; weighted coverage weights each leaf by its importance.
A system mapped only to a parent does not imply every child is covered. Cycles
make hierarchy aggregation unavailable.

Systems accept `annual_cost: {amount: '100.10', currency: PLN}` and optional
`suitability_rationale`. Amounts use decimal arithmetic and serialize as strings.
Currencies use three uppercase letters. Totals remain separated by currency;
no exchange rates are applied. Missing amounts are reported, not treated as zero.
Capability costs count each supporting system once within its subtree. Adding
capability totals together can double-count shared systems.

Lineage distinguishes `no_modeled_flows`, `risks_detected`, and
`no_detected_risks`. The legacy `is_compliant` field is deprecated: it only means
no heuristic risks were found and provides no compliance certification.

## Business cases and feasible plans

```bash
tecton roadmap business-case --source examples/planning --format json
tecton roadmap feasibility --source examples/planning --as-of-date 2026-06-01 --format json
tecton export portal --source examples/planning --as-of-date 2026-06-01 -o dist/planning-portal
```

Work packages may declare:

- `planned_cost`: nonnegative amount and currency.
- `business_case`: signed `annual_net_savings`, positive integer `horizon_years`,
  and a nonempty list of `assumptions`. Savings use the planned-cost currency.
- `introduced_system_ids` and `decommissioned_system_ids`: explicit transition roles.
- `resource_allocations`: `team_id`, `month` (`YYYY-MM`), `person_days`.
- `spend_plan`: `month`, `amount`; entries must sum exactly to planned cost.

Business cases require planned cost. Net benefit is annual savings times horizon
minus migration cost. ROI is net benefit divided by cost times 100%; zero cost
has no defined ROI. Payback is cost divided by positive annual savings; zero or
negative savings have no finite payback. The calculation assumes constant net
savings beginning in the first year after completion, without discounting.
It does not infer savings from application similarity or annual running costs.

Monthly limits live in configuration:

```yaml
teams:
  platform:
    capacity_person_days: '20'
    monthly_capacity:
      2026-06: '25'
budgets:
  2026-06:
    PLN: '900'
```

Allocations aggregate by team and month; costs aggregate by month and currency.
Repeated allocations are additive. Cancelled initiatives are excluded; all other
statuses count. Missing plans or limits produce `not_assessed` controls.
No load or spending distribution is inferred from dates.

Feasibility checks cycles, prerequisites, date inversions, missed milestones,
allocation/spending months, capability loss, dated replacement delivery,
capacity overload and exceeded budgets. Each plateau is compared with its own
predecessor. The result is `violations_detected`, `insufficient_data` or
`no_detected_violations`; the last means declared checks passed, not guaranteed
real-world feasibility. Conflicts list contributing initiatives. There is no
automatic rescheduling or resource optimizer.

## Interfaces and interchange

Read APIs expose `/api/v1/catalog/freshness`, `/api/v1/apm/costs`,
`/api/v1/roadmap/business-case` and `/api/v1/roadmap/feasibility`.
Date-dependent analyses and diagrams accept `as_of_date=YYYY-MM-DD`.
The live portal shares one selected evaluation date; exported portals display
an immutable snapshot date. Both show catalog/planning reports offline or live.

Native YAML/JSON preserves the extended fields. Backstage and ArchiMate exports
return `warnings` for extended fields whose preservation is not guaranteed;
the CLI prints warnings to stderr while retaining the interchange artifact.
Review imported models rather than relying on lossless round trips.
