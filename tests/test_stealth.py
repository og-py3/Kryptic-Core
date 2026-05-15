"""
Tests for StealthProfile.
"""
import pytest
from kryptic.stealth import StealthProfile, random_profile, USER_AGENTS, VIEWPORTS


def test_profile_defaults():
    p = StealthProfile()
    assert p.level == "medium"
    assert p.user_agent in USER_AGENTS
    assert p.viewport in VIEWPORTS


def test_profile_levels():
    for level in ("low", "medium", "high"):
        p = StealthProfile(level=level)
        assert p.level == level


def test_invalid_level():
    with pytest.raises(ValueError):
        StealthProfile(level="extreme")


def test_context_options():
    p = StealthProfile(level="high")
    opts = p.context_options()
    assert "user_agent" in opts
    assert "viewport" in opts
    assert "locale" in opts
    assert "timezone_id" in opts


def test_random_profile():
    p = random_profile("high")
    assert isinstance(p, StealthProfile)
    assert p.level == "high"


def test_random_user_agent_changes():
    p = StealthProfile()
    original = p.user_agent
    # Randomly may or may not change — just ensure it returns a valid UA
    new_ua = p.random_user_agent()
    assert new_ua in USER_AGENTS
