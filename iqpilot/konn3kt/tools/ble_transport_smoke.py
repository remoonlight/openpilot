#!/usr/bin/env python3
"""Smoke check: ble-transportd systemd + BlueZ Powered + key Params.

CLI helper (not imported by runtime). Exit 1 on hard fail.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def _systemd_active(unit: str) -> bool:
  try:
    return subprocess.run(
      ["systemctl", "is-active", "--quiet", unit],
      check=False,
    ).returncode == 0
  except Exception:
    return False


def _bluez_adapter_powered() -> bool:
  try:
    r = subprocess.run(
      ["bluetoothctl", "show"],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    return r.returncode == 0 and "Powered: yes" in r.stdout
  except Exception:
    return False


def _print_params() -> None:
  try:
    from openpilot.common.params import Params
  except Exception as e:
    print(f"Params unavailable: {e}")
    return

  p = Params()
  for key in ("Konn3ktBleTransportEnabled", "IqlinkEnabled"):
    try:
      print(f"{key}={p.get_bool(key)}")
    except Exception as e:
      print(f"{key}=<error: {e}>")
  for key in ("IqlinkBleLinkState", "IqlinkBleConnected", "IqlinkBlePeerConnected"):
    try:
      if key == "IqlinkBleLinkState":
        raw = p.get(key)
        val = raw.decode() if isinstance(raw, bytes) else raw
        print(f"{key}={val}")
      else:
        print(f"{key}={p.get_bool(key)}")
    except Exception as e:
      print(f"{key}=<error: {e}>")


def run() -> int:
  transport_ok = _systemd_active("ble-transportd")
  powered_ok = _bluez_adapter_powered()

  print(f"ble-transportd.active={transport_ok}")
  print(f"bluez.adapter_powered={powered_ok}")
  _print_params()

  if not transport_ok:
    print("FAIL: ble-transportd not active", file=sys.stderr)
    return 1
  if not powered_ok:
    print("FAIL: BlueZ adapter not Powered", file=sys.stderr)
    return 1
  print("ble_transport_smoke OK")
  return 0


def main() -> int:
  ap = argparse.ArgumentParser(description="BLE transport on-device smoke check")
  ap.parse_args()
  return run()


if __name__ == "__main__":
  sys.exit(main())
