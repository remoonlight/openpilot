"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""

from types import SimpleNamespace

from cereal import custom
from openpilot.common.constants import CV
from openpilot.iqpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlannerIQ

LongitudinalPlanSource = custom.IQPlan.LongitudinalPlanSource
NavProvider = custom.IQNavState.LongitudinalProvider
NavLongitudinalState = custom.IQNavState.LongitudinalState


class FakeParams:
  def __init__(self, values=None):
    self.values = dict(values or {})

  def get(self, key, block=False, return_default=False, encoding=None):
    _ = block, return_default, encoding
    return self.values.get(key)

  def get_bool(self, key):
    return bool(self.values.get(key, False))


class _FakeSLC:
  def __init__(self, slc_offset=0.0, slc_v_cruise=40.0):
    self.slc_offset = slc_offset
    self._slc_v_cruise = slc_v_cruise
    self.slc_target = 0.0
    self.slc_active_target = 0.0
    self.slc_source = "None"
    self.slc_active_source = "None"
    self.slc_experimental_mode = False
    self.controller_enabled = False
    self.mode_assist = False
    self.pending_events = []

  def update(self, *_args, **_kwargs):
    return self._slc_v_cruise


class _FakeIQDynamic:
  def set_slc_experimental_mode(self, *_args, **_kwargs):
    pass

  def update(self, *_args, **_kwargs):
    pass

  def force_stop_requested(self):
    return False


def _build_planner(*, exclusive=True, slc_offset=0.0, value_offset=0, is_metric=True, slc_v_cruise=40.0):
  planner = LongitudinalPlannerIQ.__new__(LongitudinalPlannerIQ)
  planner.slc = _FakeSLC(slc_offset=slc_offset, slc_v_cruise=slc_v_cruise)
  planner.iq_dynamic = _FakeIQDynamic()
  planner._params = FakeParams({
    "IqlinkExclusive": exclusive,
    "IQSpeedAssistValueOffset": value_offset,
    "IsMetric": is_metric,
  })
  planner.source = LongitudinalPlanSource.cruise
  planner.output_v_target = 0.0
  planner.output_a_target = 0.0
  planner.speed_limit_last = 0.0
  planner.speed_limit_final_last = 0.0
  planner.speed_limit_source = custom.IQPlan.SpeedLimit.Source.none
  planner.force_stop_timer = 0.0
  planner.forcing_stop = False
  planner.override_force_stop = False
  planner.override_force_stop_timer = 0.0
  planner.tracked_model_length = 0.0
  return planner


def _build_sm(*, speed_target, accel_target=-0.5, engaged=True, valid=True,
              provider=NavProvider.route, v_cruise_cluster=120.0, lead_status=False):
  return {
    "carState": SimpleNamespace(vCruiseCluster=v_cruise_cluster, gasPressed=False, standstill=False,
                                cruiseState=SimpleNamespace(speedLimitPredicative=0.0)),
    "iqCarState": SimpleNamespace(accelPressed=False),
    "selfdriveState": SimpleNamespace(enabled=True, experimentalMode=False),
    "radarState": SimpleNamespace(leadOne=SimpleNamespace(status=lead_status, vLead=0.0)),
    "iqNavState": SimpleNamespace(
      longitudinalEngaged=engaged,
      longitudinalProvider=provider,
      longitudinalState=NavLongitudinalState.active if engaged else NavLongitudinalState.disabled,
      speedTarget=float(speed_target),
      accelTarget=float(accel_target),
      valid=valid,
    ),
    "clocks": SimpleNamespace(timeValid=True),
  }


def test_exclusive_bare_60_plus_offset10_outputs_70():
  planner = _build_planner(exclusive=True, slc_offset=10.0 * CV.KPH_TO_MS)
  sm = _build_sm(speed_target=60.0 * CV.KPH_TO_MS)
  v_out, _ = planner.update_targets(sm, v_ego=20.0, a_ego=0.0, v_cruise=30.0)
  assert abs(v_out - 70.0 * CV.KPH_TO_MS) < 1e-3
  assert planner.source == LongitudinalPlanSource.nav
  # Bare limit for UI/report stays 60; offset only on execution target.
  assert abs(planner.nav_speed_target - 60.0 * CV.KPH_TO_MS) < 1e-3


def test_exclusive_red_light_stop_stays_zero():
  planner = _build_planner(exclusive=True, slc_offset=10.0 * CV.KPH_TO_MS)
  sm = _build_sm(speed_target=0.0, accel_target=-2.0)
  v_out, a_out = planner.update_targets(sm, v_ego=15.0, a_ego=0.0, v_cruise=30.0)
  assert v_out == 0.0
  assert planner.nav_stop_request is True
  assert planner.source == LongitudinalPlanSource.nav
  assert a_out == -2.0


def test_exclusive_below_60_floors_then_offset():
  # 40 → floor 60 → +10 = 70 km/h (ACCEPTANCE: 控车按 60+偏移)
  planner = _build_planner(exclusive=True, slc_offset=10.0 * CV.KPH_TO_MS)
  sm = _build_sm(speed_target=40.0 * CV.KPH_TO_MS)
  v_out, _ = planner.update_targets(sm, v_ego=12.0, a_ego=0.0, v_cruise=30.0)
  assert abs(v_out - 70.0 * CV.KPH_TO_MS) < 1e-3
  assert planner.source == LongitudinalPlanSource.nav


def test_camera_speed_path_floors_then_offset():
  # Camera-derived speedTarget (e.g. 50 kph): floor 60 then +10 → 70.
  planner = _build_planner(exclusive=True, slc_offset=10.0 * CV.KPH_TO_MS)
  sm = _build_sm(speed_target=50.0 * CV.KPH_TO_MS, provider=NavProvider.camera)
  v_out, _ = planner.update_targets(sm, v_ego=18.0, a_ego=0.0, v_cruise=30.0)
  assert abs(v_out - 70.0 * CV.KPH_TO_MS) < 1e-3
  assert planner.source == LongitudinalPlanSource.nav
  assert planner.nav_provider == NavProvider.camera


def test_value_offset_fallback_when_slc_offset_zero():
  planner = _build_planner(exclusive=True, slc_offset=0.0, value_offset=10, is_metric=True)
  sm = _build_sm(speed_target=60.0 * CV.KPH_TO_MS)
  v_out, _ = planner.update_targets(sm, v_ego=20.0, a_ego=0.0, v_cruise=30.0)
  assert abs(v_out - 70.0 * CV.KPH_TO_MS) < 1e-3


def test_follow_lead_suppresses_nav_pressure():
  planner = _build_planner(exclusive=True, slc_offset=10.0 * CV.KPH_TO_MS)
  sm = _build_sm(speed_target=0.0, accel_target=-2.0, lead_status=True)
  v_out, _ = planner.update_targets(sm, v_ego=15.0, a_ego=0.0, v_cruise=30.0)
  assert planner.nav_stop_request is False
  # No nav target while following → cruise remains.
  assert planner.source == LongitudinalPlanSource.cruise
  assert abs(v_out - 30.0) < 1e-3


def test_fresh_params_prefer_nav_without_exclusive_flag():
  # Product: no exclusive session — fresh iqNavState alone drives nav preference.
  planner = _build_planner(exclusive=False, slc_offset=10.0 * CV.KPH_TO_MS)
  sm = _build_sm(speed_target=60.0 * CV.KPH_TO_MS)
  v_out, _ = planner.update_targets(sm, v_ego=20.0, a_ego=0.0, v_cruise=30.0)
  assert abs(v_out - 70.0 * CV.KPH_TO_MS) < 1e-3
  assert planner.source == LongitudinalPlanSource.nav


def test_inactive_nav_falls_back_to_cruise():
  # No fresh params (inactive/invalid) → follow cruise/model path.
  planner = _build_planner(exclusive=True, slc_offset=10.0 * CV.KPH_TO_MS)
  sm = _build_sm(speed_target=60.0 * CV.KPH_TO_MS, engaged=False, valid=False)
  v_out, _ = planner.update_targets(sm, v_ego=20.0, a_ego=0.0, v_cruise=30.0)
  assert planner.nav_valid is False
  assert planner.source == LongitudinalPlanSource.cruise
  assert abs(v_out - 30.0) < 1e-3


def test_red_light_approach_skips_60_floor():
  planner = _build_planner(exclusive=True, slc_offset=10.0 * CV.KPH_TO_MS)
  # ~47 kph approach at 40 m (+2 m comp) must not be floored to 60.
  approach = (2.0 * 2.0 * 42.0) ** 0.5  # sqrt(2*a*d)
  sm = _build_sm(speed_target=approach, accel_target=-2.0)
  v_out, a_out = planner.update_targets(sm, v_ego=15.0, a_ego=0.0, v_cruise=30.0)
  assert abs(v_out - approach) < 1e-3
  assert v_out < 60.0 * CV.KPH_TO_MS
  assert a_out == -2.0
  assert planner.source == LongitudinalPlanSource.nav
