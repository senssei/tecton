# ADR 0003: Dry-run repository patches

- **Status:** Accepted
- **Date:** 2026-10-10

## Context

A calculated portfolio recommendation should not silently change its repository.

## Decision

Repository patch APIs default to `dry_run=True`. `tecton apm patch-time` simulates
updates unless `--apply` is supplied. This command's flag controls the write;
it has no `--dry-run` option and does not use config to enable implicit writes.

## Consequences and limits

Previewing classification changes needs no write permissions. Supported Git
TIME updates atomically replace a single file and reload the graph. This is not
a complete RFC 6902 implementation, a general mutation workflow, or a bulk
transaction guarantee. Import/export commands and explicit Python save methods
write files directly. See [CLI persistence details](../cli_reference.md).
