"""Mermaid Diagram Exporters for Enterprise Architecture Visualizations."""

from typing import Any
from html import escape
from datetime import date
from tecton_arch.core.models import Application
from tecton_arch.dsl.schema import PlateauDef, TechnologyDef, TechnologyStatus, WorkPackageDef, WorkPackageStatus
from tecton_arch.engines.bcm_engine import BCMReport, CapabilityHealth
from tecton_arch.engines.trm_engine import TechnologyRiskItem


class MermaidExporter:
    """Exports architectural models into native Mermaid diagram syntax."""

    @staticmethod
    def to_time_quadrant_chart(
        applications: list[Application], title: str = "Application Portfolio TIME Matrix", time_config=None
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

        def coordinate(score, threshold):
            if score >= threshold:
                return .5 + .48 * (score-threshold) / (5-threshold) if threshold < 5 else .5
            return .02 + .48 * (score-1) / (threshold-1) if threshold > 1 else .5
        for app in scored_apps:
            # Normalize 1.0 - 5.0 to 0.05 - 0.95 to keep points comfortably within quadrants
            t_norm = coordinate(app.technical_suitability, time_config.technical_threshold) if time_config else (app.technical_suitability - 1.0) / 4.0
            b_norm = coordinate(app.functional_suitability, time_config.business_threshold) if time_config else (app.functional_suitability - 1.0) / 4.0

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

    @staticmethod
    def to_data_lineage_flowchart(
        report: Any,
        title: str = "Data Lineage Trajectory",
    ) -> str:
        """Generate a Mermaid flowchart illustrating the end-to-end lineage of a data object."""
        lines = [
            "flowchart LR",
            f"    %% {title} - {report.data_object_name} ({report.classification.value})",
            "    classDef producer fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724;",
            "    classDef consumer fill:#d1ecf1,stroke:#17a2b8,stroke-width:2px,color:#0c5460;",
            "    classDef node_default fill:#f8f9fa,stroke:#6c757d,stroke-width:2px,color:#212529;",
        ]

        def sanitize_id(raw_id: str) -> str:
            return "sys_" + raw_id.replace("-", "_").replace(".", "_")

        names = {}
        for edge in report.flow_edges:
            names[edge.source_system_id] = edge.source_system_name
            names[edge.target_system_id] = edge.target_system_name
        senders = {edge.source_system_id for edge in report.flow_edges}
        receivers = {edge.target_system_id for edge in report.flow_edges}

        # Declare nodes with readable names and their role in this data flow.
        for s_id in report.participating_systems:
            nid = sanitize_id(s_id)
            node_class = (
                "producer" if s_id in report.producers
                else "consumer" if s_id in report.consumers
                else "node_default"
            )
            role = "Receives and sends data" if s_id in senders and s_id in receivers else "Sends data" if s_id in senders else "Receives data"
            label = escape(names.get(s_id, s_id), quote=True)
            lines.append(f'    {nid}["{label}<br/>{role}"]:::{node_class}')

        # Declare edges
        channels: dict[tuple[str, str], list[str]] = {}
        for edge in report.flow_edges:
            key = (edge.source_system_id, edge.target_system_id)
            label = f"{escape(edge.channel_name, quote=True)}<br/>({escape(edge.protocol, quote=True)})"
            if label not in channels.setdefault(key, []):
                channels[key].append(label)
        for (source, target), labels in channels.items():
            src = sanitize_id(source)
            dst = sanitize_id(target)
            edge_label = "<br/>".join(labels)
            lines.append(f'    {src} -->|"{edge_label}"| {dst}')

        return "\n".join(lines)

    @staticmethod
    def to_roadmap_gantt(
        plateaus: list[PlateauDef],
        work_packages: list[WorkPackageDef],
        title: str = "Enterprise Architecture Transformation Roadmap",
        as_of_date: date | None = None,
    ) -> str:
        """Generate a Mermaid Gantt diagram visualizing plateaus milestones and work package schedule."""
        today_val = as_of_date or date.today()
        lines: list[str] = [
            "gantt",
            f"    title {title}",
            "    dateFormat YYYY-MM-DD",
            "    axisFormat %Y-%m",
        ]

        if plateaus:
            lines.append("    section Plateaus")
            if as_of_date:
                lines.append(f"    Evaluation Date :milestone, eval_date, {as_of_date}, 0d")
            for p in plateaus:
                date_str = str(p.target_date) if p.target_date else str(today_val)
                safe_name = p.name.replace(":", " -")
                lines.append(f"    {safe_name} :milestone, {p.id}, {date_str}, 0d")

        if work_packages:
            lines.append("    section Work Packages")
            wps_sorted = sorted(
                work_packages,
                key=lambda w: (
                    0 if w.start_date else 1,
                    str(w.start_date) if w.start_date else "9999-99-99",
                ),
            )
            for wp in wps_sorted:
                safe_name = wp.name.replace(":", " -")
                status_modifier = ""
                if wp.status == WorkPackageStatus.COMPLETED:
                    status_modifier = "done, "
                elif wp.status == WorkPackageStatus.IN_PROGRESS:
                    status_modifier = "active, "
                elif wp.status == WorkPackageStatus.CANCELLED:
                    status_modifier = "crit, "

                if wp.depends_on:
                    dep_id = wp.depends_on[0]
                    duration = "30d"
                    if wp.start_date and wp.target_date:
                        days = (wp.target_date - wp.start_date).days
                        duration = f"{max(days, 1)}d"
                    lines.append(f"    {safe_name} :{status_modifier}{wp.id}, after {dep_id}, {duration}")
                elif wp.start_date and wp.target_date:
                    lines.append(f"    {safe_name} :{status_modifier}{wp.id}, {wp.start_date}, {wp.target_date}")
                elif wp.start_date:
                    lines.append(f"    {safe_name} :{status_modifier}{wp.id}, {wp.start_date}, 30d")
                else:
                    lines.append(f"    {safe_name} :{status_modifier}{wp.id}, {today_val}, 30d")

        return "\n".join(lines)

