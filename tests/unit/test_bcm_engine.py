"""Unit tests for Business Capability Management (BCM) Engine."""

from tecton.core.models import Application, TimeQuadrant
from tecton.dsl.schema import BusinessCapabilityDef
from tecton.engines.bcm_engine import BCMEngine, CapabilityHealth


def test_bcm_engine_coverage_and_gap_detection():
    caps = [
        BusinessCapabilityDef(id="cap-1", name="Order Processing", level="L1"),
        BusinessCapabilityDef(id="cap-2", name="Payment Gateway", level="L2", parent_id="cap-1"),
        BusinessCapabilityDef(id="cap-3", name="AI Analytics", level="L1"),  # Orphaned gap
    ]

    apps = [
        Application(
            id="app-1",
            name="Checkout App",
            time_classification=TimeQuadrant.INVEST,
            capabilities=["cap-1", "cap-2"],
        ),
        Application(
            id="app-2",
            name="Billing Engine",
            time_classification=TimeQuadrant.INVEST,
            capabilities=["cap-2"],
        ),
    ]

    engine = BCMEngine(hotspot_threshold=2)
    report = engine.analyze(caps, apps)

    assert report.total_capabilities == 3
    assert report.mapped_capabilities == 2
    assert report.orphaned_capabilities == ["cap-3"]
    assert report.overprovisioned_capabilities == ["cap-2"]  # 2 apps >= threshold 2
    assert round(report.coverage_percentage, 1) == 66.7

    # cap-1 has 1 INVEST app -> HEALTHY
    assert report.coverages["cap-1"].health == CapabilityHealth.HEALTHY
    # cap-3 has 0 apps -> UNMAPPED
    assert report.coverages["cap-3"].health == CapabilityHealth.UNMAPPED


def test_bcm_engine_at_risk_health_derivation():
    caps = [BusinessCapabilityDef(id="cap-legacy", name="Legacy Accounts", level="L1")]
    apps = [
        Application(
            id="app-old",
            name="Old System",
            time_classification=TimeQuadrant.ELIMINATE,
            capabilities=["cap-legacy"],
        ),
    ]

    engine = BCMEngine()
    report = engine.analyze(caps, apps)

    assert report.coverages["cap-legacy"].health == CapabilityHealth.AT_RISK
