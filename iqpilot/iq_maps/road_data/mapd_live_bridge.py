#!/usr/bin/env python3
"""Open-source mapdOut → iqLiveData bridge (display path without private iqmapd).

Registers as process mapd_live_bridge. Publishes iqLiveData at 1 Hz from mapdOut
so HUD/SLC keep working when iqmapd crash-loops.
"""
from __future__ import annotations

import cereal.messaging as messaging
from openpilot.common.realtime import Ratekeeper, config_realtime_process
from openpilot.iqpilot.iq_maps.road_data.signal_bridge import RoadSignalBridge


class MapdLiveBridge(RoadSignalBridge):
  def __init__(self):
    super().__init__()
    self.mapd_sub = messaging.SubMaster(["mapdOut"])

  def refresh_position(self) -> None:
    # Position comes from iqLiveLocation via base class SubMaster in publish path.
    self.location_sub.update(0)
    self.mapd_sub.update(0)
    loc = self.location_sub["iqLiveLocation"]
    self.fix_ready = bool(getattr(loc, "gpsHealthy", False))

  def read_current_limit(self) -> float:
    if not self.mapd_sub.alive["mapdOut"] or not self.mapd_sub.valid["mapdOut"]:
      return 0.0
    return float(self.mapd_sub["mapdOut"].speedLimit or 0.0)

  def read_upcoming_limit(self) -> tuple[float, float]:
    if not self.mapd_sub.alive["mapdOut"] or not self.mapd_sub.valid["mapdOut"]:
      return 0.0, 0.0
    m = self.mapd_sub["mapdOut"]
    return float(m.nextSpeedLimit or 0.0), float(m.nextSpeedLimitDistance or 0.0)

  def read_current_road(self) -> str:
    if not self.mapd_sub.alive["mapdOut"] or not self.mapd_sub.valid["mapdOut"]:
      return ""
    m = self.mapd_sub["mapdOut"]
    return str(m.roadName or m.wayName or "")

  def step(self) -> None:
    self.refresh_position()
    self.publish_snapshot()


def main() -> None:
  config_realtime_process([0, 1, 2, 3], 5)
  bridge = MapdLiveBridge()
  rk = Ratekeeper(1, print_delay_threshold=None)
  while True:
    bridge.step()
    rk.keep_time()


if __name__ == "__main__":
  main()
