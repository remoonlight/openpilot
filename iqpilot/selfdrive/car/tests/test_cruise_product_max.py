"""ponytail: cruise product max 120 + ±10 step defaults.

Run: pytest iqpilot/selfdrive/car/tests/test_cruise_product_max.py
"""

from openpilot.iqpilot.selfdrive.car.long_increments import (
  LongIncrementConfig,
  resolve_button_step,
)
from openpilot.selfdrive.car.cruise import V_CRUISE_MAX, V_CRUISE_PRODUCT_MAX_KPH


def test_product_max_is_120_not_119():
  assert V_CRUISE_PRODUCT_MAX_KPH == 120
  assert V_CRUISE_MAX >= 200  # safety ceiling untouched


def test_tap_step_10_reaches_120_from_110():
  cfg = LongIncrementConfig(enabled=True, tap_step=10, hold_step=5)
  snap, delta = resolve_button_step(cfg, held=False, unit_step=1.0)
  assert snap is True
  assert delta == 10.0
  assert 110.0 + delta == 120.0
  assert 110.0 + delta <= V_CRUISE_PRODUCT_MAX_KPH
