"""
ShiVi Explainable Multi-Factor Incident Triage & Priority Scoring
================================================================

Briefing:
    Provides the algorithmic triage and prioritization engine for emergency incidents.
    In mass-casualty or regional disaster events, dozens or hundreds of incidents arrive
    simultaneously. This module computes an objective, transparent, and fully explainable
    numerical priority score in the range [0.0, 100.0] to assist dispatch commanders.

Reason:
    Black-box AI or subjective manual ordering risks triage delays or bias.
    ShiVi uses a multi-factor mathematical formulation where every point in the final score
    is decomposed into transparent contributions:
    1. Severity (Weight: 30 pts): Intrinsic danger to human life (CRITICAL, HIGH, MEDIUM, LOW).
    2. People at Risk (Weight: 25 pts): Diminishing-returns logarithmic curve scaling up to 100 victims.
    3. Urgency & Time Sensitivity (Weight: 15 pts): Progression speed of environmental threat.
    4. Category Vulnerability (Weight: 15 pts): Mission type urgency (RESCUE > MEDICAL > FLOOD > SHELTER > SUPPLY).
    5. Evidence Confidence (Weight: 15 pts): Provenance trust (official responder > photo verified > unverified citizen).
"""

import math
from typing import Dict, Any, Tuple


def calculate_incident_priority(
    severity: str,
    people_at_risk: int,
    category: str,
    urgency_level: str = "HIGH",
    has_photo_evidence: bool = False,
    is_official_source: bool = False,
) -> Tuple[float, Dict[str, Any]]:
    """
    Briefing:
        Calculates a multi-factor incident priority score in [0.0, 100.0] alongside
        a comprehensive breakdown explaining each factor's mathematical contribution.

    Reason:
        Enables dispatchers and algorithms to rank incidents deterministically while
        providing human operators with a plain-English explanation of why an incident
        was ranked at a specific level, avoiding opaque prioritization decisions.

    Formula Breakdown:
        Score = min(100.0, C_sev + C_people + C_urg + C_cat + C_conf)
        - Severity Contribution: Weight 30.0 (CRITICAL=30, HIGH=24, MEDIUM=15, LOW=6)
        - People at Risk Contribution: Weight 25.0 (log10(p + 1) / log10(101) * 25)
        - Urgency Contribution: Weight 15.0 (IMMEDIATE=15, HIGH=11.25, MODERATE=6, LOW=1.5)
        - Category Contribution: Weight 15.0 (RESCUE=15, MEDICAL=13.5, FLOOD=10.5, SHELTER=7.5, SUPPLY=4.5)
        - Confidence Contribution: Weight 15.0 (Official=15, Photo=12.75, Unverified=7.5)

    Parameters:
        severity: Inbound rating ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW').
        people_at_risk: Non-negative count of individuals threatened.
        category: Incident category ('RESCUE', 'MEDICAL', 'FLOOD_HAZARD', 'SHELTER', 'SUPPLY').
        urgency_level: Environmental time sensitivity ('IMMEDIATE', 'HIGH', 'MODERATE', 'LOW').
        has_photo_evidence: True if verified photo proof is attached to the report.
        is_official_source: True if report was submitted by an authenticated first responder or agency.

    Returns:
        A tuple of `(total_score, breakdown_dict)` where `breakdown_dict` contains exact point
        contributions and a human-readable operational justification summary.
    """
    # Explanation: Factor 1 - Severity Contribution (Weight: 30 pts)
    sev_map = {
        "CRITICAL": 1.0,
        "HIGH": 0.8,
        "MEDIUM": 0.5,
        "LOW": 0.2,
    }
    f_sev = sev_map.get(severity.upper(), 0.5)
    w_sev = 30.0
    c_sev = f_sev * w_sev

    # Explanation: Factor 2 - People at Risk Contribution (Weight: 25 pts)
    # Uses logarithmic scaling so 1->10 people increases score dramatically,
    # while 90->100 people scales smoothly without dwarfing other life-safety factors.
    p_clamped = max(0, min(people_at_risk, 100))
    f_people = math.log10(p_clamped + 1) / math.log10(101)
    w_people = 25.0
    c_people = f_people * w_people

    # Explanation: Factor 3 - Urgency & Environmental Time Sensitivity (Weight: 15 pts)
    urg_map = {
        "IMMEDIATE": 1.0,
        "HIGH": 0.75,
        "MODERATE": 0.4,
        "LOW": 0.1,
    }
    f_urg = urg_map.get(urgency_level.upper(), 0.75)
    w_urg = 15.0
    c_urg = f_urg * w_urg

    # Explanation: Factor 4 - Category & Life-Safety Vulnerability (Weight: 15 pts)
    cat_map = {
        "RESCUE": 1.0,
        "MEDICAL": 0.9,
        "FLOOD_HAZARD": 0.7,
        "SHELTER": 0.5,
        "SUPPLY": 0.3,
    }
    f_cat = cat_map.get(category.upper(), 0.5)
    w_cat = 15.0
    c_cat = f_cat * w_cat

    # Explanation: Factor 5 - Evidence & Provenance Confidence (Weight: 15 pts)
    # Higher confidence prevents spoofing or false rumor reports from hijacking rescue convoys.
    if is_official_source:
        f_conf = 1.0
    elif has_photo_evidence:
        f_conf = 0.85
    else:
        f_conf = 0.5
    w_conf = 15.0
    c_conf = f_conf * w_conf

    # Explanation: Sum all contributions, round to 1 decimal place, and cap at 100.0 max
    total_score = min(100.0, round(c_sev + c_people + c_urg + c_cat + c_conf, 1))

    breakdown = {
        "total_score": total_score,
        "severity_contribution": round(c_sev, 1),
        "people_at_risk_contribution": round(c_people, 1),
        "urgency_contribution": round(c_urg, 1),
        "category_contribution": round(c_cat, 1),
        "confidence_contribution": round(c_conf, 1),
        "explanation": f"Score {total_score}/100: Category={category} ({round(c_cat,1)}), Severity={severity} ({round(c_sev,1)}), People={people_at_risk} ({round(c_people,1)})"
    }

    return total_score, breakdown


def calculate_priority_score(
    severity: str,
    category: str = "RESCUE",
    people_at_risk: int = 0,
    **kwargs
) -> float:
    """
    Briefing:
        Convenience wrapper returning just the numeric float priority score.

    Reason:
        Used in sorting pipelines or lightweight checks where detailed mathematical breakdown
        is not required in the immediate calling context.
    """
    score, _ = calculate_incident_priority(
        severity=severity,
        people_at_risk=people_at_risk,
        category=category,
        **kwargs
    )
    return score
