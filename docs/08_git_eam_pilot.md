# Git EAM catalog pilot

The pilot uses `examples/dogfood/tecton_c4_workspace` as the source of truth
for Tecton's own architecture. It tests catalog maintenance by architects and
tech leads using YAML and reviewed pull requests. Choosing Git as an
organization-wide EAM system of record remains a later decision.

## 🗂️ Model and ownership

Tecton is one software system (`sys-tecton`). Its implementation modules are
logical child components represented through the existing `containers` schema;
these entries do not imply independently deployed applications. Existing module
IDs are retained. Components inherit the product's owner and lifecycle.
The Python technology ID is also retained; its name now reflects the supported
Python 3.11+ baseline in `pyproject.toml`.

Every pilot system needs an owner, description and current lifecycle phase.
`owner` is optional in the general schema for backward compatibility;
`--require-owner` rejects missing or whitespace-only owners in this pilot.
`Tecton maintainers` is the initial accountable team label, to be mapped to
actual reviewers when the repository is hosted. Changing a display name must
preserve its ID. Deleting an entry requires removing its references in the same PR.

## ✅ Review and artifacts

```bash
tecton validate examples/dogfood/tecton_c4_workspace --require-owner --format json
python -m pytest tests/integration/test_eam_pilot.py tests/integration/test_dogfood.py
tecton export portal --source examples/dogfood/tecton_c4_workspace -o dist/eam-pilot
```

The GitHub Actions `EAM pilot catalog` check validates the synthetic merge
commit on pull requests and the merge-group state in a merge queue. Errors
block the check; warnings are informative. The portal is a read-only build
artifact, not a versioned source file or a deployed site. Its current styling
and Mermaid diagrams load CDN assets; this pilot does not promise a fully
offline visual experience.

On GitHub, configure `main` to require this check, one approval from someone
other than the author, dismissal of stale approvals, and an up-to-date branch
or merge queue. Do not allow bypasses for ordinary catalog updates. These
hosting settings cannot be enforced by committed workflow files alone.

## 🧪 Acceptance exercises

Use three reviewed PRs: add a component with a relationship; change the
product owner; remove the new component and its relationship together.
The exported portal must show the new component and changed owner, then omit
the removed component. `test_eam_pilot.py` verifies these state transitions
locally, plus duplicate IDs and dangling references introduced by combining
individually valid parallel changes. Actual PRs and reviewer approval still
require a hosted repository.

Success means all pilot systems have owners, validation passes, and the portal
reflects the accepted catalog. Review maintenance effort after the three PRs
before extracting a central repository. Business-domain adoption must be
tested separately. Discovery, external EAM synchronization and editing forms
are outside this pilot.
