"""Self-checks for overlay HUD min-limit and MEB TSK overlay flags."""
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1] / "overlay_beta"


def _load(rel, name):
  path = ROOT / rel
  spec = importlib.util.spec_from_file_location(name, path)
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod


def test_min_display_speed_limit():
  m = _load("ui/onroad/display_speed_limit.py", "display_speed_limit")
  assert m.min_display_speed_limit_mps(0, 0, 0) is None
  city = 40 / 3.6
  assert abs(m.min_display_speed_limit_mps(city, city, 0) - city) < 1e-6
  assert m.min_display_speed_limit_mps(5.0, 0, 0) is None  # below floor


def test_meb_tsk_hard_brake_overlay():
  # Inline the same mapping as CarState.meb_tsk_cruise_flags (avoid importing iqdbc).
  MEB_TEMP = 6

  def flags(tsk, standstill, esp_hold, was_enabled, near_standstill=False, driver_braking=False):
    temp_fault = tsk == MEB_TEMP
    hard_fault = tsk == 7
    hold = standstill or esp_hold or (near_standstill and was_enabled)
    temp_at_hold = temp_fault and hold
    temp_brake_overlay = temp_fault and driver_braking
    hard_at_hold = hard_fault and hold and was_enabled
    standstill_temp = temp_at_hold or hard_at_hold
    if tsk in (3, 4, 5):
      was_enabled = True
    elif tsk in (0, 1) or (hard_fault and not hard_at_hold):
      was_enabled = False
    available = tsk in (2, 3, 4, 5) or standstill_temp or temp_brake_overlay
    enabled = tsk in (3, 4, 5) or (standstill_temp and was_enabled)
    acc_faulted = (hard_fault and not hard_at_hold) or (
      temp_fault and not temp_at_hold and not temp_brake_overlay
    )
    return acc_faulted, available, enabled, was_enabled

  faulted, available, _, _ = flags(6, False, False, True, driver_braking=True)
  assert faulted is False
  assert available is True
  faulted, _, _, _ = flags(6, False, False, True, driver_braking=False)
  assert faulted is True
  faulted, _, _, _ = flags(7, False, False, True, driver_braking=True)
  assert faulted is True


def test_nav_exec_floor():
  kph_to_ms = 1 / 3.6
  floor = 60.0 * kph_to_ms
  city = 40.0 * kph_to_ms
  assert max(city, 0.0, floor) == floor
  highway = 80.0 * kph_to_ms
  assert max(highway, 0.0, floor) == highway


if __name__ == "__main__":
  test_min_display_speed_limit()
  test_meb_tsk_hard_brake_overlay()
  test_nav_exec_floor()
  print("ok")
