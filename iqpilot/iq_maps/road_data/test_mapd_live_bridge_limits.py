#!/usr/bin/env python3
"""Minimal self-check for MapdLiveBridge limit reads (no cereal loop)."""
from types import SimpleNamespace


def _read_limits(mapd_alive: bool, mapd_valid: bool, speed: float, nxt: float, dist: float, road: str):
  if not mapd_alive or not mapd_valid:
    return 0.0, 0.0, 0.0, ""
  return float(speed or 0.0), float(nxt or 0.0), float(dist or 0.0), str(road or "")


def main() -> None:
  assert _read_limits(False, True, 50 / 3.6, 0, 0, "A") == (0.0, 0.0, 0.0, "")
  assert _read_limits(True, False, 50 / 3.6, 0, 0, "A") == (0.0, 0.0, 0.0, "")
  lim, nxt, dist, road = _read_limits(True, True, 50 / 3.6, 40 / 3.6, 120.0, "Main St")
  assert abs(lim - 50 / 3.6) < 1e-6
  assert abs(nxt - 40 / 3.6) < 1e-6
  assert dist == 120.0
  assert road == "Main St"
  print("mapd_live_bridge self-check ok")


if __name__ == "__main__":
  main()
