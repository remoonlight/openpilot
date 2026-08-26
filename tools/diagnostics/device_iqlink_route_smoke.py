#!/usr/bin/env python3
"""On-device smoke test for IQ-link route render publish (comma-side only)."""
from __future__ import annotations

import sys


def main() -> int:
  from iqpilot.iqlink.bridge import IqlinkBridge, clear_stale_nav_params
  from iqpilot.iqlink import protocol as proto

  b = IqlinkBridge.__new__(IqlinkBridge)
  fields = {
    "active": True,
    "destinationValid": True,
    "destinationLatitude": 32.10,
    "destinationLongitude": 118.80,
    "nextManeuverValid": True,
    "nextManeuverType": "turn",
    "nextManeuverDirection": "left",
    "nextManeuverDistance": 250.0,
  }
  msg = b._fill_render_msg(fields, 32.03, 118.75, 90.0)
  rs = msg.iqNavRenderState
  assert rs.active is True
  assert len(rs.routePolyline) == 2
  assert len(rs.routePolylineSimplified) == 2

  raw = {
    "nRoadLimitSpeed": 60,
    "goalPosY": 32.10,
    "goalPosX": 118.80,
    "vpPosPointLat": 32.03,
    "vpPosPointLon": 118.75,
    "nGoPosDist": 5000,
  }
  mapped = proto.map_carrot_to_nav_fields(raw)
  assert mapped is not None
  msg2 = b._fill_render_msg(mapped, 0.0, 0.0, 0.0, raw)
  rs2 = msg2.iqNavRenderState
  assert len(rs2.routePolyline) == 2
  assert abs(rs2.routePolyline[0].latitude - 32.03) < 1e-5
  assert abs(rs2.routePolyline[1].latitude - 32.10) < 1e-5

  fp = FakeParams({"NavigationActive": True, "NavigationDestination": {"name": "x"}})
  clear_stale_nav_params(fp)
  assert fp.get_bool("NavigationActive") is False
  assert "NavigationDestination" not in fp.values

  print("device_iqlink_route_smoke: PASS")
  return 0


class FakeParams:
  def __init__(self, values=None):
    self.values = dict(values or {})

  def get_bool(self, key):
    return bool(self.values.get(key, False))

  def put_bool(self, key, val):
    self.values[key] = bool(val)

  def remove(self, key):
    self.values.pop(key, None)


if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except Exception as exc:
    print(f"device_iqlink_route_smoke: FAIL {exc!r}")
    raise
