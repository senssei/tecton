# 🔐 Security and deployment boundaries

Tecton is alpha software. Security fixes target the current development branch;
there is no established long-term-support release policy.

## Reporting

If GitHub private vulnerability reporting is enabled for `senssei/tecton`, use
its **Security → Report a vulnerability** entry. Otherwise contact the repository
owner privately through an available contact channel. Do not put live credentials,
real inventories or an unpatched exploit containing sensitive data in public issues.
No dedicated response-time commitment is currently established.

## Deployment assumptions

The CLI analyzes supplied manifests rather than discovering or proving the
security of deployed systems. The local API has unauthenticated read endpoints;
`TECTON_API_TOKEN` optionally guards only `POST /api/v1/reload`. It is not a full
API access-control system. The default server binding is localhost.

A static portal embeds the catalog in HTML. Anyone who can obtain that file can
read the embedded data. Its styling and diagrams load external CDN resources.
Use only data suitable for the chosen audience and hosting access rules.

Repository TIME patches simulate by default; `--apply` enables writes. Imports
and exports write files directly. Keep credentials in environment variables or
untracked local configuration. TestPyPI/PyPI workflows use Trusted Publishing,
not checked-in API tokens.
