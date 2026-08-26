#!/usr/bin/env python3
"""Export comma Params as a GitHub-safe JSON snapshot (no account / secrets / device identity).

Run on device:
  PYTHONPATH=/data/openpilot /usr/local/venv/bin/python export_comma_settings_public.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

PARAMS_DIR = "/data/params/d"
OUT = "/tmp/comma_settings_public.json"

DENY_EXACT = {
  "DongleId", "HardwareSerial", "IMEI", "Serial",
  "GithubUsername", "GithubSshKeys", "SubscriberInfo", "GitRemote",
  "WifiPassword", "WifiSsid",
  "MapboxPublicKey", "MapboxSecretKey", "MapboxAccessToken",
  "ApiCache_Owner", "ApiCache_NavDestinations",
  "ApiCache_DriveStats", "ApiCache_FirehoseStats",
  "AthenadUploadQueue", "AthenadRecentlyViewedRoutes",
  "AthenadPid", "HephaestusdPid",
  "CurrentBootlog", "LastAthenaPingTime", "LastOffroadStatusPacket",
  "GitDiff", "InstallDate", "ForceOnroadUntil",
  "CarBatteryCapacity", "DriverLockoutCount", "BootCount",
  "NavDestination", "NavDestinationWaypoints", "NavigationDestination",
  "LastGPSPosition", "LastLiveMapData",
  "LiveTorqueTemporaries", "LiveDelayTemporaries",
  "IqlinkBlePsk", "IqlinkHotspotSsid", "IqlinkHotspotPassword",
  # cellular / live runtime / usage fingerprint
  "GsmApn", "GsmRoaming", "GsmMetered",
  "IqlinkBleConnected", "IqlinkBleDiscovering", "IqlinkBleLinkState",
  "IqlinkBlePairFailed", "IqlinkBlePeerConnected",
  "NavigationActive", "IsEngaged", "IsOffroad", "IsOnroad", "IsDriverViewEnabled",
  "UptimeOffroad", "UptimeOnroad", "RouteCount",
  "LastUpdateRouteCount", "LastUpdateUptimeOnroad", "LastUpdateTime",
  "UpdaterLastFetchTime", "ModelManager_LastSyncTime", "ModelManager_DownloadIndex",
  "PreviousSpeedLimit", "MapSpeedLimit", "OsmDownloadedDate",
}

DENY_SUBSTR = (
  "password", "passwd", "secret", "token", "cookie", "credential",
  "sshkey", "ssh_key", "privatekey", "private_key",
  "dongle", "imei", "serial", "email",
  "jwt", "wifi", "mapbox", "prime", "subscription",
  "uploadqueue", "bootlog", "gps", "location",
  "calibration", "carparams", "fingerprint", "vin",
  "persistent", "psk", "hotspot", "destination", "waypoint",
)

DENY_PREFIX = ("ApiCache_", "Offroad_", "Legacy")

MAX_VALUE_CHARS = 512
MAX_VALUE_BYTES = 1024


def is_denied(name: str) -> bool:
  if name in DENY_EXACT:
    return True
  low = name.lower()
  if any(s in low for s in DENY_SUBSTR):
    return True
  return any(name.startswith(p) for p in DENY_PREFIX)


def decode_value(raw: bytes):
  if len(raw) > MAX_VALUE_BYTES or b"\x00" in raw:
    return None
  try:
    text = raw.decode("utf-8")
  except UnicodeDecodeError:
    return None
  if len(text) > MAX_VALUE_CHARS:
    return None
  low = text.lower()
  if low == "true":
    return True
  if low == "false":
    return False
  if re.fullmatch(r"-?\d+", text):
    return int(text)
  if re.fullmatch(r"-?\d+\.\d+", text):
    return float(text)
  if text[:1] in "{[":
    try:
      return json.loads(text)
    except Exception:
      pass
  return text


def sanitize_settings(settings: dict) -> dict:
  ub = settings.get("UpdaterAvailableBranches")
  if isinstance(ub, str):
    parts = [
      x.strip() for x in ub.split(",")
      if x.strip() and "cloud-agent" not in x.lower() and not x.startswith("cursor/")
    ]
    settings["UpdaterAvailableBranches"] = ",".join(parts) if parts else "iqlink"
  return settings


def main() -> int:
  cst = timezone(timedelta(hours=8))
  settings = {}
  skipped = []
  binaryish = []

  for name in sorted(os.listdir(PARAMS_DIR)):
    path = os.path.join(PARAMS_DIR, name)
    if not os.path.isfile(path):
      continue
    if is_denied(name):
      skipped.append(name)
      continue
    try:
      with open(path, "rb") as f:
        raw = f.read()
    except OSError:
      skipped.append(name)
      continue
    val = decode_value(raw)
    if val is None:
      binaryish.append(name)
      continue
    settings[name] = val

  settings = sanitize_settings(settings)
  out = {
    "meta": {
      "generated_cst": datetime.now(cst).strftime("%Y-%m-%d %H:%M:%S"),
      "source": "comma /data/params/d",
      "purpose": "GitHub-safe openpilot/IQ settings snapshot (account/device identity redacted)",
      "settings_count": len(settings),
      "excluded_count": len(skipped) + len(binaryish),
      "redaction": [
        "DongleId / HardwareSerial / IMEI",
        "GithubUsername / GithubSshKeys / GitRemote",
        "WiFi / Hotspot SSID & passwords / BLE PSK",
        "GsmApn / live IqlinkBle* link state",
        "Mapbox / API tokens & caches",
        "NavDestination / GPS / routes / uptime counters",
        "CalibrationParams / CarParams* / VIN / fingerprints",
        "Personal updater branches (cursor/cloud-agent*)",
      ],
      "note": (
        "0/1 are kept as integers (device stores BOOL and INT enums the same way). "
        "Restore is manual: copy only the keys you intend to change."
      ),
    },
    "settings": settings,
  }
  with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
  print(f"WROTE {OUT} settings={len(settings)} skipped={len(skipped)} binary={len(binaryish)}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
