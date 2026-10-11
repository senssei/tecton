"""Static and Dynamic Architecture Portal Generator."""

import functools
import json
from pathlib import Path
from importlib.resources import files
from typing import Any

from tecton_arch.application.app import TectonApp
from tecton_arch.portal.template import PORTAL_HTML_TEMPLATE


class PortalBuilder:
    """Builder for Living Architecture Intelligence Web Portal & Dashboard."""

    @classmethod
    def build_dynamic_portal_html(cls) -> str:
        """Generate dynamic HTML connected to Tecton live REST API endpoints."""
        return cls._template().replace("__DATA_PAYLOAD__", "null")

    @classmethod
    def build_static_portal_html(cls, app_or_graph: Any, as_of_date: Any = None) -> str:
        """Generate HTML snapshot with embedded model data and bundled offline visual assets with pre-baked JSON graph payload."""
        if isinstance(app_or_graph, TectonApp):
            app = app_or_graph
        else:
            app = TectonApp(app_or_graph, as_of_date=as_of_date)

        payload = app.portal_snapshot(as_of_date=as_of_date)

        # Sanitize serialized JSON against script injection / breakout (e.g., </script>)
        serialized_data = (
            json.dumps(payload, default=str)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
        )
        return cls._template().replace("__DATA_PAYLOAD__", serialized_data)

    @classmethod
    def export_portal(cls, app_or_graph: Any, output_dir: Path | str, as_of_date: Any = None) -> Path:
        """Export static portal bundle to target directory."""
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        html_file = target / "index.html"
        html_content = cls.build_static_portal_html(app_or_graph, as_of_date=as_of_date)
        html_file.write_text(html_content, encoding="utf-8")
        return html_file

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _template() -> str:
        assets = files("tecton_arch.portal").joinpath("assets")
        tailwind_script = (
            "/*\n"
            + assets.joinpath("TAILWIND-LICENSE").read_text(encoding="utf-8")
            + "\n*/\n"
            + assets.joinpath("tailwind-3.4.17.min.js").read_text(encoding="utf-8")
        )
        mermaid_script = (
            "/*\n"
            + assets.joinpath("MERMAID-LICENSE").read_text(encoding="utf-8")
            + "\n*/\n"
            + assets.joinpath("mermaid-10.9.8.min.js").read_text(encoding="utf-8")
        )
        scripts = (
            "/*\n"
            + assets.joinpath("D3-LICENSE").read_text(encoding="utf-8")
            + "\n*/\n"
            + "\n".join(
                assets.joinpath(name).read_text(encoding="utf-8")
                for name in ("d3-7.9.0.min.js", "radar.js", "dfd.js", "roadmap.js", "lineage.js")
            )
        )
        return (
            PORTAL_HTML_TEMPLATE.replace("__TAILWIND_SCRIPT__", tailwind_script.replace("</script", "<\\/script"))
            .replace("__MERMAID_SCRIPT__", mermaid_script.replace("</script", "<\\/script"))
            .replace("__RADAR_SCRIPT__", scripts.replace("</script", "<\\/script"))
            .replace("__RADAR_STYLE__", assets.joinpath("radar.css").read_text(encoding="utf-8"))
        )
