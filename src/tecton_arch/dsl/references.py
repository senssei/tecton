"""Shared catalog collection and typed-reference registry."""
COLLECTIONS = {
    "systems": "system", "containers": "container", "capabilities": "capability",
    "technologies": "technology", "interfaces": "interface", "data_objects": "data_object",
    "plateaus": "plateau", "work_packages": "work_package", "data_flow_diagrams": "data_flow_diagram",
}
# Field -> target collection; only schema-declared references, never arbitrary metadata.
REFERENCES = {
    "systems": {"capabilities": "capabilities", "technologies": "technologies"},
    "containers": {"system_id": "systems", "technology": "technologies"},
    "capabilities": {"parent_id": "capabilities"},
    "interfaces": {"provider_system_id": "systems", "consumer_system_ids": "systems", "data_objects": "data_objects"},
    "plateaus": {"previous_plateau_id": "plateaus", "active_system_ids": "systems", "decommissioned_system_ids": "systems"},
    "work_packages": {"from_plateau_id": "plateaus", "to_plateau_id": "plateaus", "involved_system_ids": "systems", "introduced_system_ids": "systems", "decommissioned_system_ids": "systems", "realized_capability_ids": "capabilities", "depends_on": "work_packages"},
    "relationships": {"source_id": "*", "target_id": "*", "data_objects": "data_objects"},
}
SET_FIELDS = {"tags", "capabilities", "technologies", "user_groups", "data_objects", "consumer_system_ids", "active_system_ids", "decommissioned_system_ids", "introduced_system_ids", "involved_system_ids", "realized_capability_ids", "depends_on"}
