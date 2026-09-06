"""
Tests for ShiVi Explainable Multi-Factor Priority Algorithm
"""
import pytest
from app.modules.incidents.priority import calculate_incident_priority


def test_critical_rescue_high_people_score():
    score, breakdown = calculate_incident_priority(
        severity="CRITICAL",
        people_at_risk=20,
        urgency_level="IMMEDIATE",
        category="RESCUE",
        is_official_source=True,
    )
    # Critical (30) + People (log10(21)/log10(101)*25 ~ 16.5) + Urgency (15) + Rescue (15) + Official (15) = ~91.5
    assert score >= 85.0
    assert score <= 100.0
    assert breakdown["severity_contribution"] == 30.0
    assert breakdown["urgency_contribution"] == 15.0
    assert breakdown["category_contribution"] == 15.0
    assert breakdown["confidence_contribution"] == 15.0


def test_low_supply_zero_people_score():
    score, breakdown = calculate_incident_priority(
        severity="LOW",
        people_at_risk=0,
        urgency_level="LOW",
        category="SUPPLY",
        is_official_source=False,
    )
    # Low (6) + People (0) + Urgency (1.5) + Supply (4.5) + Unverified (7.5) = 19.5
    assert score <= 25.0
    assert breakdown["severity_contribution"] == 6.0
    assert breakdown["people_at_risk_contribution"] == 0.0
    assert breakdown["urgency_contribution"] == 1.5
    assert breakdown["category_contribution"] == 4.5
    assert breakdown["confidence_contribution"] == 7.5


def test_score_never_exceeds_100():
    score, _ = calculate_incident_priority(
        severity="CRITICAL",
        people_at_risk=1000,
        urgency_level="IMMEDIATE",
        category="RESCUE",
        is_official_source=True,
    )
    assert score == 100.0
