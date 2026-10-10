"""Mermaid Diagram Exporters for Enterprise Architecture Visualizations."""

from typing import Any
from tecton.core.models import Application
from tecton.dsl.schema import TechnologyDef, TechnologyStatus
from tecton.engines.bcm_engine import BCMReport, CapabilityHealth
from tecton.engines.trm_engine import TechnologyRiskItem


class MermaidExporter:
    """Exports architectural models into native Mermaid diagram syntax."""

    @staticmethod
    def to_time_quadrant_chart(
        applications: list[Application], title: str = "Application Portfolio TIME Matrix"
    ) -> str:
        """Generate a Mermaid quadrantChart from applications with suitability scores.

        Normalizes suitability scores (1.0 - 5.0) to coordinates (0.0 - 1.0):
        - X axis: Technical Fit
        - Y axis: Business Fit
        """
        lines = [
            "quadrantChart",
            f"    title {title}",
            "    x-axis Low Technical Fit --> High Technical Fit",
            "    y-axis Low Business Fit --> High Business Fit",
            "    quadrant-1 INVEST",
            "    quadrant-2 TOLERATE",
            "    quadrant-3 ELIMINATE",
            "    quadrant-4 MIGRATE",
        ]

        scored_apps = [
            a for a in applications
            if a.functional_suitability is not None and a.technical_suitability is not None
        ]

        for app in scored_apps:
            # Normalize 1.0 - 5.0 to 0.05 - 0.95 to keep points comfortably within quadrants
            t_norm = (app.technical_suitability - 1.0) / 4.0
            b_norm = (app.functional_suitability - 1.0) / 4.0

            # Clamp between 0.01 and 0.99
            t_norm = max(0.02, min(0.98, t_norm))
            b_norm = max(0.02, min(0.98, b_norm))

            # Escape quotes/colons in application names
            safe_name = app.name.replace(":", " -").replace('"', "")
            lines.append(f"    {safe_name}: [{t_norm:.2f}, {b_norm:.2f}]")

        return "\n".join(lines)

    @staticmethod
    def to_capability_heatmap(
        report: BCMReport, title: str = "Business Capability Realization Heatmap"
    ) -> str:
        """Generate a color-coded Mermaid flowchart displaying the capability tree and health."""
        lines = [
            "flowchart TD",
            f"    %% {title}",
            "    classDef healthy fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724;",
            "    classDef tolerable fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#856404;",
            "    classDef at_risk fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#721c24;",
            "    classDef unmapped fill:#e2e3e5,stroke:#6c757d,stroke-width:2px,stroke-dasharray: 4 4,color:#383d41;",
            "    classDef unknown fill:#d1ecf1,stroke:#17a2b8,stroke-width:2px,color:#0c5460;",
        ]

        def sanitize_id(raw_id: str) -> str:
            return "cap_" + raw_id.replace("-", "_").replace(".", "_")

        # 1. Declare nodes with styles
        for c_id, cov in report.coverages.items():
            nid = sanitize_id(c_id)
            health_class = cov.health.value.lower()
            sys_count = len(cov.realizing_system_ids)
            clean_name = cov.name.replace('"', "'")
            status_text = cov.health.value

            label = f'"{clean_name}<br/><small>Apps: {sys_count} ({status_text})</small>"'
            lines.append(f"    {nid}[{label}]:::{health_class}")

        # 2. Declare parent -> child relations
        for c_id, cov in report.coverages.items():
            if cov.parent_id and cov.parent_id in report.coverages:
                parent_nid = sanitize_id(cov.parent_id)
                child_nid = sanitize_id(c_id)
                lines.append(f"    {parent_nid} --> {child_nid}")

        return "\n".join(lines)

    @staticmethod
    def to_tech_radar_flowchart(
        technologies: list[TechnologyDef] | list[TechnologyRiskItem],
        title: str = "Technology Standards & Obsolescence Radar",
    ) -> str:
        """Generate a grouped Mermaid flowchart visualizing technology standards by category and risk."""
        lines = [
            "flowchart LR",
            f"    %% {title}",
            "    classDef approved fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724;",
            "    classDef under_eval fill:#d1ecf1,stroke:#17a2b8,stroke-width:2px,color:#0c5460;",
            "    classDef deprecated fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#856404;",
            "    classDef prohibited fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#721c24;",
        ]

        def sanitize_id(raw_id: str) -> str:
            return "tech_" + raw_id.replace("-", "_").replace(".", "_")

        # Group by category
        categories: dict[str, list[Any]] = {}
        for t in technologies:
            cat = getattr(t, "category", None) or "General"
            cat_label = cat.replace("_", " ").title()
            categories.setdefault(cat_label, []).append(t)

        for cat_label, items in sorted(categories.items()):
            subgraph_id = "sub_" + cat_label.replace(" ", "_").lower()
            lines.append(f"    subgraph {subgraph_id}[\"{cat_label}\"]")

            for item in items:
                nid = sanitize_id(item.id)
                status_raw = item.status.value if hasattr(item.status, "value") else str(item.status)
                status_class = (
                    "under_eval" if status_raw == "under_evaluation"
                    else status_raw
                )
                eol_flag = " ⚠️ EOL" if getattr(item, "is_eol", False) else ""
                clean_name = item.name.replace('"', "'")
                lines.append(f'        {nid}["{clean_name} ({status_raw.upper()}{eol_flag})"]:::{status_class}')

            lines.append("    end")

        return "\n".join(lines)
