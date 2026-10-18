"""Regression test for EMMA (Modbus) unique_id matching — issue #14.

The unique_id list below is the real set reported in #14 by
@HairyPorter23 (EMMA / SA4H-A02, huawei_solar 2.1.5) — serial masked
upstream as BTXXXXXXXXXX. Before the EMMA-pattern fix only 2 of these
64 entities resolve to a hub sensor; this test locks in the improved
coverage and should be bumped, never lowered, as more EMMA keys are
mapped (meter phase channels, ESS capacity/energy, backup SOC are
still open — see the TODO in mapping.py).
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components")
)

from huawei_fusion_hub.coordinator import HubCoordinator
from huawei_fusion_hub.mapping import SENSOR_DEFS_BY_KEY
from huawei_fusion_hub.const import SOURCE_HUAWEI_SOLAR as HS

EMMA_UNIQUE_IDS = [
    "BTXXXXXXXXXX_inverter_total_absorbed_energy",
    "BTXXXXXXXXXX_energy_charged_today",
    "BTXXXXXXXXXX_total_charged_energy",
    "BTXXXXXXXXXX_energy_discharged_today",
    "BTXXXXXXXXXX_total_discharged_energy",
    "BTXXXXXXXXXX_ess_chargeable_energy",
    "BTXXXXXXXXXX_ess_dischargeable_energy",
    "BTXXXXXXXXXX_rated_ess_capacity",
    "BTXXXXXXXXXX_consumption_today",
    "BTXXXXXXXXXX_total_energy_consumption",
    "BTXXXXXXXXXX_feed_in_to_grid_today",
    "BTXXXXXXXXXX_total_feed_in_to_grid",
    "BTXXXXXXXXXX_supply_from_grid_today",
    "BTXXXXXXXXXX_total_supply_from_grid",
    "BTXXXXXXXXXX_inverter_energy_yield_today",
    "BTXXXXXXXXXX_inverter_total_energy_yield",
    "BTXXXXXXXXXX_pv_yield_today",
    "BTXXXXXXXXXX_total_pv_energy_yield",
    "BTXXXXXXXXXX_pv_output_power",
    "BTXXXXXXXXXX_load_power",
    "BTXXXXXXXXXX_feed_in_power",
    "BTXXXXXXXXXX_battery_charge_discharge_power",
    "BTXXXXXXXXXX_inverter_rated_power",
    "BTXXXXXXXXXX_inverter_active_power",
    "BTXXXXXXXXXX_state_of_capacity",
    "BTXXXXXXXXXX_ess_chargeable_capacity",
    "BTXXXXXXXXXX_ess_dischargeable_capacity",
    "BTXXXXXXXXXX_backup_power_state_of_charge",
    "BTXXXXXXXXXX_phase_a_voltage_built_in_energy",
    "BTXXXXXXXXXX_phase_b_voltage_built_in_energy",
    "BTXXXXXXXXXX_phase_c_voltage_built_in_energy",
    "BTXXXXXXXXXX_line_voltage_a_b_built_in_energy",
    "BTXXXXXXXXXX_line_voltage_b_c_built_in_energy",
    "BTXXXXXXXXXX_line_voltage_c_a_built_in_energy",
    "BTXXXXXXXXXX_phase_a_current_built_in_energy",
    "BTXXXXXXXXXX_phase_b_current_built_in_energy",
    "BTXXXXXXXXXX_phase_c_current_built_in_energy",
    "BTXXXXXXXXXX_active_power_built_in_energy",
    "BTXXXXXXXXXX_power_factor_built_in_energy",
    "BTXXXXXXXXXX_apparent_power_built_in_energy",
    "BTXXXXXXXXXX_phase_a_active_power_built_in_energy",
    "BTXXXXXXXXXX_phase_b_active_power_built_in_energy",
    "BTXXXXXXXXXX_phase_c_active_power_built_in_energy",
    "BTXXXXXXXXXX_total_active_energy_built_in_energy",
    "BTXXXXXXXXXX_total_negative_active_energy_built_in_energy",
    "BTXXXXXXXXXX_total_positive_active_energy_built_in_energy",
    "BTXXXXXXXXXX_phase_a_voltage_external_energy",
    "BTXXXXXXXXXX_phase_b_voltage_external_energy",
    "BTXXXXXXXXXX_phase_c_voltage_external_energy",
    "BTXXXXXXXXXX_line_voltage_a_b_external_energy",
    "BTXXXXXXXXXX_line_voltage_b_c_external_energy",
    "BTXXXXXXXXXX_line_voltage_c_a_external_energy",
    "BTXXXXXXXXXX_phase_a_current_external_energy",
    "BTXXXXXXXXXX_phase_b_current_external_energy",
    "BTXXXXXXXXXX_phase_c_current_external_energy",
    "BTXXXXXXXXXX_active_power_external_energy",
    "BTXXXXXXXXXX_power_factor_external_energy",
    "BTXXXXXXXXXX_apparent_power_external_energy",
    "BTXXXXXXXXXX_phase_a_active_power_external_energy",
    "BTXXXXXXXXXX_phase_b_active_power_external_energy",
    "BTXXXXXXXXXX_phase_c_active_power_external_energy",
    "BTXXXXXXXXXX_total_active_energy_external_energy",
    "BTXXXXXXXXXX_total_negative_active_energy_external_energy",
    "BTXXXXXXXXXX_total_positive_active_energy_external_energy",
]


def _entities():
    return [
        (SimpleNamespace(unique_id=uid, entity_id=f"sensor.emma_{i}"), None)
        for i, uid in enumerate(EMMA_UNIQUE_IDS)
    ]


# hub sensor key -> unique_id suffix it must resolve to, post-fix.
# The first two were already matching before this fix (kept as a
# baseline so a future change can't silently break them).
EXPECTED = {
    "inverter_rated_power": "inverter_rated_power",
    "pv_active_power": "inverter_active_power",
    "battery_soc": "state_of_capacity",
    "battery_power": "battery_charge_discharge_power",
    "battery_charged_today": "energy_charged_today",
    "battery_discharged_today": "energy_discharged_today",
    "battery_total_charge": "total_charged_energy",
    "battery_total_discharge": "total_discharged_energy",
    "battery_rated_capacity": "rated_ess_capacity",
    "pv_input_power": "pv_output_power",
    "inverter_yield_today": "inverter_energy_yield_today",
    "inverter_yield_total": "inverter_total_energy_yield",
    "consumption_today": "consumption_today",
    "pv_feed_in_energy_today": "feed_in_to_grid_today",
    "imported_grid_energy_today": "supply_from_grid_today",
    "total_consumption": "total_energy_consumption",
}


def test_emma_keys_resolve_to_the_right_entity():
    entities = _entities()
    for sensor_key, suffix in EXPECTED.items():
        sensor_def = SENSOR_DEFS_BY_KEY[sensor_key]
        expected_uid = f"BTXXXXXXXXXX_{suffix}"
        expected_entity_id = f"sensor.emma_{EMMA_UNIQUE_IDS.index(expected_uid)}"
        resolved = HubCoordinator._match(sensor_def, HS, entities)
        assert resolved == expected_entity_id, (
            f"{sensor_key}: expected match on '{suffix}' "
            f"({expected_entity_id}), got {resolved!r}"
        )


def test_total_emma_coverage_does_not_regress():
    entities = _entities()
    matched = sum(
        1 for sensor_def in SENSOR_DEFS_BY_KEY.values()
        if HubCoordinator._match(sensor_def, HS, entities)
    )
    assert matched >= 16, (
        f"expected at least 16 of the 64 real-world EMMA entities to "
        f"resolve, got {matched}"
    )


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
