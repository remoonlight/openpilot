# Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
from __future__ import annotations

import json
import os
import socket
import subprocess
import time

from iqpilot.cereal import messaging
from iqpilot.common.params import Params
from iqpilot.common.realtime import Ratekeeper
from iqpilot.common.swaglog import cloudlog

ANDROID_ROOT = "/data/android"
HEADLESS = f"{ANDROID_ROOT}/waydroid_headless.sh"
TRIM = f"{ANDROID_ROOT}/android_trim.sh"
GUARD = f"{ANDROID_ROOT}/android_guard.sh"
LXC_ATTACH = f"{ANDROID_ROOT}/root/usr/bin/lxc-attach"
LD = f"{ANDROID_ROOT}/root/usr/lib/aarch64-linux-gnu"

# Waze's launcher is FreeMapAppActivity; there is no com.waze.MainActivity, and asking for
# one fails with "Activity class does not exist" rather than anything that names the problem.
NAV_APPS = {
  "waze": ("com.waze", "com.waze/.FreeMapAppActivity"),
  "maps": ("com.google.android.apps.maps", "com.google.android.apps.maps/com.google.android.maps.MapsActivity"),
}
BRIDGE_HOST = "192.168.240.112"
BRIDGE_PORT = 8099
GPS_SOURCES = ["iqLiveLocation", "liveLocationKalman", "gpsLocationExternal", "gpsLocation"]
PROVIDERS = ("gps", "fused", "network")
GPS_INTERVAL_S = 0.5


def attach(*args: str, timeout: float = 10.0) -> subprocess.CompletedProcess:
  cmd = ["sudo", "-n", "env", f"LD_LIBRARY_PATH={LD}", LXC_ATTACH,
         "-P", "/var/lib/waydroid/lxc", "-n", "waydroid", "--", *args]
  return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def container_booted() -> bool:
  try:
    return attach("/system/bin/getprop", "sys.boot_completed", timeout=8).stdout.strip() == "1"
  except (subprocess.SubprocessError, OSError):
    return False


def bring_up() -> None:
  # AGNOS mounts / read-only, so no unit file can be installed; a transient unit is the only
  # way the compositor and lxc-start survive this process exiting.
  subprocess.run(["sudo", "-n", "systemd-run", "--unit=iq-android", "--service-type=oneshot",
                  "--remain-after-exit", HEADLESS, "up"],
                 capture_output=True, text=True, timeout=120, check=False)


def start_guard() -> None:
  subprocess.run(["sudo", "-n", "systemd-run", "--unit=iq-android-guard", GUARD],
                 capture_output=True, text=True, timeout=30, check=False)


def trim(nav_app: str) -> None:
  subprocess.run(["sudo", "-n", "env", f"ANDROID_NAV_APP={nav_app}", TRIM],
                 capture_output=True, timeout=240, check=False)


def enable_mock_location() -> None:
  # Wiped by every container restart, and the package form does not cover uid 0: without the
  # --uid form every injection fails with SecurityException and the apps just say "no GPS".
  attach("/system/bin/cmd", "appops", "set", "--uid", "0", "android:mock_location", "allow")
  for p in PROVIDERS:
    attach("/system/bin/cmd", "location", "providers", "add-test-provider", p)
    attach("/system/bin/cmd", "location", "providers", "set-test-provider-enabled", p, "true")
  # The a11y tree is only updated while the display is awake; asleep it emits nothing at all.
  attach("/system/bin/svc", "power", "stayon", "true")


def inject(lat: float, lon: float) -> None:
  for p in PROVIDERS:
    attach("/system/bin/cmd", "location", "providers", "set-test-provider-location", p,
           "--location", f"{lat:.6f},{lon:.6f}", "--accuracy", "4", timeout=6)


def read_position(sm: messaging.SubMaster) -> tuple[float, float] | None:
  for src in GPS_SOURCES:
    if src not in sm.data or not sm.valid.get(src, False):
      continue
    msg = sm[src]
    for lat_a, lon_a in (("latitude", "longitude"), ("lat", "lon")):
      lat = getattr(msg, lat_a, None)
      lon = getattr(msg, lon_a, None)
      if lat is not None and lon is not None and (lat or lon):
        return float(lat), float(lon)
  return None


class AndroidNavDaemon:
  def __init__(self) -> None:
    self.params = Params()
    self.sources = [s for s in GPS_SOURCES if s in messaging.SERVICE_LIST]
    self.sm = messaging.SubMaster(self.sources) if self.sources else None
    self.last_inject = 0.0
    self.up = False

  def status(self, text: str) -> None:
    self.params.put("IQAndroidNavStatus", text)

  def sign_in(self) -> None:
    email = self.params.get("IQAndroidNavEmail", encoding="utf8")
    password = self.params.get("IQAndroidNavPassword", encoding="utf8")
    if not email or not password:
      return
    try:
      with socket.create_connection((BRIDGE_HOST, BRIDGE_PORT), timeout=10) as s:
        s.sendall(json.dumps({"cmd": "signin", "email": email, "password": password}).encode() + b"\n")
      self.status("sign-in requested")
    except OSError:
      cloudlog.exception("androidd: sign-in request failed")
      self.status("sign-in failed")
    finally:
      # Never let the credential outlive the one use it was handed over for.
      self.params.remove("IQAndroidNavEmail")
      self.params.remove("IQAndroidNavPassword")

  def nav_app(self) -> str:
    value = self.params.get("IQAndroidNavApp", encoding="utf8") or "waze"
    return value if value in NAV_APPS else "waze"

  def enforce_single_app(self, nav_app: str) -> None:
    for name, (pkg, _) in NAV_APPS.items():
      if name != nav_app:
        attach("/system/bin/am", "force-stop", pkg)

  def ensure_app_running(self, nav_app: str) -> None:
    pkg, component = NAV_APPS[nav_app]
    if attach("/system/bin/pidof", pkg, timeout=8).stdout.strip():
      return
    attach("/system/bin/am", "start", "-n", component, timeout=20)

  def ensure_up(self) -> None:
    if container_booted():
      if not self.up:
        nav_app = self.nav_app()
        enable_mock_location()
        trim(nav_app)
        self.enforce_single_app(nav_app)
        start_guard()
        self.status(f"running:{nav_app}")
        self.up = True
      return
    self.up = False
    self.status("starting")
    bring_up()

  def step(self) -> None:
    if not self.params.get_bool("IQAndroidNav"):
      if self.up:
        subprocess.run(["sudo", "-n", "systemctl", "stop", "iq-android", "iq-android-guard"],
                       capture_output=True, timeout=60, check=False)
        self.up = False
        self.status("disabled")
      return

    self.ensure_up()
    if not self.up:
      return

    self.sign_in()
    self.ensure_app_running(self.nav_app())

    if self.sm is None:
      return
    self.sm.update(0)
    now = time.monotonic()
    if now - self.last_inject < GPS_INTERVAL_S:
      return
    position = read_position(self.sm)
    if position is not None:
      self.last_inject = now
      try:
        inject(*position)
      except subprocess.SubprocessError:
        cloudlog.exception("androidd: location inject failed")


def main() -> None:
  if not os.path.exists(HEADLESS):
    cloudlog.warning("androidd: android stack not staged, exiting")
    return
  daemon = AndroidNavDaemon()
  rk = Ratekeeper(2.0, print_delay_threshold=None)
  while True:
    try:
      daemon.step()
    except Exception:
      cloudlog.exception("androidd: step failed")
    rk.keep_time()


if __name__ == "__main__":
  main()
