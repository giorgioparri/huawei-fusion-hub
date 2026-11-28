"""Disabled source entities: a candidate with no registry state is no candidate.

A registry entry with `disabled_by` set never gets an entity object, so the hub
can discover it by unique_id and resolve it as a candidate forever while never
being able to read a value from it. On a real EMMA install 117 of 172
huawei_solar entities are disabled by the integration itself, and its
`/api/states` holds exactly the 55 enabled ids, so the distinction is not
academic: it decides whether a hub key has a working fallback at all.

Two issues are raised, not one: a key with no working source is a problem, a
dead fallback lane is not. Each carries its own entity list, so each is one
click to fix and the optional one can simply be ignored.
"""
import logging
import os
import sys
from types import SimpleNamespace

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components")
)

import huawei_fusion_hub.coordinator as coordinator_module
from homeassistant.helpers.entity_registry import RegistryEntryDisabler
from huawei_fusion_hub.const import (
    DOMAIN,
    ISSUE_DISABLED_FALLBACK_ENTITIES,
    ISSUE_DISABLED_SOURCE_ENTITIES,
    SOURCE_FUSION_SOLAR_PLUS,
    SOURCE_HUAWEI_SOLAR,
)
from huawei_fusion_hub.coordinator import (
    critical_disabled_candidates,
    disabled_candidate_report,
)
from huawei_fusion_hub.repairs import (
    EnableDisabledEntitiesFlow,
    async_create_fix_flow,
)

DISABLER_INTEGRATION = RegistryEntryDisabler.INTEGRATION
DISABLER_USER = RegistryEntryDisabler.USER


class _RecordingIssueRegistry:
    """Stand-in for homeassistant.helpers.issue_registry."""

    IssueSeverity = SimpleNamespace(WARNING="warning")

    def __init__(self):
        self.created: list[dict] = []
        self.deleted: list[tuple[str, str]] = []

    def async_create_issue(self, hass, domain, issue_id, **kwargs):
        self.created.append(
            {"hass": hass, "domain": domain, "issue_id": issue_id, **kwargs}
        )

    def async_delete_issue(self, hass, domain, issue_id):
        self.deleted.append((domain, issue_id))


def _coordinator_with(disabled_candidates, candidates=None):
    """A coordinator with only what the reporting method touches."""
    coordinator = object.__new__(coordinator_module.HubCoordinator)
    coordinator.hass = SimpleNamespace()
    coordinator.disabled_candidates = disabled_candidates
    coordinator.candidates = (
        candidates
        if candidates is not None
        else {key: dict(per_source) for key, per_source in disabled_candidates.items()}
    )
    return coordinator


def _report(disabled_candidates, candidates=None):
    """Run the report against a recording issue registry."""
    original = coordinator_module.ir
    recorder = _RecordingIssueRegistry()
    coordinator_module.ir = recorder
    try:
        _coordinator_with(disabled_candidates, candidates)._report_disabled_candidates()
    finally:
        coordinator_module.ir = original
    return recorder


def _issues(recorder):
    return {issue["issue_id"]: issue for issue in recorder.created}


def test_reports_only_the_disabled_candidates():
    candidates = {
        "grid_imported_energy": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_total_supply_from_grid",
            SOURCE_FUSION_SOLAR_PLUS: "sensor.fsp_ne_forward_active_energy",
        },
    }
    disabled_by = {
        "sensor.emma_total_supply_from_grid": None,
        "sensor.fsp_ne_forward_active_energy": None,
    }

    assert disabled_candidate_report(candidates, disabled_by) == {}


def test_a_disabled_entity_is_reported_with_its_key_and_source():
    candidates = {
        "battery_rated_capacity": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_rated_ess_capacity",
        },
        "battery_soc": {SOURCE_HUAWEI_SOLAR: "sensor.emma_state_of_capacity"},
    }
    disabled_by = {
        "sensor.emma_rated_ess_capacity": DISABLER_INTEGRATION,
        "sensor.emma_state_of_capacity": None,
    }

    assert disabled_candidate_report(candidates, disabled_by) == {
        "battery_rated_capacity": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_rated_ess_capacity"
        }
    }


def test_entities_disabled_by_the_user_are_not_reported():
    """Turning a source off on purpose must not produce a nag."""
    candidates = {
        "battery_soc": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_state_of_capacity",
            SOURCE_FUSION_SOLAR_PLUS: "sensor.fsp_state_of_charge",
        }
    }
    disabled_by = {
        "sensor.emma_state_of_capacity": DISABLER_USER,
        "sensor.fsp_state_of_charge": DISABLER_INTEGRATION,
    }

    report = disabled_candidate_report(candidates, disabled_by)

    assert report == {"battery_soc": {SOURCE_FUSION_SOLAR_PLUS: "sensor.fsp_state_of_charge"}}


def test_critical_means_every_source_of_that_key_is_disabled():
    candidates = {
        # one healthy source left: a dead lane, not a dead key
        "grid_imported_energy": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_total_supply_from_grid",
            SOURCE_FUSION_SOLAR_PLUS: "sensor.fsp_forward_active_energy",
        },
        # only source is disabled: this key can never resolve
        "total_consumption": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_total_energy_consumption",
        },
    }
    disabled_by = {
        "sensor.emma_total_supply_from_grid": DISABLER_INTEGRATION,
        "sensor.fsp_forward_active_energy": None,
        "sensor.emma_total_energy_consumption": DISABLER_INTEGRATION,
    }
    disabled = disabled_candidate_report(candidates, disabled_by)

    critical = critical_disabled_candidates(candidates, disabled)

    assert set(critical) == {"total_consumption"}


def test_control_proxies_are_never_critical():
    candidates = {"battery_soc": {SOURCE_HUAWEI_SOLAR: "sensor.emma_state_of_capacity"}}
    # a key that is not a sensor candidate at all (a control proxy) must not count
    assert critical_disabled_candidates(candidates, {"inverter_on_off": {"x": "y"}}) == {}


def test_real_emma_install_reports_the_four_disabled_mapping_entities():
    """The EMMA entity set from issue #14, with the four disabled ones."""
    candidates = {
        "grid_imported_energy": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_total_positive_active_energy_2",
        },
        "grid_exported_energy": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_total_negative_active_energy_2",
        },
        "battery_rated_capacity": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_rated_ess_capacity",
        },
        "total_consumption": {
            SOURCE_HUAWEI_SOLAR: "sensor.emma_total_energy_consumption",
        },
        "battery_soc": {SOURCE_HUAWEI_SOLAR: "sensor.emma_state_of_capacity"},
        "pv_active_power": {SOURCE_HUAWEI_SOLAR: "sensor.emma_inverter_active_power"},
    }
    disabled_by = {
        "sensor.emma_total_positive_active_energy_2": DISABLER_INTEGRATION,
        "sensor.emma_total_negative_active_energy_2": DISABLER_INTEGRATION,
        "sensor.emma_rated_ess_capacity": DISABLER_INTEGRATION,
        "sensor.emma_total_energy_consumption": DISABLER_INTEGRATION,
        "sensor.emma_state_of_capacity": None,
        "sensor.emma_inverter_active_power": None,
    }

    report = disabled_candidate_report(candidates, disabled_by)

    assert set(report) == {
        "grid_imported_energy",
        "grid_exported_energy",
        "battery_rated_capacity",
        "total_consumption",
    }


def test_a_dead_fallback_lane_gets_the_optional_issue_only():
    """The common case: another source works, so nothing is broken today."""
    recorder = _report(
        {"grid_imported_energy": {SOURCE_HUAWEI_SOLAR: "sensor.emma_a"}},
        candidates={
            "grid_imported_energy": {
                SOURCE_HUAWEI_SOLAR: "sensor.emma_a",
                SOURCE_FUSION_SOLAR_PLUS: "sensor.fsp_a",
            }
        },
    )
    issues = _issues(recorder)
    assert ISSUE_DISABLED_SOURCE_ENTITIES not in issues
    fallback = issues[ISSUE_DISABLED_FALLBACK_ENTITIES]
    assert fallback["data"]["entities"] == "sensor.emma_a"
    assert fallback["is_fixable"] is True


def test_a_broken_key_gets_the_source_issue():
    recorder = _report(
        {"total_consumption": {SOURCE_HUAWEI_SOLAR: "sensor.emma_total_consumption"}}
    )
    issues = _issues(recorder)
    assert set(issues) == {ISSUE_DISABLED_SOURCE_ENTITIES}
    issue = issues[ISSUE_DISABLED_SOURCE_ENTITIES]
    assert issue["translation_key"] == ISSUE_DISABLED_SOURCE_ENTITIES
    assert issue["is_fixable"] is True
    assert issue["severity"] == "warning"
    assert issue["translation_placeholders"]["count"] == "1"
    assert issue["translation_placeholders"]["keys"] == "1"
    assert "sensor.emma_total_consumption" in issue["data"]["entities"]
    assert issue["learn_more_url"].endswith("#disabled-source-entities")


def test_issue_lists_distinct_entities_even_when_a_source_feeds_several_keys():
    """One entity can be the candidate of several keys; the issue lists it once."""
    recorder = _report(
        {
            "a": {SOURCE_HUAWEI_SOLAR: "sensor.shared"},
            "b": {SOURCE_HUAWEI_SOLAR: "sensor.shared"},
        }
    )
    issue = _issues(recorder)[ISSUE_DISABLED_SOURCE_ENTITIES]
    assert issue["data"]["entities"] == "sensor.shared"
    assert issue["translation_placeholders"]["count"] == "1"
    assert issue["translation_placeholders"]["keys"] == "2"


def test_both_issues_are_deleted_once_nothing_is_disabled():
    recorder = _report({})
    assert recorder.created == []
    assert recorder.deleted == [
        (DOMAIN, ISSUE_DISABLED_SOURCE_ENTITIES),
        (DOMAIN, ISSUE_DISABLED_FALLBACK_ENTITIES),
    ]


def test_the_report_warns_in_the_log_as_well():
    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = _Capture()
    coordinator_module._LOGGER.addHandler(handler)
    try:
        _report({"battery_soc": {SOURCE_HUAWEI_SOLAR: "sensor.bma_state_of_capacity"}})
    finally:
        coordinator_module._LOGGER.removeHandler(handler)

    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    message = records[0].getMessage()
    assert "1 with no working source left" in message


def test_the_fix_flow_lists_one_entity_per_line():
    flow = EnableDisabledEntitiesFlow({"entities": "a\nb\n\nc"})
    assert flow._entity_ids == ["a", "b", "c"]


def test_every_disabled_issue_gets_the_custom_flow():
    import asyncio

    for issue_id in (ISSUE_DISABLED_SOURCE_ENTITIES, ISSUE_DISABLED_FALLBACK_ENTITIES):
        flow = asyncio.run(
            async_create_fix_flow(None, issue_id, {"entities": "sensor.a"})
        )
        assert isinstance(flow, EnableDisabledEntitiesFlow), issue_id


if __name__ == "__main__":
    import traceback

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception:
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
            failed += 1
    sys.exit(1 if failed else 0)
