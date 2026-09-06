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
    Computes explainable multi-factor priority score P in [0, 100].
    """
    # 1. Severity Factor (Weight: 30)
    sev_map = {
        "CRITICAL": 1.0,
        "HIGH": 0.8,
        "MEDIUM": 0.5,
        "LOW": 0.2,
    }
    f_sev = sev_map.get(severity.upper(), 0.5)
    w_sev = 30.0
    c_sev = f_sev * w_sev

    # 2. People at Risk Factor (Weight: 25)
    # Log scale up to 100 people
    p_clamped = max(0, min(people_at_risk, 100))
    f_people = math.log10(p_clamped + 1) / math.log10(101)
    w_people = 25.0
    c_people = f_people * w_people

    # 3. Urgency & Time Sensitivity (Weight: 15)
    urg_map = {
        "IMMEDIATE": 1.0,
        "HIGH": 0.75,
        "MODERATE": 0.4,
        "LOW": 0.1,
    }
    f_urg = urg_map.get(urgency_level.upper(), 0.75)
    w_urg = 15.0
    c_urg = f_urg * w_urg

    # 4. Category & Life-Safety Vulnerability (Weight: 15)
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

    # 5. Evidence & Provenance Confidence (Weight: 15)
    if is_official_source:
        f_conf = 1.0
    elif has_photo_evidence:
        f_conf = 0.85
    else:
        f_conf = 0.5
    w_conf = 15.0
    c_conf = f_conf * w_conf

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
