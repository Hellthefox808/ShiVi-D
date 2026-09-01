"""
Tests for ShiVi String Integrity & Unicode Encoding
"""
import pytest
import json
import hashlib
from app.modules.intelligence.gateway import IntelligenceGateway
from app.modules.incidents.priority import calculate_incident_priority
from app.core.security import hash_password, verify_password


def test_unicode_and_special_character_strings():
    # Test Indic Unicode strings and emergency text
    unicode_text = "गुवाहाटी सेक्टर 4 में बाढ़ का पानी बढ़ रहा है। 5 लोग फंसे हैं!"
    res = IntelligenceGateway.extract_structured_incident(unicode_text)
    assert res.estimated_people == 5
    assert res.suggested_title.startswith("गुवाहाटी")


def test_string_hash_deterministic():
    data = "ShiVi-Deterministic-String-Payload-2026"
    hash1 = hashlib.sha256(data.encode("utf-8")).hexdigest()
    hash2 = hashlib.sha256(data.encode("utf-8")).hexdigest()
    assert hash1 == hash2
    assert len(hash1) == 64


def test_password_hash_and_verify_strings():
    pwd = "MySecretComplexPassword!@#$123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_priority_string_case_insensitivity():
    score1, _ = calculate_incident_priority("critical", 5, "rescue", "immediate", is_official_source=True)
    score2, _ = calculate_incident_priority("CRITICAL", 5, "RESCUE", "IMMEDIATE", is_official_source=True)
    assert score1 == score2
