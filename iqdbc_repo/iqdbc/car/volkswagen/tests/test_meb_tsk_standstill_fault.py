"""MEB TSK=6/7 at standstill must not raise Cruise Faulted.

See iqpilot/CRUISE_FAULTED_FIXES.md.
Reproduces qlog 00000065--e9e438edaf--17 (TSK=6) and 00000071--b9692f4465--2 (TSK=7).
"""
from iqdbc.car.volkswagen.carstate import CarState


def test_tsk6_at_standstill_keeps_long_without_fault():
  faulted, available, enabled, was = CarState.meb_tsk_cruise_flags(
    tsk_status=3, standstill=False, esp_hold=False, was_enabled=False
  )
  assert (faulted, available, enabled, was) == (False, True, True, True)

  faulted, available, enabled, was = CarState.meb_tsk_cruise_flags(
    tsk_status=6, standstill=True, esp_hold=False, was_enabled=was
  )
  assert faulted is False
  assert available is True
  assert enabled is True
  assert was is True


def test_tsk6_while_moving_is_still_fault():
  faulted, available, enabled, was = CarState.meb_tsk_cruise_flags(
    tsk_status=6, standstill=False, esp_hold=False, was_enabled=True
  )
  assert faulted is True
  assert available is False
  assert enabled is False
  assert was is True


def test_tsk7_while_moving_is_hard_fault():
  faulted, available, enabled, was = CarState.meb_tsk_cruise_flags(
    tsk_status=7, standstill=False, esp_hold=False, was_enabled=True
  )
  assert faulted is True
  assert available is False
  assert enabled is False
  assert was is False


def test_tsk7_at_standstill_after_op_long_ok():
  # 071--2 @173.95: Motion_State=3 + standstill + TSK 3→7 after OP hold.
  faulted, available, enabled, was = CarState.meb_tsk_cruise_flags(
    tsk_status=3, standstill=True, esp_hold=True, was_enabled=False
  )
  assert was is True
  faulted, available, enabled, was = CarState.meb_tsk_cruise_flags(
    tsk_status=7, standstill=True, esp_hold=True, was_enabled=was
  )
  assert faulted is False
  assert available is True
  assert enabled is True
  assert was is True


def test_tsk7_at_standstill_without_prior_long_still_faults():
  # Never engaged OP long → TSK=7 at park remains a real hard fault.
  faulted, available, enabled, was = CarState.meb_tsk_cruise_flags(
    tsk_status=7, standstill=True, esp_hold=True, was_enabled=False
  )
  assert faulted is True
  assert available is False
  assert enabled is False
  assert was is False


def test_tsk6_with_esp_hold_ok():
  faulted, available, enabled, was = CarState.meb_tsk_cruise_flags(
    tsk_status=6, standstill=False, esp_hold=True, was_enabled=True
  )
  assert faulted is False
  assert available is True
  assert enabled is True
