"""
Synthetic MEB "fake car" check: starting → ACC_HMS_RELEASE, hold path → ACC_HMS_HOLD.
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""
from types import SimpleNamespace

from iqdbc.car import structs
from iqdbc.car.volkswagen.mebcan import (
  ACC_HMS_HOLD,
  ACC_HMS_RELEASE,
  acc_hold_type,
  compute_meb_long_starting,
)

LongCtrlState = structs.CarControl.Actuators.LongControlState
V_EGO_STARTING = 0.5


def test_pid_esp_hold_low_speed_requests_release():
  starting = compute_meb_long_starting(
    LongCtrlState.pid, 0.1, V_EGO_STARTING, True, False, False, (), 0.2,
  )
  assert starting is True
  hold = acc_hold_type(
    main_switch_on=True,
    acc_faulted=False,
    long_active=True,
    starting=starting,
    stopping=False,
    esp_hold=True,
    override=False,
    override_begin=False,
    long_disabling=False,
  )
  assert hold == ACC_HMS_RELEASE


def test_pid_esp_hold_negative_accel_keeps_hold():
  """Lead follow-stop: pid flicker + brake accel must not HMS RELEASE (dump#6)."""
  starting = compute_meb_long_starting(
    LongCtrlState.pid, 0.1, V_EGO_STARTING, True, False, False, (), -0.27,
  )
  assert starting is False
  hold = acc_hold_type(
    main_switch_on=True,
    acc_faulted=False,
    long_active=True,
    starting=starting,
    stopping=False,
    esp_hold=True,
    override=False,
    override_begin=False,
    long_disabling=False,
  )
  assert hold == ACC_HMS_HOLD


def test_stopping_esp_hold_keeps_hold():
  starting = compute_meb_long_starting(
    LongCtrlState.stopping, 0.1, V_EGO_STARTING, True, True, False, (), -0.56,
  )
  assert starting is False
  hold = acc_hold_type(
    main_switch_on=True,
    acc_faulted=False,
    long_active=True,
    starting=starting,
    stopping=True,
    esp_hold=True,
    override=False,
    override_begin=False,
    long_disabling=False,
  )
  assert hold == ACC_HMS_HOLD


def test_resume_button_at_hold_requests_release():
  btn = SimpleNamespace(type=structs.CarState.ButtonEvent.Type.resumeCruise, pressed=True)
  starting = compute_meb_long_starting(
    LongCtrlState.stopping, 0.1, V_EGO_STARTING, True, True, True, (btn,), -0.56,
  )
  assert starting is True
  hold = acc_hold_type(
    main_switch_on=True,
    acc_faulted=False,
    long_active=True,
    starting=starting,
    stopping=True,
    esp_hold=True,
    override=False,
    override_begin=False,
    long_disabling=False,
  )
  assert hold == ACC_HMS_RELEASE
