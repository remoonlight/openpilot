"""Park/reverse and single-light hold helpers (no cereal import)."""
from pathlib import Path
from types import SimpleNamespace

_PLANNER = (
  Path(__file__).resolve().parents[1]
  / "overlay_beta/selfdrive/controls/lib/iq_longitudinal_planner.py"
)


def _load_helpers():
  src = _PLANNER.read_text(encoding="utf-8")
  start = src.index("def nav_long_blocked_by_gear")
  end = src.index("\nclass LongitudinalPlannerIQ")
  ns = {"_GEAR": SimpleNamespace(park="park", reverse="reverse", drive="drive")}
  exec(src[start:end], ns)
  return ns


_H = _load_helpers()
nav_long_blocked_by_gear = _H["nav_long_blocked_by_gear"]
nav_long_blocked = _H["nav_long_blocked"]
iqlink_nav_go = _H["iqlink_nav_go"]
hold_at_standstill = _H["hold_at_standstill"]
_GEAR = _H["_GEAR"]


def test_park_blocks_nav_long():
  assert nav_long_blocked_by_gear(_GEAR.park) is True


def test_reverse_blocks_nav_long():
  assert nav_long_blocked_by_gear(_GEAR.reverse) is True


def test_drive_allows_nav_long():
  assert nav_long_blocked_by_gear(_GEAR.drive) is False


def test_stale_ble_blocks_nav_long_in_drive():
  assert nav_long_blocked(_GEAR.drive, link_warn=True) is True


def test_fresh_ble_allows_nav_long_in_drive():
  assert nav_long_blocked(_GEAR.drive, link_warn=False) is False


class _CS:
  def __init__(self, standstill, gas=False, v_ego=0.0):
    self.standstill = standstill
    self.gasPressed = gas
    self.vEgo = v_ego


def test_standstill_without_light_does_not_hold():
  assert hold_at_standstill(_CS(True, False)) is False


def test_standstill_holds_without_gas():
  assert hold_at_standstill(_CS(True, False), light_stop_active=True) is True


def test_standstill_releases_on_gas():
  assert hold_at_standstill(_CS(True, True), light_stop_active=True) is False


def test_moving_does_not_hold():
  assert hold_at_standstill(_CS(False, False, v_ego=5.0), light_stop_active=True) is False


def test_creep_speed_without_standstill_flag_still_holds():
  assert hold_at_standstill(_CS(False, False, v_ego=0.4), light_stop_active=True) is True


def test_nav_go_releases_standstill_hold():
  assert hold_at_standstill(_CS(True, False), nav_go=True, light_stop_active=True) is False


def test_lead_moving_releases_light_hold():
  assert hold_at_standstill(_CS(True, False), light_stop_active=True, lead_moving=True) is False


def test_vision_go_releases_light_hold():
  assert hold_at_standstill(_CS(True, False), light_stop_active=True, vision_go=True) is False


def test_iqlink_nav_go_matches_iq_link1():
  assert iqlink_nav_go(nav_valid=True, nav_stop_request=False, nav_speed_target=60 / 3.6, nav_accel_target=0.0) is True
  assert iqlink_nav_go(nav_valid=True, nav_stop_request=True, nav_speed_target=0.0, nav_accel_target=-2.0) is False
  assert iqlink_nav_go(nav_valid=False, nav_stop_request=False, nav_speed_target=60 / 3.6, nav_accel_target=0.0) is False


def test_iqlink_nav_go_apk_green():
  assert iqlink_nav_go(
    nav_valid=True, nav_stop_request=False, nav_speed_target=60 / 3.6, nav_accel_target=-2.0,
    traffic_light="green",
  ) is True
