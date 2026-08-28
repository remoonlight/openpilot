"""Lead-follow standstill hold (no cereal, no APK/BLE)."""
from pathlib import Path
from types import SimpleNamespace

_IQ = Path(__file__).resolve().parents[1] / "iq_longitudinal_planner.py"
_LONG = Path(__file__).resolve().parents[1] / "longitudinal_planner.py"


def _load_hold():
  src = _IQ.read_text(encoding="utf-8")
  start = src.index("def hold_at_standstill")
  end = src.index("\nclass LongitudinalPlannerIQ")
  ns = {"_STANDSTILL_HOLD_MS": 0.75}
  exec(src[start:end], ns)
  return ns["hold_at_standstill"]


def _load_apply():
  src = _LONG.read_text(encoding="utf-8")
  start = src.index("def apply_follow_standstill_hold")
  end = src.index("\ndef get_cruise_accel")
  ns = {}
  exec(src[start:end], ns)
  return ns["apply_follow_standstill_hold"]


hold_at_standstill = _load_hold()
apply_follow_standstill_hold = _load_apply()


class _CS:
  def __init__(self, standstill, gas=False, v_ego=0.0):
    self.standstill = standstill
    self.gasPressed = gas
    self.vEgo = v_ego


def _sm(lead_status=False, v_lead=0.0):
  return {"radarState": SimpleNamespace(leadOne=SimpleNamespace(status=lead_status, vLead=v_lead))}


def test_no_hold_without_active_stop():
  assert hold_at_standstill(_CS(True)) is False


def test_hold_after_active_stop():
  assert hold_at_standstill(_CS(True), light_stop_active=True) is True


def test_gas_releases_hold():
  assert hold_at_standstill(_CS(True, gas=True), light_stop_active=True) is False


def test_lead_moving_releases_hold():
  assert hold_at_standstill(_CS(True), light_stop_active=True, lead_moving=True) is False


def test_creep_still_holds():
  assert hold_at_standstill(_CS(False, v_ego=0.4), light_stop_active=True) is True


def test_apply_keeps_mpc_stop_until_lead_moves():
  should_stop, a_target = apply_follow_standstill_hold(_CS(True), _sm(), 0.4, True)
  assert should_stop is True
  assert a_target <= 0.0


def test_apply_releases_when_lead_moving():
  should_stop, a_target = apply_follow_standstill_hold(
    _CS(True), _sm(lead_status=True, v_lead=2.0), 0.4, True)
  assert should_stop is True
  assert a_target == 0.4


def test_apply_does_not_invent_stop_while_moving():
  should_stop, a_target = apply_follow_standstill_hold(
    _CS(False, v_ego=8.0), _sm(), 0.4, False)
  assert should_stop is False
  assert a_target == 0.4


if __name__ == "__main__":
  for _name, _fn in list(globals().items()):
    if _name.startswith("test_"):
      _fn()
  print("ok")
