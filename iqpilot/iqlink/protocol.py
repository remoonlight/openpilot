"""Map CPIQ-link / Carrot flat nav JSON → iqNavState field dict.

Called by: iqpilot/iqlink/bridge.py, iqpilot/iqlink/tests/test_protocol.py
"""

from __future__ import annotations

import math
from typing import Any

from . import AGGRESSIVE_LC_DISTANCE_M

_TURN_LEFT = {1, 12, 16, 17, 18}
_TURN_RIGHT = {2, 13, 19, 20, 21}
_LC_LEFT = {3, 7, 9, 22, 23}
_LC_RIGHT = {4, 8, 10, 24, 25}
_ROUNDABOUT = {5, 14, 15}
_EXIT = {6, 11}

# Strong decelerate for nav red/yellow stop (m/s^2).
_RED_LIGHT_ACCEL = -2.0
_RED_LIGHT_DECEL_MS2 = 2.0
# Roadtest: nav red stop landed ~2 m early of the stop line.
_STOP_LINE_EARLY_COMP_M = 2.0
# 到站只停横向 desire，不清 active/限速/红灯（R1）。
NEAR_DEST_REMAIN_M = 150.0
# China RTOR / left-arrow: only treat turn as "at this light" inside this window.
_LIGHT_TURN_WINDOW_M = 150.0


def _f(data: dict[str, Any], key: str, default: float = 0.0) -> float:
  try:
    v = data.get(key, default)
    if v is None:
      return default
    return float(v)
  except (TypeError, ValueError):
    return default


def _s(data: dict[str, Any], key: str, default: str = "") -> str:
  v = data.get(key, default)
  return "" if v is None else str(v)


def _kph_to_ms(kph: float) -> float:
  return max(kph, 0.0) / 3.6


def _turn_bucket(turn_type: int) -> str:
  if turn_type in _TURN_LEFT:
    return "turn_left"
  if turn_type in _TURN_RIGHT:
    return "turn_right"
  if turn_type in _LC_LEFT:
    return "lc_left"
  if turn_type in _LC_RIGHT:
    return "lc_right"
  if turn_type in _ROUNDABOUT:
    return "roundabout"
  if turn_type in _EXIT:
    return "exit"
  return "none"


def _maneuver_type(bucket: str) -> str:
  if bucket.startswith("turn"):
    return "turn"
  if bucket.startswith("lc"):
    return "fork"
  if bucket == "exit":
    return "exit"
  if bucket == "roundabout":
    return "roundabout"
  if bucket == "arrive":
    return "arrive"
  return "none"


def _dir_from_bucket(bucket: str) -> str:
  if "left" in bucket:
    return "left"
  if "right" in bucket:
    return "right"
  return "none"


def _red_light_approach_ms(light_dist_m: float, road_limit_ms: float) -> float:
  """Distance-based red stop cap; +2 m compensates measured early stop."""
  d = max(0.0, float(light_dist_m) + _STOP_LINE_EARLY_COMP_M)
  if d <= 0.05:
    return 0.0
  v = math.sqrt(2.0 * _RED_LIGHT_DECEL_MS2 * d)
  if road_limit_ms > 0:
    v = min(v, road_limit_ms)
  return v


def _red_light_takeover_m(road_limit_ms: float) -> float:
  """Hard-brake once DistM is within v^2/(2a) of the stop line (+2 m early-stop)."""
  v = max(0.0, float(road_limit_ms))
  return (v * v) / (2.0 * _RED_LIGHT_DECEL_MS2) + _STOP_LINE_EARLY_COMP_M


def flatten_payload(payload: dict[str, Any]) -> dict[str, Any]:
  if not isinstance(payload, dict):
    return {}
  if isinstance(payload.get("rgdata"), dict):
    return dict(payload["rgdata"])
  return dict(payload)


def is_nav_heartbeat(data: dict[str, Any]) -> bool:
  return "nRoadLimitSpeed" in data


def map_carrot_to_nav_fields(
  data: dict[str, Any],
  *,
  aggressive_lc: bool = True,
  command_index: int = 0,
  vision_stop: bool = False,
  clock_aligned: bool = True,
) -> dict[str, Any] | None:
  data = flatten_payload(data)
  if not is_nav_heartbeat(data):
    return None

  road_limit_kph = _f(data, "nRoadLimitSpeed")
  speed_ms = _kph_to_ms(road_limit_kph)

  turn_type = int(_f(data, "nTBTTurnType"))
  turn_dist = _f(data, "nTBTDist")
  bucket = _turn_bucket(turn_type)
  mtype = _maneuver_type(bucket)
  direction = _dir_from_bucket(bucket)
  desc = _s(data, "szTBTMainText") or _s(data, "szNearDirName")

  next_type = int(_f(data, "nTBTTurnTypeNext"))
  next_dist = _f(data, "nTBTDistNext")
  next_bucket = _turn_bucket(next_type)

  # goalPos* = destination; vpPosPoint* = ego GPS report only (never treat as dest).
  dest_lat = _f(data, "goalPosY")
  dest_lon = _f(data, "goalPosX")
  if abs(dest_lat) > 90 and abs(dest_lat) < 90000000:
    dest_lat /= 1e6
  if abs(dest_lon) > 180 and abs(dest_lon) < 180000000:
    dest_lon /= 1e6

  dest_name = _s(data, "szGoalName")
  go_dist = _f(data, "nGoPosDist")
  go_time = _f(data, "nGoPosTime")

  # SDI / speed-camera pressure: 本期不做（手机不上线 nSdi*；设备忽略）。
  cam_type = "none"
  cam_valid = False

  lc_window = AGGRESSIVE_LC_DISTANCE_M if aggressive_lc else 500.0
  is_lc = bucket.startswith("lc")
  send_lc = bool(is_lc and 0.0 < turn_dist <= lc_window)
  send_turn = bool(bucket.startswith("turn") and 0.0 < turn_dist <= 120.0)
  # B1: amapauto 13012 laneRecommend=straight → suppress auto LC (TBT HUD still valid).
  lane_rec = _s(data, "laneRecommend", "none").strip().lower()
  if send_lc and lane_rec == "straight":
    send_lc = False

  # TBT distance speed cap removed: turns/LC/exit leave speedTarget at road limit.
  # Curve slowdown is owned by IQ.Dynamic experimental/blended longitudinal.
  long_speed = speed_ms
  long_provider = "route"
  accel_target = 0.0

  # Green-wave: no amapauto source — do not consume nGreenWaveSpeed (C5-b).

  light = _s(data, "trafficLight", "none").strip().lower()
  light_dist = _f(data, "trafficLightDistM")
  light_remain_s = int(_f(data, "trafficLightRemainS")) if "trafficLightRemainS" in data else None
  vision_stop = bool(vision_stop) or bool(data.get("visionStop"))
  # China RTOR: imminent right turn skips nav red/yellow stop (E2E must not own the stop).
  right_turn_pending = bucket == "turn_right" and 0.0 < turn_dist <= _LIGHT_TURN_WINDOW_M
  left_turn_pending = bucket == "turn_left" and 0.0 < turn_dist <= _LIGHT_TURN_WINDOW_M
  # remain<5 + model not stopping outranks remain 0–1 prestart on through roads.
  # Left-turn red: model often "sees green" (through arrow) — never release on model_go.
  model_go = not vision_stop
  remain_lt_5 = light_remain_s is not None and 0 <= light_remain_s < 5
  remain_le_1 = light_remain_s is not None and 0 <= light_remain_s <= 1
  stop_for_light = False
  red_prestart_go = False
  if light == "green":
    # APK green is authoritative (incl. left-arrow green). Release hold immediately.
    red_prestart_go = True
  elif right_turn_pending and light in ("red", "yellow"):
    stop_for_light = False
  elif light == "yellow":
    stop_for_light = True
  elif light == "red":
    if left_turn_pending:
      # Left-arrow red: never release on model_go (through looks green).
      # remain 0/1 from APK = countdown ended / about to green — go without clock/model gate
      # (clock skew + vision_stop was leaving cars stuck after APK already showed green).
      if remain_le_1:
        red_prestart_go = True
      else:
        stop_for_light = True
    elif remain_lt_5 and model_go:
      red_prestart_go = True
    elif remain_le_1 and clock_aligned:
      red_prestart_go = True
    else:
      stop_for_light = True

  if stop_for_light:
    if light_dist > 0:
      road_ms = long_speed if long_speed > 0 else speed_ms
      long_speed = _red_light_approach_ms(light_dist, road_ms)
      if light_dist <= _red_light_takeover_m(road_ms):
        accel_target = _RED_LIGHT_ACCEL
    else:
      long_speed = 0.0
      accel_target = _RED_LIGHT_ACCEL
    long_provider = "route"
  elif red_prestart_go:
    # Keep road/TBT long_speed; force non-negative accel so hold can release.
    accel_target = max(accel_target, 0.0)
    long_provider = "route"

  engaged = bool(stop_for_light or long_speed > 0.0)

  # 到站 150m 内：先算灯/速度，再砍横向（R1 不清参）。
  if 0.0 < go_dist <= NEAR_DEST_REMAIN_M:
    send_lc = False
    send_turn = False
    mtype = "arrive"

  return {
    "active": True,
    # Raw Gaode road limit for HUD (distinct from targetSpeed which may be TBT/red capped).
    "roadSpeedLimit": speed_ms,
    "roadSpeedLimitValid": speed_ms > 0.0,
    # Fullscreen Gaode often has remain distance/time but no POI title in a11y tree.
    "destinationValid": bool(
      dest_name
      or (abs(dest_lat) > 0.01 and abs(dest_lon) > 0.01)
      or go_dist > 500.0
    ),
    "distanceRemaining": go_dist,
    "timeRemaining": go_time,
    "nextManeuverValid": turn_dist > 0 and mtype != "none",
    "nextManeuverDistance": turn_dist,
    "nextManeuverType": mtype,
    "nextManeuverDirection": direction,
    "nextManeuverDescription": desc,
    "secondNextManeuverValid": next_dist > 0 and next_bucket != "none",
    "secondNextManeuverType": _maneuver_type(next_bucket),
    "secondNextManeuverDirection": _dir_from_bucket(next_bucket),
    "secondNextManeuverDistance": next_dist,
    "shouldSendTurnDesire": send_turn,
    "turnDesireDirection": direction if send_turn else "none",
    "shouldSendLaneChangeDesire": send_lc,
    "laneChangeDesireDirection": direction if send_lc else "none",
    "maneuverPhase": "turnActive" if send_turn else ("highwayCommit" if send_lc else "none"),
    "maneuverDirection": direction if (send_turn or send_lc) else "none",
    "command": "laneChange" if send_lc else "none",
    "commandDirection": direction if send_lc else "none",
    "commandIndex": command_index,
    "destinationLatitude": dest_lat,
    "destinationLongitude": dest_lon,
    "destinationName": dest_name,
    "targetSpeed": long_speed,
    "targetSpeedValid": engaged,
    "speedTarget": long_speed,
    "accelTarget": accel_target,
    "valid": engaged,
    "longitudinalEngaged": engaged,
    "longitudinalProvider": long_provider,
    "longitudinalState": "active" if engaged else "disabled",
    "navSpeedTargetActive": engaged and (stop_for_light or long_speed < speed_ms - 1e-3),
    "cameraValid": cam_valid,
    "cameraType": cam_type,
    "cameraDistance": 0.0,
    "cameraSpeedLimit": 0.0,
    "navTurnDesireDirection": direction if send_turn else "none",
    "navLaneChangeDesireDirection": direction if send_lc else "none",
    "trafficLight": light,
    "trafficLightRemainS": -1 if light_remain_s is None else int(light_remain_s),
    "visionStop": vision_stop,
    "rightTurnPending": right_turn_pending,
    "leftTurnPending": left_turn_pending,
  }
