"""Declared costs and transparent, undiscounted business cases."""
from decimal import Decimal


def cost_summary(systems):
    totals = {}
    missing = []
    for system in sorted(systems, key=lambda s: s.id):
        if system.annual_cost is None:
            missing.append(system.id)
        else:
            currency = system.annual_cost.currency
            totals[currency] = totals.get(currency, Decimal(0)) + system.annual_cost.amount
    return {"totals_by_currency": {c: str(v) for c, v in sorted(totals.items())}, "systems_with_cost": len(systems)-len(missing), "total_systems": len(systems), "missing_system_ids": missing, "complete": not missing}


def business_cases(graph):
    items = []
    for package in sorted(graph.work_packages.values(), key=lambda p: p.id):
        cost, case = package.planned_cost, package.business_case
        item = {"work_package_id": package.id, "status": "insufficient_data"}
        if cost and case:
            benefit = case.annual_net_savings * case.horizon_years - cost.amount
            roi = benefit / cost.amount * 100 if cost.amount else None
            payback = cost.amount / case.annual_net_savings if case.annual_net_savings > 0 else None
            item.update(status="calculated", currency=cost.currency, planned_cost=str(cost.amount), annual_net_savings=str(case.annual_net_savings), horizon_years=case.horizon_years, net_benefit=str(benefit), roi_percent=str(roi) if roi is not None else None, payback_years=str(payback) if payback is not None else None, assumptions=case.assumptions, calculation_basis="Constant annual net savings from the first year after completion; no discounting")
        items.append(item)
    return {"items": items}
