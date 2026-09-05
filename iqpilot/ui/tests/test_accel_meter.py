"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""
import pytest

from iqpilot.ui.onroad.hud_overlays import IQAccelBar


@pytest.mark.parametrize("acceleration", [-0.12, 0.0, 0.12])
def test_acceleration_meter_deadband(acceleration):
  assert IQAccelBar._normalized(acceleration) == 0.0


@pytest.mark.parametrize("acceleration", [-4.0, -3.0, 3.0, 4.0])
def test_acceleration_meter_clamps_full_scale(acceleration):
  assert IQAccelBar._normalized(acceleration) == 1.0


def test_acceleration_meter_is_symmetric():
  assert IQAccelBar._normalized(-1.5) == IQAccelBar._normalized(1.5)


def test_acceleration_meter_attack_is_faster_than_release():
  attack = IQAccelBar._next_value(0.0, 1.0, 0.05)
  release = IQAccelBar._next_value(1.0, 0.0, 0.05)
  assert attack > 1.0 - release


def test_acceleration_meter_crosses_direction_smoothly():
  shown = IQAccelBar._next_value(0.8, -0.8, 0.05)
  assert -0.8 < shown < 0.8
