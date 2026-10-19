"""Tests for the notice about the next minimum Home Assistant version.

Standalone, in the same style as test_normalize.py: run with
`python tests/test_min_ha_notice.py`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))

from homeassistant.const import MAJOR_VERSION, MINOR_VERSION
from huawei_fusion_hub.const import NEXT_MIN_HA_VERSION, ha_below_next_minimum


def test_releases_before_the_minimum_get_the_notice():
    assert ha_below_next_minimum(2026, 3)
    assert ha_below_next_minimum(2026, 7)


def test_minimum_and_later_releases_do_not():
    assert not ha_below_next_minimum(2026, 8)
    assert not ha_below_next_minimum(2026, 10)
    assert not ha_below_next_minimum(2026, 12)


def test_the_year_decides_before_the_month():
    """A plain minor comparison would get both of these wrong."""
    assert ha_below_next_minimum(2025, 12)
    assert not ha_below_next_minimum(2027, 1)


def test_works_with_the_installed_home_assistant_constants():
    """The names the integration will read at setup exist and are integers."""
    assert isinstance(MAJOR_VERSION, int) and isinstance(MINOR_VERSION, int)
    assert isinstance(ha_below_next_minimum(MAJOR_VERSION, MINOR_VERSION), bool)
    assert NEXT_MIN_HA_VERSION == (2026, 8)


def _run():
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
        except AssertionError as err:
            failures += 1
            print(f"FAIL {name}: {err}")
        else:
            print(f"PASS {name}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
