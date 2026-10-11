# ADR 0007: Pilot the catalog on Tecton itself

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

Before committing to a central Git EAM repository, verify that owners can
maintain model entries through reviewed changes and a generated read-only portal.

## Decision

Use the existing dogfood workspace for a catalog of one Tecton product and
logical child components. Preserve stable module IDs. Add optional system
ownership to the shared schema and require it in the pilot with `--require-owner`.
Validate PR merge states and publish the portal as a CI artifact.

## Consequences and limits

The pilot reuses the current parser, analysis and portal instead of creating a
second catalog service. Modules use the existing `containers` representation;
ownership/lifecycle inheritance is a documented convention. Local tests exercise
addition, owner change, deletion and conflicting parallel changes. Actual reviewed
PRs and a later business-domain pilot are needed to establish organizational fit.
See the [pilot guide](../08_git_eam_pilot.md).
