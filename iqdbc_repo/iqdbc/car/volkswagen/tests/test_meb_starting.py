"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""
from types import SimpleNamespace

import pytest

from iqdbc.car import structs
from iqdbc.car.volkswagen.mebcan import compute_meb_long_starting

LongCtrlState = structs.CarControl.Actuators.LongControlState
ButtonType = structs.CarState.ButtonEvent.Type

V_EGO_STARTING = 0.5


def _btn(btn_type, pressed=True):
  return SimpleNamespace(type=btn_type, pressed=pressed)


@pytest.mark.parametrize(
  "long_state, v_ego, esp_hold, stopping, cc_enabled, buttons, accel, expected",
  [
    (LongCtrlState.pid, 0.1, True, False, False, (), 0.0, True),
    (LongCtrlState.pid, 0.1, True, False, False, (), 0.3, True),
    # qlog 81-1 / dump#6: pid flicker while still braking for lead → must NOT start
    (LongCtrlState.pid, 0.1, True, False, False, (), -0.27, False),
    (LongCtrlState.stopping, 0.1, True, True, False, (), -0.56, False),
    (LongCtrlState.starting, 0.1, True, False, False, (), 0.0, False),
    (
      LongCtrlState.stopping, 0.1, True, True, True,
      (_btn(ButtonType.resumeCruise),), -0.56, True,
    ),
    (LongCtrlState.pid, 1.0, True, False, False, (), 0.3, False),
  ],
  ids=[
    "pid_esp_hold_low_speed",
    "pid_esp_hold_positive_accel",
    "pid_esp_hold_negative_accel_no_start",
    "stopping_esp_hold",
    "starting_state_not_used",
    "stopping_esp_hold_resume_button",
    "pid_above_vEgoStarting",
  ],
)
def test_meb_long_starting(long_state, v_ego, esp_hold, stopping, cc_enabled, buttons, accel, expected):
  assert compute_meb_long_starting(
    long_state, v_ego, V_EGO_STARTING, esp_hold, stopping, cc_enabled, buttons, accel,
  ) == expected
