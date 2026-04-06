"""Ensure the category registry is consistent and complete."""

import pytest
from services.category_registry import (
    ALL_CATEGORY_KEYS,
    CATEGORY_BY_KEY,
    CATEGORY_REGISTRY,
    RED_CATEGORIES,
    get_explanation,
    get_label,
    get_severity,
)


def test_no_duplicate_keys():
    keys = [c.key for c in CATEGORY_REGISTRY]
    assert len(keys) == len(set(keys)), f"Duplicate keys: {[k for k in keys if keys.count(k) > 1]}"


def test_all_keys_frozenset_matches():
    assert ALL_CATEGORY_KEYS == frozenset(c.key for c in CATEGORY_REGISTRY)


def test_red_categories_subset():
    assert RED_CATEGORIES <= ALL_CATEGORY_KEYS


def test_severities_valid():
    for c in CATEGORY_REGISTRY:
        assert c.severity in ("red", "yellow"), f"{c.key} has invalid severity {c.severity}"


def test_get_label_fallback():
    assert get_label("zombie_renewal") == "Zombie Renewal / Hidden Auto-Renew"
    assert get_label("nonexistent_key") == "Nonexistent Key"


def test_get_severity_fallback():
    assert get_severity("arbitration_waiver") == "red"
    assert get_severity("auto_renewal") == "yellow"
    assert get_severity("nonexistent_key") == "yellow"


def test_all_have_nonempty_fields():
    for c in CATEGORY_REGISTRY:
        assert c.key, "Empty key"
        assert c.label, f"{c.key}: empty label"
        assert c.explanation, f"{c.key}: empty explanation"
