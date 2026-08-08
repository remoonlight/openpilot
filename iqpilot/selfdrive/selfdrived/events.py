import cereal.messaging as messaging
from cereal import log, car, custom
from openpilot.common.constants import CV
from openpilot.iqpilot.common.atlas_alerts import EventBook as EventsBase, Tier as Priority, Tags as ET, AlertCard as Alert, \
  NoEntryCard as NoEntryAlert, HardDisableCard as ImmediateDisableAlert, ChimeCard as EngagementAlert, \
  BannerCard as NormalPermanentAlert, AlertFactory as AlertCallbackType, car_mode_entry_alert as wrong_car_mode_alert


AlertSize = log.SelfdriveState.AlertSize
AlertStatus = log.SelfdriveState.AlertStatus
VisualAlert = car.CarControl.HUDControl.VisualAlert
AudibleAlert = car.CarControl.HUDControl.AudibleAlert
AudibleAlertIQ = custom.IQState.AudibleAlert
EventNameIQ = custom.IQOnroadEvent.EventName


# get event name from enum
EVENT_NAME_IQ = {v: k for k, v in EventNameIQ.schema.enumerants.items()}


def _get_longitudinal_plan_ext(sm: messaging.SubMaster):
  return sm['iqPlan']


def speed_limit_adjust_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  plan = _get_longitudinal_plan_ext(sm)
  resolver = plan.speedLimit.resolver
  speed_conv = CV.MS_TO_KPH if metric else CV.MS_TO_MPH
  speed = round(resolver.speedLimit * speed_conv)
  return Alert(
    f"限速{speed} km/h" if metric else f"Speed Limit {speed} mph",
    "",
    AlertStatus.normal, AlertSize.small,
    Priority.LOW, VisualAlert.none, AudibleAlert.none, 4.)


def speed_limit_pre_active_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  plan = _get_longitudinal_plan_ext(sm)
  resolver = plan.speedLimit.resolver
  speed_conv = CV.MS_TO_KPH if metric else CV.MS_TO_MPH
  pending_speed = round(resolver.speedLimit * speed_conv)
  last_speed = resolver.speedLimitFinalLast * speed_conv
  is_lower = pending_speed < last_speed or last_speed <= 0
  confirm_hint = "SET" if is_lower else "RES"
  return Alert(
    f"限速{pending_speed} km/h" if metric else f"Speed Limit: {pending_speed} mph",
    f"Press {confirm_hint} to apply",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOW, VisualAlert.none, AudibleAlertIQ.promptSingleLow, .1)


def speed_limit_changed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  resolver = _get_longitudinal_plan_ext(sm).speedLimit.resolver
  speed_conv = CV.MS_TO_KPH if metric else CV.MS_TO_MPH
  speed = round(resolver.speedLimit * speed_conv)
  return Alert(
    f"限速{speed} km/h" if metric else f"Speed Limit changed to {speed} mph",
    "",
    AlertStatus.normal, AlertSize.small,
    Priority.LOW, VisualAlert.none, AudibleAlertIQ.promptSingleHigh, 3.)


def construction_zone_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  resolver = _get_longitudinal_plan_ext(sm).speedLimit.resolver
  speed_conv = CV.MS_TO_KPH if metric else CV.MS_TO_MPH
  speed = round(resolver.speedLimit * speed_conv)
  return Alert(
    f"限速{speed} km/h" if metric else f"Construction Zone: {speed} mph",
    "",
    AlertStatus.userPrompt, AlertSize.small,
    Priority.MID, VisualAlert.none, AudibleAlertIQ.promptSingleHigh, 4.)


_CAMERA_LABELS_ZH = {
  int(custom.IQNavState.CameraType.fixedSpeed): "测速摄像头",
  int(custom.IQNavState.CameraType.mobileSpeed): "流动测速",
  int(custom.IQNavState.CameraType.sectionStart): "区间测速",
  int(custom.IQNavState.CameraType.sectionEnd): "区间测速结束",
  int(custom.IQNavState.CameraType.averageZone): "区间测速",
  int(custom.IQNavState.CameraType.redLight): "闯红灯拍照",
  int(custom.IQNavState.CameraType.bump): "减速带",
  int(custom.IQNavState.CameraType.alpr): "电子警察",
}

_CAMERA_LABELS = {
  int(custom.IQNavState.CameraType.fixedSpeed): "Speed Camera",
  int(custom.IQNavState.CameraType.mobileSpeed): "Mobile Speed Camera",
  int(custom.IQNavState.CameraType.sectionStart): "Average-Speed Zone",
  int(custom.IQNavState.CameraType.sectionEnd): "Average-Speed Zone Ends",
  int(custom.IQNavState.CameraType.averageZone): "Average-Speed Zone",
  int(custom.IQNavState.CameraType.redLight): "Red-Light Camera",
  int(custom.IQNavState.CameraType.bump): "Speed Bump",
  int(custom.IQNavState.CameraType.alpr): "Flock / ALPR Camera",
}


def speed_camera_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  nav = sm['iqNavState']
  cam_raw = int(getattr(nav.cameraType, "raw", nav.cameraType) or 0)
  distance = float(getattr(nav, "cameraDistance", 0.0) or 0.0)
  # RF Flock/ALPR live proximity hit: distance 0, prioritize over map-distance banner.
  if cam_raw == int(custom.IQNavState.CameraType.alpr) and distance <= 0.0:
    text = "电子警察" if metric else "Flock Camera Detected"
    return Alert(
      text,
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.HIGH, VisualAlert.none, AudibleAlert.prompt, .2)
  # Metric/zh UI: small Chinese "限速xx km/h" (Latin digits/units keep Inter in alert renderer).
  if metric:
    if float(nav.cameraSpeedLimit) > 0.0:
      speed = round(float(nav.cameraSpeedLimit) * CV.MS_TO_KPH)
      text = f"限速{speed} km/h"
    else:
      text = _CAMERA_LABELS_ZH.get(cam_raw, "测速摄像头")
  elif float(nav.cameraSpeedLimit) > 0.0:
    speed = round(float(nav.cameraSpeedLimit) * CV.MS_TO_MPH)
    text = f"Speed Limit {speed} mph"
  else:
    text = _CAMERA_LABELS.get(cam_raw, "Speed Camera")
  return Alert(
    text,
    "",
    AlertStatus.normal, AlertSize.small,
    Priority.LOW, VisualAlert.none, AudibleAlert.prompt, .2)


class IQEvents(EventsBase):
  def __init__(self):
    super().__init__()
    self.event_counters = dict.fromkeys(EVENTS_IQ.keys(), 0)

  def get_events_mapping(self) -> dict[int, dict[str, Alert | AlertCallbackType]]:
    return EVENTS_IQ

  def get_event_name(self, event: int):
    return EVENT_NAME_IQ[event]

  def get_event_msg_type(self):
    return custom.IQOnroadEvent.Event


EVENTS_IQ_TYPE = dict[int, dict[str, Alert | AlertCallbackType]]

_GUIDANCE_EVENTS: EVENTS_IQ_TYPE = {
  EventNameIQ.speedLimitActive: {
    ET.WARNING: speed_limit_adjust_alert,
  },

  EventNameIQ.speedLimitPreActive: {
    ET.WARNING: speed_limit_pre_active_alert,
  },

  EventNameIQ.speedLimitChanged: {
    ET.WARNING: speed_limit_changed_alert,
  },

  EventNameIQ.speedCameraAhead: {
    ET.WARNING: speed_camera_alert,
  },

  EventNameIQ.constructionZoneDetected: {
    ET.WARNING: construction_zone_alert,
  },

  EventNameIQ.navExitLeft: {
    ET.WARNING: Alert(
      "Navigation: Exit Maneuver",
      "Nudge the wheel left to change lanes",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.none, AudibleAlert.prompt, 1.5),
  },

  EventNameIQ.navExitRight: {
    ET.WARNING: Alert(
      "Navigation: Exit Maneuver",
      "Nudge the wheel right to change lanes",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.none, AudibleAlert.prompt, 1.5),
  },

  # HUD text suppressed; keep keys so any stale event name stays mapped.
  EventNameIQ.navTurnLeft: {},
  EventNameIQ.navTurnRight: {},

  EventNameIQ.modelTurnLeft: {
    ET.WARNING: Alert(
      "Lane Turn Left",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1.),
  },

  EventNameIQ.modelTurnRight: {
    ET.WARNING: Alert(
      "Lane Turn Right",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1.),
  },

}

_ENGAGE_EVENTS: EVENTS_IQ_TYPE = {
  EventNameIQ.alcEngaged: {
    ET.ENABLE: EngagementAlert(AudibleAlert.engage),
  },

  EventNameIQ.alcEngagedSilent: {
    ET.ENABLE: EngagementAlert(AudibleAlert.none),
  },

  EventNameIQ.alcDisengaged: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
  },

  EventNameIQ.alcDisengagedSilent: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.none),
  },

  EventNameIQ.steerManually: {
    ET.USER_DISABLE: Alert(
      "Lane Centering Off",
      "Steer Manually",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.disengage, 1.),
  },

  EventNameIQ.speedManually: {
    ET.WARNING: Alert(
      "Adaptive Cruise Off",
      "Control Speed Manually",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1.),
  },

  EventNameIQ.steeringOverrideReengageAlc: {
    ET.WARNING: Alert(
      "Steering Overridden By Driver",
      "Re-Engage ALC",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.none, AudibleAlert.prompt, 2.0),
  },

  EventNameIQ.latMismatch: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Lateral Controls Mismatch"),
    ET.NO_ENTRY: NoEntryAlert("Lateral Controls Mismatch"),
  },

}

_CABIN_BLOCK_EVENTS: EVENTS_IQ_TYPE = {
  EventNameIQ.brakeHoldSilent: {
    ET.WARNING: EngagementAlert(AudibleAlert.none),
    ET.NO_ENTRY: NoEntryAlert("Brake Hold Engaged"),
  },

  EventNameIQ.gearNotDriveSilent: {
    ET.WARNING: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0.),
    ET.NO_ENTRY: Alert(
      "Not in Drive",
      "IQ.Pilot Unavailable",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0.),
  },

  EventNameIQ.parkBrakeSilent: {
    ET.WARNING: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0.),
    ET.NO_ENTRY: NoEntryAlert("Parking Brake On"),
  },

  EventNameIQ.doorAjarSilent: {
    ET.WARNING: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0.),
    ET.NO_ENTRY: NoEntryAlert("Door Ajar"),
  },

  EventNameIQ.seatbeltUnbuckledSilent: {
    ET.WARNING: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0.),
    ET.NO_ENTRY: NoEntryAlert("Seatbelt Unbuckled"),
  },

  EventNameIQ.reverseSilent: {
    ET.PERMANENT: Alert(
      "In\nReverse",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2, creation_delay=0.5),
    ET.NO_ENTRY: NoEntryAlert("In Reverse"),
  },

}

_NOTICE_EVENTS: EVENTS_IQ_TYPE = {
  EventNameIQ.carModeMismatchNotice: {
    ET.WARNING: wrong_car_mode_alert,
  },

  EventNameIQ.pedalHeldNotice: {
    ET.WARNING: NoEntryAlert("Pedal Held")
  },

  EventNameIQ.experimentalToggled: {
    ET.WARNING: NormalPermanentAlert("Experimental Mode Switched", duration=1.5)
  },

  EventNameIQ.e2eChime: {
    ET.PERMANENT: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.MID, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

}

EVENTS_IQ: EVENTS_IQ_TYPE = {**_GUIDANCE_EVENTS, **_ENGAGE_EVENTS, **_CABIN_BLOCK_EVENTS, **_NOTICE_EVENTS}
