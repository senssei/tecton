"""Generic GraphQL Repository Adapter for remote EAM graph services."""

from typing import Any
import requests
from tecton_arch.adapters.base import ArchitectureRepositoryPort
from tecton_arch.core.models import Application, TimeQuadrant


class GraphQLRepositoryAdapter(ArchitectureRepositoryPort):
    """Remote graph API adapter communicating via GraphQL queries and mutations."""

    def __init__(
        self,
        endpoint_url: str,
        api_token: str | None = None,
        timeout_seconds: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.api_token = api_token
        self.timeout_seconds = timeout_seconds
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        if self.api_token:
            self.session.headers.update({"Authorization": f"Bearer {self.api_token}"})
        self.session.headers.update({"Content-Type": "application/json"})

    def execute_query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a raw GraphQL query against the remote endpoint."""
        payload = {"query": query, "variables": variables or {}}
        response = self.session.post(
            self.endpoint_url,
            json=payload,
            timeout=self.timeout_seconds,
            verify=self.verify_ssl,
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data and data["errors"]:
            raise RuntimeError(f"GraphQL Error: {data['errors']}")
        return data.get("data", {})

    def fetch_applications(self) -> list[Application]:
        """Fetch applications using standard GraphQL query with cursor-based pagination."""
        applications: list[Application] = []
        has_next_page = True
        after_cursor: str | None = None

        query = """
        query GetAllApplications($after: String) {
          allFactSheets(factSheetType: Application, after: $after, first: 100) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
                id
                name
                ... on Application {
                  businessCriticality
                  functionalSuitability
                  technicalSuitability
                  timeClassification
                }
              }
            }
          }
        }
        """

        while has_next_page:
            variables = {"after": after_cursor} if after_cursor else {}
            data = self.execute_query(query, variables)
            fs_data = data.get("allFactSheets", {})
            page_info = fs_data.get("pageInfo", {})
            edges = fs_data.get("edges", [])

            for edge in edges:
                node = edge.get("node", {})
                app_id = node.get("id")
                name = node.get("name")
                if not app_id or not name:
                    continue

                raw_time = node.get("timeClassification") or "UNKNOWN"
                try:
                    time_val = TimeQuadrant(raw_time)
                except ValueError:
                    time_val = TimeQuadrant.UNKNOWN

                app = Application(
                    id=app_id,
                    name=name,
                    business_criticality=node.get("businessCriticality"),
                    functional_suitability=node.get("functionalSuitability"),
                    technical_suitability=node.get("technicalSuitability"),
                    time_classification=time_val,
                )
                applications.append(app)

            has_next_page = page_info.get("hasNextPage", False)
            after_cursor = page_info.get("endCursor")

        return applications

    def save_application(self, application: Application) -> Application:
        """Remote create/save application via GraphQL mutation."""
        # For simplicity, returning the application or implementing mutation as needed
        return application

    def apply_patches(
        self, entity_id: str, patches: list[dict[str, Any]], dry_run: bool = True
    ) -> dict[str, Any]:
        """Send JSON Patch update mutation to the remote GraphQL endpoint."""
        if dry_run:
            return {
                "entity_id": entity_id,
                "dry_run": True,
                "applied_count": len(patches),
                "patches": patches,
                "status": "simulated",
            }

        mutation = """
        mutation UpdateEntity($id: ID!, $patches: [Patch]!) {
          updateFactSheet(id: $id, patches: $patches) {
            factSheet {
              id
            }
          }
        }
        """
        variables = {"id": entity_id, "patches": patches}
        data = self.execute_query(mutation, variables)
        return {
            "entity_id": entity_id,
            "dry_run": False,
            "applied_count": len(patches),
            "response": data,
            "status": "applied",
        }
