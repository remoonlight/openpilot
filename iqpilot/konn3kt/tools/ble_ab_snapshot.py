#!/usr/bin/env python3
"""A/B reboot checklist helper — state snapshots at T+0 / +30s / +60s.

Double-blind matrix (manual reboot between cells):
  A: IqlinkEnabled=0 → reboot → run this script → note connect time from phone
  B: IqlinkEnabled=1 → reboot → run this script → note connect time from phone

This script does NOT reboot or change Params. It only prints timed snapshots.
"""

from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
import time


MATRIX = """
A/B matrix (set Params manually, reboot device, then run this script):
  Cell A: IqlinkEnabled=0, Konn3ktBleTransportEnabled=1 (default)
  Cell B: IqlinkEnabled=1, Konn3ktBleTransportEnabled=1 (default)
Record phone-side time-to-connect after each reboot; compare A vs B.
"""


def _run(cmd: list[str]) -> str:
  try:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
    out = (r.stdout or "") + (r.stderr or "")
    return out.strip() or f"<exit {r.returncode}>"
  except Exception as e:
    return f"<error: {e}>"


def _bool_param(key: str) -> str:
  try:
    from openpilot.common.params import Params
    return str(Params().get_bool(key))
  except Exception as e:
    return f"<error: {e}>"


def _raw_param(key: str) -> str:
  try:
    from openpilot.common.params import Params
    raw = Params().get(key)
    if isinstance(raw, bytes):
      return raw.decode()
    return str(raw) if raw is not None else ""
  except Exception as e:
    return f"<error: {e}>"


def snapshot(label: str) -> None:
  ts = datetime.datetime.now().isoformat(timespec="seconds")
  print(f"=== {label} @ {ts} ===")
  print(f"ble-transportd: {_run(['systemctl', 'is-active', 'ble-transportd'])}")
  print(f"iqlinkd: {_run(['systemctl', 'is-active', 'iqlinkd'])}")
  bt = _run(["bluetoothctl", "show"])
  for line in bt.splitlines():
    if "Powered:" in line or "Discoverable:" in line or "Pairable:" in line:
      print(f"  {line.strip()}")
  print(f"Konn3ktBleTransportEnabled={_bool_param('Konn3ktBleTransportEnabled')}")
  print(f"IqlinkEnabled={_bool_param('IqlinkEnabled')}")
  print(f"IqlinkBleLinkState={_raw_param('IqlinkBleLinkState')}")
  print(f"IqlinkBleConnected={_bool_param('IqlinkBleConnected')}")
  print(f"IqlinkBlePeerConnected={_bool_param('IqlinkBlePeerConnected')}")
  print()


def main() -> int:
  ap = argparse.ArgumentParser(description="BLE A/B snapshot helper (no reboot)")
  ap.add_argument(
    "--intervals",
    type=int,
    default=30,
    help="Seconds between snapshots after T+0 (default: 30 → T+0/30/60)",
  )
  ap.add_argument("--quiet-matrix", action="store_true", help="Skip matrix instructions")
  args = ap.parse_args()

  if not args.quiet_matrix:
    print(MATRIX.strip())

  snapshot("T+0s")
  for i in range(1, 3):
    time.sleep(max(args.intervals, 1))
    snapshot(f"T+{i * args.intervals}s")

  print("Done. Compare phone connect time across A/B cells after manual reboots.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
