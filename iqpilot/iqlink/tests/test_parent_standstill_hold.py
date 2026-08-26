"""Parent planner standstill hold helpers (no cereal import)."""
from pathlib import Path
from types import SimpleNamespace

_PLANNER = (
  Path(__file__).resolve().parents[1]
  / "overlay_beta/selfdrive/controls/lib/longitudinal_planner.py"
)


def _load_helpers():
  src = _PLANNER.read_text(encoding="utf-8")
  start = src.index("def parent_nav_go")
  end = src.index("\ndef get_max_accel")
  ns = {}
  exec(src[start:end], ns)
  return ns


_H = _load_helpers()
parent_nav_go = _H["parent_nav_go"]
apply_parent_standstill_hold = _H["apply_parent_standstill_hold"]


class _CS:
  def __init__(self, standstill, gas=False, v_ego=0.0):
    self.standstill = standstill
    self.gasPressed = gas
    self.vEgo = v_ego


def test_standstill_forces_should_stop_and_clips_accel():
  should_stop, a_target = apply_parent_standstill_hold(_CS(True), False, 0.4, False)
  assert should_stop is True
  assert a_target <= 0.0


def test_creep_speed_forces_should_stop():
  should_stop, a_target = apply_parent_standstill_hold(_CS(False, v_ego=0.4), False, 0.3, False)
  assert should_stop is True
  assert a_target <= 0.0


def test_nav_go_does_not_force_hold():
  should_stop, a_target = apply_parent_standstill_hold(_CS(True), True, 0.4, False)
  assert should_stop is False
  assert a_target == 0.4


def test_gas_does_not_force_hold():
  should_stop, a_target = apply_parent_standstill_hold(_CS(True, gas=True), False, 0.4, False)
  assert should_stop is False
  assert a_target == 0.4


def test_parent_nav_go_from_speed_targets():
  planner = SimpleNamespace(nav_valid=True, nav_stop_request=False, nav_speed_target=16.6, nav_accel_target=0.0)
  sm = {}
  assert parent_nav_go(planner, sm) is True


def test_parent_nav_go_false_on_stop_request():
  planner = SimpleNamespace(nav_valid=True, nav_stop_request=True, nav_speed_target=0.0, nav_accel_target=-2.0)
  assert parent_nav_go(planner, {}) is False


def test_parent_nav_go_right_turn_window():
  planner = SimpleNamespace(nav_valid=False, nav_stop_request=True, nav_speed_target=0.0, nav_accel_target=-2.0)
  nav = SimpleNamespace(
    nextManeuverType=SimpleNamespace(name="turn"),
    nextManeuverDirection=SimpleNamespace(name="right"),
    nextManeuverDistance=40.0,
  )
  assert parent_nav_go(planner, {"iqNavState": nav}) is True
