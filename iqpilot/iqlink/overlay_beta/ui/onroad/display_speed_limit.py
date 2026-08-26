"""Display speed-limit helper for mici HUD (always-on right-edge number).

Takes the minimum of ACC / Gaode road (not turn-capped) / vision-map sources.
"""
from __future__ import annotations

IQLINK_ROAD_SPEED_SHM = "/dev/shm/iqlink_road_speed_ms"
LIMIT_MIN_SPEED_MS = 8.33


def min_display_speed_limit_mps(acc_mps: float, nav_road_mps: float, vision_mps: float) -> float | None:
  vals = [float(v) for v in (acc_mps, nav_road_mps, vision_mps) if float(v or 0.0) >= LIMIT_MIN_SPEED_MS]
  return min(vals) if vals else None


def read_iqlink_road_speed_mps(path: str = IQLINK_ROAD_SPEED_SHM) -> float:
  try:
    with open(path, encoding="utf-8") as f:
      return float(f.read().strip() or 0.0)
  except Exception:
    return 0.0
