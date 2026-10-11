# 🐙 GitHub publication

The target repository is [senssei/tecton](https://github.com/senssei/tecton).
GitHub hosts source, documentation, CI and reviewed changes. PyPI will distribute
`tecton-arch`; see the [release guide](pypi_release.md).

## Included repository materials

README/logo, Apache-2.0 license, contribution/security guides, changelog,
bug/feature templates, PR template, documentation checker, build/installation
checks and the EAM pilot workflow are versioned with the source. Generated portals
and distribution files are ignored and uploaded as CI artifacts.

## Verification before pushing

```bash
python -m pytest
python scripts/check_docs.py
tecton validate examples/dogfood/tecton_c4_workspace --require-owner --format json
python -m build
python -m twine check --strict dist/*.whl dist/*.tar.gz
python scripts/check_distribution.py
```

The general CI runs tests/docs on Python 3.11 and 3.14, then checks distribution
metadata and installs the wheel outside the source checkout. The pilot workflow
validates the merged catalog and builds a portal artifact. Neither workflow
publishes a package or deploys a website.

## Repository settings

Set the default branch to `main`. Require the general CI jobs and
`EAM pilot catalog`, one approval from another person, stale-approval dismissal,
and an up-to-date branch or merge queue. Workflow files cannot enable these
hosting settings by themselves. Configure real owner/team reviewers before adding
CODEOWNERS; no invented usernames are included.

Suggested description: **Enterprise architecture as code: Git catalog, graph
validation, portfolio analysis and a read-only portal.** Suggested topics:
`enterprise-architecture`, `architecture-as-code`, `eam`, `gitops`, `python`,
`mermaid`, `application-portfolio-management`.

Public exposure, branch rules, private vulnerability reporting and GitHub
Environments are repository settings. Adding source files does not configure them.

## New clone or remote

```bash
git clone https://github.com/senssei/tecton.git
```

For an existing checkout with no remote, add it once:

```bash
git remote add origin https://github.com/senssei/tecton.git
```

Commit reviewed changes and push a normal fast-forward. Do not overwrite remote
history if another contributor has pushed. Check the
[Actions page](https://github.com/senssei/tecton/actions) after pushing and download
the pilot artifact to inspect its portal.

## PyPI preparation

Create the `testpypi` and `pypi` environments and configure trusted publishers
as described in the [release guide](pypi_release.md). The publish workflow is
manual and expects a version tag; ordinary pushes only test/build artifacts.

See the [GitHub workflow event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
for PR/merge-group behavior.
