"""Static and Dynamic Architecture Portal Generator."""

import json
from pathlib import Path
from typing import Any

from tecton_arch.application.app import TectonApp
from tecton_arch.portal.template import PORTAL_HTML_TEMPLATE


class PortalBuilder:
    """Builder for Living Architecture Intelligence Web Portal & Dashboard."""

    @classmethod
    def build_dynamic_portal_html(cls) -> str:
        """Generate dynamic HTML connected to Tecton live REST API endpoints."""
        return PORTAL_HTML_TEMPLATE.replace("__DATA_PAYLOAD__", "null")

    @classmethod
    def build_static_portal_html(cls, app_or_graph: Any) -> str:
        """Generate HTML snapshot with embedded model data and CDN-hosted visual assets with pre-baked JSON graph payload."""
        if isinstance(app_or_graph, TectonApp):
            app = app_or_graph
        else:
            app = TectonApp(app_or_graph)

        payload = app.portal_snapshot()

        # Sanitize serialized JSON against script injection / breakout (e.g., </script>)
        serialized_data = (
            json.dumps(payload, default=str)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
        )
        return PORTAL_HTML_TEMPLATE.replace("__DATA_PAYLOAD__", serialized_data)

    @classmethod
    def export_portal(cls, app_or_graph: Any, output_dir: Path | str) -> Path:
        """Export static portal bundle to target directory."""
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        html_file = target / "index.html"
        html_content = cls.build_static_portal_html(app_or_graph)
        html_file.write_text(html_content, encoding="utf-8")
        return html_file
