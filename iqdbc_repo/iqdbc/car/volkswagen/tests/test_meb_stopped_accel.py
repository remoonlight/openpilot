"""
MEB stop handshake aligned with release-meb.

Hold 前：Anhalten=1 + 真实减速；仅 ESP hold 后才 ACCEL_INACTIVE。
起步（绿灯 / SET@hold）路径不在此文件，见 test_meb_starting / test_meb_acc_hold_release。
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""
from types import SimpleNamespace

from iqdbc.car.volkswagen.mebcan import (
  ACCEL_INACTIVE,
  ACC_CTRL_ACTIVE,
  ACC_HMS_HOLD,
  acc_hold_type,
  create_acc_accel_control,
)

STOPPING_ACCEL = -0.56


class _CapturePacker:
  def __init__(self):
    self.msgs = {}

  def make_can_msg(self, name, bus, values):
    self.msgs[name] = values
    return name, bus, values


def _acc_18(*, stopping, esp_hold, starting, speed_kph, accel=STOPPING_ACCEL):
  packer = _CapturePacker()
  create_acc_accel_control(
    packer, 0, SimpleNamespace(flags=0), 1, True,
    4.0, 4.0, 1.0, 1.0,
    accel, ACC_CTRL_ACTIVE, ACC_HMS_HOLD, stopping, starting, esp_hold,
    speed_kph, False, False,
  )
  return packer.msgs["ACC_18"]


def test_creep_without_esp_hold_keeps_real_accel_and_anhalten():
  """release-meb: near-zero without hold must not look 'already stopped'."""
  for speed in (0.0, 0.3, -0.04):
    values = _acc_18(stopping=True, esp_hold=False, starting=False, speed_kph=speed)
    assert values["ACC_Sollbeschleunigung_02"] == STOPPING_ACCEL
    assert values["ACC_Anhalten"] == 1
    assert values["ACC_neg_Sollbeschl_Grad_02"] == 4.0


def test_still_rolling_keeps_real_accel():
  values = _acc_18(stopping=True, esp_hold=False, starting=False, speed_kph=5.0)
  assert values["ACC_Sollbeschleunigung_02"] == STOPPING_ACCEL
  assert values["ACC_Anhalten"] == 1


def test_stopping_without_esp_hold_still_requests_hold():
  hold = acc_hold_type(
    main_switch_on=True, acc_faulted=False, long_active=True,
    starting=False, stopping=True, esp_hold=False,
    override=False, override_begin=False, long_disabling=False,
  )
  assert hold == ACC_HMS_HOLD


def test_esp_hold_sends_neutral_accel():
  values = _acc_18(stopping=True, esp_hold=True, starting=False, speed_kph=0.0)
  assert values["ACC_Sollbeschleunigung_02"] == ACCEL_INACTIVE
  assert values["ACC_Anhalten"] == 0
  assert values["ACC_neg_Sollbeschl_Grad_02"] == 0


def test_starting_from_stop_restores_limits():
  """Green light / lead pulls away: limits must come back so the car can move."""
  values = _acc_18(stopping=False, esp_hold=False, starting=True, speed_kph=0.0, accel=0.5)
  assert values["ACC_Anfahren"] is True
  assert values["ACC_neg_Sollbeschl_Grad_02"] == 4.0
  assert values["ACC_pos_Sollbeschl_Grad_02"] == 4.0
  assert values["ACC_Sollbeschleunigung_02"] == 0.5
