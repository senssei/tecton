"""Catalog review reporting and isolated, validated ID refactoring."""
from datetime import date, timedelta
from pathlib import Path
import json
import tempfile
import shutil
import os
import yaml
from tecton_arch.core.config import TectonConfig
from tecton_arch.dsl.parser import C4EAMParser
from tecton_arch.dsl.references import COLLECTIONS, REFERENCES


def catalog_document(graph):
    document = {key: [entity.model_dump(mode="json") for entity in sorted(getattr(graph, key).values(), key=lambda e: e.id)] for key in COLLECTIONS}
    document["relationships"] = [r.model_dump(mode="json") for r in graph.relationships]
    return document


class CatalogService:
    def __init__(self, graph, config=None):
        self.graph = graph
        self.config = config or TectonConfig()

    def freshness(self, as_of_date=None):
        target = as_of_date or date.today()
        items = []
        for collection in [*COLLECTIONS, "relationships"]:
            entities = getattr(self.graph, collection)
            entities = entities if isinstance(entities, list) else entities.values()
            for index, entity in enumerate(entities):
                review = entity.review
                due = None
                status = "missing"
                if review and review.reviewed_on:
                    due = review.next_review_on or review.reviewed_on + timedelta(days=self.config.quality.review_valid_days)
                    status = "future_dated" if review.reviewed_on > target else "overdue" if due < target else "current"
                items.append({"entity_type": collection, "entity_id": getattr(entity, "id", f"relationship:{index}"), "owner": getattr(entity, "owner", None), "reviewed_on": str(review.reviewed_on) if review and review.reviewed_on else None, "reviewed_by": review.reviewed_by if review else None, "next_review_on": str(due) if due else None, "status": status, "reason": {"missing": "No dated review", "current": "Review is current", "overdue": "Review deadline has passed", "future_dated": "Review date is in the future"}[status]})
        return {"as_of_date": str(target), "items": items, "needs_review": sum(i["status"] != "current" for i in items)}

    def rename(self, old_id, new_id, source, output=None):
        if not new_id.strip() or new_id != new_id.strip() or old_id == new_id:
            raise ValueError("New ID must be nonblank, trimmed and different")
        ids = self.graph.all_symbol_ids()
        if old_id not in ids or new_id in ids:
            raise ValueError("Old ID does not exist or new ID already exists")
        from tecton_arch.engines.linter import GraphLinter
        if not GraphLinter().lint(self.graph).is_valid:
            raise ValueError("Source catalog must pass structural validation before refactoring")
        document = catalog_document(self.graph)
        collection = next(key for key in COLLECTIONS if old_id in getattr(self.graph, key))
        changes, warnings = [], []

        def change(record, field, path):
            value = record.get(field)
            replaced = [new_id if v == old_id else v for v in value] if isinstance(value, list) else new_id if value == old_id else value
            if replaced != value:
                record[field] = replaced
                changes.append(path)

        for key, records in document.items():
            for i, record in enumerate(records):
                if key == collection and record.get("id") == old_id:
                    change(record, "id", f"{key}[{i}].id")
                for field, target in REFERENCES.get(key, {}).items():
                    if target in (collection, "*"):
                        change(record, field, f"{key}[{i}].{field}")
                if key == "data_flow_diagrams":
                    if collection == "systems":
                        for j, node in enumerate(record["nodes"]):
                            change(node, "system_id", f"{key}[{i}].nodes[{j}].system_id")
                    if collection == "data_objects":
                        for j, flow in enumerate(record["flows"]):
                            change(flow, "data_objects", f"{key}[{i}].flows[{j}].data_objects")
                if old_id in json.dumps(record.get("metadata", {})):
                    warnings.append(f"{key}[{i}].metadata: inspect occurrences of {old_id}")
        config_data = self.config.model_dump(mode="json")
        config_data["manifests"] = {"include": ["catalog.yaml"], "exclude": []}
        output_config = TectonConfig.model_validate(config_data)
        parser = C4EAMParser(config=output_config, strict=True)
        candidate = parser.parse_content(yaml.safe_dump(document, sort_keys=False), file_origin="catalog.yaml")
        report = GraphLinter().lint(candidate)
        if not report.is_valid:
            raise ValueError("Refactored catalog failed validation: " + "; ".join(i.message for i in report.issues if i.severity.value == "ERROR"))
        result = {"old_id": old_id, "new_id": new_id, "changes": changes, "references_changed": len(changes)-1, "warnings": warnings, "valid": True, "output_path": None}
        if output:
            target = Path(output).resolve()
            source_path = Path(source).resolve()
            if target.exists() or target == source_path or source_path in target.parents or target in source_path.parents:
                raise ValueError("Output must not exist and must be separate from source")
            target.parent.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix=".tecton-rename-", dir=target.parent))
            try:
                (staging / "catalog.yaml").write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
                (staging / "tecton.yaml").write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
                validated = parser.parse_directory(staging)
                if not GraphLinter().lint(validated).is_valid:
                    raise ValueError("Written catalog failed validation")
                if target.exists():
                    raise FileExistsError(target)
                os.rename(staging, target)
                result["output_path"] = str(target)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)
        return result
