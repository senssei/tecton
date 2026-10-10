"""Mermaid Diagram Exporters for Enterprise Architecture Visualizations."""

from tecton.core.models import Application


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
