from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "longitudinal_planner.py"
STOPPING_SPEED = 0.25


def _load_stopped_lead_hold():
  src = _SRC.read_text(encoding="utf-8")
  const_start = src.index("LEAD_HOLD_GAP")
  const_end = src.index("# Lookup table for turns")
  fn_start = src.index("def stopped_lead_hold")
  fn_end = src.index("\nclass LongitudinalPlanner")
  ns = {}
  exec(src[const_start:const_end] + src[fn_start:fn_end], ns)
  return ns["stopped_lead_hold"]


stopped_lead_hold = _load_stopped_lead_hold()


def test_stopped_close_stationary_lead_arms():
  assert stopped_lead_hold(False, 0.0, STOPPING_SPEED, True, 1.0, 0.0, False) is True


def test_armed_hysteresis_vlead():
  assert stopped_lead_hold(True, 0.0, STOPPING_SPEED, True, 1.0, 0.4, False) is True
  assert stopped_lead_hold(True, 0.0, STOPPING_SPEED, True, 1.0, 0.6, False) is False


def test_gap_and_missing_lead_release():
  assert stopped_lead_hold(True, 0.0, STOPPING_SPEED, True, 6.0, 0.0, False) is False
  assert stopped_lead_hold(True, 0.0, STOPPING_SPEED, False, 1.0, 0.0, False) is False


def test_override_releases():
  assert stopped_lead_hold(True, 0.0, STOPPING_SPEED, True, 1.0, 0.0, True) is False


def test_not_stopped_does_not_arm():
  assert stopped_lead_hold(False, 0.3, STOPPING_SPEED, True, 1.0, 0.0, False) is False


def test_unarmed_vlead_between_hysteresis_does_not_arm():
  assert stopped_lead_hold(False, 0.0, STOPPING_SPEED, True, 1.0, 0.4, False) is False
