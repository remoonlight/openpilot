"""Unit tests for iqlink protocol mapping.

Run: pytest iqpilot/iqlink/tests/test_protocol.py
"""

from openpilot.iqpilot.iqlink.protocol import map_carrot_to_nav_fields


def test_basic_speed_and_turn():
  raw = {
    "nRoadLimitSpeed": 80,
    "nTBTTurnType": 2,
    "nTBTDist": 90,
    "szTBTMainText": "右转",
    "nGoPosDist": 1200,
    "nGoPosTime": 180,
    "goalPosY": 32.03,
    "goalPosX": 118.90,
    "szGoalName": "家",
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["active"] is True
  # TBT distance cap removed: near turn keeps bare road limit; desire still fires.
  assert abs(f["speedTarget"] - 80 / 3.6) < 1e-3
  assert f["navSpeedTargetActive"] is False
  assert f["shouldSendTurnDesire"] is True
  assert f["nextManeuverDirection"] == "right"
  assert f["destinationName"] == "家"


def test_aggressive_lane_change_window():
  raw = {
    "nRoadLimitSpeed": 100,
    "nTBTTurnType": 4,
    "nTBTDist": 700,
  }
  f = map_carrot_to_nav_fields(raw, aggressive_lc=True)
  assert f is not None
  assert f["shouldSendLaneChangeDesire"] is True
  assert f["command"] == "laneChange"
  assert f["nextManeuverType"] == "fork"

  f2 = map_carrot_to_nav_fields(raw, aggressive_lc=False)
  assert f2 is not None
  assert f2["shouldSendLaneChangeDesire"] is False


def test_lane_recommend_straight_suppresses_lc():
  raw = {
    "nRoadLimitSpeed": 100,
    "nTBTTurnType": 4,
    "nTBTDist": 700,
    "laneRecommend": "straight",
  }
  f = map_carrot_to_nav_fields(raw, aggressive_lc=True)
  assert f is not None
  assert f["shouldSendLaneChangeDesire"] is False
  assert f["command"] == "none"
  # Maneuver HUD still describes the exit/LC.
  assert f["nextManeuverValid"] is True


def test_lane_recommend_left_keeps_lc():
  raw = {
    "nRoadLimitSpeed": 100,
    "nTBTTurnType": 4,
    "nTBTDist": 700,
    "laneRecommend": "left",
  }
  f = map_carrot_to_nav_fields(raw, aggressive_lc=True)
  assert f is not None
  assert f["shouldSendLaneChangeDesire"] is True


def test_camera_ignored_this_phase():
  # SDI / speed-camera pressure disabled; road limit owns speedTarget.
  raw = {
    "nRoadLimitSpeed": 120,
    "nSdiType": 1,
    "nSdiDist": 200,
    "nSdiSpeedLimit": 60,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["cameraValid"] is False
  assert abs(f["speedTarget"] - 120 / 3.6) < 1e-3
  assert f["longitudinalProvider"] == "route"


def test_rgdata_wrapper():
  raw = {"rgdata": {"nRoadLimitSpeed": 50}}
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["active"] is True


def test_rejects_without_heartbeat():
  assert map_carrot_to_nav_fields({"nTBTDist": 10}) is None


def test_green_wave_ignored():
  """C5-b: nGreenWaveSpeed must not affect speedTarget."""
  raw = {
    "nRoadLimitSpeed": 80,
    "nGreenWaveSpeed": 48,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert abs(f["speedTarget"] - 80 / 3.6) < 1e-3
  assert f["longitudinalEngaged"] is True


def test_tbt_near_turn_keeps_road_limit():
  """Near turn: no distance speed cap; turn desire still sent for lateral."""
  raw = {
    "nRoadLimitSpeed": 80,
    "nTBTTurnType": 1,
    "nTBTDist": 40,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["shouldSendTurnDesire"] is True
  assert abs(f["speedTarget"] - 80 / 3.6) < 1e-3
  assert f["navSpeedTargetActive"] is False


def test_tbt_far_turn_no_cap():
  raw = {
    "nRoadLimitSpeed": 80,
    "nTBTTurnType": 1,
    "nTBTDist": 500,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert abs(f["speedTarget"] - 80 / 3.6) < 1e-3
  assert f["navSpeedTargetActive"] is False


def test_red_light_stop_keeps_engaged():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 20,
    "trafficLightDistM": 40,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  # Distance curve (+2 m early-stop compensate): not slam to 0 at 40 m.
  assert 0.0 < f["speedTarget"] < 60 / 3.6
  assert f["longitudinalEngaged"] is True
  assert f["valid"] is True
  assert f["accelTarget"] == -2.0
  assert f["cameraType"] != "redLight"


def test_red_remain_3_model_stop_still_stops():
  # remain 3 + model still stopping: keep red-stop (no fake green).
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 3,
    "trafficLightDistM": 25,
    "visionStop": True,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["accelTarget"] == -2.0
  assert f["speedTarget"] < 60 / 3.6
  assert f["trafficLight"] == "red"


def test_red_remain_3_model_go_releases():
  # remain < 5 and model can-go outranks the old remain==3 stop.
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 3,
    "trafficLightDistM": 25,
  }
  f = map_carrot_to_nav_fields(raw, vision_stop=False)
  assert f is not None
  assert abs(f["speedTarget"] - 60 / 3.6) < 1e-3
  assert f["accelTarget"] >= 0.0
  assert f["trafficLight"] == "red"


def test_red_remain_1_prestart_releases_nav_stop():
  # Explicit remainS 0..1 + aligned clocks clears nav red stop (accel>=0).
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 1,
    "trafficLightDistM": 5,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert abs(f["speedTarget"] - 60 / 3.6) < 1e-3
  assert f["accelTarget"] >= 0.0
  assert f["trafficLight"] == "red"
  assert f["trafficLightRemainS"] == 1
  assert f["longitudinalEngaged"] is True


def test_red_remain_0_prestart_releases_nav_stop():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 0,
    "trafficLightDistM": 5,
  }
  f = map_carrot_to_nav_fields(raw, clock_aligned=True)
  assert f is not None
  assert abs(f["speedTarget"] - 60 / 3.6) < 1e-3
  assert f["accelTarget"] >= 0.0


def test_red_remain_0_model_stop_prestart_needs_sticky_align():
  """APK quiet: keep clock_aligned so remain 0 still prestarts while vision wants stop."""
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 0,
    "trafficLightDistM": 5,
  }
  go = map_carrot_to_nav_fields(raw, clock_aligned=True, vision_stop=True)
  halt = map_carrot_to_nav_fields(raw, clock_aligned=False, vision_stop=True)
  assert go is not None and halt is not None
  assert go["accelTarget"] >= 0.0
  assert halt["accelTarget"] == -2.0


def test_red_remain_1_without_clock_align_model_stop_keeps_stop():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 1,
    "trafficLightDistM": 5,
    "visionStop": True,
  }
  f = map_carrot_to_nav_fields(raw, clock_aligned=False)
  assert f is not None
  assert f["accelTarget"] == -2.0


def test_red_remain_1_model_go_releases_without_clock():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 1,
    "trafficLightDistM": 5,
  }
  f = map_carrot_to_nav_fields(raw, clock_aligned=False, vision_stop=False)
  assert f is not None
  assert f["accelTarget"] >= 0.0


def test_red_without_remain_does_not_prestart():
  # Omitted remainS: no clock — keep red stop until APK sends green.
  raw = {"nRoadLimitSpeed": 60, "trafficLight": "red", "trafficLightDistM": 30}
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["accelTarget"] == -2.0
  assert f["speedTarget"] < 60 / 3.6
  assert f["trafficLightRemainS"] == -1


def test_red_light_without_dist_holds_stop():
  # APK red with no meters → hold stopped.
  raw = {"nRoadLimitSpeed": 60, "trafficLight": "red"}
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["speedTarget"] == 0.0
  assert f["accelTarget"] == -2.0
  assert f["longitudinalEngaged"] is True
  assert f["valid"] is True


def test_red_light_right_turn_no_nav_stop():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightDistM": 30,
    "nTBTTurnType": 2,
    "nTBTDist": 40,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["nextManeuverDirection"] == "right"
  # Right-turn-on-red: no nav red stop (accel stays off the red-stop -2.0 path).
  assert f["accelTarget"] != -2.0
  # No TBT speed cap either — bare road limit.
  assert abs(f["speedTarget"] - 60 / 3.6) < 1e-3
  assert f["rightTurnPending"] is True


def test_red_right_turn_far_still_stops():
  # Distant right turn must not skip the light at the current stop line.
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightDistM": 30,
    "nTBTTurnType": 2,
    "nTBTDist": 400,
  }
  f = map_carrot_to_nav_fields(raw, vision_stop=False)
  assert f is not None
  assert f["rightTurnPending"] is False
  assert f["accelTarget"] == -2.0


def test_yellow_right_turn_no_nav_stop():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "yellow",
    "trafficLightDistM": 20,
    "nTBTTurnType": 2,
    "nTBTDist": 30,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["accelTarget"] != -2.0


def test_left_turn_red_remain_3_model_go_still_stops():
  # Left-arrow red: model often sees through-green — must not punch on remain<5.
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 3,
    "trafficLightDistM": 25,
    "nTBTTurnType": 1,
    "nTBTDist": 40,
  }
  f = map_carrot_to_nav_fields(raw, vision_stop=False)
  assert f is not None
  assert f["leftTurnPending"] is True
  assert f["accelTarget"] == -2.0
  assert f["speedTarget"] < 60 / 3.6


def test_left_turn_red_remain_1_may_prestart():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 1,
    "trafficLightDistM": 5,
    "nTBTTurnType": 1,
    "nTBTDist": 20,
  }
  # remain 0/1 alone releases left (no clock/model gate — APK countdown end).
  f = map_carrot_to_nav_fields(raw, clock_aligned=False, vision_stop=True)
  assert f is not None
  assert f["accelTarget"] >= 0.0


def test_left_turn_apk_green_releases():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "green",
    "trafficLightRemainS": 12,
    "trafficLightDistM": 20,
    "nTBTTurnType": 1,
    "nTBTDist": 30,
  }
  f = map_carrot_to_nav_fields(raw, vision_stop=True)
  assert f is not None
  assert f["accelTarget"] >= 0.0
  assert abs(f["speedTarget"] - 60 / 3.6) < 1e-3


def test_red_no_remain_not_right_stops():
  raw = {"nRoadLimitSpeed": 60, "trafficLight": "red", "trafficLightDistM": 30}
  f = map_carrot_to_nav_fields(raw, vision_stop=False)
  assert f is not None
  assert f["accelTarget"] == -2.0


def test_red_remain_8_model_go_still_stops():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 8,
    "trafficLightDistM": 40,
  }
  f = map_carrot_to_nav_fields(raw, vision_stop=False)
  assert f is not None
  assert f["accelTarget"] == -2.0


def test_yellow_near_stops():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "yellow",
    "trafficLightDistM": 20,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert 0.0 <= f["speedTarget"] < 60 / 3.6
  assert f["longitudinalEngaged"] is True
  assert f["accelTarget"] == -2.0


def test_yellow_far_no_hard_brake():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "yellow",
    "trafficLightDistM": 80,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  # 80 m > ~71 m takeover at 60 kph: distance curve (mins to road limit), no hard brake.
  assert f["accelTarget"] != -2.0
  assert abs(f["speedTarget"] - 60 / 3.6) < 1e-3


def test_red_light_far_no_hard_brake():
  raw = {
    "nRoadLimitSpeed": 60,
    "trafficLight": "red",
    "trafficLightRemainS": 20,
    "trafficLightDistM": 800,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["accelTarget"] != -2.0
  assert abs(f["speedTarget"] - 60 / 3.6) < 1e-3


def test_green_restores_limit():
  raw = {
    "nRoadLimitSpeed": 70,
    "trafficLight": "green",
    "trafficLightRemainS": 10,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert abs(f["speedTarget"] - 70 / 3.6) < 1e-3
  assert f["cameraType"] != "redLight"


def test_vision_stop_without_green():
  # vision_stop no longer forces nav stop — E2E owns implicit stops.
  raw = {"nRoadLimitSpeed": 60, "trafficLight": "none"}
  f = map_carrot_to_nav_fields(raw, vision_stop=True)
  assert f is not None
  assert abs(f["speedTarget"] - 60 / 3.6) < 1e-3


def test_vision_stop_ignored_when_gaode_green():
  raw = {"nRoadLimitSpeed": 60, "trafficLight": "green"}
  f = map_carrot_to_nav_fields(raw, vision_stop=True)
  assert f is not None
  assert abs(f["speedTarget"] - 60 / 3.6) < 1e-3


def test_section_sdi_ignored_this_phase():
  raw = {
    "nRoadLimitSpeed": 100,
    "nSdiType": 1,
    "nSdiDist": 500,
    "nSdiSpeedLimit": 80,
    "nSdiBlockType": 2,
    "nSdiBlockDist": 120,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert abs(f["speedTarget"] - 100 / 3.6) < 1e-3
  assert f["cameraValid"] is False
  assert f["cameraDistance"] == 0.0


def test_vp_pos_is_not_destination():
  """Phone GPS ego report must not mark destinationValid."""
  raw = {
    "nRoadLimitSpeed": 60,
    "vpPosPointLat": 32.03,
    "vpPosPointLon": 118.90,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["destinationValid"] is False
  assert abs(f["destinationLatitude"]) < 1e-6


def test_remain_distance_marks_destination_without_poi_name():
  """Fullscreen Gaode often has remain km but no szGoalName in a11y."""
  raw = {
    "nRoadLimitSpeed": 80,
    "nGoPosDist": 17000,
    "nGoPosTime": 1200,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["destinationValid"] is True
  assert f["distanceRemaining"] == 17000
  assert f["destinationName"] == ""


def test_arrive_maps_to_arrive_and_kills_desire():
  # Morning route end: LC-right icon near dest. Kill lateral; keep active/limit.
  raw = {
    "nRoadLimitSpeed": 50,
    "nTBTTurnType": 4,
    "nTBTDist": 49,
    "nGoPosDist": 62,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["nextManeuverType"] == "arrive"
  assert f["shouldSendLaneChangeDesire"] is False
  assert f["shouldSendTurnDesire"] is False
  assert f["maneuverPhase"] == "none"
  assert f["command"] == "none"
  assert f["commandDirection"] == "none"
  assert f["active"] is True
  assert abs(f["speedTarget"] - 50 / 3.6) < 1e-3


def test_lane_change_icon_is_fork_not_exit():
  raw = {
    "nRoadLimitSpeed": 100,
    "nTBTTurnType": 4,
    "nTBTDist": 700,
    "nGoPosDist": 1200,
  }
  f = map_carrot_to_nav_fields(raw, aggressive_lc=True)
  assert f is not None
  assert f["nextManeuverType"] == "fork"
  assert f["shouldSendLaneChangeDesire"] is True


def test_real_ramp_exit_still_commits():
  # True _EXIT bucket has no left/right; is_lc is lc-only so send_lc stays False.
  raw = {
    "nRoadLimitSpeed": 100,
    "nTBTTurnType": 6,
    "nTBTDist": 700,
    "nGoPosDist": 5000,
  }
  f = map_carrot_to_nav_fields(raw, aggressive_lc=True)
  assert f is not None
  assert f["nextManeuverType"] == "exit"
  assert f["shouldSendLaneChangeDesire"] is False
  assert f["command"] == "none"


def test_near_turn_not_killed_when_far_from_dest():
  raw = {
    "nRoadLimitSpeed": 80,
    "nTBTTurnType": 1,
    "nTBTDist": 40,
    "nGoPosDist": 1200,
  }
  f = map_carrot_to_nav_fields(raw)
  assert f is not None
  assert f["shouldSendTurnDesire"] is True
  assert f["nextManeuverType"] == "turn"
