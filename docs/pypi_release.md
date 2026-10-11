# 📦 Releasing tecton-arch to PyPI

| Name | Value |
| --- | --- |
| Product / repository | Tecton / `senssei/tecton` |
| Distribution | `tecton-arch` |
| Python import | `tecton_arch` |
| Command | `tecton` |
| License | Apache-2.0 |
| Current prepared version | `0.1.0` (alpha) |

The unrelated [`tecton` distribution](https://pypi.org/project/tecton/) already
exists. This project uses a separate distribution and import namespace.
`tecton-arch` has not been reserved by preparing these files; verify availability
again when configuring the first publisher. Package-index availability is not a
trademark determination.

## Local package checks

```bash
python -m pip install -e '.[dev,release]'
python -m pytest
python scripts/check_docs.py
python -m build
python -m twine check --strict dist/*.whl dist/*.tar.gz
python scripts/check_distribution.py
```

`python -m build` builds the sdist and then a wheel from it. The sdist includes
source, docs, examples, tests and helper scripts. The wheel contains the Python
package, entry point and license notices; it does not include repository example
catalogs. CI installs the wheel in a fresh environment and runs commands from a
separate working directory, so editable imports cannot hide missing package files.

The index description comes from `PYPI_README.md`, with absolute repository links
and an inline model example. Metadata uses an SPDX license expression and requires
setuptools 77+ for PEP 639 support; see the
[setuptools configuration reference](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html).

## Configure Trusted Publishing once

In GitHub, create environments named `testpypi` and `pypi`; configure required
reviewers for production publication if supported by your account/repository.
In each package index, register a pending trusted publisher with:

- Project: `tecton-arch`.
- GitHub owner: `senssei`.
- Repository: `tecton`.
- Workflow filename: `publish.yml`.
- Environment: `testpypi` for TestPyPI, `pypi` for PyPI.

PyPI and TestPyPI have separate accounts and configuration. A pending publisher
creates the project on its first successful upload; it does not reserve the name.
Follow the [PyPI pending-publisher guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
and the [PyPA workflow guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).
No API-token secret is needed by this workflow.

## First release

1. Ensure `pyproject.toml`, the source fallback version and changelog describe the
   same version. Run the checks above and merge reviewed changes into `main`.
2. Create and push an annotated version tag such as `v0.1.0` at that commit.
3. Open GitHub Actions → **Publish package** → **Run workflow**. Choose the
   reviewed `main` workflow, tag `v0.1.0`, and target `testpypi`.
4. The workflow verifies tag/version consistency, tests, builds, checks metadata
   and installs the wheel before upload. Verify the resulting TestPyPI artifact.
5. Run the same workflow/tag with target `pypi` after accepting the TestPyPI result.
   Approve the production environment if configured. Create GitHub release notes
   from the changelog after the upload succeeds.

The workflow never publishes on an ordinary push. Uploaded index versions cannot
be overwritten; increment the version for a corrected release. Remove the
README's first-release preparation note after publication.

## Check the published package

For TestPyPI, first install dependencies from normal PyPI in an isolated environment,
then fetch only this distribution from TestPyPI:

```bash
python -m pip install requests 'pydantic>=2.6' 'typer>=0.9' 'rich>=13.7' 'pyyaml>=6' 'fastapi>=0.100' 'uvicorn>=0.25'
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps 'tecton-arch==0.1.0'
tecton --version
```

After production publication:

```bash
python -m pip install 'tecton-arch==0.1.0'
python -c 'from tecton_arch.application import TectonApp; print(TectonApp)'
tecton --version
```

Run outside the source checkout in a fresh virtual environment. Verify the
[project page](https://pypi.org/project/tecton-arch/) and the install instructions.
