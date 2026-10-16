"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import unittest
from unittest import mock

from opendbc.car.structs import car
from openpilot.common.parameterized import parameterized
from openpilot.selfdrive.controls.controlsd import Controls
from openpilot.sunnypilot.selfdrive.controls.controlsd_ext import ControlsExt

SteerControlType = car.CarParams.SteerControlType
V0 = object()
STOCK = object()


def _cp(steer_type, tuning='torque'):
  CP = car.CarParams.new_message()
  CP.steerControlType = steer_type
  CP.lateralTuning.init(tuning)
  if tuning == 'torque':
    CP.lateralTuning.torque.latAccelFactor = 1.0
  else:
    CP.lateralTuning.pid.kpBP = [0.0]
    CP.lateralTuning.pid.kpV = [1.0]
  return CP


def _ext(CP, enforce=False, tune=0.0):
  ext = ControlsExt.__new__(ControlsExt)
  ext.CP = CP
  ext.CP_SP = mock.Mock()
  ext.params = mock.Mock()
  ext.params.get_bool.return_value = enforce
  ext.params.get.return_value = tune
  ext._param_update_time = 0.0
  ext.blinker_pause_lateral = mock.Mock()
  return ext


class TestControlsdLateralSelection(unittest.TestCase):

  @parameterized.expand([
    (SteerControlType.angle, False, 0.0),
    (SteerControlType.angle, True, 0.0),
    (SteerControlType.angle, True, 1.0),
    (SteerControlType.curvature, False, 0.0),
    (SteerControlType.curvature, True, 0.0),
    (SteerControlType.curvature, True, 1.0),
  ])
  def test_preserves_angle_curvature_under_torque_tuning(self, steer_type, enforce, tune):
    ext = _ext(_cp(steer_type, 'torque'), enforce=enforce, tune=tune)
    with mock.patch(
      "openpilot.sunnypilot.selfdrive.controls.controlsd_ext.LatControlTorqueV0",
      return_value=V0,
    ) as ctor:
      assert ext.initialize_lateral_control(STOCK, None, 0.01) is STOCK
      ctor.assert_not_called()

  @parameterized.expand([
    (False, 0.0, V0),
    (False, 1.0, V0),
    (True, 0.0, V0),
    (True, 1.0, STOCK),
  ])
  def test_torque_steer_tune_versions(self, enforce, tune, expected):
    ext = _ext(_cp(SteerControlType.torque, 'torque'), enforce=enforce, tune=tune)
    with mock.patch(
      "openpilot.sunnypilot.selfdrive.controls.controlsd_ext.LatControlTorqueV0",
      return_value=V0,
    ):
      assert ext.initialize_lateral_control(STOCK, None, 0.01) is expected

  def test_torque_steer_pid_tuning_kept_when_not_enforced(self):
    ext = _ext(_cp(SteerControlType.torque, 'pid'), enforce=False, tune=0.0)
    with mock.patch(
      "openpilot.sunnypilot.selfdrive.controls.controlsd_ext.LatControlTorqueV0",
      return_value=V0,
    ) as ctor:
      assert ext.initialize_lateral_control(STOCK, None, 0.01) is STOCK
      ctor.assert_not_called()

  def test_get_params_sp_skips_lat_delay_for_curvature(self):
    ext = _ext(_cp(SteerControlType.curvature, 'torque'))
    sm = mock.MagicMock()
    with mock.patch(
      "openpilot.sunnypilot.selfdrive.controls.controlsd_ext.get_lat_delay",
    ) as get_lat_delay:
      ext.get_params_sp(sm)
      get_lat_delay.assert_not_called()
      assert not hasattr(ext, "lat_delay")

  def test_get_params_sp_updates_lat_delay_for_torque_steer(self):
    ext = _ext(_cp(SteerControlType.torque, 'torque'))
    sm = mock.MagicMock()
    sm["lateralDelay"].lateralDelay = 0.2
    with mock.patch(
      "openpilot.sunnypilot.selfdrive.controls.controlsd_ext.get_lat_delay",
      return_value=0.25,
    ) as get_lat_delay:
      ext.get_params_sp(sm)
      get_lat_delay.assert_called_once()
      assert ext.lat_delay == 0.25

  def test_update_torque_controller_skips_curvature(self):
    controls = Controls.__new__(Controls)
    controls.CP = _cp(SteerControlType.curvature, 'torque')
    controls.LaC = mock.Mock(spec=["update"])
    controls.sm = mock.MagicMock()
    controls.update_torque_controller()
    assert controls.sm.mock_calls == []

  def test_update_torque_controller_runs_for_torque_steer(self):
    controls = Controls.__new__(Controls)
    controls.CP = _cp(SteerControlType.torque, 'torque')
    controls.lat_delay = 0.2
    controls.LaC = mock.Mock()
    controls.sm = mock.MagicMock()
    controls.sm.all_checks.return_value = True
    controls.sm['lateralTorqueParameters'].useParams = True
    controls.sm['lateralTorqueParameters'].latAccelFactorFiltered = 1.0
    controls.sm['lateralTorqueParameters'].latAccelOffsetFiltered = 0.0
    controls.sm['lateralTorqueParameters'].frictionCoefficientFiltered = 0.1
    controls.update_torque_controller()
    controls.LaC.update_torque_parameters.assert_called_once()
    controls.LaC.extension.update_limits.assert_called_once()
    controls.LaC.extension.update_model_v2.assert_called_once()
    controls.LaC.extension.update_lateral_lag.assert_called_once_with(0.2)
