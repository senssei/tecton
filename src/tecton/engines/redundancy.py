"""Redundancy Detection Engine using weighted Jaccard similarity metrics."""

from tecton.core.models import Application, RedundancyCluster, RedundancyConfig


class RedundancyDetectionEngine:
    """Detects functional and organizational redundancy in application portfolios."""

    def __init__(self, config: RedundancyConfig | None = None) -> None:
        self.config = config or RedundancyConfig()

    def calculate_similarity(
        self, app_a: Application, app_b: Application
    ) -> tuple[float, list[str], list[str]]:
        """Calculate weighted Jaccard similarity between two applications.

        Returns:
            (similarity_score, shared_capabilities, shared_user_groups)
        """
        caps_a = set(app_a.capabilities)
        caps_b = set(app_b.capabilities)
        shared_caps = sorted(caps_a & caps_b)
        all_caps = caps_a | caps_b
        jaccard_caps = len(shared_caps) / len(all_caps) if all_caps else 0.0

        users_a = set(app_a.user_groups)
        users_b = set(app_b.user_groups)
        shared_users = sorted(users_a & users_b)
        all_users = users_a | users_b
        jaccard_users = len(shared_users) / len(all_users) if all_users else 0.0

        # Adjust weights if one of the dimensions has no data
        w_c = self.config.capability_weight
        w_u = self.config.user_group_weight

        if not all_caps and not all_users:
            return 0.0, [], []
        elif not all_caps:
            weighted_score = jaccard_users
        elif not all_users:
            weighted_score = jaccard_caps
        else:
            weighted_score = (w_c * jaccard_caps) + (w_u * jaccard_users)

        return round(weighted_score, 4), shared_caps, shared_users

    def find_redundancies(self, applications: list[Application]) -> list[RedundancyCluster]:
        """Exhaustively compare all application pairs and cluster redundant systems."""
        clusters: list[RedundancyCluster] = []
        n = len(applications)

        for i in range(n):
            for j in range(i + 1, n):
                app_a = applications[i]
                app_b = applications[j]

                sim, shared_caps, shared_users = self.calculate_similarity(app_a, app_b)

                if sim >= self.config.similarity_threshold:
                    cluster_id = f"RED-{app_a.id[:8]}-{app_b.id[:8]}"
                    recommendation = self._generate_recommendation(
                        app_a, app_b, sim, shared_caps, shared_users
                    )

                    clusters.append(
                        RedundancyCluster(
                            cluster_id=cluster_id,
                            application_ids=[app_a.id, app_b.id],
                            application_names=[app_a.name, app_b.name],
                            similarity_score=sim,
                            shared_capabilities=shared_caps,
                            shared_user_groups=shared_users,
                            recommendation=recommendation,
                        )
                    )

        # Sort clusters by highest similarity first
        return sorted(clusters, key=lambda c: c.similarity_score, reverse=True)

    def _generate_recommendation(
        self,
        app_a: Application,
        app_b: Application,
        sim: float,
        shared_caps: list[str],
        shared_users: list[str],
    ) -> str:
        """Formulate actionable rationalization recommendation."""
        # Determine stronger candidate based on suitability
        score_a = (app_a.functional_suitability or 0) + (app_a.technical_suitability or 0)
        score_b = (app_b.functional_suitability or 0) + (app_b.technical_suitability or 0)

        caps_desc = f"{len(shared_caps)} capabilities" if shared_caps else "overlapping functions"
        users_desc = f"in {', '.join(shared_users)}" if shared_users else "across the organization"

        if score_a > score_b:
            preferred, redundant = app_a.name, app_b.name
        elif score_b > score_a:
            preferred, redundant = app_b.name, app_a.name
        else:
            return (
                f"Overlap of {sim*100:.1f}% across {caps_desc} {users_desc}. "
                f"Consider consolidating {app_a.name} and {app_b.name}."
            )

        return (
            f"High functional overlap ({sim*100:.1f}%) on {caps_desc} {users_desc}. "
            f"Recommend consolidating {redundant} into higher-scoring {preferred}."
        )
