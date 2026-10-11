"""Checks declared schedules, transition coverage, capacity and monthly budgets."""
from collections import defaultdict
from decimal import Decimal
from tecton_arch.core.config import TectonConfig
from tecton_arch.engines.roadmap_engine import RoadmapEngine


class FeasibilityService:
    def __init__(self, graph, config=None):
        self.graph = graph
        self.config = config or TectonConfig()

    def analyze(self, as_of_date=None):
        issues, missing = [], []
        def issue(rule, entity, message, **details):
            issues.append({"rule": rule, "entity_id": entity, "message": message, **details})
        from tecton_arch.engines.linter import GraphLinter
        structural = GraphLinter().lint(self.graph, as_of_date=as_of_date, config=self.config)
        for finding in structural.issues:
            if finding.severity.value == "ERROR":
                issue(finding.rule, finding.entity_id, finding.message)
        packages = self.graph.work_packages
        resource = defaultdict(lambda: [Decimal(0), set()])
        spending = defaultdict(lambda: [Decimal(0), set()])
        roadmap = RoadmapEngine(self.graph).analyze_roadmap(as_of_date)
        if not roadmap.is_valid_dag:
            issue("ROADMAP_CYCLE", None, "Roadmap contains a cycle")
        for wp in sorted(packages.values(), key=lambda p: p.id):
            if wp.status.value == "CANCELLED":
                continue
            if not wp.start_date or not wp.target_date:
                missing.append({"entity_id": wp.id, "control": "schedule", "reason": "Missing start or target date"})
            elif wp.start_date > wp.target_date:
                issue("SCHEDULE_INVERTED", wp.id, "Start date follows target date")
            for dep_id in wp.depends_on:
                dep = packages.get(dep_id)
                if dep is None or dep.status.value == "CANCELLED":
                    issue("PREREQUISITE_UNAVAILABLE", wp.id, f"Prerequisite {dep_id} is missing or cancelled")
                elif dep.target_date and wp.start_date:
                    if wp.start_date < dep.target_date:
                        issue("PREREQUISITE_NOT_FINISHED", wp.id, f"Starts before prerequisite {dep_id} finishes")
                else:
                    missing.append({"entity_id": wp.id, "control": "dependencies", "reason": f"Missing dates for prerequisite {dep_id}"})
            target = self.graph.plateaus.get(wp.to_plateau_id)
            if wp.to_plateau_id and not target:
                issue("UNKNOWN_TARGET_PLATEAU", wp.id, "Target plateau does not exist")
            if target and target.target_date and wp.target_date and wp.target_date > target.target_date:
                issue("MILESTONE_MISSED", wp.id, "Initiative finishes after target plateau")
            if not wp.resource_allocations:
                missing.append({"entity_id": wp.id, "control": "resources", "reason": "No resource plan"})
            if not wp.spend_plan:
                missing.append({"entity_id": wp.id, "control": "budget", "reason": "No spending plan"})
            for allocation in wp.resource_allocations:
                key = (allocation.team_id, allocation.month)
                resource[key][0] += allocation.person_days
                resource[key][1].add(wp.id)
                if wp.start_date and wp.target_date and not str(wp.start_date)[:7] <= allocation.month <= str(wp.target_date)[:7]:
                    issue("ALLOCATION_OUTSIDE_SCHEDULE", wp.id, "Resource allocation outside schedule", month=allocation.month)
            for spend in wp.spend_plan:
                key = (wp.planned_cost.currency, spend.month)
                spending[key][0] += spend.amount
                spending[key][1].add(wp.id)
                if wp.start_date and wp.target_date and not str(wp.start_date)[:7] <= spend.month <= str(wp.target_date)[:7]:
                    issue("SPEND_OUTSIDE_SCHEDULE", wp.id, "Spending outside schedule", month=spend.month)
        resources, budgets = [], []
        for (team_id, month), (amount, contributors) in sorted(resource.items()):
            team = self.config.teams.get(team_id)
            limit = team.monthly_capacity.get(month, team.capacity_person_days) if team else None
            row = {"team_id": team_id, "month": month, "person_days": str(amount), "capacity_person_days": str(limit) if limit is not None else None, "work_package_ids": sorted(contributors), "status": "not_assessed" if limit is None else "exceeded" if amount > limit else "within_limit"}
            resources.append(row)
            if limit is None:
                missing.append({"entity_id": team_id, "control": "resources", "reason": "Unknown team capacity", "month": month})
            elif amount > limit:
                issue("TEAM_CAPACITY_EXCEEDED", team_id, "Monthly team capacity exceeded", **row)
        for (currency, month), (amount, contributors) in sorted(spending.items()):
            limit = self.config.budgets.get(month, {}).get(currency)
            row = {"currency": currency, "month": month, "planned_spend": str(amount), "budget": str(limit) if limit is not None else None, "work_package_ids": sorted(contributors), "status": "not_assessed" if limit is None else "exceeded" if amount > limit else "within_limit"}
            budgets.append(row)
            if limit is None:
                missing.append({"entity_id": None, "control": "budget", "reason": "No monthly budget limit", "month": month, "currency": currency})
            elif amount > limit:
                issue("BUDGET_EXCEEDED", None, "Monthly budget exceeded", **row)
        if roadmap.is_valid_dag:
            states = {s.plateau_id: s for s in roadmap.plateau_states}
            for plateau in sorted(self.graph.plateaus.values(), key=lambda p: p.id):
                previous = states.get(plateau.previous_plateau_id)
                current = states[plateau.id]
                if not previous:
                    continue
                for cap in sorted(set(previous.covered_capability_ids)-set(current.covered_capability_ids)):
                    issue("CAPABILITY_COVERAGE_LOST", plateau.id, f"Capability {cap} has no replacement in target plateau", capability_id=cap)
                for system_id in sorted(set(current.active_system_ids)-set(previous.active_system_ids)):
                    delivery = [w for w in packages.values() if w.status.value != "CANCELLED" and system_id in w.introduced_system_ids and w.to_plateau_id == plateau.id]
                    if not delivery or not plateau.target_date or not any(w.target_date and w.target_date <= plateau.target_date for w in delivery):
                        missing.append({"entity_id": system_id, "control": "replacement", "reason": f"No dated delivery by plateau {plateau.id}"})
                for system_id in sorted(set(previous.active_system_ids)-set(current.active_system_ids)):
                    retirement = [w for w in packages.values() if w.status.value != "CANCELLED" and system_id in w.decommissioned_system_ids and w.to_plateau_id == plateau.id]
                    if not retirement or not plateau.target_date or not any(w.target_date and w.target_date <= plateau.target_date for w in retirement):
                        missing.append({"entity_id": system_id, "control": "retirement", "reason": f"No retirement initiative for plateau {plateau.id}"})
        if not packages:
            missing.append({"entity_id": None, "control": "plan", "reason": "No initiatives modeled"})
        return {"assessment_status": "violations_detected" if issues else "insufficient_data" if missing else "no_detected_violations", "is_valid_dag": roadmap.is_valid_dag, "issues": issues, "missing_data": missing, "resource_usage": resources, "budget_usage": budgets}
