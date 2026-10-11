"""Bidirectional identifier mapping contract between Tecton domain IDs and external formats."""

import re


class IdCollisionError(ValueError):
    """Raised when external identifier translation results in an ambiguous ID collision."""


class IdMapper:
    """Manages reversible mapping between raw Tecton domain IDs and schema-restricted format IDs."""

    PROPERTY_KEY_XML = "tecton:domain-id"
    PROPERTY_DEF_REF_XML = "propref-tecton-domain-id"
    ANNOTATION_KEY_BACKSTAGE = "tecton.io/domain-id"

    def __init__(self) -> None:
        self._domain_to_xml: dict[str, str] = {}
        self._xml_to_domain: dict[str, str] = {}
        self._domain_to_backstage: dict[str, str] = {}
        self._backstage_to_domain: dict[str, str] = {}

    @staticmethod
    def format_xml_id(raw_id: str) -> str:
        """Sanitize raw ID to strict XML NCName / ID specification (starts with NCName char)."""
        if not raw_id:
            return "id-unspecified"
        clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_id)
        return clean if clean.startswith("id-") else f"id-{clean}"

    @staticmethod
    def format_backstage_name(raw_id: str) -> str:
        """Sanitize raw ID to comply with Backstage Kubernetes DNS-1123 name rules."""
        sanitized = raw_id.lower().replace("_", "-").replace(" ", "-")
        cleaned = re.sub(r"[^a-z0-9\-]", "", sanitized).strip("-")
        return cleaned or "entity"

    def register_xml_id(self, domain_id: str) -> str:
        """Register domain ID and return unique, valid XML NCName identifier."""
        if domain_id in self._domain_to_xml:
            return self._domain_to_xml[domain_id]

        xml_id = self.format_xml_id(domain_id)
        if xml_id in self._xml_to_domain and self._xml_to_domain[xml_id] != domain_id:
            existing = self._xml_to_domain[xml_id]
            raise IdCollisionError(
                f"XML ID collision: '{domain_id}' and '{existing}' both map to '{xml_id}'. "
                "Ensure domain IDs differ sufficiently to remain distinct when sanitized."
            )

        self._domain_to_xml[domain_id] = xml_id
        self._xml_to_domain[xml_id] = domain_id
        return xml_id

    def resolve_domain_id_from_xml(
        self, xml_id: str, property_domain_id: str | None = None
    ) -> str:
        """Resolve raw domain ID from XML identifier and explicit metadata property."""
        if property_domain_id:
            self._xml_to_domain[xml_id] = property_domain_id
            self._domain_to_xml[property_domain_id] = xml_id
            return property_domain_id

        if xml_id in self._xml_to_domain:
            return self._xml_to_domain[xml_id]

        # Stripping synthetic id- prefix if recognized prefix follows
        known_prefixes = ("sys-", "cap-", "tech-", "if-", "data-", "plat-", "wp-", "rel-")
        if xml_id.startswith("id-") and any(xml_id[3:].startswith(p) for p in known_prefixes):
            recovered = xml_id[3:]
            self._xml_to_domain[xml_id] = recovered
            return recovered

        return xml_id

    def register_backstage_name(self, domain_id: str) -> str:
        """Register domain ID and return unique, valid Backstage entity name."""
        if domain_id in self._domain_to_backstage:
            return self._domain_to_backstage[domain_id]

        bs_name = self.format_backstage_name(domain_id)
        if bs_name in self._backstage_to_domain and self._backstage_to_domain[bs_name] != domain_id:
            existing = self._backstage_to_domain[bs_name]
            raise IdCollisionError(
                f"Backstage name collision: '{domain_id}' and '{existing}' both map to '{bs_name}'."
            )

        self._domain_to_backstage[domain_id] = bs_name
        self._backstage_to_domain[bs_name] = domain_id
        return bs_name

    def resolve_domain_id_from_backstage(
        self, bs_name: str, annotation_domain_id: str | None = None
    ) -> str:
        """Resolve raw domain ID from Backstage metadata annotation or name."""
        if annotation_domain_id:
            self._backstage_to_domain[bs_name] = annotation_domain_id
            self._domain_to_backstage[annotation_domain_id] = bs_name
            return annotation_domain_id

        if bs_name in self._backstage_to_domain:
            return self._backstage_to_domain[bs_name]

        return bs_name
